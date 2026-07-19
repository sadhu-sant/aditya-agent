#!/usr/bin/env python3
"""
Aditya's HTTP API.

Run locally:      uvicorn server:app --reload
Run in Docker:     see Dockerfile
Deploy anywhere:   Render, Railway, Fly.io, Google Cloud Run, a VPS, etc.
                   -- see README.md for one-click deploy notes.

Once deployed, Aditya is reachable from anywhere via:
    POST /chat        {"session_id": "...", "message": "..."}
"""
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from aditya.agent import Aditya
from aditya.config import settings
from aditya.memory import clear_history, load_history, save_history

app = FastAPI(
    title=settings.NAME + " Agent API",
    description="A dynamic, tool-using AI agent -- accessible from anywhere.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = Aditya()


@app.get("/")
def root():
    """Serve the built-in chat webpage at the root URL."""
    return FileResponse("static/index.html")


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    reply: str
    session_id: str


def _check_api_key(x_api_key: str | None):
    if settings.API_KEY and x_api_key != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header")


@app.get("/health")
def health():
    return {"status": "ok", "agent": settings.NAME, "model": settings.MODEL}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, x_api_key: str | None = Header(default=None)):
    _check_api_key(x_api_key)
    history = load_history(req.session_id)
    reply, history = agent.run(history, req.message)
    save_history(req.session_id, history)
    return ChatResponse(reply=reply, session_id=req.session_id)


@app.post("/reset")
def reset(session_id: str = "default", x_api_key: str | None = Header(default=None)):
    _check_api_key(x_api_key)
    clear_history(session_id)
    return {"status": "cleared", "session_id": session_id}


@app.get("/history")
def history(session_id: str = "default", x_api_key: str | None = Header(default=None)):
    _check_api_key(x_api_key)
    return {"session_id": session_id, "messages": load_history(session_id)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host=settings.HOST, port=settings.PORT, reload=False)
