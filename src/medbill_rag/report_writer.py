from datetime import datetime
from typing import Dict, Any


def build_report_md_prompt(bill_folder_id: str, meta: dict, findings_json: dict) -> str:
    """
    Build prompt for generating a comprehensive markdown report.
    The report should be professional, well-structured, and suitable for internal review.
    """
    dt = datetime.utcnow().isoformat()
    hospital = meta.get("provider_name") or "Unknown Hospital"
    state = meta.get("provider_state") or ""
    payer = meta.get("payer_name") or "Unknown"
    total_charge = meta.get("total_charge") or meta.get("total_amount")
    patient_resp = meta.get("patient_responsibility")

    # Convert to float for formatting, handling both string and numeric types
    def format_currency(value, default="Not available"):
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

    total_line = format_currency(total_charge)
    resp_line = format_currency(patient_resp)

    findings = findings_json.get("findings", [])
    total_potential_reduction = 0
    reduction_items = []
    for f in findings:
        reduction_str = f.get("estimated_reduction_amount", "")
        if reduction_str and "$" in reduction_str:
            # Try to extract dollar amount
            try:
                # Simple extraction - look for $X,XXX.XX pattern
                import re
                amounts = re.findall(r'\$[\d,]+\.?\d*', reduction_str)
                if amounts:
                    # Take first amount, remove $ and commas
                    amt_str = amounts[0].replace("$", "").replace(",", "")
                    amt = float(amt_str)
                    total_potential_reduction += amt
                    reduction_items.append(f"{f.get('type', 'Unknown')}: {amounts[0]}")
            except:
                pass

    total_reduction_line = f"${total_potential_reduction:,.2f}" if total_potential_reduction > 0 else "TBD (requires additional information)"

    return f"""
You are creating a comprehensive internal case report for a medical bill reduction analysis.

[Case Information]
- Bill Folder ID: {bill_folder_id}
- Generated: {dt}
- Hospital/Facility: {hospital} {f'({state})' if state else ''}
- Insurance/Payer: {payer}
- Total Charges: {total_line}
- Current Patient Responsibility: {resp_line}
- Estimated Total Reduction Potential: {total_reduction_line}

[Analysis Findings]
{findings_json}

[Report Requirements]
Create a professional markdown report with the following structure:

1. **Executive Summary** (2-3 paragraphs)
   - Brief overview of the case
   - Key reduction opportunities identified
   - Overall reduction potential estimate
   - Priority actions needed

2. **Case Details**
   - Bill information (dates of service, amounts, etc.)
   - Patient information (household size, income range - anonymized appropriately)
   - Documents available (EOB, Statement, Itemized Bill)

3. **Detailed Findings** (one section per finding)
   For each finding, include:
   - Finding type and confidence level
   - Specific reduction opportunity (what can be reduced)
   - Legal/policy basis (why it can be reduced)
   - Estimated reduction amount
   - Current amount (if applicable)
   - Supporting evidence (quotes from documents)
   - Missing information needed
   - Recommended next actions

4. **Reduction Summary Table**
   - Create a table summarizing all findings with:
     * Finding Type
     * Current Amount
     * Estimated Reduction
     * Confidence Level
     * Status (Ready to pursue / Needs more info)

5. **Action Plan**
   - Prioritized list of next steps
   - Required documents/information
   - Recommended timeline
   - Key contacts (if applicable)

6. **Risk Assessment**
   - Confidence levels for each finding
   - Potential challenges or obstacles
   - Alternative approaches if primary path fails

7. **Notes & Recommendations**
   - Additional observations
   - Suggestions for follow-up
   - Any concerns or limitations

[Format Guidelines]
- Use proper markdown formatting (headers, lists, tables, code blocks)
- Be professional and clear
- Include specific dollar amounts where available
- Reference document quotes accurately
- Use clear section headers
- Make it easy to scan and understand quickly

[Important]
- This is an internal report - be thorough and detailed
- Include all relevant information from the findings
- Be specific about amounts, dates, and references
- Highlight high-priority items clearly
- Note any missing information that would strengthen the case

Generate the complete markdown report now.
"""
