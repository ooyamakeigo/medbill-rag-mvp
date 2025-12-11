import os
from dataclasses import dataclass
from typing import Optional


def _req(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v


def _opt(name: str, default: str) -> str:
    v = os.getenv(name)
    return v if v else default


def _opt_bool(name: str, default: bool = True) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    s = str(v).strip().lower()
    if s in ("1", "true", "t", "yes", "y"):
        return True
    if s in ("0", "false", "f", "no", "n"):
        return False
    return default


def _opt_int(name: str, default: Optional[int] = None) -> Optional[int]:
    v = os.getenv(name)
    if v is None or str(v).strip() == "":
        return default
    try:
        return int(str(v).strip())
    except Exception:
        return default


@dataclass
class Config:
    # GCP / Vertex AI
    project_id: str
    location: str
    model_id: str

    # Buckets
    bucket_case: str
    bucket_kb: str

    # Document AI
    docai_location: str
    docai_processor_id: str

    # Legacy flag
    use_vertex: bool = True

    # ---- User-known inputs (corrected) ----
    # household size is numeric
    household_size: Optional[int] = None
    # income is often only a range in MVP -> keep STRING
    annual_income_range: Optional[str] = None

    # backward compatible (if someone still sets old vars)
    annual_income_usd: Optional[float] = None  # not used unless range missing

    # Output file naming prefix
    output_file_header: str = ""

    @classmethod
    def from_env(cls) -> "Config":
        # Prefer new correct vars; fall back to older ones if present
        household = _opt_int("HOUSEHOLD_SIZE", None)
        if household is None:
            household = _opt_int("HOUSEHOLD_SIZE_NUM", None)

        income_range = os.getenv("ANNUAL_INCOME_RANGE")
        if not income_range:
            # old mistaken key name (range stored under household range) -> ignore
            income_range = os.getenv("ANNUAL_INCOME_USD_RANGE")

        income_usd = os.getenv("ANNUAL_INCOME_USD")
        annual_income_usd_val = None
        if income_usd:
            try:
                annual_income_usd_val = float(income_usd)
            except Exception:
                annual_income_usd_val = None

        return cls(
            project_id=_req("PROJECT_ID"),
            location=_opt("LOCATION", "us-central1"),
            model_id=_opt("MODEL_ID", "gemini-2.5-flash"),

            bucket_case=_req("BUCKET_CASE"),
            bucket_kb=_req("BUCKET_KB"),

            docai_location=_opt("DOCAI_LOCATION", "us"),
            docai_processor_id=_req("DOCAI_PROCESSOR_ID"),

            use_vertex=_opt_bool("USE_VERTEX", True),

            household_size=household,
            annual_income_range=income_range,
            annual_income_usd=annual_income_usd_val,
            output_file_header=_opt("OUTPUT_FILE_HEADER", ""),
        )


class _SettingsProxy:
    _cfg: Optional[Config] = None

    def _get(self) -> Config:
        if self._cfg is None:
            self._cfg = Config.from_env()
        return self._cfg

    def __getattr__(self, name: str):
        cfg = self._get()

        mapping = {
            # legacy uppercase
            "PROJECT_ID": "project_id",
            "LOCATION": "location",
            "MODEL_ID": "model_id",
            "BUCKET_CASE": "bucket_case",
            "BUCKET_KB": "bucket_kb",
            "DOCAI_LOCATION": "docai_location",
            "DOCAI_PROCESSOR_ID": "docai_processor_id",
            "USE_VERTEX": "use_vertex",

            # correct user profile keys
            "HOUSEHOLD_SIZE": "household_size",
            "ANNUAL_INCOME_RANGE": "annual_income_range",

            # output file header
            "OUTPUT_FILE_HEADER": "output_file_header",

            # allow direct
            "use_vertex": "use_vertex",
        }
        if name in mapping:
            return getattr(cfg, mapping[name])

        return getattr(cfg, name)


settings = _SettingsProxy()

__all__ = ["Config", "settings"]
