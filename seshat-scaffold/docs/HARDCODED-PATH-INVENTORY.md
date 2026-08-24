---
project: seshat
status: critical-reference
created: 2026-07-08
---

# HARDCODED PATH INVENTORY — What You CANNOT Move

This document maps every program, config, and script that hardcodes a Dropbox path.
**Do not move anything listed here without updating every reference.**

---

## 🔴 LEVEL 1: NEVER MOVE — Hardcoded Everywhere

### `~/Dropbox/5-HOME/Workspace/pi_workspace/`

| What Hardcodes It | File | Exact Reference |
|---|---|---|
| **Bash alias** | `~/.bashrc.d/ag2-aliases.sh` | `alias pi-mem='/home/e404/Dropbox/5-HOME/Workspace/pi_workspace/pi-autoboot.sh'` |
| **Desktop launcher** | `~/.local/share/applications/pi-tui.desktop` | `Exec=/home/e404/Dropbox/5-HOME/Workspace/pi_workspace/pi-autoboot.sh` |
| **Pi TUI settings** | `~/.pi/agent/settings.json` | `"/home/e404/Dropbox/5-HOME/Workspace/pi_workspace/.pi/extensions/tiered-memory/extension.ts"` |
| **Cockpit plugin installer** | `pi_workspace/scripts/install-cockpit-plugin.sh` | `PLUGIN_DIR="/home/e404/Dropbox/5-HOME/Workspace/extras/cockpit-dashboard"` |
| **Benchmark script** | `pi_workspace/scripts/benchmark-tiered-memory.sh` | `WORKSPACE="${1:-$HOME/Dropbox/5-HOME/Workspace/pi_workspace}"` |
| **Session distill** | `pi_workspace/scripts/session-distill.sh` | `MEMORY_DIR="${HOME}/Dropbox/5-HOME/Workspace/pi_workspace/memory"` |

**Verdict:** `pi_workspace/` is the most hardcoded directory. If you move it, you must update **6+ files** across bash aliases, desktop files, Pi settings, and internal scripts.

---

### `~/Dropbox/5-HOME/Workspace/hermes_workspace/`

| What Hardcodes It | File | Exact Reference |
|---|---|---|
| **Hermes setup script** | `hermes_workspace/setup-hermes-podman.sh` | `HERMES_DIR="/home/e404/Dropbox/5-HOME/Workspace/hermes_workspace"` |
| **Hermes env file** | `hermes_workspace/.env` | `HERMES_WORKSPACE=/home/e404/Dropbox/5-HOME/Workspace` |
| **Hermes env example** | `hermes_workspace/.env.example` | `HERMES_WEBUI_EXTENSION_DIR=/home/e404/Dropbox/5-HOME/Workspace/hermes_workspace/extensions` |
| **Docker compose** | `hermes_workspace/docker-compose.yml` | `volumes:` binds to `/home/e404/Dropbox/5-HOME/Workspace/hermes-data` and `/home/e404/Dropbox/5-HOME/Workspace` |
| **Atlas router venv** | `hermes_workspace/atlas-router/.venv/*` | Every venv file hardcodes the full path (can be rebuilt, but tedious) |
| **Hermes README** | `hermes_workspace/README.md` | References paths throughout |

**Verdict:** `hermes_workspace/` is deeply hardcoded. The **docker-compose.yml bind mounts are the killer** — these tell Podman where to mount host directories into the container. Changing them requires rebuilding containers.

---

## 🟡 LEVEL 2: MOVEABLE BUT NEEDS UPDATES

### `~/Dropbox/5-HOME/Workspace/hermes-data/`

| What Hardcodes It | File | Exact Reference |
|---|---|---|
| **Docker compose** | `hermes_workspace/docker-compose.yml` | `/home/e404/Dropbox/5-HOME/Workspace/hermes-data:/home/hermeswebui/.hermes:Z` |
| **Seshat sync script** | `seshat/src/pi-sync-to-hermes.sh` | `HERMES_SCAFFOLD="${HOME}/Dropbox/5-HOME/Workspace/hermes-data/pi-scaffold"` |

**Verdict:** Only 2 hard references. Both are in config files. Moveable if you update the compose file and the sync script.

---

### `~/Dropbox/5-HOME/Workspace/FREYJA/`

| What Hardcodes It | File | Exact Reference |
|---|---|---|
| **Seshat canon config** | `seshat/config/canon-dirs.json` | `path: ~/Dropbox/5-HOME/Workspace/FREYJA` (AG2i-only) |

**Verdict:** Only referenced in Seshat's own config. Trivial to update.

---

### `~/Cloud/GIT-REPOS/`

| What Hardcodes It | File | Exact Reference |
|---|---|---|
| **Seshat self** | `seshat/config/canon-dirs.json` | `path: ~/Cloud/GIT-REPOS` |
| **Seshat self** | `seshat/src/*.sh` | `SESHAT_ROOT="${HOME}/Dropbox/9-PROJECTS/seshat"` |
| **Seshat README** | `workspace README` | `cd ~/9-PROJECTS/Akkadia` (outdated — now Akkadia is in home dir) |

