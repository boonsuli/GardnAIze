"""GardnAIze AI service: lightweight API scaffold."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from app.garden_analysis import analyze_image

from app.recommendations import RecommendationRequest, RecommendationResponse, suggest

VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
requested_level = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = requested_level if requested_level in VALID_LOG_LEVELS else "INFO"

logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("gardnaize.ai")


@asynccontextmanager
async def lifespan(application: FastAPI):
    logger.info("AI service started")
    yield
    logger.info("AI service stopped")


app = FastAPI(
    title="GardnAIze AI Service",
    version="0.1.0",
    description="AI inference service scaffold; recommendation endpoints are planned.",
    lifespan=lifespan,
)


@app.get("/health", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-service"}


@app.get("/", tags=["operations"])
def root() -> dict[str, str]:
    return {
        "service": "GardnAIze AI Service",
        "status": "ready",
        "documentation": "/docs",
    }


@app.post("/recommendations", response_model=RecommendationResponse, tags=["recommendations"])
def recommendations(request: RecommendationRequest) -> RecommendationResponse:
    return suggest(request)


class AnalyzeRequest(BaseModel):
    photoId: str
    mimeType: str
    imageBase64: str = Field(min_length=1)
    requirements: dict = Field(default_factory=dict)


@app.post("/analyze", tags=["vision"])
def analyze(request: AnalyzeRequest) -> dict:
    try:
        return analyze_image(request.imageBase64, request.mimeType)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        logger.warning("Vision analysis failed: %s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="External vision analysis unavailable") from exc
