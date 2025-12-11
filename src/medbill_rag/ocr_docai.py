from typing import Optional
from google.cloud import documentai_v1 as documentai

from .config import Config


def ocr_gcs_file(
    gcs_uri: str,
    mime_type: str,
    processor_id: Optional[str] = None,
    cfg: Optional[Config] = None,
) -> str:
    """
    OCR a single file in GCS using Document AI.
    Returns plain text.
    """
    if not gcs_uri:
        return ""

    cfg = cfg or Config.from_env()
    pid = processor_id or cfg.docai_processor_id
    loc = cfg.docai_location

    client = documentai.DocumentProcessorServiceClient(
        client_options={"api_endpoint": f"{loc}-documentai.googleapis.com"}
    )
    name = client.processor_path(cfg.project_id, loc, pid)

    request = documentai.ProcessRequest(
        name=name,
        gcs_document=documentai.GcsDocument(
            gcs_uri=gcs_uri,
            mime_type=mime_type,
        ),
    )

    result = client.process_document(request=request)
    doc = result.document
    return doc.text or ""
