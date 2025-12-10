def build_reduction_prompt(
    eob_text: str,
    itemized_text: str,
    statement_text: str,
    global_kb: str,
    overlay_kb: str,
    meta: dict
) -> str:
    return f"""
You are supporting a PATIENT-LED medical bill review.
Do NOT provide legal advice. Do NOT threaten.
Use only the provided sources. If a document is missing, state what is missing.

[Case Meta]
{meta}

[Sources]
[EOB]
{eob_text}

[ITEMIZED]
{itemized_text}

[STATEMENT]
{statement_text}

[GLOBAL_KB]
{global_kb}

[OVERLAY_KB]
{overlay_kb}

[Task]
1) Check high-impact reduction angles first:
   - CharityCareEligibility
   - FAPLimitAGB (501r)
   - NSA_OONBalanceBilling
   - SelfPayDiscount
   - BenefitCalcError / NetworkMismatch (if signals exist)

2) For each applicable angle:
   - Explain why it may apply.
   - Quote supporting sentences with labels:
     (EOB: ...), (ITEMIZED: ...), (STATEMENT: ...), (GLOBAL_KB: ...), (OVERLAY_KB: ...)
   - List missing evidence the patient should provide.

3) Output JSON ONLY with these keys:
   - findings: array of objects with keys:
       type, confidence, evidence_quotes, next_actions
   - summary: short string
"""
