<!-- TAGNET README HEADER — Catppuccin Mocha — do not edit by hand -->
<div align="center">

[![License](https://img.shields.io/github/license/e404-tagnet/memory-scaffold?color=313244&labelColor=11111b&label=License&style=flat-square)](https://github.com/e404-tagnet/memory-scaffold/blob/main/LICENSE)
[![Status](https://img.shields.io/badge/Status-stable-a6e3a1?labelColor=11111b&style=flat-square)](https://github.com/e404-tagnet/memory-scaffold/pulse)
[![Version](https://img.shields.io/github/v/release/e404-tagnet/memory-scaffold?color=313244&labelColor=11111b&label=Version&style=flat-square)](https://github.com/e404-tagnet/memory-scaffold/releases)
[![Repo](https://img.shields.io/badge/Repo-memory-scaffold-94e2d5?labelColor=11111b&style=flat-square&logo=github&logoColor=94e2d5)](https://github.com/e404-tagnet/memory-scaffold)
[![Tagnet](https://img.shields.io/badge/By-Tagnet-89dceb?labelColor=11111b&style=flat-square&logo=tag&logoColor=89dceb)](https://tagnet.dev)

</div>
<!-- TAGNET README HEADER — end -->

# Memory Scaffold

A lightweight, tiered memory architecture for LLM coding agents and AI workspaces.

## What This Is

Your LLM session starts blank. Every time. This scaffold fixes that by giving your agent persistent, structured context across sessions — without bloat.

## Architecture

```
┌─────────────────────────────────────────────┐
│  🔴 RAM Layer (session-cache.md)            │  ← Volatile, loaded FIRST
│  ├─ Current task state                       │     Overwrite each session
│  ├─ In-progress items                        │
│  └─ Scratchpad                               │
├─────────────────────────────────────────────┤
│  🟢 ROM Hot Tier (core.md, memories.md)     │  ← Always loaded
│  ├─ Identity, hardware specs                 │
│  └─ Learnings, discoveries                   │
├─────────────────────────────────────────────┤
│  🟡 ROM Warm Tier (*-notes.md)              │  ← On demand
│  └─ Domain knowledge                         │
├─────────────────────────────────────────────┤
│  ⚪ ROM Cold Tier (archived/)               │  ← Search only
│  └─ Historical logs                          │
└─────────────────────────────────────────────┘
```

## Files

| File | Tier | Purpose |
|------|------|---------|
| `session-cache.md` | 🔴 RAM | Current session state — overwrite freely |
| `core.md` | 🟢 HOT | Identity, preferences, hardware |
| `memories.md` | 🟢 HOT | Accumulated learnings |
| `*-notes.md` | 🟡 WARM | Domain knowledge, on-demand load |
| `archived/*` | ⚪ COLD | History, search-only |

## Quick Start

1. **Copy this scaffold** into your workspace root
2. **Fill in the blanks** in `core-template.md` and `memories-template.md`, rename to `core.md` / `memories.md`
3. **Start each session** with your agent reading `session-cache.md` → `core.md` → `memories.md`
4. **Update** `session-cache.md` at session end with current state

## Extension (Optional)

The included `extension.ts` auto-loads RAM + HOT tiers on agent boot if your environment supports extensions. Install by registering the path in your agent settings.

## Principles

- **Don't paste your whole life** — structured tiers keep context lean
- **RAM is cheap** — write session state without guilt, overwrite next time
- **HOT is forever** — identity and learnings accumulate
- **WARM is optional** — load domain files only when relevant

## License

MIT — use it, fork it, improve it.

<!-- TAGNET README FOOTER — start -->

<div align="center">

**Like this work? Fuel the next widget / experiment / scaffold.**

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20a%20Coffee-%23FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/e404.tagnet)
[![Patreon](https://img.shields.io/badge/Support-Patreon-ff424d?logo=patreon&logoColor=white&style=for-the-badge)](https://www.patreon.com/VeritasExMachina?utm_campaign=creatorshare_creator)

<small>Crafted with caffeine, curiosity, and a Catppuccin palette · © e404-tagnet</small>

</div>
<!-- TAGNET README FOOTER — end -->
