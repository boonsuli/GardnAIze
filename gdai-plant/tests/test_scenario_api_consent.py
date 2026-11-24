import argparse
import unittest
from matching.generate_garden_scenarios import check_api_authorization

def args(**changes):
    data = dict(input_json=None, allow_paid_api=False, confirm_api_spend=None, model="test-model")
    data.update(changes)
    return argparse.Namespace(**data)

class PaidApiConsentTests(unittest.TestCase):
    def setUp(self):
        self.parser = argparse.ArgumentParser()
    def test_default_denies_api(self):
        with self.assertRaises(SystemExit):
            check_api_authorization(args(), self.parser)
    def test_key_or_model_does_not_authorize(self):
        with self.assertRaises(SystemExit):
            check_api_authorization(args(allow_paid_api=True), self.parser)
    def test_confirmation_without_flag_denied(self):
        with self.assertRaises(SystemExit):
            check_api_authorization(args(confirm_api_spend="I_AUTHORIZE_GEMINI_API_COST"), self.parser)
    def test_offline_allowed(self):
        check_api_authorization(args(input_json="/tmp/test.json"), self.parser)
    def test_offline_with_spend_flags_denied(self):
        with self.assertRaises(SystemExit):
            check_api_authorization(args(input_json="/tmp/test.json", allow_paid_api=True), self.parser)

if __name__ == "__main__":
    unittest.main()
