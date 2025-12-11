from __future__ import annotations
from typing import Any, Dict, List

# 「患者主導」であることを明記した、非弁/非医療を意識した文面テンプレ
# - 具体的な減額・修正要求の“論点”は記述するが
# - 法律行為の代理や断定的な法的主張、威圧的表現は避ける
# - 署名欄で「患者自身が内容に同意し送付する」ことを明確にする


def build_hospital_letter_prompt(meta: Dict[str, Any], findings_json: Dict[str, Any], user_name: str = None) -> str:
    """
    Build prompt for generating patient-led hospital letter using LLM.
    This letter will be sent to the hospital's billing department.
    """
    provider = meta.get("provider_name") or "[Hospital / Facility Name]"
    state = meta.get("provider_state") or ""
    payer = meta.get("payer_name") or "[Insurance (if applicable)]"
    plan = meta.get("plan_name") or ""

    dos_from = meta.get("dos_from") or meta.get("service_date_from") or "[Service Date From]"
    dos_to = meta.get("dos_to") or meta.get("service_date_to") or "[Service Date To]"
    total_charge = meta.get("total_charge") or meta.get("total_amount")
    patient_resp = meta.get("patient_responsibility")

    # Convert to float for formatting, handling both string and numeric types
    def format_currency(value, default="[Amount]"):
        if value is None:
            return default
        try:
            if isinstance(value, str):
                cleaned = value.replace("$", "").replace(",", "").strip()
                num_value = float(cleaned) if cleaned else None
            else:
                num_value = float(value)
            return f"${num_value:,.2f}" if num_value is not None else default
        except (ValueError, TypeError):
            return str(value) if value else default

    total_charge_line = format_currency(total_charge, "[Total Charges]")
    patient_resp_line = format_currency(patient_resp, "[Patient Balance / Responsibility]")

    findings = findings_json.get("findings", [])
    if not isinstance(findings, list):
        findings = []

    # Calculate total potential reduction
    total_reduction = 0
    for f in findings:
        reduction_amt = f.get("estimated_reduction_amount", "")
        if reduction_amt and "$" in str(reduction_amt):
            try:
                import re
                amounts = re.findall(r'\$[\d,]+\.?\d*', str(reduction_amt))
                if amounts:
                    amt_str = amounts[0].replace("$", "").replace(",", "")
                    amt = float(amt_str)
                    total_reduction += amt
            except:
                pass

    total_reduction_line = f"${total_reduction:,.2f}" if total_reduction > 0 else "TBD (requires additional information)"

    return f"""
You are writing a professional, patient-led letter to a hospital's billing department requesting bill review and reduction.

This letter MUST be written as if the PATIENT THEMSELVES wrote it. The tone should be:
- Professional and respectful
- Clear and specific about reduction requests
- Patient-led (not from a third party)
- Non-accusatory but firm about rights
- Focused on administrative review, not legal threats

[Letter Recipient]
To: Patient Financial Services / Billing Department
Hospital/Facility: {provider} {f'({state})' if state else ''}

[Patient Information]
Patient Name: {user_name or "[Your Full Name]"}
Date of Birth: [MM/DD/YYYY]
Account Number(s): [If known]
Claim Number(s): [If known]
Phone / Email: [Your Contact Info]

[Case Details]
Dates of Service: {dos_from} to {dos_to}
Insurance (if applicable): {payer} {f' / {plan}' if plan else ''}
Total charges shown: {total_charge_line}
Amount currently billed to me: {patient_resp_line}
Estimated total reduction potential: {total_reduction_line}

[Analysis Findings]
{findings_json}

[Critical Requirements]

1. **Letter Structure** (follow this exact format):
   - Header: "PATIENT-LED BILL REVIEW & ASSISTANCE REQUEST"
   - Subheader: "(Copy/paste into Google Docs, fill placeholders, then sign before sending)"
   - To: Patient Financial Services / Billing Department
   - Hospital/Facility name
   - Re: line with subject
   - Patient information section (name, DOB, account numbers, contact)
   - Dates of service and insurance info
   - Summary of amounts
   - Professional greeting
   - Main body paragraphs
   - Specific reduction requests section
   - Requested actions section
   - Closing paragraph
   - Patient attestation section
   - Signature lines
   - Attachments list

2. **Main Body Content** - MUST include for EACH finding:
   a) **WHAT can be reduced**:
      - Specific line items, charges, or portions of the bill
      - Be very specific (e.g., "Line item 12345 for $2,500", "Entire bill eligible for charity care", "OON balance billing of $1,200")

   b) **WHY it can be reduced** (legal/policy basis):
      - Reference specific laws: IRS 501(r), No Surprises Act (NSA), state regulations
      - Reference hospital policies: FAP (Financial Assistance Policy), self-pay discounts
      - Reference calculation rules: deductible, copay, coinsurance, OOP max
      - Be specific: "IRS 501(r) requires your hospital to provide FAP for households at or below 200% FPL"
      - Quote policy sections when available

   c) **HOW MUCH can be reduced**:
      - Include specific dollar amounts when available
      - If amount is calculable, show the calculation or state the exact amount
      - If amount requires additional info, state what's needed and provide estimate range
      - Format: "$X,XXX.XX" or "Estimated $X,XXX - $X,XXX" or "Requires [specific info] to calculate"

   d) **Supporting Evidence**:
      - Quote relevant sections from documents (EOB, statement, itemized bill)
      - Reference specific policy documents when available
      - Include line numbers or charge codes when applicable

3. **Patient-Led Language**:
   - Write in first person ("I", "my", "me")
   - Use phrases like:
     * "I am writing to request..."
     * "Based on my review of my bill..."
     * "I believe there may be an error..."
     * "I would appreciate your review of..."
   - NEVER use third-party language like "we", "our analysis", "our team"
   - Make it clear the patient personally reviewed their documents

4. **Professional Tone**:
   - Respectful and courteous
   - Focus on administrative review, not legal action
   - Express appreciation for their assistance
   - Avoid accusatory language
   - Be firm but polite about rights

5. **Specific Reduction Requests Section**:
   For each finding, create a numbered section with:
   - Clear title describing the issue
   - What can be reduced (specific)
   - Why it can be reduced (legal/policy basis with citations)
   - Estimated reduction amount
   - Supporting evidence quotes
   - What additional information patient can provide

6. **Requested Actions Section**:
   - List specific actions requested from hospital
   - Be clear about what patient wants (review, adjustment, application process, etc.)
   - Include timeline expectations if appropriate

7. **Patient Attestation** (CRITICAL - must include):
   Include this exact section before signature:

   "PATIENT ATTESTATION (Please read before signing)
   I confirm that this letter reflects my own request for a review of my bill and available assistance options.
   I have personally reviewed my medical bills, insurance documents, and relevant policies.
   Any third-party support I may have received was administrative or informational in nature and does not constitute legal or medical advice.
   I understand that I am responsible for the content I choose to send and I am sending this letter under my own name and authority."

8. **Signature Section** (must include):
   - Patient Signature line: "Patient Signature: _______________________________   Date: _______________"
   - Printed Name line: "Printed Name: ____________________________________"
   - Note: These are placeholders for the patient to fill in

9. **Attachments List**:
   - List documents that should be attached (Statement, Itemized Bill, EOB, etc.)

[Format Guidelines]
- Use clear, professional business letter format
- Single-spaced, readable paragraphs
- Use bullet points for lists
- Include specific dollar amounts formatted as $X,XXX.XX
- Keep paragraphs concise but complete
- Make it easy to scan and understand

[Important Notes]
- This letter will be copied into Google Docs and sent to the hospital
- The patient will sign it themselves
- It must sound like the patient wrote it personally
- Include all specific reduction opportunities with amounts
- Reference legal/policy basis for each request
- Be professional and respectful throughout

Generate the complete letter now, following all requirements above.
"""


