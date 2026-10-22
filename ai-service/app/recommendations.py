"""Explicitly non-ML demo recommendations until botanical datasets are integrated."""

from pydantic import BaseModel, Field


class RecommendationRequest(BaseModel):
    location: str = Field(min_length=1, max_length=160)
    exposure: str
    soilType: str


class PlantSuggestion(BaseModel):
    name: str
    reason: str


class RecommendationResponse(BaseModel):
    mode: str
    plants: list[PlantSuggestion]


def suggest(request: RecommendationRequest) -> RecommendationResponse:
    if request.exposure == "FULL_SUN":
        plants = [
            PlantSuggestion(name="Lavandula angustifolia", reason="Sun-loving; requires drainage."),
            PlantSuggestion(name="Cistus × purpureus", reason="Drought-tolerant once established."),
            PlantSuggestion(name="Salvia greggii", reason="Flowers in sunny, well-drained areas."),
        ]
    else:
        plants = [
            PlantSuggestion(name="Sarcococca confusa", reason="Evergreen for shade."),
            PlantSuggestion(name="Fatsia japonica", reason="Tolerates partial shade; needs water."),
            PlantSuggestion(name="Liriope muscari", reason="Groundcover for partial shade."),
        ]

    return RecommendationResponse(mode="demo-rules-not-ai", plants=plants)
