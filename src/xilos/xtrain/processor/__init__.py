import abc
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

class DataProcessor(abc.ABC, BaseEstimator, TransformerMixin):

    @abc.abstractmethod
    def clean(self, data: pd.DataFrame) -> pd.DataFrame:
        """Clean data"""

    @abc.abstractmethod
    def feature_engineer(self, data: pd.DataFrame) -> pd.DataFrame:
        """Feature engineering"""
    
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        return X