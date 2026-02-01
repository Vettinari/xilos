from pydantic import BaseModel

class PredictRequest(BaseModel):
    data: List[Dict[str, Any]]