HIGH_IMPACT_ORDER = [
    "CharityCareEligibility",
    "FAPLimitAGB",
    "FinancialAssistance",
    "SelfPayDiscount",
    "PromptPay",
    "NSA_OONBalanceBilling",
    "NetworkMismatch",
    "BenefitCalcError",
    "OOPMaxError",
    "EOBMismatch",
    "Duplicate",
    "Units",
    "Unbundling",
    "TimeMismatch",
    "WrongCode",
    "ModifierError",
    "POSMismatch",
    "StatusMismatch",
    "DRGError",
    "MUEError",
]

FINDING_FRIENDLY = {
    "CharityCareEligibility": "Financial Assistance / Charity Care eligibility review",
    "FAPLimitAGB": "501(r) / AGB related charge limit review (if applicable to this hospital)",
    "FinancialAssistance": "Financial assistance screening and application support",
    "SelfPayDiscount": "Self-pay / uninsured discount review",
    "PromptPay": "Prompt-pay / paid-in-full discount review",
    "NSA_OONBalanceBilling": "No Surprises Act / out-of-network balance billing compliance check",
    "NetworkMismatch": "In-network vs out-of-network classification review",
    "BenefitCalcError": "Insurance benefit calculation / patient responsibility accuracy review",
    "OOPMaxError": "Out-of-pocket maximum application review",
    "EOBMismatch": "Reconciliation between hospital bill and insurer EOB",
    "Duplicate": "Duplicate charge review",
    "Units": "Units/quantity reasonableness review",
    "Unbundling": "Bundling / NCCI-style consistency review",
    "TimeMismatch": "Time/length-of-stay consistency review",
    "WrongCode": "Coding / revenue code accuracy review",
    "ModifierError": "Modifier usage review",
    "POSMismatch": "Place of service classification review",
    "StatusMismatch": "Observation vs inpatient status review",
    "DRGError": "DRG assignment review",
    "MUEError": "MUE / structural quantity outlier review",
}

