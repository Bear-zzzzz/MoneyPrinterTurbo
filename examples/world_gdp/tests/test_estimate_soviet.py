import unittest

from estimate_soviet import backcast


class SovietBackcastTests(unittest.TestCase):
    def test_exact_anchor(self):
        result = backcast(433412461168.88885, {1960: 50, 1970: 100}, {1960: 0.8, 1970: 1})
        self.assertEqual(result[-1]["value_usd"], 433412461168.88885)
        self.assertEqual(result[-1]["status"], "source_published")

    def test_separates_real_output_and_price_ratios(self):
        result = backcast(100, {1960: 50, 1970: 100}, {1960: 0.8, 1970: 1})
        self.assertAlmostEqual(result[0]["value_usd"], 40)
        self.assertEqual(result[0]["status"], "estimated")
        self.assertAlmostEqual(result[0]["constant_price_proxy_usd"], 50)

    def test_missing_price_does_not_impute(self):
        with self.assertRaises(ValueError):
            backcast(100, {1960: 50, 1970: 100}, {1970: 1})

    def test_invalid_inputs_rejected(self):
        for invalid in (0, -1, float("nan"), float("inf")):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    backcast(100, {1960: invalid, 1970: 100}, {1960: 0.8, 1970: 1})


if __name__ == "__main__":
    unittest.main()
