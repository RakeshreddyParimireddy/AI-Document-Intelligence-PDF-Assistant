# Deploying DocuMind (free)

| Part | Where | Cost |
|---|---|---|
| Database (PostgreSQL + pgvector) | [Neon](https://neon.tech) | Free |
| Backend (FastAPI, Docker) | [Hugging Face Spaces](https://huggingface.co/spaces) | Free (CPU basic, 16 GB memory) |
| Frontend (Next.js) | [Vercel](https://vercel.com) | Free (Hobby) |

```
Browser ──> Vercel (frontend) ──> Hugging Face Space (backend API) ──> Neon (database)
                                              └──> Claude API (answers, summaries)
```

Do the steps in order: each one gives you something the next one needs.
Keep a notepad open for the values marked 📋.

---

## Step 1 — Database on Neon

1. Sign up at **neon.tech** (you can use your GitHub account).
2. Create a project: name `documind`, Postgres version 16 or newer, a region near you.
3. On the project dashboard click **Connect**.
   Turn **Connection pooling OFF** and copy the connection string.
   📋 It looks like `postgresql://neondb_owner:xxxx@ep-xxxx.region.aws.neon.tech/neondb?sslmode=require`
   — this is your **DATABASE_URL**. Treat it like a password.

You don't need to create tables or turn on pgvector: the backend does that when it starts.

## Step 2 — Backend on Hugging Face Spaces

1. Sign up at **huggingface.co**.
2. Click your picture → **New Space**:
   - Space name: `documind-api`
   - SDK: **Docker** → template **Blank**
   - Hardware: **CPU basic (free)**
   - Visibility: **Public** (the website must be able to reach the API; your code and secrets stay protected — secrets are never shown publicly)
3. In the Space, open **Settings → Variables and secrets** and add these as **New secret**:

   | Name | Value |
   |---|---|
   | `DATABASE_URL` | 📋 from step 1 |
   | `JWT_SECRET` | a long random string — make one with `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
   | `LLM_API_KEY` | your Claude API key (from console.anthropic.com) |
   | `CORS_ORIGINS` | `http://localhost:3000` for now (changed in step 4) |

   Optional, as **New variable**: `LLM_MODEL` = `claude-haiku-5-5` (much cheaper than the default Opus).
4. Create an access token so GitHub can upload the code: click your picture → **Settings → Access Tokens → Create new token** → type **Write** → name `github-deploy`.
   📋 Copy the token (starts with `hf_`).
5. In **GitHub**, open your repository → **Settings → Secrets and variables → Actions**:
   - **Secrets** tab → **New repository secret**: name `HF_TOKEN`, value = 📋 the `hf_...` token
   - **Variables** tab → **New repository variable**: name `HF_SPACE`, value = `<your-hf-username>/documind-api`
6. Deploy: GitHub → **Actions** → **CI** → **Run workflow** (on `main`).
   When the 3 jobs are green, the Space starts building (watch it in the Space's **Logs** tab; the first build takes ~5–10 minutes).
7. Check it: open 📋 `https://<your-hf-username>-documind-api.hf.space/api/health`
   → `{"status":"ok","database":"connected","pgvector":true}`.
   This address is your **backend URL**.

From now on, every push to `main` that passes the tests deploys the backend automatically.

## Step 3 — Frontend on Vercel

1. Sign up at **vercel.com** with your GitHub account.
2. **Add New → Project** → import this repository.
3. Set **Root Directory** to `frontend` (click Edit). Framework: Next.js (detected automatically).
4. Under **Environment Variables** add:
   `NEXT_PUBLIC_API_URL` = 📋 your backend URL from step 2 (e.g. `https://you-documind-api.hf.space`)
5. Click **Deploy**. When it's done you get 📋 your **live link**, like `https://documind-xxxx.vercel.app`.

Vercel redeploys the frontend by itself on every push to `main`.

## Step 4 — Connect them (CORS)

The backend only answers browsers coming from addresses it trusts.
In the Hugging Face Space → **Settings → Variables and secrets**, edit `CORS_ORIGINS` and set it to
📋 your Vercel link, e.g. `https://documind-xxxx.vercel.app` — you can keep localhost too:
`https://documind-xxxx.vercel.app,http://localhost:3000`.
The Space restarts by itself (about a minute).

## Step 5 — Try the live site

Open your Vercel link → **Create account** → upload `samples/sample-invoice.pdf` →
wait for **Ready** → ask *"What is the total amount due?"* → you should get **$14,850.00** with a **p. 1** citation.

---

## Good to know

- **Sleeping:** a free Space goes to sleep after ~48 hours without visitors, and Neon pauses an idle database.
  The first visit after that takes about a minute to wake up — normal for free hosting.
- **Your Claude bill:** anyone with the link can create an account and ask questions on your API key.
  In **console.anthropic.com → Billing / Limits**, set a **monthly spend limit** (for example $5),
  and consider `LLM_MODEL=claude-haiku-5-5` for the live demo.
- **PDF files are not stored on the server.** After a PDF is processed, its text, chunks and vectors live
  in the database and the file is deleted — free hosting deletes files on every restart anyway.
- **Never** put real secrets in the repository: they live only in Neon, the Space's secrets,
  GitHub secrets and Vercel environment variables.

## Something's wrong?

| Problem | Fix |
|---|---|
| Website says it can't reach the server / "Failed to fetch" | `CORS_ORIGINS` (step 4) must exactly match the Vercel link, starting with `https://`. Also check `NEXT_PUBLIC_API_URL` in Vercel, then **Redeploy** (Vercel only reads it at build time). |
| `/api/health` shows `"database":"unavailable"` | Check `DATABASE_URL` in the Space secrets (copy it again from Neon). |
| Space shows "Build error" / "Runtime error" | Open the Space's **Logs** tab — the last red lines say why. |
| "Deploy backend" job is skipped in Actions | The `HF_SPACE` variable is missing (step 2.5). |
| "Deploy backend" job fails with 401/403 | The `HF_TOKEN` secret is wrong or isn't a **Write** token. |
| Answers say "The AI is not configured" | Add `LLM_API_KEY` to the Space secrets. |
