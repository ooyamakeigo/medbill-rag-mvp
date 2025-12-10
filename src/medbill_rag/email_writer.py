def build_user_email_prompt(user_name: str | None, findings_json: dict) -> str:
    return f"""
You are writing a short, empathetic email to a patient.
Tone: calm, helpful, non-accusatory. No legal advice.

Patient name (if known): {user_name}

Findings JSON:
{findings_json}

Write:
1) 3–5 sentence summary of what we found
2) bullets of what we still need from the patient
3) what happens next
"""
