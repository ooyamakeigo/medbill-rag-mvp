import re
from typing import Optional, Dict

# -----------------------------
# Helpers
# -----------------------------
def _slugify(text: str) -> str:
    t = text.strip().lower()
    t = re.sub(r"[^a-z0-9]+", "_", t)
    t = re.sub(r"_+", "_", t).strip("_")
    return t


def _norm_name(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


# -----------------------------
# Hospital aliases (casefolded)
# Keep this small and grow just-in-time.
# -----------------------------
_HOSPITAL_ALIAS_TO_CANONICAL: Dict[str, str] = {
    _norm_name("Ascension SE Wisconsin Hospital - St. Joseph Campus"): "Ascension SE Wisconsin",
    _norm_name("Ascension SE Wisconsin Hospital - Elmbrook Campus"): "Ascension SE Wisconsin",
    _norm_name("Ascension SE Wisconsin Hospital - Franklin Campus"): "Ascension SE Wisconsin",
    _norm_name("Acension SE Wisconsin"): "Ascension SE Wisconsin",
    _norm_name("Ascension SE Wisconsin"): "Ascension SE Wisconsin",
}

# Optional payer aliases (you can extend)
_PAYER_ALIAS_TO_CANONICAL: Dict[str, str] = {
    _norm_name("anthem"): "Anthem",
    _norm_name("Anthem Blue Cross and Blue Shield"): "Anthem",
    _norm_name("BCBSWI"): "Anthem",
}


def normalize_hospital_id(provider_name: str, state: Optional[str] = None) -> str:
    """
    Normalize hospital name + state into a stable slug.
    Example:
      "Ascension SE Wisconsin Hospital - Franklin Campus", "WI"
        -> "wi_ascension_se_wisconsin"
    """
    if not provider_name:
        base = "unknown_hospital"
    else:
        key = _norm_name(provider_name)
        canonical = _HOSPITAL_ALIAS_TO_CANONICAL.get(key, provider_name)
        base = _slugify(canonical)

    st = (state or "").strip().lower()
    if st:
        return f"{st}_{base}"
    return base


def normalize_payer_id(payer_name: Optional[str]) -> Optional[str]:
    if not payer_name:
        return None
    key = _norm_name(payer_name)
    canonical = _PAYER_ALIAS_TO_CANONICAL.get(key, payer_name)
    return _slugify(canonical)


# -----------------------------
# Backward-compatible aliases
# (Older modules import hospital_id / payer_id)
# -----------------------------
def hospital_id(provider_name: str, state: Optional[str] = None) -> str:
    return normalize_hospital_id(provider_name, state)


def payer_id(payer_name: Optional[str] = None) -> Optional[str]:
    return normalize_payer_id(payer_name)
