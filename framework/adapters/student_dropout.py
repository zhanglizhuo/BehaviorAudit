"""Adapter for Predict Students' Dropout and Academic Success (UCI ID=697).

N=4424, 36 features, 3-class target (Dropout/Enrolled/Graduate).
Grouping by Course (17 unique).
Reference: Martins et al. (2021) / Realinho et al. (2022).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from ..types import AuditDatasetBundle


class StudentDropoutAdapter:
    name = "student_dropout"

    def load(self, dataset_root: Optional[str] = None) -> AuditDatasetBundle:
        if dataset_root is None:
            dataset_root = "StudentDropout"
        root = Path(dataset_root)

        csv_path = root / "student_dropout.csv"
        if not csv_path.exists():
            return AuditDatasetBundle(
                dataset_name=self.name,
                dataset_root=str(root),
                X=None, y=None, group_ids=None,
                data_card={"error": f"Missing {csv_path}"},
                feature_names=[], missing_data=True,
                error=f"Missing {csv_path}",
            )

        df = pd.read_csv(csv_path)

        # Target: binary — Graduate=1, Dropout=0, exclude Enrolled (ambiguous)
        df_clean = df[df["Target"] != "Enrolled"].copy()
        label_map = {"Dropout": 0, "Graduate": 1}
        y = df_clean["Target"].map(label_map).values.astype(float)

        # Features: all numeric columns except Target
        feat_df = df_clean.drop(columns=["Target"])

        # Grouping: Course (17 unique programs)
        group_ids = df_clean["Course"].astype(str).tolist()

        # All features are already numeric in this dataset
        cat_cols = feat_df.select_dtypes(include=["object"]).columns.tolist()
        if cat_cols:
            X_df = pd.get_dummies(feat_df, columns=cat_cols, dummy_na=False)
        else:
            X_df = feat_df.copy()
        X_df = X_df.fillna(0).astype(float)
        X = X_df.values

        data_card = {
            "n_samples": len(df_clean),
            "n_samples_total": len(df),
            "n_excluded_enrolled": int((df["Target"] == "Enrolled").sum()),
            "n_features_original": len(feat_df.columns),
            "n_features_encoded": X.shape[1],
            "n_graduate": int((y == 1).sum()),
            "n_dropout": int((y == 0).sum()),
            "n_groups": df_clean["Course"].nunique(),
            "reference": "Realinho et al. (2022)",
        }

        return AuditDatasetBundle(
            dataset_name=self.name,
            dataset_root=str(root),
            X=X, y=y,
            group_ids=group_ids,
            data_card=data_card,
            feature_names=list(X_df.columns),
            missing_data=False, error=None,
        )
