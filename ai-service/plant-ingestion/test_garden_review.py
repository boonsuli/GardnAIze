import tempfile
import unittest
from pathlib import Path
from garden_review import assign_split, load_manifest, load_reviews, save_reviews, reviewed_records

class GardenReviewTest(unittest.TestCase):
    def test_stable_split_by_garden(self):
        self.assertEqual(assign_split("garden-a"),assign_split("garden-a"))
        self.assertIn(assign_split("garden-a"),("TRAIN","VAL","TEST"))
    def test_review_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"reviews.csv"
            key=("source","image")
            reviews={key:{"source_key":"source","external_id":"image","review_status":"ACCEPTED","review_reason":""}}
            save_reviews(path,reviews)
            self.assertEqual(load_reviews(path)[key]["review_status"],"ACCEPTED")
            row={"source_key":"source","external_id":"image","garden_group_key":"garden-a"}
            self.assertEqual(reviewed_records([row],load_reviews(path))[0]["dataset_split"],assign_split("garden-a"))
    def test_duplicate_manifest_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"images.csv"
            path.write_text("source_key,external_id,garden_group_key\\ns,x,g\\ns,x,g\\n")
            with self.assertRaises(ValueError):load_manifest(path)

if __name__=="__main__": unittest.main()
