#!/usr/bin/env bash
set -euo pipefail

BILL_ID="${1:-}"
if [ -z "$BILL_ID" ]; then
  echo "Usage: bash scripts/run_bill_folder_docker.sh <bill_folder_id>"
  echo "Example: bash scripts/run_bill_folder_docker.sh ba47f8d2-79bb-4f1f-9a8e-05fc402b2ba7"
  exit 1
fi

IMAGE_NAME="medbill-rag-mvp:latest"

cd "$(dirname "$0")/.."

# .env があるか確認
if [ ! -f .env ]; then
  echo "❌ .env not found in $(pwd)"
  echo "  First: cp .env.example .env して、PROJECT_ID や BUCKET_CASE などを設定してください。"
  exit 1
fi

# Docker イメージをビルド（初回 or Dockerfile 変更時だけ走る）
echo "🔧 Building Docker image: ${IMAGE_NAME} ..."
docker build -t "${IMAGE_NAME}" .

echo "🚀 Running bill pipeline in Docker for BILL_FOLDER_ID=${BILL_ID} ..."
docker run --rm \
  --env-file .env \
  -e BILL_FOLDER_ID="${BILL_ID}" \
  "${IMAGE_NAME}"

echo ""
echo "✅ Done. Check outputs in GCS:"
echo "   gs://$(grep '^BUCKET_CASE=' .env | cut -d'=' -f2)/bills/${BILL_ID}/outputs/"
