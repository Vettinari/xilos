import abc

import pandas as pd
from sklearn.base import TransformerMixin


class DataProcessor(abc.ABC, TransformerMixin):

    @abc.abstractmethod
    def clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean data"""

    @abc.abstractmethod
    def feature_engineer(self, data: pd.DataFrame) -> pd.DataFrame:
        """Feature engineering"""

    @abc.abstractmethod
    def fit(self, X, y=None):
        """Fit the processor to the data"""

    @abc.abstractmethod
    def transform(self, X):
        """Transform the data"""
