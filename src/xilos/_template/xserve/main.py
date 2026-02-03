import gc
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

import pandas as pd
import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger

from xilos._template.registry import registry

from ..xtrain.model import MLModel
from .schemas.predict import PredictRequest


# Define a concrete class for loading models (since MLModel is abstract)
class ServingModel(MLModel):
    def _build_model(self, **kwargs):
        raise NotImplementedError("ServingModel is for loading existing models only.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    logger.info("Lifespan: Loading resources...")

    yield

    logger.info("Lifespan: Cleaning up resources...")
    gc.collect()
    logger.info("Resources cleared.")


app = FastAPI(title="xServe API", lifespan=lifespan)


@app.get("/health")
def health_check(
    request: Request,
    model: MLModel = Depends(registry.get_model),  # noqa: B008
    processor: Any = Depends(registry.get_processor),  # noqa: B008
):
    is_model = model is not None
    is_processor = processor is not None
    status = "ok" if all([is_model, is_processor]) else "error"
    return {"status": status, "model_loaded": is_model, "processor_loaded": is_processor}


@app.post("/predict")
def predict(
    request: PredictRequest,
    model: MLModel = Depends(registry.get_model),  # noqa: B008
    processor: Any = Depends(registry.get_processor),  # noqa: B008
):
    request_id = str(uuid.uuid4())
    start_time = datetime.now(UTC)

    log_payload = {
        "request_id": request_id,
        "timestamp": start_time.isoformat(),
        "input": request.dict(),
        "status": "pending",
        "output": None,
        "error": None,
    }

    try:
        # Inference logic
        df = pd.DataFrame(request.data)
        X_processed = processor.transform(df)
        predictions = model.predict(X_processed)
        result_list = predictions.tolist()

        # Update log
        log_payload["status"] = "success"
        log_payload["output"] = result_list

        return {"request_id": request_id, "predictions": result_list}

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        log_payload["status"] = "failed"
        log_payload["error"] = str(e)

        return JSONResponse(status_code=500, content={"request_id": request_id, "error": str(e)})


def main():
    from ..settings import project_config

    uvicorn.run(
        "xilos.xserve.main:app",
        host=project_config.SERVE_HOST,
        port=project_config.SERVE_PORT,
        reload=True,
    )


if __name__ == "__main__":
    main()
