"""Validate Gemini-proposed garden scenarios before any ML labelling.

No API calls, database writes or claims of real-world observations.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any
import json

EXPOSURES = {"FULL_SUN", "PARTIAL_SHADE", "FULL_SHADE"}
DRAINAGE = {"POOR", "MODERATE", "GOOD"}
WATER = {"LOW", "MEDIUM", "HIGH"}
ORIGINS = {"SYNTHETIC_AI", "OBSERVED", "DOCUMENTED"}
CLIMATE_ZONES = {"TEMPERATE_OCEANIC", "TEMPERATE_SEMI_CONTINENTAL", "TEMPERATE_TRANSITIONAL"}
SOIL_TEXTURES = {"CLAY", "LOAM", "SAND", "SILT", "STONY", "MIXED"}
MOISTURE = {"DRY_SUMMER", "SEASONAL_WET", "CONSISTENTLY_MOIST", "WELL_DRAINED"}
CONTEXTS = {"IN_GROUND_BORDER", "HEDGE", "COURTYARD", "RAISED_BED", "PLANTER", "RAIN_GARDEN"}

FIELDS = ("sun_exposure", "soil_drainage", "water_availability",
          "minimum_winter_temperature_c", "maximum_height_cm",
          "maximum_spread_cm", "evergreen_preferred", "climate_zone", "soil_texture", "soil_moisture_seasonality", "planting_context", "terrain_type")

@dataclass
class Review:
    status: str
    reasons: list[str]
    scenario: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

def validate(scenario: dict[str, Any]) -> Review:
    """Reject contradictions; quarantine unsupported/ambiguous cases."""
    errors, review = [], []
    if not isinstance(scenario, dict):
        return Review("REJECTED", ["NOT_AN_OBJECT"], {})
    sid = scenario.get("id")
    if not isinstance(sid, str) or not sid.strip():
        errors.append("MISSING_ID")
    for field, allowed in (("sun_exposure", EXPOSURES),
                           ("soil_drainage", DRAINAGE),
                           ("water_availability", WATER)):
        if scenario.get(field) not in allowed:
            errors.append(f"INVALID_{field.upper()}")
    for field in ("minimum_winter_temperature_c", "maximum_height_cm", "maximum_spread_cm"):
        value = scenario.get(field)
        if value is None or isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append(f"INVALID_{field.upper()}")
        elif field == "minimum_winter_temperature_c" and not -40 <= value <= 20:
            review.append("EXTREME_WINTER_TEMPERATURE")
        elif field != "minimum_winter_temperature_c" and not 20 <= value <= 5000:
            errors.append(f"OUT_OF_RANGE_{field.upper()}")
    if not isinstance(scenario.get("evergreen_preferred"), bool):
        errors.append("INVALID_EVERGREEN_PREFERRED")
    if scenario.get("origin") not in ORIGINS:
        errors.append("INVALID_ORIGIN")
    if scenario.get("origin") == "OBSERVED" and not scenario.get("observation_ref"):
        errors.append("OBSERVATION_REFERENCE_REQUIRED")
    if scenario.get("origin") == "DOCUMENTED" and not scenario.get("source_ref"):
        errors.append("SOURCE_REFERENCE_REQUIRED")
    if not isinstance(scenario.get("plausibility_reason"), str) or not scenario.get("plausibility_reason", "").strip():
        review.append("PLAUSIBILITY_EXPLANATION_MISSING")
    # An exposure describes one zone, not a whole multi-zone garden.
    if scenario.get("sun_exposure") == "FULL_SHADE" and scenario.get("direct_sun_hours", 0) >= 6:
        errors.append("SHADE_SUN_CONTRADICTION")
    if "direct_sun_hours" in scenario:
        h = scenario["direct_sun_hours"]
        if isinstance(h, bool) or not isinstance(h, (int, float)) or not 0 <= h <= 24:
            errors.append("INVALID_SUN_HOURS")
        elif scenario.get("sun_exposure") == "FULL_SUN" and h < 4:
            review.append("SUN_EXPOSURE_HOURS_MISMATCH")
    # Missing metadata on legacy records is reviewable, not silently accepted.
    for field, allowed in (
        ("climate_zone", CLIMATE_ZONES),
        ("soil_texture", SOIL_TEXTURES),
        ("soil_moisture_seasonality", MOISTURE),
        ("planting_context", CONTEXTS),
    ):
        if field not in scenario:
            review.append(f"MISSING_{field.upper()}")
        elif scenario[field] not in allowed:
            if field == "climate_zone" and scenario[field] in {"MEDITERRANEAN", "ALPINE", "MOUNTAIN"}:
                errors.append("OUT_OF_SCOPE_CLIMATE")
            else:
                review.append(f"UNRECOGNIZED_{field.upper()}")
    terrain = scenario.get("terrain_type")
    if terrain is None:
        review.append("MISSING_TERRAIN_TYPE")
    elif terrain in {"MOUNTAIN", "HIGH_ALTITUDE"}:
        errors.append("OUT_OF_SCOPE_MOUNTAIN_TERRAIN")
    elif terrain != "LOWLAND":
        review.append("UNRECOGNIZED_TERRAIN_TYPE")
    if scenario.get("soil_moisture_seasonality") == "CONSISTENTLY_MOIST" and scenario.get("water_availability") == "LOW":
        review.append("MOISTURE_WATER_AVAILABILITY_MISMATCH")
    if scenario.get("planting_context") == "PLANTER" and isinstance(scenario.get("maximum_spread_cm"), (int, float)) and scenario["maximum_spread_cm"] > 300:
        review.append("PLANTER_SPREAD_REVIEW")
    desc = (str(scenario.get("plausibility_reason", "")) + " " + str(scenario.get("region", ""))).lower()
    if any(term in desc for term in ("mid-altitude", "high-altitude", "mountain valley", "vallée jurassienne", "alpine valley")):
        review.append("POSSIBLE_MOUNTAIN_CONTEXT")
    # Climate and soil combinations are not rejected solely for being unusual.
    return Review("REJECTED" if errors else "REVIEW_REQUIRED" if review else "ACCEPTED",
                  errors + review, scenario)

def fingerprint(scenario: dict[str, Any]) -> str:
    """Exact normalized features; near-duplicates need separate review."""
    return json.dumps({k: scenario.get(k) for k in FIELDS}, sort_keys=True)

def validate_batch(scenarios: list[dict[str, Any]]) -> list[Review]:
    seen_ids, seen_profiles = set(), set()
    output = []
    for scenario in scenarios:
        result = validate(scenario)
        sid = scenario.get("id") if isinstance(scenario, dict) else None
        if sid in seen_ids:
            result.status = "REJECTED"
            result.reasons.append("DUPLICATE_ID")
        seen_ids.add(sid)
        if result.status != "REJECTED":
            key = fingerprint(scenario)
            if key in seen_profiles:
                result.status = "REVIEW_REQUIRED"
                result.reasons.append("DUPLICATE_FEATURE_PROFILE")
            seen_profiles.add(key)
        output.append(result)
    return output
