"""Permission-gated merchant CSV normalization and Latin-name matching."""
import argparse,csv,json,unicodedata
from pathlib import Path
from authorized_sources import read_merchant_export

def latin_key(name,cultivar=""):
    normalized=lambda v:" ".join(unicodedata.normalize("NFKC",str(v or "")).casefold().split())
    return normalized(name),normalized(cultivar)

def merge_authorized_feed(csv_path,manifest,column_map):
    offers=[]
    for row in read_merchant_export(csv_path,manifest,column_map):
        row["latin_key"]=list(latin_key(row["scientific_name"],row.get("cultivar")))
        offers.append(row)
    return offers

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--csv",type=Path,required=True)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--column-map",type=Path,required=True)
    p.add_argument("--output",type=Path,default=Path("ai-service/plant-ingestion/outputs/merchant_normalized.json"))
    p.add_argument("--apply",action="store_true")
    a=p.parse_args()
    manifest=json.loads(a.manifest.read_text(encoding="utf-8"))
    mapping=json.loads(a.column_map.read_text(encoding="utf-8"))
    offers=merge_authorized_feed(a.csv,manifest,mapping)
    print(f"Approved merchant offers={len(offers)} apply={a.apply}")
    if a.apply:
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(offers,ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__":
    main()
