import argparse
import os
import re
from dataclasses import dataclass
from pathlib import Path
import pandas as pd

CHUNK_SIZE = 200_000

CASH_PATTERNS = [
    r"standard_charge\|discounted_cash",
    r"discounted[_\s]?cash",
    r"\bcash\b",
    r"self[_\s-]?pay",
    r"uninsured",
]

GROSS_PATTERNS = [
    r"standard_charge\|gross",
    r"\bgross\b",
    r"chargemaster",
]

DESC_PATTERNS = [
    r"\bdescription\b",
    r"service_description",
    r"item_description",
]

CODE_CANDIDATES = [
    "code",
    "cpt",
    "hcpcs",
    "revenue_code",
    "rev_code",
    "drg",
    "ms_drg",
    "ndc",
]

HEADER_HINT_KEYWORDS = [
    "standard_charge",
    "discounted_cash",
    "gross",
    "description",
    "code",
    "payer",
]

DELIM_CANDIDATES = [",", "|", "\t", ";"]


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s).strip().lower())


def pick_col(cols, patterns):
    for pat in patterns:
        for c in cols:
            if re.search(pat, c, re.IGNORECASE):
                return c
    return None


def pick_first_existing(cols, candidates):
    cols_map = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in cols_map:
            return cols_map[cand.lower()]
    # code|1 みたいな構造も拾う
    for c in cols:
        if re.search(r"^code\|\d+$", c, re.IGNORECASE):
            return c
    return None


def infer_campus_from_path(p: str):
    name = Path(p).stem.lower()
    if "franklin" in name:
        return "franklin"
    if "elmbrook" in name:
        return "elmbrook"
    if "joseph" in name or "st_joseph" in name or "st-joseph" in name:
        return "st_joseph"
    return name


@dataclass
class CsvFormat:
    sep: str
    skiprows: int


def sniff_format(path: str) -> CsvFormat:
    # 先頭数十行を軽く読む
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = []
        for _ in range(80):
            line = f.readline()
            if not line:
                break
            lines.append(line.rstrip("\n"))

    # header候補行を探す（standard_charge/description などが含まれる行）
    header_idx = 0
    best_score = -1
    best_line = lines[0] if lines else ""

    for i, line in enumerate(lines):
        l = line.lower()
        score = sum(1 for kw in HEADER_HINT_KEYWORDS if kw in l)
        if score > best_score:
            best_score = score
            best_line = line
            header_idx = i

    # 区切り文字を推定：headerっぽい行で最も多い delimiter を採用
    counts = {d: best_line.count(d) for d in DELIM_CANDIDATES}
    sep = max(counts, key=counts.get) if counts else ","

    # delimiter出現が少なすぎる場合の保険
    if counts.get(sep, 0) == 0:
        # 全行の中で delimiter が一番安定して多いものを選ぶ
        agg = {}
        for d in DELIM_CANDIDATES:
            agg[d] = sum(line.count(d) for line in lines)
        sep = max(agg, key=agg.get) if agg else ","

    return CsvFormat(sep=sep, skiprows=header_idx)


def safe_preview(path: str, fmt: CsvFormat):
    # pythonエンジン + on_bad_lines で崩れ耐性
    return pd.read_csv(
        path,
        engine="python",
        sep=fmt.sep,
        skiprows=fmt.skiprows,
        nrows=20,
        on_bad_lines="skip",
    )


def safe_chunks(path: str, fmt: CsvFormat, usecols):
    return pd.read_csv(
        path,
        engine="python",
        sep=fmt.sep,
        skiprows=fmt.skiprows,
        usecols=usecols,
        chunksize=CHUNK_SIZE,
        on_bad_lines="skip",
    )


def build_one_file(path, rows):
    fmt = sniff_format(path)
    preview = safe_preview(path, fmt)
    cols = list(preview.columns)

    cash_col = pick_col(cols, CASH_PATTERNS)
    gross_col = pick_col(cols, GROSS_PATTERNS)
    desc_col = pick_col(cols, DESC_PATTERNS)
    code_col = pick_first_existing(cols, CODE_CANDIDATES)

    # descriptionが無い場合の保険
    if desc_col is None:
        for c in cols:
            if re.search(r"service", c, re.IGNORECASE):
                desc_col = c
                break

    if not cash_col:
        raise ValueError(
            f"[{path}] cash-like column not found.\n"
            f"Detected sep='{fmt.sep}', skiprows={fmt.skiprows}\n"
            f"Columns sample: {cols[:60]}"
        )

    use_cols = []
    for c in [code_col, desc_col, gross_col, cash_col]:
        if c and c not in use_cols:
            use_cols.append(c)

    campus = infer_campus_from_path(path)

    for chunk in safe_chunks(path, fmt, use_cols):
        out = pd.DataFrame()
        out["campus"] = campus

        if code_col and code_col in chunk.columns:
            out["code"] = chunk[code_col].astype(str)
        else:
            out["code"] = ""

        if desc_col and desc_col in chunk.columns:
            out["description"] = chunk[desc_col].astype(str)
        else:
            out["description"] = ""

        if gross_col and gross_col in chunk.columns:
            out["gross_charge"] = chunk[gross_col]
        else:
            out["gross_charge"] = None

        out["cash_price"] = chunk[cash_col]

        # 空/ゼロを除外
        out = out.dropna(subset=["cash_price"])
        try:
            out = out[out["cash_price"].astype(float) > 0]
        except Exception:
            out = out[out["cash_price"].astype(str).str.strip() != ""]

        rows.append(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", help="MRF CSV paths")
    parser.add_argument("-o", "--output", required=True, help="Output csv path")
    args = parser.parse_args()

    rows = []
    for p in args.inputs:
        build_one_file(p, rows)

    df = pd.concat(rows, ignore_index=True)

    # 軽量KBとして重複除去
    df = df.drop_duplicates(subset=["campus", "code", "description", "cash_price"])

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    print(f"✅ saved: {out_path} rows={len(df)}")


if __name__ == "__main__":
    main()
