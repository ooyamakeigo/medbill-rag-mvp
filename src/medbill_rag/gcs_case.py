import json
from google.cloud import storage
from .config import settings

def _bucket():
    if not settings.bucket_case:
        raise RuntimeError("BUCKET_CASE is not set")
    return storage.Client().bucket(settings.bucket_case)

def list_bill_blobs(bill_folder_id: str):
    prefix = f"bills/{bill_folder_id}/"
    client = storage.Client()
    return list(client.list_blobs(settings.bucket_case, prefix=prefix))

def upload_text_to_bill_outputs(bill_folder_id: str, filename: str, text: str, content_type="text/plain; charset=utf-8"):
    blob = _bucket().blob(f"bills/{bill_folder_id}/outputs/{filename}")
    blob.upload_from_string(text, content_type=content_type)

def upload_json_to_bill_outputs(bill_folder_id: str, filename: str, data: dict):
    upload_text_to_bill_outputs(
        bill_folder_id,
        filename,
        json.dumps(data, ensure_ascii=False, indent=2),
        content_type="application/json; charset=utf-8",
    )
