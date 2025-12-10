import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    project_id: str = os.getenv("PROJECT_ID", "")

    # Backward compatible default
    location: str = os.getenv("LOCATION", "us-central1")

    # New: split locations
    vertex_location: str = os.getenv("VERTEX_LOCATION", os.getenv("LOCATION", "us-central1"))
    docai_location: str = os.getenv("DOCAI_LOCATION", "us")

    model_id: str = os.getenv("MODEL_ID", "gemini-2.5-flash")
    use_vertex: bool = os.getenv("USE_VERTEX", "true").lower() == "true"

    bucket_case: str = os.getenv("BUCKET_CASE", "")
    bucket_kb: str = os.getenv("BUCKET_KB", "")

    default_ocr_processor_id: str = os.getenv("DEFAULT_OCR_PROCESSOR_ID", "")

    log_level: str = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()
