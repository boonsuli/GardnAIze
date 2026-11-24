import unittest
from api.recommendation_engine import Candidate, rank

class RecommendationEngineTests(unittest.TestCase):
    def test_excludes_pending_by_default(self):
        self.assertEqual(rank({'evergreen_preferred': True}, [Candidate(1,'A',is_evergreen=True)]), [])
    def test_hardiness_exclusion(self):
        p=Candidate(1,'A',minimum_hardiness_c=-5,quality_status='VALIDATED')
        self.assertEqual(rank({'minimum_winter_temperature_c':-10},[p]), [])
    def test_sun_exclusion(self):
        p=Candidate(1,'A',sun_exposures=('FULL_SUN',),quality_status='VALIDATED')
        self.assertEqual(rank({'sun_exposure':'FULL_SHADE'},[p]), [])
    def test_no_evidence_no_recommendation(self):
        self.assertEqual(rank({'sun_exposure':'FULL_SUN'},[Candidate(1,'A',quality_status='VALIDATED')]),[])
    def test_stable_rank_and_limit(self):
        ps=[Candidate(2,'Z',is_evergreen=True,quality_status='VALIDATED'),Candidate(1,'A',is_evergreen=True,quality_status='VALIDATED')]
        self.assertEqual([x['plant_id'] for x in rank({'evergreen_preferred':True},ps,limit=1)],[1])
    def test_pending_demo_is_flagged(self):
        result=rank({'evergreen_preferred':True},[Candidate(1,'A',is_evergreen=True)],allow_pending=True)
        self.assertIn('PENDING_REVIEW_DEMO_ONLY',result[0]['warnings'])
    def test_drought_incompatibility(self):
        p=Candidate(1,'A',is_drought_tolerant=False,quality_status='VALIDATED')
        self.assertEqual(rank({'water_availability':'LOW'},[p]),[])
    def test_unknown_water_not_treated_as_compatible(self):
        p=Candidate(1,'A',quality_status='VALIDATED')
        self.assertEqual(rank({'water_availability':'LOW'},[p]),[])

if __name__=='__main__': unittest.main()
