"""Local-only image review manifest, deterministic garden-group split and safe exports."""
import csv
import hashlib
import json
from pathlib import Path

FIELDS = ("source_key","external_id","image_path","garden_group_key","license_name",
          "redistribution_allowed","climate_zone","soil_type","exposure")
DECISIONS = {"PENDING","ACCEPTED","REJECTED","UNCERTAIN"}

def load_manifest(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        if not row.get("source_key") or not row.get("external_id") or not row.get("garden_group_key"):
            raise ValueError("source_key, external_id and garden_group_key required")
    if len({(r["source_key"],r["external_id"]) for r in rows}) != len(rows):
        raise ValueError("Duplicate source image identifier")
    return rows

def load_reviews(path):
    if not Path(path).exists():
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        return {(r["source_key"],r["external_id"]): r for r in csv.DictReader(f)}

def save_reviews(path, reviews):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix+".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["source_key","external_id","review_status","review_reason"])
        w.writeheader()
        for key, r in sorted(reviews.items()):
            if r["review_status"] not in DECISIONS:
                raise ValueError("Invalid decision")
            w.writerow({k:r.get(k,"") for k in w.fieldnames})
    tmp.replace(path)

def assign_split(group_key):
    # Same garden is always in same split, independent of input order.
    bucket = int(hashlib.sha256(group_key.encode("utf-8")).hexdigest()[:8],16) % 100
    return "TRAIN" if bucket < 70 else ("VAL" if bucket < 85 else "TEST")

def reviewed_records(manifest, reviews):
    result=[]
    for r in manifest:
        decision=reviews.get((r["source_key"],r["external_id"]),{})
        status=decision.get("review_status","PENDING")
        if status not in DECISIONS:
            raise ValueError("Invalid decision")
        row={**r,"review_status":status,"review_reason":decision.get("review_reason",""),
             "dataset_split":assign_split(r["garden_group_key"]) if status=="ACCEPTED" else ""}
        result.append(row)
    return result

def export_json(path, records):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding="utf-8")
