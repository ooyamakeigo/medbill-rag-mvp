MedBill RAG MVP (Compute Engine)

Minimal MVP for:
- GCS bills/{bill_id}/ docs (EOB / Itemized / Statement)
- Document AI OCR
- Vertex AI Gemini analysis w/ lightweight RAG (Base + optional Overlay placeholder)
- Outputs saved back to bills/{bill_id}/outputs/

Expected input structure (CASE bucket):
gs://<BUCKET_CASE>/bills/{bill_id}/
  - eob.pdf (optional)
  - itemized_bill.pdf (optional)
  - statement.pdf (optional)

Outputs:
gs://<BUCKET_CASE>/bills/{bill_id}/outputs/
  - findings.json
  - report.md
  - email_draft.txt

Setup:
1) python3 -m venv .venv && source .venv/bin/activate
2) pip install -r requirements.txt
3) cp .env.example .env && edit values
4) export PYTHONPATH=src

Run:
bash scripts/run_bill_folder.sh <bill_id>

Notes:
- Do NOT put PHI into this repo.
- rag_base/ must be non-PHI.
