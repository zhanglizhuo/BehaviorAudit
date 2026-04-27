from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

import numpy as np

from .baselines import (
    ablation_feature_subset_analysis,
    ablation_group_holdout,
    ablation_label_permutation_test,
    baseline_feature2_probe,
    baseline_linear_regression,
    baseline_mean_quality,
    baseline_quadratic_probe,
    baseline_ridge_regression,
    compute_metrics,
    set_seed,
    split_indices,
)
from .types import DatasetAdapter


@dataclass(frozen=True)
class AuditConfig:
    train_split_ratio: float = 0.8
    ridge_alpha: float = 1.0
    n_permutations: int = 5
    feature_subset_size: int = 2
    seeds: Tuple[int, ...] = (0, 1, 2)


def _summarize_seed_metrics(seed_metrics: Dict[int, Dict[str, float]]) -> Dict[str, float]:
    mae_vals = [metrics["mae"] for metrics in seed_metrics.values()]
    r2_vals = [metrics["r2"] for metrics in seed_metrics.values()]
    return {
        "mae_mean": float(np.mean(mae_vals)),
        "mae_std": float(np.std(mae_vals)),
        "r2_mean": float(np.mean(r2_vals)),
        "r2_std": float(np.std(r2_vals)),
        "pearson_mean": float(np.mean([metrics["pearson"] for metrics in seed_metrics.values()])),
        "spearman_mean": float(np.mean([metrics["spearman"] for metrics in seed_metrics.values()])),
    }


def run_behavior_audit(
    adapter: DatasetAdapter,
    output_dir: str | Path,
    config: Optional[AuditConfig] = None,
    dataset_root: Optional[str] = None,
) -> Dict[str, object]:
    config = config or AuditConfig()
    bundle = adapter.load(dataset_root=dataset_root)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results: Dict[str, object] = {
        "dataset": adapter.name,
        "hyperparameters": asdict(config),
        "data_card": bundle.data_card,
        "metrics": {},
        "status": "running",
    }

    if bundle.missing_data or bundle.X is None or bundle.y is None:
        results["status"] = "missing_data"
        results["metrics"] = {"error": bundle.error or "Dataset unavailable."}
        _write_outputs(output_path, bundle.data_card, results)
        return results

    X = bundle.X
    y = bundle.y
    group_ids = bundle.group_ids

    teacher_holdout_enabled = bool(group_ids and len(set(group_ids)) < len(y))
    all_results: Dict[str, Dict[int, Dict[str, float]]] = {}
    ablation_results: Dict[str, Dict[int, Dict[str, float]]] = {}

    baselines = ["mean_quality", "linear_regression", "ridge_regression"]
    probes = ["feature1_quadratic_probe", "feature2_linear_probe"]
    ablations = ["label_permutation_null", "group_holdout", "random_2feature_subset"]

    for seed in config.seeds:
        set_seed(seed)
        train_idx, test_idx = split_indices(len(y), config.train_split_ratio, seed)
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        if len(X_test) == 0:
            continue

        for name in baselines:
            if name == "mean_quality":
                y_pred = baseline_mean_quality(X_train, y_train, X_test)
            elif name == "linear_regression":
                y_pred = baseline_linear_regression(X_train, y_train, X_test)
            else:
                y_pred = baseline_ridge_regression(X_train, y_train, X_test, alpha=config.ridge_alpha)
            all_results.setdefault(name, {})[seed] = compute_metrics(y_test, y_pred)

        all_results.setdefault("feature1_quadratic_probe", {})[seed] = compute_metrics(
            y_test,
            baseline_quadratic_probe(X_train, y_train, X_test),
        )
        all_results.setdefault("feature2_linear_probe", {})[seed] = compute_metrics(
            y_test,
            baseline_feature2_probe(X_train, y_train, X_test),
        )

        permutation_metrics = ablation_label_permutation_test(X, y, n_permutations=config.n_permutations, seed=seed)
        if permutation_metrics:
            ablation_results.setdefault("label_permutation_null", {})[seed] = {
                "mae": float(np.mean([item["mae"] for item in permutation_metrics])),
                "r2": float(np.mean([item["r2"] for item in permutation_metrics])),
                "pearson": float(np.mean([item["pearson"] for item in permutation_metrics])),
                "spearman": float(np.mean([item["spearman"] for item in permutation_metrics])),
            }

        if teacher_holdout_enabled:
            holdout_metrics = ablation_group_holdout(X, y, group_ids, seed=seed)
            if holdout_metrics:
                ablation_results.setdefault("group_holdout", {})[seed] = holdout_metrics

        all_results.setdefault("random_2feature_subset", {})[seed] = compute_metrics(
            y_test,
            ablation_feature_subset_analysis(
                X_train,
                y_train,
                X_test,
                subset_size=config.feature_subset_size,
                seed=seed,
            ),
        )

    final_metrics: Dict[str, Dict[str, float]] = {}
    for name, seed_metrics in all_results.items():
        if seed_metrics:
            final_metrics[name] = _summarize_seed_metrics(seed_metrics)
    for name, seed_metrics in ablation_results.items():
        if seed_metrics:
            final_metrics[name] = _summarize_seed_metrics(seed_metrics)

    results.update(
        {
            "metrics": final_metrics,
            "status": "completed",
            "samples_processed": int(len(y)),
            "features_used": int(X.shape[1]) if len(X.shape) > 1 else 0,
            "group_holdout_enabled": teacher_holdout_enabled,
        }
    )
    _write_outputs(output_path, bundle.data_card, results)
    return results


def _write_outputs(output_dir: Path, data_card: Dict[str, object], results: Dict[str, object]) -> None:
    (output_dir / "data_card.json").write_text(json.dumps(data_card, indent=2, ensure_ascii=False), encoding="utf-8")
    (output_dir / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
