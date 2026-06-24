"""
supplementary_revision_analyses.py
====================================
Three supplementary analyses requested by Scientific Reports reviewers:

1. Reviewer 1 (#5): Cross-group standard deviation for group-holdout R^2
2. Reviewer 2 (#2): Train-test R^2 gap for each model
3. Reviewer 2 (#4): Feature-attribution stability across 100 repeated splits

Run with: python3 scripts/supplementary_revision_analyses.py
"""
from __future__ import annotations
import json, os
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings("ignore")

RANDOM_SEEDS = list(range(100))

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = REPO_ROOT / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MODELS = {
    "linear": LinearRegression(),
    "ridge": Ridge(alpha=1.0),
    "rf":     RandomForestRegressor(n_estimators=50, random_state=0),
    "gbt":    GradientBoostingRegressor(
        n_estimators=50, max_depth=3, learning_rate=0.1, random_state=0
    ),
}

# ── Data loading helpers ────────────────────────────────────────────────────

def load_uci_student(root: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    path = root / "datasets" / "UCI" / "student-por.csv"
    df = pd.read_csv(path, sep=";")
    y = df["G3"].values.astype(float)
    df = df.drop(columns=["G3", "G1", "G2"])
    df = pd.get_dummies(df, drop_first=True)
    groups = df["school_MS"].values if "school_MS" in df.columns else None
    X = df.drop(columns=[c for c in df.columns if c.startswith("school_")])
    return X.values.astype(float), y, groups


def load_higher_ed(root: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    path = root / "datasets" / "StudentExam" / "higher_ed_856.csv"
    df = pd.read_csv(path)
    # Identify target column (contains "OUTPUT Grade")
    target_col = [c for c in df.columns if "OUTPUT" in c and "Grade" in c][0]
    y = df[target_col].values.astype(float)
    groups = df["Course ID"].values if "Course ID" in df.columns else None
    drop_cols = [target_col, "Course ID"] if groups is not None else [target_col]
    df = df.drop(columns=drop_cols)
    df = pd.get_dummies(df, drop_first=True)
    return df.values.astype(float), y, groups


def load_oulad(root: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray | None]:
    # simplified OULAD loader for revision analyses
    info = pd.read_csv(root / "datasets" / "OULAD" / "studentInfo.csv")
    ass = pd.read_csv(root / "datasets" / "OULAD" / "assessments.csv")
    reg = pd.read_csv(root / "datasets" / "OULAD" / "studentRegistration.csv")
    vle = pd.read_csv(root / "datasets" / "OULAD" / "studentVle.csv")
    sa = pd.read_csv(root / "datasets" / "OULAD" / "studentAssessment.csv")

    score = sa.groupby("id_student")["score"].mean().reset_index()
    vle_agg = vle.groupby("id_student")["sum_click"].sum().reset_index()

    merged = info.merge(score, on="id_student", how="left")
    merged = merged.merge(vle_agg, on="id_student", how="left")
    merged = merged.dropna(subset=["score", "sum_click"])
    # reduce sample for faster analysis in revision
    merged = merged.sample(n=min(5000, len(merged)), random_state=0)

    merged["final_result"] = merged["final_result"].map(
        {"Pass": 1, "Distinction": 1, "Fail": 0, "Withdrawn": 0}
    )
    y = merged["final_result"].values.astype(float)
    groups = merged["code_presentation"].values
    df = merged.drop(columns=["final_result", "id_student", "code_presentation"])
    df = pd.get_dummies(df, drop_first=True)
    return df.values.astype(float), y, groups


DATASET_LOADERS = {
    "UCI Student": load_uci_student,
    "Higher Ed": load_higher_ed,
    "OULAD": load_oulad,
}


# ── Analysis 1: Group-holdout uncertainty (reads from main pipeline JSON) ──

def analysis1_group_holdout_uncertainty() -> pd.DataFrame:
    json_path = REPO_ROOT / "audit_7dataset_results.json"
    with open(json_path) as f:
        data = json.load(f)

    MODEL_KEY_MAP = {"linear": "linear", "ridge": "ridge", "rf": "rf", "gbt": "gbt"}
    records = []
    for d in data:
        name = d.get("dataset", "?")
        gh = d.get("group_holdout", {})
        if not isinstance(gh, dict) or not gh:
            continue
        for model_name, json_key in MODEL_KEY_MAP.items():
            m = gh.get(json_key)
            if m is None:
                continue
            r2_mean = m.get("r2_mean")
            r2_std = m.get("r2_std")
            r2_min = m.get("worst_r2")
            r2_max = m.get("best_r2")
            n_grp = m.get("n_groups_tested", 0)
            if r2_mean is None:
                continue
            records.append({
                "dataset": name,
                "model": model_name,
                "n_groups_tested": n_grp,
                "group_r2_mean": r2_mean,
                "group_r2_sd": r2_std if r2_std is not None else "N/A",
                "group_r2_min": r2_min if r2_min is not None else "N/A",
                "group_r2_max": r2_max if r2_max is not None else "N/A",
            })

    df = pd.DataFrame(records)
    print("\n=== Analysis 1: Group-Holdout Uncertainty (from main pipeline JSON) ===")
    print(df.to_string(index=False))
    return df


# ── Analysis 2: Train-test gap ──────────────────────────────────────────────

def analysis2_train_test_gap(dataset_name: str, X, y, n_splits: int = 100):
    records = []
    for model_name, model_template in MODELS.items():
        train_r2s, test_r2s = [], []
        for seed in RANDOM_SEEDS[:n_splits]:
            X_tr, X_te, y_tr, y_te = train_test_split(
                X, y, test_size=0.2, random_state=seed
            )
            scaler = StandardScaler().fit(X_tr)
            model = type(model_template)(**model_template.get_params())
            model.fit(scaler.transform(X_tr), y_tr)
            train_r2s.append(r2_score(y_tr, model.predict(scaler.transform(X_tr))))
            test_r2s.append(r2_score(y_te, model.predict(scaler.transform(X_te))))

        train_r2s = np.array(train_r2s)
        test_r2s = np.array(test_r2s)
        gap = train_r2s - test_r2s
        records.append({
            "dataset": dataset_name,
            "model": model_name,
            "train_r2_mean": train_r2s.mean(),
            "test_r2_mean": test_r2s.mean(),
            "train_test_gap_mean": gap.mean(),
            "train_test_gap_sd": gap.std(ddof=1),
        })

    df = pd.DataFrame(records)
    print(f"\n=== Analysis 2: Train-Test Gap -- {dataset_name} ===")
    print(df.to_string(index=False))
    return df


# ── Analysis 3: Feature-attribution stability ───────────────────────────────

def analysis3_feature_attribution_stability(
    dataset_name: str, X, y, n_splits: int = 100, top_k: int = 10
):
    feature_names = [f"f{i}" for i in range(X.shape[1])]
    X_arr = np.asarray(X)

    # Linear coefficients
    coefs = []
    for seed in RANDOM_SEEDS[:n_splits]:
        X_tr, _, y_tr, _ = train_test_split(X_arr, y, test_size=0.2, random_state=seed)
        scaler = StandardScaler().fit(X_tr)
        model = LinearRegression().fit(scaler.transform(X_tr), y_tr)
        coefs.append(model.coef_)
    coefs = np.array(coefs)

    mean_coef = coefs.mean(axis=0)
    sd_coef = coefs.std(axis=0, ddof=1)
    majority_sign = np.sign(mean_coef)
    sign_flip_rate = (np.sign(coefs) != majority_sign).mean(axis=0)

    order = np.argsort(-np.abs(mean_coef))[:top_k]
    lin_df = pd.DataFrame({
        "dataset": dataset_name,
        "feature": [feature_names[i] for i in order],
        "mean_coef": mean_coef[order],
        "sd_coef": sd_coef[order],
        "sign_flip_rate": sign_flip_rate[order],
    })
    print(f"\n=== Analysis 3: Linear Coef Stability -- {dataset_name} ===")
    print(lin_df.to_string(index=False))

    # RF importances
    importances = []
    for seed in RANDOM_SEEDS[:n_splits]:
        X_tr, _, y_tr, _ = train_test_split(X_arr, y, test_size=0.2, random_state=seed)
        scaler = StandardScaler().fit(X_tr)
        model = RandomForestRegressor(n_estimators=100, random_state=seed).fit(
            scaler.transform(X_tr), y_tr
        )
        importances.append(model.feature_importances_)
    importances = np.array(importances)

    mean_imp = importances.mean(axis=0)
    sd_imp = importances.std(axis=0, ddof=1)
    cv_imp = sd_imp / (mean_imp + 1e-8)

    order_imp = np.argsort(-mean_imp)[:top_k]
    rf_df = pd.DataFrame({
        "dataset": dataset_name,
        "feature": [feature_names[i] for i in order_imp],
        "mean_importance": mean_imp[order_imp],
        "sd_importance": sd_imp[order_imp],
        "cv_importance": cv_imp[order_imp],
    })
    print(f"\n=== Analysis 3: RF Importance Stability -- {dataset_name} ===")
    print(rf_df.to_string(index=False))

    return lin_df, rf_df


# ── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    TARGETS = ["UCI Student", "Higher Ed", "OULAD"]
    all_a1, all_a2, lin_stab, rf_stab = [], [], [], []

    a1 = analysis1_group_holdout_uncertainty()
    if a1 is not None:
        all_a1.append(a1)

    for name in TARGETS:
        loader = DATASET_LOADERS.get(name)
        if loader is None:
            print(f"Skipping {name}: no loader defined")
            continue
        print(f"\n{'='*60}\nLoading {name}...\n{'='*60}")
        X, y, groups = loader(REPO_ROOT)
        print(f"  Shape: {X.shape}, groups: {len(np.unique(groups)) if groups is not None else 'N/A'}")

        a2 = analysis2_train_test_gap(name, X, y)
        all_a2.append(a2)

        lin_df, rf_df = analysis3_feature_attribution_stability(name, X, y)
        lin_stab.append(lin_df)
        rf_stab.append(rf_df)

    # Save CSVs
    if all_a1:
        pd.concat(all_a1, ignore_index=True).to_csv(
            OUT_DIR / "supp_table_group_holdout_uncertainty.csv", index=False)
    if all_a2:
        pd.concat(all_a2, ignore_index=True).to_csv(
            OUT_DIR / "supp_table_train_test_gap.csv", index=False)
    if lin_stab:
        pd.concat(lin_stab, ignore_index=True).to_csv(
            OUT_DIR / "supp_table_linear_coef_stability.csv", index=False)
    if rf_stab:
        pd.concat(rf_stab, ignore_index=True).to_csv(
            OUT_DIR / "supp_table_rf_importance_stability.csv", index=False)

    print(f"\n{'='*60}\nAll outputs saved to {OUT_DIR}/\n{'='*60}")
