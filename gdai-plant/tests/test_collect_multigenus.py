import csv
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ingestion'))
from collect_multigenus import read_candidates, nursery_evidence, select

class CollectMultiGenusTests(unittest.TestCase):
    def test_filter_and_dedupe(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'input.csv'
            p.write_text('scientific_name,taxonomic_status,rank\nSalvia officinalis,ACCEPTED,SPECIES\nSalvia officinalis,ACCEPTED,SPECIES\nSalvia bogus,DOUBTFUL,SPECIES\nOrobanche salviae,ACCEPTED,SPECIES\n',encoding='utf-8')
            self.assertEqual(list(read_candidates([p])),['salvia officinalis'])
    def test_nursery_evidence_requires_recent_fr_listing(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'nursery.csv'
            p.write_text('scientific_name,nursery_name,country,product_url,observed_at,listed_for_sale\nSalvia officinalis,Example Nursery,FR,https://example.org/p,2026-11-01,true\nSalvia pratensis,Example Nursery,DE,https://example.org/p,2026-11-01,true\n',encoding='utf-8')
            self.assertEqual(list(nursery_evidence(p,date(2026,11,22))),['salvia officinalis'])
    def test_genus_cap(self):
        c={x.casefold():{'scientific_name':x,'genus':x.split()[0]} for x in ['Salvia officinalis','Salvia pratensis','Salvia nemorosa','Geranium macrorrhizum']}
        rows,_=select(c,{},4,1,require_nursery=False)
        self.assertEqual(len(rows),2)
        self.assertEqual(len({r['genus'] for r in rows}),2)
    def test_no_nursery_no_catalog(self):
        c={'salvia officinalis':{'scientific_name':'Salvia officinalis','genus':'Salvia'}}
        rows,_=select(c,{},300,5)
        self.assertEqual(rows,[])

if __name__=='__main__': unittest.main()
