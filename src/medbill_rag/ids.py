import re

def _slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "unknown"

def hospital_id(provider_name: str, state: str | None = None) -> str:
    base = _slugify(provider_name)
    st = _slugify(state) if state else None
    return f"{st}_{base}" if st else base

def payer_id(payer_name: str, plan_name: str | None = None) -> str:
    p = _slugify(payer_name)
    pl = _slugify(plan_name) if plan_name else None
    return f"{p}_{pl}" if pl else p
