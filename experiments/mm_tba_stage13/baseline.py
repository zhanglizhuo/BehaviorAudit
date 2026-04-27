import math

import numpy as np

def set_seed(seed):
    np.random.seed(seed)

def split_indices(n_samples, train_ratio=0.8, seed=0):
    if n_samples <= 1:
        return np.arange(n_samples), np.array([], dtype=int)

    indices = np.arange(n_samples)
    rng = np.random.default_rng(seed)
    rng.shuffle(indices)

    split_idx = int(round(n_samples * train_ratio))
    split_idx = max(1, min(n_samples - 1, split_idx))
    return indices[:split_idx], indices[split_idx:]

def compute_metrics(y_true, y_pred):
    """Computes MAE, R2, Pearson, Spearman."""
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    mae = float(np.mean(np.abs(y_true - y_pred)))

    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
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
        'mae': mae,
        'r2': r2,
        'pearson': pearson,
        'spearman': spearman,
    }

def baseline_mean_quality(X_train, y_train, X_test):
    del X_train
    if len(y_train) == 0:
        return np.zeros(len(X_test))
    mean_val = float(np.mean(y_train))
    return np.full(len(X_test), mean_val, dtype=float)

def baseline_linear_regression(X_train, y_train, X_test):
    if X_train.shape[0] == 0 or X_train.shape[1] == 0:
        return baseline_mean_quality(X_train, y_train, X_test)

    X_train_bias = np.c_[np.ones((X_train.shape[0], 1)), X_train]
    X_test_bias = np.c_[np.ones((X_test.shape[0], 1)), X_test]

    try:
        coefficients, _, _, _ = np.linalg.lstsq(X_train_bias, y_train, rcond=None)
        y_pred = X_test_bias @ coefficients
    except np.linalg.LinAlgError:
        y_pred = np.full(len(X_test), float(np.mean(y_train)) if len(y_train) > 0 else 0.0)

    return y_pred

def baseline_ridge_regression(X_train, y_train, X_test, alpha=1.0):
    if X_train.shape[0] == 0 or X_train.shape[1] == 0:
        return baseline_mean_quality(X_train, y_train, X_test)

    X_train_bias = np.c_[np.ones((X_train.shape[0], 1)), X_train]
    X_test_bias = np.c_[np.ones((X_test.shape[0], 1)), X_test]

    n = X_train_bias.shape[1]
    try:
        XtX = X_train_bias.T @ X_train_bias
        reg_matrix = alpha * np.eye(n)
        reg_matrix[0, 0] = 0
        coefficients = np.linalg.inv(XtX + reg_matrix) @ X_train_bias.T @ y_train
        y_pred = X_test_bias @ coefficients
    except np.linalg.LinAlgError:
        y_pred = np.full(len(X_test), float(np.mean(y_train)) if len(y_train) > 0 else 0.0)

    return y_pred

def baseline_quadratic_density_regression(X_train, y_train, X_test):
    if X_train.shape[1] == 0:
        return baseline_mean_quality(X_train, y_train, X_test)

    x1 = X_train[:, 0].reshape(-1, 1)
    x1_test = X_test[:, 0].reshape(-1, 1)

    X_poly = np.hstack([np.ones_like(x1), x1, x1 ** 2])
    X_test_poly = np.hstack([np.ones_like(x1_test), x1_test, x1_test ** 2])

    try:
        coefficients, _, _, _ = np.linalg.lstsq(X_poly, y_train, rcond=None)
        y_pred = X_test_poly @ coefficients
    except np.linalg.LinAlgError:
        y_pred = np.full(len(X_test), float(np.mean(y_train)) if len(y_train) > 0 else 0.0)

    return y_pred

def baseline_temporal_entropy_regression(X_train, y_train, X_test):
    if X_train.shape[1] == 0:
        return baseline_mean_quality(X_train, y_train, X_test)

    if X_train.shape[1] >= 2:
        entropy_proxy = X_train[:, 1]
        entropy_test = X_test[:, 1]
    else:
        entropy_proxy = np.var(X_train, axis=1)
        entropy_test = np.var(X_test, axis=1)

    X_entropy = np.c_[np.ones(len(entropy_proxy)), entropy_proxy]
    X_test_entropy = np.c_[np.ones(len(entropy_test)), entropy_test]

    try:
        coefficients, _, _, _ = np.linalg.lstsq(X_entropy, y_train, rcond=None)
        y_pred = X_test_entropy @ coefficients
    except np.linalg.LinAlgError:
        y_pred = np.full(len(X_test), float(np.mean(y_train)) if len(y_train) > 0 else 0.0)

    return y_pred

def ablation_label_permutation_test(X, y, n_permutations=5, seed=0):
    rng = np.random.default_rng(seed)
    metrics_list = []

    for i in range(n_permutations):
        y_shuffled = rng.permutation(y)
        train_idx, test_idx = split_indices(len(y), train_ratio=0.8, seed=seed + 1000 + i)
        X_tr, X_te = X[train_idx], X[test_idx]
        y_tr, y_te = y_shuffled[train_idx], y_shuffled[test_idx]

        if len(X_te) == 0:
            metrics_list.append({'mae': 0.0, 'r2': 0.0, 'pearson': 0.0, 'spearman': 0.0})
            continue

        y_pred = baseline_linear_regression(X_tr, y_tr, X_te)
        metrics = compute_metrics(y_te, y_pred)
        metrics_list.append({'mae': metrics['mae'], 'r2': metrics['r2'], 'pearson': metrics['pearson'], 'spearman': metrics['spearman']})

    return metrics_list

def ablation_teacher_holdout(X, y, teacher_ids, seed=0):
    if teacher_ids is None or len(teacher_ids) == 0:
        return None

    unique_teachers = list(set(teacher_ids))
    if len(unique_teachers) < 2:
        return None

    rng = np.random.default_rng(seed)
    holdout_teacher = rng.choice(unique_teachers)

    mask = np.array([t != holdout_teacher for t in teacher_ids])

    X_tr, X_te = X[mask], X[~mask]
    y_tr, y_te = y[mask], y[~mask]

    if len(X_te) == 0:
        return None

    y_pred = baseline_linear_regression(X_tr, y_tr, X_te)
    return compute_metrics(y_te, y_pred)

def ablation_feature_subset_analysis(X_train, y_train, X_test, subset_size=2, seed=0):
    if X_train.shape[1] == 0 or subset_size <= 0:
        return baseline_mean_quality(X_train, y_train, X_test)

    rng = np.random.default_rng(seed)
    subset_size = min(subset_size, X_train.shape[1])

    if X_train.shape[1] <= subset_size:
        return baseline_linear_regression(X_train, y_train, X_test)

    indices = list(range(X_train.shape[1]))
    rng.shuffle(indices)
    selected_indices = sorted(indices[:subset_size])

    X_train_sub = X_train[:, selected_indices]
    X_test_sub = X_test[:, selected_indices] if X_test.shape[1] >= subset_size else X_test
    return baseline_linear_regression(X_train_sub, y_train, X_test_sub)