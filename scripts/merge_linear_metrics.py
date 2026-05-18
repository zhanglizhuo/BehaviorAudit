"""Merge per-dataset linear split metrics into one combined CSV."""

from pathlib import Path

import pandas as pd


def main():
    gen = Path("generated")
    files = sorted(gen.glob("*/linear_split_metrics.csv"))
    if not files:
        print("No files found under generated/*/linear_split_metrics.csv")
        return

    dfs = []
    for p in files:
        df = pd.read_csv(p)
        df.insert(0, "dataset", p.parent.name)
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)
    out = gen / "combined_linear_split_metrics.csv"
    combined.to_csv(out, index=False)
    print(f"Wrote {out} ({len(combined)} rows)")


if __name__ == "__main__":
    main()
