from __future__ import annotations
from typing import Any, Dict, List


def build_hospital_letter_prompt(meta: Dict[str, Any], findings_json: Dict[str, Any], user_name: str = None) -> str:
    """
    Build prompt for generating a patient-led hospital letter using LLM.
    This letter will be sent to the hospital's billing department.

    Goal:
    - Patient-led, non-legalistic, non-threatening
    - Clear, concrete, and administratively useful for PFS/billing staff
    - Focus on 2–3 highest-impact topics, not every tiny discrepancy
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

    # Rough total potential reduction – for context only, not to be promised in the letter
    total_reduction = 0.0
    for f in findings:
        reduction_amt = f.get("estimated_reduction_amount", "")
        if reduction_amt and "$" in str(reduction_amt):
            try:
                import re
                amounts = re.findall(r"\$[\d,]+\.?\d*", str(reduction_amt))
                if amounts:
                    amt_str = amounts[0].replace("$", "").replace(",", "")
                    amt = float(amt_str)
                    total_reduction += amt
            except Exception:
                pass

    total_reduction_line = f"${total_reduction:,.2f}" if total_reduction > 0 else "TBD (requires additional information)"

    return f"""
You are writing a professional, **patient-led** letter to a hospital's billing / patient financial services department
requesting a review of the patient's bill and potential reduction options.

This letter MUST be written as if the PATIENT THEMSELVES wrote it. The tone should be:
- Professional and respectful
- Clear and specific about what the patient is asking the hospital to review
- Patient-led (not from a third party)
- Non-accusatory and non-threatening
- Focused on administrative review and clarification, not legal demands or aggressive rights language

Use the metadata and analysis findings below as *background only*:

[Case Metadata]
- Hospital/Facility: {provider} {f"({state})" if state else ""}
- Insurance/Payer: {payer}{f" / {plan}" if plan else ""}
- Dates of Service: {dos_from} to {dos_to}
- Total charges (if known): {total_charge_line}
- Current patient responsibility (if known): {patient_resp_line}
- Rough estimated reduction opportunity (for your context, NOT to be promised): {total_reduction_line}

[Analysis Findings JSON – FOR YOUR REFERENCE ONLY, DO NOT COPY RAW JSON]
{findings_json}

The JSON above contains one or more findings with:
- type, confidence, reduction_opportunity, legal_basis, estimated_reduction_amount, current_amount,
- evidence_quotes, missing_info, next_actions, etc.

You MUST use this JSON as internal guidance, BUT:
- DO NOT include any raw JSON in the letter.
- DO NOT mention every single finding if there are many.
- DO NOT include 'MinorDeMinimis' type findings or very small, low-impact amounts as separate numbered items.
- Focus on at most **2–3 of the most financially meaningful or high-confidence topics**.

[Critical Requirements]

1. **Letter Structure** (follow this general structure):
   - Header: "PATIENT-LED BILL REVIEW & ASSISTANCE REQUEST"
   - Subheader: "(Copy/paste into Google Docs, fill placeholders, then sign before sending)"
   - To: Patient Financial Services / Billing Department
   - Hospital/Facility name
   - Re: line with subject (e.g., "Request for Bill Review, Coding Verification, and Payment Options")
   - [Patient Information] section (name, DOB, account numbers, contact)
   - [Case Details] section (dates of service, insurance, summary of amounts)
   - A short introductory paragraph explaining why the patient is writing
   - 2–3 numbered sections, each corresponding to a key review topic derived from findings_json
   - A "Requested Actions" section summarizing what the patient is asking the hospital to do
   - A closing paragraph
   - A Patient Attestation section (provided below)
   - Signature lines
   - Attachments list

2. **Main Body Content – For each chosen finding (max 2–3)**:
   a) **WHAT the patient is asking to review / reduce**:
      - Use specific, concrete descriptions: e.g., "the $30 copay applied to the office visit on 09/03/25".
      - Avoid broad statements like "entire bill must be written off" unless the finding has high confidence and strong policy support.
      - For charity care / FAP in high-income or low-confidence cases, frame it as a request for clarification, not a demand for forgiveness.

   b) **WHY the patient believes it might be adjustable** (legal/policy/administrative basis):
      - When referencing laws or regulations (e.g., ACA preventive services, IRS 501(r), NSA), phrase them as the patient's understanding, for example:
        * "My understanding is that many non-grandfathered plans cover qualifying preventive services at no cost to the patient."
        * "My understanding is that non-profit hospitals maintain a Financial Assistance Policy under IRS 501(r)."
      - Avoid absolute legal conclusions like "this violates the law" or "this is only valid if...".
      - Use soft, administrative language: "I would appreciate it if your team could review whether this is consistent with your policies and my plan's rules."

   c) **HOW MUCH might be reduced (if appropriate)**:
      - Use specific amounts or conservative ranges when they exist in findings_json.
      - Make it clear that these are estimates (e.g., "approximately", "in the range of", "could reduce my balance by around $X").
      - DO NOT promise a total combined reduction number as something the hospital "must" grant.

   d) **Supporting Evidence**:
      - Briefly mention relevant lines from the statement/EOB (date, general description, patient responsibility).
      - Keep quotes short and practical (e.g., "09/03/25 Preventive Service... Your share: 0.00").
      - Do not over-quote long passages.

   e) **Missing information / openness to provide documents**:
      - Where findings_json lists "missing_info", mention that you are willing to provide medical notes, income documentation, etc., if needed.

