from datetime import datetime

def build_report_md(bill_folder_id: str, meta: dict, findings_json: dict) -> str:
    dt = datetime.utcnow().isoformat()
    return "\n".join([
        "# MedBill Rescue – Case Report (MVP)",
        f"- Bill Folder ID: {bill_folder_id}",
        f"- Generated: {dt}",
        "",
        "## Extracted Meta",
        "```json",
        str(meta),
        "```",
        "",
        "## Findings",
        "```json",
        str(findings_json),
        "```",
        "",
        "## Summary",
        findings_json.get("summary", ""),
        "",
        "## Notes",
        "- If EOB/Itemized/Statement is missing, request it for stronger validation.",
    ])
