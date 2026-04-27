"""Sensitivity analysis: classification-appropriate metrics for binary/ordinal datasets.

Runs AUC-ROC (binary), accuracy, and ordinal-appropriate metrics alongside MAE/R²
to verify that the audit conclusions (instability ratio, group-holdout findings)
hold under classification-appropriate metrics.

Tests: OULAD (binary), Dropout (binary), xAPI-Edu (3-class), Entrance Exam (4-class)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

from framework.adapters import (
    OULADAdapter, StudentDropoutAdapter,
    XAPIEduAdapter, EntranceExamAdapter,
)
from framework.baselines import split_indices

ROOT = Path(__file__).resolve().parent.parent


def fit_models_classify(X_train, y_train, X_test, seed=0):
    """Fit all 4 classification models, return predicted probabilities and class labels."""
    results = {}

    # Majority-class baseline
    from collections import Counter
    majority = Counter(y_train).most_common(1)[0][0]
    maj_pred = np.full(len(X_test), majority)
    results["majority"] = {"pred": maj_pred, "prob": None}

    # Logistic Regression (analog of linear)
    lr = LogisticRegression(max_iter=2000, random_state=seed, solver="lbfgs")
    lr.fit(X_train, y_train)
    results["logistic"] = {"pred": lr.predict(X_test), "prob": lr.predict_proba(X_test)}

    # Ridge Classifier
    rc = RidgeClassifier(alpha=1.0, random_state=seed)
    rc.fit(X_train, y_train)
    # RidgeClassifier doesn't have predict_proba; use decision function
    results["ridge_clf"] = {"pred": rc.predict(X_test), "prob": None}

    # Random Forest
    rf = RandomForestClassifier(n_estimators=100, max_depth=None, random_state=seed, n_jobs=-1)
    rf.fit(X_train, y_train)
    results["rf_clf"] = {"pred": rf.predict(X_test), "prob": rf.predict_proba(X_test)}

    # Gradient Boosting
    gb = GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, random_state=seed)
    gb.fit(X_train, y_train)
    results["gbt_clf"] = {"pred": gb.predict(X_test), "prob": gb.predict_proba(X_test)}

    return results


def compute_classification_metrics(y_true, model_results, n_classes):
    """Compute accuracy and AUC-ROC (where applicable)."""
    metrics = {}
    for name, res in model_results.items():
        pred = res["pred"]
        prob = res["prob"]

        acc = accuracy_score(y_true, pred)
        auc = None

        if prob is not None and n_classes == 2:
            # Binary AUC
            try:
                auc = roc_auc_score(y_true, prob[:, 1])
            except (ValueError, IndexError):
                auc = None
        elif prob is not None and n_classes > 2:
            # Multi-class AUC (one-vs-rest)
            try:
                auc = roc_auc_score(y_true, prob, multi_class="ovr", average="weighted")
            except (ValueError, IndexError):
                auc = None

        metrics[name] = {"accuracy": float(acc), "auc_roc": float(auc) if auc is not None else None}
    return metrics


def run_classification_audit(X, y, n_classes, n_repeats=100):
    """Repeated 80/20 splits with classification metrics."""
    all_metrics = {name: [] for name in ["majority", "logistic", "ridge_clf", "rf_clf", "gbt_clf"]}

    for i in range(n_repeats):
        train_idx, test_idx = split_indices(len(y), 0.8, seed=i)
        Xtr, Xte = X[train_idx], X[test_idx]
        ytr, yte = y[train_idx].astype(int), y[test_idx].astype(int)

        model_results = fit_models_classify(Xtr, ytr, Xte, seed=i)
        metrics = compute_classification_metrics(yte, model_results, n_classes)
        for name in all_metrics:
            all_metrics[name].append(metrics[name])

    # Summarize
    summaries = {}
    for name in all_metrics:
        accs = [m["accuracy"] for m in all_metrics[name]]
        aucs = [m["auc_roc"] for m in all_metrics[name] if m["auc_roc"] is not None]

        maj_accs = [m["accuracy"] for m in all_metrics["majority"]]
        delta_acc = np.mean(accs) - np.mean(maj_accs) if name != "majority" else 0.0
        I_acc = np.std(accs) / (abs(delta_acc) + 1e-8) if name != "majority" else float("nan")
        beat_rate = np.mean([accs[i] > maj_accs[i] for i in range(len(accs))]) if name != "majority" else float("nan")

        summaries[name] = {
            "acc_mean": float(np.mean(accs)),
            "acc_std": float(np.std(accs)),
            "auc_mean": float(np.mean(aucs)) if aucs else None,
            "auc_std": float(np.std(aucs)) if aucs else None,
            "delta_acc": float(delta_acc),
            "I_acc": float(I_acc),
            "beat_rate_acc": float(beat_rate),
        }
    return summaries


def run_classification_group_holdout(X, y, group_ids, n_classes):
    """Leave-one-group-out with classification metrics."""
    if group_ids is None:
        return None

    group_arr = np.array(group_ids)
    unique_groups = sorted(set(group_ids))
    valid_groups = [g for g in unique_groups if (group_arr == g).sum() >= 10]
    if len(valid_groups) < 2:
        return None

    group_results = {}
    for g in valid_groups:
        mask = group_arr != g
        Xtr, Xte = X[mask], X[~mask]
        ytr, yte = y[mask].astype(int), y[~mask].astype(int)

        model_results = fit_models_classify(Xtr, ytr, Xte, seed=42)
        metrics = compute_classification_metrics(yte, model_results, n_classes)
        group_results[g] = metrics

    # Summary per model
    summary = {}
    for name in ["logistic", "ridge_clf", "rf_clf", "gbt_clf"]:
        accs = [group_results[g][name]["accuracy"] for g in valid_groups]
        aucs = [group_results[g][name]["auc_roc"] for g in valid_groups
                if group_results[g][name]["auc_roc"] is not None]
        summary[name] = {
            "acc_mean": float(np.mean(accs)),
            "acc_std": float(np.std(accs)),
            "acc_worst": float(np.min(accs)),
            "auc_mean": float(np.mean(aucs)) if aucs else None,
            "n_groups": len(valid_groups),
        }
    return summary


def main():
    datasets = [
        ("OULAD (N=32593, binary)", OULADAdapter(), 2, str(ROOT / "datasets" / "OULAD")),
        ("Dropout (N=3630, binary)", StudentDropoutAdapter(), 2, str(ROOT / "datasets" / "StudentDropout")),
        ("xAPI-Edu (N=480, 3-class)", XAPIEduAdapter(), 3, str(ROOT / "datasets" / "xAPI-Edu")),
        ("Entrance Exam (N=666, 4-class)", EntranceExamAdapter(), 4, str(ROOT / "datasets" / "StudentExam")),
    ]

    all_results = []

    for ds_name, adapter, n_classes, ds_root in datasets:
        print(f"\n{'='*70}")
        print(f"  CLASSIFICATION SENSITIVITY: {ds_name}")
        print(f"{'='*70}")
        t0 = time.time()

        bundle = adapter.load(dataset_root=ds_root)
        if bundle.X is None:
            print(f"  ERROR: {bundle.error}")
            continue

        scaler = StandardScaler()
        X = scaler.fit_transform(bundle.X)
        y = bundle.y
        group_ids = bundle.group_ids

        print(f"  N={len(y)}, n_classes={n_classes}, groups={len(set(group_ids)) if group_ids else 'N/A'}")

        # 1. Repeated splits
        print(f"\n  --- Repeated 80/20 splits (n=100) ---")
        summaries = run_classification_audit(X, y, n_classes, n_repeats=100)

        for name, s in summaries.items():
            auc_str = f"AUC={s['auc_mean']:.4f}±{s['auc_std']:.4f}" if s["auc_mean"] else "AUC=N/A"
            print(
                f"  {name:12s}: Acc={s['acc_mean']:.4f}±{s['acc_std']:.4f}  {auc_str}  "
                f"ΔAcc={s['delta_acc']:+.4f}  I_acc={s['I_acc']:.4f}  beat={s['beat_rate_acc']:.2f}"
            )

        # 2. Group holdout
        print(f"\n  --- Group Holdout (classification) ---")
        gh = run_classification_group_holdout(X, y, group_ids, n_classes)
        if gh:
            for name, gs in gh.items():
                auc_str = f"AUC={gs['auc_mean']:.4f}" if gs["auc_mean"] else "AUC=N/A"
                print(
                    f"  {name:12s}: Acc={gs['acc_mean']:.4f}±{gs['acc_std']:.4f}  "
                    f"worst={gs['acc_worst']:.4f}  {auc_str}  (n_groups={gs['n_groups']})"
                )
        else:
            print("  No valid grouping")

        elapsed = time.time() - t0
        print(f"  Elapsed: {elapsed:.1f}s")

        all_results.append({
            "dataset": ds_name,
            "n_classes": n_classes,
            "summaries": summaries,
            "group_holdout": gh,
        })

    # Save results
    out_path = Path(__file__).parent / "paper" / "classification_sensitivity_results.json"
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\nResults saved to {out_path}")


if __name__ == "__main__":
    main()
