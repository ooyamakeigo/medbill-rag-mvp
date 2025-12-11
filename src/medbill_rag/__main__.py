import os
import sys

from .email_templates import write_hospital_email_output

# pipeline_end2end is assumed to exist in the project
from .pipeline_end2end import run_bill_folder


def main():
    bill_id = None
    if len(sys.argv) >= 2:
        bill_id = sys.argv[1]
    if not bill_id:
        bill_id = os.environ.get("BILL_FOLDER_ID")

    if not bill_id:
        raise SystemExit("BILL_FOLDER_ID is required. Usage: python -m medbill_rag <BILL_FOLDER_ID>")

    result = run_bill_folder(bill_id)

    # Add patient-led hospital email doc
    try:
        path = write_hospital_email_output(bill_id, result)
        print(f"✅ Hospital email draft saved: {path}")
    except Exception as e:
        print(f"⚠️ Hospital email generation skipped due to error: {e}")

    return result


if __name__ == "__main__":
    main()