3. **Charity Care / FAP specific guidance**:
   - If findings_json suggests that income is high relative to FPL, or confidence is "low":
     * Treat the charity care topic as a **clarification request**, not a stated eligibility.
     * Use language like:
       "I understand that my income may be above typical thresholds for standard financial assistance,
        but I would appreciate clarification on whether any partial discounts, catastrophic relief,
        or medical indigency review might apply in my situation."
     * DO NOT state or imply "I qualify" or "the balance should be forgiven".
   - DO NOT introduce specific FPL multiples (e.g., "up to 500% or 600% FPL") unless those exact numbers are explicitly present in the findings_json or policy text.

4. **Self-pay / Prompt-pay discount guidance**:
   - Make it clear that any prompt-pay or lump-sum discount is **discretionary**, not legally required.
   - Use phrasing like:
     * "I have heard that some hospitals are sometimes able to offer a courtesy discount for immediate payment of large balances."
     * "If possible, I would like to request a courtesy prompt-pay discount in exchange for paying the remaining balance in full."
   - Do NOT state that hospitals "must" offer a specific percentage.
   - You may mention a conservative range (e.g., "around 10–20%") if it appears in findings_json, but frame it as an example, not a demand.

5. **Preventive services / copay (ACA) guidance**:
   - Use "PreventiveCostSharingCheck" findings to phrase the issue as:
     * "My understanding is that many in-network preventive services are covered with no copay."
     * "Because I see both a preventive service and a separate office visit on the same date, I would appreciate it if you could confirm whether it was appropriate to apply this copay."
   - Avoid absolute statements like "this split billing is only valid if...".
   - Emphasize that you are asking for a **coding/coverage review**, not asserting malpractice or wrongdoing.

6. **Patient-Led Language**:
   - First-person voice ONLY: "I", "my", "me".
   - Explicitly acknowledge that you are not a lawyer or medical professional:
     * e.g., "I am not a legal or medical professional; I am simply trying to understand my bill and ensure it is correct."
   - You MUST also include **one clear English sentence** stating that the patient has already contacted their insurance company:
     * Include this exact sentence in the introductory part of the letter, after mentioning that you reviewed your bill and EOB:
       "I have already contacted my insurance company to ask questions and to clarify how this claim was processed."
   - Never use third-party language like "we", "our analysis", "our team".
   - Make it clear that the patient personally reviewed the bill and documents.

7. **Professional Tone**:
   - Respectful, cooperative, and appreciative.
   - No threats of legal action or complaints.
   - You may say that you will wait for the review outcome before finalizing payment decisions, but frame it calmly and reasonably.

8. **Requested Actions Section**:
   - Summarize the main requests in bullet form, such as:
     * Review specific copay/charge for coding and coverage consistency.
     * Confirm whether any financial assistance or discount programs can apply.
     * Clarify how the deductible and patient responsibility were calculated.
   - Be explicit about what you are asking PFS to do (review, clarify, consider discount), not what they "must" do legally.

9. **Patient Attestation (CRITICAL - include exactly, or with only minimal formatting changes)**:
   Include this attestation section before the signature lines:

   PATIENT ATTESTATION (Please read before signing)
   I confirm that this letter reflects my own request for a review of my bill and available assistance options.
   I have personally reviewed my medical bills, insurance documents, and relevant policies.
   Any third-party support I may have received was administrative or informational in nature and does not constitute legal or medical advice.
   I understand that I am responsible for the content I choose to send and I am sending this letter under my own name and authority.

10. **Signature Section**:
    - Patient Signature line: "Patient Signature: _______________________________   Date: _______________"
    - Printed Name line: "Printed Name: ____________________________________"

11. **Attachments List**:
    - List typical attachments: statement, itemized bill, EOB, and any other relevant docs.

[Format Guidelines]
- Use a clear, professional letter style that will paste cleanly into Google Docs.
- Headings and bullet points are okay (Markdown-style **bold** is acceptable, but not required).
- Keep paragraphs concise but complete.
- Make it easy for the hospital billing staff to quickly see what you are asking them to review and what information you are providing.

Generate the **complete letter now**, following all requirements above.
It should be a single cohesive letter, written in the patient's voice, ready to paste into Google Docs.
"""
