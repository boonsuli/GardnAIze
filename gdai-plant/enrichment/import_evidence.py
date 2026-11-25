"""Import reviewed, licensed horticultural facts from a local JSON manifest.

No web scraping; no automatic promotion to validated plant fields.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse

ALLOWED = {'OBSERVED', 'EXPERT_REVIEWED'}

def validate(rows):
    if not isinstance(rows, list):
        raise ValueError('Expected JSON array')
    result=[]
    for i,r in enumerate(rows,1):
        if not isinstance(r,dict): raise ValueError(f'Row {i}: expected object')
        for k in ('scientific_name','source_name','source_url','attribute_name','value','evidence_type'):
            if k not in r or r[k] is None or r[k]=='': raise ValueError(f'Row {i}: missing {k}')
        if r['evidence_type'] not in ALLOWED: raise ValueError(f'Row {i}: unsupported evidence type')
        if urlparse(r['source_url']).scheme != 'https': raise ValueError(f'Row {i}: source_url must be HTTPS')
        if not isinstance(r['attribute_name'],str) or len(r['attribute_name'])>80: raise ValueError('Invalid attribute name')
        result.append(r)
    return result

def apply(rows,dsn):
    import psycopg
    from psycopg.types.json import Jsonb
    inserted=0
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            for r in rows:
                cur.execute('SELECT plant_id FROM horticulture.plant WHERE normalized_scientific_name=%s',(' '.join(r['scientific_name'].casefold().split()),))
                plant=cur.fetchone()
                if not plant: raise ValueError('Unknown plant: '+r['scientific_name'])
                cur.execute('SELECT data_source_id FROM horticulture.data_source WHERE source_name=%s',(r['source_name'],))
                source=cur.fetchone()
                if not source: raise ValueError('Unknown registered source: '+r['source_name'])
                # Stable, source-scoped identifier for a *specific* evidence record.
                key=json.dumps({'url':r['source_url'],'plant':r['scientific_name'],'attribute':r['attribute_name'],'value':r['value']},sort_keys=True,ensure_ascii=False)
                ext='curated:'+hashlib.sha256(key.encode()).hexdigest()
                cur.execute('''INSERT INTO horticulture.plant_source_record
                  (plant_id,data_source_id,external_plant_id,scientific_name_as_reported,source_url,raw_payload)
                  VALUES (%s,%s,%s,%s,%s,%s)
                  ON CONFLICT (data_source_id,external_plant_id) DO NOTHING''',
                  (plant[0],source[0],ext,r['scientific_name'],r['source_url'],Jsonb({'manifest_entry':r})))
                cur.execute('''SELECT plant_source_record_id,plant_id FROM horticulture.plant_source_record
                  WHERE data_source_id=%s AND external_plant_id=%s''',(source[0],ext))
                rec=cur.fetchone()
                if rec[1]!=plant[0]: raise ValueError('Source record plant mismatch')
                cur.execute('''SELECT 1 FROM horticulture.plant_attribute_evidence
                  WHERE plant_id=%s AND source_record_id=%s AND attribute_name=%s
                    AND evidence_type=%s AND value_as_reported=%s''',
                    (plant[0],rec[0],r['attribute_name'],r['evidence_type'],Jsonb(r['value'])))
                if not cur.fetchone():
                    cur.execute('''INSERT INTO horticulture.plant_attribute_evidence
                    (plant_id,attribute_name,data_source_id,source_record_id,value_as_reported,evidence_type)
                    VALUES (%s,%s,%s,%s,%s,%s)''',
                    (plant[0],r['attribute_name'],source[0],rec[0],Jsonb(r['value']),r['evidence_type']))
                    inserted+=1
    return inserted

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--manifest',required=True)
    p.add_argument('--apply',action='store_true')
    p.add_argument('--dsn',help='libpq DSN; defaults to GDAI_PLANT_DSN')
    a=p.parse_args()
    rows=validate(json.loads(Path(a.manifest).read_text(encoding='utf-8')))
    print(f'Validated {len(rows)} evidence rows; DRY RUN' if not a.apply else f'Validated {len(rows)} evidence rows')
    if a.apply:
        import os
        dsn=a.dsn or os.getenv('GDAI_PLANT_DSN')
        if not dsn: p.error('DSN required for --apply')
        print(f'Inserted {apply(rows,dsn)} new evidence rows')
if __name__=='__main__':main()
