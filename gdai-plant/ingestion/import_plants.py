#!/usr/bin/env python3
"""Auditable, conservative plant-catalog import. Dry run unless --apply."""
import argparse
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

GBIF_URL = 'https://api.gbif.org/v1/species/match'


def normalize(name):
    return ' '.join(name.casefold().split())


def valid_horticultural_name(name):
    """Accept species, botanical varieties and named cultivars."""
    if not isinstance(name, str):
        return False

    genus = r"[A-Z][a-zA-Z-]*"
    epithet = r"[a-z][a-z-]*"
    cultivar = r"'[^']+'"

    patterns = [
        rf"{genus}\s+{epithet}",
        rf"{genus}\s+{epithet}\s+{cultivar}",
        rf"{genus}\s+{cultivar}",
        rf"{genus}\s+{epithet}\s+var\.\s+{epithet}",
    ]

    return any(
        re.fullmatch(pattern, name.strip()) is not None
        for pattern in patterns
    )


def parse_catalog(path):
    rows = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(rows, list):
        raise ValueError('Catalog must be a JSON array')
    result = []
    seen = set()
    for i, row in enumerate(rows, 1):
        name = row.get('scientific_name')
        if not valid_horticultural_name(name):
            raise ValueError(
                f"Row {i}: invalid botanical or horticultural scientific_name"
            )
        key = normalize(name)
        if key in seen:
            raise ValueError(f'Duplicate name: {name}')
        seen.add(key)
        result.append({'scientific_name': name.strip(), 'normalized_scientific_name': key, 'pilot': row})
    return result


def gbif_match(name):
    url = GBIF_URL + '?' + urlencode({'name': name, 'strict': 'true'})
    req = Request(url, headers={'User-Agent': 'GardnAIze-Plant-V1/0.1 (taxonomy verification)', 'Accept': 'application/json'})
    with urlopen(req, timeout=12) as response:
        data = json.load(response)
    return {
        'matchType': data.get('matchType'), 'rank': data.get('rank'),
        'status': data.get('status'), 'scientificName': data.get('scientificName'),
        'canonicalName': data.get('canonicalName'), 'usageKey': data.get('usageKey'),
        'confidence': data.get('confidence'), 'url': url,
    }


def verified_species(item):
    g = item.get('gbif') or {}
    # Conservative: GBIF accepted species only, exact canonical binomial match.
    return (g.get('matchType') == 'EXACT' and g.get('rank') == 'SPECIES'
            and g.get('status') == 'ACCEPTED'
            and normalize(g.get('canonicalName') or '') == item['normalized_scientific_name'])


def prepare(path, online=False):
    out = []
    for row in parse_catalog(path):
        item = dict(row)
        item['gbif'] = None
        item['review_reason'] = 'TAXONOMY_NOT_CHECKED'
        if online:
            try:
                item['gbif'] = gbif_match(row['scientific_name'])
                item['review_reason'] = 'TAXONOMY_MATCHED' if verified_species(item) else 'TAXONOMY_REVIEW_REQUIRED'
            except Exception as exc:
                item['review_reason'] = 'GBIF_LOOKUP_FAILED'
                item['lookup_error'] = str(exc)
            time.sleep(0.12)
        out.append(item)
    return out


def write_db(rows, dsn):
    try:
        import psycopg
    except ImportError as exc:
        raise SystemExit('Install psycopg[binary] for --apply') from exc
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute('SELECT data_source_id FROM horticulture.data_source WHERE source_name=%s', ('GBIF',))
            src = cur.fetchone()
            if src is None:
                raise RuntimeError('GBIF missing from horticulture.data_source')
            source_id = src[0]
            for item in rows:
                # Only botanical identity is imported. Pilot care properties are NOT verified.
                cur.execute('''INSERT INTO horticulture.plant
                        (scientific_name, normalized_scientific_name, quality_status, validation_notes)
                    VALUES (%s, %s, 'PENDING', %s)
                    ON CONFLICT (normalized_scientific_name) DO NOTHING''',
                    (item['scientific_name'], item['normalized_scientific_name'],
                     'Pilot catalog; horticultural attributes not yet verified. ' + item['review_reason']))
                cur.execute('SELECT plant_id FROM horticulture.plant WHERE normalized_scientific_name=%s',
                            (item['normalized_scientific_name'],))
                plant_id = cur.fetchone()[0]
                if verified_species(item):
                    g = item['gbif']
                    cur.execute('''INSERT INTO horticulture.plant_source_record
                            (plant_id, data_source_id, external_plant_id, scientific_name_as_reported,
                             source_url, raw_payload)
                        VALUES (%s,%s,%s,%s,%s,%s::jsonb)
                        ON CONFLICT (data_source_id, external_plant_id) DO NOTHING''',
                        (plant_id, source_id, str(g['usageKey']), g['scientificName'],
                         g['url'], json.dumps(g)))
    return len(rows)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalog', required=True, help='Existing pilot plants.json')
    p.add_argument('--online', action='store_true', help='Query GBIF species match API')
    p.add_argument('--report', default='plant_import_report.json')
    p.add_argument('--apply', action='store_true', help='Write PENDING plants and verified GBIF matches')
    p.add_argument('--dsn', help='PostgreSQL DSN; alternatively use GDAI_PLANT_DSN')
    args = p.parse_args(argv)
    rows = prepare(args.catalog, args.online)
    Path(args.report).write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Prepared {len(rows)} plants; verified GBIF exact accepted species: {sum(verified_species(r) for r in rows)}')
    print(f'Report: {args.report}')
    if args.apply:
        import os
        dsn = args.dsn or os.environ.get('GDAI_PLANT_DSN')
        if not dsn:
            p.error('--apply requires --dsn or GDAI_PLANT_DSN')
        print(f'Imported/rechecked {write_db(rows, dsn)} PENDING plants')
    else:
        print('DRY RUN: PostgreSQL unchanged')
    return 0


if __name__ == '__main__':
    sys.exit(main())
