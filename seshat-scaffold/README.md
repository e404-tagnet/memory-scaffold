<!-- TAGNET README HEADER — Catppuccin Mocha — do not edit by hand -->
<div align="center">

[![License](https://img.shields.io/github/license/e404-tagnet/memory-scaffold?color=313244&labelColor=11111b&label=License&style=flat-square)](https://github.com/e404-tagnet/memory-scaffold/blob/main/LICENSE)
[![Status](https://img.shields.io/badge/Status-stable-a6e3a1?labelColor=11111b&style=flat-square)](https://github.com/e404-tagnet/memory-scaffold/pulse)
[![Version](https://img.shields.io/github/v/release/e404-tagnet/memory-scaffold?color=313244&labelColor=11111b&label=Version&style=flat-square)](https://github.com/e404-tagnet/memory-scaffold/releases)
[![Repo](https://img.shields.io/badge/Repo-memory-scaffold-94e2d5?labelColor=11111b&style=flat-square&logo=github&logoColor=94e2d5)](https://github.com/e404-tagnet/memory-scaffold)
[![Tagnet](https://img.shields.io/badge/By-Tagnet-89dceb?labelColor=11111b&style=flat-square&logo=tag&logoColor=89dceb)](https://tagnet.dev)

</div>
<!-- TAGNET README HEADER — end -->

project: seshat
status: phase-1-active
created: 2026-07-08

# Seshat — E404 Memory System V2

> *"She who scrivens, she who measures, she who remembers all."*

**Seshat** (Egyptian: ssḥt, "she who scrivens") — goddess of writing, knowledge, wisdom, and record-keeping. Depicted with a seven-pointed emblem above her head, a palm rib in one hand, and a measuring rope in the other. Patron of scribes, keeper of books, measurer of time and memory.

This is the E404 Memory System V2. Not Pi. Not Hermes. Something better.

## Why Seshat?

| Name | Origin | Meaning | Fit |
|------|--------|---------|-----|
| **Seshat** | Egyptian | "She who scrivens" — writing, knowledge, measurement | Record-keeper of all things |
| Mnemosyne | Greek | Memory — mother of the Muses | Too obvious, everyone uses it |
| Nisaba | Sumerian | Goddess of writing, learning, grain | Good, but harder to pronounce |
| Thoth | Egyptian | Wisdom, writing, magic | Too broad — he's everything |

Seshat wins because she **measures and records**. That's what this system does: measure the filesystem, record the sessions, guard the canon.

## Phase 1 — Guard Rails (ACTIVE)

```
┌────────────────────────────────────────────┐
│  SESHAT PHASE 1: GUARD RAILS               │
├────────────────────────────────────────────┤
│                                            │
│  ┌─────────────┐   ┌─────────────────┐   │
│  │ canon-dirs  │──►│  fs-guardian.sh │   │
│  │ .json       │   │  (cron/5min)    │   │
│  └─────────────┘   └────────┬────────┘   │
│                             │            │
│                             ▼            │
│                   ┌─────────────────┐     │
│                   │  canon-index    │     │
│                   │  .json (hash)   │     │
│                   └────────┬────────┘     │
│                            │             │
│              ┌─────────────┼─────────────┐│
│              ▼             ▼             ▼│
│         ┌────────┐   ┌────────┐   ┌───────┐
│         │  OK    │   │ CHANGE │   │ PANIC │
│         │        │   │  log   │   │ alert │
│         └────────┘   └────────┘   └───────┘
│                                            │
└────────────────────────────────────────────┘
```

### Files

| File | Purpose | Status |
|------|---------|--------|
| `config/canon-dirs.json` | Contract — what dirs must exist | ✅ Created |
| `src/fs-guardian.sh` | Watcher — scans, hashes, alerts | 🔄 Building |
| `src/pi-sync-to-hermes.sh` | Syncs pi_workspace → hermes | 🔄 Building |
| `logs/guardian.log` | Guardian output | ✅ Ready |
| `logs/alerts.log` | PANIC events | ✅ Ready |

## Phase 2 — Distill Pipeline

Auto-extract facts from Hermes JSON sessions → warm/*.md

## Phase 3 — GUI

Visual graph of memory. Timeline view. Sync dashboard.

## Canonical Directory Contract

These directories are sacred. If any vanish, Seshat screams.

```json
// config/canon-dirs.json
[
  "~/Cloud/GIT-REPOS/",
  "~/Dropbox/5-HOME/Workspace/pi_workspace/",
  "~/Dropbox/5-HOME/Workspace/hermes_workspace/",
  "~/Dropbox/5-HOME/Workspace/FREYJA/",
  "~/Cloud/04-WORKSPACES/"
]
```

## Quick Commands

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

## Architecture

See `docs/ARCHITECTURE.md` (copied from pi_workspace design doc).

**Last updated:** 2026-07-08
**Status:** Phase 1 implementation in progress
**Machines:** AG2i (building), T480 (awaiting sync)

<!-- TAGNET README FOOTER — start -->

<div align="center">

**Like this work? Fuel the next widget / experiment / scaffold.**

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-%23FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/e404.tagnet)
[![Patreon](https://img.shields.io/badge/Support-Patreon-ff424d?logo=patreon&logoColor=white&style=for-the-badge)](https://www.patreon.com/VeritasExMachina?utm_campaign=creatorshare_creator)

<small>Crafted with caffeine, curiosity, and a Catppuccin palette · © e404-tagnet</small>

</div>
<!-- TAGNET README FOOTER — end -->
