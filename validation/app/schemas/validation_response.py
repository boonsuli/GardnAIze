from typing import Literal
from pydantic import BaseModel, Field

class ModelInfo(BaseModel):
    name: str = "resnet18"
    version: str

class ValidationResponse(BaseModel):
    request_id: str
    valid: bool
    status: Literal["VALID", "INVALID"]
    confidence: float = Field(ge=0, le=1)
    predicted_class: str
    model: ModelInfo
    reason_code: str | None = None
    message: str
