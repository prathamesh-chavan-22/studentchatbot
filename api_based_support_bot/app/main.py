from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel, Field

import asyncio
from contextlib import asynccontextmanager
from typing import Any

from app.bot import FYJCSupportBot


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

bot = FYJCSupportBot()

# Task queue for non-blocking processing
chat_queue: asyncio.Queue = asyncio.Queue()

async def chat_worker():
    """Background worker to process chat queries sequentially from the queue."""
    while True:
        future, query, history = await chat_queue.get()
        try:
            # Process sync bot logic in a thread to keep worker responsive
            result = await asyncio.to_thread(bot.answer, query, history)
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)
        finally:
            chat_queue.task_done()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: launch the background chat worker
    asyncio.create_task(chat_worker())
    yield
    # Shutdown: nothing extra needed; worker will be cancelled automatically

app = FastAPI(title="FYJC Support Bot", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Log absolute paths for debugging server environment
print(f"DEBUG: BASE_DIR is {BASE_DIR}")
print(f"DEBUG: Templates directory is {BASE_DIR / 'templates'}")
print(f"DEBUG: Static directory is {BASE_DIR / 'static'}")

# Check if index.html exists
idx_path = BASE_DIR / "templates" / "index.html"
print(f"DEBUG: index.html exists: {idx_path.exists()}")


class ChatRequest(BaseModel):
    message: str = Field(..., max_length=500)
    history: list[dict[str, str]] = Field(default_factory=list)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    sample_faqs = bot._questions[:12]
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "sample_faqs": sample_faqs,
        },
    )


@app.post("/api/chat")
async def chat(payload: ChatRequest) -> dict:
    query = payload.message.strip()
    history = payload.history
    if not query:
        return {"answer": "Please type a question.", "sources": [], "used_groq": False}
    if len(query) > 500:
        return {"answer": "Query too long. Limit: 500 chars.", "sources": [], "used_groq": False}

    # Submit query and history to queue and wait for result
    loop = asyncio.get_running_loop()
    future = loop.create_future()
    await chat_queue.put((future, query, history))
    
    try:
        return await future
    except Exception as e:
        return {"answer": f"Error: {str(e)}", "sources": [], "used_groq": False}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
