from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol

import numpy as np


@dataclass
class AuditDatasetBundle:
    dataset_name: str
    dataset_root: Optional[str]
    X: Optional[np.ndarray]
    y: Optional[np.ndarray]
    group_ids: Optional[List[str]]
    data_card: Dict[str, object]
    feature_names: List[str]
    missing_data: bool
    error: Optional[str] = None
    group_column_indices: Optional[list[int]] = None


class DatasetAdapter(Protocol):
    name: str

    def load(self, dataset_root: Optional[str] = None) -> AuditDatasetBundle:
        ...
