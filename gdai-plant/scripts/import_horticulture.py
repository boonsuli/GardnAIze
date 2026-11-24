#!/usr/bin/env python3
"""Import research staging into existing horticulture tables, conservatively."""
import argparse, os, json, hashlib
from collections import Counter
from urllib.parse import urlsplit
import psycopg
from psycopg.types.json import Jsonb

FIELDS={'sun_exposure','soil_drainage','water_need','hardiness_min_c','height_cm','spread_cm','evergreen'}
def norm(s): return ' '.join(s.split()).casefold()
def digest(s): return hashlib.sha256(s.encode()).hexdigest()[:32]
def main():
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');p.add_argument('--dsn',default=os.getenv('GARDNAIZE_ML_DATABASE_URL'));a=p.parse_args()
 if not a.dsn:p.error('Set GARDNAIZE_ML_DATABASE_URL or --dsn')
 try:
  with psycopg.connect(a.dsn) as conn:
   with conn.cursor() as c:
    c.execute('SELECT scientific_name,field,observed_value,original_range,source_url,source_license,commercial_reuse_allowed,reviewer,reviewed_at,review_status,notes FROM gardnaize_import_stage.plant_trait_evidence ORDER BY scientific_name,field')
    columns=[d.name for d in c.description];data=[dict(zip(columns,row)) for row in c.fetchall()]
    keys={(norm(r['scientific_name']),r['field']) for r in data};names={r['scientific_name'] for r in data}
    if not data or len(keys)!=len(data) or any(r['field'] not in FIELDS or not (r['observed_value'] or r['original_range']) for r in data):raise ValueError('Invalid or duplicate staging evidence')
    if any({r['field'] for r in data if r['scientific_name']==name}!=FIELDS for name in names):raise ValueError('Incomplete species: expected seven traits each')
    print(json.dumps({'species':len(names),'traits':len(data),'missing_source_url':sum(not r['source_url'] for r in data),'mode':'APPLY' if a.apply else 'DRY_RUN'},indent=2))
    if not a.apply:return
    c.execute('SELECT pg_advisory_xact_lock(624818,1)')
    ids={};created=0
    for name in sorted(names):
     c.execute('SELECT plant_id,scientific_name FROM horticulture.plant WHERE normalized_scientific_name=%s',(norm(name),));row=c.fetchone()
     if row:
      if row[1]!=name:raise ValueError(f'Normalized name collision: {name} / {row[1]}')
      ids[name]=row[0]
     else:
      c.execute("INSERT INTO horticulture.plant(scientific_name,normalized_scientific_name,quality_status,ready_for_matching) VALUES (%s,%s,'PENDING',false) RETURNING plant_id",(name,norm(name)))
      ids[name]=c.fetchone()[0];created+=1
    sources={};records={};inserted=updated=0
    for r in data:
     name=r['scientific_name'];url=r['source_url'].strip();host=urlsplit(url).hostname if url else None
     if url and (urlsplit(url).scheme not in ('https','http') or not host):raise ValueError(f'Invalid URL: {url}')
     source_name='GardnAIze research - '+(host.lower() if host else 'unattributed')
     if source_name not in sources:
      c.execute('INSERT INTO horticulture.data_source(source_name,base_url,license_name,commercial_reuse_allowed) VALUES (%s,%s,%s,NULL) ON CONFLICT(source_name) DO UPDATE SET source_name=EXCLUDED.source_name RETURNING data_source_id',(source_name,('https://'+host if host else None),'UNKNOWN'))
      sources[source_name]=c.fetchone()[0]
     sid=sources[source_name];key=(name,sid,url)
     if key not in records:
      external='gdai-research-v1:'+digest(name+'|'+url+'|'+source_name)
      c.execute('''INSERT INTO horticulture.plant_source_record(plant_id,data_source_id,external_plant_id,scientific_name_as_reported,source_url,raw_payload,normalization_warnings)
       VALUES (%s,%s,%s,%s,%s,%s,%s)
       ON CONFLICT(data_source_id,external_plant_id) DO UPDATE SET plant_id=EXCLUDED.plant_id,source_url=EXCLUDED.source_url,raw_payload=EXCLUDED.raw_payload,normalization_warnings=EXCLUDED.normalization_warnings
       RETURNING plant_source_record_id''',(ids[name],sid,external,name,url or None,Jsonb({'origin':'gardnaize_import_stage','source_url':url or None,'rights':'UNVERIFIED'}),Jsonb(['SOURCE_URL_MISSING'] if not url else [])))
      records[key]=c.fetchone()[0]
     rid=records[key]
     value={k:r[k] for k in ('observed_value','original_range','source_url','source_license','commercial_reuse_allowed','reviewer','reviewed_at','review_status','notes')}
     value['import_pipeline']='gdai-research-v1'
     c.execute('''SELECT plant_attribute_evidence_id FROM horticulture.plant_attribute_evidence WHERE plant_id=%s AND attribute_name=%s AND source_record_id=%s AND evidence_type='OBSERVED' AND value_as_reported->>'import_pipeline'='gdai-research-v1' ORDER BY plant_attribute_evidence_id FOR UPDATE''',(ids[name],r['field'],rid))
     matches=[x[0] for x in c.fetchall()]
     if len(matches)>1:raise ValueError(f'Duplicate importer-owned evidence: {name}/{r["field"]}')
     if matches:
      c.execute('UPDATE horticulture.plant_attribute_evidence SET value_as_reported=%s,data_source_id=%s WHERE plant_attribute_evidence_id=%s',(Jsonb(value),sid,matches[0]));updated+=1
     else:
      c.execute("INSERT INTO horticulture.plant_attribute_evidence(plant_id,attribute_name,data_source_id,source_record_id,value_as_reported,evidence_type) VALUES (%s,%s,%s,%s,%s,'OBSERVED')",(ids[name],r['field'],sid,rid,Jsonb(value)));inserted+=1
    print(json.dumps({'plants_created':created,'plants_matched':len(names)-created,'evidence_inserted':inserted,'evidence_updated':updated,'merchant_offers_created':0},indent=2))
   conn.commit()
  print('COMMITTED: plant operational fields unchanged; readiness unchanged.')
 except (psycopg.Error,ValueError) as exc:raise SystemExit(f'IMPORT ABORTED (rolled back): {exc}')
if __name__=='__main__':main()
