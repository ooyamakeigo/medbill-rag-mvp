import json
from .client import get_genai_client
from .config import settings
from .rest_client import generate_content as generate_content_rest

EXTRACT_PROMPT = """
You are extracting structured data from US medical billing documents.
Return JSON ONLY with keys:
- doc_type: one of ["EOB","ITEMIZED","STATEMENT","UNKNOWN"]
- provider_name
- provider_state
- payer_name
- plan_name
- dos_from
- dos_to
- total_charge
- patient_responsibility
- is_out_of_network_mentioned: boolean

If unknown, use null.
"""

def extract_from_text(text: str) -> dict:
    # Use REST API for gemini-3-pro-preview, SDK for others
    if settings.model_id == "gemini-3-pro-preview":
        resp = generate_content_rest(
            model_id=settings.model_id,
            contents=[EXTRACT_PROMPT, text],
            config={"response_mime_type": "application/json"},
        )
    else:
        client = get_genai_client()
        resp = client.models.generate_content(
            model=settings.model_id,
            contents=[EXTRACT_PROMPT, text],
            config={"response_mime_type": "application/json"},
        )
    return json.loads(resp.text)
