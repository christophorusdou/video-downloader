#!/usr/bin/env bash
# Sync downloaded videos from N100 staging to TrueNAS, then shut down NAS.
# Intended to run as root via cron:
#   0 3 * * * /opt/vidarchive/sync-to-nas.sh >> /var/log/vidarchive-sync.log 2>&1
set -euo pipefail

STAGING_DIR="/opt/vidarchive/downloads"
NAS_HOST="192.168.130.230"
NAS_USER="chris"
NAS_SSH_KEY="/root/.ssh/id_ed25519_backup"
NAS_DEST="/mnt/main/media/vidarchive/"
NAS_MAC="58:11:22:4d:ac:18"
SSH_OPTS="-i $NAS_SSH_KEY -o ConnectTimeout=5 -o StrictHostKeyChecking=accept-new"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

# Exit early if nothing to transfer
if [ -z "$(find "$STAGING_DIR" -mindepth 1 -maxdepth 1 2>/dev/null)" ]; then
    log "Nothing to transfer. Exiting."
    exit 0
fi

# Wake TrueNAS
log "Sending WoL packet to TrueNAS..."
etherwake -i enp3s0 "$NAS_MAC" 2>/dev/null || wakeonlan "$NAS_MAC" 2>/dev/null || true

# Wait for SSH connectivity (up to 3 minutes)
log "Waiting for TrueNAS to come online..."
for i in $(seq 1 36); do
    if ssh $SSH_OPTS "$NAS_USER@$NAS_HOST" "echo ok" >/dev/null 2>&1; then
        log "TrueNAS is online."
        break
    fi
    if [ "$i" -eq 36 ]; then
        log "ERROR: TrueNAS did not come online after 3 minutes."
        exit 1
    fi
    sleep 5
done

# Ensure target directory exists
ssh $SSH_OPTS "$NAS_USER@$NAS_HOST" "mkdir -p '$NAS_DEST'"

# Transfer files, removing source after successful copy
log "Starting rsync transfer..."
rsync -avz --remove-source-files \
    -e "ssh $SSH_OPTS" \
    "$STAGING_DIR/" \
    "$NAS_USER@$NAS_HOST:$NAS_DEST"

# Clean empty uploader directories left behind
find "$STAGING_DIR" -mindepth 1 -type d -empty -delete

log "Transfer complete."

# Shut down TrueNAS
log "Shutting down TrueNAS..."
ssh $SSH_OPTS "$NAS_USER@$NAS_HOST" "sudo shutdown -h now" || true

log "Done."
