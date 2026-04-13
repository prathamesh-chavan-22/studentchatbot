import os
import uuid
import time
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, field_validator
import asyncio
from loguru import logger

from contextlib import asynccontextmanager
from app.bot import SimilarityBot
from app.moderation import ContentModerator
from app.exceptions import (
    BotError,
    EmptyInputError,
    InputTooLongError,
    ValidationError,
    ModelLoadError,
    KnowledgeBaseError,
    InferenceError,
    SearchError,
    QAFileError,
    ContentModerationError,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "intfloat/multilingual-e5-base")
QA_JSON_PATH = os.getenv("QA_JSON_PATH", "questions_answers.json")
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.85"))

FALLBACK_MESSAGES = {
    "en": os.getenv(
        "FALLBACK_MESSAGE_EN",
        "I'm sorry, I couldn't find a close match for your question. Questions? Please contact support at: support@mahafyjcadmissions.in",
    ),
    "mr": os.getenv(
        "FALLBACK_MESSAGE_MR",
        "क्षमस्व, तुमच्या प्रश्नाशी जुळणारे उत्तर सापडले नाही. काही प्रश्न असल्यास, कृपया या ईमेलवर संपर्क करा: support@mahafyjcadmissions.in",
    ),
    "hi": os.getenv(
        "FALLBACK_MESSAGE_HI",
        "क्षमा करें, मुझे आपके प्रश्न का कोई सटीक उत्तर नहीं मिला। अधिक जानकारी के लिए कृपया support@mahafyjcadmissions.in पर संपर्क करें।",
    ),
    "hinglish": os.getenv(
        "FALLBACK_MESSAGE_HINGLISH",
        "Maaf karna, mujhe aapke sawaal ka sahi jawab nahi mila. Agar aapko madad chahiye toh email karein: support@mahafyjcadmissions.in",
    ),
}

# ---------------------------------------------------------------------------
# Globals
# ---------------------------------------------------------------------------
bot: SimilarityBot | None = None
moderator = ContentModerator()

# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: initialize bot on startup, shut down on exit."""
    global bot
    logger.info("Application startup — initializing SimilarityBot...")
    try:
        bot = SimilarityBot(
            model_name=EMBEDDING_MODEL,
            qa_json_path=QA_JSON_PATH,
            threshold=SIMILARITY_THRESHOLD,
            fallback_messages=FALLBACK_MESSAGES,
        )
        logger.info("SimilarityBot initialized successfully.")
    except (ModelLoadError, QAFileError) as exc:
        logger.critical(f"Fatal: failed to initialize bot: {exc}")
        # Don't raise — allow health endpoint to still work
        bot = None
    except Exception as exc:
        logger.critical(f"Unexpected fatal error during startup: {exc}", exc_info=True)
        bot = None

    yield

    # Cleanup
    if bot is not None:
        logger.info("Application shutdown — stopping bot batcher...")
        try:
            await bot.shutdown()
        except Exception as exc:
            logger.error(f"Error during bot shutdown: {exc}")
        logger.info("Application shutdown complete.")


app = FastAPI(title="Multilingual Semantic Bot", version="1.1.0", lifespan=lifespan)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Static files and templates
# ---------------------------------------------------------------------------
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=500, min_length=1)
    history: list[dict[str, str]] = Field(default_factory=list)

    @field_validator("message")
    @classmethod
    def message_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message cannot be empty or whitespace-only")
        return v.strip()


class ChatResponse(BaseModel):
    answer: str
    match_score: float | None = None
    match_id: str | None = None
    detected_lang: str | None = None
    error: str | None = None


class ErrorResponse(BaseModel):
    detail: str
    error_code: str | None = None
    request_id: str | None = None


# ---------------------------------------------------------------------------
# Middleware — request ID & timing
# ---------------------------------------------------------------------------

@app.middleware("http")
async def add_request_id_and_log(request: Request, call_next):
    """Attach a unique request ID and log timing for every request."""
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id

    start_time = time.monotonic()
    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception:
        elapsed = time.monotonic() - start_time
        logger.error(
            f"Request {request_id} failed after {elapsed:.3f}s: "
            f"{request.method} {request.url.path}",
            exc_info=True,
        )
        raise
    finally:
        elapsed = time.monotonic() - start_time
        logger.info(
            f"Request {request_id} completed: {request.method} {request.url.path} "
            f"in {elapsed:.3f}s"
        )


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    """Return a 400 with field-level validation errors."""
    request_id = getattr(request.state, "request_id", "unknown")
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []))
        msg = error.get("msg", "Invalid input")
        errors.append({"field": field, "message": msg})

    logger.warning(
        f"Validation error on request {request_id}: {errors}"
    )
    return JSONResponse(
        status_code=400,
        content={
            "detail": "Invalid request payload",
            "errors": errors,
            "request_id": request_id,
        },
    )


@app.exception_handler(EmptyInputError)
async def empty_input_handler(request: Request, exc: EmptyInputError):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(f"Empty input on request {request_id}")
    return JSONResponse(
        status_code=400,
        content={
            "detail": "Please enter a question.",
            "error_code": exc.code,
            "request_id": request_id,
        },
    )


