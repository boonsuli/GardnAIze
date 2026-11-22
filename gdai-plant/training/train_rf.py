"""Train a supervised baseline only from independently reviewed expert garden/plant labels."""
import argparse
import json
from pathlib import Path

FEATURES=['area_m2','soil_ph','sun_hours_per_day','minimum_winter_temperature_c','maximum_summer_temperature_c','evergreen_preferred','low_maintenance_preferred','privacy_screening_required','minimum_hardiness_c','maximum_height_cm','is_evergreen','is_drought_tolerant']

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--dsn',help='libpq DSN; defaults to GDAI_PLANT_DSN')
    p.add_argument('--out',required=True)
    p.add_argument('--min-gardens',type=int,default=10)
    a=p.parse_args()
    import os,psycopg
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import make_pipeline
    from sklearn.model_selection import GroupShuffleSplit
    from sklearn.metrics import classification_report,balanced_accuracy_score
    import joblib
    dsn=a.dsn or os.getenv('GDAI_PLANT_DSN')
    if not dsn:p.error('DSN required')
    q='''SELECT a.ml_garden_sample_id AS garden_id,a.relevance_grade,
        g.area_m2,g.soil_ph,g.sun_hours_per_day,g.minimum_winter_temperature_c,g.maximum_summer_temperature_c,
        g.evergreen_preferred,g.low_maintenance_preferred,g.privacy_screening_required,
        p.minimum_hardiness_c,p.maximum_height_cm,p.is_evergreen,p.is_drought_tolerant
        FROM horticulture.ml_garden_plant_assessment a
        JOIN horticulture.ml_garden_sample g ON g.id=a.ml_garden_sample_id
        JOIN horticulture.plant p ON p.plant_id=a.plant_id
        WHERE a.label_source='EXPERT' AND g.source_kind='CURATED' AND p.quality_status='VALIDATED' '''
    with psycopg.connect(dsn) as conn:
      with conn.cursor() as cur:
        cur.execute(q)
        names=[d.name for d in cur.description]
        df=pd.DataFrame(cur.fetchall(),columns=names)
    if df.empty:raise SystemExit('No independent EXPERT labels on CURATED gardens and VALIDATED plants; training blocked')
    groups=df['garden_id']
    if groups.nunique()<a.min_gardens:raise SystemExit(f'Need at least {a.min_gardens} distinct curated gardens, got {groups.nunique()}')
    if df['relevance_grade'].nunique()<2:raise SystemExit('Need at least 2 relevance classes')
    x=df[FEATURES].copy()
    for f in FEATURES:x[f]=pd.to_numeric(x[f],errors='coerce')
    y=df['relevance_grade'].astype(int)
    train,test=next(GroupShuffleSplit(n_splits=1,test_size=.25,random_state=42).split(x,y,groups))
    if y.iloc[train].nunique()<2 or y.iloc[test].nunique()<2:raise SystemExit('Group split lacks >=2 classes in both sets; collect more diverse expert labels')
    model=make_pipeline(SimpleImputer(strategy='constant',fill_value=-999),RandomForestClassifier(n_estimators=200,min_samples_leaf=2,random_state=42,class_weight='balanced'))
    model.fit(x.iloc[train],y.iloc[train]);pred=model.predict(x.iloc[test])
    metrics={'balanced_accuracy':balanced_accuracy_score(y.iloc[test],pred),'classification_report':classification_report(y.iloc[test],pred,output_dict=True,zero_division=0),'train_gardens':int(groups.iloc[train].nunique()),'test_gardens':int(groups.iloc[test].nunique()),'train_rows':len(train),'test_rows':len(test),'features':FEATURES,'label_source':'EXPERT'}
    out=Path(a.out);out.parent.mkdir(parents=True,exist_ok=True)
    joblib.dump(model,out)
    out.with_suffix('.metrics.json').write_text(json.dumps(metrics,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in metrics.items() if k!='classification_report'},indent=2))
if __name__=='__main__':main()
