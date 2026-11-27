"""Runtime registry. Load only trusted locally produced joblib artifacts."""
import json
from pathlib import Path
import hashlib
import joblib
from api.rf_features import features

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class Registry:
    def __init__(self, path):
        self.models = []
        if path is None:
            return
        path = Path(path)
        config = json.loads(path.read_text())
        if config["schema_version"] != 1:
            raise ValueError("Unsupported registry schema")
        ids = set()
        for entry in config["models"]:
            if not entry["enabled"]:
                continue
            ident = entry["model_id"]
            if ident in ids:
                raise ValueError("Duplicate model ID")
            ids.add(ident)
            root = (path.parent / entry["bundle"]).resolve()
            metadata = json.loads((root / "metadata.json").read_text())
            if metadata["model_id"] != ident or metadata["scope"] != entry["scope"]:
                raise ValueError("Bundle scope mismatch")
            for name in ("rf.joblib", "catalogue.json"):
                if sha(root / name) != metadata["sha256"][name]:
                    raise ValueError("Bundle checksum mismatch")
            catalogue = json.loads((root / "catalogue.json").read_text())
            if not catalogue or len({p["scientific_name"] for p in catalogue}) != len(catalogue):
                raise ValueError("Invalid catalogue")
            model = joblib.load(root / "rf.joblib")
            if not set(model.classes_) <= {0, 1, 2, 3}:
                raise ValueError("Invalid model classes")
            self.models.append((entry, metadata, model, catalogue))

    def select(self, garden):
        matches = [m for m in self.models if all(garden.get(k) == v for k,v in m[0]["scope"].items())]
        if len(matches) > 1:
            raise ValueError("Ambiguous model scope")
        return matches[0] if matches else None

    def predict(self, bundle, garden, limit):
        entry, metadata, model, catalogue = bundle
        rows = [features({**{"garden_"+k:v for k,v in garden.items()}, **p["features"]}) for p in catalogue]
        grades = model.predict(rows)
        scores = model.predict_proba(rows)[:, model.classes_ >= 2].sum(axis=1)
        ranked = sorted(range(len(rows)), key=lambda i: (-scores[i], catalogue[i]["scientific_name"]))
        return [{"plant_id": catalogue[i]["plant_id"], "scientific_name": catalogue[i]["scientific_name"],
                 "method": "RANDOM_FOREST", "reasons": [], "score": float(scores[i])}
                for i in ranked if grades[i] >= 2][:min(limit,5)]
