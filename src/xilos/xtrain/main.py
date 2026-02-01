import sys
import pandas as pd
from typing import Type
from sklearn.ensemble import RandomForestClassifier

from xilos.settings import settings, logger
from xilos.xtrain.model import MLModel
from xilos.xtrain.processor import DataProcessor
from xilos.xtrain.processor.example import ExampleProcessor



class RandomForestModel(MLModel):
    """Example concrete model implementation."""
    def _build_model(self, **kwargs):
        # Pass random_seed from kwargs or settings
        seed = kwargs.get("random_state", settings.random_seed)
        return RandomForestClassifier(random_state=seed, **kwargs)

def load_data(path: str) -> pd.DataFrame:
    """Load data from path."""
    logger.info(f"Loading data from {path}...")
    # For template purposes, return dummy data if file doesn't exist
    try:
        return pd.read_csv(path)
    except FileNotFoundError:
        logger.warning(f"File not found: {path}. Generating dummy data.")
        return pd.DataFrame({
            "feature1": [1.0, 2.0, 3.0, 4.0, 5.0],
            "feature2": [5.0, 4.0, 3.0, 2.0, 1.0],
            "target": [0, 0, 1, 1, 0]
        })

def run_training_pipeline(
    processor_class: Type[DataProcessor],
    model_class: Type[MLModel]
):
    """Main training pipeline execution."""
    logger.info(f"Starting training pipeline for {settings.app_name}...")
    
    # 1. Load Data
    df = load_data(settings.train_data_path)
    
    # 2. Split Data (Simplified for template)
    X = df.drop(columns=["target"])
    y = df["target"]
    
    # 3. Process Data
    logger.info("Initializing processor...")
    processor = processor_class()
    processor.fit(X)
    X_processed = processor.transform(X)
    
    # 4. Train Model
    logger.info("Initializing model...")
    model = model_class()
    model.train(X_processed, y)
    
    # 5. Save Artifacts
    model.save(settings.model_output_path)
    logger.info("Pipeline finished successfully.")

def main() -> None:
    """Entry point."""
    try:
        run_training_pipeline(
            processor_class=ExampleProcessor,
            model_class=RandomForestModel
        )
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
