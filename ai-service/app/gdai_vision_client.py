"""GDAI-VISION Gemini image analysis client; no API keys or image bytes in logs."""
import base64
import logging
import os
import time

import httpx

logger = logging.getLogger("gardnaize.vision")
BASE = "https://generativelanguage.googleapis.com/v1beta"
PROMPT = (
    "Analyze the visible garden. Return JSON with isGarden, isUsable, "
    "gardenElements, visibleConditions and warnings. Do not infer soil or climate."
)


def analyze_garden(image: bytes, mime_type: str, correlation_id: str = "") -> dict:
    if mime_type not in ("image/png", "image/jpeg", "image/webp"):
        raise ValueError("Unsupported image type")
    if not image or len(image) > 10 * 1024 * 1024:
        raise ValueError("Image empty or exceeds 10 MB")
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not configured")
    model = os.environ.get("GDAI_GEMINI_MODEL", "gemini-2.5-flash")
    body = {
        "contents": [{"parts": [
            {"inline_data": {"mime_type": mime_type, "data": base64.b64encode(image).decode("ascii")}},
            {"text": PROMPT},
        ]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }
    import json
    with httpx.Client(timeout=90) as client:
        for attempt in range(3):
            started = time.monotonic()
            try:
                response = client.post(
                    f"{BASE}/models/{model}:generateContent",
                    headers={"x-goog-api-key": key},
                    json=body,
                )
            except httpx.RequestError as exc:
                logger.warning("GDAI-VISION transport failure correlationId=%s", correlation_id)
                raise RuntimeError("Gemini transport failure") from exc
            logger.info("GDAI-VISION correlationId=%s model=%s status=%s durationMs=%d",
                        correlation_id, model, response.status_code,
                        int((time.monotonic() - started) * 1000))
            if response.status_code in (500, 502, 503, 504) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            if response.status_code != 200:
                raise RuntimeError(f"Gemini returned HTTP {response.status_code}")
            payload = response.json()
            try:
                analysis = json.loads(payload["candidates"][0]["content"]["parts"][0]["text"])
            except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
                raise RuntimeError("Invalid Gemini response") from exc
            logger.info("GDAI-VISION usage correlationId=%s usage=%s",
                        correlation_id, payload.get("usageMetadata", {}))
            return {"analysis": analysis, "usageMetadata": payload.get("usageMetadata", {})}
    raise RuntimeError("Gemini unavailable")
