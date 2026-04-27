"""Adapter for Higher Education Students Performance Evaluation (UCI ID=856).

N=145, 31 features, continuous target (OUTPUT Grade 0-7).
Grouping by Course ID (9 unique courses).
Reference: Yilmaz & Sekeroglu (2020).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from ..types import AuditDatasetBundle


class HigherEdAdapter:
    name = "higher_ed"

    def load(self, dataset_root: Optional[str] = None) -> AuditDatasetBundle:
        if dataset_root is None:
            dataset_root = "StudentExam"
        root = Path(dataset_root)

        csv_path = root / "higher_ed_856.csv"
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

        # Target: continuous grade 0-7
        y = df["OUTPUT Grade"].values.astype(float)

        # Features
        feat_df = df.drop(columns=["OUTPUT Grade"])

        # Grouping: Course ID
        group_ids = df["Course ID"].astype(str).tolist()

        # One-hot encode categoricals
        cat_cols = feat_df.select_dtypes(include=["object"]).columns.tolist()
        if cat_cols:
            X_df = pd.get_dummies(feat_df, columns=cat_cols, dummy_na=False)
        else:
            X_df = feat_df.copy()
        X_df = X_df.fillna(0).astype(float)
        X = X_df.values

        data_card = {
            "n_samples": len(df),
            "n_features_original": len(feat_df.columns),
            "n_features_encoded": X.shape[1],
            "target_mean": float(y.mean()),
            "target_std": float(y.std()),
            "target_range": f"{y.min()}-{y.max()}",
            "n_groups": df["Course ID"].nunique(),
            "reference": "Yilmaz & Sekeroglu (2020)",
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
