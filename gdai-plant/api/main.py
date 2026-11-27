"""GDAI-PLANT V1 contract API. No unvalidated horticultural recommendations."""
from typing import Literal
from contextlib import asynccontextmanager
import os
from api.model_registry import Registry
from fastapi import FastAPI
from pydantic import BaseModel, Field

@asynccontextmanager
async def lifespan(app):
    app.state.registry = Registry(os.getenv("GDAI_PLANT_MODEL_REGISTRY"))
    yield

app = FastAPI(title='GDAI-PLANT', version='0.2.0', lifespan=lifespan)
app.state.registry = Registry(None)

class GardenProfile(BaseModel):
    continent: str | None = None
    country: str | None = None
    region: str | None = None
    climate_zone: str | None = None
    maximum_height_cm: float | None = None
    maximum_spread_cm: float | None = None
    soil_texture: str | None = None
    soil_moisture_seasonality: str | None = None
    planting_context: str | None = None
    maintenance_preference: str | None = None
    sun_exposure: Literal['FULL_SUN', 'PARTIAL_SHADE', 'FULL_SHADE'] | None = None
    soil_drainage: str | None = None
    water_availability: Literal['LOW', 'MEDIUM', 'HIGH'] | None = None
    minimum_winter_temperature_c: float | None = None
    evergreen_preferred: bool | None = None
    privacy_screening_required: bool | None = None

class RecommendationRequest(BaseModel):
    request_id: str = Field(min_length=1)
    garden: GardenProfile
    limit: int = Field(default=5, ge=1, le=10)

class PlantResult(BaseModel):
    plant_id: int
    scientific_name: str
    score: float | None = None
    reasons: list[str]
    method: Literal['RULES', 'RANDOM_FOREST']

class RecommendationResponse(BaseModel):
    request_id: str
    status: Literal['COMPLETED', 'INSUFFICIENT_DATA']
    recommendations: list[PlantResult]
    model_version: str | None = None
    warnings: list[str] = Field(default_factory=list)

@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'GDAI-PLANT', 'loaded_models': len(app.state.registry.models)}

@app.get('/v1/models')
def models():
    return [m[1] for m in app.state.registry.models]

@app.post('/v1/recommendations', response_model=RecommendationResponse)
def recommend(req: RecommendationRequest):
    garden = req.garden.model_dump()
    registry = app.state.registry
    bundle = registry.select(garden)
    if bundle is None:
        return RecommendationResponse(request_id=req.request_id, status='INSUFFICIENT_DATA',
            recommendations=[], warnings=['No model for supplied geographic scope'])
    required = ("sun_exposure", "soil_drainage", "water_availability", "minimum_winter_temperature_c")
    if any(garden[k] is None for k in required):
        return RecommendationResponse(request_id=req.request_id, status='INSUFFICIENT_DATA',
            recommendations=[], warnings=['Missing environmental inputs'])
    results = registry.predict(bundle, garden, req.limit)
    return RecommendationResponse(request_id=req.request_id,
        status='COMPLETED' if results else 'INSUFFICIENT_DATA',
        recommendations=results, model_version=bundle[0]["model_id"],
        warnings=['Experimental rule-derived model; independent validation pending'])
