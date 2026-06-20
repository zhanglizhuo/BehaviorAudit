"""Adapter for xAPI-Edu-Data (Kalboard 360).

N=480, 16 features, 3-class target (L/M/H), grouping by Topic (12 classes).
Reference: Amrieh et al., 2016.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from ..types import AuditDatasetBundle


class XAPIEduAdapter:
    name = "xapi_edu"

    def load(self, dataset_root: Optional[str] = None) -> AuditDatasetBundle:
        if dataset_root is None:
            dataset_root = "xAPI-Edu"
        root = Path(dataset_root)

        csv_path = root / "xAPI-Edu-Data.csv"
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

        # Target: L=0, M=1, H=2 (ordinal encoding for regression-style audit)
        label_map = {"L": 0, "M": 1, "H": 2}
        y = df["Class"].map(label_map).values.astype(float)

        # Features: everything except Class
        feat_df = df.drop(columns=["Class"])

        # Grouping: Topic (12 unique subjects)
        group_ids = df["Topic"].astype(str).tolist()

        # One-hot encode categoricals
        cat_cols = feat_df.select_dtypes(include=["object"]).columns.tolist()
        X_df = pd.get_dummies(feat_df, columns=cat_cols, dummy_na=False)
        X_df = X_df.fillna(0).astype(float)
        X = X_df.values

        data_card = {
            "n_samples": len(df),
            "n_features_original": len(feat_df.columns),
            "n_features_encoded": X.shape[1],
            "target_distribution": df["Class"].value_counts().to_dict(),
            "n_groups": df["Topic"].nunique(),
            "reference": "Amrieh et al. (2016)",
        }

        group_col_idxs = [i for i, col in enumerate(X_df.columns)
                          if col.startswith("Topic_")]

        return AuditDatasetBundle(
            dataset_name=self.name,
            dataset_root=str(root),
            X=X, y=y,
            group_ids=group_ids,
            data_card=data_card,
            feature_names=list(X_df.columns),
            missing_data=False, error=None,
            group_column_indices=group_col_idxs or None,
        )
