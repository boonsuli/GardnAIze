"""GDAI-PLANT V1 contract API. No unvalidated horticultural recommendations."""
from typing import Literal
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title='GDAI-PLANT', version='0.1.0')

class GardenProfile(BaseModel):
    sun_exposure: Literal['FULL_SUN', 'PARTIAL_SHADE', 'FULL_SHADE'] | None = None
    soil_drainage: str | None = None
    water_availability: Literal['LOW', 'MEDIUM', 'HIGH'] | None = None
    minimum_winter_temperature_c: float | None = None
    evergreen_preferred: bool | None = None
    privacy_screening_required: bool | None = None

class RecommendationRequest(BaseModel):
    request_id: str = Field(min_length=1)
    garden: GardenProfile
    limit: int = Field(default=5, ge=1, le=5)

class PlantResult(BaseModel):
    plant_id: int
    scientific_name: str
    reasons: list[str]
    method: Literal['RULES', 'RANDOM_FOREST']

class RecommendationResponse(BaseModel):
    request_id: str
    status: Literal['COMPLETED', 'INSUFFICIENT_DATA']
    recommendations: list[PlantResult]
    model_version: str | None = None
    warnings: list[str] = []

@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'GDAI-PLANT'}

@app.post('/v1/recommendations', response_model=RecommendationResponse)
def recommend(req: RecommendationRequest):
    """Strict fallback: only VALIDATED plants with supported suitability evidence.

    Until the curated catalog exists, return INSUFFICIENT_DATA rather than fabricate
    five recommendations. A production scorer must evaluate sun/soil/water/hardiness.
    """
    return RecommendationResponse(
        request_id=req.request_id,
        status='INSUFFICIENT_DATA',
        recommendations=[],
        warnings=['No validated suitability scorer is configured; no recommendations invented.'],
    )
