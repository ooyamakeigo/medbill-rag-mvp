import json
from google.cloud import storage
from .config import settings
from .ids import hospital_id as _hid, payer_id as _pid

def _kb_bucket():
    if not settings.bucket_kb:
        raise RuntimeError("BUCKET_KB is not set")
    return storage.Client().bucket(settings.bucket_kb)

def ensure_hospital_overlay(provider_name: str, state: str | None):
    hid = _hid(provider_name, state)
    prefix = f"10_dynamic_inputs/hospitals/{hid}/"

    bucket = _kb_bucket()
    bucket.blob(prefix + ".keep").upload_from_string("")
    meta = {"hospital_id": hid, "provider_name": provider_name, "state": state}
    bucket.blob(prefix + "meta.json").upload_from_string(
        json.dumps(meta, ensure_ascii=False, indent=2),
        content_type="application/json; charset=utf-8",
    )
    return hid

def ensure_payer_overlay(payer_name: str, plan_name: str | None):
    pid = _pid(payer_name, plan_name)
    prefix = f"10_dynamic_inputs/payers/{pid}/"

    bucket = _kb_bucket()
    bucket.blob(prefix + ".keep").upload_from_string("")
    meta = {"payer_id": pid, "payer_name": payer_name, "plan_name": plan_name}
    bucket.blob(prefix + "meta.json").upload_from_string(
        json.dumps(meta, ensure_ascii=False, indent=2),
        content_type="application/json; charset=utf-8",
    )
    return pid
