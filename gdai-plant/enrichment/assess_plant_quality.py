"""Plant-level quality gate for provisional AI profiles."""
from enrichment.validate_claude_review import validate_review

ESSENTIAL = {"sun_exposure", "soil_drainage", "water_need", "hardiness_min_c", "height_cm", "spread_cm"}
ORDINAL = {"water_need", "heat_tolerance", "drought_tolerance", "root_development"}
SETS = {"sun_exposure", "soil_drainage", "soil_type", "soil_moisture_tolerance", "planting_context"}

def major(key, a, b):
    if a is None or b is None:
        return False
    if key == "hardiness_min_c":
        return abs(a-b) >= 5
    if key in ("height_cm", "spread_cm"):
        return abs(a[1]-b[1]) > 0.5 * min(a[1], b[1])
    if key in ORDINAL:
        return {a,b} == {"LOW","HIGH"}
    if key in SETS:
        return not set(a).intersection(b)
    return key == "evergreen" and a != b

def assess(payload, review, consolidated):
    validate_review(payload, review)
    originals = {p["scientific_name"]: p["traits"] for p in payload["profiles"]}
    retained = {p["scientific_name"]: p["traits"] for p in consolidated["profiles"]}
    if set(retained) != set(originals) or len(consolidated["profiles"]) != len(originals):
        raise ValueError("Consolidated taxa mismatch")
    results = []
    for p in review["profiles"]:
        name = p["scientific_name"]
        traits = {k:t for k,t in p["traits"].items() if k != "french_nursery_availability"}
        supported = sum(t["verdict"] == "SUPPORTED" and originals[name][k]["value"] is not None for k,t in traits.items())
        ratio = supported / len(traits)
        majors = [k for k,t in traits.items() if major(k, originals[name][k]["value"], t["proposed_value"])]
        missing = sorted(k for k in ESSENTIAL if retained[name][k]["value"] is None)
        status = "EXCLUDED" if ratio < .70 or len(majors) >= 2 or len(missing) >= 2 else "ACCEPTED" if ratio >= .85 and not majors and not missing else "CONDITIONAL"
        results.append({"scientific_name":name,"status":status,"agreement":ratio,"major_divergences":majors,"missing_essential":missing})
    return {"policy":"PROVISIONAL_V1","plants":results}

if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("gemini","review","consolidated","out"):
        p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args()
    report=assess(*(json.loads(x.read_text()) for x in (a.gemini,a.review,a.consolidated)))
    with a.out.open("x",encoding="utf-8") as f:
        json.dump(report,f,ensure_ascii=False,indent=2)
    print(json.dumps(report,ensure_ascii=False,indent=2))
