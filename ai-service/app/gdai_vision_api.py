"""GDAI-VISION API router. Gemini is called only by GDAI-BACK after consent."""
import base64
import binascii
import logging
import os
import time
import uuid

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger("gardnaize.vision")
router = APIRouter(prefix="/api/v1/vision", tags=["GDAI-VISION"])
_ALLOWED = {"image/png", "image/jpeg", "image/webp"}
_MAX_IMAGE_BYTES = 5 * 1024 * 1024


class VisionRequest(BaseModel):
    photoId: str = Field(min_length=1, max_length=128)
    mimeType: str
    imageBase64: str = Field(min_length=1)
    correlationId: str | None = None


class VisionResponse(BaseModel):
    correlationId: str
    model: str
    analysis: dict
    usageMetadata: dict = Field(default_factory=dict)


@router.post("/analyze", response_model=VisionResponse)
def analyze_garden(request: VisionRequest) -> VisionResponse:
    """Synchronous FastAPI handler; Starlette executes it in a worker thread."""
    correlation_id = request.correlationId or str(uuid.uuid4())
    if request.mimeType not in _ALLOWED:
        raise HTTPException(422, "Unsupported image MIME type")
    try:
        raw = base64.b64decode(request.imageBase64, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise HTTPException(422, "Invalid image encoding") from exc
    if not raw or len(raw) > _MAX_IMAGE_BYTES:
        raise HTTPException(413, "Image empty or exceeds 5 MB")
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        logger.error("GDAI-VISION missing Gemini key correlationId=%s", correlation_id)
        raise HTTPException(503, "Gemini is not configured")
    model = os.getenv("GDAI_GEMINI_MODEL", "gemini-2.5-flash")
    prompt = (
        "Analyze visible garden features only. Return JSON with isGarden, isUsable, "
        "gardenElements, visibleConditions, warnings. Do not infer soil or climate."
    )
    body = {"contents": [{"parts": [
        {"inline_data": {"mime_type": request.mimeType, "data": request.imageBase64}},
        {"text": prompt}
    ]}], "generationConfig": {"responseMimeType": "application/json"}}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    started = time.monotonic()
    try:
        with httpx.Client(timeout=60) as client:
            for attempt in range(3):
                response = client.post(url, headers={"x-goog-api-key": key}, json=body)
                logger.info("GDAI-VISION correlationId=%s attempt=%d status=%d",
                            correlation_id, attempt + 1, response.status_code)
                if response.status_code in (500, 502, 503, 504) and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                if response.status_code != 200:
                    raise HTTPException(503, f"Gemini returned HTTP {response.status_code}")
                payload = response.json()
                import json
                analysis = json.loads(payload["candidates"][0]["content"]["parts"][0]["text"])
                if not isinstance(analysis, dict):
                    raise ValueError("Expected JSON object")
                logger.info("GDAI-VISION completed correlationId=%s durationMs=%d",
                            correlation_id, int((time.monotonic() - started) * 1000))
                return VisionResponse(correlationId=correlation_id, model=model,
                                      analysis=analysis, usageMetadata=payload.get("usageMetadata", {}))
    except (httpx.RequestError, KeyError, IndexError, ValueError) as exc:
        logger.warning("GDAI-VISION failed correlationId=%s type=%s",
                       correlation_id, type(exc).__name__)
        raise HTTPException(503, "Gemini analysis unavailable") from exc
    raise HTTPException(503, "Gemini analysis unavailable")
