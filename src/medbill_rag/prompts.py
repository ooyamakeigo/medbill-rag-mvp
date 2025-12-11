from typing import Dict, Any, Optional


def build_reduction_prompt(
    meta: Dict[str, Any],
    bill_texts: Optional[Dict[str, str]] = None,
    retrieved_docs_text: str = "",
    eob_text: str = "",
    itemized_text: str = "",
    statement_text: str = "",
    global_kb: str = "",
    overlay_kb: str = "",
    **kwargs
) -> str:
    """
    Prompt builder for findings.json generation.
    Identifies bill reduction opportunities with specific amounts, evidence, and legal basis.
    """
    # Handle both old and new calling conventions
    if bill_texts:
        eob_text = bill_texts.get("eob_text", eob_text)
        statement_text = bill_texts.get("statement_text", statement_text)
        itemized_text = bill_texts.get("itemized_text", itemized_text)

    # Combine retrieved docs
    retrieved_docs_text = retrieved_docs_text or ""
    if global_kb:
        retrieved_docs_text = f"{global_kb}\n\n{retrieved_docs_text}" if retrieved_docs_text else global_kb
    if overlay_kb:
        retrieved_docs_text = f"{retrieved_docs_text}\n\n{overlay_kb}" if retrieved_docs_text else overlay_kb

    hospital = meta.get("provider_name") or meta.get("provider_name_normalized") or "Unknown Hospital"
    state = meta.get("provider_state") or "Unknown"
    payer = meta.get("payer_name") or "Unknown"
    total_charge = meta.get("total_charge") or meta.get("total_amount")
    patient_resp = meta.get("patient_responsibility")

    household = meta.get("household_size")
    income_range = meta.get("annual_income_range")
    income_usd = meta.get("annual_income_usd")

    household_line = str(household) if household is not None else "unknown"
    income_line = str(income_range) if income_range else (str(income_usd) if income_usd is not None else "unknown")

    # Convert to float for formatting, handling both string and numeric types
    def format_currency(value):
        if value is None:
            return "unknown"
        try:
            if isinstance(value, str):
                # Remove $ and commas, then convert
                cleaned = value.replace("$", "").replace(",", "").strip()
                num_value = float(cleaned) if cleaned else None
            else:
                num_value = float(value)
            return f"${num_value:,.2f}" if num_value is not None else "unknown"
        except (ValueError, TypeError):
            return str(value) if value else "unknown"

    total_charge_line = format_currency(total_charge)
    patient_resp_line = format_currency(patient_resp)

    prompt = f"""
You are a US medical billing reduction analyst specializing in identifying bill reduction opportunities with concrete evidence and legal basis.

Your task is to analyze medical bills and identify specific reduction opportunities with:
1. WHAT can be reduced (specific line items, charges, or overall bill)
2. WHY it can be reduced (legal basis, policy basis, or calculation error)
3. HOW MUCH can potentially be reduced (specific dollar amounts when calculable)

We focus on 5 priority reduction angles:
1) Charity Care / Financial Assistance eligibility (IRS 501(r), FPL-based)
2) Self-pay / cash price discount opportunities
3) No Surprises Act (NSA) / out-of-network balance billing protection
4) In-network vs out-of-network classification errors
5) Insurance benefit calculation/processing errors (deductible, copay, coinsurance, OOP max)

[Patient Information]
- Household size: {household_line}
- Annual income: {income_line}

[Case Context]
- Hospital/Facility: {hospital}
- State: {state}
- Insurance/Payer: {payer}
- Total charges: {total_charge_line}
- Current patient responsibility: {patient_resp_line}

[Retrieved Policy & Legal Documents]
{retrieved_docs_text if retrieved_docs_text else "(No policy documents retrieved - base analysis on general rules and OCR text)"}

[OCR Text from Documents]
[EOB - Explanation of Benefits]
{eob_text[:6000] if eob_text else "(EOB not provided)"}

[STATEMENT - Patient Statement]
{statement_text[:6000] if statement_text else "(Statement not provided)"}

[ITEMIZED BILL - Detailed Charges]
{itemized_text[:8000] if itemized_text else "(Itemized bill not provided)"}

[Critical Instructions]
1. For each finding, you MUST identify:
   - Specific reduction opportunity: What exact charge, line item, or portion of the bill can be reduced?
   - Legal/policy basis: Reference specific laws (501(r), NSA, state regulations), hospital policies (FAP), or calculation rules
   - Estimated reduction amount: Calculate specific dollar amounts when possible. If calculation requires additional info, state what's needed and provide a reasonable estimate range.

2. Evidence requirements:
   - Quote exact text from documents that supports the finding
   - Reference specific policy sections, FPL thresholds, or legal provisions
   - Include line numbers or charge codes when available

3. Accuracy requirements:
   - Do NOT invent claim numbers, patient IDs, or document references
   - If information is missing, clearly state what is needed
   - Use high-confidence findings based on rules and evidence
   - For Charity Care: Calculate FPL percentage using household size and income range. If range is too broad, state assumptions clearly.

4. Output format - Return JSON only:
{{
  "findings": [
    {{
      "type": "CharityCareEligibility | SelfPayDiscount | NSA_OONBalanceBilling | NetworkMismatch | BenefitCalcError | Other",
      "confidence": "high | medium | low",
      "reduction_opportunity": "Specific description of what can be reduced (e.g., 'Line item 12345 for $2,500', 'Entire bill eligible for 100% charity care', 'OON balance billing of $1,200')",
      "legal_basis": "Specific legal or policy basis (e.g., 'IRS 501(r) requires FAP for households at or below 200% FPL', 'NSA Section 2799B-1 prohibits balance billing for emergency services', 'Hospital FAP policy states 100% discount for income below 150% FPL')",
      "estimated_reduction_amount": "Specific dollar amount when calculable (e.g., '$2,500', '$0 (full charity care)', 'Estimated $800-$1,200 based on cash price comparison'). If not calculable, state 'Requires additional information: [what is needed]'",
      "current_amount": "Current charge/amount for this item (if applicable)",
      "evidence_quotes": ["Exact quotes from documents supporting this finding"],
      "missing_info": ["What additional information is needed to confirm or calculate"],
      "next_actions": ["Specific actions patient should take (e.g., 'Submit FAP application with tax return', 'Request itemized bill', 'Contact insurance to verify network status')"]
    }}
  ],
  "overall_notes": "Summary of overall reduction potential and key next steps"
}}
"""
    return prompt.strip()
