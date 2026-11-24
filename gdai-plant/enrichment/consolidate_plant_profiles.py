"""Conservative provisional consensus, never expert validation."""
import argparse
import json
from pathlib import Path
from enrichment.validate_claude_review import validate_review
from enrichment.prepare_claude_review import digest
from enrichment.validate_plant_profiles import validate

def consolidate(payload, review):
    report = validate_review(payload, review)
    reviewed = {p["scientific_name"]: p["traits"] for p in review["profiles"]}
    profiles, decisions = [], []
    for p in payload["profiles"]:
        name = p["scientific_name"]
        traits = {}
        for k, original in p["traits"].items():
            r = reviewed[name][k]
            v = original["value"]
            if r["verdict"] == "SUPPORTED" and v is not None:
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
    return result, {"status": "PROVISIONAL_NOT_EXPERT_VALIDATED", "input_sha256": digest(payload),
                    "review_sha256": digest(review), "review_report": report, "decisions": decisions,
                    "retained_traits": sum(d["retained_value"] is not None for d in decisions)}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gemini", type=Path, required=True)
    p.add_argument("--review", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    a = p.parse_args()
    result, report = consolidate(json.loads(a.gemini.read_text()), json.loads(a.review.read_text()))
    a.out_dir.mkdir(parents=True, exist_ok=False)
    for name, data in (("profiles-provisional.json", result), ("consolidation.json", report)):
        (a.out_dir / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "decisions"}))

if __name__ == "__main__":
    main()
