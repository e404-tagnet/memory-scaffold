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