def _sort_findings(findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    order_index = {k: i for i, k in enumerate(HIGH_IMPACT_ORDER)}
    return sorted(
        findings,
        key=lambda f: order_index.get(str(f.get("type")), 999)
    )

def _extract_evidence_quotes(f: Dict[str, Any], limit: int = 3) -> List[str]:
    # evidence_quotes が文字列配列 or dict配列のどちらでも安全に処理
    eq = f.get("evidence_quotes") or []
    out: List[str] = []

    if isinstance(eq, list):
        for item in eq:
            if isinstance(item, str) and item.strip():
                out.append(item.strip())
            elif isinstance(item, dict):
                txt = item.get("quote") or item.get("text") or ""
                label = item.get("source") or item.get("label") or ""
                txt = str(txt).strip()
                label = str(label).strip()
                if txt:
                    out.append(f"{label}: {txt}" if label else txt)
            if len(out) >= limit:
                break
    elif isinstance(eq, str) and eq.strip():
        out.append(eq.strip())

    return out[:limit]

def build_patient_led_hospital_letter(meta: Dict[str, Any], findings_json: Dict[str, Any]) -> str:
    provider = meta.get("provider_name") or "[Hospital / Facility Name]"
    state = meta.get("provider_state") or ""
    payer = meta.get("payer_name") or "[Insurance (if applicable)]"
    plan = meta.get("plan_name") or ""

    dos_from = meta.get("dos_from") or "[Service Date From]"
    dos_to = meta.get("dos_to") or "[Service Date To]"
    total_charge = meta.get("total_charge") or "[Total Charges]"
    patient_resp = meta.get("patient_responsibility") or "[Patient Balance / Responsibility]"

    findings = findings_json.get("findings") or []
    if not isinstance(findings, list):
        findings = []

    findings = _sort_findings(findings)

    # 署名欄の“患者主導”明記を強化
    patient_attestation = """
PATIENT ATTESTATION (Please read before signing)
I confirm that this letter reflects my own request for a review of my bill and available assistance options.
Any third-party support I may have received was administrative or informational in nature and does not constitute legal or medical advice.
I understand that I am responsible for the content I choose to send and I am sending this letter under my own name and authority.
""".strip()

    # 本文（Google Docs に貼って完成する体裁）
    lines: List[str] = []

    lines.append("PATIENT-LED BILL REVIEW & ASSISTANCE REQUEST")
    lines.append("(Copy/paste into Google Docs, fill placeholders, then sign before sending)")
    lines.append("")
    lines.append("To: Patient Financial Services / Billing Department")
    lines.append(f"Hospital/Facility: {provider} {f'({state})' if state else ''}")
    lines.append("")
    lines.append("Re: Request for review of charges, insurance processing, and available patient assistance options")
    lines.append("")
    lines.append("Patient Name: [Your Full Name]")
    lines.append("Date of Birth: [MM/DD/YYYY]")
    lines.append("Account Number(s): [If known]")
    lines.append("Claim Number(s): [If known]")
    lines.append("Phone / Email: [Your Contact Info]")
    lines.append("")
    lines.append(f"Dates of Service: {dos_from} to {dos_to}")
    lines.append(f"Insurance (if applicable): {payer} {f' / {plan}' if plan else ''}")
    lines.append("")
    lines.append("Summary of amounts (per my current records):")
    lines.append(f"- Total charges shown: {total_charge}")
    lines.append(f"- Amount currently billed to me / patient responsibility: {patient_resp}")
    lines.append("")
    lines.append("Dear Patient Financial Services Team,")
    lines.append("")
    lines.append(
        "I am writing to request a careful review of my bill and related insurance processing for the dates of service listed above. "
        "Before I arrange payment, I would appreciate your help confirming charge accuracy, correcting any discrepancies, and "
        "reviewing whether I qualify for any assistance or discounts your hospital offers."
    )
    lines.append("")
    lines.append(
        "This is a patient-led request intended to ensure accurate billing and fair application of hospital policies and applicable coverage rules. "
        "I am not requesting legal representation, and I am not asserting any allegation beyond asking for an administrative review and correction where appropriate."
    )
    lines.append("")

    # 具体論点セクション
    if findings:
        lines.append("Key review topics based on my documents:")
        lines.append("")

        for idx, f in enumerate(findings, start=1):
            ftype = str(f.get("type") or "Unknown")
            conf = f.get("confidence")
            conf_str = ""
            if isinstance(conf, (int, float)):
                conf_str = f" (confidence: {conf:.2f})"

            title = FINDING_FRIENDLY.get(ftype, ftype)

            lines.append(f"{idx}. {title}{conf_str}")
            lines.append("   - Why I’m requesting this review:")
            lines.append(
                "     Based on the bill/EOB/statement I currently have, this area may warrant verification for accuracy and policy compliance. "
                "I would appreciate your team confirming whether an adjustment, reprocessing, or application of a hospital discount/assistance rule is appropriate."
            )

            # evidence quote（短く）
            ev = _extract_evidence_quotes(f, limit=3)
            if ev:
                lines.append("   - Supporting lines from my documents (for your reference):")
                for q in ev:
                    # 長すぎる引用は避けつつ、貼り付けやすい体裁
                    qt = q.strip()
                    if len(qt) > 260:
                        qt = qt[:260] + "..."
                    lines.append(f"     • {qt}")

            # next actions（患者に必要な追加資料）
            na = f.get("next_actions") or []
            if isinstance(na, list) and na:
                lines.append("   - Additional information I can provide if needed:")
                for a in na[:4]:
                    a = str(a).strip()
                    if a:
                        lines.append(f"     • {a}")

            lines.append("")

    else:
        lines.append("Key review topics:")
        lines.append("")
        lines.append("1. Charge accuracy check (line-item validation if available)")
        lines.append("2. Insurance processing and patient responsibility calculation")
        lines.append("3. Financial assistance / hardship review, if offered by this hospital")
        lines.append("4. Self-pay or prompt-pay discounts, if applicable")
        lines.append("")

    # 依頼事項の明確化
    lines.append("Requested actions:")
    lines.append("• Please provide or confirm an itemized bill if not already provided.")
    lines.append("• Please review the charges for accuracy, including any potential duplicates, unit/quantity anomalies, or bundled service consistency.")
    lines.append("• Please reconcile any differences between the hospital billing and insurer EOB (if applicable).")
    lines.append("• Please confirm whether I qualify for financial assistance, hardship programs, self-pay discounts, or prompt-pay options.")
    lines.append("• If corrections or reprocessing are needed, please advise me of the expected next steps and timeline.")
    lines.append("")

    # 丁寧な締め
    lines.append(
        "I appreciate your assistance and your time. My goal is to resolve this matter promptly once I understand the accurate balance "
        "and any available programs that may reduce my out-of-pocket burden."
    )
    lines.append("")

    # 署名・患者主導明記
    lines.append(patient_attestation)
    lines.append("")
    lines.append("Patient Signature: _______________________________   Date: _______________")
    lines.append("Printed Name: ____________________________________")
    lines.append("")
    lines.append("Attachments (as applicable):")
    lines.append("• Statement")
    lines.append("• Itemized Bill (if provided)")
    lines.append("• EOB (if provided)")
    lines.append("• Any supporting documents requested by the hospital (income verification, insurance card, etc.)")
    lines.append("")

    return "\n".join(lines)
