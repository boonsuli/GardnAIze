"""Offline candidate enumeration; no horticultural labels are inferred."""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ("sun_exposure", "soil_drainage", "water_availability",
          "minimum_winter_temperature_c", "maximum_height_cm",
          "maximum_spread_cm", "evergreen_preferred", "climate_zone",
          "soil_texture", "soil_moisture_seasonality", "planting_context",
          "terrain_type")

def build(gardens, plants):
    for rows, key, expected in ((gardens, "id", 50), (plants, "scientific_name", 40)):
        ids = [r[key] for r in rows]
        if len(ids) != expected or len(set(ids)) != expected or any(
            not isinstance(i, str) or not i.strip() or i != i.strip() for i in ids
        ):
            raise ValueError(f"Expected {expected} unique nonblank {key} values")
    return [
        {"garden_id": g["id"], "scientific_name": p["scientific_name"],
         **{"garden_" + f: g[f] for f in FIELDS},
         "garden_origin": g["origin"], "plant_category": p["candidate_category"],
         "relevance_grade": None, "label_source": None,
         "assessment_status": "PENDING"}
        for g in gardens for p in plants
    ]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "data/matching")
    args = parser.parse_args()
    gardens = json.loads((ROOT / "data/scenarios/garden-scenarios-final-v2.json").read_text(encoding="utf-8"))["scenarios"]
    plants = json.loads((ROOT / "data/plants-mvp-40.json").read_text(encoding="utf-8"))
    rows = build(gardens, plants)
    report = {"garden_count": len(gardens), "plant_count": len(plants),
              "expected_pairs": len(gardens)*len(plants), "generated_pairs": len(rows),
              "duplicate_pairs": len(rows)-len({(r["garden_id"], r["scientific_name"]) for r in rows}),
              "labelled_pairs": 0, "pending_pairs": len(rows), "api_calls": 0,
              "training_eligible_pairs": 0}
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for name, obj in (("garden-plant-pairs-v1.json", rows), ("garden-plant-quality-report-v1.json", report)):
        (args.out_dir / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    with (args.out_dir / "garden-plant-pairs-v1.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
