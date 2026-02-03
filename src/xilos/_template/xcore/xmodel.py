import abc
from pathlib import Path
from typing import Any

import pandas as pd


class XModel(abc.ABC):
    """Abstract base class for all ML models."""

    def __init__(self, **kwargs):
        self.model = self._build_model(**kwargs)

    @abc.abstractmethod
    def _build_model(self, **kwargs) -> Any:
        """Build and return the underlying model object (e.g. sklearn estimator)."""

    @abc.abstractmethod
    def fit(self, x: pd.DataFrame, y: pd.Series) -> None:
        """Train the model."""

    @abc.abstractmethod
    def predict(self, x: pd.DataFrame) -> Any:
        """Make predictions."""

    @abc.abstractmethod
    def save(self, path: str | Path) -> None:
        """Save model to disk."""

    @classmethod
    @abc.abstractmethod
    def load(cls, path: str | Path) -> "XModel":
        """Load model from disk."""
