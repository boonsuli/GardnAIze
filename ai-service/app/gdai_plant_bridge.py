"""GDAI-PLANT adapter: receives confirmed garden observations, never raw photos."""
import logging
from typing import Any

from app.recommendations import RecommendationRequest, suggest

logger = logging.getLogger("gardnaize.plant")


def build_plant_context(vision_json: dict[str, Any], confirmed: bool,
                        preferences: dict[str, Any], correlation_id: str) -> dict[str, Any]:
    """Validate the consent gate and prepare observations for the plant pipeline.

    This is an integration boundary, not a trained Random Forest predictor.
    The current rule-based recommender has its own request contract.
    """
    if not confirmed:
        raise ValueError("Explicit user confirmation required")
    if not vision_json.get("isGarden") or not vision_json.get("isUsable"):
        raise ValueError("Image is not a usable garden")
    observations = {
        "gardenElements": vision_json.get("gardenElements", {}),
        "visibleConditions": vision_json.get("visibleConditions", {}),
        "warnings": vision_json.get("warnings", []),
    }
    logger.info("GDAI-PLANT context prepared correlationId=%s preferenceFields=%d",
                correlation_id, len(preferences))
    return {"correlationId": correlation_id, "observations": observations,
            "preferences": preferences, "status": "ready_for_recommendation"}


def recommend_from_context(context: dict[str, Any], request: RecommendationRequest):
    """Invoke existing demonstration recommender; not a trained ML model."""
    logger.info("GDAI-PLANT demo recommendation requested correlationId=%s",
                context["correlationId"])
    return suggest(request)
