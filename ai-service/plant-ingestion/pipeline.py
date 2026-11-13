"""Licensed-source ingestion and canonical plant enrichment for GardnAIze.
Only explicitly approved local exports are read. No web scraping is performed.
"""
from __future__ import annotations
import csv
import json
import re
import unicodedata
from pathlib import Path

FIELDS = ("scientific_name","cultivar","common_name","outdoor","europe_compatible",
            "exposure","soil","water_requirement","hardiness_min_c","height_cm",
            "foliage_color","flower_color","flowering_months","pollen_allergy",
            "pollinators","heat_tolerance","drought_tolerance")
REQUIRED = ("scientific_name","outdoor","europe_compatible","exposure","soil",
            "water_requirement","hardiness_min_c","height_cm")
ALLOWED = {"CC0-1.0","CC-BY-4.0","CC-BY-3.0"}

def canonical_key(row):
    name = unicodedata.normalize("NFKC", str(row.get("scientific_name") or "")).casefold()
    name = " ".join(name.split())
    cultivar = unicodedata.normalize("NFKC", str(row.get("cultivar") or "")).casefold().strip()
    return (name, cultivar)

def read_authorized_csv(path, manifest):
    if not manifest.get("automated_access_allowed") or not manifest.get("commercial_reuse_allowed"):
        raise PermissionError("Source not approved for automated commercial use")
    if manifest.get("license") not in ALLOWED and not manifest.get("written_permission"):
        raise PermissionError("Missing compatible licence or written permission")
    if not manifest.get("source_url"):
        raise ValueError("Source URL required for provenance")
    with Path(path).open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            record = {field: (row.get(field) or "").strip() or None for field in FIELDS}
            record["source"] = manifest["name"]
            record["source_url"] = manifest["source_url"]
            record["license"] = manifest.get("license")
            yield record

def eligible(row):
    return str(row.get("outdoor") or "").casefold() in {"true","yes","1"} and str(row.get("europe_compatible") or "").casefold() in {"true","yes","1"}

def merge_records(rows):
    plants = {}
    conflicts = []
    for row in rows:
        if not eligible(row):
            continue
        key = canonical_key(row)
        if not key[0]:
            continue
        if key not in plants:
            plants[key] = dict(row, sources=[row["source"]])
            continue
        target = plants[key]
        if row["source"] not in target["sources"]:
            target["sources"].append(row["source"])
        for field in FIELDS:
            incoming = row.get(field)
            if incoming is None:
                continue
            if target.get(field) is None:
                target[field] = incoming
            elif target[field] != incoming:
                conflicts.append({"taxon":key, "field":field,
                                    "existing":target[field],"incoming":incoming,
                                    "source":row["source"]})
    for plant in plants.values():
        plant["missing_required"] = [field for field in REQUIRED if plant.get(field) is None]
        plant["quality_status"] = "READY_FOR_REVIEW" if not plant["missing_required"] else "INCOMPLETE"
    return list(plants.values()), conflicts

def export(plants, conflicts, output_dir):
    dest = Path(output_dir)
    dest.mkdir(parents=True, exist_ok=True)
    with (dest / "plants.json").open("w",encoding="utf-8") as f:
        json.dump(plants,f,ensure_ascii=False,indent=2)
    with (dest / "conflicts.json").open("w",encoding="utf-8") as f:
        json.dump(conflicts,f,ensure_ascii=False,indent=2)
    with (dest / "plants.csv").open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=[*FIELDS,"quality_status","missing_required","sources"],extrasaction="ignore")
        writer.writeheader()
        for plant in plants:
            writer.writerow({k: json.dumps(v,ensure_ascii=False) if isinstance(v,list) else v for k,v in plant.items()})
