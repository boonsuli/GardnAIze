"""Offline, reproducible enrichment of the reviewed 10-scenario pilot.

All added values are reviewer hypotheses, NOT measurements or expert labels.
The Jura mountain scenario is excluded only from the V1 candidate output.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from matching.realistic_scenarios import validate_batch

# Explicit review hypotheses, not a regional climate/soil inference engine.
ENRICHMENT = {
    "FR-PAR-01": ("TEMPERATE_TRANSITIONAL", "LOAM", "WELL_DRAINED", "IN_GROUND_BORDER"),
    "FR-BRE-02": ("TEMPERATE_OCEANIC", "MIXED", "SEASONAL_WET", "HEDGE"),
    "FR-AQU-03": ("TEMPERATE_OCEANIC", "MIXED", "DRY_SUMMER", "IN_GROUND_BORDER"),
    "FR-CTR-04": ("TEMPERATE_TRANSITIONAL", "MIXED", "WELL_DRAINED", "IN_GROUND_BORDER"),
    "FR-EST-05": ("TEMPERATE_SEMI_CONTINENTAL", "SILT", "SEASONAL_WET", "IN_GROUND_BORDER"),
    "FR-NOR-06": ("TEMPERATE_OCEANIC", "MIXED", "WELL_DRAINED", "IN_GROUND_BORDER"),
    "FR-RHO-07": ("TEMPERATE_TRANSITIONAL", "CLAY", "SEASONAL_WET", "COURTYARD"),
    "FR-OCC-08": ("TEMPERATE_TRANSITIONAL", "STONY", "DRY_SUMMER", "IN_GROUND_BORDER"),
    "FR-IDF-09": ("TEMPERATE_TRANSITIONAL", "CLAY", "SEASONAL_WET", "RAIN_GARDEN"),
}
EXCLUDED = {"FR-JUR-10": "OUT_OF_SCOPE_MID_ALTITUDE_MOUNTAIN"}
FIELDS = ("climate_zone", "soil_texture", "soil_moisture_seasonality", "planting_context")

def enrich(data: dict) -> dict:
    source = data.get("reviews")
    if not isinstance(source, list):
        raise ValueError("Expected input with reviews array")
    scenarios = []
    excluded = []
    seen = set()
    for item in source:
        scenario = item.get("scenario") if isinstance(item, dict) else None
        if not isinstance(scenario, dict):
            raise ValueError("Invalid review entry")
        sid = scenario.get("id")
        if sid in seen:
            raise ValueError(f"Duplicate scenario ID: {sid}")
        seen.add(sid)
        if sid in EXCLUDED:
            excluded.append({"id": sid, "reason": EXCLUDED[sid]})
            continue
        if sid not in ENRICHMENT:
            raise ValueError(f"No reviewed enrichment mapping for {sid}")
        enriched = dict(scenario)
        for field, value in zip(FIELDS, ENRICHMENT[sid]):
            enriched[field] = value
        enriched["terrain_type"] = "LOWLAND"
        # This provenance concerns the five enriched fields only.
        enriched["enrichment_provenance"] = "HUMAN_REVIEW_HYPOTHESIS"
        scenarios.append(enriched)
    if seen != set(ENRICHMENT) | set(EXCLUDED):
        raise ValueError(f"Pilot incomplete: missing {sorted((set(ENRICHMENT) | set(EXCLUDED)) - seen)}")
    reviews = validate_batch(scenarios)
    return {
        "schema_version": "1.3",
        "generator": "OFFLINE_ENRICHMENT",
        "source_schema_version": data.get("schema_version"),
        "api_usage": None,
        "requested_count": len(scenarios),
        "excluded": excluded,
        "summary": {status: sum(r.status == status for r in reviews)
                    for status in ("ACCEPTED", "REVIEW_REQUIRED", "REJECTED")},
        "reviews": [r.to_dict() for r in reviews],
        "validation_note": "Automatic checks only; enrichment values are unverified review hypotheses.",
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    source = Path(args.input)
    dest = Path(args.out)
    if source.resolve() == dest.resolve():
        parser.error("Input and output must be different to preserve the source")
    result = enrich(json.loads(source.read_text(encoding="utf-8")))
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"], "excluded": result["excluded"]}))

if __name__ == "__main__":
    main()
