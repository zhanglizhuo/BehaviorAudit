from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import numpy as np


def set_seed(seed: int) -> None:
    np.random.seed(seed)


def split_indices(n_samples: int, train_ratio: float = 0.8, seed: int = 0) -> Tuple[np.ndarray, np.ndarray]:
    if n_samples <= 1:
        return np.arange(n_samples), np.array([], dtype=int)

    indices = np.arange(n_samples)
    rng = np.random.default_rng(seed)
    rng.shuffle(indices)

    split_idx = int(round(n_samples * train_ratio))
    split_idx = max(1, min(n_samples - 1, split_idx))
    return indices[:split_idx], indices[split_idx:]


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    mae = float(np.mean(np.abs(y_true - y_pred)))
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - np.mean(y_true)) ** 2))
    r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    pearson = 0.0
    if len(y_true) > 1 and np.std(y_true) > 0 and np.std(y_pred) > 0:
        pearson = float(np.corrcoef(y_true, y_pred)[0, 1])
        if math.isnan(pearson):
            pearson = 0.0

    rank_true = np.argsort(np.argsort(y_true))
    rank_pred = np.argsort(np.argsort(y_pred))
    spearman = 0.0
    if len(y_true) > 1 and np.std(rank_true) > 0 and np.std(rank_pred) > 0:
        spearman = float(np.corrcoef(rank_true, rank_pred)[0, 1])
        if math.isnan(spearman):
            spearman = 0.0

    return {
        "mae": mae,
        "r2": r2,
        "pearson": pearson,
        "spearman": spearman,
    }


def baseline_mean_quality(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray) -> np.ndarray:
    del X_train
    if len(y_train) == 0:
        return np.zeros(len(X_test), dtype=float)
    return np.full(len(X_test), float(np.mean(y_train)), dtype=float)


def baseline_linear_regression(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray) -> np.ndarray:
    if X_train.shape[0] == 0 or X_train.shape[1] == 0:
        return baseline_mean_quality(X_train, y_train, X_test)

    X_train_bias = np.c_[np.ones((X_train.shape[0], 1)), X_train]
    X_test_bias = np.c_[np.ones((X_test.shape[0], 1)), X_test]

    try:
        coefficients, _, _, _ = np.linalg.lstsq(X_train_bias, y_train, rcond=None)
        return X_test_bias @ coefficients
    except np.linalg.LinAlgError:
        return np.full(len(X_test), float(np.mean(y_train)) if len(y_train) > 0 else 0.0)


def baseline_ridge_regression(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray, alpha: float = 1.0) -> np.ndarray:
    if X_train.shape[0] == 0 or X_train.shape[1] == 0:
        return baseline_mean_quality(X_train, y_train, X_test)

    X_train_bias = np.c_[np.ones((X_train.shape[0], 1)), X_train]
    X_test_bias = np.c_[np.ones((X_test.shape[0], 1)), X_test]

    n = X_train_bias.shape[1]
    try:
        xtx = X_train_bias.T @ X_train_bias
        reg_matrix = alpha * np.eye(n)
        reg_matrix[0, 0] = 0
        coefficients = np.linalg.inv(xtx + reg_matrix) @ X_train_bias.T @ y_train
        return X_test_bias @ coefficients
    except np.linalg.LinAlgError:
        return np.full(len(X_test), float(np.mean(y_train)) if len(y_train) > 0 else 0.0)


def baseline_quadratic_probe(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray) -> np.ndarray:
    if X_train.shape[1] == 0:
        return baseline_mean_quality(X_train, y_train, X_test)

    x1 = X_train[:, 0].reshape(-1, 1)
    x1_test = X_test[:, 0].reshape(-1, 1)
    x_poly = np.hstack([np.ones_like(x1), x1, x1**2])
    x_test_poly = np.hstack([np.ones_like(x1_test), x1_test, x1_test**2])

    try:
        coefficients, _, _, _ = np.linalg.lstsq(x_poly, y_train, rcond=None)
        return x_test_poly @ coefficients
    except np.linalg.LinAlgError:
        return np.full(len(X_test), float(np.mean(y_train)) if len(y_train) > 0 else 0.0)


def baseline_feature2_probe(X_train: np.ndarray, y_train: np.ndarray, X_test: np.ndarray) -> np.ndarray:
    if X_train.shape[1] == 0:
        return baseline_mean_quality(X_train, y_train, X_test)

    if X_train.shape[1] >= 2:
        feature_train = X_train[:, 1]
        feature_test = X_test[:, 1]
    else:
        feature_train = np.var(X_train, axis=1)
        feature_test = np.var(X_test, axis=1)

    x_train = np.c_[np.ones(len(feature_train)), feature_train]
    x_test = np.c_[np.ones(len(feature_test)), feature_test]

    try:
        coefficients, _, _, _ = np.linalg.lstsq(x_train, y_train, rcond=None)
        return x_test @ coefficients
    except np.linalg.LinAlgError:
        return np.full(len(X_test), float(np.mean(y_train)) if len(y_train) > 0 else 0.0)


def ablation_label_permutation_test(X: np.ndarray, y: np.ndarray, n_permutations: int = 5, seed: int = 0) -> List[Dict[str, float]]:
    rng = np.random.default_rng(seed)
    metrics_list: List[Dict[str, float]] = []

    for i in range(n_permutations):
        y_shuffled = rng.permutation(y)
        train_idx, test_idx = split_indices(len(y), train_ratio=0.8, seed=seed + 1000 + i)
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y_shuffled[train_idx], y_shuffled[test_idx]

        if len(X_test) == 0:
            metrics_list.append({"mae": 0.0, "r2": 0.0, "pearson": 0.0, "spearman": 0.0})
            continue

        y_pred = baseline_linear_regression(X_train, y_train, X_test)
        metrics_list.append(compute_metrics(y_test, y_pred))

    return metrics_list


def ablation_group_holdout(X: np.ndarray, y: np.ndarray, group_ids: Optional[List[str]], seed: int = 0) -> Optional[Dict[str, float]]:
    if not group_ids:
        return None

    unique_groups = sorted(set(group_ids))
    if len(unique_groups) < 2:
        return None

    rng = np.random.default_rng(seed)
    holdout_group = str(rng.choice(unique_groups))
    mask = np.array([group != holdout_group for group in group_ids], dtype=bool)

    X_train, X_test = X[mask], X[~mask]
    y_train, y_test = y[mask], y[~mask]
    if len(X_test) == 0:
        return None

    y_pred = baseline_linear_regression(X_train, y_train, X_test)
    return compute_metrics(y_test, y_pred)


def ablation_feature_subset_analysis(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    subset_size: int = 2,
    seed: int = 0,
) -> np.ndarray:
    if X_train.shape[1] == 0 or subset_size <= 0:
        return baseline_mean_quality(X_train, y_train, X_test)

    rng = np.random.default_rng(seed)
    subset_size = min(subset_size, X_train.shape[1])
    if X_train.shape[1] <= subset_size:
        return baseline_linear_regression(X_train, y_train, X_test)

    indices = list(range(X_train.shape[1]))
    rng.shuffle(indices)
    selected_indices = sorted(indices[:subset_size])
    return baseline_linear_regression(X_train[:, selected_indices], y_train, X_test[:, selected_indices])
