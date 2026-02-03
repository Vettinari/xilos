import sys

from loguru import logger
from sklearn.model_selection import train_test_split

from ..config import project_config
from ..xcore.xmodel import XModel
from ..xcore.xprocessor import DataProcessor
from ..xcore.xstore import DataStorage, DataTable
from .model import MLModel
from .processor.processor import ExampleProcessor


def run_training_pipeline(
    data_storage: DataStorage,
    data_table: DataTable,
    processor: DataProcessor,
    model: XModel,
):
    """Main training pipeline execution."""
    logger.info(f"Starting training pipeline for {project_config}...")

    # 1. Load data
    df = data_storage.download_dataframe(
        cloud_path=project_config.cloud_path,
        save_path=None,
    )

    df = processor.clean_data(df)
    df = processor.fit(df)
    df = processor.transform(df)
    df = processor.feature_engineer(df)

    # 2. Split data
    X = df.drop(columns=["target"])
    y = df["target"]
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=project_config.RANDOM_SEED,
    )

    # 3. Train model
    logger.info("Initializing model...")
    model.train(X_train, y_train)

    # 4. Save Artifacts
    model.save(project_config.model_output_path)
    logger.info("Pipeline finished successfully.")


def main() -> None:
    """Entry point."""
    try:
        run_training_pipeline(
            processor=ExampleProcessor(),
            model=MLModel(),
            # In a real scenario, storage/table should be passed here too or injected
            data_storage=None,  # Placeholder or mock if not available in template main
            data_table=None,
        )
    except Exception as e:
        logger.error(f"Training pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
