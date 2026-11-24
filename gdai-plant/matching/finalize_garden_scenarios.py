"""Build a deterministic 50-scenario MVP selection, offline.

Inputs remain immutable. Selection is not horticultural ground truth.
Run: python -m matching.finalize_garden_scenarios
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from matching.consolidate_garden_scenarios import near_duplicate_pairs
from matching.realistic_scenarios import validate_batch

DATA_DIR = Path(__file__).resolve().parents[1] / "data" / "scenarios"
BASE = "garden-scenarios-consolidated-v1.json"
NEW = "pilot-24-targeted-v1.2.json"
OUTPUT = "garden-scenarios-final-v2.json"

# Explicit, reviewable MVP selection. No fabricated changes to original values.
EXCLUSIONS = {
    "FR-TEM-001": "Near-duplicate of FR-PAR-01, excluded in v1.",
    "FR-TEM-019": "RAIN_GARDEN label for a natural wet depression remains unresolved; hold outside MVP.",
    "FR-TEM-021": "Strongly similar to FR-PAR-01; conservative exclusion for a distinct-profile MVP.",
}
RETAINED_VARIANTS = {
    frozenset(("FR-TEM-009", "FR-TEM-012")):
        "Distinct drainage (MODERATE vs GOOD), geographic setting and planting descriptions; retained as variants.",
    frozenset(("FR-IDF-09", "FR-TEM-015")):
        "Distinct exposure and spatial constraints for a wet clay swale; retained as variants.",
}

def finalize(base: dict, new: dict, target: int = 50) -> dict:
    if not isinstance(base.get("records"), list) or not isinstance(new.get("reviews"), list):
        raise ValueError("Expected consolidated-v1 records and new batch reviews")
    old = [r["scenario"] for r in base["records"]]
    fresh = [r["scenario"] for r in new["reviews"]]
    all_scenarios = old + fresh
    ids = [s["id"] for s in all_scenarios]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate IDs across sources")
    if len(all_scenarios) != 53:
        raise ValueError(f"Expected 53 raw scenarios, got {len(all_scenarios)}")
    if not set(EXCLUSIONS).issubset(ids):
        raise ValueError("Exclusion ID absent from inputs")
    checked = validate_batch(all_scenarios)
    invalid = [(r.scenario.get("id"), r.reasons) for r in checked if r.status != "ACCEPTED"]
    if invalid:
        raise ValueError(f"Unresolved schema validation: {invalid}")
    selected = [s for s in all_scenarios if s["id"] not in EXCLUSIONS]
    if len(selected) != target:
        raise ValueError(f"Expected exactly {target} selected scenarios, got {len(selected)}")
    pairs = near_duplicate_pairs(selected)
    unexplained = [p for p in pairs if frozenset(p["ids"]) not in RETAINED_VARIANTS]
    if unexplained:
        raise ValueError(f"Unreviewed near-duplicate pairs: {unexplained}")
    return {
        "schema_version": "2.0",
        "generator": "OFFLINE_FINAL_SELECTION",
        "source_files": [BASE, NEW],
        "summary": {"raw": len(all_scenarios), "selected": len(selected),
                    "excluded": len(EXCLUSIONS), "validation_accepted": len(selected)},
        "selection_policy": "Deterministic MVP selection; synthetic hypotheses, not expert-validated observations or garden-plant compatibility labels.",
        "excluded": [{"id": sid, "reason": reason} for sid, reason in EXCLUSIONS.items()],
        "reviewed_near_duplicate_pairs": [
            {"ids": p["ids"], "rationale": RETAINED_VARIANTS[frozenset(p["ids"])]}
            for p in pairs
        ],
        "scenarios": selected,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    out = args.out or args.data_dir / OUTPUT
    sources = [args.data_dir / BASE, args.data_dir / NEW]
    if out.resolve() in {s.resolve() for s in sources}:
        parser.error("Output cannot overwrite an input")
    result = finalize(*(json.loads(p.read_text(encoding="utf-8")) for p in sources))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"summary": result["summary"],
                      "excluded": result["excluded"],
                      "reviewed_near_duplicate_pairs": result["reviewed_near_duplicate_pairs"]},
                     indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
