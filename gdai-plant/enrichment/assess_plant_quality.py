"""Plant-level quality gate for provisional AI profiles."""
from enrichment.validate_claude_review import validate_review

ESSENTIAL = {"sun_exposure", "soil_drainage", "water_need", "hardiness_min_c", "height_cm", "spread_cm"}
ENVIRONMENT = {"sun_exposure", "soil_drainage", "water_need", "hardiness_min_c", "soil_type", "soil_moisture_tolerance", "heat_tolerance", "drought_tolerance", "planting_context"}
CORE = {"sun_exposure", "soil_drainage", "water_need", "hardiness_min_c"}
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

def assess(payload, review, consolidated, policy="v2"):
    from enrichment.validate_plant_profiles import validate
    validate(consolidated, [p["scientific_name"] for p in payload["profiles"]])
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
        env_ratio = sum(traits[k]["verdict"] == "SUPPORTED" and originals[name][k]["value"] is not None for k in ENVIRONMENT) / len(ENVIRONMENT)
        if policy == "v2":
            missing = sorted(k for k in CORE if retained[name][k]["value"] is None)
            critical_majors = [k for k in majors if k in ENVIRONMENT or k in ("height_cm", "spread_cm", "root_development")]
            status = "EXCLUDED" if env_ratio < .70 or len(critical_majors) >= 2 or len(missing) >= 2 else "ACCEPTED" if env_ratio >= .85 and not critical_majors and not missing else "CONDITIONAL"
        results.append({"scientific_name":name,"status":status,"agreement":ratio,"environment_agreement":env_ratio,"major_divergences":majors,"missing_essential":missing,
                        "missing_traits":sorted(k for k in traits if retained[name][k]["value"] is None)})
    return {"policy":"PROVISIONAL_"+policy.upper(),"plants":results}

if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("gemini","review","consolidated","out"):
        p.add_argument("--"+name,type=Path,required=True)
    p.add_argument("--policy", choices=("v1", "v2"), default="v2")
    a=p.parse_args()
    report=assess(*(json.loads(x.read_text()) for x in (a.gemini,a.review,a.consolidated)), policy=a.policy)
    with a.out.open("x",encoding="utf-8") as f:
        json.dump(report,f,ensure_ascii=False,indent=2)
    print(json.dumps(report,ensure_ascii=False,indent=2))
