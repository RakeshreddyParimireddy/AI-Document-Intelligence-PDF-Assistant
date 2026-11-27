# Deploying DocuMind (free)

| Part | Where | Cost |
|---|---|---|
| Database (PostgreSQL + pgvector) | [Neon](https://neon.tech) | Free |
| Backend (FastAPI, Docker) | [Render](https://render.com) | Free web service (0.1 CPU, 512 MB memory) |
| Frontend (Next.js) | [Vercel](https://vercel.com) | Free (Hobby) |

```
Browser ──> Vercel (frontend) ──> Render (backend API) ──> Neon (database)
                                        └──> Gemini API (answers, summaries, extraction)
```

Do the steps in order: each one gives you something the next one needs.
Keep a notepad open for the values marked 📋. **Never paste them into the repository or a chat.**

---

## Step 1 — Database on Neon

1. Sign up at **neon.tech** (you can use your GitHub account).
2. Create a project: name `documind`, Postgres version 16 or newer, a region near you. Remember the region.
3. On the project dashboard click **Connect**.
   Turn **Connection pooling OFF** and copy the connection string.
   📋 It looks like `postgresql://neondb_owner:xxxx@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require`
   — this is your **DATABASE_URL**. Treat it like a password.

You don't need to create tables or turn on pgvector: the backend does that when it starts.

## Step 2 — Backend on Render

The file [`render.yaml`](render.yaml) already describes the backend (Docker, free plan, health check,
settings), so Render sets most things up by itself.

1. **Region:** in `render.yaml`, `region:` must be the Render region closest to your Neon region
   (it can't be changed later). A far-away database makes every request slow.

   | Neon region | Render `region:` |
   |---|---|
   | US West (Oregon) | `oregon` |
   | US East (Ohio) | `ohio` |
   | US East (N. Virginia) | `virginia` |
   | Europe (Frankfurt, London) | `frankfurt` |
   | Asia Pacific (Singapore, Sydney, Mumbai…) | `singapore` |

   If you change it, commit and push before the next step.
2. Sign up at **render.com** with your GitHub account.
3. In the Render dashboard click **New → Blueprint**, connect GitHub if asked, and pick this repository
   (if it isn't listed, click *Configure GitHub* and give Render access to it).
4. Render reads `render.yaml` and shows the service **documind-api**. Give the Blueprint a name (e.g. `documind`)
   and fill in the values it asks for:

   | Name | Value |
   |---|---|
   | `DATABASE_URL` | 📋 from step 1 |
   | `LLM_API_KEY` | 📋 your free Gemini API key (see below) |
   | `CORS_ORIGINS` | `http://localhost:3000` for now (changed in step 4) |

   You don't type a `JWT_SECRET`: Render generates a strong random one.
   `LLM_PROVIDER` is preset to `gemini`.

   **Getting a free Gemini key:** go to **aistudio.google.com/apikey**, sign in with a Google account,
   click **Create API key**, and copy it with the **Copy key** button. No card needed.
   New keys are "auth keys" starting with `AQ.` (older keys start with `AIza`); both work.
5. Click **Deploy Blueprint**. Open the service to watch the **Logs**; the first build takes ~5 minutes.
6. Check it: at the top of the service page is its address, 📋 like `https://documind-api.onrender.com`
   (Render may add letters if the name is taken). Open `<that address>/api/health`
   → `{"status":"ok","database":"connected","pgvector":true}`. This is your **backend URL**.

From now on, every push to `main` that changes `backend/` is deployed automatically — but only after the GitHub CI checks pass.

## Step 3 — Frontend on Vercel

1. Sign up at **vercel.com** with your GitHub account.
2. **Add New → Project** → import this repository.
3. Set **Root Directory** to `frontend` (click Edit). Framework: Next.js (detected automatically).
4. Under **Environment Variables** add:
   `NEXT_PUBLIC_API_URL` = 📋 your backend URL from step 2 (e.g. `https://documind-api.onrender.com`)
5. Click **Deploy**. When it's done you get 📋 your **live link**, like `https://documind-xxxx.vercel.app`.

Vercel redeploys the frontend by itself on every push to `main`.

## Step 4 — Connect them (CORS)

The backend only answers browsers coming from addresses it trusts.
In Render → your service → **Environment**, edit `CORS_ORIGINS` and set it to 📋 your Vercel link —
you can keep localhost too: `https://documind-xxxx.vercel.app,http://localhost:3000` — then
**Save, rebuild, and deploy**.

## Step 5 — Try the live site

Open your Vercel link → **Create account** → upload `samples/sample-invoice.pdf` →
wait for **Ready** → ask *"What is the total amount due?"* → you should get **$14,850.00** with a **p. 1** citation.

---

## Good to know

- **Sleeping:** the free backend goes to sleep after 15 minutes without visitors, and Neon pauses an idle database.
  The first visit after that takes about a minute — normal for free hosting. (Render's free 750 hours a month
  are enough to run one service all month.)
- **Small CPU, so PDFs are limited to 30 pages.** The free plan gets 0.1 of a CPU. Measured under the free plan's
  exact limits: a 30-page PDF takes about **2½ minutes** to process (a few pages: seconds); several uploads are
  processed one after another; and questions keep answering in **about 1 second** meanwhile.
  Longer PDFs are refused with a clear message.
- **Want bigger PDFs?** Render's **Starter** plan ($7/month) has 5× the CPU and never sleeps. Switch in the service's
  settings, then raise `MAX_PDF_PAGES` in **Environment** — no code changes needed.
- **Memory:** tested under the exact 512 MB limit with two 30-page PDFs uploaded at once: at most ~350 MB used.
- **Gemini free tier — privacy:** Google may use text sent on the free tier to improve its products, and human
  reviewers may read it. That's why the upload box says *"Demo app: please don't upload private or sensitive
  documents"*. Use the sample PDFs for demos.
- **Gemini free tier — limits:** it allows only a limited number of requests per minute and per day. When the limit
  is hit, users see *"The AI is busy right now (free plan limit). Please try again in a minute."*
- **Using Claude instead (paid):** set `LLM_PROVIDER` to `claude` and `LLM_API_KEY` to a Claude key in Render →
  Environment. Set a **monthly spend limit** in console.anthropic.com first: anyone with the link can ask questions.
- **PDF files are not stored on the server.** After a PDF is processed, its text, chunks and vectors live
  in the database and the file is deleted — free hosting deletes files on every restart anyway.
- **Never** put real secrets in the repository: they live only in Neon, Render and Vercel.

## Something's wrong?

| Problem | Fix |
|---|---|
| Website says it can't reach the server / "Failed to fetch" | The backend may be waking up — wait a minute and retry. Otherwise `CORS_ORIGINS` (step 4) must exactly match the Vercel link, starting with `https://`. Also check `NEXT_PUBLIC_API_URL` in Vercel, then **Redeploy** (Vercel only reads it at build time). |
| `/api/health` shows `"database":"unavailable"` | Check `DATABASE_URL` in Render → Environment (copy it again from Neon). |
| Deploy failed on Render | Open the service's **Logs** / **Events** — the last red lines say why. |
| A push didn't deploy | Render waits for the GitHub CI checks to pass, and only deploys changes in `backend/`. Check the **Actions** tab on GitHub. |
| Answers say "The AI isn't set up on this server yet" | Add `LLM_API_KEY` in Render → Environment. |
| Answers say "The AI service failed" | The key may be wrong, or the model name invalid: check `LLM_API_KEY` (and `LLM_MODEL`, if you set one) and the Render **Logs**. |
| Deploy fails with "LLM_MODEL=… doesn't match LLM_PROVIDER=…" | Remove `LLM_MODEL` (or set a model of the chosen provider). |
