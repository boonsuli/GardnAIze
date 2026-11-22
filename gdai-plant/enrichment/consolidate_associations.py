"""Consolidate exact sun/use evidence mappings, with explicit review and source rights.

Default is read-only. --apply requires --approved and confirmed source rights.
Never changes plant.quality_status or guesses unmapped categories.
"""
import argparse
import os
import sys
from collections import Counter

import psycopg
from psycopg.rows import dict_row

MAPPINGS = {
    'sun_exposure': ('sun_exposure', 'plant_sun_exposure', 'sun_exposure_id', {'FULL_SUN', 'PARTIAL_SHADE', 'FULL_SHADE'}),
    'garden_uses': ('plant_use', 'plant_use_assignment', 'plant_use_id', {'GROUND_COVER'}),
}


def run(dsn, apply=False, approved=False):
    if apply and not approved:
        raise ValueError('--apply requires --approved (human review and source rights confirmation)')
    counts = Counter()
    with psycopg.connect(dsn) as conn:
        with conn.transaction():
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute('''
                    SELECT e.plant_attribute_evidence_id AS evidence_id, e.plant_id,
                           p.scientific_name, e.attribute_name, e.value_as_reported,
                           e.evidence_type, ds.source_name, ds.commercial_reuse_allowed,
                           psr.source_url
                    FROM horticulture.plant_attribute_evidence e
                    JOIN horticulture.plant p ON p.plant_id=e.plant_id
                    JOIN horticulture.data_source ds ON ds.data_source_id=e.data_source_id
                    JOIN horticulture.plant_source_record psr
                      ON psr.plant_source_record_id=e.source_record_id
                    WHERE e.attribute_name IN ('sun_exposure', 'garden_uses')
                    ORDER BY e.plant_id, e.attribute_name, e.plant_attribute_evidence_id
                ''')
                rows = cur.fetchall()
                # Refuse ambiguous source values for same plant and attribute.
                by_attr = {}
                for r in rows:
                    by_attr.setdefault((r['plant_id'], r['attribute_name']), []).append(r)
                for key, entries in by_attr.items():
                    if len({tuple(sorted(x['value_as_reported'])) if isinstance(x['value_as_reported'], list)
                            else str(x['value_as_reported']) for x in entries}) > 1:
                        counts['conflicting_attribute_groups'] += 1
                        print('CONFLICT', key, file=sys.stderr)
                if counts['conflicting_attribute_groups']:
                    raise ValueError('Conflicting evidence values: manual review required')
                for r in rows:
                    if r['commercial_reuse_allowed'] is not True:
                        counts['SOURCE_RIGHTS_NOT_CONFIRMED'] += 1
                        print('SKIP rights:', r['scientific_name'], r['attribute_name'], r['source_name'])
                        continue
                    if r['evidence_type'] not in ('OBSERVED', 'EXPERT_REVIEWED'):
                        counts['UNSUPPORTED_EVIDENCE'] += 1
                        continue
                    if not isinstance(r['value_as_reported'], list):
                        counts['INVALID_VALUE'] += 1
                        continue
                    ref_table, join_table, id_col, allowed = MAPPINGS[r['attribute_name']]
                    for code in sorted(set(r['value_as_reported'])):
                        if code not in allowed:
                            counts['NO_EXACT_MAPPING'] += 1
                            print('SKIP unmapped:', r['scientific_name'], r['attribute_name'], code)
                            continue
                        cur.execute(f'SELECT {id_col} AS id FROM horticulture.{ref_table} WHERE code=%s', (code,))
                        ref = cur.fetchone()
                        if ref is None:
                            raise ValueError(f'Missing reference code: {ref_table}.{code}')
                        cur.execute(f'SELECT 1 FROM horticulture.{join_table} WHERE plant_id=%s AND {id_col}=%s',
                                    (r['plant_id'], ref['id']))
                        if cur.fetchone():
                            counts['ALREADY_PRESENT'] += 1
                            continue
                        counts['CANDIDATE'] += 1
                        print(('APPLY' if apply else 'PLAN'), r['scientific_name'], r['attribute_name'], code,
                              'evidence_id=', r['evidence_id'])
                        if apply:
                            if join_table == 'plant_sun_exposure':
                                cur.execute('''INSERT INTO horticulture.plant_sun_exposure
                                  (plant_id, sun_exposure_id, suitability) VALUES (%s,%s,'SUITABLE')
                                  ON CONFLICT (plant_id,sun_exposure_id) DO NOTHING''', (r['plant_id'], ref['id']))
                            else:
                                cur.execute('''INSERT INTO horticulture.plant_use_assignment
                                  (plant_id,plant_use_id) VALUES (%s,%s)
                                  ON CONFLICT (plant_id,plant_use_id) DO NOTHING''', (r['plant_id'], ref['id']))
    print('SUMMARY:', dict(counts))
    print('MODE:', 'APPLY' if apply else 'DRY_RUN')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dsn', default=os.getenv('GDAI_PLANT_DSN'))
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--approved', action='store_true')
    args = parser.parse_args()
    if not args.dsn:
        parser.error('DSN required (--dsn or GDAI_PLANT_DSN)')
    try:
        run(args.dsn, args.apply, args.approved)
    except (ValueError, psycopg.Error) as exc:
        print('ERROR:', exc, file=sys.stderr)
        sys.exit(1)
