"""Structural validation only; never certifies horticultural truth."""
import argparse
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from enrichment.prepare_profile_pilot import ROOT

def validate(payload, names):
    schema = json.loads((ROOT / "schemas/plant-enrichment-v1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(payload)
    actual = [p["scientific_name"] for p in payload["profiles"]]
    if len(actual) != len(names) or set(actual) != set(names):
        raise ValueError("Unexpected or duplicate scientific names")
    warnings = []
    for p in payload["profiles"]:
        for key, trait in p["traits"].items():
            v = trait["value"]
            if v is not None and (not trait["source_urls"] or trait["evidence_status"] != "RETRIEVED"):
                warnings.append(f"{p['scientific_name']}: {key} has unverified evidence")
            if key == "french_nursery_availability" and v in ("IN_STOCK", "OUT_OF_STOCK"):
                warnings.append(f"{p['scientific_name']}: stock claim is optional and unverified")
            if key in ("height_cm", "spread_cm") and v is not None and v[0] > v[1]:
                raise ValueError(f"Reversed range: {key}")
    return {"profiles": len(actual), "status": "STRUCTURE_VALID_PENDING_REVIEW", "warnings": warnings}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input", type=Path)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--count", type=int, default=5)
    a = p.parse_args()
    plants = json.loads((ROOT / "data/plants-mvp-40.json").read_text(encoding="utf-8"))
    if a.offset < 0 or not 1 <= a.count <= 5 or a.offset+a.count > len(plants):
        p.error("Invalid batch")
    names = [x["scientific_name"] for x in plants[a.offset:a.offset+a.count]]
    print(json.dumps(validate(json.loads(a.input.read_text(encoding="utf-8")), names)))

if __name__ == "__main__":
    main()
