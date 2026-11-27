"""Experimental eligibility filter; never certifies live market access."""
import math
import unittest

FLAGS = ("isSbc", "isObjective", "isEvolutionPlayerItem", "isProvisional")

def classify(row, quote):
    if any(row.get(k) is True for k in FLAGS):
        return "excluded"
    if any(row.get(k) is not False for k in FLAGS):
        return "unknown"
    if type(row.get("eaId")) is not int or row["eaId"] <= 0:
        return "unknown"
    if type(quote) not in (int, float) or not math.isfinite(quote) or quote <= 0:
        return "unknown"
    return "candidate"

class FilterTests(unittest.TestCase):
    def setUp(self):
        self.row = dict(eaId=67316992, **dict.fromkeys(FLAGS, False))
    def test_candidate(self):
        self.assertEqual(classify(dict(self.row, hasPrice=False), 32000), "candidate")
    def test_exclusions(self):
        for flag in FLAGS:
            self.assertEqual(classify(dict(self.row, **{flag: True}), 61760), "excluded")
    def test_missing(self):
        for flag in FLAGS:
            row = self.row.copy()
            del row[flag]
            self.assertEqual(classify(row, 32000), "unknown")
    def test_invalid_price(self):
        for price in (0, -1, None, True, "32000", float("nan"), float("inf")):
            self.assertEqual(classify(self.row, price), "unknown")

if __name__ == "__main__":
    unittest.main()
