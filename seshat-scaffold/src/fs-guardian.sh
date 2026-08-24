#!/bin/bash
# SESHAT fs-guardian.sh — Phase 1
# Scans canonical directories. Alerts on anomalies.
# Run via cron: */5 * * * * /home/e404/Cloud/GIT-REPOS/memory-scaffold/seshat-scaffold/src/fs-guardian.sh
# Or manually when needed.

set -euo pipefail

SESHAT_ROOT="${HOME}/Cloud/GIT-REPOS/memory-scaffold/seshat-scaffold"
CANON_CONFIG="${SESHAT_ROOT}/config/canon-dirs.json"
CANON_INDEX="${SESHAT_ROOT}/config/canon-index.json"
GUARDIAN_LOG="${SESHAT_ROOT}/logs/guardian.log"
ALERT_LOG="${SESHAT_ROOT}/logs/alerts.log"
TIMESTAMP=$(date -Iseconds)
HOSTNAME=$(hostname)

# Ensure log dirs exist
mkdir -p "$(dirname "$GUARDIAN_LOG")" "$(dirname "$ALERT_LOG")"

log_guardian() {
    echo "[$TIMESTAMP] [${HOSTNAME}] $*" >> "$GUARDIAN_LOG"
}

log_alert() {
    echo "[$TIMESTAMP] [${HOSTNAME}] PANIC: $*" >> "$ALERT_LOG"
    echo "[$TIMESTAMP] [${HOSTNAME}] PANIC: $*" >&2
}

log_guardian "=== SESHAT Guardian Scan Start ==="

# Check python3 exists (needed for JSON parsing)
if ! command -v python3 &>/dev/null; then
    log_alert "python3 not found — cannot parse canon-dirs.json"
    exit 1
fi

# Parse canon-dirs.json and check each directory
python3 << 'PYEOF'
import json, os, sys, hashlib, subprocess
from pathlib import Path
from datetime import datetime, timezone

home = str(Path.home())
root = Path(home) / "Cloud/GIT-REPOS/memory-scaffold/seshat-scaffold"
config_path = root / "config/canon-dirs.json"
index_path = root / "config/canon-index.json"
guardian_log = root / "logs/guardian.log"
alert_log = root / "logs/alerts.log"
hostname = os.uname().nodename

def log(msg):
    ts = datetime.now(timezone.utc).isoformat()
    with open(guardian_log, "a") as f:
        f.write(f"[{ts}] [{hostname}] {msg}\n")

def alert(msg):
    ts = datetime.now(timezone.utc).isoformat()
    line = f"[{ts}] [{hostname}] PANIC: {msg}"
    with open(alert_log, "a") as f:
        f.write(line + "\n")
    print(line, file=sys.stderr)

def hash_dir(path):
    """Return a simple hash of a directory: count files, total size, subdir count."""
    total_size = 0
    file_count = 0
    dir_count = 0
    for rootp, dirs, files in os.walk(path):
        dir_count += len(dirs)
        for f in files:
            fp = Path(rootp) / f
            if fp.is_file():
                try:
                    total_size += fp.stat().st_size
                    file_count += 1
                except (OSError, PermissionError):
                    pass
    data = f"{file_count}:{total_size}:{dir_count}"
    return hashlib.sha256(data.encode()).hexdigest()[:16], file_count, total_size, dir_count

# Load config
with open(config_path) as f:
    config = json.load(f)

# Load previous index if exists
previous = {}
if index_path.exists():
    try:
        with open(index_path) as f:
            previous = json.load(f)
    except json.JSONDecodeError:
        log("WARNING: canon-index.json corrupt, treating as empty")

# Build current index
current = {
    "version": "1.0",
    "generated": datetime.now(timezone.utc).isoformat(),
    "hostname": hostname,
    "entries": {}
}

panics = []
changes = []
skipped = []

for entry in config["directories"]:
    dir_id = entry["id"]
    machines = entry.get("machines", [])
    
    # Skip if machine-scoped and not for this host
    if machines and hostname not in machines:
        skipped.append(dir_id)
        continue
    
    raw_path = entry["path"].replace("~", home)
    is_critical = entry.get("critical", False)
    desc = entry.get("desc", "")

    current["entries"][dir_id] = {
        "path": raw_path,
        "exists": False,
        "hash": None,
        "file_count": 0,
        "total_size": 0,
        "dir_count": 0,
        "critical": is_critical
    }

    p = Path(raw_path)

    if not p.exists():
        msg = f"MISSING: {dir_id} -> {raw_path} ({desc})"
        if is_critical:
            alert(f"CRITICAL DIRECTORY MISSING: {dir_id} at {raw_path} — {desc}")
            panics.append(msg)
        else:
            log(f"WARNING: {msg}")
        continue

    if not p.is_dir():
        alert(f"PATH IS NOT A DIRECTORY: {dir_id} at {raw_path}")
        panics.append(f"NOT_DIR: {dir_id}")
        continue

    h, fc, ts, dc = hash_dir(raw_path)
    current["entries"][dir_id]["exists"] = True
    current["entries"][dir_id]["hash"] = h
    current["entries"][dir_id]["file_count"] = fc
    current["entries"][dir_id]["total_size"] = ts
    current["entries"][dir_id]["dir_count"] = dc

    # Compare to previous
    if dir_id in previous.get("entries", {}):
        prev = previous["entries"][dir_id]
        if prev.get("hash") != h:
            delta_size = ts - prev.get("total_size", 0)
            delta_files = fc - prev.get("file_count", 0)
            log(f"CHANGE: {dir_id} hash changed | files: {delta_files:+d} | size: {delta_size:+d} bytes")
            changes.append(dir_id)
        else:
            log(f"OK: {dir_id} unchanged ({fc} files, {ts} bytes)")
    else:
        log(f"NEW: {dir_id} first seen ({fc} files, {ts} bytes)")

# Write new index
with open(index_path, "w") as f:
    json.dump(current, f, indent=2)

# Summary
log(f"=== Scan Complete: {len(panics)} panics, {len(changes)} changes, {len(skipped)} skipped ===")

if panics:
    print(f"\n🚨 SESHAT ALERTS: {len(panics)} critical issues. Check {alert_log}")
    sys.exit(2)
elif changes:
    print(f"\n⚠️  SESHAT: {len(changes)} directories changed. Check {guardian_log}")
    sys.exit(1)
else:
    print(f"\n✅ SESHAT: All {len(current['entries'])} canonical directories OK. ({len(skipped)} machine-skipped)")
    sys.exit(0)
PYEOF

exit $?
