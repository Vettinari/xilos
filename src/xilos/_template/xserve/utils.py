from typing import Any

from fastapi import Request
from loguru import logger

from ..xtrain.model import MLModel
from ..xtrain.processor.example import ExampleProcessor


# Dependencies
def get_model(request: Request) -> MLModel:
    import os
    if os.path.exists(settings.model_output_path):
        model = ServingModel.load(settings.model_output_path)
        logger.info(f"Model loaded from {settings.model_output_path}")

        yield model

        del model

    else:
        logger.warning(f"Model file not found at {settings.model_output_path}. Predictions will fail.")


def get_processor(request: Request) -> Any:
    try:
        processor = ExampleProcessor()
        logger.info("Processor initialized.")
        yield processor
        del processor

    except Exception as e:
        logger.error(f"Failed to initialize processor: {e}")
