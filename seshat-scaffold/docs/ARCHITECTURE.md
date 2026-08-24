---
tier: hot
project: seshat-memory-system
created: 2026-07-08
status: phase-1-active
---

# SESHAT — E404 Memory System V2 Architecture

## Why Seshat?

**Seshat** (Egyptian: ssḥt, "she who scrivens") — goddess of writing, knowledge, wisdom, and record-keeping. Depicted with a seven-pointed emblem, a palm rib (writing tool), and a measuring rope. Patron of scribes. Keeper of books. Measurer of time and memory.

She doesn't forget. Neither do we.

---

## 1. The Problem (What Was Broken)

```
┌─────────────────────────────────────────────────────────────┐
│                     BEFORE: Two Silos                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────────┐         ┌──────────────┐               │
│   │   Pi TUI     │         │   Hermes     │               │
│   │  (terminal)  │         │  (WebUI)     │               │
│   └──────┬───────┘         └──────┬───────┘               │
│          │                        │                       │
│          │ markdown files          │ JSON sessions        │
│          │ (manual curation)       │ (auto-saved)         │
│          │                         │                       │
│   ┌──────▼───────┐         ┌──────▼───────┐               │
│   │  Only knows  │         │  Has data    │               │
│   │  what you    │         │  but buried  │               │
│   │  wrote       │         │  in JSON     │               │
│   └──────────────┘         └──────────────┘               │
│                                                             │
│   RESULT: 9-PROJECTS vanished. Neither system caught it.   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Pi** had clean markdown but was incomplete — it only knew what you manually distilled.  
**Hermes** had raw conversations but they were unqueryable JSON soup.

---

## 2. SESHAT Architecture (V2)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SESHAT MEMORY SYSTEM V2                          │
│                    "One brain, two bodies, zero forgetting"              │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  LAYER 0: REALITY — Filesystem Guardian (fs-guardian.sh)               │
│  ────────────────────────────────────────────────────────              │
│                                                                         │
│   ┌─────────────┐                                                       │
│   │ canon-dirs  │  Sacred contract — these dirs must exist            │
│   │ .json       │  Machine-scoped (AG2i vs T480 aware)                 │
│   └──────┬──────┘                                                       │
│          │                                                              │
│          ▼                                                              │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐               │
│   │ fs-guardian │───►│ canon-index │───►│  alerts.log │               │
│   │  (cron 5m)  │    │ .json       │    │ guardian.log│               │
│   └─────────────┘    └─────────────┘    └─────────────┘               │
│                                                                         │
│   STATES:  OK (green) | CHANGE (yellow) | PANIC (red)                │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: SESSION — Hermes Conversations (Auto-saved)                  │
│  ────────────────────────────────────────────────────                  │
│                                                                         │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐             │
│   │  Hermes      │───►│  session-    │───►│  distill-    │             │
│   │  (any agent) │    │  store/*.json│    │  pipeline    │             │
│   └──────────────┘    └──────────────┘    └──────┬───────┘             │
│                                                   │                    │
│                    Raw JSON kept 30 days         │ Auto-extract       │
│                    then purged                     │ every 24h          │
│                                                   │                    │
│                                                   ▼                    │
│   ┌─────────────────────────────────────────────────────────────┐    │
│   │  LAYER 1a: Distilled Facts → warm/session/*.md (forever)   │    │
│   └─────────────────────────────────────────────────────────────┘    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  LAYER 2: TIERED — Pi Markdown (Curated + Auto-populated)             │
│  ─────────────────────────────────────────────────────────            │
│                                                                         │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│   │   RAM   │  │  HOT    │  │  HOT/   │  │  WARM   │  │  COLD   │   │
│   │         │  │         │  │ RECENT  │  │         │  │         │   │
│   └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘   │
│        │            │            │            │            │        │
│   volatile     always       last 10      on-demand    archived     │
│   session      loaded      sessions     reference    (yearly)       │
│   state        identity     summaries    context                  │
│                                                                         │
│   RAM:    auto from fs-guardian + current session                   │
│   HOT:    identity + directory-map (auto-updated)                   │
│   WARM:   auto from distill-pipeline + manual edits                 │
│   COLD:   yearly compressed snapshot of warm                         │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  LAYER 3: AGENT CONTEXT — What Pi TUI Loads at Boot                     │
│  ──────────────────────────────────────────────────────                 │
│                                                                         │
│   1. Load HOT:    core.md + memories.md + directory-map.md            │
│   2. Load RAM:    session-cache.md (current device)                   │
│   3. Guardian:    "All canon dirs present?" alert if not             │
│   4. User loads:  /load warm/topic on demand                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  SYNC: T480 ↔ AG2i                                                     │
│  ─────────────────                                                     │
│                                                                         │
│            ┌─────────────┐                                              │
│            │   Dropbox   │                                              │
│            │   Cloud     │                                              │
│            └──────┬──────┘                                              │
│                   │                                                     │
│      ┌────────────┼────────────┐                                      │
│      ▼            ▼            ▼                                      │
│   ┌──────┐   ┌──────┐   ┌──────┐                                      │
│   │ AG2i │◄─►│canon │◄─►│ T480 │                                      │
│   │      │   │index │   │      │                                      │
│   └──────┘   └──────┘   └──────┘                                      │
│                                                                         │
│   Dropbox syncs files. canon-index.json is the contract.              │
│   Machine-scoped entries mean AG2i-only dirs don't panic T480.      │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Implementation Phases

```
PHASE 1 — GUARD RAILS (Active Now)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[✅] canon-dirs.json       — sacred directory contract
[✅] fs-guardian.sh       — cron scanner, hash trees, PANIC alerts
[✅] pi-sync-to-hermes.sh — pi_workspace → hermes-data mirror
[✅] Machine scoping      — AG2i vs T480 aware
[ ]  Cron setup            — */5 * * * * on both machines
[ ]  T480 mirror           — same scripts, same structure

