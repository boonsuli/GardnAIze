"""Gemini external vision adapter with versioned, conservative observations.

No climate/soil inference from pixels; these are verified later from the questionnaire.
"""
import base64
import json
import os
from urllib import error, request

SCHEMA_VERSION = "1.0"
MAX_IMAGE_BYTES = 10 * 1024 * 1024
SUPPORTED_MIME = {"image/jpeg", "image/png"}

SYSTEM_PROMPT = """Analyze the attached photograph for GardnAIze.
Return JSON only. Describe visible garden evidence, not inferred geography.
A photo cannot establish a climate zone, exact soil type, actual dimensions,
or sun hours per day. Use climateCode UNKNOWN. Do not recommend plants.
Mark isGarden false for unrelated scenes, and isAnalyzable false when
blurred, too dark, occluded, or without identifiable plantable areas.
Use uppercase controlled vocabulary for categorical observations.
Only include what is visible; uncertainty should be explicit.
Return:
{
 "schemaVersion":"1.0", "isGarden":true, "isAnalyzable":true,
 "climateCode":"UNKNOWN",
 "description":{
  "summary":"...",
  "spaceType":"PRIVATE_GARDEN|COURTYARD|BALCONY|TERRACE|OTHER|UNKNOWN",
  "surfaces":["LAWN","SOIL","PAVING","GRAVEL","CONCRETE"],
  "visibleVegetation":["TREE","SHRUB","HEDGE","GRASS","FLOWER"],
  "shadeLevel":"SUNNY|PARTIAL|SHADED|UNKNOWN",
  "privacyExposure":"LOW|MODERATE|HIGH|UNKNOWN",
  "plantableAreasDetected":true,
  "limitations":["..."]
 }
}"""

def analyze_image(image_base64: str, mime_type: str) -> dict:
    if mime_type not in SUPPORTED_MIME:
        raise ValueError("Unsupported image MIME type")
    try:
        image = base64.b64decode(image_base64, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError("Invalid base64 photo") from exc
    if not image or len(image) > MAX_IMAGE_BYTES:
        raise ValueError("Image size outside MVP limits")

    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    payload = {
        "contents": [{"parts": [
            {"text": SYSTEM_PROMPT},
            {"inline_data": {"mime_type": mime_type, "data": image_base64}},
        ]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0},
    }
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    req = request.Request(endpoint, data=json.dumps(payload).encode("utf-8"),
                          headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
                          method="POST")
    try:
        with request.urlopen(req, timeout=25) as response:
            provider_json = json.load(response)
    except error.HTTPError as exc:
        # Do not expose provider response bodies, which can contain sensitive details.
        raise RuntimeError(f"Gemini HTTP error {exc.code}") from exc
    except (error.URLError, TimeoutError) as exc:
        raise RuntimeError("Gemini is unreachable") from exc
    try:
        text = provider_json["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(text)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise RuntimeError("Gemini returned invalid JSON") from exc
    if not isinstance(parsed, dict) or not isinstance(parsed.get("description"), dict):
        raise RuntimeError("Gemini JSON contract mismatch")
    if not isinstance(parsed.get("isGarden"), bool) or not isinstance(parsed.get("isAnalyzable"), bool):
        raise RuntimeError("Gemini garden flags missing")
    # Climate cannot be verified from image alone; never trust model speculation.
    parsed["climateCode"] = "UNKNOWN"
    parsed["schemaVersion"] = SCHEMA_VERSION
    return parsed
