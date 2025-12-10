import json
from pathlib import Path

from .case_discovery import list_bill_folder_files, pick_best_by_kind
from .ocr_docai import ocr_gcs_file
from .extract_structured import extract_from_text
from .hydrate_overlay import ensure_hospital_overlay, ensure_payer_overlay
from .gcs_kb import load_local_global_kb_text
from .gcs_case import upload_json_to_bill_outputs, upload_text_to_bill_outputs
from .client import get_genai_client
from .config import settings
from .prompts import build_reduction_prompt
from .report_writer import build_report_md
from .email_writer import build_user_email_prompt
from .hospital_letter_writer import build_patient_led_hospital_letter


def run_bill_folder(bill_folder_id: str) -> dict:
    files = list_bill_folder_files(bill_folder_id)
    if not files:
        out = {"bill_folder_id": bill_folder_id, "error": "No files found under bills/{id}/"}
        upload_json_to_bill_outputs(bill_folder_id, "findings.json", out)
        return out

    picked = pick_best_by_kind(files)

    def ocr_one(f):
        if not f:
            return ""
        return ocr_gcs_file(f["gcs_uri"], f["mime_type"])

    eob_text = ocr_one(picked.get("EOB"))
    itemized_text = ocr_one(picked.get("ITEMIZED"))
    statement_text = ocr_one(picked.get("STATEMENT"))

    extracted = []
    for t in [eob_text, itemized_text, statement_text]:
        if t and t.strip():
            extracted.append(extract_from_text(t))

    meta = {
        "provider_name": None,
        "provider_state": None,
        "payer_name": None,
        "plan_name": None,
        "dos_from": None,
        "dos_to": None,
        "total_charge": None,
        "patient_responsibility": None,
        "doc_types_detected": [m.get("doc_type") for m in extracted if isinstance(m, dict)],
        "files_detected": [f.get("blob_name") for f in files],
        "picked": {k: (v.get("blob_name") if v else None) for k, v in picked.items() if k != "UNKNOWN"},
    }

    # Merge best-known fields
    for m in extracted:
        if not isinstance(m, dict):
            continue
        for k in ["provider_name","provider_state","payer_name","plan_name","dos_from","dos_to","total_charge","patient_responsibility"]:
            if meta.get(k) is None and m.get(k) is not None:
                meta[k] = m.get(k)

    # ===== Overlay (optional in MVP) =====
    hid = None
    pid = None
    if settings.bucket_kb:
        try:
            if meta.get("provider_name"):
                hid = ensure_hospital_overlay(meta["provider_name"], meta.get("provider_state"))
            if meta.get("payer_name"):
                pid = ensure_payer_overlay(meta["payer_name"], meta.get("plan_name"))
        except Exception as e:
            meta["overlay_warning"] = f"overlay skipped due to error: {type(e).__name__}"

    meta["hospital_id"] = hid
    meta["payer_id"] = pid

    # Load non-PHI base docs locally
    project_root = Path(__file__).resolve().parents[2]
    global_kb = load_local_global_kb_text(str(project_root / "rag_base"))
    overlay_kb = ""  # MVP: keep empty; add real overlay retrieval later

    prompt = build_reduction_prompt(
        eob_text=eob_text,
        itemized_text=itemized_text,
        statement_text=statement_text,
        global_kb=global_kb,
        overlay_kb=overlay_kb,
        meta=meta,
    )

    client = get_genai_client()
    resp = client.models.generate_content(
        model=settings.model_id,
        contents=[prompt],
        config={"response_mime_type":"application/json"},
    )
    findings_json = json.loads(resp.text)

    # 1) findings.json
    upload_json_to_bill_outputs(bill_folder_id, "findings.json", findings_json)

    # 2) report.md
    report_md = build_report_md(bill_folder_id, meta, findings_json)
    upload_text_to_bill_outputs(
        bill_folder_id,
        "report.md",
        report_md,
        content_type="text/markdown; charset=utf-8"
    )

    # 3) email_draft.txt
    email_prompt = build_user_email_prompt(None, findings_json)
    email_resp = client.models.generate_content(
        model=settings.model_id,
        contents=[email_prompt],
    )
    upload_text_to_bill_outputs(bill_folder_id, "email_draft.txt", email_resp.text)

    # 4) hospital_letter_for_docs.txt  ← NEW
    #    患者主導・署名欄付きの説明/交渉ドキュメント（Google Docs 貼り付け用）
    hospital_letter = build_patient_led_hospital_letter(meta, findings_json)
    upload_text_to_bill_outputs(
        bill_folder_id,
        "hospital_letter_for_docs.txt",
        hospital_letter,
        content_type="text/plain; charset=utf-8"
    )

    return {
        "bill_folder_id": bill_folder_id,
        "meta": meta,
        "findings": findings_json,
        "saved": True,
    }
