# Demo video script (about 2 minutes)

**Record with:** Windows **Snipping Tool** → *Record* (or `Win + Alt + R` with the Xbox Game Bar), or OBS Studio.
Browser at 100% zoom, full screen, a clean account. Upload the PDFs in `samples/` **before** recording
so you don't wait on camera — but keep one to upload live.

**Upload the video:** YouTube (set to *Unlisted*) or Loom, then paste the link at the top of `README.md`.

| Time | Show | Say (or put as captions) |
|---|---|---|
| 0:00–0:10 | The dashboard | "This is DocuMind — upload PDFs and ask questions about them, with answers that cite the exact page." |
| 0:10–0:25 | Drag `sample-handbook.pdf` onto the upload box; status goes *Processing → Ready* | "When I upload a PDF, the backend reads each page, splits it into chunks, and turns them into vectors stored in PostgreSQL with pgvector." |
| 0:25–0:55 | Open **sample-invoice.pdf** → Chat → ask *"What is the total amount due and when is it due?"*; click the **p. 1** citation chip | "Answers come only from the document. Each one has citation chips — clicking one shows the exact source text and page." |
| 0:55–1:05 | Ask *"Who is the CEO of the company?"* | "If the answer isn't in the document, it says so instead of making something up." |
| 1:05–1:20 | **Summary** tab → *Generate summary* | "Summary reads the whole document and gives a short summary plus key points." |
| 1:20–1:40 | **Extract** tab → add *Invoice date*, *Total amount*, *Sales contact* → Extract → **Download CSV**, open it | "Extract pulls structured fields into a table with page numbers — downloadable as CSV." |
| 1:40–1:55 | **Multi-doc chat** → select both PDFs → ask *"When is the invoice payment due, and how many vacation days do employees get?"* | "Multi-document chat answers across several PDFs at once, citing each document." |
| 1:55–2:10 | GitHub: README badge → **Actions** tab with green runs | "It's built with Next.js, FastAPI, pgvector and an LLM (Gemini or Claude), has 58 automated tests, and GitHub Actions tests and deploys it on every push." |

## Screenshots for the README

Take them with `Win + Shift + S`, save as PNG in `docs/screenshots/` with exactly these names:

| File | What to capture |
|---|---|
| `chat.png` | Document workspace, Chat tab: an answer with citation chips and the source panel open on the right |
| `dashboard.png` | Dashboard with stats cards and a few documents (Ready) |
| `summary.png` | Summary tab with a generated summary and key points |
| `extract.png` | Extract tab with a filled results table |

Tip: crop out the browser bars and anything private (like your email in the sidebar).
