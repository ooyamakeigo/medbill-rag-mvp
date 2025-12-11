def build_user_email_prompt(user_name: str | None, findings_json: dict, meta: dict = None) -> str:
    """
    Build prompt for generating patient-facing email draft.
    The email should be clear, empathetic, and actionable.
    """
    meta = meta or {}
    hospital = meta.get("provider_name") or "the hospital"
    total_charge = meta.get("total_charge") or meta.get("total_amount")
    patient_resp = meta.get("patient_responsibility")

    # Convert to float for formatting, handling both string and numeric types
    def format_currency(value, default="unknown"):
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

    total_line = format_currency(total_charge, "your bill")
    resp_line = format_currency(patient_resp, "your responsibility")

    return f"""
You are writing a clear, empathetic, and helpful email to a patient about their medical bill analysis results.

Patient name (if known): {user_name or "[Patient Name]"}
Hospital: {hospital}
Total charges: {total_line}
Current patient responsibility: {resp_line}

Analysis findings:
{findings_json}

[Email Requirements]
1. Subject line: Write a clear, professional subject line (e.g., "Medical Bill Review Results - [Hospital Name]")

2. Opening: Start with a warm, empathetic greeting. Acknowledge that medical bills can be stressful.

3. Summary section (3-5 sentences):
   - Clearly state what reduction opportunities were identified
   - Mention the most significant finding first (highest dollar amount or highest confidence)
   - Explain in simple terms what this means for the patient
   - Be specific about potential savings when amounts are available

4. Key findings section:
   - List 2-4 most important findings as bullet points
   - For each finding, include:
     * What can potentially be reduced
     * Why it can be reduced (brief explanation)
     * Estimated reduction amount (if available)
   - Use clear, non-technical language

5. What we need from you section:
   - List specific documents or information needed from the patient
   - Explain why each item is needed
   - Be specific about deadlines if applicable

6. Next steps section:
   - Explain what will happen next
   - Set clear expectations about timeline
   - Provide reassurance about the process

7. Closing: End with a supportive, professional closing.

[Tone Guidelines]
- Calm, helpful, and supportive
- Professional but warm
- Avoid legal jargon - explain in plain language
- No legal advice - focus on administrative review
- Empowering - help patient understand their options
- Reassuring - emphasize that help is available

[Format]
Write the complete email including:
- Subject line
- Salutation
- Body paragraphs
- Closing
- Your name/signature line

Do not include placeholders like [Your Name] - write as if this is the final email to send.
"""
