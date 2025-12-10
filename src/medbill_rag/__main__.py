import os
import json
from .pipeline_end2end import run_bill_folder

def main() -> None:
    bill_id = os.environ.get("BILL_FOLDER_ID")
    if not bill_id:
        raise SystemExit("BILL_FOLDER_ID env var is required (e.g. -e BILL_FOLDER_ID=ba47...)")

    result = run_bill_folder(bill_id)
    # 標準出力には軽くサマリだけ表示（詳細は GCS の outputs/ に保存済み）
    print(json.dumps(result, ensure_ascii=False, indent=2)[:2000])

if __name__ == "__main__":
    main()