**Verdict:** Seshat is self-aware. If you move `9-PROJECTS/`, you must update Seshat's own config and scripts. But that's only 3 files.

---

### `~/Cloud/04-WORKSPACES/`

| What Hardcodes It | File | Exact Reference |
|---|---|---|
| **Seshat canon config** | `seshat/config/canon-dirs.json` | `path: ~/Cloud/04-WORKSPACES` |

**Verdict:** Only Seshat knows about it. Not referenced by any running program. **Safe to move.**

---

## 🟢 LEVEL 3: SAFE TO MOVE — Not Hardcoded

| Directory | Why It's Safe | Notes |
|---|---|---|
| `~/Dropbox/2-TAGNET-482/` | Referenced by Seshat only | 232MB |
| `~/Dropbox/11-MACHINE-LEARNING/` | Referenced by Seshat only | 192MB |
| `~/Dropbox/12-E404/` | Referenced by Seshat only | 56MB |
| `~/Dropbox/8-TOOLBOX/` | Referenced by Seshat only | 35MB |
| `~/Dropbox/10-TEMPLATES/` | Referenced by Seshat only | 27MB |
| `~/Dropbox/3-AG2I/` | Referenced by Seshat only | 3MB |
| `~/Dropbox/6-FILES/` | Referenced by Seshat only | 2.7MB |
| `~/Dropbox/4-T480/` | Referenced by Seshat only | 2.6MB |
| `~/Dropbox/7-SCRIPTS/` | Referenced by Seshat only | 1MB |
| `~/Dropbox/13-VIRT-OS/` | Referenced by Seshat only | 1MB |
| `~/Dropbox/0-ARCHIVE/` | Referenced by Seshat only | 664K |
| `~/Dropbox/1-INBOX/` | Referenced by Seshat only | 160K |

---

## 📊 DROPBOX SIZE AUDIT

```
Total Dropbox usage: ~1.9GB (near 2GB limit)

Top offenders:
1.3G  5-HOME/           ← LEVEL 1: CANNOT MOVE (hardcoded everywhere)
232M  2-TAGNET-482/     ← LEVEL 3: Moveable
192M  11-MACHINE-LEARNING/  ← LEVEL 3: Moveable
142M  Apps/             ← Dropbox app metadata
 56M  12-E404/          ← LEVEL 3: Moveable
 35M  8-TOOLBOX/        ← LEVEL 3: Moveable
 27M  10-TEMPLATES/      ← LEVEL 3: Moveable
```

---

## 💡 RECOMMENDATIONS FOR SPACE MANAGEMENT

### Option A: Move LEVEL 3 dirs to `~/Cloud/`
**Effort:** Low (no hardcoded references)
**Space freed:** ~550MB
**Risk:** None

```bash
# Example: move 11-MACHINE-LEARNING to Cloud
mv ~/Dropbox/11-MACHINE-LEARNING ~/Cloud/
# Update Seshat canon-dirs.json to match
```

### Option B: Split `5-HOME/Workspace/` into Dropbox vs Cloud
**Effort:** High (docker-compose bind mounts, Pi settings, bash aliases)
**Space freed:** Potentially 1GB+
**Risk:** High — one missed reference breaks a container or Pi boot

```
KEEP IN DROPBOX (hardcoded):
├── pi_workspace/          (small: ~750KB of markdown)
└── hermes_workspace/      (small: configs only, not data)

MOVE TO CLOUD:
├── hermes-data/           (BIG: 27MB of JSON, sessions, node_modules)
└── _archive/              (already there)
└── FREYJA/                (if on AG2i)
```

### Option C: Leave structure, upgrade Dropbox plan
**Effort:** Zero
**Cost:** ~$12/month for 2TB
**Risk:** None

---

## 🛠️ IF YOU MUST MOVE SOMETHING

Use this checklist:

```bash
# 1. Update docker-compose.yml (bind mounts)
vim ~/Dropbox/5-HOME/Workspace/hermes_workspace/docker-compose.yml
# Rebuild container:
podman-compose down && podman-compose up -d

# 2. Update bash alias
vim ~/.bashrc.d/ag2-aliases.sh
source ~/.bashrc

# 3. Update desktop file
vim ~/.local/share/applications/pi-tui.desktop
update-desktop-database ~/.local/share/applications/

# 4. Update Pi TUI settings
vim ~/.pi/agent/settings.json

# 5. Update Seshat config
vim ~/Cloud/GIT-REPOS/memory-scaffold/seshat-scaffold/config/canon-dirs.json

# 6. Run guardian to verify
~/Cloud/GIT-REPOS/memory-scaffold/seshat-scaffold/src/fs-guardian.sh
```

---

Last updated: 2026-07-08
Status: Critical reference — keep updated when paths change
