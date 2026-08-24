#!/bin/bash
# SESHAT pi-sync-to-hermes.sh
# Mirrors pi_workspace/ into hermes-data/pi-scaffold/
# Run after every Pi session, or cron every hour.
# Also syncs seshat/ itself so hermes has the backup.

set -euo pipefail

SESHAT_ROOT="${HOME}/Cloud/GIT-REPOS/memory-scaffold/seshat-scaffold"
PI_WORKSPACE="${HOME}/Dropbox/5-HOME/Workspace/pi_workspace"
HERMES_SCAFFOLD="${HOME}/Dropbox/5-HOME/Workspace/hermes-data/pi-scaffold"
LOG="${SESHAT_ROOT}/logs/sync.log"
TIMESTAMP=$(date -Iseconds)

mkdir -p "$(dirname "$LOG")"

log() {
    echo "[$TIMESTAMP] $*" >> "$LOG"
    echo "[$TIMESTAMP] $*"
}

if [ ! -d "$PI_WORKSPACE" ]; then
    log "ERROR: pi_workspace not found at $PI_WORKSPACE"
    exit 1
fi

log "=== SESHAT Sync Start ==="

# Ensure target exists
mkdir -p "$HERMES_SCAFFOLD"

# rsync pi_workspace into hermes-data/pi-scaffold/
# -a = archive (recursive, preserve perms, times, symlinks)
# --delete = remove files in target that no longer exist in source
# -v = verbose
if command -v rsync &>/dev/null; then
    rsync -av --delete "$PI_WORKSPACE/" "$HERMES_SCAFFOLD/"
    log "rsync complete: $PI_WORKSPACE/ -> $HERMES_SCAFFOLD/"
else
    # Fallback to cp -a + find delete (less efficient but no deps)
    rm -rf "$HERMES_SCAFFOLD"
    mkdir -p "$HERMES_SCAFFOLD"
    cp -a "$PI_WORKSPACE/"* "$HERMES_SCAFFOLD/"
    log "cp -a complete (rsync not installed)"
fi

# Also sync seshat/ config into hermes-data so it's backed up too
HERMES_SESHAT="${HOME}/Dropbox/5-HOME/Workspace/hermes-data/seshat-mirror"
mkdir -p "$HERMES_SESHAT"

cp -a "$SESHAT_ROOT/config/"* "$HERMES_SESHAT/"
cp -a "$SESHAT_ROOT/src/"* "$HERMES_SESHAT/"
log "Seshat config/src mirrored to $HERMES_SESHAT/"

log "=== SESHAT Sync Complete ==="
