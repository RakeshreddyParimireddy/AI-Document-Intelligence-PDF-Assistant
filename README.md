# DocuMind — AI Document Intelligence & PDF Assistant

Upload PDFs, ask questions with page citations, summarize and extract data. See `PLAN.md`.

## Run it
Requires Docker Desktop and Node.js.

**1. Backend + database** (from the project folder):

```powershell
Copy-Item .env.example .env      # then edit the values in .env
docker compose up --build -d
```

- Health check: http://localhost:8000/api/health
- API docs: http://localhost:8000/docs

If port 8000 is already in use, set `BACKEND_PORT=8001` in `.env` and use 8001 in the URLs.

**2. Frontend** (in a second terminal):

```powershell
cd frontend
Copy-Item .env.example .env.local   # set NEXT_PUBLIC_API_URL to the backend address
npm install
npm run dev
```

Open http://localhost:3000

Stop the backend with `docker compose down` (add `-v` to also delete the database data).

## Run the tests
The backend has pytest tests for auth, upload, the chunker, retrieval and chat.
They use a separate `documind_test` database (your real data is never touched)
and a fake LLM, so **no API key is needed and nothing costs money**.

```powershell
docker compose up --build -d
docker compose exec backend pytest -v
```
