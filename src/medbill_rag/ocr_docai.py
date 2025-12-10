from google.cloud import documentai
from google.api_core.client_options import ClientOptions
from .config import settings

def ocr_gcs_file(gcs_uri: str, mime_type: str, processor_id=None) -> str:
    pid = processor_id or settings.default_ocr_processor_id
    if not pid:
        raise ValueError("DEFAULT_OCR_PROCESSOR_ID not set")

    # Use docai-specific location
    doc_loc = settings.docai_location

    # Endpoint pattern supports multi-region like "us" -> "us-documentai.googleapis.com"
    opts = ClientOptions(api_endpoint=f"{doc_loc}-documentai.googleapis.com")
    client = documentai.DocumentProcessorServiceClient(client_options=opts)

    name = client.processor_path(settings.project_id, doc_loc, pid)

    request = documentai.ProcessRequest(
        name=name,
        gcs_document=documentai.GcsDocument(gcs_uri=gcs_uri, mime_type=mime_type)
    )
    result = client.process_document(request=request)
    return result.document.text or ""
