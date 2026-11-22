"""Construct reproducible rule-derived garden/plant labels, without asserting expert truth."""
import argparse
import json
from pathlib import Path

FIELDS=['soil_drainage','water_availability','sun_hours_per_day','minimum_winter_temperature_c','evergreen_preferred','low_maintenance_preferred','privacy_screening_required']

def grade(g,p):
    # Missing attributes are unknown, never interpreted as compatible.
    reasons=[]
    if g.get('minimum_winter_temperature_c') is not None and p.get('minimum_hardiness_c') is not None:
        if float(g['minimum_winter_temperature_c']) < float(p['minimum_hardiness_c']): return 0,['hardiness']
    else: reasons.append('unknown_hardiness')
    score=1
    if g.get('evergreen_preferred') is True:
        if p.get('is_evergreen') is True: score+=1
        elif p.get('is_evergreen') is None: reasons.append('unknown_evergreen')
    if g.get('low_maintenance_preferred') is True:
        if p.get('maintenance_level')=='LOW':score+=1
        elif p.get('maintenance_level') is None:reasons.append('unknown_maintenance')
    if g.get('water_availability') and p.get('water_requirement'):
        if g['water_availability']=='LOW' and p['water_requirement']=='HIGH':return 0,['water_mismatch']
    else: reasons.append('unknown_water')
    if g.get('privacy_screening_required') is True: reasons.append('screening_not_evaluated')
    if g.get('soil_drainage'): reasons.append('drainage_not_evaluated')
    if g.get('sun_hours_per_day') is not None: reasons.append('sun_not_evaluated')
    # Conservative: never assign high relevance when key dimensions are unassessed.
    return min(score,2),reasons

def build(gardens,plants):
    return [{'garden_id':g['id'],'plant_id':p['plant_id'],'relevance_grade':grade(g,p)[0],
             'label_source':'RULE_DERIVED','assessment_notes':';'.join(grade(g,p)[1])}
            for g in gardens for p in plants]

def main():
    a=argparse.ArgumentParser()
    a.add_argument('--dsn',help='libpq DSN; defaults to GDAI_PLANT_DSN')
    a.add_argument('--out',required=True)
    a.add_argument('--include-pending',action='store_true',help='For diagnostics only; NOT for training')
    args=a.parse_args()
    import os,psycopg
    dsn=args.dsn or os.getenv('GDAI_PLANT_DSN')
    if not dsn:a.error('DSN required')
    with psycopg.connect(dsn) as conn:
      with conn.cursor(row_factory=psycopg.rows.dict_row) as c:
        c.execute('SELECT id,soil_drainage,water_availability,sun_hours_per_day,minimum_winter_temperature_c,evergreen_preferred,low_maintenance_preferred,privacy_screening_required FROM horticulture.ml_garden_sample')
        gardens=c.fetchall()
        sql='SELECT plant_id,minimum_hardiness_c,is_evergreen,maintenance_level,water_requirement FROM horticulture.plant WHERE quality_status=\'VALIDATED\''
        if args.include_pending:sql=sql.replace(" WHERE quality_status='VALIDATED'",'')
        c.execute(sql);plants=c.fetchall()
    pairs=build(gardens,plants)
    Path(args.out).write_text(json.dumps(pairs,indent=2,default=str),encoding='utf-8')
    print(f'{len(gardens)} gardens x {len(plants)} plants => {len(pairs)} diagnostic pairs; NO database changes')
    if args.include_pending:print('WARNING: pending plant attributes are incomplete; do not train on this output')
if __name__=='__main__':main()
