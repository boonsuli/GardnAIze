import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.v1.validation_controller import router
from app.services.validation_service import classifier

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        classifier.load()
    except (ValueError, RuntimeError, KeyError) as exc:
        logger.error("Model loading failed: %s", type(exc).__name__)
    yield

app = FastAPI(title="GardnAIze GDAI-VALID", version="0.1.0",
              description="Garden image validation using a separately trained ResNet-18.",
              lifespan=lifespan)
app.include_router(router)
