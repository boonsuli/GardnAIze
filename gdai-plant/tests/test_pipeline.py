import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'enrichment'))
sys.path.insert(0,str(ROOT/'matching'))
from import_evidence import validate
from build_pairs import grade,build
class PipelineTests(unittest.TestCase):
 def test_reject_unattributed(self):
  with self.assertRaises(ValueError):validate([{'scientific_name':'Vinca minor'}])
 def test_accept_reviewed_fact(self):
  self.assertEqual(len(validate([{'scientific_name':'Vinca minor','source_name':'RHS','source_url':'https://example.org/plant','attribute_name':'water','value':'LOW','evidence_type':'OBSERVED'}])),1)
 def test_hardiness_exclusion(self):
  self.assertEqual(grade({'minimum_winter_temperature_c':-15},{'minimum_hardiness_c':-5})[0],0)
 def test_no_fabricated_top_grade(self):
  self.assertLess(grade({'evergreen_preferred':True},{'is_evergreen':True})[0],3)
 def test_pair_provenance(self):
  rows=build([{'id':1}],[{'plant_id':2}]);self.assertEqual(rows[0]['label_source'],'RULE_DERIVED')
if __name__=='__main__':unittest.main()
