---
project: seshat
status: setup-instruction
created: 2026-07-08
---

# T480 Mirror Setup — SESHAT Phase 1

## What Already Syncs (Dropbox)

These directories sync automatically via Dropbox:
- `~/Cloud/GIT-REPOS/memory-scaffold/seshat-scaffold/` — this project ✅
- `~/Dropbox/5-HOME/Workspace/pi_workspace/` — Pi memory ✅
- `~/Dropbox/5-HOME/Workspace/hermes_workspace/` — Hermes compose ✅

## What You Need to Do on T480

### 1. Verify Seshat Arrived

```bash
ls -la ~/Cloud/GIT-REPOS/memory-scaffold/seshat-scaffold/
# Should show: README.md, config/, src/, docs/, logs/
```

### 2. Run Guardian Once (Test)

```bash
~/Cloud/GIT-REPOS/memory-scaffold/seshat-scaffold/src/fs-guardian.sh
```

**Expected:** All green except:
- `freyja` — skipped (AG2i-only) ✅
- Any AG2i-only dirs — skipped ✅

### 3. Install Cron Job

```bash
# Open crontab
crontab -e

# Add this line:
*/5 * * * * /home/e404/Cloud/GIT-REPOS/memory-scaffold/seshat-scaffold/src/fs-guardian.sh >/dev/null 2>&1

# Add hourly sync:
0 * * * * /home/e404/Cloud/GIT-REPOS/memory-scaffold/seshat-scaffold/src/pi-sync-to-hermes.sh >/dev/null 2>&1
```

### 4. Verify Cron

```bash
crontab -l | grep seshat
```

### 5. Check Alerts

```bash
cat ~/Cloud/GIT-REPOS/memory-scaffold/seshat-scaffold/logs/alerts.log
```

Should be empty (or only show old AG2i-only warnings that are now skipped).

---

## Machine Differences (Already Handled)

| Directory | AG2i | T480 | Status |
|-----------|------|------|--------|
| `FREYJA` | ✅ | ❌ | AG2i-only, T480 skips |
| `9-PROJECTS` | ✅ | ✅ | Both have it now |
| `pi_workspace` | ✅ | ✅ | Synced via Dropbox |
| `hermes_workspace` | ✅ | ✅ | Synced via Dropbox |
| `Cloud/04-WORKSPACES` | ✅ | ✅ | Synced via Cloud |

The `canon-dirs.json` `machines` field handles this automatically.

---

## Done

Once cron is set up, T480 is a mirror. Seshat guards both machines.

Last updated: 2026-07-08
