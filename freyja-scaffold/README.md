<!-- TAGNET README HEADER — Catppuccin Mocha — do not edit by hand -->
<div align="center">

[![License](https://img.shields.io/github/license/e404-tagnet/memory-scaffold?color=313244&labelColor=11111b&label=License&style=flat-square)](https://github.com/e404-tagnet/memory-scaffold/blob/main/LICENSE)
[![Status](https://img.shields.io/badge/Status-wip-f9e2af?labelColor=11111b&style=flat-square)](https://github.com/e404-tagnet/memory-scaffold/pulse)
[![Version](https://img.shields.io/github/v/release/e404-tagnet/memory-scaffold?color=313244&labelColor=11111b&label=Version&style=flat-square)](https://github.com/e404-tagnet/memory-scaffold/releases)
[![Repo](https://img.shields.io/badge/Repo-memory-scaffold-94e2d5?labelColor=11111b&style=flat-square&logo=github&logoColor=94e2d5)](https://github.com/e404-tagnet/memory-scaffold)
[![Tagnet](https://img.shields.io/badge/By-Tagnet-89dceb?labelColor=11111b&style=flat-square&logo=tag&logoColor=89dceb)](https://tagnet.dev)

</div>
<!-- TAGNET README HEADER — end -->

# FREYJA — Companion Chatbot Platform

A full-stack AI companion chatbot with user accounts, chat history, tiered access, Stripe billing, and optional voice (ElevenLabs). Built for self-hosting on commodity hardware or GPU pods.

## What's Included

- **Backend:** FastAPI + async SQLite + JWT auth + Stripe webhooks
- **Frontend:** Next.js + Tailwind (dark theme, mobile-friendly)
- **AI:** Ollama-compatible (local models, no API keys needed)
- **Billing:** Stripe checkout → auto-upgrades user tier
- **Deploy:** Docker Compose with Caddy reverse proxy + HTTPS


## 30-Second Start (Local Dev)

**Requirements:** Python 3.11+, Node.js 18+

### 1. Clone & Enter

```bash
cd freyja-scaffold/backend
```

### 2. Start the Backend

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Edit config (optional — defaults work out of the box)
cp ../.env.example .env

# Run
uvicorn app.main:app --reload --port 8000
```

Backend is now live at `http://localhost:8000`

Open `http://localhost:8000/docs` to see the API.

### 3. Start the Frontend (new terminal)

```bash
cd freyja-scaffold/frontend
npm install
npm run dev
```

Frontend is now live at `http://localhost:3000`

### 4. Pull a Model (Ollama)

```bash
ollama pull phi4-mini:latest
```

Done. Visit `http://localhost:3000`, sign up, and chat.


## Production Deploy (Docker)

**Requirements:** Docker + Docker Compose

### 1. Configure

```bash
cd freyja-scaffold/infra/docker
cp ../../.env.example .env
# Edit .env — set SECRET_KEY and any Stripe keys
```

### 2. Launch

```bash
docker compose up -d
```

### 3. Pull a Model

```bash
docker exec -it ollama ollama pull phi4-mini:latest
```

### 4. HTTPS (Caddy)

Edit `freyja-scaffold/infra/caddy/Caddyfile`:

```
yourdomain.com {
    reverse_proxy backend:8000
}
```

Restart Caddy:

```bash
docker compose restart caddy
```

Caddy auto-provisions Let's Encrypt certs. No manual cert management.


## Configuration

All settings live in `.env`. Key ones:

| Variable | Required? | What it does |
|---|---|---|
| `SECRET_KEY` | **Yes** | JWT signing — generate 64 random chars |
| `DATABASE_URL` | No | Defaults to local SQLite |
| `OLLAMA_BASE_URL` | No | Defaults to `http://localhost:11434` |
| `STRIPE_SECRET_KEY` | Only for billing | Your Stripe test/live key |
| `STRIPE_WEBHOOK_SECRET` | Only for billing | Stripe webhook signing secret |
| `STRIPE_PRICE_PREMIUM` | Only for billing | Stripe Price ID for premium tier |
| `ELEVENLABS_API_KEY` | Only for voice | TTS integration |


## Project Structure

```
freyja-scaffold/
├── backend/
│   ├── app/
│   │   ├── api/           # REST routes (auth, chat, billing)
│   │   ├── core/          # Config, DB, security, logging
│   │   ├── middleware/    # Age verification gate
│   │   ├── models/        # Database tables (User, Message, Payment)
│   │   ├── schemas/       # Request/response validation
│   │   ├── services/      # Business logic
│   │   └── main.py        # App entrypoint
│   ├── Dockerfile
│   └── pyproject.toml     # Python deps
├── frontend/
│   ├── src/app/           # Next.js pages (chat UI, auth)
│   ├── src/hooks/         # React hooks (auth, chat)
│   └── package.json       # Node deps
├── infra/
│   ├── docker/
│   │   └── docker-compose.yml   # Full stack orchestration
│   └── caddy/
│       └── Caddyfile            # HTTPS reverse proxy
└── .env.example           # Copy me to .env
```


## API Overview

| Method | Path | Auth? | Description |
|---|---|---|---|
| POST | `/api/auth/signup` | No | Create account |
| POST | `/api/auth/login` | No | Login (sets cookie) |
| POST | `/api/auth/logout` | Yes | Clear session |
| GET | `/api/auth/me` | Yes | Current user info |
| GET | `/api/chat/history` | Yes | Past messages |
| POST | `/api/chat/send` | Yes | Stream chat response |
| POST | `/api/billing/checkout` | Yes | Stripe checkout URL |
| POST | `/api/billing/webhook` | No | Stripe webhook (no auth) |
| GET | `/health` | No | Health check |

Full OpenAPI docs at `/docs` when running.


## How Tiers Work

- **Basic (default):** 6-turn memory window, limited model access
- **Premium:** 500-turn memory, all models, voice support

Stripe checkout → webhook hits `/api/billing/webhook` → user tier flips to `premium` automatically.


## Troubleshooting

**"Ollama connection refused"**
- Ollama isn't running. Start it: `ollama serve`
- Or check `OLLAMA_BASE_URL` in `.env` points to the right host.

**"No module named 'app'"**
- Run from inside `backend/`: `cd backend && uvicorn app.main:app --reload`

**"Stripe checkout fails"**
- `.env` is missing Stripe keys. Set `STRIPE_SECRET_KEY` and `STRIPE_PRICE_PREMIUM`.

**Frontend shows "Connection refused"**
- Backend isn't running, or frontend is pointing to the wrong URL. Default expects backend on `localhost:8000`.


## License

Private / E404 — Not for redistribution.

<!-- TAGNET README FOOTER — start -->

<div align="center">

**Like this work? Fuel the next widget / experiment / scaffold.**

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-%23FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/e404.tagnet)
[![Patreon](https://img.shields.io/badge/Support-Patreon-ff424d?logo=patreon&logoColor=white&style=for-the-badge)](https://www.patreon.com/VeritasExMachina?utm_campaign=creatorshare_creator)

<small>Crafted with caffeine, curiosity, and a Catppuccin palette · © e404-tagnet</small>

</div>
<!-- TAGNET README FOOTER — end -->
