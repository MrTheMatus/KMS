#!/usr/bin/env bash
# Backup vault + SQLite state.db (non-interactive). Run from repository root.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DEST="${KMS_BACKUP_DEST:-kms/backups}"
mkdir -p "$DEST"
ARCHIVE="${DEST}/kms-backup-${STAMP}.tar.gz"

ITEMS=()
if [[ -d example-vault ]]; then
  ITEMS+=(example-vault)
fi
if [[ -f kms/data/state.db ]]; then
  ITEMS+=(kms/data/state.db)
fi

if [[ ${#ITEMS[@]} -eq 0 ]]; then
  echo "backup: nothing to archive (missing example-vault/ and kms/data/state.db)" >&2
  exit 1
fi

tar -czf "${ARCHIVE}" "${ITEMS[@]}"
echo "${ARCHIVE}"
