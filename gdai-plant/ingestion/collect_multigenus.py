#!/usr/bin/env python3
"""Conservative GBIF taxonomy discovery + nursery evidence based catalog selection.

Discovery is not proof of nursery stock or climate suitability. Default: no network.
"""
import argparse
import csv
import json
import re
import time
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API = 'https://api.gbif.org/v1'
CATEGORIES = {
    'SHRUB': ['Cornus','Viburnum','Philadelphus','Spiraea','Weigela','Hydrangea','Deutzia','Potentilla','Ribes','Euonymus','Ilex','Berberis','Cotoneaster','Syringa','Forsythia','Pyracantha','Escallonia','Photinia'],
    'PERENNIAL': ['Geranium','Salvia','Nepeta','Echinacea','Rudbeckia','Achillea','Helenium','Aster','Campanula','Heuchera','Helleborus','Hosta','Astilbe','Bergenia','Euphorbia','Penstemon','Phlox','Coreopsis','Gaura'],
    'GRASS': ['Miscanthus','Panicum','Molinia','Calamagrostis','Deschampsia','Festuca','Stipa','Carex','Pennisetum','Hakonechloa'],
    'TREE': ['Acer','Amelanchier','Carpinus','Betula','Sorbus','Malus','Prunus','Cercis','Tilia','Liquidambar','Magnolia','Crataegus'],
    'GROUNDCOVER': ['Vinca','Ajuga','Pachysandra','Waldsteinia','Lamium','Epimedium','Thymus','Sedum','Saxifraga','Cerastium','Armeria'],
    'CLIMBER': ['Clematis','Lonicera','Hedera','Wisteria','Parthenocissus','Jasminum','Trachelospermum','Humulus'],
}
TARGETS = {'SHRUB':80,'PERENNIAL':90,'GRASS':35,'TREE':35,'GROUNDCOVER':40,'CLIMBER':20}
BINOMIAL = re.compile(r'^[A-Z][a-zA-Z-]+ [a-z][a-z-]+$')


def request_json(path, params):
    url = f'{API}{path}?{urlencode(params)}'
    req = Request(url, headers={'User-Agent':'GardnAIze-V1/0.1 (taxonomic candidate discovery)', 'Accept':'application/json'})
    for attempt in range(3):
        try:
            with urlopen(req, timeout=20) as response:
                return json.load(response)
        except Exception:
            if attempt == 2: raise
            time.sleep(1.5 * (attempt+1))


def discover_genus(genus, max_results=100):
    match = request_json('/species/match', {'name':genus,'strict':'true'})
    if not (match.get('matchType') == 'EXACT' and match.get('rank') == 'GENUS'
            and match.get('status') == 'ACCEPTED'
            and match.get('canonicalName') == genus and match.get('usageKey')):
        return []
    key = match['usageKey']
    found = []
    for offset in range(0, max_results, 100):
        payload = request_json('/species/search', {'highertaxon_key':key,'rank':'SPECIES','status':'ACCEPTED',
                                                    'limit':min(100,max_results-offset),'offset':offset})
        results = payload.get('results', [])
        for row in results:
            name = row.get('canonicalName','')
            if (row.get('rank') == 'SPECIES' and row.get('taxonomicStatus') == 'ACCEPTED'
                and row.get('genus') == genus and BINOMIAL.fullmatch(name)
                and row.get('key')):
                found.append({'scientific_name':name,'external_id':str(row['key']),
                              'source_url':f'https://www.gbif.org/species/{row["key"]}',
                              'source_key':'GBIF','genus':genus})
        if payload.get('endOfRecords') or not results: break
        time.sleep(0.15)
    return found


def read_candidates(paths):
    result = {}
    for path in paths:
        with Path(path).open(encoding='utf-8-sig',newline='') as f:
            for row in csv.DictReader(f):
                name = (row.get('scientific_name') or '').strip()
                if not BINOMIAL.fullmatch(name): continue
                genus = name.split()[0]
                if genus not in {g for gs in CATEGORIES.values() for g in gs}: continue
                if row.get('taxonomic_status') and row['taxonomic_status'] != 'ACCEPTED': continue
                if row.get('rank') and row['rank'] != 'SPECIES': continue
                if row.get('canonical_name') and row['canonical_name'] != name: continue
                result.setdefault(name.casefold(), {'scientific_name':name,'genus':genus,
                    'external_id':row.get('external_id',''), 'source_url':row.get('source_url',''),
                    'source_key':row.get('source_key','')})
    return result


