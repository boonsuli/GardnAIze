"""Offline batch qualification; preserve per-batch review hashes."""
import json
from pathlib import Path
from collections import Counter
from enrichment.consolidate_plant_profiles import consolidate
from enrichment.assess_plant_quality import assess
from enrichment.prepare_claude_review import digest
from enrichment.validate_plant_profiles import validate

def qualify(catalogue, batches):
    names = [p["scientific_name"] for p in catalogue]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate catalogue names")
    profiles, quality, provenance = [], [], []
    seen = set()
    for expected, payload, review in batches:
        validate(payload, expected)
        if not set(expected) <= set(names) or seen.intersection(expected):
            raise ValueError("Unexpected or duplicate batch taxa")
        consolidated, report = consolidate(payload, review, policy="v2")
        assessment = assess(payload, review, consolidated, policy="v2")
        profiles.extend(consolidated["profiles"])
        quality.extend(assessment["plants"])
        seen.update(expected)
        provenance.append({"names":expected,"input_sha256":digest(payload),"review_sha256":digest(review)})
    return {"profiles":profiles}, {"policy":"PROVISIONAL_V2","plants":quality}, {
        "status":"PROVISIONAL_NOT_EXPERT_VALIDATED",
        "catalogue_sha256":digest(catalogue),
        "expected":len(names),"processed":len(seen),
        "missing":[n for n in names if n not in seen],
        "quality_counts":dict(Counter(p["status"] for p in quality)),
        "batches":provenance,"api_calls":0}
