"""GBIF documented API taxon resolution; dry-run by default.

Input: UTF-8 CSV with scientific_name. Output: provenance-rich JSON.
GBIF is taxonomic evidence, not horticultural suitability evidence.
"""
import argparse
import csv
import json
import time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen

API="https://api.gbif.org/v1/species/match"
def match(name):
    url=API+"?"+urlencode({"name":name,"kingdom":"Plantae","strict":"true"})
    request=Request(url,headers={"User-Agent":"GardnAIze-research/0.1 (taxonomy matching)"})
    with urlopen(request,timeout=25) as response:
        result=json.load(response)
    return {"input_name":name,"matched_name":result.get("scientificName"),
            "canonical_name":result.get("canonicalName"),
            "rank":result.get("rank"),"status":result.get("status"),
            "match_type":result.get("matchType"),"confidence":result.get("confidence"),
            "gbif_usage_key":result.get("usageKey"),"source_url":url,
            "retrieved_at":datetime.now(timezone.utc).isoformat(),
            "raw":result}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input",type=Path,required=True)
    p.add_argument("--output",type=Path,default=Path("ai-service/plant-ingestion/outputs/gbif_matches.json"))
    p.add_argument("--apply",action="store_true",help="Perform API requests and write output")
    p.add_argument("--limit",type=int,default=300)
    a=p.parse_args()
    with a.input.open(encoding="utf-8-sig",newline="") as fh:
        names=list(dict.fromkeys((r.get("scientific_name") or "").strip()
            for r in csv.DictReader(fh)))
    names=[n for n in names if n][:a.limit]
    print(f"Taxa to resolve: {len(names)} apply={a.apply}")
    if not a.apply:
        return
    output=[]
    for name in names:
        try:
            output.append(match(name))
        except Exception as exc:
            output.append({"input_name":name,"error":str(exc)})
        time.sleep(0.35)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(output,indent=2,ensure_ascii=False),encoding="utf-8")
    print(f"Wrote {len(output)} results to {a.output}; not imported into PostgreSQL")
if __name__=="__main__":
    main()
