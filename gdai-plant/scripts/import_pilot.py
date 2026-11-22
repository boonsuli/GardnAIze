#!/usr/bin/env python3
"""Non-destructive GardnAIze pilot import into isolated PostgreSQL staging schema."""
import argparse,csv,json,os
from pathlib import Path
from collections import Counter

FIELDS={'sun_exposure','soil_drainage','water_need','hardiness_min_c','height_cm','spread_cm','evergreen'}

def read(path):
    with open(path,encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--traits',type=Path,default=Path('gdai-plant/data/sources/mvp40-required-traits-batch01.csv'))
    p.add_argument('--commercial',type=Path,default=Path('gdai-plant/data/sources/mvp40-commercial-summary.csv'))
    p.add_argument('--dsn',default=os.getenv('GARDNAIZE_ML_DATABASE_URL'))
    p.add_argument('--apply',action='store_true')
    a=p.parse_args(); traits=read(a.traits); commercial=read(a.commercial)
    names={r['scientific_name'].strip() for r in traits}; keys=[(r['scientific_name'].strip(),r['field'].strip()) for r in traits]
    if len(traits)!=70 or len(names)!=10 or len(set(keys))!=70 or any(f not in FIELDS for _,f in keys):raise SystemExit('Invalid traits shape: expected 10 plants × 7 unique fields')
    if any({r['field'] for r in traits if r['scientific_name']==n}!=FIELDS for n in names):raise SystemExit('Missing or unexpected trait')
    if len(commercial)!=10 or {r['scientific_name'].strip() for r in commercial}!=names:raise SystemExit('Commercial catalog mismatch')
    if len({r['scientific_name'] for r in commercial})!=10:raise SystemExit('Duplicate commercial row')
    allowed={'UNVERIFIED','CATALOG_LISTED','PRODUCT_VERIFIED'}
    if any(r['commercial_evidence_level'] not in allowed for r in commercial):raise SystemExit('Invalid commercial level')
    if any(r.get('review_status')=='VALIDATED' for r in traits):raise SystemExit('Unexpected validated trait; manual review required')
    summary={'species':len(names),'traits':len(traits),'empty_traits':sum(not(r['observed_value'].strip() or r['original_range'].strip()) for r in traits),'commercial':dict(Counter(r['commercial_evidence_level'] for r in commercial)),'mode':'APPLY' if a.apply else 'DRY_RUN'}
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    if not a.apply:return
    if not a.dsn:raise SystemExit('Set GARDNAIZE_ML_DATABASE_URL or --dsn')
    import psycopg
    # Intentionally isolated from horticulture.plant and Flyway-managed application tables.
    with psycopg.connect(a.dsn) as conn:
        with conn.cursor() as cur:
            cur.execute('CREATE SCHEMA IF NOT EXISTS gardnaize_import_stage')
            cur.execute('''CREATE TABLE IF NOT EXISTS gardnaize_import_stage.plant_trait_evidence (
              scientific_name text NOT NULL, field text NOT NULL, observed_value text NOT NULL DEFAULT '',
              original_range text NOT NULL DEFAULT '', source_url text NOT NULL DEFAULT '',
              source_license text NOT NULL DEFAULT '', commercial_reuse_allowed text NOT NULL DEFAULT '',
              reviewer text NOT NULL DEFAULT '', reviewed_at text NOT NULL DEFAULT '',
              review_status text NOT NULL DEFAULT '', notes text NOT NULL DEFAULT '',
              PRIMARY KEY(scientific_name,field))''')
            cur.execute('''CREATE TABLE IF NOT EXISTS gardnaize_import_stage.plant_commercial_summary (
              scientific_name text PRIMARY KEY, commercial_evidence_level text NOT NULL,
              evidence_type text NOT NULL DEFAULT '', nursery_name text NOT NULL DEFAULT '',
              nursery_country text NOT NULL DEFAULT '', evidence_url text NOT NULL DEFAULT '',
              observed_at text NOT NULL DEFAULT '', stock_confirmed text NOT NULL DEFAULT '',
              product_page_verified text NOT NULL DEFAULT '', review_status text NOT NULL DEFAULT '',
              notes text NOT NULL DEFAULT '')''')
            cols=['scientific_name','field','observed_value','original_range','source_url','source_license','commercial_reuse_allowed','reviewer','reviewed_at','review_status','notes']
            for r in traits:
                vals=[r.get(c,'') for c in cols]
                cur.execute('''INSERT INTO gardnaize_import_stage.plant_trait_evidence
                 (scientific_name,field,observed_value,original_range,source_url,source_license,commercial_reuse_allowed,reviewer,reviewed_at,review_status,notes)
                 VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                 ON CONFLICT (scientific_name,field) DO UPDATE SET
                 observed_value=EXCLUDED.observed_value,original_range=EXCLUDED.original_range,
                 source_url=EXCLUDED.source_url,source_license=EXCLUDED.source_license,
                 commercial_reuse_allowed=EXCLUDED.commercial_reuse_allowed,reviewer=EXCLUDED.reviewer,
                 reviewed_at=EXCLUDED.reviewed_at,review_status=EXCLUDED.review_status,notes=EXCLUDED.notes''',vals)
            ccols=['scientific_name','commercial_evidence_level','evidence_type','nursery_name','nursery_country','evidence_url','observed_at','stock_confirmed','product_page_verified','review_status','notes']
            for r in commercial:
                cur.execute('''INSERT INTO gardnaize_import_stage.plant_commercial_summary
                (scientific_name,commercial_evidence_level,evidence_type,nursery_name,nursery_country,evidence_url,observed_at,stock_confirmed,product_page_verified,review_status,notes)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (scientific_name) DO UPDATE SET
                commercial_evidence_level=EXCLUDED.commercial_evidence_level,evidence_type=EXCLUDED.evidence_type,
                nursery_name=EXCLUDED.nursery_name,nursery_country=EXCLUDED.nursery_country,
                evidence_url=EXCLUDED.evidence_url,observed_at=EXCLUDED.observed_at,
                stock_confirmed=EXCLUDED.stock_confirmed,product_page_verified=EXCLUDED.product_page_verified,
                review_status=EXCLUDED.review_status,notes=EXCLUDED.notes''',[r.get(c,'') for c in ccols])
            cur.execute('SELECT count(*) FROM gardnaize_import_stage.plant_trait_evidence'); print('DB trait rows:',cur.fetchone()[0])
            cur.execute('SELECT count(*) FROM gardnaize_import_stage.plant_commercial_summary'); print('DB commercial rows:',cur.fetchone()[0])
        conn.commit()
    print('COMMITTED staging import. No changes to horticulture.plant.')
if __name__=='__main__':main()
