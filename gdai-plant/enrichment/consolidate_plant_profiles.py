"""Conservative provisional consensus, never expert validation."""
import argparse
import json
from pathlib import Path
from enrichment.validate_claude_review import validate_review
from enrichment.prepare_claude_review import digest
from enrichment.validate_plant_profiles import validate

from enrichment.assess_plant_quality import major, SETS

def arbitrate(key, a, b, verdict):
    if key == "french_nursery_availability":
        if verdict != "UNCERTAIN" and a in ("LISTED", "IN_STOCK", "OUT_OF_STOCK") and b in ("LISTED", "IN_STOCK", "OUT_OF_STOCK"):
            return "LISTED", "PROVISIONAL_CATALOGUE"
        return None, "UNRESOLVED"
    if verdict == "SUPPORTED" and a is not None:
        return a, "PROVISIONAL_CONSENSUS"
    if verdict != "CONTRADICTED" or a is None or b is None:
        return None, "UNRESOLVED"
    if major(key, a, b):
        return None, "MAJOR_DIVERGENCE"
    levels = ("LOW", "MEDIUM", "HIGH")
    if key == "water_need":
        return max((a,b), key=levels.index), "PRUDENT_WATER"
    if key in ("heat_tolerance", "drought_tolerance"):
        return min((a,b), key=levels.index), "PRUDENT_TOLERANCE"
    if key == "hardiness_min_c":
        return max(a,b), "PRUDENT_FROST"
    if key in ("height_cm", "spread_cm"):
        return [min(a[0],b[0]), max(a[1],b[1])], "DIMENSION_ENVELOPE"
    if key in SETS or key in ("flower_color", "flowering_months"):
        common = sorted(set(a).intersection(b))
        return (common, "COMMON_VALUES") if common else (None, "UNRESOLVED")
    return None, "UNRESOLVED"

def consolidate(payload, review, policy="v2"):
    report = validate_review(payload, review)
    reviewed = {p["scientific_name"]: p["traits"] for p in review["profiles"]}
    profiles, decisions = [], []
    for p in payload["profiles"]:
        name = p["scientific_name"]
        traits = {}
        for k, original in p["traits"].items():
            r = reviewed[name][k]
            v = original["value"]
            if policy == "v2":
                v, decision = arbitrate(k, v, r["proposed_value"], r["verdict"])
            elif r["verdict"] == "SUPPORTED" and v is not None:
                decision = "PROVISIONAL_CONSENSUS"
                if k == "french_nursery_availability" and v in ("IN_STOCK", "OUT_OF_STOCK"):
                    v = "LISTED"
            else:
                v = None
                decision = "UNRESOLVED"
            traits[k] = {"value": v, "source_urls": sorted(set(original["source_urls"] + r["source_urls"])),
                         "notes": "Gemini: " + original["notes"] + " | Claude: " + r["justification"],
                         "evidence_status": "SUGGESTED" if v is not None else "UNKNOWN"}
            decisions.append({"scientific_name": name, "trait": k, "decision": decision,
                              "gemini_value": original["value"], "claude_value": r["proposed_value"],
                              "retained_value": v})
        profiles.append({"scientific_name": name, "traits": traits})
    result = {"profiles": profiles}
    validate(result, [p["scientific_name"] for p in profiles])
    return result, {"status": "PROVISIONAL_NOT_EXPERT_VALIDATED", "policy": policy, "input_sha256": digest(payload),
                    "review_sha256": digest(review), "review_report": report, "decisions": decisions,
                    "retained_traits": sum(d["retained_value"] is not None for d in decisions)}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gemini", type=Path, required=True)
    p.add_argument("--review", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--policy", choices=("v1", "v2"), default="v2")
    a = p.parse_args()
    result, report = consolidate(json.loads(a.gemini.read_text()), json.loads(a.review.read_text()), a.policy)
    a.out_dir.mkdir(parents=True, exist_ok=False)
    for name, data in (("profiles-provisional.json", result), ("consolidation.json", report)):
        (a.out_dir / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "decisions"}))

if __name__ == "__main__":
    main()
