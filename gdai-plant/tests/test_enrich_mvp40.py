import importlib.util
import unittest
from pathlib import Path

path=Path(__file__).resolve().parents[1]/'scripts'/'enrich_mvp40.py'
spec=importlib.util.spec_from_file_location('enrich_mvp40',path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
P=[{'scientific_name':'Viburnum tinus','candidate_category':'SHRUB'}]
class EnrichmentTests(unittest.TestCase):
    def test_no_evidence_is_pending(self):
        rows,errors=m.evaluate(P,[],[])
        self.assertEqual(rows[0]['review_status'],'PENDING')
        self.assertEqual(rows[0]['documented_fields'],0)
    def test_unlicensed_evidence_rejected(self):
        evidence=[dict(scientific_name='Viburnum tinus',field='evergreen',value='true',source_url='https://example.org',source_license='UNKNOWN',commercial_reuse_allowed='false',reviewer='expert',reviewed_at='2026-11-22')]
        rows,errors=m.evaluate(P,evidence,[])
        self.assertEqual(rows[0]['documented_fields'],0)
        self.assertEqual(len(errors),1)
    def test_accepted_evidence(self):
        evidence=[dict(scientific_name='Viburnum tinus',field='evergreen',value='true',source_url='https://example.org',source_license='CC0-1.0',commercial_reuse_allowed='true',reviewer='expert',reviewed_at='2026-11-22')]
        rows,errors=m.evaluate(P,evidence,[])
        self.assertEqual(rows[0]['evergreen'],'true')
        self.assertFalse(errors)
    def test_unknown_plant_rejected(self):
        evidence=[dict(scientific_name='unknown',field='evergreen',value='true',source_url='https://example.org',source_license='CC0-1.0',commercial_reuse_allowed='true',reviewer='expert',reviewed_at='2026-11-22')]
        rows,errors=m.evaluate(P,evidence,[])
        self.assertEqual(len(errors),1)
