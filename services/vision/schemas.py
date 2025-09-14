"""Vision service schemas"""
from pydantic import BaseModel
from typing import Dict

class VisionResult(BaseModel):
    tokens: Dict[str, float]
    confidence: float
