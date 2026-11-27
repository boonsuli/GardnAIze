"""Package a trusted trained model with its exact eligible catalogue."""
import argparse
import json
import shutil
from pathlib import Path
from api.model_registry import sha
from api.rf_features import PLANT

def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("pairs", "run", "out"):
        p.add_argument("--"+key, type=Path, required=True)
    for key in ("model-id", "dataset-profile", "rule-set", "country", "continent", "region", "climate-zone"):
        p.add_argument("--"+key, required=True)
    a = p.parse_args()
    metrics = json.loads((a.run/"metrics.json").read_text())
    if metrics["input_sha256"] != sha(a.pairs):
        raise ValueError("Training input mismatch")
    plants = {}
    for row in json.loads(a.pairs.read_text()):
        if row.get("experimental_training_eligible") is not True or row.get("plant_quality") != "ACCEPTED" or row.get("label_source") != "RULE_DERIVED":
            continue
        name = row["scientific_name"]
        values = {"plant_"+k:row.get("plant_"+k) for k in PLANT}
        if name in plants and plants[name] != values:
            raise ValueError("Inconsistent plant features")
        plants[name] = values
    if len(plants) != metrics["distinct_eligible_plants"]:
        raise ValueError("Catalogue count mismatch")
    catalogue = [{"plant_id":i+1,"scientific_name":name,"features":plants[name]}
                 for i,name in enumerate(sorted(plants))]
    scope = {k:getattr(a,k) for k in ("continent","country","region","climate_zone")}
    a.out.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(a.run/"rf.joblib",a.out/"rf.joblib")
    shutil.copyfile(a.run/"metrics.json",a.out/"metrics.json")
    (a.out/"catalogue.json").write_text(json.dumps(catalogue,ensure_ascii=False,indent=2))
    metadata = {"model_id":a.model_id,"scope":scope,"dataset_profile_id":a.dataset_profile,
                "rule_set_id":a.rule_set,"label_source":"RULE_DERIVED",
                "horticultural_validation":"PENDING","plant_id_namespace":"BUNDLE_LOCAL",
                "training_input_sha256":sha(a.pairs),
                "sha256":{name:sha(a.out/name) for name in ("rf.joblib","catalogue.json")}}
    (a.out/"metadata.json").write_text(json.dumps(metadata,indent=2))
    registry = {"schema_version":1,"models":[{"model_id":a.model_id,"enabled":True,"scope":scope,"bundle":"."}]}
    (a.out/"registry.json").write_text(json.dumps(registry,indent=2))

if __name__ == "__main__":
    main()
