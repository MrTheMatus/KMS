#!/usr/bin/env bash
# Onboarding: venv, deps, local config from example (idempotent).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q -r requirements.txt

CFG_EX="$ROOT/kms/config/config.example.yaml"
CFG="$ROOT/kms/config/config.yaml"
if [[ ! -f "$CFG" ]]; then
  cp "$CFG_EX" "$CFG"
  echo "Created $CFG — edit vault.root if needed."
else
  echo "Keeping existing $CFG"
fi

echo "Done. Activate: source .venv/bin/activate"
echo "Run (from repo root, PYTHONPATH=.):"
echo "  python -m kms.scripts.scan_inbox"
echo "  python -m kms.scripts.make_review_queue"
echo "  python -m kms.scripts.apply_decisions --dry-run"
