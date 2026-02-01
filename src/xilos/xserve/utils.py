import json
from datetime import datetime
from typing import Any, Dict

import pandas as pd
from fastapi import HTTPException, Depends, Request
from pydantic import BaseModel

from xilos.settings import settings, logger
from xilos.xstore import get_saver
from xilos.xtrain.model import MLModel
from xilos.xtrain.processor.example import ExampleProcessor


def save_log(log_payload: Dict[str, Any]):
    """Background task to save logs to cloud storage."""
    try:
        saver = get_saver()
        destination = settings.log_destination

        if settings.cloud_storage in ["bigquery"]:
            df = pd.DataFrame([log_payload])
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
            saver.save(df, destination)

        elif settings.cloud_storage in ["dynamodb", "cosmos"]:
            payload = log_payload.copy()
            if settings.cloud_storage == "cosmos":
                payload["id"] = payload["request_id"]
            saver.save(payload, destination)

        else:
            ts = datetime.fromisoformat(log_payload["timestamp"])
            path = f"{destination}/{ts.year}/{ts.month:02d}/{ts.day:02d}/{log_payload['request_id']}.json"
            saver.save(json.dumps(log_payload), path)

    except Exception as e:
        logger.error(f"Failed to save log: {e}")


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
