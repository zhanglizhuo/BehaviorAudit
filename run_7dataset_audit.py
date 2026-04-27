"""Unified 7-dataset audit experiment.

Runs the full 4-dimension audit + model-complexity ablation on ALL datasets:
  1. MM-TBA (N=186)          — existing
  2. UCI Student (N=649)     — existing 
  3. OULAD (N=32593)         — existing
  4. xAPI-Edu (N=480)        — NEW
  5. Student Dropout (N=3630)— NEW
  6. Entrance Exam (N=666)   — NEW
  7. Higher Ed (N=145)       — NEW

For each dataset, computes:
  - 100 repeated 80/20 splits: MAE, R², Pearson r, beat rate, I ratio
  - 4 models: mean, linear, ridge, RF, GBT
  - Group holdout (where grouping available)
  - Permutation null (500 draws on first 10 splits)
  - Summary table for cross-dataset comparison
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.preprocessing import StandardScaler

from framework.adapters import (
    MMTBAAdapter, OULADAdapter, UCIStudentAdapter,
    XAPIEduAdapter, StudentDropoutAdapter, EntranceExamAdapter, HigherEdAdapter,
)
from framework.baselines import (
    baseline_linear_regression,
    baseline_mean_quality,
    baseline_ridge_regression,
    compute_metrics,
    split_indices,
)

ROOT = Path(__file__).resolve().parent  # BehaviorAudit root (datasets/ live here)


def fit_rf(X_train, y_train, X_test, seed=0):
    m = RandomForestRegressor(n_estimators=100, max_depth=None, random_state=seed, n_jobs=-1)
    m.fit(X_train, y_train)
    return m.predict(X_test)


def fit_gbt(X_train, y_train, X_test, seed=0):
    m = GradientBoostingRegressor(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=seed)
    m.fit(X_train, y_train)
    return m.predict(X_test)


MODELS = {
    "mean": lambda Xtr, ytr, Xte, s: baseline_mean_quality(Xtr, ytr, Xte),
    "linear": lambda Xtr, ytr, Xte, s: baseline_linear_regression(Xtr, ytr, Xte),
    "ridge": lambda Xtr, ytr, Xte, s: baseline_ridge_regression(Xtr, ytr, Xte),
    "rf": lambda Xtr, ytr, Xte, s: fit_rf(Xtr, ytr, Xte, seed=s),
    "gbt": lambda Xtr, ytr, Xte, s: fit_gbt(Xtr, ytr, Xte, seed=s),
}


def run_repeated_splits(X, y, n_repeats=100):
    """100 repeated 80/20 splits for all models."""
    results = {name: [] for name in MODELS}
    for i in range(n_repeats):
        train_idx, test_idx = split_indices(len(y), 0.8, seed=i)
        Xtr, Xte = X[train_idx], X[test_idx]
        ytr, yte = y[train_idx], y[test_idx]
        for name, fn in MODELS.items():
            pred = fn(Xtr, ytr, Xte, i)
            results[name].append(compute_metrics(yte, pred))
    return results


def summarize_results(results, n_repeats=100):
    """Compute summary statistics for each model."""
    summaries = {}
    mean_maes = [results["mean"][i]["mae"] for i in range(n_repeats)]
    mean_mae = np.mean(mean_maes)

    for name in MODELS:
        mae_vals = [r["mae"] for r in results[name]]
        r2_vals = [r["r2"] for r in results[name]]
        r_vals = [r["pearson"] for r in results[name]]

        delta = mean_mae - np.mean(mae_vals)
        I_ratio = np.std(mae_vals) / (abs(delta) + 1e-8) if name != "mean" else float("nan")
        beat_rate = np.mean(
            [results[name][i]["mae"] < results["mean"][i]["mae"] for i in range(n_repeats)]
        ) if name != "mean" else float("nan")

        summaries[name] = {
            "mae_mean": float(np.mean(mae_vals)),
            "mae_std": float(np.std(mae_vals)),
            "r2_mean": float(np.mean(r2_vals)),
            "r2_std": float(np.std(r2_vals)),
            "r_mean": float(np.mean(r_vals)),
            "delta_mae": float(delta),
            "I": float(I_ratio),
            "beat_rate": float(beat_rate),
        }
    return summaries


def run_group_holdout(X, y, group_ids):
    """Leave-one-group-out holdout for model comparison."""
    if group_ids is None:
        return None
    group_arr = np.array(group_ids)
    unique_groups = sorted(set(group_ids))

    # Only run for groups with at least 10 test samples
    valid_groups = [g for g in unique_groups if (group_arr == g).sum() >= 10]
    if len(valid_groups) < 2:
        return None

    group_results = {}
    for g in valid_groups:
        mask = group_arr != g
        Xtr, Xte = X[mask], X[~mask]
        ytr, yte = y[mask], y[~mask]
        n_test = (~mask).sum()

        group_results[g] = {"n_test": n_test, "models": {}}
        for name in ["linear", "ridge", "rf", "gbt"]:
            pred = MODELS[name](Xtr, ytr, Xte, 42)
            m = compute_metrics(yte, pred)
            group_results[g]["models"][name] = m

    # Summarize: mean metrics across held-out groups
    summary = {}
    for name in ["linear", "ridge", "rf", "gbt"]:
        r2_vals = [group_results[g]["models"][name]["r2"] for g in valid_groups]
        mae_vals = [group_results[g]["models"][name]["mae"] for g in valid_groups]
        r_vals = [group_results[g]["models"][name]["pearson"] for g in valid_groups]
        summary[name] = {
            "r2_mean": float(np.mean(r2_vals)),
            "r2_std": float(np.std(r2_vals)),
            "mae_mean": float(np.mean(mae_vals)),
            "r_mean": float(np.mean(r_vals)),
            "n_groups_tested": len(valid_groups),
            "worst_r2": float(np.min(r2_vals)),
            "best_r2": float(np.max(r2_vals)),
        }
    return summary, group_results


def run_permutation_null(X, y, n_splits=10, n_perm=500):
    """Permutation null on first n_splits to check null separation.

    Records both Pearson r and R\u00b2 for the observed model and for every
    permutation draw, so the empirical null distribution can be plotted
    directly (no synthetic approximation needed downstream).
    """
    p_values = []
    for s in range(n_splits):
        train_idx, test_idx = split_indices(len(y), 0.8, seed=s)
        Xtr, Xte = X[train_idx], X[test_idx]
        ytr, yte = y[train_idx], y[test_idx]

        # Observed
        pred = baseline_linear_regression(Xtr, ytr, Xte)
        obs_metrics = compute_metrics(yte, pred)
        obs_r = obs_metrics["pearson"]
        obs_r2 = obs_metrics["r2"]

        # Null distribution
        null_rs = []
        null_r2s = []
        for p in range(n_perm):
            rng = np.random.default_rng(s * 10000 + p)
            y_perm = rng.permutation(ytr)
            pred_null = baseline_linear_regression(Xtr, y_perm, Xte)
            m_null = compute_metrics(yte, pred_null)
            null_rs.append(m_null["pearson"])
            null_r2s.append(m_null["r2"])
        null_rs = np.array(null_rs)
        null_r2s = np.array(null_r2s)
        p_val = float(np.mean(null_rs >= obs_r))
        p_values.append({
            "split": s,
            "obs_r": float(obs_r),
            "obs_r2": float(obs_r2),
            "p_value": p_val,
            "null_r": null_rs.tolist(),
            "null_r2": null_r2s.tolist(),
        })

    # Proportion of splits with p < 0.05
    sig_rate = np.mean([p["p_value"] < 0.05 for p in p_values])
    return {
        "splits": p_values,
        "sig_rate": float(sig_rate),
        "median_p": float(np.median([p["p_value"] for p in p_values])),
        "mean_obs_r": float(np.mean([p["obs_r"] for p in p_values])),
        "mean_obs_r2": float(np.mean([p["obs_r2"] for p in p_values])),
    }


def audit_dataset(name, adapter, dataset_root, n_repeats=100):
    """Run full audit on one dataset."""
    print(f"\n{'='*70}")
    print(f"  AUDITING: {name}")
    print(f"{'='*70}")
    t0 = time.time()

    bundle = adapter.load(dataset_root=dataset_root)
    if bundle.X is None:
        print(f"  ERROR: {bundle.error}")
        return None

    X_raw = bundle.X
    y = bundle.y
    group_ids = bundle.group_ids

    # Standardize
    scaler = StandardScaler()
    X = scaler.fit_transform(X_raw)

    print(f"  N={len(y)}, Features={X.shape[1]}, Groups={len(set(group_ids)) if group_ids else 'N/A'}")
    print(f"  Target: mean={y.mean():.4f}, std={y.std():.4f}, range=[{y.min():.2f}, {y.max():.2f}]")

    # 1. Repeated splits
    print(f"\n  --- Repeated 80/20 splits (n={n_repeats}) ---")
    results = run_repeated_splits(X, y, n_repeats)
    summaries = summarize_results(results, n_repeats)

    for mname in MODELS:
        s = summaries[mname]
        print(
            f"  {mname:8s}: MAE={s['mae_mean']:.4f}±{s['mae_std']:.4f}  "
            f"R²={s['r2_mean']:.4f}  r={s['r_mean']:.4f}  "
            f"Δ_MAE={s['delta_mae']:+.4f}  I={s['I']:.4f}  beat={s['beat_rate']:.2f}"
        )

    # 2. Group holdout
    print(f"\n  --- Group Holdout ---")
    gh = run_group_holdout(X, y, group_ids)
    if gh is not None:
        gh_summary, gh_detail = gh
        for mname in ["linear", "ridge", "rf", "gbt"]:
            gs = gh_summary[mname]
            print(
                f"  {mname:8s}: R²={gs['r2_mean']:.4f}±{gs['r2_std']:.4f}  "
                f"MAE={gs['mae_mean']:.4f}  r={gs['r_mean']:.4f}  "
                f"worst_R²={gs['worst_r2']:.4f}  best_R²={gs['best_r2']:.4f}  "
                f"(n_groups={gs['n_groups_tested']})"
            )
    else:
        print("  No valid grouping (insufficient group sizes)")
        gh_summary = None

    # 3. Permutation null
    print(f"\n  --- Permutation Null (10 splits × 500 draws) ---")
    perm = run_permutation_null(X, y, n_splits=10, n_perm=500)
    print(f"  sig_rate={perm['sig_rate']:.2f}  median_p={perm['median_p']:.4f}  mean_obs_r={perm['mean_obs_r']:.4f}")
    for p in perm["splits"]:
        star = "*" if p["p_value"] < 0.05 else " "
        print(f"    split {p['split']}: r={p['obs_r']:.4f}  p={p['p_value']:.4f} {star}")

    elapsed = time.time() - t0
    print(f"\n  Elapsed: {elapsed:.1f}s")

    # 4. Compile audit profile
    lin = summaries["linear"]
    profile = {
        "dataset": name,
        "N": len(y),
        "n_features": X.shape[1],
        "n_groups": len(set(group_ids)) if group_ids else 0,
        # Dimension 1: Baseline gap
        "delta_mae_linear": lin["delta_mae"],
        "beat_rate_linear": lin["beat_rate"],
        # Dimension 2: Split instability
        "I_linear": lin["I"],
        "I_ridge": summaries["ridge"]["I"],
        "I_rf": summaries["rf"]["I"],
        "I_gbt": summaries["gbt"]["I"],
        # Dimension 3: Null separation
        "perm_sig_rate": perm["sig_rate"],
        "perm_median_p": perm["median_p"],
        # Dimension 4: Metadata adequacy (group holdout R² retention)
        "group_holdout_available": gh_summary is not None,
        "group_r2_linear": gh_summary["linear"]["r2_mean"] if gh_summary else None,
        "group_r2_worst": gh_summary["linear"]["worst_r2"] if gh_summary else None,
        "iid_r2_linear": lin["r2_mean"],
        # Model complexity
        "summaries": summaries,
        "group_holdout": gh_summary,
        "permutation": perm,
    }

    return profile


def print_comparison_table(profiles):
    """Print cross-dataset comparison table."""
    print(f"\n\n{'='*100}")
    print(f"  CROSS-DATASET AUDIT COMPARISON TABLE")
    print(f"{'='*100}")

    header = f"{'Dataset':<22} {'N':>6} {'Feat':>4} {'ΔMAE':>7} {'Beat':>5} {'I_lin':>6} {'I_gbt':>6} {'Perm%':>5} {'iid_R²':>7} {'Grp_R²':>7} {'W_R²':>7} {'Profile':<18}"
    print(header)
    print("-" * len(header))

    for p in sorted(profiles, key=lambda x: x["I_linear"]):
        grp_r2 = f"{p['group_r2_linear']:.3f}" if p["group_r2_linear"] is not None else "N/A"
        worst_r2 = f"{p['group_r2_worst']:.3f}" if p["group_r2_worst"] is not None else "N/A"

        # Determine audit profile
        dim_pass = 0
        # D1: baseline gap
        d1 = p["beat_rate_linear"] >= 0.90
        dim_pass += d1
        # D2: split instability
        d2 = p["I_linear"] < 1.0
        dim_pass += d2
        # D3: null separation
        d3 = p["perm_sig_rate"] >= 0.80
        dim_pass += d3
        # D4: metadata adequacy
        if p["group_holdout_available"] and p["iid_r2_linear"] > 0:
            r2_retention = p["group_r2_linear"] / (p["iid_r2_linear"] + 1e-8)
            d4 = r2_retention >= 0.50
        elif p["group_holdout_available"]:
            d4 = p["group_r2_linear"] > 0
        else:
            d4 = False  # no grouping = fail
        dim_pass += d4

        labels = {0: "Fragile(0/4)", 1: "Weak(1/4)", 2: "Partial(2/4)",
                  3: "Mostly OK(3/4)", 4: "Strong(4/4)"}
        profile_label = labels[dim_pass]
        flags = f"[{'✓' if d1 else '✗'}{'✓' if d2 else '✗'}{'✓' if d3 else '✗'}{'✓' if d4 else '✗'}]"

        print(
            f"{p['dataset']:<22} {p['N']:>6} {p['n_features']:>4} "
            f"{p['delta_mae_linear']:>+7.3f} {p['beat_rate_linear']:>5.2f} "
            f"{p['I_linear']:>6.3f} {p['I_gbt']:>6.3f} "
            f"{p['perm_sig_rate']:>5.2f} {p['iid_r2_linear']:>7.3f} "
            f"{grp_r2:>7} {worst_r2:>7} "
            f"{flags} {profile_label}"
        )


def main():
    datasets = [
        ("MM-TBA (N=186)", MMTBAAdapter(), str(ROOT / "datasets" / "MM-TBA")),
        ("Higher Ed (N=145)", HigherEdAdapter(), str(ROOT / "datasets" / "StudentExam")),
        ("xAPI-Edu (N=480)", XAPIEduAdapter(), str(ROOT / "datasets" / "xAPI-Edu")),
        ("Entrance Exam (N=666)", EntranceExamAdapter(), str(ROOT / "datasets" / "StudentExam")),
        ("UCI Student (N=649)", UCIStudentAdapter(), str(ROOT / "datasets" / "UCI")),
        ("Dropout (N=3630)", StudentDropoutAdapter(), str(ROOT / "datasets" / "StudentDropout")),
        ("OULAD (N=32593)", OULADAdapter(), str(ROOT / "datasets" / "OULAD")),
    ]

    profiles = []
    for name, adapter, root in datasets:
        profile = audit_dataset(name, adapter, root, n_repeats=100)
        if profile is not None:
            profiles.append(profile)

    if profiles:
        print_comparison_table(profiles)

        # Save raw results
        out_path = Path(__file__).resolve().parent / "paper" / "audit_7dataset_results.json"
        # Strip non-serializable parts
        save_profiles = []
        for p in profiles:
            sp = {k: v for k, v in p.items() if k not in ("summaries", "group_holdout", "permutation")}
            sp["summaries"] = p["summaries"]
            sp["group_holdout"] = p["group_holdout"]
            sp["perm_sig_rate"] = p["perm_sig_rate"]
            sp["perm_median_p"] = p["perm_median_p"]
            sp["permutation"] = p["permutation"]  # raw null distributions
            save_profiles.append(sp)
        with open(out_path, "w") as f:
            json.dump(save_profiles, f, indent=2, default=str)
        print(f"\nResults saved to {out_path}")

        # Also write a copy at repo root for figure regeneration scripts
        root_out = Path(__file__).resolve().parent / "audit_7dataset_results.json"
        with open(root_out, "w") as f:
            json.dump(save_profiles, f, indent=2, default=str)
        print(f"Also saved to {root_out}")


if __name__ == "__main__":
    main()
