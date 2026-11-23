"""Consolidate the two reviewed pilot batches without Gemini or DB writes.

Preserve originals; record explicit human review decisions; never fabricate
horticultural ground truth. Run: python -m matching.consolidate_garden_scenarios
"""
from __future__ import annotations
import argparse
import json
from collections import Counter
from pathlib import Path
from matching.realistic_scenarios import validate_batch

DEFAULT_DIR = Path(__file__).resolve().parents[1] / "data" / "scenarios"
SOURCES = ("pilot-10-reviewed-v1.3.json", "pilot-20-new-v1.2.json")
# Decision ledger: no silent modification of generated feature values.
DECISIONS = {
    "FR-TEM-001": ("EXCLUDED_NEAR_DUPLICATE", "Very similar to FR-PAR-01: same region, exposure, soil, water, dimensions, evergreen and climate."),
    "FR-TEM-019": ("MANUAL_REVIEW_REQUIRED", "Natural wet depression described as RAIN_GARDEN; confirm intended planting context."),
}
REVIEW_NOTES = {
    "FR-TEM-015": "Retained as a partial-shade variant of FR-IDF-09, with different dimensions.",
    "FR-TEM-003": "Verify whether consistently moist silty soil is compatible with the stated site conditions.",
}
CATEGORICAL = ("sun_exposure", "soil_drainage", "water_availability",
               "evergreen_preferred", "climate_zone", "soil_texture",
               "soil_moisture_seasonality", "planting_context", "terrain_type")

def load_reviews(path: Path):
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict) or not isinstance(obj.get("reviews"), list):
        raise ValueError(f"Invalid reviews source: {path}")
    scenarios = []
    for review in obj["reviews"]:
        if not isinstance(review, dict) or not isinstance(review.get("scenario"), dict):
            raise ValueError(f"Invalid scenario in {path}")
        scenarios.append(dict(review["scenario"]))
    return scenarios

def near_duplicate_pairs(scenarios):
    """Flag only strong similarity; no automatic deletion by numeric score."""
    pairs = []
    for i, left in enumerate(scenarios):
        for right in scenarios[i+1:]:
            matches = sum(left.get(k) == right.get(k) for k in CATEGORICAL)
            height_diff = abs(left["maximum_height_cm"] - right["maximum_height_cm"])
            spread_diff = abs(left["maximum_spread_cm"] - right["maximum_spread_cm"])
            temp_diff = abs(left["minimum_winter_temperature_c"] - right["minimum_winter_temperature_c"])
            if matches >= 8 and height_diff <= 30 and spread_diff <= 30 and temp_diff <= 2:
                pairs.append({"ids": [left["id"], right["id"]],
                              "matching_categorical_features": matches,
                              "height_difference_cm": height_diff,
                              "spread_difference_cm": spread_diff,
                              "winter_temperature_difference_c": temp_diff})
    return pairs

def consolidate(first, second):
    scenarios = first + second
    ids = [s.get("id") for s in scenarios]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate scenario IDs across batches")
    reviews = validate_batch(scenarios)
    records = []
    for review in reviews:
        sid = review.scenario["id"]
        if review.status == "REJECTED":
            decision, note = "REJECTED_BY_VALIDATOR", ", ".join(review.reasons)
        elif sid in DECISIONS:
            decision, note = DECISIONS[sid]
        elif review.status == "REVIEW_REQUIRED":
            decision, note = "MANUAL_REVIEW_REQUIRED", ", ".join(review.reasons)
        else:
            decision, note = "CANDIDATE", REVIEW_NOTES.get(sid, "Passed automatic checks; synthetic and not expert-validated.")
        records.append({"id": sid, "decision": decision, "review_note": note,
                        "validator_status": review.status, "validator_reasons": review.reasons,
                        "scenario": review.scenario})
    pairs = near_duplicate_pairs(scenarios)
    # Only an explicit decision excludes a scenario. All other close pairs are
    # visible for manual review rather than silently collapsed.
    decisions = Counter(r["decision"] for r in records)
    return {
        "schema_version": "1.0", "generator": "OFFLINE_CONSOLIDATION",
        "sources": list(SOURCES), "total_input": len(scenarios),
        "summary": dict(sorted(decisions.items())),
        "near_duplicate_pairs": pairs,
        "records": records,
        "note": "CANDIDATE means automatically valid and provisionally retained, not independent horticultural truth or an RF training label."
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    out = args.out or args.data_dir / "garden-scenarios-consolidated-v1.json"
    inputs = [args.data_dir / name for name in SOURCES]
    if out.resolve() in {p.resolve() for p in inputs}:
        parser.error("Output must not overwrite a source file")
    result = consolidate(*(load_reviews(path) for path in inputs))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"total_input": result["total_input"], "summary": result["summary"],
                      "near_duplicate_pairs": result["near_duplicate_pairs"]}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
