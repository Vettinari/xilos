from typing import Any

from pydantic import BaseModel


class PredictRequest(BaseModel):
    data: list[dict[str, Any]]
