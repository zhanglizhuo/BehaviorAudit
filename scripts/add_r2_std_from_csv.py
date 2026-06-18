#!/usr/bin/env python3
"""Add r2_std (per-dataset) to audit_7dataset_results.json using
diagnostics/combined_linear_split_metrics.csv as the source of per-split r2.

Places the computed std into each entry at `summaries.linear.r2_std`.
Backs up the original JSON before writing.
"""
import json
import os
import shutil
from datetime import datetime

try:
    import pandas as pd
except Exception:
    pd = None


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_PATH = os.path.join(ROOT, "audit_7dataset_results.json")
CSV_PATH = os.path.join(ROOT, "diagnostics", "combined_linear_split_metrics.csv")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def compute_r2_std_with_pandas(csv_path):
    df = pd.read_csv(csv_path)
    # ensure column names
    if "dataset" not in df.columns or "r2" not in df.columns:
        raise ValueError("CSV missing required columns 'dataset' or 'r2'")
    series = df.groupby("dataset")["r2"].std(ddof=1)
    return series


def compute_r2_std_plain(csv_path):
    import csv, math
    data = {}
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ds = row['dataset']
            try:
                r2 = float(row['r2'])
            except Exception:
                continue
            data.setdefault(ds, []).append(r2)
    out = {}
    for ds, vals in data.items():
        n = len(vals)
        if n <= 1:
            out[ds] = None
            continue
        mean = sum(vals) / n
        var = sum((v - mean) ** 2 for v in vals) / (n - 1)
        out[ds] = var ** 0.5
    return out


def find_match(name, candidates):
    # exact match preferred
    if name in candidates:
        return name
    # try prefix match (JSON name may include ' (N=...)')
    for c in candidates:
        if c.startswith(name) or name.startswith(c):
            return c
    # case-insensitive
    lname = name.lower()
    for c in candidates:
        if c.lower() == lname:
            return c
    for c in candidates:
        if c.lower().startswith(lname) or lname.startswith(c.lower()):
            return c
    return None


def main():
    if not os.path.exists(JSON_PATH):
        print("JSON not found:", JSON_PATH)
        return 1
    if not os.path.exists(CSV_PATH):
        print("CSV not found:", CSV_PATH)
        return 1

    print("Loading JSON:", JSON_PATH)
    data = load_json(JSON_PATH)

    print("Computing r2 std from CSV:", CSV_PATH)
    if pd is not None:
        series = compute_r2_std_with_pandas(CSV_PATH)
        r2_std_map = {k: (None if pd.isna(v) else float(v)) for k, v in series.items()}
    else:
        r2_std_map = compute_r2_std_plain(CSV_PATH)

    candidates = list(r2_std_map.keys())

    # backup original
    bak_path = JSON_PATH + ".bak." + datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    shutil.copy(JSON_PATH, bak_path)
    print("Backed up original JSON to", bak_path)

    updated = 0
    for entry in data:
        ds_full = entry.get('dataset', '')
        ds_name = ds_full.split(' (')[0]
        match = find_match(ds_name, candidates)
        val = None
        if match is not None:
            val = r2_std_map.get(match)
        # place into summaries.linear.r2_std
        summaries = entry.setdefault('summaries', {})
        linear = summaries.setdefault('linear', {})
        # avoid overwriting an existing r2_std
        if 'r2_std' not in linear:
            linear['r2_std'] = val if val is not None else None
            updated += 1

    write_json(JSON_PATH, data)
    print(f"Updated {updated} entries in {JSON_PATH}")
    # print overview
    for entry in data:
        ds_full = entry.get('dataset', '')
        r2std = entry.get('summaries', {}).get('linear', {}).get('r2_std')
        print(f"{ds_full}: r2_std={r2std}")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
