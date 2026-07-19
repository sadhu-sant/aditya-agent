"""
Built-in tools for Aditya, defined in OpenAI's function-calling schema
(the de-facto standard that LiteLLM translates for every provider).

To add a new tool:
  1. Write a function with a plain (str) return value.
  2. Add its JSON schema to TOOL_SCHEMAS.
  3. Register it in TOOL_REGISTRY.
That's it -- the agent loop in agent.py will pick it up automatically.
"""
import ast
import operator
import os
import time
from datetime import datetime, timezone

import requests

from .config import settings

_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg, ast.UAdd: operator.pos, ast.FloorDiv: operator.floordiv,
}


def _safe_eval(node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Only numeric constants are allowed")
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("Unsupported expression")


def calculator(expression: str) -> str:
    try:
        result = _safe_eval(ast.parse(expression, mode="eval").body)
        return str(result)
    except Exception as e:
        return "Error evaluating expression: " + str(e)


def web_search(query: str, max_results: int = 5) -> str:
    try:
        resp = requests.post(
            "https://html.duckduckgo.com/html/",
            data={"q": query},
            headers={"User-Agent": "Mozilla/5.0 (AditaAgent/1.0)"},
            timeout=10,
        )
        resp.raise_for_status()
    except Exception as e:
        return "Web search failed: " + str(e)

    from html import unescape
    import re

    results = []
    for m in re.finditer(r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', resp.text):
        url, title = m.group(1), re.sub("<.*?>", "", unescape(m.group(2)))
        results.append("- " + title.strip() + " (" + url + ")")
        if len(results) >= max_results:
            break

    if not results:
        return "No results found."
    return "\n".join(results)


def get_current_time(timezone_name: str = "UTC") -> str:
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%d %H:%M:%S UTC")


def _safe_workspace_path(filename: str) -> str:
    base = os.path.abspath(settings.WORKSPACE_DIR)
    target = os.path.abspath(os.path.join(base, filename))
    if not target.startswith(base):
        raise ValueError("Path escapes workspace sandbox")
    return target


def read_file(filename: str) -> str:
    try:
        path = _safe_workspace_path(filename)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()[:20000]
    except Exception as e:
        return "Error reading file: " + str(e)


def write_file(filename: str, content: str) -> str:
    try:
        path = _safe_workspace_path(filename)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return "Wrote " + str(len(content)) + " characters to " + filename
    except Exception as e:
        return "Error writing file: " + str(e)


TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate a numeric arithmetic expression using plus minus times divide power percent double-slash operators. Use for any precise math.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "example: (2 plus 3) times 4 divided by 2"}
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the live web for current information, facts, or recent events.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "default": 5},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time (UTC).",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file from the agent's sandboxed workspace directory.",
            "parameters": {
                "type": "object",
                "properties": {"filename": {"type": "string"}},
                "required": ["filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write text content to a file in the agent's sandboxed workspace directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["filename", "content"],
            },
        },
    },
]

TOOL_REGISTRY = {
    "calculator": calculator,
    "web_search": web_search,
    "get_current_time": get_current_time,
    "read_file": read_file,
    "write_file": write_file,
}
