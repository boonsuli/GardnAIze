"""GardnAIze AI service: lightweight API scaffold."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

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
