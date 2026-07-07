# NetOps AI Sentinel — Code Conventions

This document defines the conventions for this codebase. Read it before writing any new file.

---

## Project layout rules

- `api/` — FastAPI route files only. No business logic. One file per domain: `tickets.py`, `anomalies.py`, `chat.py`, `rca.py`.
- `services/` — All business logic lives here. Routes call services; services call repositories and utils.
- `repository/` — All database queries. Services call repositories; routes never touch the DB directly.
- `utils/` — Stateless helper functions only. No side effects, no DB calls.
- `prompts/` — All LLM prompt templates as `.jinja2` files. Never hardcode prompt strings in Python.
- `pipelines/` — ETL jobs: `ingest_tickets.py`, `ingest_logs.py`, `embed_docs.py`. Run on schedule or manually.
- `scripts/` — One-off developer tools: `seed_db.py`, `rebuild_index.py`, `export_rca.py`.

---

## Python style

- Python 3.11+
- Type hints on every function signature — no bare `def foo(x):`
- Pydantic models for all request/response shapes
- `snake_case` for variables, functions, files and folders
- `PascalCase` for class names
- Constants in `UPPER_SNAKE_CASE` in `config/`
- Max line length: 100 characters

---

## LLM calls

- All LLM calls go through `services/llm_service.py` — never call the Anthropic/OpenAI SDK directly from routes or other services
- Always wrap LLM calls in `tenacity` retry logic (already in requirements)
- Log the prompt, model, and token usage for every call
- Use structured output (JSON mode or function calling) wherever the output needs to be parsed

---

## PDF handling

- **Ingestion (RAG)**: use `pdfplumber` — it handles layout-aware extraction from telecom docs
- **Generation (RCA reports)**: use `reportlab.platypus` with `SimpleDocTemplate` — see `utils/pdf_reporter.py`
- Never use `PyPDF2` — it is deprecated

## Prompt templates

- All prompts live in `prompts/` as `.jinja2` files
- Subfolder per use case: `prompts/rca/`, `prompts/classifier/`, `prompts/chat/`
- Variable names in templates use `{{ double_braces }}`
- Every template has a comment block at the top describing its inputs and expected output format

---

## Environment variables

- All config comes from `.env` via `python-dotenv`
- Never hardcode API keys, paths, or thresholds in source files
- Reference `.env.example` for the full list of required variables
- Load config once in `config/settings.py` using Pydantic `BaseSettings`

---

## Error handling

- Raise specific exceptions, not bare `Exception`
- Services raise domain exceptions (e.g. `TicketNotFoundError`)
- API routes catch service exceptions and return appropriate HTTP status codes
- All external calls (LLM APIs, DB, file I/O) wrapped in try/except with logging

---

## Testing

- Mirror `services/` structure in `tests/`: `test_ticket_service.py`, `test_rag_service.py`, etc.
- Use `pytest`
- Mock all external calls (LLM APIs, DB) in unit tests
- Integration tests in `tests/integration/` — these are allowed to hit the real DB

---

## Git

- Branch naming: `feat/`, `fix/`, `chore/` prefix — e.g. `feat/rca-pdf-generator`
- Commit messages: imperative present tense — "Add RCA PDF template" not "Added RCA PDF"
- Never commit `.env`, model `.pkl` files, or FAISS index files — all in `.gitignore`