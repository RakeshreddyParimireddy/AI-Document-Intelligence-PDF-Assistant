# DocuMind — AI Document Intelligence & PDF Assistant

Upload PDFs, ask questions with page citations, summarize and extract data. See `PLAN.md`.

## Run it (Milestone 1)
Requires Docker Desktop.

```powershell
Copy-Item .env.example .env      # then edit the values in .env
docker compose up --build -d
```

- Health check: http://localhost:8000/api/health
- API docs: http://localhost:8000/docs

If port 8000 is already in use, set `BACKEND_PORT=8001` in `.env` and use 8001 in the URLs.

Stop with `docker compose down` (add `-v` to also delete the database data).
