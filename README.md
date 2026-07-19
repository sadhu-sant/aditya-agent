# Aditya 🤖

A dynamic, tool-using AI agent — chat with it from the terminal, or deploy it
as an HTTP API that's reachable from anywhere. No static HTML page here:
Aditya is a real backend service with memory and tools, built on
[LiteLLM](https://github.com/BerriAI/litellm) so it works with **any**
LLM provider (OpenAI, Anthropic/Claude, Groq, Gemini, Mistral, local Ollama
models, and 100+ more) just by changing one environment variable.

## Features

- **Provider-agnostic** — swap models/providers via `ADITYA_MODEL` + an API key, no code changes.
- **Tool use** — web search, calculator, current time, sandboxed file read/write. Easy to add more.
- **Persistent memory** — each conversation (`session_id`) is saved to disk and survives restarts.
- **Two interfaces** — a terminal CLI (`cli.py`) and an HTTP API (`server.py`) you can call from any client, app, or website.
- **Deploy anywhere** — Dockerfile included; works on Render, Railway, Fly.io, Cloud Run, a VPS, or your own machine.

## Project structure

```
aditya-agent/
├── aditya/
│   ├── __init__.py
│   ├── config.py      # env-var driven settings
│   ├── memory.py       # per-session conversation persistence
│   ├── tools.py         # built-in tools + their function-calling schemas
│   └── agent.py          # the agent loop (calls the model, runs tools, loops)
├── cli.py               # terminal chat client
├── server.py             # FastAPI HTTP API
├── requirements.txt
├── Dockerfile
├── .env.example
└── README.md
```

## 1. Setup

```bash
git clone https://github.com/<your-username>/aditya-agent.git
cd aditya-agent
python -m venv .venv && source .venv/bin/activate   # optional but recommended
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
- Set **one** provider's API key. Default is `GROQ_API_KEY` — get a free one at
  [console.groq.com/keys](https://console.groq.com/keys).
- Set `ADITYA_MODEL` to match that provider (defaults to `groq/llama-3.3-70b-versatile`).
  - Groq: `groq/llama-3.3-70b-versatile`
  - Local (Ollama, no key needed): `ollama/llama3`
  - OpenAI: `gpt-4o-mini`, `gpt-4o`, etc.
  - Anthropic: `anthropic/claude-sonnet-4-5-20250929`
  - Gemini: `gemini/gemini-2.0-flash`

Groq/Llama is the default on purpose: it's an open-weight model with no
branded consumer-assistant persona baked in, so Aditya's own identity (set
in the system prompt) is what users see — there's no "actually I'm ChatGPT /
Claude / Gemini" moment to worry about.

## 2. Chat from the terminal

```bash
python cli.py
```

```
Aditya ready. Model: gpt-4o-mini  (session: local)
Type 'exit' or Ctrl+C to quit.

you> What's 18234 * 88, and what's today's date?
Aditya> 18234 * 88 = 1,604,592. Today is 2026-07-19 (UTC).
```

Use `--session <name>` for a named, persisted conversation, and `--new` to
wipe a session's history and start fresh.

## 3. Run the API server

```bash
uvicorn server:app --reload
```

Then, from anywhere (curl, Postman, a frontend, another app):

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "demo", "message": "Explain quicksort in 2 sentences."}'
```

Response:

```json
{"reply": "Quicksort picks a pivot...", "session_id": "demo"}
```

Other endpoints: `GET /health`, `POST /reset?session_id=demo`,
`GET /history?session_id=demo`.

If you set `ADITYA_API_KEY` in `.env`, every request must include an
`X-API-Key` header matching it — do this before exposing the server publicly.

## 4. Deploy so it's reachable from anywhere

GitHub hosts your *code*; to get a live, always-on URL you need to run that
code somewhere. Easiest options, all using the included `Dockerfile`:

**Render / Railway / Fly.io (free tiers available)**
1. Push this repo to GitHub.
2. Create a new "Web Service" from your repo on the platform of choice.
3. It will detect the `Dockerfile` automatically (or set the start command
   to `uvicorn server:app --host 0.0.0.0 --port $PORT`).
4. Add your `OPENAI_API_KEY` (or chosen provider key), `ADITYA_MODEL`, and
   `ADITYA_API_KEY` as environment variables in the platform's dashboard.
5. Deploy — you'll get a public URL like `https://aditya.onrender.com`.

**Docker anywhere (VPS, Cloud Run, etc.)**

```bash
docker build -t aditya-agent .
docker run -p 8000:8000 --env-file .env aditya-agent
```

Once deployed, `POST https://your-url/chat` works from any device, app, or
website — that's what makes Aditya "accessible from anywhere," rather than
a static page that only runs in one browser tab.

## 5. Adding your own tools

Open `aditya/tools.py`:
1. Write a plain Python function that returns a string.
2. Add its JSON schema to `TOOL_SCHEMAS`.
3. Register the function in `TOOL_REGISTRY`.

The agent loop in `aditya/agent.py` picks up new tools automatically — no
other changes needed.

## Notes

- `web_search` uses DuckDuckGo's HTML endpoint and needs no API key; swap in
  a paid search API in `tools.py` if you want higher-quality results.
- `read_file` / `write_file` are sandboxed to the `workspace/` directory and
  cannot escape it.
- Conversation history is stored as JSON files under `sessions/` — swap
  `aditya/memory.py` for a real database (Postgres, Redis, etc.) if you need
  multi-instance deployments or higher scale.

## License

MIT — see `LICENSE`.
