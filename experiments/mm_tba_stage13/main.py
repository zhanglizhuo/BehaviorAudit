import json

import numpy as np

from baseline import *
from data_loader import *

HYPERPARAMETERS = {
    'train_split_ratio': 0.8,
    'ridge_alpha': 1.0,
    'n_permutations': 5,
    'feature_subset_size': 2,
}

SEEDS = [0, 1, 2]

def main():
    results = {
        'hyperparameters': HYPERPARAMETERS,
        'data_card': {},
        'metrics': {},
        'status': 'running',
    }

    print('Loading MM-TBA local data...')
    data_status = load_mm_tba_data(root_dir='.')
    results['data_card'] = get_data_card(data_status)

    if data_status['missing_data']:
        print(f"CRITICAL: {data_status.get('error', 'MM-TBA data unavailable.')}")
        results['status'] = 'missing_data'
        results['metrics'] = {'error': data_status.get('error', 'MM-TBA data unavailable.')}
        with open('data_card.json', 'w') as f:
            json.dump(results['data_card'], f, indent=2)
        with open('results.json', 'w') as f:
            json.dump(results, f, indent=2)
        return

    print(f"Loaded MM-TBA data from {data_status['dataset_root']}")

    print('Extracting features and targets from loaded files...')
    X, y, teacher_ids = extract_features_and_targets(data_status)

    if X is None or y is None:
        print('CRITICAL: Could not extract features and targets.')
        results['status'] = 'extraction_failed'
        results['metrics'] = {'error': 'Failed to extract features and targets'}
        with open('data_card.json', 'w') as f:
            json.dump(results['data_card'], f, indent=2)
        with open('results.json', 'w') as f:
            json.dump(results, f, indent=2)
        return

    if len(y) == 0:
        print('CRITICAL: No valid target values found.')
        results['status'] = 'no_targets'
        results['metrics'] = {'error': 'No valid target values found'}
        with open('data_card.json', 'w') as f:
            json.dump(results['data_card'], f, indent=2)
        with open('results.json', 'w') as f:
            json.dump(results, f, indent=2)
        return

    print(f"Successfully loaded {len(y)} samples with {X.shape[1] if len(X.shape) > 1 else 0} features.")

    teacher_holdout_enabled = teacher_ids is not None and len(set(teacher_ids)) < len(y)
    if not teacher_holdout_enabled:
        print('Warning: teacher-level IDs are unavailable in the MM-TBA lecture evaluation subset; skipping teacher_holdout.')

    baselines = ['mean_quality', 'linear_regression', 'ridge_regression']
    proposed_methods = ['quadratic_density', 'temporal_entropy']
    ablations = ['label_permutation', 'teacher_holdout', 'feature_subset']

    all_results = {}
    ablation_results = {}

    for seed in SEEDS:
        set_seed(seed)

        train_idx, test_idx = split_indices(len(y), HYPERPARAMETERS['train_split_ratio'], seed)
        X_tr, X_te = X[train_idx], X[test_idx]
        y_tr, y_te = y[train_idx], y[test_idx]

        if len(X_te) == 0:
            print(f'SEED {seed}: Insufficient data for split, skipping this seed.')
            continue

        print(f'\n--- SEED {seed} ---')

        # Baselines
        for cond_name in baselines:
            if cond_name == 'mean_quality':
                y_pred = baseline_mean_quality(X_tr, y_tr, X_te)
            elif cond_name == 'linear_regression':
                y_pred = baseline_linear_regression(X_tr, y_tr, X_te)
            else:
                y_pred = baseline_ridge_regression(X_tr, y_tr, X_te, alpha=HYPERPARAMETERS['ridge_alpha'])

            metrics = compute_metrics(y_te, y_pred)
            print(f"condition={cond_name} seed={seed} primary_metric: {metrics['mae']:.4f}")
            all_results.setdefault(cond_name, {})[seed] = metrics

        # Proposed methods
        for cond_name in proposed_methods:
            if cond_name == 'quadratic_density':
                y_pred = baseline_quadratic_density_regression(X_tr, y_tr, X_te)
            else:
                y_pred = baseline_temporal_entropy_regression(X_tr, y_tr, X_te)

            metrics = compute_metrics(y_te, y_pred)
            print(f"condition={cond_name} seed={seed} primary_metric: {metrics['mae']:.4f}")
            all_results.setdefault(cond_name, {})[seed] = metrics

        # Ablations
        for cond_name in ablations:
            if cond_name == 'label_permutation':
                perm_metrics = ablation_label_permutation_test(X, y, n_permutations=HYPERPARAMETERS['n_permutations'], seed=seed)
                if perm_metrics:
                    avg_mae = float(np.mean([m['mae'] for m in perm_metrics]))
                    avg_r2 = float(np.mean([m['r2'] for m in perm_metrics]))
                    avg_pearson = float(np.mean([m['pearson'] for m in perm_metrics]))
                    avg_spearman = float(np.mean([m['spearman'] for m in perm_metrics]))
                    print(f"condition={cond_name} seed={seed} primary_metric: {avg_mae:.4f}")
                    ablation_results.setdefault(cond_name, {})[seed] = {
                        'mae': avg_mae, 'r2': avg_r2, 'pearson': avg_pearson, 'spearman': avg_spearman
                    }
            elif cond_name == 'teacher_holdout':
                if not teacher_holdout_enabled:
                    continue
                holdout = ablation_teacher_holdout(X, y, teacher_ids, seed=seed)
                if holdout:
                    print(f"condition={cond_name} seed={seed} primary_metric: {holdout['mae']:.4f}")
                    ablation_results.setdefault(cond_name, {})[seed] = holdout
            else:
                y_pred = ablation_feature_subset_analysis(X_tr, y_tr, X_te, subset_size=HYPERPARAMETERS['feature_subset_size'], seed=seed)
                metrics = compute_metrics(y_te, y_pred)
                print(f"condition={cond_name} seed={seed} primary_metric: {metrics['mae']:.4f}")
                all_results.setdefault(cond_name, {})[seed] = metrics

    final_metrics = {}

    for cond_name, seed_metrics in all_results.items():
        if len(seed_metrics) == 0:
            continue
        mae_vals = [m['mae'] for m in seed_metrics.values()]
        r2_vals = [m['r2'] for m in seed_metrics.values()]
        final_metrics[cond_name] = {
            'mae_mean': float(np.mean(mae_vals)),
            'mae_std': float(np.std(mae_vals)),
            'r2_mean': float(np.mean(r2_vals)),
            'r2_std': float(np.std(r2_vals)),
            'pearson_mean': float(np.mean([m['pearson'] for m in seed_metrics.values()])),
            'spearman_mean': float(np.mean([m['spearman'] for m in seed_metrics.values()])),
        }
        print(f"condition={cond_name} primary_metric_mean: {final_metrics[cond_name]['mae_mean']:.4f} primary_metric_std: {final_metrics[cond_name]['mae_std']:.4f}")

    for cond_name, seed_metrics in ablation_results.items():
        if len(seed_metrics) == 0:
            continue
        mae_vals = [m['mae'] for m in seed_metrics.values()]
        r2_vals = [m['r2'] for m in seed_metrics.values()] if 'r2' in list(seed_metrics.values())[0] else []
        final_metrics[cond_name] = {
            'mae_mean': float(np.mean(mae_vals)),
            'mae_std': float(np.std(mae_vals)),
            'r2_mean': float(np.mean(r2_vals)) if r2_vals else 0.0,
            'r2_std': float(np.std(r2_vals)) if r2_vals else 0.0,
            'pearson_mean': float(np.mean([m['pearson'] for m in seed_metrics.values()])) if 'pearson' in list(seed_metrics.values())[0] else 0.0,
            'spearman_mean': float(np.mean([m['spearman'] for m in seed_metrics.values()])) if 'spearman' in list(seed_metrics.values())[0] else 0.0,
        }
        print(f"condition={cond_name} primary_metric_mean: {final_metrics[cond_name]['mae_mean']:.4f} primary_metric_std: {final_metrics[cond_name]['mae_std']:.4f}")

    print('\n=== EXPERIMENT SUMMARY ===')
    print(f"Total conditions evaluated: {len(final_metrics)}")
    print(f"Seeds per condition: {len(SEEDS)}")
    for cond_name, metrics in sorted(final_metrics.items()):
        print(f"condition={cond_name} primary_metric_mean: {metrics['mae_mean']:.4f} primary_metric_std: {metrics['mae_std']:.4f}")

    results['metrics'] = final_metrics
    results['status'] = 'completed'
    results['samples_processed'] = len(y)
    results['features_used'] = X.shape[1] if len(X.shape) > 1 else 0
    results['teachers_ids_count'] = len(set(teacher_ids)) if teacher_ids is not None else 0
    results['teacher_holdout_enabled'] = teacher_holdout_enabled

    with open('data_card.json', 'w') as f:
        json.dump(results['data_card'], f, indent=2)

    with open('results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print('\nExperiment finished. Results saved to results.json')

if __name__ == '__main__':
    main()