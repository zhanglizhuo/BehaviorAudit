"""Extended UCI Student Performance audit to match paper reporting format.

Produces: 100 repeated 80/20, 50 repeated 5-fold CV, permutation null,
BF10 approximation, feature-group ablation, and group holdout analysis.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

# Add parent to path so we can import framework
sys.path.insert(0, str(Path(__file__).resolve().parent))

from framework.adapters import UCIStudentAdapter
from framework.baselines import (
    baseline_linear_regression,
    baseline_mean_quality,
    baseline_ridge_regression,
    compute_metrics,
    set_seed,
    split_indices,
)


def repeated_splits(X, y, n_repeats=100, train_ratio=0.8):
    """100 repeated 80/20 splits."""
    results = {"linear": [], "ridge": [], "mean": []}
    for i in range(n_repeats):
        train_idx, test_idx = split_indices(len(y), train_ratio, seed=i)
        Xtr, Xte = X[train_idx], X[test_idx]
        ytr, yte = y[train_idx], y[test_idx]
        results["linear"].append(compute_metrics(yte, baseline_linear_regression(Xtr, ytr, Xte)))
        results["ridge"].append(compute_metrics(yte, baseline_ridge_regression(Xtr, ytr, Xte)))
        results["mean"].append(compute_metrics(yte, baseline_mean_quality(Xtr, ytr, Xte)))
    return results


def repeated_cv(X, y, n_repeats=50, k_folds=5):
    """50 repeated 5-fold CV."""
    results = {"linear": [], "ridge": [], "mean": []}
    for rep in range(n_repeats):
        rng = np.random.default_rng(rep)
        indices = np.arange(len(y))
        rng.shuffle(indices)
        folds = np.array_split(indices, k_folds)
        for fold_i in range(k_folds):
            test_idx = folds[fold_i]
            train_idx = np.concatenate([folds[j] for j in range(k_folds) if j != fold_i])
            Xtr, Xte = X[train_idx], X[test_idx]
            ytr, yte = y[train_idx], y[test_idx]
            results["linear"].append(compute_metrics(yte, baseline_linear_regression(Xtr, ytr, Xte)))
            results["ridge"].append(compute_metrics(yte, baseline_ridge_regression(Xtr, ytr, Xte)))
            results["mean"].append(compute_metrics(yte, baseline_mean_quality(Xtr, ytr, Xte)))
    return results


def permutation_null(X, y, n_splits=100, n_perms_per_split=5):
    """Permutation null analysis."""
    observed_rs = []
    null_rs = []
    for i in range(n_splits):
        train_idx, test_idx = split_indices(len(y), 0.8, seed=i)
        Xtr, Xte = X[train_idx], X[test_idx]
        ytr, yte = y[train_idx], y[test_idx]
        pred = baseline_linear_regression(Xtr, ytr, Xte)
        m = compute_metrics(yte, pred)
        observed_rs.append(m["pearson"])
        rng = np.random.default_rng(i + 10000)
        for _ in range(n_perms_per_split):
            y_shuf = rng.permutation(y)
            ytr_s, yte_s = y_shuf[train_idx], y_shuf[test_idx]
            pred_s = baseline_linear_regression(Xtr, ytr_s, Xte)
            null_rs.append(compute_metrics(yte_s, pred_s)["pearson"])
    return observed_rs, null_rs


def bic_bf10(X, y, n_splits=100):
    """BIC-based BF10 approximation."""
    bf10_values = []
    k0, k1 = 1, X.shape[1] + 1  # intercept-only vs full model
    for i in range(n_splits):
        train_idx, test_idx = split_indices(len(y), 0.8, seed=i)
        Xtr, Xte = X[train_idx], X[test_idx]
        ytr, yte = y[train_idx], y[test_idx]
        n = len(yte)
        # Null: mean-only
        pred_null = baseline_mean_quality(Xtr, ytr, Xte)
        sse_null = float(np.sum((yte - pred_null) ** 2))
        # Alt: linear regression
        pred_alt = baseline_linear_regression(Xtr, ytr, Xte)
        sse_alt = float(np.sum((yte - pred_alt) ** 2))
        if sse_null <= 0 or sse_alt <= 0:
            continue
        bic_null = n * np.log(sse_null / n) + k0 * np.log(n)
        bic_alt = n * np.log(sse_alt / n) + k1 * np.log(n)
        delta_bic = bic_null - bic_alt
        log10_bf10 = delta_bic / (2 * np.log(10))
        bf10_values.append(log10_bf10)
    return bf10_values


def group_holdout_analysis(X, y, group_ids, n_repeats=20):
    """Repeated group holdout (hold out one school at a time, repeated with different seeds)."""
    unique_groups = sorted(set(group_ids))
    group_arr = np.array(group_ids)
    results = []
    for g in unique_groups:
        mask = group_arr != g
        Xtr, Xte = X[mask], X[~mask]
        ytr, yte = y[mask], y[~mask]
        if len(Xte) == 0:
            continue
        pred = baseline_linear_regression(Xtr, ytr, Xte)
        m = compute_metrics(yte, pred)
        m["holdout_group"] = g
        m["n_test"] = int((~mask).sum())
        results.append(m)
    return results


def feature_group_ablation(X, y, behavioral_idx, metadata_idx, n_splits=100):
    """Feature-group ablation: behavioral vs metadata."""
    results = {"full": [], "behavioral": [], "metadata": []}
    for i in range(n_splits):
        train_idx, test_idx = split_indices(len(y), 0.8, seed=i)
        ytr, yte = y[train_idx], y[test_idx]
        for key, idx in [("full", None), ("behavioral", behavioral_idx), ("metadata", metadata_idx)]:
            Xtr = X[train_idx] if idx is None else X[train_idx][:, idx]
            Xte = X[test_idx] if idx is None else X[test_idx][:, idx]
            pred = baseline_linear_regression(Xtr, ytr, Xte)
            results[key].append(compute_metrics(yte, pred))
    return results


def summarize(metrics_list):
    """Summarize a list of metric dicts."""
    keys = ["mae", "r2", "pearson"]
    s = {}
    for k in keys:
        vals = [m[k] for m in metrics_list]
        s[f"{k}_mean"] = float(np.mean(vals))
        s[f"{k}_std"] = float(np.std(vals))
        s[f"{k}_q025"] = float(np.percentile(vals, 2.5))
        s[f"{k}_q975"] = float(np.percentile(vals, 97.5))
    return s


def main():
    adapter = UCIStudentAdapter()
    repo_root = Path(__file__).resolve().parent
    bundle = adapter.load(dataset_root=str(repo_root / "datasets" / "UCI"))
    X, y = bundle.X, bundle.y
    group_ids = bundle.group_ids
    data_card = bundle.data_card

    behavioral_cols = data_card["behavioral_cols"]
    metadata_cols = data_card["metadata_cols"]
    all_cols = bundle.feature_names
    behavioral_idx = [all_cols.index(c) for c in behavioral_cols]
    metadata_idx = [all_cols.index(c) for c in metadata_cols]

    print("=" * 60)
    print(f"UCI Student Performance Extended Audit")
    print(f"N={len(y)}, features={X.shape[1]} (30 original → {X.shape[1]} after encoding)")
    print(f"Target: G3 (final grade), mean={np.mean(y):.2f}, std={np.std(y):.2f}, range=[{np.min(y):.0f}, {np.max(y):.0f}]")
    print(f"Groups: {data_card['group_sizes']}")
    print("=" * 60)

    # 1. Repeated 80/20
    print("\n--- 100 Repeated 80/20 Splits ---")
    r80 = repeated_splits(X, y, n_repeats=100)
    for model in ["linear", "ridge", "mean"]:
        s = summarize(r80[model])
        print(f"  {model:8s}: MAE={s['mae_mean']:.4f}±{s['mae_std']:.4f}  R²={s['r2_mean']:.4f}±{s['r2_std']:.4f}  r={s['pearson_mean']:.4f}")

    # Instability ratio
    delta_mae = summarize(r80["mean"])["mae_mean"] - summarize(r80["linear"])["mae_mean"]
    instability = summarize(r80["linear"])["mae_std"] / (abs(delta_mae) + 1e-8)
    beat_rate = np.mean([r80["linear"][i]["mae"] < r80["mean"][i]["mae"] for i in range(100)])
    print(f"  Δ_MAE = {delta_mae:.4f}, I = {instability:.4f}, beat_rate = {beat_rate:.2f}")

    # 2. Repeated 5-fold CV
    print("\n--- 50 Repeated 5-fold CV ---")
    rcv = repeated_cv(X, y, n_repeats=50)
    for model in ["linear", "ridge", "mean"]:
        s = summarize(rcv[model])
        print(f"  {model:8s}: MAE={s['mae_mean']:.4f}±{s['mae_std']:.4f}  R²={s['r2_mean']:.4f}±{s['r2_std']:.4f}  r={s['pearson_mean']:.4f}")

    cv_delta = summarize(rcv["mean"])["mae_mean"] - summarize(rcv["linear"])["mae_mean"]
    cv_instability = summarize(rcv["linear"])["mae_std"] / (abs(cv_delta) + 1e-8)
    cv_beat = np.mean([rcv["linear"][i]["mae"] < rcv["mean"][i]["mae"] for i in range(len(rcv["linear"]))])
    print(f"  Δ_MAE = {cv_delta:.4f}, I = {cv_instability:.4f}, beat_rate = {cv_beat:.2f}")

    # 3. Permutation null
    print("\n--- Permutation Null ---")
    obs_rs, null_rs = permutation_null(X, y, n_splits=100, n_perms_per_split=5)
    print(f"  observed r: mean={np.mean(obs_rs):.4f}, 95% CI=[{np.percentile(obs_rs, 2.5):.4f}, {np.percentile(obs_rs, 97.5):.4f}]")
    print(f"  null r:     mean={np.mean(null_rs):.4f}, 95% CI=[{np.percentile(null_rs, 2.5):.4f}, {np.percentile(null_rs, 97.5):.4f}]")
    # Empirical p-value
    obs_median = np.median(obs_rs)
    p_val = np.mean(np.array(null_rs) >= obs_median)
    print(f"  empirical p (null >= observed median): {p_val:.6f}")

    # 4. BF10
    print("\n--- BIC-based BF10 ---")
    bf10_log = bic_bf10(X, y, n_splits=100)
    print(f"  log10(BF10): median={np.median(bf10_log):.2f}, range=[{np.min(bf10_log):.2f}, {np.max(bf10_log):.2f}]")

    # 5. Group holdout
    print("\n--- Group Holdout (leave-one-school-out) ---")
    gh = group_holdout_analysis(X, y, group_ids)
    for g in gh:
        print(f"  holdout={g['holdout_group']}: n_test={g['n_test']}, MAE={g['mae']:.4f}, R²={g['r2']:.4f}, r={g['pearson']:.4f}")

    # 6. Feature-group ablation
    print("\n--- Feature-Group Ablation (100 splits) ---")
    fa = feature_group_ablation(X, y, behavioral_idx, metadata_idx, n_splits=100)
    for group in ["full", "behavioral", "metadata"]:
        s = summarize(fa[group])
        n_cols = X.shape[1] if group == "full" else len(behavioral_idx) if group == "behavioral" else len(metadata_idx)
        print(f"  {group:12s} ({n_cols:2d} cols): MAE={s['mae_mean']:.4f}±{s['mae_std']:.4f}  R²={s['r2_mean']:.4f}±{s['r2_std']:.4f}  r={s['pearson_mean']:.4f}")

    # Save full results
    output = {
        "repeated_80_20": {m: summarize(r80[m]) for m in r80},
        "repeated_cv": {m: summarize(rcv[m]) for m in rcv},
        "instability_80_20": {"delta_mae": delta_mae, "I": instability, "beat_rate": float(beat_rate)},
        "instability_cv": {"delta_mae": cv_delta, "I": cv_instability, "beat_rate": float(cv_beat)},
        "permutation": {"obs_r_mean": float(np.mean(obs_rs)), "null_r_mean": float(np.mean(null_rs)), "empirical_p": float(p_val)},
        "bf10_log10": {"median": float(np.median(bf10_log)), "min": float(np.min(bf10_log)), "max": float(np.max(bf10_log))},
        "group_holdout": gh,
        "feature_ablation": {g: summarize(fa[g]) for g in fa},
    }
    out_dir = Path(__file__).resolve().parent / "generated" / "uci_student"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "extended_results.json"
    out_path.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nFull results saved to {out_path}")


if __name__ == "__main__":
    main()
