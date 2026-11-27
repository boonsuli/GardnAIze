"""Offline RF trained on provisional rule-derived labels, not expert truth."""
import argparse
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import make_pipeline

GARDEN = ("sun_exposure", "soil_drainage", "water_availability",
          "minimum_winter_temperature_c", "maximum_height_cm", "maximum_spread_cm",
          "evergreen_preferred", "soil_texture", "soil_moisture_seasonality",
          "planting_context", "maintenance_preference")
PLANT = ("sun_exposure", "soil_drainage", "water_need", "hardiness_min_c",
         "height_cm", "spread_cm", "evergreen", "soil_type",
         "soil_moisture_tolerance", "planting_context", "category",
         "heat_tolerance", "drought_tolerance", "maintenance_level")


def features(row):
    result = {}
    for prefix, fields in (("garden_", GARDEN), ("plant_", PLANT)):
        for field in fields:
            key = prefix + field
            value = row.get(key)
            if value is None:
                result[key + ":missing"] = 1
            elif field in ("height_cm", "spread_cm"):
                result[key + ":min"], result[key + ":max"] = value
            elif isinstance(value, list):
                for item in value:
                    result[key + ":" + str(item)] = 1
            else:
                result[key] = value
    return result


def train(rows):
    eligible = [r for r in rows if r.get("experimental_training_eligible") is True
                and r.get("label_source") == "RULE_DERIVED"
                and r.get("plant_quality") == "ACCEPTED"
                and r.get("relevance_grade") in (0, 1, 2, 3)]
    groups = [r["garden_id"] for r in eligible]
    if len(set(groups)) < 10:
        raise ValueError("At least ten distinct eligible gardens required")
    if len({(r["garden_id"], r["scientific_name"]) for r in eligible}) != len(eligible):
        raise ValueError("Duplicate eligible pairs")
    x = [features(r) for r in eligible]
    y = np.array([r["relevance_grade"] for r in eligible])
    tr, te = next(GroupShuffleSplit(n_splits=1, test_size=.25, random_state=42).split(x, y, groups))
    if len(set(y[tr])) < 2 or len(set(y[te])) < 2:
        raise ValueError("Need multiple classes in both garden groups")
    model = make_pipeline(DictVectorizer(), RandomForestClassifier(
        n_estimators=200, min_samples_leaf=2, class_weight="balanced",
        random_state=42, n_jobs=2))
    model.fit([x[i] for i in tr], y[tr])
    pred = model.predict([x[i] for i in te])
    probabilities = model.predict_proba([x[i] for i in te])
    scores = probabilities[:, model.classes_ >= 2].sum(axis=1)
    precision = []
    for garden in sorted({groups[i] for i in te}):
        positions = [j for j, i in enumerate(te) if groups[i] == garden]
        top = sorted(positions, key=lambda j: -scores[j])[:5]
        precision.append(sum(y[te[j]] >= 2 for j in top) / len(top))
    metrics = {"status": "EXPERIMENTAL_RULE_AGREEMENT_NOT_EXPERT_VALIDATION",
               "train_gardens": len({groups[i] for i in tr}),
               "test_gardens": len({groups[i] for i in te}),
               "train_rows": len(tr), "test_rows": len(te),
               "macro_f1": float(f1_score(y[te], pred, labels=[0,1,2,3], average="macro", zero_division=0)),
               "confusion_matrix": confusion_matrix(y[te], pred, labels=[0,1,2,3]).tolist(),
               "classification_report": classification_report(y[te], pred, labels=[0,1,2,3], output_dict=True, zero_division=0),
               "mean_top_up_to_5_rule_precision": float(np.mean(precision)),
               "distinct_eligible_plants": len({r["scientific_name"] for r in eligible})}
    return model, metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pairs", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    raw = args.pairs.read_bytes()
    model, metrics = train(json.loads(raw))
    metrics["input_sha256"] = hashlib.sha256(raw).hexdigest()
    args.out_dir.mkdir(parents=True, exist_ok=False)
    joblib.dump(model, args.out_dir / "rf.joblib")
    (args.out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
