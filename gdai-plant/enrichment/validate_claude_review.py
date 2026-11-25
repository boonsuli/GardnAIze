"""Validate a review against its exact Gemini input."""
import argparse
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from enrichment.prepare_claude_review import digest
from enrichment.prepare_profile_pilot import ROOT
from enrichment.validate_plant_profiles import validate

def equivalent(key, a, b):
    if isinstance(a, list) and isinstance(b, list) and key not in ("height_cm", "spread_cm"):
        return set(a) == set(b)
    return a == b

def validate_review(payload, review):
    names = [p["scientific_name"] for p in payload["profiles"]]
    validate(payload, names)
    schema = json.loads((ROOT / "schemas/claude-review-v1.schema.json").read_text())
    Draft202012Validator(schema).validate(review)
    if review["input_sha256"] != digest(payload):
        raise ValueError("Review input digest mismatch")
    actual = [p["scientific_name"] for p in review["profiles"]]
    if len(actual) != len(names) or set(actual) != set(names):
        raise ValueError("Unexpected or duplicate reviewed names")
    originals = {p["scientific_name"]: p["traits"] for p in payload["profiles"]}
    counts = dict.fromkeys(("SUPPORTED", "CONTRADICTED", "UNCERTAIN"), 0)
    for p in review["profiles"]:
        for k, t in p["traits"].items():
            v = t["proposed_value"]
            original = originals[p["scientific_name"]][k]["value"]
            if t["verdict"] == "SUPPORTED" and not equivalent(k, original, v):
                raise ValueError(f"Supported value differs: {k}")
            if t["verdict"] == "UNCERTAIN" and v is not None:
                raise ValueError(f"Uncertain value must be null: {k}")
            if k in ("height_cm", "spread_cm") and v is not None and v[0] > v[1]:
                raise ValueError(f"Reversed range: {k}")
            counts[t["verdict"]] += 1
    return {"profiles": len(names), "verdict_counts": counts, "status": "REVIEW_STRUCTURE_VALID"}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gemini", type=Path, required=True)
    p.add_argument("--review", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(validate_review(json.loads(a.gemini.read_text()), json.loads(a.review.read_text())), indent=2))

if __name__ == "__main__":
    main()
