import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from xilos.xtrain.processor import DataProcessor

class ExampleProcessor(DataProcessor):
    """Example concrete implementation of DataProcessor."""
    
    def __init__(self):
        self.pipeline = Pipeline([
            ('imputer', SimpleImputer(strategy='mean')),
            ('scaler', StandardScaler())
        ])
        
    def clean(self, data: pd.DataFrame) -> pd.DataFrame:
        """Basic cleaning: remove duplicates."""
        return data.drop_duplicates()
        
    def feature_engineer(self, data: pd.DataFrame) -> pd.DataFrame:
        """Feature engineering: example numerical features."""
        # This is where custom logic goes. 
        # For this example, we assume all numeric columns are features.
        return data.select_dtypes(include=['number'])

    def fit(self, X, y=None):
        """Fit the internal pipeline."""
        X_clean = self.clean(X)
        X_feat = self.feature_engineer(X_clean)
        self.pipeline.fit(X_feat)
        return self
        
    def transform(self, X):
        """Transform data."""
        X_clean = self.clean(X)
        X_feat = self.feature_engineer(X_clean)
        return pd.DataFrame(self.pipeline.transform(X_feat), columns=X_feat.columns)
