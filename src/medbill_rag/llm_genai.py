import json
from typing import Any, Dict, Optional, List

from .config import Config
from .genai_client import get_genai_client
from .rest_client import generate_content as generate_content_rest


def generate_text(
    prompt: str,
    cfg: Optional[Config] = None,
    model_id: Optional[str] = None,
) -> str:
    cfg = cfg or Config.from_env()
    model = model_id or cfg.model_id

    # Use REST API for gemini-3-pro-preview, SDK for others
    if model == "gemini-3-pro-preview":
        resp = generate_content_rest(
            model_id=model,
            contents=[prompt],
        )
    else:
        client = get_genai_client(cfg)
        resp = client.models.generate_content(
            model=model,
            contents=[prompt],
        )
    return getattr(resp, "text", "") or ""


def generate_json(
    prompt: str,
    cfg: Optional[Config] = None,
    model_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Best-effort JSON response. If parsing fails, returns {"raw_text": "..."}.
    """
    cfg = cfg or Config.from_env()
    model = model_id or cfg.model_id

    # Use REST API for gemini-3-pro-preview, SDK for others
    if model == "gemini-3-pro-preview":
        resp = generate_content_rest(
            model_id=model,
            contents=[prompt],
            config={"response_mime_type": "application/json"},
        )
    else:
        client = get_genai_client(cfg)
        resp = client.models.generate_content(
            model=model,
            contents=[prompt],
            config={"response_mime_type": "application/json"},
        )
    text = getattr(resp, "text", "") or ""
    try:
        return json.loads(text)
    except Exception:
        return {"raw_text": text}
