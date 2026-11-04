"""Unit tests for garden image dataset splitting."""

import importlib.util
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "download_garden_images.py"
)

spec = importlib.util.spec_from_file_location(
    "download_garden_images", SCRIPT
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class TestDatasetSplit(unittest.TestCase):

    def test_requested_fraction(self):
        for fraction, expected in [
            (0.1, 3),
            (0.2, 6),
            (0.3, 9),
            (0.4, 12),
        ]:
            with self.subTest(fraction=fraction):
                splits = [
                    module.choose_split(i, fraction)
                    for i in range(30)
                ]

                self.assertEqual(
                    splits.count("garden_test"),
                    expected,
                )

    def test_deterministic(self):
        first = [
            module.choose_split(i, 0.2)
            for i in range(30)
        ]

        second = [
            module.choose_split(i, 0.2)
            for i in range(30)
        ]

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()