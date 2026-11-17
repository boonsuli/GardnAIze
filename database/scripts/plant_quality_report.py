"""Quality report for multisource plant candidates; read-only and no fabricated labels."""
import argparse,os,json
from pathlib import Path
def main():
 p=argparse.ArgumentParser()
 p.add_argument("--output",type=Path)
 a=p.parse_args()
 import psycopg
 dsn=os.environ["GARDNAIZE_ML_DATABASE_URL"].replace("postgresql+psycopg://","postgresql://",1)
 with psycopg.connect(dsn) as c:
  with c.cursor() as cur:
   cur.execute("""SELECT COUNT(*),COUNT(*) FILTER(WHERE quality_status='VALIDATED'),
    COUNT(*) FILTER(WHERE ready_for_matching),
    COUNT(*) FILTER(WHERE outdoor_confirmed IS TRUE AND temperate_confirmed IS TRUE),
    COUNT(*) FILTER(WHERE exposure IS NOT NULL AND soil_texture IS NOT NULL
                       AND water_requirement IS NOT NULL AND hardiness_min_c IS NOT NULL)
    FROM horticulture.ml_plant_catalog""")
   counts=cur.fetchone()
   cur.execute("""SELECT source_key,COUNT(*) FROM horticulture.ml_plant_source_record
     GROUP BY source_key ORDER BY COUNT(*) DESC""")
   sources=cur.fetchall()
   cur.execute("""SELECT COUNT(*),COUNT(*) FILTER(WHERE rights_reviewed),
     COUNT(*) FILTER(WHERE local_uri IS NOT NULL)
     FROM horticulture.ml_plant_image""")
   images=cur.fetchone()
   cur.execute("""SELECT COUNT(*) FROM (SELECT lower(scientific_name),COUNT(*)
     FROM horticulture.ml_plant_catalog GROUP BY lower(scientific_name)
     HAVING COUNT(*)>1) duplicates""")
   shared_names=cur.fetchone()[0]
 result={"total":counts[0],"validated":counts[1],"ready_for_matching":counts[2],
         "outdoor_temperate_confirmed":counts[3],"complete_core_attributes":counts[4],
         "sources":dict(sources),"images":{"metadata":images[0],"rights_reviewed":images[1],
         "downloaded":images[2]},"scientific_names_with_multiple_rows":shared_names}
 print(json.dumps(result,ensure_ascii=False,indent=2))
 if a.output:
  a.output.parent.mkdir(parents=True,exist_ok=True)
  a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
if __name__=="__main__":main()
