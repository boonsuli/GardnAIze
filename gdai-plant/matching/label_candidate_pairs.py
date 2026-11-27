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

def grade(g, p, policy="v2", config=None):
    if policy == "v4":
        from matching.compensation_engine import evaluate_v4
        result = evaluate_v4(g,p,config if config is not None else load_config())
        return result["relevance_grade"], result["reasons"]
    if policy == "v3":
        from matching.rule_engine import evaluate
        return evaluate(g,p,config if config is not None else load_config())
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

def load_config():
    return json.loads((Path(__file__).resolve().parents[1] / "config/matching-rules-v3.json").read_text(encoding="utf-8"))

def build(gardens, profiles, quality, policy="v2", categories=None, config=None, *, synthetic_compensation=False):
    if policy in ("v3", "v4"):
        config = config if config is not None else load_config()
        if categories is None or any(p["scientific_name"] not in categories for p in profiles["profiles"]):
            raise ValueError("V3/V4 requires catalogue categories for all profiles")
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
            if policy in ("v3", "v4"):
                values["category"] = categories[name]
            status=statuses[name]
            label,reasons=(None,{"excluded":["plant_quality"]}) if status=="EXCLUDED" else grade(g,values,policy,config)
            extra = {}
            if policy == "v4":
                from matching.compensation_engine import evaluate_v4
                from matching.alternative_engine import suggest_alternatives
                if status != "EXCLUDED":
                    kwargs = {}
                    if synthetic_compensation:
                        if g.get("compensation_provenance") != "SYNTHETIC_SENSITIVITY_V1":
                            raise ValueError("Missing synthetic compensation provenance")
                        kwargs = {"accepted": g["compensation_accepted"], "feasible": g["compensation_feasible"]}
                    extra = evaluate_v4(g, values, config, **kwargs)
                    label, reasons = extra["relevance_grade"], extra["reasons"]
                    extra["questionnaire_changes"] = suggest_alternatives(g, values, config, **kwargs) if status == "ACCEPTED" else []
                    extra["recommendation_eligible"] = extra["recommendation_eligible"] and status == "ACCEPTED"
                else:
                    extra = {"initial_relevance_grade": None, "resolved_conditions": [], "unresolved_conditions": ["plant_quality"], "usage_advice": [], "questionnaire_changes": [], "recommendation_eligible": False}
            # Conditional plants are diagnostic only until their quality is resolved.
            eligible=label is not None and status=="ACCEPTED"
            rows.append({"garden_id":g["id"],"scientific_name":name,"garden_origin":g["origin"],
                         **{"garden_"+k:v for k,v in g.items() if k not in ("id","origin","plausibility_reason","enrichment_provenance")},
                         **{"plant_"+k:v for k,v in values.items()},
                         "matching_policy":"HORTICULTURAL_RULES_"+policy.upper(),"plant_quality":status,"relevance_grade":label,
                         "label_source":"RULE_DERIVED" if label is not None else None,
                         "assessment_status":"EXCLUDED" if status=="EXCLUDED" else "INSUFFICIENT_DATA" if label is None else "PROVISIONAL",
                         "experimental_training_eligible":eligible,"reasons":reasons, **extra})
    return rows

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("gardens","gemini","review","out-dir"):
        p.add_argument("--"+name,type=Path,required=True)
    p.add_argument("--catalogue", type=Path, default=Path(__file__).resolve().parents[1] / "data/plants-mvp-40.json")
    p.add_argument("--policy", choices=("v1","v2","v3","v4"), default="v3")
    p.add_argument("--synthetic-compensation", action="store_true")
    a=p.parse_args()
    if a.synthetic_compensation and a.policy != "v4":
        p.error("Synthetic compensation requires V4")
    read=lambda path:json.loads(path.read_text(encoding="utf-8"))
    gardens=read(a.gardens)["scenarios"]
    gemini,review=read(a.gemini),read(a.review)
    profiles,_=consolidate(gemini,review,policy="v2")
    quality=assess(gemini,review,profiles,policy="v2")
    config = load_config() if a.policy in ("v3", "v4") else None
    catalogue = read(a.catalogue) if a.policy in ("v3", "v4") else []
    categories = {p["scientific_name"]:p["candidate_category"] for p in catalogue}
    if len(categories) != len(catalogue):
        raise ValueError("Duplicate catalogue taxa")
    rows=build(gardens,profiles,quality,a.policy,categories,config, synthetic_compensation=a.synthetic_compensation)
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
    if a.policy == "v4":
        report["compensation_mode"] = "SYNTHETIC_SENSITIVITY_V1" if a.synthetic_compensation else "NO_UNVERIFIED_COMMITMENTS"
        report["initial_label_counts"] = dict(Counter(str(r["initial_relevance_grade"]) for r in rows))
        report["resolved_conditions"] = sum(len(r["resolved_conditions"]) for r in rows)
        report["alternative_pairs"] = sum(bool(r["questionnaire_changes"]) for r in rows)
        coverage = Counter(r["garden_id"] for r in rows if r["recommendation_eligible"])
        report["gardens_with_at_least_five_recommendations"] = sum(n >= 5 for n in coverage.values())
    if config is not None:
        report["rule_config"] = config
        report["rule_config_sha256"] = digest(config)
        report["catalogue_sha256"] = digest(catalogue)
    a.out_dir.mkdir(parents=True,exist_ok=False)
    for name,data in (("labelled-pairs.json",rows),("matching-report.json",report)):
        (a.out_dir/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,indent=2))

if __name__=="__main__":
    main()
