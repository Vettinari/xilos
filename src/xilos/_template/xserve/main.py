import gc
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List

import pandas as pd
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from xilos.settings import logger
from xilos.xserve.utils import get_model, get_processor, save_log
from xilos.xtrain.model import MLModel


# Define a concrete class for loading models (since MLModel is abstract)
class ServingModel(MLModel):
    def _build_model(self, **kwargs):
        raise NotImplementedError("ServingModel is for loading existing models only.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    logger.info("Lifespan: Loading resources...")

    yield

    # --- Shutdown ---
    logger.info("Lifespan: Cleaning up resources...")

    gc.collect()

    logger.info("Resources cleared.")


app = FastAPI(title="xServe API", lifespan=lifespan)


class PredictRequest(BaseModel):
    data: List[Dict[str, Any]]


@app.get("/health")
def health_check(request: Request):
    model = getattr(request.app.state, "model", None)
    return {"status": "ok", "model_loaded": model is not None}


@app.post("/predict")
def predict(
        request: PredictRequest,
        background_tasks: BackgroundTasks,
        model: MLModel = Depends(get_model),
        processor: Any = Depends(get_processor)
):
    request_id = str(uuid.uuid4())
    start_time = datetime.now(timezone.utc)

    log_payload = {
        "request_id": request_id,
        "timestamp": start_time.isoformat(),
        "input": request.dict(),
        "status": "pending",
        "output": None,
        "error": None
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
        background_tasks.add_task(save_log, log_payload)

        return {"request_id": request_id, "predictions": result_list}

    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        log_payload["status"] = "failed"
        log_payload["error"] = str(e)
        background_tasks.add_task(save_log, log_payload)

        return JSONResponse(
            status_code=500,
            content={"request_id": request_id, "error": str(e)}
        )


def main():
    uvicorn.run("xilos.xserve.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
