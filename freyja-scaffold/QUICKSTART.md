# FREYJA — Quick Start (Copy-Paste Edition)

Pick your path below. No thinking required.

---

## Path A: Try It Locally (No Docker)

**You need:** Python 3.11+ and Node.js 18+

### Step 1 — Backend

Open a terminal and paste:

```bash
cd freyja-scaffold/backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Leave it running. Open `http://localhost:8000/docs` in a browser to confirm it works.

### Step 2 — Frontend

Open a **second** terminal and paste:

```bash
cd freyja-scaffold/frontend
npm install
npm run dev
```

Leave it running. Open `http://localhost:3000` in a browser.

### Step 3 — AI Model

Make sure Ollama is installed, then:

```bash
ollama pull phi4-mini:latest
```

### Step 4 — Test

1. Go to `http://localhost:3000`
2. Sign up for an account
3. Start chatting

Done.

---

## Path B: Production (Docker)

**You need:** Docker + Docker Compose + a domain name (for HTTPS)

### Step 1 — Configure

```bash
cd freyja-scaffold/infra/docker
cp ../../.env.example .env
```

Edit `.env`:

```
SECRET_KEY= paste-a-64-character-random-string-here-now-seriously-do-it
```

*(Generate one: `openssl rand -hex 32`)*

If you want billing, also add your Stripe keys (optional for testing).

### Step 2 — Launch

```bash
docker compose up -d
```

Wait 30 seconds.

### Step 3 — Pull a Model

```bash
docker exec -it ollama ollama pull phi4-mini:latest
```

### Step 4 — Point Your Domain

Edit `freyja-scaffold/infra/caddy/Caddyfile`:

```
yourdomain.com {
    reverse_proxy backend:8000
}
```

Restart:

```bash
docker compose restart caddy
```

Caddy automatically gets HTTPS. No certbot, no manual steps.

### Step 5 — Test

Visit `https://yourdomain.com`. Sign up. Chat.

Done.

---

## One-Liner Health Checks

| What | Command |
|---|---|
| Backend alive? | `curl http://localhost:8000/health` |
| Ollama models? | `ollama list` |
| Docker logs | `docker compose logs -f backend` |
| Database | SQLite file at `backend/freyja.db` |

---

## What If Something Breaks?

| Symptom | Fix |
|---|---|
| "Connection refused" on :8000 | Backend isn't running. Did you `cd backend` first? |
| "No module named app" | Run from inside `backend/` directory |
| "Ollama not found" | Install Ollama or check `OLLAMA_BASE_URL` in `.env` |
| Blank page on :3000 | Frontend still building. Wait 10s, refresh |
| Stripe doesn't work | You didn't set Stripe keys in `.env` — optional for testing |

---

## Next

Read `README.md` for architecture details, API docs, and tier/billing logic.
