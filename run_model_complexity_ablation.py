"""Focused model-complexity ablation for three representative datasets.

The full seven-dataset model-complexity results are produced by
``run_7dataset_audit.py``. This helper keeps the original three-dataset ablation
available for quick inspection of MM-TBA, UCI Student, and OULAD.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.preprocessing import StandardScaler

from framework.adapters import MMTBAAdapter, OULADAdapter, UCIStudentAdapter
from framework.baselines import (
    baseline_linear_regression,
    baseline_mean_quality,
    baseline_ridge_regression,
    compute_metrics,
    split_indices,
)


def fit_rf(X_train, y_train, X_test, seed=0):
    try:
        m = RandomForestRegressor(n_estimators=100, max_depth=None, random_state=seed, n_jobs=-1)
        m.fit(X_train, y_train)
        return m.predict(X_test)
    except Exception:
        return baseline_mean_quality(X_train, y_train, X_test)


def fit_gbt(X_train, y_train, X_test, seed=0):
    try:
        m = GradientBoostingRegressor(
            n_estimators=100, max_depth=3, learning_rate=0.1, random_state=seed
        )
        m.fit(X_train, y_train)
        return m.predict(X_test)
    except Exception:
        return baseline_mean_quality(X_train, y_train, X_test)


def run_ablation(X, y, group_ids, dataset_name, n_repeats=100):
    """Run repeated 80/20 splits + group holdout for all model types."""
    models = {
        "mean": lambda Xtr, ytr, Xte, s: baseline_mean_quality(Xtr, ytr, Xte),
        "linear": lambda Xtr, ytr, Xte, s: baseline_linear_regression(Xtr, ytr, Xte),
        "ridge": lambda Xtr, ytr, Xte, s: baseline_ridge_regression(Xtr, ytr, Xte),
        "rf": lambda Xtr, ytr, Xte, s: fit_rf(Xtr, ytr, Xte, seed=s),
        "gbt": lambda Xtr, ytr, Xte, s: fit_gbt(Xtr, ytr, Xte, seed=s),
    }

    # --- 1. Repeated 80/20 splits ---
    results = {name: [] for name in models}
    for i in range(n_repeats):
        train_idx, test_idx = split_indices(len(y), 0.8, seed=i)
        Xtr, Xte = X[train_idx], X[test_idx]
        ytr, yte = y[train_idx], y[test_idx]
        for name, fn in models.items():
            pred = fn(Xtr, ytr, Xte, i)
            results[name].append(compute_metrics(yte, pred))

    print(f"\n{'='*70}")
    print(f"  {dataset_name} — Model-Complexity Ablation ({n_repeats} repeated 80/20)")
    print(f"{'='*70}")

    summaries = {}
    for name in models:
        mae_vals = [r["mae"] for r in results[name]]
        r2_vals = [r["r2"] for r in results[name]]
        r_vals = [r["pearson"] for r in results[name]]
        summaries[name] = {
            "mae_mean": np.mean(mae_vals),
            "mae_std": np.std(mae_vals),
            "r2_mean": np.mean(r2_vals),
            "r2_std": np.std(r2_vals),
            "pearson_mean": np.mean(r_vals),
        }

    mean_mae = summaries["mean"]["mae_mean"]
    for name in models:
        s = summaries[name]
        delta = mean_mae - s["mae_mean"]
        I_ratio = s["mae_std"] / (abs(delta) + 1e-8) if name != "mean" else float("nan")
        beat_rate = np.mean(
            [results[name][i]["mae"] < results["mean"][i]["mae"] for i in range(n_repeats)]
        ) if name != "mean" else float("nan")
        print(
            f"  {name:8s}: MAE={s['mae_mean']:.4f}±{s['mae_std']:.4f}  "
            f"R²={s['r2_mean']:.4f}±{s['r2_std']:.4f}  "
            f"r={s['pearson_mean']:.4f}  "
            f"Δ_MAE={delta:+.4f}  I={I_ratio:.4f}  beat={beat_rate:.2f}"
        )

    # --- 2. Group holdout (if available) ---
    if group_ids is not None:
        unique_groups = sorted(set(group_ids))
        group_arr = np.array(group_ids)
        print(f"\n  --- Group Holdout (hold out each group) ---")
        for g in unique_groups:
            mask = group_arr != g
            Xtr, Xte = X[mask], X[~mask]
            ytr, yte = y[mask], y[~mask]
            n_test = (~mask).sum()
            print(f"  Holdout={g} (n_test={n_test}):")
            for name in ["linear", "ridge", "rf", "gbt"]:
                if name in ("rf", "gbt"):
                    pred = models[name](Xtr, ytr, Xte, 42)
                else:
                    pred = models[name](Xtr, ytr, Xte, 42)
                m = compute_metrics(yte, pred)
                print(f"    {name:8s}: MAE={m['mae']:.4f}  R²={m['r2']:.4f}  r={m['pearson']:.4f}")

    return results, summaries


def main():
    repo_root = Path(__file__).resolve().parent

    adapter = MMTBAAdapter()
    bundle = adapter.load(dataset_root=str(repo_root / "datasets" / "MM-TBA"))
    if bundle.X is not None:
        # Standardize
        scaler = StandardScaler()
        X = scaler.fit_transform(bundle.X)
        run_ablation(X, bundle.y, bundle.group_ids, "MM-TBA (N=186)", n_repeats=100)
    else:
        print(f"MM-TBA load error: {bundle.error}")

    adapter = UCIStudentAdapter()
    bundle = adapter.load(dataset_root=str(repo_root / "datasets" / "UCI"))
    if bundle.X is not None:
        scaler = StandardScaler()
        X = scaler.fit_transform(bundle.X)
        run_ablation(X, bundle.y, bundle.group_ids, "UCI Student (N=649)", n_repeats=100)
    else:
        print(f"UCI load error: {bundle.error}")

    adapter = OULADAdapter()
    bundle = adapter.load(dataset_root=str(repo_root / "datasets" / "OULAD"))
    if bundle.X is not None:
        scaler = StandardScaler()
        X = scaler.fit_transform(bundle.X)
        run_ablation(X, bundle.y, bundle.group_ids, "OULAD (N=32593)", n_repeats=100)
    else:
        print(f"OULAD load error: {bundle.error}")


if __name__ == "__main__":
    main()
