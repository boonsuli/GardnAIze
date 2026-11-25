"""Conservative, auditable evidence-to-plant consolidation.

Only lossless foliage_persistence=EVERGREEN -> is_evergreen=True is supported.
No scraping, no automatic approval, no quality-status changes.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

QUERY = """
SELECT p.plant_id, p.scientific_name, p.quality_status, p.is_evergreen,
       e.plant_attribute_evidence_id AS evidence_id, e.attribute_name,
       e.value_as_reported, e.evidence_type, ds.source_name,
       ds.commercial_reuse_allowed, psr.source_url
FROM horticulture.plant p
JOIN horticulture.plant_attribute_evidence e ON e.plant_id=p.plant_id
JOIN horticulture.data_source ds ON ds.data_source_id=e.data_source_id
JOIN horticulture.plant_source_record psr ON psr.plant_source_record_id=e.source_record_id
WHERE e.attribute_name='foliage_persistence'
ORDER BY p.plant_id,e.plant_attribute_evidence_id
"""


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def build_plan(rows):
    groups = {}
    for r in rows:
        groups.setdefault(r['plant_id'], []).append(r)
    operations, skipped = [], []
    for plant_id, entries in sorted(groups.items()):
        first = entries[0]
        name = first['scientific_name']
        values = {canonical(r['value_as_reported']) for r in entries}
        if len(values) != 1:
            skipped.append({'plant_id': plant_id, 'plant': name, 'reason': 'CONFLICTING_EVIDENCE'})
            continue
        if first['value_as_reported'] != 'EVERGREEN':
            skipped.append({'plant_id': plant_id, 'plant': name, 'reason': 'NO_LOSSLESS_MAPPING'})
            continue
        if any(r['evidence_type'] not in ('OBSERVED', 'EXPERT_REVIEWED') for r in entries):
            skipped.append({'plant_id': plant_id, 'plant': name, 'reason': 'UNSUPPORTED_EVIDENCE'})
            continue
        if any(r['commercial_reuse_allowed'] is not True for r in entries):
            skipped.append({'plant_id': plant_id, 'plant': name, 'reason': 'SOURCE_RIGHTS_NOT_CONFIRMED'})
            continue
        current = first['is_evergreen']
        if current is True:
            skipped.append({'plant_id': plant_id, 'plant': name, 'reason': 'ALREADY_APPLIED'})
            continue
        if current is False:
            skipped.append({'plant_id': plant_id, 'plant': name, 'reason': 'CANONICAL_CONFLICT'})
            continue
        operations.append({
            'plant_id': plant_id, 'plant': name, 'field': 'is_evergreen',
            'old_value': None, 'new_value': True,
            'evidence_ids': [r['evidence_id'] for r in entries],
            'sources': sorted(set(r['source_name'] for r in entries)),
            'source_urls': sorted(set(r['source_url'] for r in entries)),
        })
    return {'schema_version': 1, 'operations': operations, 'skipped': skipped}


def fingerprint(plan):
    return hashlib.sha256(canonical(plan).encode('utf-8')).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--plan', metavar='PATH', help='Write read-only review plan')
    mode.add_argument('--apply', metavar='PATH', help='Apply a previously reviewed plan')
    parser.add_argument('--approved', action='store_true', help='Explicit human review of this exact plan')
    args = parser.parse_args()
    if args.apply and not args.approved:
        parser.error('--apply requires --approved')
    dsn = os.getenv('GDAI_PLANT_DSN')
    if not dsn:
        parser.error('GDAI_PLANT_DSN is required')

    with psycopg.connect(dsn) as conn:
        conn.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
        with conn.cursor(row_factory=dict_row) as cur:
            if args.apply:
                # Lock all affected plants; concurrent changes invalidate the snapshot.
                cur.execute('SELECT plant_id FROM horticulture.plant ORDER BY plant_id FOR UPDATE')
            cur.execute(QUERY)
            plan = build_plan(cur.fetchall())
            digest = fingerprint(plan)
            if args.plan:
                payload = {'plan': plan, 'sha256': digest}
                Path(args.plan).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
                print(f'DRY RUN: {len(plan["operations"])} candidates; {len(plan["skipped"])} skipped; SHA256={digest}')
                print('No database writes')
                return
            approved = json.loads(Path(args.apply).read_text(encoding='utf-8'))
            if approved.get('sha256') != fingerprint(approved.get('plan')):
                raise ValueError('Review plan checksum invalid')
            if approved['plan'] != plan:
                raise ValueError('Database evidence or canonical values changed since review; generate a new plan')
            if not plan['operations']:
                print('No pending approved operations; no changes')
                return
            for op in plan['operations']:
                cur.execute('''UPDATE horticulture.plant SET is_evergreen=TRUE
                               WHERE plant_id=%s AND is_evergreen IS NULL''', (op['plant_id'],))
                if cur.rowcount != 1:
                    raise ValueError(f'Concurrent change to plant {op["plant_id"]}')
            print(f'APPLIED: {len(plan["operations"])} plants; quality_status unchanged')
        # Commit on context exit, rollback automatically on exception.


if __name__ == '__main__':
    main()
