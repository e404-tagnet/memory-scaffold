---
project: seshat
status: setup-instruction
created: 2026-07-08
---

# T480 Mirror Setup — SESHAT Phase 1

## What Already Syncs (Dropbox)

These directories sync automatically via Dropbox:
- `~/Dropbox/9-PROJECTS/seshat/` — this project ✅
- `~/Dropbox/5-HOME/Workspace/pi_workspace/` — Pi memory ✅
- `~/Dropbox/5-HOME/Workspace/hermes_workspace/` — Hermes compose ✅

## What You Need to Do on T480

### 1. Verify Seshat Arrived

```bash
ls -la ~/Dropbox/9-PROJECTS/seshat/
# Should show: README.md, config/, src/, docs/, logs/
```

### 2. Run Guardian Once (Test)

```bash
~/Dropbox/9-PROJECTS/seshat/src/fs-guardian.sh
```

**Expected:** All green except:
- `freyja` — skipped (AG2i-only) ✅
- Any AG2i-only dirs — skipped ✅

### 3. Install Cron Job

```bash
# Open crontab
crontab -e

# Add this line:
*/5 * * * * /home/e404/Dropbox/9-PROJECTS/seshat/src/fs-guardian.sh >/dev/null 2>&1

# Add hourly sync:
0 * * * * /home/e404/Dropbox/9-PROJECTS/seshat/src/pi-sync-to-hermes.sh >/dev/null 2>&1
```

### 4. Verify Cron

```bash
crontab -l | grep seshat
```

### 5. Check Alerts

```bash
cat ~/Dropbox/9-PROJECTS/seshat/logs/alerts.log
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
