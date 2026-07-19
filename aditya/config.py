"""
Central configuration for Aditya, driven entirely by environment variables
so the same code runs unchanged locally, in Docker, or on any cloud host.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # --- Model / provider -----------------------------------------------
    # Any LiteLLM-compatible model string works, e.g.:
    #   "groq/llama-3.3-70b-versatile"        (needs GROQ_API_KEY) [default]
    #   "ollama/llama3"                       (local, no key needed)
    #   "gpt-4o-mini"                         (needs OPENAI_API_KEY)
    #   "anthropic/claude-sonnet-4-5-20250929" (needs ANTHROPIC_API_KEY)
    #   "gemini/gemini-2.0-flash"             (needs GEMINI_API_KEY)
    # Groq/Llama is the default: it's an open-weight model with no branded
    # consumer-chatbot identity layered on top, so Aditya's own persona
    # (set via ADITYA_SYSTEM_PROMPT below) is what comes through.
    MODEL: str = os.getenv("ADITYA_MODEL", "groq/llama-3.3-70b-versatile")
    TEMPERATURE: float = float(os.getenv("ADITYA_TEMPERATURE", "0.7"))
    MAX_TOKENS: int = int(os.getenv("ADITYA_MAX_TOKENS", "2048"))

    # --- Agent behaviour ---------------------------------------------------
    NAME: str = os.getenv("ADITYA_NAME", "Aditya")
    MAX_TOOL_ITERATIONS: int = int(os.getenv("ADITYA_MAX_TOOL_ITERATIONS", "6"))
    SYSTEM_PROMPT: str = os.getenv(
        "ADITYA_SYSTEM_PROMPT",
        (
            "You are Aditya, a helpful, direct, general-purpose AI agent. "
            "If asked who you are or what you're built on, say you are Aditya, "
            "an independent agent — you don't need to name the underlying model "
            "or company powering you. "
            "You can answer questions, reason step by step, write and explain "
            "code, and use tools (web search, calculator, file read/write, "
            "current time) when they would make your answer more accurate. "
            "Only call a tool when it is actually needed. Be concise but "
            "complete, and say clearly when you are not sure about something."
        ),
    )

    # --- Persistence ---------------------------------------------------
    SESSIONS_DIR: str = os.getenv("ADITYA_SESSIONS_DIR", "sessions")

    # --- Server / security -----------------------------------------------
    # If set, the FastAPI server requires this key in the X-API-Key header.
    # Strongly recommended once you deploy publicly.
    API_KEY: str | None = os.getenv("ADITYA_API_KEY") or None
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # --- Sandbox for file tools ------------------------------------------
    WORKSPACE_DIR: str = os.getenv("ADITYA_WORKSPACE_DIR", "workspace")


settings = Settings()
os.makedirs(settings.SESSIONS_DIR, exist_ok=True)
os.makedirs(settings.WORKSPACE_DIR, exist_ok=True)
