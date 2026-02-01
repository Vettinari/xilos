import abc
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from loguru import logger

from ..xcore.xmodel import XModel


class ExampleLGBMModel(XModel):
    """Abstract base class for all ML models."""

    def __init__(self, **kwargs):
        self.model = self._build_model(**kwargs)

    @abc.abstractmethod
    def _build_model(self, **kwargs) -> Any:
        """Build and return the underlying model object (e.g. sklearn estimator)."""

    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Train the model."""
        logger.info(f"Training {self.__class__.__name__}...")
        self.model.fit(X, y)
        logger.info("Training complete.")

    def predict(self, X: pd.DataFrame) -> Any:
        """Make predictions."""
        return self.model.predict(X)

    def save(self, path: str | Path) -> None:
        """Save model to disk."""
        logger.info(f"Saving model to {path}...")
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, path)
        logger.info("Model saved.")

    @classmethod
    def load(cls, path: str | Path) -> 'MLModel':
        """Load model from disk."""
        logger.info(f"Loading model from {path}...")
        instance = cls.__new__(cls)
        instance.model = joblib.load(path)
        return instance
