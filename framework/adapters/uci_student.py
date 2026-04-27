from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from ..types import AuditDatasetBundle


class UCIStudentAdapter:
    """Adapter for the UCI Student Performance dataset (Cortez & Silva, 2008).

    Uses the Portuguese-language subset (student-por.csv, N=649) by default.
    Target: G3 (final grade, 0-20, continuous regression).
    Grouping: school (GP / MS).

    Design choice: G1 and G2 (first and second period grades) are excluded
    from the feature set because they are trivially predictive of G3 and would
    mask the contribution of demographic and behavioral variables.  The audit
    therefore tests whether contextual covariates alone support a defensible
    baseline — the same question asked of MM-TBA's 13-feature representation.
    """

    name = "uci_student"

    def load(self, dataset_root: Optional[str] = None) -> AuditDatasetBundle:
        if dataset_root is None:
            dataset_root = "UCI"
        root = Path(dataset_root)

        # Prefer Portuguese (larger); fall back to Math
        por_path = root / "student-por.csv"
        mat_path = root / "student-mat.csv"
        if por_path.exists():
            csv_path = por_path
        elif mat_path.exists():
            csv_path = mat_path
        else:
            return AuditDatasetBundle(
                dataset_name="uci_student",
                dataset_root=str(root),
                X=None,
                y=None,
                group_ids=None,
                data_card={"error": "Missing student-por.csv and student-mat.csv"},
                feature_names=[],
                missing_data=True,
                error="Missing student-por.csv and student-mat.csv",
            )

        df = pd.read_csv(csv_path, sep=";")

        # --- Target ---
        y = df["G3"].values.astype(float)

        # --- Features (exclude G1, G2, G3) ---
        drop_cols = ["G1", "G2", "G3"]
        feat_df = df.drop(columns=drop_cols, errors="ignore")

        # --- Grouping variable: school ---
        group_ids = df["school"].astype(str).tolist()

        # --- One-hot encode categorical columns ---
        cat_cols = feat_df.select_dtypes(include=["object"]).columns.tolist()
        num_cols = feat_df.select_dtypes(exclude=["object"]).columns.tolist()

        X_df = pd.get_dummies(feat_df, columns=cat_cols, dummy_na=False)
        X_df = X_df.fillna(0).astype(float)
        X = X_df.values

        # --- Feature groups for ablation reporting ---
        # Behavioral/academic: studytime, failures, schoolsup, famsup, paid,
        #   activities, nursery, higher, absences  (9 original variables)
        # Metadata/demographic: everything else (21 original variables)
        behavioral_original = {
            "studytime", "failures", "schoolsup", "famsup", "paid",
            "activities", "nursery", "higher", "absences",
        }
        behavioral_cols = []
        metadata_cols = []
        for col in X_df.columns:
            base = col.split("_")[0] if "_" in col else col
            # Check against original variable names
            matched = any(col.startswith(bv) for bv in behavioral_original)
            if matched:
                behavioral_cols.append(col)
            else:
                metadata_cols.append(col)

        data_card = {
            "n_samples": len(df),
            "n_features_original": len(feat_df.columns),
            "n_features_encoded": X.shape[1],
            "n_behavioral_cols": len(behavioral_cols),
            "n_metadata_cols": len(metadata_cols),
            "target_mean": float(np.mean(y)),
            "target_std": float(np.std(y)),
            "target_min": float(np.min(y)),
            "target_max": float(np.max(y)),
            "source_file": csv_path.name,
            "groups": sorted(set(group_ids)),
            "group_sizes": {g: int((np.array(group_ids) == g).sum()) for g in sorted(set(group_ids))},
            "features_original": list(feat_df.columns),
            "behavioral_cols": behavioral_cols,
            "metadata_cols": metadata_cols,
        }

        return AuditDatasetBundle(
            dataset_name="uci_student",
            dataset_root=str(root),
            X=X,
            y=y,
            group_ids=group_ids,
            data_card=data_card,
            feature_names=list(X_df.columns),
            missing_data=False,
            error=None,
        )
