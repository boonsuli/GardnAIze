"""Consolidate an explicitly approved evergreen fact; conservative V1."""
import argparse
import os
import sys
import psycopg

SQL = """
SELECT e.value_as_reported, e.evidence_type, ds.source_name, psr.source_url
FROM horticulture.plant_attribute_evidence e
JOIN horticulture.data_source ds ON ds.data_source_id = e.data_source_id
JOIN horticulture.plant_source_record psr ON psr.plant_source_record_id = e.source_record_id
WHERE e.plant_id = %s AND e.attribute_name = 'foliage_persistence'
"""

def run(dsn, apply, approved):
    with psycopg.connect(dsn) as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                cur.execute("SELECT plant_id, is_evergreen, quality_status FROM horticulture.plant WHERE normalized_scientific_name = %s FOR UPDATE", ('vinca minor',))
                row = cur.fetchone()
                if row is None:
                    raise ValueError('Vinca minor not found')
                plant_id, current, status = row
                cur.execute(SQL, (plant_id,))
                evidence = cur.fetchall()
                if not evidence:
                    raise ValueError('No foliage evidence')
                if any(v != 'EVERGREEN' for v, *_ in evidence):
                    raise ValueError('Conflicting or unrecognized foliage evidence')
                if not any(t == 'OBSERVED' and s == 'RHS' and u == 'https://www.rhs.org.uk/plants/18973/vinca-minor/details' for v,t,s,u in evidence):
                    raise ValueError('Expected RHS evidence missing')
                if current is False:
                    raise ValueError('Existing value false; refusing overwrite')
                print(f'Plant: Vinca minor; current={current}; proposed=True; status={status}; evidence={len(evidence)}')
                if not apply:
                    print('DRY RUN: no changes')
                    return
                if not approved:
                    raise ValueError('--apply requires --approved')
                if current is True:
                    print('ALREADY APPLIED: no changes')
                    return
                cur.execute('UPDATE horticulture.plant SET is_evergreen = TRUE WHERE plant_id = %s AND is_evergreen IS NULL', (plant_id,))
                if cur.rowcount != 1:
                    raise ValueError('Concurrent change detected')
                print('APPLIED: is_evergreen=True; quality_status unchanged')

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--dsn', default=os.getenv('GDAI_PLANT_DSN'))
    p.add_argument('--apply', action='store_true')
    p.add_argument('--approved', action='store_true', help='Human reviewer confirms the fact and source usage permissions')
    a=p.parse_args()
    if not a.dsn: p.error('Set GDAI_PLANT_DSN or pass --dsn')
    try: run(a.dsn, a.apply, a.approved)
    except (ValueError, psycopg.Error) as e:
        print(f'ERROR: {e}', file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__': main()
