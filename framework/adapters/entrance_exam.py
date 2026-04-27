"""Adapter for Student Performance on Entrance Examination (UCI ID=582).

N=666, 11 features, 4-class target (Average/Good/Vg/Excellent).
Grouping by Class_ten_education (3 education boards: SEBA/CBSE/OTHERS).
Reference: Bora & Dey (2021).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from ..types import AuditDatasetBundle


class EntranceExamAdapter:
    name = "entrance_exam"

    def load(self, dataset_root: Optional[str] = None) -> AuditDatasetBundle:
        if dataset_root is None:
            dataset_root = "StudentExam"
        root = Path(dataset_root)

        csv_path = root / "student_entrance_582.csv"
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

        # Target: ordinal encoding Average=0, Good=1, Vg=2, Excellent=3
        label_map = {"Average": 0, "Good": 1, "Vg": 2, "Excellent": 3}
        y = df["Performance"].map(label_map).values.astype(float)

        # Features
        feat_df = df.drop(columns=["Performance"])

        # Grouping: Class_ten_education (education board: SEBA/CBSE/OTHERS)
        group_ids = df["Class_ten_education"].astype(str).tolist()

        # One-hot encode
        cat_cols = feat_df.select_dtypes(include=["object"]).columns.tolist()
        X_df = pd.get_dummies(feat_df, columns=cat_cols, dummy_na=False)
        X_df = X_df.fillna(0).astype(float)
        X = X_df.values

        data_card = {
            "n_samples": len(df),
            "n_features_original": len(feat_df.columns),
            "n_features_encoded": X.shape[1],
            "target_distribution": df["Performance"].value_counts().to_dict(),
            "n_groups": df["Class_ten_education"].nunique(),
            "reference": "Bora & Dey (2021)",
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
