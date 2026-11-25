#!/usr/bin/env python3
"""Non-destructive commercial evidence summary; standard-library only."""
import argparse, csv, json
from collections import Counter
from pathlib import Path

EXPECTED = {'scientific_name','nursery_name','nursery_country','nursery_product_url','nursery_observed_at','listed_for_sale','evidence_type','verification_status','notes'}
RANK = {'NONE':0,'CATEGORY_LISTING':1,'CULTIVAR_LISTING':1,'PRODUCT_PAGE_VERIFIED':2}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',required=True,type=Path)
    p.add_argument('--catalog',default='gdai-plant/data/sources/mvp40-required-traits-batch01.csv',type=Path)
    p.add_argument('--output',default='gdai-plant/data/sources/mvp40-commercial-summary.csv',type=Path)
    a=p.parse_args()
    with a.source.open(encoding='utf-8-sig',newline='') as f:
        r=csv.DictReader(f); missing=EXPECTED-set(r.fieldnames or [])
        if missing: raise SystemExit(f'Missing source columns: {sorted(missing)}')
        source=list(r)
    with a.catalog.open(encoding='utf-8-sig',newline='') as f:
        catalog=list(csv.DictReader(f))
    names=set(x['scientific_name'].strip() for x in catalog)
    by_name={}
    for x in source:
        name=x['scientific_name'].strip()
        if name not in names: raise SystemExit(f'Unknown plant: {name}')
        if name in by_name: raise SystemExit(f'Duplicate evidence row: {name}; multi-seller support requires separate evidence table')
        kind=x['evidence_type'].strip()
        if kind not in RANK: raise SystemExit(f'Unknown evidence type: {kind}')
        if kind=='NONE' and any(x[k].strip() for k in ('nursery_name','nursery_product_url','listed_for_sale')): raise SystemExit(f'Inconsistent NONE evidence: {name}')
        by_name[name]=x
    rows=[]
    for name in sorted(by_name):
        x=by_name[name]; kind=x['evidence_type'].strip(); url=x['nursery_product_url'].strip()
        # Category and cultivar pages do not establish stock or a species-level product page.
        rows.append({'scientific_name':name,'commercial_evidence_level':'CATALOG_LISTED' if RANK[kind]==1 else ('PRODUCT_VERIFIED' if RANK[kind]==2 else 'UNVERIFIED'), 'evidence_type':kind,'nursery_name':x['nursery_name'].strip(),'nursery_country':x['nursery_country'].strip(),'evidence_url':url,'observed_at':x['nursery_observed_at'].strip(),'stock_confirmed':'false','product_page_verified':'true' if RANK[kind]==2 else 'false','review_status':x['verification_status'].strip(),'notes':x['notes'].strip()})
    if a.output.resolve()==a.source.resolve(): raise SystemExit('Output must not overwrite source')
    if a.output.exists(): raise SystemExit(f'Output already exists: {a.output}; choose another --output to avoid overwriting')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print(json.dumps({'species':len(rows),'evidence_levels':dict(Counter(x['commercial_evidence_level'] for x in rows)),'stock_confirmed':0,'output':str(a.output)},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
