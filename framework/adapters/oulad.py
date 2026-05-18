from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..types import AuditDatasetBundle


class OULADAdapter:
    name = "oulad"

    def load(self, dataset_root: Optional[str] = None) -> AuditDatasetBundle:
        if dataset_root is None:
            dataset_root = "OULAD"
        root = Path(dataset_root)
        required_files = [
            "studentInfo.csv", "courses.csv", "studentAssessment.csv",
            "studentRegistration.csv", "studentVle.csv", "vle.csv", "assessments.csv"
        ]
        for fname in required_files:
            if not (root / fname).exists():
                return AuditDatasetBundle(
                    dataset_name="oulad",
                    dataset_root=str(root),
                    X=None,
                    y=None,
                    group_ids=None,
                    data_card={"error": f"Missing file: {fname}"},
                    feature_names=[],
                    missing_data=True,
                    error=f"Missing file: {fname}"
                )
        info = pd.read_csv(root / "studentInfo.csv")
        vle = pd.read_csv(root / "studentVle.csv")
        vle_agg = vle.groupby("id_student").agg(
            vle_total_clicks=("sum_click", "sum"),
            vle_active_weeks=("date", "nunique"),
        ).reset_index()
        assess = pd.read_csv(root / "studentAssessment.csv")
        assess_agg = assess.groupby("id_student").agg(
            assessment_count=("id_assessment", "count"),
            assessment_score_mean=("score", "mean"),
            assessment_score_std=("score", "std"),
        ).reset_index()
        df = info.merge(vle_agg, on="id_student", how="left").merge(assess_agg, on="id_student", how="left")
        features = [
            "age_band", "gender", "region", "highest_education", "imd_band", "num_of_prev_attempts",
            "vle_total_clicks", "vle_active_weeks", "assessment_count", "assessment_score_mean", "assessment_score_std"
        ]
        X_df = pd.get_dummies(df[features], dummy_na=True)
        X_df = X_df.fillna(0).astype(float)
        X = X_df.values
        y = df["final_result"].map({"Pass": 1, "Distinction": 1, "Fail": 0, "Withdrawn": 0}).fillna(0).values
        group_ids = df["code_module"].astype(str) + "_" + df["code_presentation"].astype(str)
        data_card = {
            "n_samples": len(df),
            "features": features,
            "n_pass": int((y == 1).sum()),
            "n_fail": int((y == 0).sum()),
            "mean_vle_clicks": float(np.nanmean(df["vle_total_clicks"])),
            "mean_assess_score": float(np.nanmean(df["assessment_score_mean"])),
        }
        return AuditDatasetBundle(
            dataset_name="oulad",
            dataset_root=str(root),
            X=X,
            y=y,
            group_ids=group_ids.tolist(),
            data_card=data_card,
            feature_names=list(X_df.columns),
            missing_data=False,
            error=None
        )
