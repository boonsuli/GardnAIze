#!/usr/bin/env python3
"""Auditable offline enrichment: source observations, not scraped/invented values."""
import argparse, csv, json
from collections import Counter
from datetime import date
from pathlib import Path

TRAITS = ('sun_exposure','soil_type','soil_drainage','water_need','hardiness_min_c','height_cm','spread_cm','evergreen','flower_color','flowering_months','maintenance_level','heat_tolerance','drought_tolerance')
REQUIRED = ('sun_exposure','soil_drainage','water_need','hardiness_min_c','height_cm','spread_cm','evergreen')
EVIDENCE_FIELDS = ('scientific_name','field','value','source_url','source_license','commercial_reuse_allowed','reviewer','reviewed_at')
NURSERY_FIELDS = ('scientific_name','nursery_name','nursery_country','nursery_product_url','nursery_observed_at','listed_for_sale')

def read_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        return list(csv.DictReader(f))

def write_csv(path, fields, rows):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w=csv.DictWriter(f, fieldnames=fields);w.writeheader();w.writerows(rows)

def evaluate(catalog, evidence, nurseries):
    names={p['scientific_name'] for p in catalog}
    accepted={}; errors=[]
    for n,row in enumerate(evidence,2):
        name, field = row.get('scientific_name','').strip(),row.get('field','').strip()
        if name not in names or field not in TRAITS:
            errors.append(f'evidence line {n}: unknown plant or field');continue
        if not all(row.get(k,'').strip() for k in ('value','source_url','source_license','reviewer','reviewed_at')) or row.get('commercial_reuse_allowed','').strip().lower() != 'true' or not row['source_url'].startswith('https://'):
            errors.append(f'evidence line {n}: incomplete provenance or rights not confirmed');continue
        value=row['value'].strip()
        if field=='evergreen' and value.lower() not in ('true','false'):
            errors.append(f'evidence line {n}: evergreen must be true/false');continue
        if field in ('hardiness_min_c','height_cm','spread_cm'):
            try: num=float(value)
            except ValueError:
                errors.append(f'evidence line {n}: invalid numeric value');continue
            if field!='hardiness_min_c' and num<=0:
                errors.append(f'evidence line {n}: nonpositive dimension');continue
        key=(name,field)
        if key in accepted and accepted[key]['value']!=value:
            errors.append(f'evidence line {n}: conflicting evidence for {name}/{field}')
            accepted.pop(key,None)
            continue
        accepted[key]=row
    listings={}
    for n,row in enumerate(nurseries,2):
        name=row.get('scientific_name','').strip()
        if name not in names or row.get('listed_for_sale','').strip().lower()!='true' or row.get('nursery_country','').strip().upper()!='FR' or not row.get('nursery_product_url','').startswith('https://') or not row.get('nursery_name','').strip():
            continue
        try: observed=date.fromisoformat(row.get('nursery_observed_at',''))
        except ValueError: continue
        if observed>date.today(): continue
        listings.setdefault(name,row)
    results=[]
    for p in catalog:
        name=p['scientific_name'];fields={field:accepted[(name,field)]['value'] for field in TRAITS if (name,field) in accepted}
        missing=[field for field in REQUIRED if field not in fields]
        results.append({'scientific_name':name,'plant_type':p['candidate_category'],**fields,'documented_fields':len(fields),'missing_required':';'.join(missing),'nursery_evidence':name in listings,'review_status':'READY_FOR_EXPERT_REVIEW' if not missing and name in listings else 'PENDING'})
    return results,errors

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--catalog',default='gdai-plant/data/plants-mvp-40.json')
    ap.add_argument('--evidence',default='gdai-plant/data/sources/mvp40-trait-evidence.csv')
    ap.add_argument('--nurseries',default='gdai-plant/data/sources/mvp40-nursery-evidence.csv')
    ap.add_argument('--init',action='store_true')
    ap.add_argument('--report',default='gdai-plant/data/mvp40-quality-report.json')
    args=ap.parse_args()
    catalog=json.loads(Path(args.catalog).read_text(encoding='utf-8'))
    assert len(catalog)==40 and len({p['scientific_name'] for p in catalog})==40
    if args.init:
        for path,fields in ((args.evidence,EVIDENCE_FIELDS),(args.nurseries,NURSERY_FIELDS)):
            p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
            if p.exists(): print('PRESERVED',p)
            else: write_csv(p,fields,[]);print('CREATED',p)
        return
    evidence=read_csv(args.evidence);nurseries=read_csv(args.nurseries)
    results,errors=evaluate(catalog,evidence,nurseries)
    summary={'total':len(results),'traits_accepted':sum(r['documented_fields'] for r in results),'plants_with_all_required_traits':sum(not r['missing_required'] for r in results),'plants_with_french_nursery_evidence':sum(r['nursery_evidence'] for r in results),'ready_for_expert_review':sum(r['review_status']=='READY_FOR_EXPERT_REVIEW' for r in results),'errors':errors,'plants':results}
    p=Path(args.report);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in summary.items() if k!='plants'},ensure_ascii=False,indent=2))
    print('REPORT',p)

if __name__=='__main__':main()
