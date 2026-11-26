# AI Document Intelligence & PDF Assistant — Project Plan

## 1. Goal
A web app where users upload PDFs and then:
- **Ask questions** and get answers with **source citations** (document name + page number)
- **Summarize** a document (short summary + key points)
- **Extract information** (dates, names, amounts, key terms) into a clean table / JSON
- Chat across **one or many documents**

Design inspiration: "TalkPDF Dashboard – Chat with Documents" (Dribbble) — left sidebar with documents, chat in the middle, PDF/source preview on the right.

## 2. Tech Stack
| Part         | Choice | Resume keywords it adds |
|--------------|--------|--------------------------|
| Frontend     | Next.js + React + TypeScript + Tailwind CSS | React, Next.js, TypeScript |
| Backend      | Python FastAPI | Python, FastAPI, REST API |
| Database     | PostgreSQL + **pgvector** extension | PostgreSQL, Vector Database |
| PDF reading  | PyMuPDF (fitz) | PDF Parsing |
| Embeddings   | sentence-transformers (free, runs locally) | Embeddings, NLP |
| LLM          | One LLM API (Claude or OpenAI) — key stored in `.env` | LLM, Generative AI, Prompt Engineering |
| Auth         | JWT login (email + password, hashed with bcrypt) | JWT Authentication |
| Testing      | pytest | Unit Testing |
| DevOps       | Docker + docker-compose, GitHub Actions | Docker, CI/CD |
| Deploy       | Frontend on Vercel, backend + DB on Render/Railway (or similar) | Cloud Deployment |

## 3. How RAG works in this app (simple version)
1. **Upload** → read the PDF text page by page.
2. **Chunk** → split text into small pieces (~500–800 characters, with some overlap), remembering the page number.
3. **Embed** → turn each chunk into a vector (list of numbers that represents its meaning).
4. **Store** → save chunks + vectors in PostgreSQL (pgvector).
5. **Ask** → turn the user's question into a vector, find the most similar chunks.
6. **Answer** → send the question + those chunks to the LLM, ask it to answer ONLY from them and cite pages.

## 4. Folder Structure
```
documind/
├── PLAN.md  AGENTS.md  CLAUDE.md  README.md
├── docker-compose.yml          # postgres(pgvector) + backend + frontend
├── .env.example                # LLM_API_KEY=, DATABASE_URL=, JWT_SECRET=
├── .github/workflows/ci.yml    # run tests on every push
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py           # reads .env
│   │   ├── database.py
│   │   ├── models.py           # tables
│   │   ├── schemas.py
│   │   ├── auth.py             # register/login, JWT
│   │   ├── routers/            # auth.py, documents.py, chat.py, insights.py
│   │   └── services/
│   │       ├── pdf_reader.py   # extract text per page
│   │       ├── chunker.py
│   │       ├── embeddings.py
│   │       ├── retriever.py    # vector search
│   │       └── llm.py          # all LLM calls + prompts
│   ├── tests/
│   └── requirements.txt
└── frontend/
    ├── app/
    │   ├── login/  register/
    │   ├── page.tsx            # Dashboard (documents + stats)
    │   └── documents/[id]/     # Chat + summary + extraction for one doc
    ├── components/             # Sidebar, UploadBox, ChatWindow, CitationChip, SummaryCard, ExtractTable
    └── lib/api.ts
```

## 5. Database Tables
- **users**: id, email, password_hash, created_at
- **documents**: id, user_id → users, filename, pages, size_kb, status (processing/ready/failed), uploaded_at
- **chunks**: id, document_id → documents, page_number, content, embedding (vector)
- **chats**: id, user_id, title, created_at
- **chat_documents**: chat_id, document_id  (which docs a chat uses)
- **messages**: id, chat_id, role (user/assistant), content, citations (JSON), created_at
- **summaries**: id, document_id, summary, key_points (JSON), created_at

## 6. API Endpoints
Auth
- `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`

Documents
- `POST /api/documents/upload` — upload PDF (max 20 MB), process in background
- `GET /api/documents` — my documents
- `GET /api/documents/{id}` — details + status
- `DELETE /api/documents/{id}`

Chat (RAG)
- `POST /api/chats` — new chat with selected document ids
- `GET /api/chats`, `GET /api/chats/{id}/messages`
- `POST /api/chats/{id}/ask` — question → answer + citations `[{document, page, snippet}]`

Insights
- `POST /api/documents/{id}/summarize` — summary + key points
- `POST /api/documents/{id}/extract` — body: list of fields (e.g. "invoice date", "total amount") → JSON table
- `GET /api/dashboard/stats` — documents count, pages processed, questions asked

## 7. Pages
- **Login / Register**
- **Dashboard** — upload box (drag & drop), documents list with status, stats cards
- **Document workspace** — tabs: **Chat** | **Summary** | **Extract**
  - Chat shows answers with clickable citation chips (doc + page)
  - Summary shows short summary + key points
  - Extract: type field names → get a table, download as CSV
- **Multi-doc chat** — pick several documents and ask across them

## 8. Milestones (one at a time)
1. **Setup** — Docker Compose runs PostgreSQL with pgvector; FastAPI `GET /api/health` works.
2. **Auth** — register/login with JWT; protected routes.
3. **Upload + PDF reading** — upload a PDF, extract text per page, save document.
4. **Chunking + embeddings** — split text, create embeddings, store in pgvector.
5. **Retrieval** — endpoint that returns the top 5 relevant chunks for a question (test in /docs).
6. **RAG answers** — send chunks to LLM, return answer + citations; say "not found in the document" when the answer isn't there.
7. **Frontend skeleton** — Next.js, login/register pages, sidebar layout.
8. **Dashboard + upload UI** — drag & drop, status (processing → ready).
9. **Chat UI** — chat window, citation chips, chat history.
10. **Summarize + Extract** — tabs, CSV download.
11. **Multi-document chat**.
12. **Tests** — pytest for auth, upload, chunker, retrieval (mock the LLM in tests).
13. **CI/CD** — GitHub Actions runs tests on every push.
14. **Deploy** — live link.
15. **README + demo video** — architecture diagram, screenshots, features, how to run.

## 9. Rules
- Never commit the `.env` file or API keys.
- Limit upload size and file type (PDF only).
- Users can only see their own documents.

## 10. Definition of Done (each milestone)
- Runs without errors, I tested it myself, committed and pushed to GitHub.

## 11. Resume line (fill in real numbers at the end)
*Built an AI Document Intelligence platform using Python, FastAPI, RAG, LLMs, PostgreSQL (pgvector) and Next.js, enabling question answering with page-level citations, summarization and structured data extraction from PDFs; containerized with Docker and deployed with CI/CD via GitHub Actions.*
