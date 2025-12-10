import re
from typing import Dict, List, Optional
from google.cloud import storage
from .config import settings

EOB_PAT = re.compile(r"\beob\b", re.IGNORECASE)
ITEMIZED_PAT = re.compile(r"itemized|itemised|detail", re.IGNORECASE)
STATEMENT_PAT = re.compile(r"statement|summary", re.IGNORECASE)

def _guess_kind_from_name(name: str) -> str:
    base = name.split("/")[-1]
    if EOB_PAT.search(base):
        return "EOB"
    if ITEMIZED_PAT.search(base):
        return "ITEMIZED"
    if STATEMENT_PAT.search(base):
        return "STATEMENT"
    return "UNKNOWN"

def list_bill_folder_files(bill_folder_id: str) -> List[Dict]:
    if not settings.bucket_case:
        raise ValueError("BUCKET_CASE is not set")

    prefix = f"bills/{bill_folder_id}/"
    client = storage.Client()
    blobs = list(client.list_blobs(settings.bucket_case, prefix=prefix))

    files = []
    for b in blobs:
        if b.name.endswith("/") or b.name.endswith(".keep"):
            continue
        if "/outputs/" in b.name:
            continue

        mime = "application/pdf"
        low = b.name.lower()
        if low.endswith(".png"):
            mime = "image/png"
        elif low.endswith(".jpg") or low.endswith(".jpeg"):
            mime = "image/jpeg"

        files.append({
            "gcs_uri": f"gs://{settings.bucket_case}/{b.name}",
            "mime_type": mime,
            "hint": _guess_kind_from_name(b.name),
            "blob_name": b.name,
        })
    return files

def pick_best_by_kind(files: List[Dict]) -> Dict[str, Optional[Dict]]:
    grouped = {"EOB": [], "ITEMIZED": [], "STATEMENT": [], "UNKNOWN": []}
    for f in files:
        grouped[f["hint"]].append(f)

    def choose(lst):
        if not lst:
            return None
        lst = sorted(lst, key=lambda x: len(x["blob_name"]))
        return lst[0]

    return {
        "EOB": choose(grouped["EOB"]),
        "ITEMIZED": choose(grouped["ITEMIZED"]),
        "STATEMENT": choose(grouped["STATEMENT"]),
        "UNKNOWN": grouped["UNKNOWN"] or None,
    }
