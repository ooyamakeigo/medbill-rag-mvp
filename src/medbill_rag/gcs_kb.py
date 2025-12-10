from pathlib import Path

def load_local_global_kb_text(rag_base_dir: str) -> str:
    base = Path(rag_base_dir)
    if not base.exists():
        return ""

    parts = []
    for p in sorted(base.rglob("*.md")):
        try:
            parts.append(f"\n\n# FILE: {p.relative_to(base)}\n")
            parts.append(p.read_text(encoding="utf-8"))
        except Exception:
            continue

    for p in sorted(base.rglob("*.csv")):
        try:
            parts.append(f"\n\n# FILE: {p.relative_to(base)}\n")
            parts.append(p.read_text(encoding="utf-8"))
        except Exception:
            continue

    return "\n".join(parts)
