#!/usr/bin/env bash
set -euo pipefail

BILL_ID="${1:-}"
if [ -z "$BILL_ID" ]; then
  echo "Usage: bash scripts/run_bill_folder.sh <bill_folder_id>"
  exit 1
fi

cd "$(dirname "$0")/.."

python3.11 -m venv .venv >/dev/null 2>&1 || true
source .venv/bin/activate

pip install -q -r requirements.txt

set -a
source .env
set +a

export PYTHONPATH=src

python - <<PY
from medbill_rag.pipeline_end2end import run_bill_folder
import json
out = run_bill_folder("${BILL_ID}")
print(json.dumps(out, indent=2)[:2000])
PY

echo ""
echo "Check outputs in GCS:"
echo "gs://<BUCKET_CASE>/bills/${BILL_ID}/outputs/"
