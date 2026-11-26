# AGENTS.md — How AI agents should work on this project

## About the developer
- I am a beginner learning to code. Explain what you did in simple words after each task.
- I work on Windows with VS Code. Give terminal commands that work in the VS Code terminal.

## Source of truth
- Follow `PLAN.md`. Do not add features that are not in the plan unless I ask.
- Work on ONE milestone at a time. Stop when it is done and tell me how to test it.

## Coding rules
- Backend: Python FastAPI in `backend/`. Routes in `backend/app/routers/`, logic in `backend/app/services/`.
- All LLM calls and prompts live in `backend/app/services/llm.py` only.
- Frontend: Next.js + TypeScript + Tailwind in `frontend/`. All backend calls go through `frontend/lib/api.ts`.
- Read secrets (LLM key, DB URL, JWT secret) from `.env` only. Keep `.env` in `.gitignore`; update `.env.example` when adding a new setting.
- Use clear names, short comments where logic is not obvious, and simple readable code.
- In tests, mock the LLM so tests run without an API key.

## After each milestone
1. Make sure everything runs with no errors.
2. Tell me exactly how to test it (URLs, buttons, sample PDF to use).
3. Suggest a git commit message.

## Agent team roles (only when using agent teams)
- **Backend agent** — `backend/` only: database, RAG pipeline, APIs, tests.
- **Frontend agent** — `frontend/` only: pages, components.
- **Reviewer agent** — reviews changes, runs tests, checks security (auth, file upload limits, no leaked keys). Does not write features.
- Agree on API shapes in `backend/app/schemas.py` before the frontend uses them.
