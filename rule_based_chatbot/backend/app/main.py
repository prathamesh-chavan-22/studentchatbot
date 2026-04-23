import os
from functools import partial
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import (
    authenticate_admin,
    create_session_token,
    ensure_admin_user,
    parse_session_token,
)
from app.chat_service import normalize_text, similarity_score
from app.db import build_engine, build_session_local, db_session, init_db
from app.models import ChatLog, QnA


class AskRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, value: str) -> str:
        message = value.strip()
        if not message:
            raise ValueError("Message cannot be blank")
        return message


class SelectRequest(BaseModel):
    qna_id: int


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=100)


class QnAInput(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    answer: str = Field(..., min_length=1, max_length=5000)

    @field_validator("question", "answer")
    @classmethod
    def non_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Field cannot be blank")
        return cleaned


def create_app(
    database_url: str | None = None,
    admin_username: str | None = None,
    admin_password: str | None = None,
    testing: bool = False,
) -> FastAPI:
    base_dir = Path(__file__).resolve().parent.parent
    database_url = database_url or os.getenv(
        "DATABASE_URL", f"sqlite:///{base_dir / 'rule_based_chatbot.db'}"
    )
    admin_username = admin_username or os.getenv("ADMIN_USERNAME", "admin")
    admin_password = admin_password or os.getenv("ADMIN_PASSWORD", "admin123")
    secret_key = os.getenv("SESSION_SECRET", "change-me-in-production")
    # Default to False to support HTTP-only deployments (like IP-based student projects)
    session_secure = os.getenv("SESSION_SECURE", "false").lower() == "true"

    engine = build_engine(database_url)
    session_local = build_session_local(engine)
    init_db(engine)
    with session_local() as db:
        ensure_admin_user(db, admin_username, admin_password)

    app = FastAPI(title="Rule Based Chatbot", version="1.0.0")

    # Enable CORS for all origins (development only)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    static_dir = base_dir / "static"
    admin_dir = base_dir.parent / "admin"
    admin_index_path = admin_dir / "index.html"
    templates = Jinja2Templates(directory=str(base_dir / "templates"))
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    get_db = partial(db_session, session_local)

    def require_admin(request: Request) -> str:
        token = request.cookies.get("admin_session")
        if not token:
            raise HTTPException(status_code=401, detail="Authentication required")
        username = parse_session_token(secret_key=secret_key, token=token)
        if not username:
            raise HTTPException(status_code=401, detail="Invalid session")
        return username

    @app.get("/health")
    def health():
        return {"status": "ok", "mode": "rule_based"}

    @app.get("/", response_class=HTMLResponse)
    def home(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    @app.get("/admin")
    @app.get("/admin/")
    def admin_dashboard():
        if not admin_index_path.is_file():
            raise HTTPException(status_code=404, detail="Admin dashboard not found")
        return FileResponse(admin_index_path)

    @app.post("/api/chat/ask")
    def ask(payload: AskRequest, db: Session = Depends(get_db)):
        normalized_query = normalize_text(payload.message)
        exact = db.scalar(
            select(QnA).where(func.lower(QnA.question) == normalized_query)
        )
        if exact:
            return {"type": "answer", "answer": exact.answer}

        candidates = db.scalars(select(QnA)).all()
        ranked = sorted(
            (
                {
                    "id": row.id,
                    "question": row.question,
                    "score": similarity_score(payload.message, row.question),
                }
                for row in candidates
            ),
            key=lambda x: x["score"],
            reverse=True,
        )

        # Filter for matches with 80% or higher similarity
        suggestions = [{"id": item["id"], "question": item["question"]} for item in ranked if item["score"] >= 0.8]
        
        # Log the interaction
        if suggestions:
            bot_response = f"Suggestions: {', '.join(s['question'] for s in suggestions)}"
        else:
            bot_response = "Please contact the FYJC center as I'm unable to help with your query"
        
        log_entry = ChatLog(
            user_message=payload.message,
            bot_response=bot_response
        )
        db.add(log_entry)
        db.commit()

        if not suggestions:
            return {
                "type": "no_match",
                "message": "Please contact the FYJC center as I'm unable to help with your query"
            }
        
        return {
            "type": "suggestions",
            "suggestions": suggestions,
        }

    @app.post("/api/chat/select")
    def select_suggestion(payload: SelectRequest, db: Session = Depends(get_db)):
        record = db.get(QnA, payload.qna_id)
        if not record:
            raise HTTPException(status_code=404, detail="Suggestion not found")
        # Log the interaction
        log_entry = ChatLog(
            user_message=f"[Selection ID: {payload.qna_id}]",
            bot_response=record.answer
        )
        db.add(log_entry)
        db.commit()

        return {"type": "answer", "answer": record.answer}

    @app.post("/api/admin/login")
    def admin_login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
        admin = authenticate_admin(db, payload.username, payload.password)
        if not admin:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_session_token(secret_key=secret_key, username=admin.username)
        response.set_cookie(
            "admin_session",
            token,
            httponly=True,
            samesite="lax",
            secure=session_secure,
        )
        return {"username": admin.username}

    @app.post("/api/admin/logout")
    def admin_logout(response: Response):
        response.delete_cookie("admin_session")
        return {"ok": True}

    @app.get("/api/admin/me")
    def admin_me(username: str = Depends(require_admin)):
        return {"username": username}

    @app.get("/api/admin/qna")
    def list_qna(
        _: str = Depends(require_admin),
        db: Session = Depends(get_db),
    ):
        rows = db.scalars(select(QnA).order_by(QnA.id.desc())).all()
        return [{"id": row.id, "question": row.question, "answer": row.answer} for row in rows]

    @app.post("/api/admin/qna", status_code=201)
    def create_qna(
        payload: QnAInput,
        _: str = Depends(require_admin),
        db: Session = Depends(get_db),
    ):
        record = QnA(question=payload.question, answer=payload.answer)
        db.add(record)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Question already exists")
        db.refresh(record)
        return {"id": record.id, "question": record.question, "answer": record.answer}

    @app.put("/api/admin/qna/{qna_id}")
    def update_qna(
        qna_id: int,
        payload: QnAInput,
        _: str = Depends(require_admin),
        db: Session = Depends(get_db),
    ):
        record = db.get(QnA, qna_id)
        if not record:
            raise HTTPException(status_code=404, detail="Q&A not found")
        record.question = payload.question
        record.answer = payload.answer
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=409, detail="Question already exists")
        db.refresh(record)
        return {"id": record.id, "question": record.question, "answer": record.answer}

    @app.delete("/api/admin/qna/{qna_id}", status_code=204)
    def delete_qna(
        qna_id: int,
        _: str = Depends(require_admin),
        db: Session = Depends(get_db),
    ):
        record = db.get(QnA, qna_id)
        if not record:
            raise HTTPException(status_code=404, detail="Q&A not found")
        db.delete(record)
        db.commit()
        return Response(status_code=204)

    @app.get("/api/admin/logs")
    def list_logs(
        _: str = Depends(require_admin),
        db: Session = Depends(get_db),
    ):
        rows = db.scalars(select(ChatLog).order_by(ChatLog.timestamp.desc())).all()
        return [
            {
                "id": row.id,
                "user_message": row.user_message,
                "bot_response": row.bot_response,
                "timestamp": row.timestamp.isoformat(),
            }
            for row in rows
        ]

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=True)