PHASE 2 — DISTILL PIPELINE (Next)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ]  session-distill-v2.py — read Hermes JSON → warm/*.md
[ ]  auto-extract rules     — project refs, file paths, decisions
[ ]  directory-map.md       — auto-generated from guardian
[ ]  30-day JSON purge      — keep sessions lean

PHASE 3 — GUI (When Ready)
━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ]  Visual graph          — projects/sessions/files as nodes
[ ]  Timeline view          — what happened when
[ ]  Sync dashboard         — AG2i vs T480 divergence
[ ]  Live fs monitor        — watch canon dirs in real-time
[ ]  Unified search         — across markdown + JSON + filesystem
```

---

## 4. File Locations (Both Machines)

```
~/Cloud/GIT-REPOS/memory-scaffold/seshat-scaffold/
├── README.md
├── config/
│   ├── canon-dirs.json       ← sacred contract
│   └── canon-index.json      ← generated hash tree
├── src/
│   ├── fs-guardian.sh        ← cron watcher
│   └── pi-sync-to-hermes.sh  ← backup sync
├── logs/
│   ├── guardian.log          ← normal scan output
│   ├── alerts.log            ← PANIC events only
│   └── sync.log              ← sync output
└── docs/
    └── ARCHITECTURE.md       ← this file

~/Dropbox/5-HOME/Workspace/hermes-data/
├── pi-scaffold/              ← synced mirror of pi_workspace/
├── seshat-mirror/            ← synced seshat config + src
└── webui/sessions/           ← raw JSON (30-day retention)
```

---

## 5. Memory Tier Definitions (V2)

| Tier | Source | Auto? | TTL | Purpose |
|------|--------|-------|-----|---------|
| **RAM** | fs-guardian + session | ✅ Yes | Session | Current state, device context, alerts |
| **HOT** | identity + canon-map | ✅ Yes | Forever | Who you are, what dirs must exist |
| **HOT/Recent** | distill-pipeline | ✅ Yes | 30 days | Last 10 session summaries |
| **WARM** | distill-pipeline | ✅ Yes | 1 year | Project facts, decisions, learnings |
| **COLD** | yearly snapshot | ✅ Yes | Forever | Compressed archive |
| **SESSION** | Hermes JSON | ✅ Yes | 30 days | Raw conversation replay (audit) |

**Key change:** Everything below HOT is auto-generated. You only edit HOT (identity) and RAM (current session). The machine does the rest.

---

## 6. Quick Commands

```bash
# Run guardian manually
~/Cloud/GIT-REPOS/memory-scaffold/seshat-scaffold/src/fs-guardian.sh

# Sync pi_workspace to hermes backup
~/Cloud/GIT-REPOS/memory-scaffold/seshat-scaffold/src/pi-sync-to-hermes.sh

# Check alerts
cat ~/Cloud/GIT-REPOS/memory-scaffold/seshat-scaffold/logs/alerts.log

# View canon index
cat ~/Cloud/GIT-REPOS/memory-scaffold/seshat-scaffold/config/canon-index.json
```

---

Last updated: 2026-07-08
Status: Phase 1 active on T480, awaiting AG2i mirror
