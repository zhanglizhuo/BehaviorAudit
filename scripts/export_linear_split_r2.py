from __future__ import annotations

"""Export linear-model split-level metrics for figure regeneration.

The manuscript's split-instability figure uses per-split MAE, R², and Pearson r
from 100 repeated 80/20 splits. This script writes one CSV per dataset under
``diagnostics/<Dataset>/linear_split_metrics.csv``.
"""

import csv
from pathlib import Path

import numpy as np

from framework.adapters import (
    MMTBAAdapter, OULADAdapter, UCIStudentAdapter,
    XAPIEduAdapter, StudentDropoutAdapter, EntranceExamAdapter, HigherEdAdapter,
)
from framework.baselines import baseline_linear_regression, compute_metrics, split_indices
from sklearn.preprocessing import StandardScaler


DATASETS = [
    ("MM-TBA", MMTBAAdapter(), "datasets/MM-TBA"),
    ("HigherEd", HigherEdAdapter(), "datasets/StudentExam"),
    ("xAPI-Edu", XAPIEduAdapter(), "datasets/xAPI-Edu"),
    ("EntranceExam", EntranceExamAdapter(), "datasets/StudentExam"),
    ("UCI", UCIStudentAdapter(), "datasets/UCI"),
    ("Dropout", StudentDropoutAdapter(), "datasets/StudentDropout"),
    ("OULAD", OULADAdapter(), "datasets/OULAD"),
]


def export_for_dataset(name: str, adapter, dataset_root: str, n_repeats: int = 100):
    print(f"Processing {name} -> {dataset_root}")
    bundle = adapter.load(dataset_root=dataset_root)
    if bundle.X is None:
        print(f"  SKIP {name}: missing data ({bundle.error})")
        return

    X_raw = bundle.X
    y = bundle.y
    scaler = StandardScaler()
    X = scaler.fit_transform(X_raw)

    out_dir = Path(__file__).resolve().parents[1] / "generated" / name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "linear_split_metrics.csv"

    with out_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["seed", "mae", "r2", "pearson"])

        for seed in range(n_repeats):
            train_idx, test_idx = split_indices(len(y), 0.8, seed=seed)
            Xtr, Xte = X[train_idx], X[test_idx]
            ytr, yte = y[train_idx], y[test_idx]
            if len(Xte) == 0:
                writer.writerow([seed, None, None, None])
                continue
            pred = baseline_linear_regression(Xtr, ytr, Xte)
            m = compute_metrics(yte, pred)
            writer.writerow([seed, m.get("mae"), m.get("r2"), m.get("pearson")])

    print(f"  Saved {out_path}")


def main():
    for name, adapter, root in DATASETS:
        dataset_root = str(Path(__file__).resolve().parents[1] / root)
        export_for_dataset(name, adapter, dataset_root, n_repeats=100)


if __name__ == "__main__":
    main()