@app.exception_handler(InputTooLongError)
async def input_too_long_handler(request: Request, exc: InputTooLongError):
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(f"Input too long on request {request_id}")
    return JSONResponse(
        status_code=400,
        content={
            "detail": exc.user_message,
            "error_code": exc.code,
            "request_id": request_id,
        },
    )


@app.exception_handler(BotError)
async def bot_error_handler(request: Request, exc: BotError):
    """Catch-all for domain-specific bot errors."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        f"Bot error on request {request_id}: [{exc.code}] {exc}"
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": exc.user_message,
            "error_code": exc.code,
            "request_id": request_id,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Last-resort handler — catches anything not handled above.
    NEVER leak internal details to the client.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.critical(
        f"Unhandled exception on request {request_id}: {exc}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An unexpected error occurred. Please try again later.",
            "error_code": "INTERNAL_ERROR",
            "request_id": request_id,
        },
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict:
    """
    Health check endpoint.

    Returns degraded status when the bot failed to initialize so
    that orchestrators can distinguish between 'bot down' and
    'process alive but bot broken'.
    """
    if bot is None:
        return {
            "status": "degraded",
            "bot": "not_initialized",
            "message": "The AI model or knowledge base failed to load",
        }
    if not getattr(bot, "_is_initialized", False):
        return {
            "status": "degraded",
            "bot": "not_ready",
            "message": "The bot is still initializing or the knowledge base is empty",
        }
    return {
        "status": "ok",
        "bot": "ready",
        "batcher_healthy": (
            bot.batcher.is_running if bot.batcher else False
        ),
    }


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/api/chat")
async def chat(payload: ChatRequest, request: Request) -> dict:
    """
    Process a user query and return the best matching answer.

    Error handling:
    - Input validation is done by Pydantic (ChatRequest model)
    - Content moderation runs before any inference
    - All bot errors are caught and translated to safe responses
    - Request ID is included for traceability
    """
    request_id = getattr(request.state, "request_id", "unknown")
    query = payload.message  # already stripped by validator

    logger.info(f"Request {request_id}: Received query: '{query[:80]}...'")

    # -- Safety Check: Content Moderation --------------------------------
    try:
        is_safe, violation_lang = moderator.is_appropriate(query)
    except Exception as exc:
        # Moderation itself failed — log and reject safely
        logger.error(
            f"Request {request_id}: Content moderation failed: {exc}"
        )
        raise ContentModerationError(
            "Unable to validate message content", original=exc
        ) from exc

    if not is_safe:
        logger.warning(
            f"Request {request_id}: Blocked inappropriate query (lang={violation_lang})"
        )
        refusal = moderator.get_refusal_message(violation_lang)
        return {
            "answer": refusal,
            "blocked": True,
            "request_id": request_id,
        }

    # -- Ensure bot is ready ---------------------------------------------
    if bot is None:
        logger.error(
            f"Request {request_id}: Bot not initialized — cannot process query"
        )
        return {
            "answer": "The AI assistant is currently unavailable. Please try again later or contact support at: support@mahafyjcadmissions.in",
            "match_score": None,
            "match_id": None,
            "detected_lang": "en",
            "request_id": request_id,
        }

    if not getattr(bot, "_is_initialized", False):
        logger.warning(
            f"Request {request_id}: Bot not fully initialized — knowledge base may be empty"
        )
        return {
            "answer": "The knowledge base is currently being prepared. Please try again in a moment.",
            "match_score": None,
            "match_id": None,
            "detected_lang": "en",
            "request_id": request_id,
        }

    # -- Process query ----------------------------------------------------
    try:
        result = await bot.answer(query, payload.history)
    except EmptyInputError:
        # Shouldn't reach here due to Pydantic validation, but handle anyway
        return {
            "answer": "Please enter a question.",
            "match_score": None,
            "match_id": None,
            "detected_lang": "en",
            "request_id": request_id,
        }
    except (InferenceError, SearchError) as exc:
        logger.error(
            f"Request {request_id}: Bot processing error: {exc}",
            exc_info=True,
        )
        return {
            "answer": "Unable to process your question right now. Please try again.",
            "match_score": None,
            "match_id": None,
            "detected_lang": "en",
            "request_id": request_id,
        }
    except BotError as exc:
        logger.error(
            f"Request {request_id}: Bot error: [{exc.code}] {exc}",
            exc_info=True,
        )
        return {
            "answer": exc.user_message,
            "match_score": None,
            "match_id": None,
            "detected_lang": "en",
            "request_id": request_id,
        }
    except Exception as exc:
        logger.critical(
            f"Request {request_id}: Unexpected error processing query: {exc}",
            exc_info=True,
        )
        return {
            "answer": "An unexpected error occurred while processing your question. Please try again later or contact support.",
            "match_score": None,
            "match_id": None,
            "detected_lang": "en",
            "request_id": request_id,
        }

    return {
        "answer": result["answer"],
        "match_score": result.get("score"),
        "match_id": result.get("match_id"),
        "detected_lang": result.get("detected_lang"),
        "request_id": request_id,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