def nursery_evidence(path, as_of, max_age_days=180):
    """Explicit, recent supplier listing evidence; not a guarantee of real-time stock."""
    evidence = {}
    if not path: return evidence
    with Path(path).open(encoding='utf-8-sig',newline='') as f:
        reader = csv.DictReader(f)
        required = {'scientific_name','nursery_name','country','product_url','observed_at','listed_for_sale'}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError('Nursery CSV missing columns: '+', '.join(sorted(required-set(reader.fieldnames or []))))
        for row in reader:
            try: age = (as_of - date.fromisoformat(row['observed_at'])).days
            except (ValueError,TypeError): continue
            if not (0 <= age <= max_age_days): continue
            if row['country'].strip().upper() != 'FR': continue
            if row['listed_for_sale'].strip().lower() not in ('true','1','yes'): continue
            if not row['product_url'].startswith('https://'): continue
            if not row['nursery_name'].strip(): continue
            name = row['scientific_name'].strip().casefold()
            evidence.setdefault(name, []).append(row)
    return evidence


def select(candidates, evidence, target, max_per_genus, require_nursery=True):
    if target < 1 or max_per_genus < 1: raise ValueError('target and max_per_genus must be positive')
    by_cat = {cat:[] for cat in CATEGORIES}
    for item in candidates.values():
        if require_nursery and item['scientific_name'].casefold() not in evidence: continue
        cat = next((cat for cat, genera in CATEGORIES.items() if item['genus'] in genera),None)
        if cat: by_cat[cat].append(item)
    for items in by_cat.values(): items.sort(key=lambda x:x['scientific_name'].casefold())
    selected, counts, per_genus = [], Counter(), Counter()
    # Round-robin categories and genera, preventing one genus from dominating.
    enforce_quotas = True
    while len(selected) < target:
        progress = False
        for cat in CATEGORIES:
            if len(selected) >= target: break
            quota = max(1, round(TARGETS[cat]*target/300))
            if enforce_quotas and counts[cat] >= quota: continue
            eligible = [x for x in by_cat[cat] if per_genus[x['genus']] < max_per_genus]
            if not eligible: continue
            # Prefer least represented genus, then name for deterministic output.
            item = min(eligible,key=lambda x:(per_genus[x['genus']],x['scientific_name'].casefold()))
            by_cat[cat].remove(item)
            selected.append(dict(item,category=cat,nursery_evidence_count=len(evidence.get(item['scientific_name'].casefold(),[]))))
            counts[cat] += 1; per_genus[item['genus']] += 1; progress = True
        if not progress:
            if enforce_quotas:
                enforce_quotas = False
                continue
            break
    return selected, dict(counts)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',action='append',default=[],help='Existing candidate CSV, repeatable')
    p.add_argument('--online',action='store_true',help='Query GBIF for all configured genera')
    p.add_argument('--nursery-csv',help='CSV of explicit recent French nursery listings')
    p.add_argument('--target',type=int,choices=[300,3000],default=300)
    p.add_argument('--max-per-genus',type=int,default=None)
    p.add_argument('--allow-unverified',action='store_true',help='Diagnostic only; no availability claims')
    p.add_argument('--out-dir',default='gdai-plant/data')
    p.add_argument('--as-of',type=date.fromisoformat,default=date.today())
    args = p.parse_args(argv)
    candidates = read_candidates(args.input)
    errors = {}
    if args.online:
        for genus in dict.fromkeys(g for genera in CATEGORIES.values() for g in genera):
            try:
                found = discover_genus(genus, max_results=100)
                for item in found: candidates.setdefault(item['scientific_name'].casefold(),item)
                print(f'{genus}: {len(found)} candidates')
            except Exception as exc:
                errors[genus] = str(exc)
                print(f'WARNING {genus}: {exc}')
    evidence = nursery_evidence(args.nursery_csv,args.as_of) if args.nursery_csv else {}
    selected, counts = select(candidates,evidence,args.target,
                              args.max_per_genus or (5 if args.target==300 else 50),
                              require_nursery=not args.allow_unverified)
    out = Path(args.out_dir); out.mkdir(parents=True,exist_ok=True)
    # Never overwrite a verified catalog with a partial one.
    report = {'target':args.target,'candidate_count':len(candidates),'selected':len(selected),
              'categories':counts,'nursery_evidence_names':len(evidence),'errors':errors,
              'availability_verified':not args.allow_unverified,
              'warning':'Nursery listing is historical evidence, not live stock confirmation.'}
    (out/f'catalog-{args.target}-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    (out/f'catalog-{args.target}-audit.json').write_text(json.dumps(selected,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    if len(selected)==args.target:
        path=out/f'plants-{args.target}.json'
        path.write_text(json.dumps([{'scientific_name':x['scientific_name']} for x in selected],indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        print(f'CREATED {path}')
    else:
        print(f'NOT CREATED plants-{args.target}.json: {len(selected)}/{args.target} qualified candidates')
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return 0 if len(selected)==args.target else 2

if __name__=='__main__': raise SystemExit(main())
