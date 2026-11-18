import unittest

from prepare import top_ten, animate_value


class RankingTests(unittest.TestCase):
    def test_excludes_aggregates_and_nulls(self):
        records = [
            {"code": "USA", "value": 100},
            {"code": "WLD", "value": 1000},
            {"code": "SUN", "value": None},
            {"code": "CHN", "value": 90},
        ]
        self.assertEqual([row["code"] for row in top_ten(records, {"USA", "SUN", "CHN"})], ["USA", "CHN"])

    def test_sorts_all_countries_not_a_fixed_ten(self):
        records = [{"code": f"country-{index}", "value": index} for index in range(15)]
        selected = top_ten(records, {row["code"] for row in records})
        self.assertEqual(len(selected), 10)
        self.assertEqual(selected[0]["value"], 14)
        self.assertEqual(selected[-1]["value"], 5)

    def test_historical_identity_remains_distinct(self):
        records = [{"code": "SUN", "value": 500}, {"code": "RUS", "value": 200}]
        self.assertEqual(top_ten(records, {"SUN"})[0]["code"], "SUN")

    def test_animation_preserves_exact_endpoints(self):
        self.assertEqual(animate_value(1234.5, 2345.6, 0), 1234.5)
        self.assertEqual(animate_value(1234.5, 2345.6, 1), 2345.6)
        self.assertAlmostEqual(animate_value(100, 200, 0.5), 150)


if __name__ == "__main__":
    unittest.main()
