from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from textwrap import dedent
from pathlib import Path
import json
from datetime import date


@dataclass
class InsuranceCallInfo:
    """
    Ops assumption for MVP:
    - Insurer verification is generally performed first.
    - Therefore confirmed defaults to True unless explicitly set False in meta.
    - Do NOT include member IDs / claim numbers in this email.
    """
    confirmed: bool = True
    payer_name: Optional[str] = None
    summary: Optional[str] = None
    rep_name: Optional[str] = None
    call_date: Optional[str] = None


def _normalize_bool(value: Any, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("true", "t", "yes", "y", "1"):
            return True
        if v in ("false", "f", "no", "n", "0"):
            return False
    return default


def build_hospital_inquiry_email(
    meta: Dict[str, Any],
    findings: Optional[List[Dict[str, Any]]] = None,
    insurance_call: Optional[InsuranceCallInfo] = None,
) -> str:
    """
    Patient-led inquiry email draft to hospital.
    Safe tone: inquiry-based, no legal demands, includes patient signature block.
    """
    insurance_call = insurance_call or InsuranceCallInfo()

    hospital = meta.get("provider_name") or meta.get("provider_name_normalized") or "the hospital"
    state = meta.get("provider_state") or ""
    payer = insurance_call.payer_name or meta.get("payer_name") or "my insurer"

    reason_for_visit = meta.get("reason_for_visit") or "[brief reason for visit]"
    concern_summary = meta.get("patient_concern_summary") or "[brief summary of what feels inconsistent, incorrect, or unclear]"

    bullet_lines: List[str] = []
    if findings:
        for f in findings[:6]:
            et = f.get("type") or f.get("error_type") or "Potential issue"
            short = f.get("summary") or f.get("description") or ""
            bullet_lines.append(f"- {et}: {short}" if short else f"- {et}")

    bullets = "\n".join(bullet_lines) if bullet_lines else "- [Potential billing/coverage/assistance angles identified in the attached summary]"

    if insurance_call.confirmed:
        rep_line = " I spoke with a representative." if not insurance_call.rep_name else f" I spoke with a representative ({insurance_call.rep_name})."
        date_line = f" on {insurance_call.call_date}" if insurance_call.call_date else ""
        summary_line = f"\n- Summary from {payer}: {insurance_call.summary}" if insurance_call.summary else ""

        insurance_section = dedent(f"""
        Insurance confirmation
        - I contacted {payer}{date_line}.{rep_line}
        - Based on that discussion, my understanding is that there may be a billing/processing/network classification issue that contributed to my current balance.
        {summary_line}
        """).strip()
    else:
        insurance_section = dedent(f"""
        Insurance confirmation (to be updated by the patient if applicable)
        - I plan to contact {payer} to confirm benefit processing and network classification.
        - If needed, I will follow up with details from that conversation.
        """).strip()

    today = date.today().isoformat()

    body = dedent(f"""
    Subject: Patient request for billing review and assistance

    To the Patient Financial Services / Billing Team at {hospital},

    I hope you are well. I am writing to request a review of my recent billing related to care received at {hospital} {f"({state})" if state else ""}.
    I am seeking clarification and, if applicable, corrections or appropriate financial assistance options.

    Visit context
    - Reason for visit: {reason_for_visit}
    - Why I am concerned: {concern_summary}

    Key points I would appreciate you reviewing
    {bullets}

    {insurance_section}

    What I am requesting
    - Please review the itemized charges, coding/classification, and account status for accuracy.
    - If any corrections are appropriate, I kindly request that the claim/charges be adjusted and resubmitted as needed.
    - If I may qualify for Financial Assistance/Charity Care or any uninsured/self-pay/prompt-pay options, I would appreciate guidance on how to apply and what documents you need.

    Attachments
    - Statement / Itemized Bill / EOB (if applicable)
    - Summary of potential concern areas (patient-led review)

    Patient acknowledgment / signature
    I, the patient, confirm that this message reflects my own concerns and questions.
    Any third-party drafting assistance I used is not providing legal or medical advice.
    I will provide separate written authorization if I wish the hospital to communicate with a designated representative.

    Patient Name: ______________________________

    Signature: _________________________________

    Date: {today}

    Preferred contact:
    Email: _________________________________
    Phone: _________________________________
    """).strip()

    return body


def _extract_findings_from_result(result: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
    analysis = result.get("analysis") or result.get("llm_analysis") or result.get("result") or {}
    if isinstance(analysis, dict):
        f = analysis.get("findings")
        if isinstance(f, list):
            return f
    return None


def _extract_meta_from_result(result: Dict[str, Any]) -> Dict[str, Any]:
    meta = result.get("meta") or result.get("metadata") or {}
    return meta if isinstance(meta, dict) else {}


def write_hospital_email_output(
    bill_id: str,
    result: Optional[Dict[str, Any]] = None,
    out_root: str = "output",
) -> str:
    """
    Create output/<bill_id>/04_email_to_hospital.txt
    """
    result = result or {}
    out_dir = Path(out_root) / bill_id
    out_dir.mkdir(parents=True, exist_ok=True)

    meta = _extract_meta_from_result(result)

    if not meta:
        meta_path = out_dir / "meta.json"
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception:
                meta = {}

    findings = _extract_findings_from_result(result)

    confirmed = _normalize_bool(meta.get("insurance_call_confirmed", None), default=True)

    insurance_call = InsuranceCallInfo(
        confirmed=confirmed,
        payer_name=meta.get("payer_name"),
        summary=meta.get("insurance_call_summary"),
        rep_name=meta.get("insurance_call_rep_name"),
        call_date=meta.get("insurance_call_date"),
    )

    email_text = build_hospital_inquiry_email(
        meta=meta,
        findings=findings,
        insurance_call=insurance_call,
    )

    out_path = out_dir / "04_email_to_hospital.txt"
    out_path.write_text(email_text, encoding="utf-8")
    return str(out_path)
