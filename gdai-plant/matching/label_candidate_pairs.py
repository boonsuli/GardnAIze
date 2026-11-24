"""Experimental rule-derived labels, not expert ground truth."""
import argparse
import json
from collections import Counter
from pathlib import Path
from enrichment.assess_plant_quality import assess
from enrichment.consolidate_plant_profiles import consolidate
from enrichment.prepare_claude_review import digest

LEVELS = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
MEMBERSHIP = {"sun_exposure":"sun_exposure", "soil_drainage":"soil_drainage",
              "soil_texture":"soil_type", "soil_moisture_seasonality":"soil_moisture_tolerance",
              "planting_context":"planting_context"}

def grade(g, p, policy="v2"):
    if policy not in ("v1", "v2"):
        raise ValueError("Unknown matching policy")
    advisory = []
    incompatible, unknown, conditional = [], [], []
    for garden, plant in MEMBERSHIP.items():
        a,b = g.get(garden),p.get(plant)
        if a is None or b is None:
            unknown.append(plant)
        elif a not in b:
            if plant in ("sun_exposure","soil_drainage"):
                incompatible.append(plant)
            else:
                conditional.append(plant)
    a,b = g.get("minimum_winter_temperature_c"),p.get("hardiness_min_c")
    if a is None or b is None:
        unknown.append("hardiness_min_c")
    elif a < b:
        incompatible.append("hardiness_min_c")
    elif a-b <= 2:
        conditional.append("frost_margin")
    a,b = g.get("water_availability"),p.get("water_need")
    if a is None or b is None:
        unknown.append("water_need")
    elif LEVELS[b]-LEVELS[a] >= 2:
        incompatible.append("water_need")
    elif LEVELS[b] > LEVELS[a]:
        conditional.append("water_need")
    for garden,plant in (("maximum_height_cm","height_cm"),("maximum_spread_cm","spread_cm")):
        a,b = g.get(garden),p.get(plant)
        if policy == "v2":
            if a is None or b is None:
                advisory.append("unknown_" + plant)
            elif a < b[1]:
                advisory.append("review_size_management_" + plant)
        elif a is None or b is None:
            unknown.append(plant)
        elif a < b[0]:
            incompatible.append(plant)
        elif a < b[1]:
            conditional.append(plant)
    if g.get("evergreen_preferred") is True:
        if p.get("evergreen") is None:
            unknown.append("evergreen")
        elif not p["evergreen"]:
            conditional.append("evergreen_preference")
    reasons = {"incompatible":incompatible,"unknown":unknown,"conditional":conditional,"advisory":advisory}
    if incompatible:
        return 0,reasons
    if unknown:
        return None,reasons
    if conditional:
        return 1,reasons
    return (3 if g.get("evergreen_preferred") is True and p.get("evergreen") is True else 2),reasons

def build(gardens, profiles, quality, policy="v2"):
    names = [p["scientific_name"] for p in profiles["profiles"]]
    statuses = {p["scientific_name"]:p["status"] for p in quality["plants"]}
    if len(set(names)) != len(names) or set(names) != set(statuses) or len(statuses) != len(quality["plants"]):
        raise ValueError("Profile/quality mismatch")
    if quality["policy"] != "PROVISIONAL_V2" or not set(statuses.values()) <= {"ACCEPTED","CONDITIONAL","EXCLUDED"}:
        raise ValueError("Invalid quality policy")
    if len({g["id"] for g in gardens}) != len(gardens):
        raise ValueError("Duplicate garden")
    rows=[]
    for g in gardens:
        for p in profiles["profiles"]:
            name=p["scientific_name"]
            values={k:v["value"] for k,v in p["traits"].items()}
            status=statuses[name]
            label,reasons=(None,{"excluded":["plant_quality"]}) if status=="EXCLUDED" else grade(g,values,policy)
            # Conditional plants are diagnostic only until their quality is resolved.
            eligible=label is not None and status=="ACCEPTED"
            rows.append({"garden_id":g["id"],"scientific_name":name,"garden_origin":g["origin"],
                         **{"garden_"+k:v for k,v in g.items() if k not in ("id","origin","plausibility_reason","enrichment_provenance")},
                         **{"plant_"+k:v for k,v in values.items()},
                         "matching_policy":"HORTICULTURAL_RULES_"+policy.upper(),"plant_quality":status,"relevance_grade":label,
                         "label_source":"RULE_DERIVED" if label is not None else None,
                         "assessment_status":"EXCLUDED" if status=="EXCLUDED" else "INSUFFICIENT_DATA" if label is None else "PROVISIONAL",
                         "experimental_training_eligible":eligible,"reasons":reasons})
    return rows

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("gardens","gemini","review","out-dir"):
        p.add_argument("--"+name,type=Path,required=True)
    p.add_argument("--policy", choices=("v1","v2"), default="v2")
    a=p.parse_args()
    read=lambda path:json.loads(path.read_text(encoding="utf-8"))
    gardens=read(a.gardens)["scenarios"]
    gemini,review=read(a.gemini),read(a.review)
    profiles,_=consolidate(gemini,review,policy="v2")
    quality=assess(gemini,review,profiles,policy="v2")
    rows=build(gardens,profiles,quality,a.policy)
    report={"policy":"HORTICULTURAL_RULES_"+a.policy.upper(),"status":"EXPERIMENTAL_NOT_EXPERT_VALIDATED",
            "garden_sha256":digest(gardens),"gemini_sha256":digest(gemini),"review_sha256":digest(review),
            "pairs":len(rows),"assessment_counts":dict(Counter(r["assessment_status"] for r in rows)),
            "label_counts":dict(Counter(str(r["relevance_grade"]) for r in rows)),
            "experimental_training_eligible":sum(r["experimental_training_eligible"] for r in rows),
            "eligible_label_counts":dict(Counter(str(r["relevance_grade"]) for r in rows if r["experimental_training_eligible"])),
            "eligible_incompatible_reasons":dict(Counter(reason for r in rows if r["experimental_training_eligible"] for reason in r["reasons"].get("incompatible",[]))),
            "eligible_conditional_reasons":dict(Counter(reason for r in rows if r["experimental_training_eligible"] and r["relevance_grade"]==1 for reason in r["reasons"].get("conditional",[]))),
            "eligible_advisory_reasons":dict(Counter(reason for r in rows if r["experimental_training_eligible"] for reason in r["reasons"].get("advisory",[]))),
            "api_calls":0}
    a.out_dir.mkdir(parents=True,exist_ok=False)
    for name,data in (("labelled-pairs.json",rows),("matching-report.json",report)):
        (a.out_dir/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
