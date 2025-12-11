from typing import Optional, Dict, Any

from .config import Config
from .llm_genai import generate_json


META_PROMPT = """
You are a medical billing intake assistant.
Extract metadata from the provided OCR text(s).
Output JSON only.

Keys:
- provider_name: string or null
- provider_state: string or null (2-letter if inferable)
- payer_name: string or null
- is_itemized: boolean
- total_amount: number or null
- service_date_from: string or null (YYYY-MM-DD if inferable)
- service_date_to: string or null
- reason_for_visit: string or null
- patient_concern_summary: string or null

IMPORTANT:
- If unsure, use null.
- Do not invent insurer contact.
- Keep it conservative.
"""


def _inject_known_user_inputs(meta: Dict[str, Any], cfg: Config) -> Dict[str, Any]:
    """
    Corrected MVP assumption:
    - household size is known as a NUMBER
    - income is only known as a RANGE STRING
    """
    if cfg.household_size is not None:
        meta["household_size"] = int(cfg.household_size)

    if cfg.annual_income_range:
        meta["annual_income_range"] = str(cfg.annual_income_range).strip()

    # fallback: if someone only provided numeric income
    if "annual_income_range" not in meta and cfg.annual_income_usd is not None:
        meta["annual_income_usd"] = cfg.annual_income_usd

    return meta


def extract_metadata_from_text(
    text: str,
    cfg: Optional[Config] = None,
) -> Dict[str, Any]:
    cfg = cfg or Config.from_env()
    prompt = META_PROMPT + "\n\n[OCR_TEXT]\n" + (text or "")
    meta = generate_json(prompt, cfg=cfg)
    if not isinstance(meta, dict):
        meta = {"raw_text": str(meta)}
    return _inject_known_user_inputs(meta, cfg)


def merge_document_texts(
    eob_text: str = "",
    statement_text: str = "",
    itemized_text: str = "",
) -> str:
    parts = []
    if eob_text:
        parts.append("[EOB]\n" + eob_text)
    if statement_text:
        parts.append("[STATEMENT]\n" + statement_text)
    if itemized_text:
        parts.append("[ITEMIZED]\n" + itemized_text)
    return "\n\n".join(parts)


def extract_metadata_from_docs(
    eob_text: str = "",
    statement_text: str = "",
    itemized_text: str = "",
    cfg: Optional[Config] = None,
) -> Dict[str, Any]:
    cfg = cfg or Config.from_env()
    text = merge_document_texts(eob_text, statement_text, itemized_text)
    meta = extract_metadata_from_text(text, cfg=cfg)
    return meta
