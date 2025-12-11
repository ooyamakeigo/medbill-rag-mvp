#!/usr/bin/env bash
set -euo pipefail

BILL_FOLDER_ID="${1:-}"

if [[ -z "${BILL_FOLDER_ID}" ]]; then
  echo "Usage: bash scripts/run_bill_folder_docker.sh <BILL_FOLDER_ID>"
  exit 1
fi

IMAGE_NAME="medbill-rag-mvp:latest"

echo "🔧 Building Docker image: ${IMAGE_NAME} ..."
docker build -t "${IMAGE_NAME}" .

echo "🚀 Running bill pipeline in Docker for BILL_FOLDER_ID=${BILL_FOLDER_ID} ..."

# Mount gcloud config to allow ADC inside container (works even if not using user creds)
# Pass .env for BUCKET/PROJECT/DOCAI configs
docker run --rm \
  --env-file .env \
  -e BILL_FOLDER_ID="${BILL_FOLDER_ID}" \
  -v "${HOME}/.config/gcloud:/root/.config/gcloud:ro" \
  "${IMAGE_NAME}"
