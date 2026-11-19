"""Discover GBIF backbone taxa via documented species/search API.

This is botanical candidate discovery, NOT a filter for temperate/outdoor plants.
Use --query for a taxon/genus (e.g. Salvia); no merchant scraping.
Writes staging-compatible CSV; no database writes.
"""
import argparse,csv,json,time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request,urlopen
BASE="https://api.gbif.org/v1/species/search"
FIELDS=["external_id","scientific_name","canonical_name","source_url","taxonomic_status","rank","source_key"]
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--query",required=True,help="Genus or taxon search query")
    p.add_argument("--limit",type=int,default=200)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--apply",action="store_true")
    a=p.parse_args()
    if not 1<=a.limit<=5000:p.error("--limit must be between 1 and 5000")
    print(f"GBIF taxon search query={a.query!r} max={a.limit} apply={a.apply}")
    if not a.apply:return
    results=[];seen=set();offset=0
    while len(results)<a.limit:
        size=min(100,a.limit-len(results))
        url=BASE+"?"+urlencode({"q":a.query,"rank":"SPECIES","highertaxonKey":6,"limit":size,"offset":offset})
        req=Request(url,headers={"User-Agent":"GardnAIze-research/0.1 (GBIF taxonomy discovery)"})
        with urlopen(req,timeout=40) as resp: data=json.load(resp)
        batch=data.get("results",[])
        if not batch:break
        for item in batch:
            ident=item.get("key")
            if ident is None or ident in seen:continue
            if item.get("kingdom")!="Plantae" or item.get("rank")!="SPECIES":continue
            if item.get("taxonomicStatus")!="ACCEPTED":continue
            name=item.get("canonicalName") or item.get("scientificName")
            if not name:continue
            seen.add(ident)
            results.append({"external_id":str(ident),"scientific_name":name,
                    "canonical_name":name,"source_url":"https://www.gbif.org/species/"+str(ident),
                    "taxonomic_status":item.get("taxonomicStatus"),"rank":item.get("rank"),"source_key":"GBIF"})
        offset+=len(batch)
        if data.get("endOfRecords") or len(batch)<size:break
        time.sleep(.25)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows(results)
    print(f"Saved {len(results)} accepted Plantae species candidates to {a.output}")
    print("Review taxa and source terms; no outdoor/temperate suitability asserted.")
if __name__=="__main__":main()
