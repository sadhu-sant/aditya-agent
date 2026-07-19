"""
Simple, dependency-free conversation memory.

Each session (a conversation thread, identified by a session_id you choose,
e.g. a user id or a random UUID from your frontend) is persisted as a JSON
file, so history survives process restarts without needing a database.
"""
import json
import os
import threading
from typing import Any

from .config import settings

_lock = threading.Lock()


def _path(session_id: str) -> str:
    safe_id = "".join(c for c in session_id if c.isalnum() or c in ("-", "_")) or "default"
    return os.path.join(settings.SESSIONS_DIR, f"{safe_id}.json")


def load_history(session_id: str) -> list[dict[str, Any]]:
    path = _path(session_id)
    if not os.path.exists(path):
        return []
    with _lock, open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_history(session_id: str, messages: list[dict[str, Any]]) -> None:
    path = _path(session_id)
    with _lock, open(path, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)


def clear_history(session_id: str) -> None:
    path = _path(session_id)
    if os.path.exists(path):
        os.remove(path)
