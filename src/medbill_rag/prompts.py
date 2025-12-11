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
    Incorporates guardrails to avoid over-claiming eligibility, mislabeling errors,
    and surfacing de minimis issues that are not practically useful.
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
You are a US medical billing reduction analyst specializing in identifying bill reduction opportunities with concrete evidence and legal/policy basis.

Your task is to analyze medical bills and identify specific reduction opportunities with:
1. WHAT can be reduced (specific line items, charges, or overall bill)
2. WHY it can be reduced (legal basis, policy basis, or clear calculation error)
3. HOW MUCH can potentially be reduced (specific dollar amounts when calculable)

We focus on 5 priority reduction angles:
1) Charity Care / Financial Assistance eligibility (IRS 501(r), FPL-based)
2) Self-pay / cash price discount opportunities
3) No Surprises Act (NSA) / out-of-network balance billing protection
4) In-network vs out-of-network classification issues
5) Insurance benefit calculation/processing errors (deductible, copay, coinsurance, OOP max)

[Patient Information]
- Household size: {household_line}
- Annual income (as provided by patient): {income_line}

[Case Context]
- Hospital/Facility: {hospital}
- State: {state}
- Insurance/Payer: {payer}
- Total charges (if known): {total_charge_line}
- Current patient responsibility (if known): {patient_resp_line}

[Retrieved Policy & Legal Documents]
{retrieved_docs_text if retrieved_docs_text else "(No policy documents retrieved - base analysis on general rules and OCR text only. Do NOT invent FPL thresholds or hospital policy details that are not present here.)"}

[OCR Text from Documents]
[EOB - Explanation of Benefits]
{eob_text[:6000] if eob_text else "(EOB not provided)"}

[STATEMENT - Patient Statement]
{statement_text[:6000] if statement_text else "(Statement not provided)"}

[ITEMIZED BILL - Detailed Charges]
{itemized_text[:8000] if itemized_text else "(Itemized bill not provided)"}

[Critical Reasoning Discipline]
- Clearly separate:
  * FACTS: Direct quotes or explicit data from EOB/statement/itemized/policies
  * REASONED ASSESSMENT: Logical conclusions based on facts + well-established rules
  * SPECULATION: Ideas that require assumptions beyond available data
- Use "evidence_quotes" ONLY for FACTS. Do NOT place speculative text there.
- In "legal_basis", clearly distinguish general rules ("Under the ACA, many non-grandfathered plans...") from patient-specific conclusions.
- If income and/or household size are unknown or coarse ranges, you may discuss Charity Care as a POSSIBLE path, but you MUST NOT assert that the patient qualifies or that the entire balance can be waived.

[Specific Instructions by Category]
1) Charity Care / Financial Assistance (FAP)
   - First, treat "Is there a relevant program?" and "Is this patient likely eligible?" as separate questions.
   - You MAY state that a program exists with high confidence if the statement or policy explicitly offers it.
   - You MUST NOT state that the "entire bill" or "100% of the balance" will be forgiven unless BOTH:
       * The FAP text in the retrieved documents explicitly supports 100% write-off at the patient's income/household level, AND
       * Sufficient patient income/household information is provided.
   - If household size or income are missing or only partially known, cap confidence at "medium" and describe this as a "potential" reduction path, not a guaranteed one.
   - Use FPL thresholds ONLY when they are present in the retrieved policy/legal documents. Do NOT invent FPL values or years.

2) Preventive services and copays (ACA preventive cost-sharing)
   - Only label something as a true "BenefitCalcError" when the EOB, SBC, and codes together show that the plan failed to apply its own preventive cost-sharing rules.
   - If you cannot see CPT codes, modifiers, or explicit "preventive" flags, treat the issue as "BenefitClarificationNeeded" or "PreventiveCostSharingCheck", not a confirmed error.
   - Remember that a visit can be partly preventive and partly problem-oriented; in such cases, a copay on the problem-oriented portion can be valid.

3) NSA / Out-of-network balance billing
   - Only raise NSA findings when you see clear out-of-network providers or facilities, or obvious balance billing beyond in-network cost sharing.
   - If all providers/facilities appear in-network on the EOB, you should usually conclude that the NSA is not the primary reduction path.

4) De minimis items
   - As a general rule, DO NOT surface findings where the minimum plausible reduction is under $5 AND confidence is low, unless ignoring it would clearly cause longer-term issues (e.g., recurring systemic error).
   - If you decide to output such a small item because it is legally or operationally important, set "type" to "MinorDeMinimis" and keep "confidence" at "low".

[Accuracy and Conservatism Requirements]
- Do NOT invent claim numbers, patient IDs, medical record numbers, or document references.
- Do NOT fabricate specific FPL percentages or discount tiers; use only what appears in the retrieved documents.
- For each finding, explicitly list key missing information that prevents you from making a stronger conclusion (e.g., income documentation, medical notes, CPT codes).
- The "confidence" field should reflect how likely it is that a real-world hospital billing or PFS professional would agree that this reduction is achievable for this specific patient, given the current evidence.

[Output format - Return JSON ONLY, no prose]
Return a single JSON object with this structure:

{{
  "findings": [
    {{
      "type": "CharityCareEligibility | CharityCareProgramAvailable | SelfPayDiscount | NSA_OONBalanceBilling | NetworkMismatch | BenefitCalcError | PreventiveCostSharingCheck | BenefitClarificationNeeded | MinorDeMinimis | Other",
      "confidence": "high | medium | low",
      "reduction_opportunity": "Specific and conservative description of what can be reduced (e.g., 'Possible charity care discount on the remaining hospital balance, contingent on income verification', 'Office visit copay may be contestable if visit was purely preventive')",
      "legal_basis": "Specific legal or policy basis, clearly distinguishing general rules from patient-specific conclusions (e.g., 'IRS 501(r) requires a FAP; this bill advertises Ascension's Financial Assistance program, but patient income is unknown so eligibility is uncertain', 'Plan's SBC shows $0 cost-sharing for in-network preventive care; EOB flags this service as preventive but still applies a copay')",
      "estimated_reduction_amount": "Conservative dollar estimate when reasonably calculable (e.g., '$2,500', 'Up to approximately $1,800 depending on FAP eligibility', 'Requires additional information: [what is needed]' if you cannot safely quantify). Use ranges when appropriate.",
      "current_amount": "Current charge/amount for this item (if applicable)",
      "evidence_quotes": ["Exact quotes from documents supporting this finding (FACTS only, no speculation)"],
      "missing_info": ["What additional information is needed to confirm or calculate (e.g., 'Exact household income and size for FPL comparison', 'Visit notes to confirm whether a separate problem-oriented service was billed')"],
      "next_actions": ["Specific, realistic actions the patient should take (e.g., 'Request and review the hospital's Financial Assistance application', 'Ask the provider whether a separate problem-oriented visit was billed', 'Call the insurer to clarify why a preventive service incurred a copay')"]
    }}
  ],
  "overall_notes": "Conservative summary of overall reduction potential and key next steps. Make it clear which paths are high-confidence vs tentative or dependent on missing information."
}}
"""
    return prompt.strip()
