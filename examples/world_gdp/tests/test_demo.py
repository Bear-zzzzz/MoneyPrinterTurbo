import unittest

from PIL import ImageChops

from render_demo import build_years, transition_rows, rolling_text, number_image, annual_progress, YEAR_SECONDS, FPS, counter_image


class DemoTests(unittest.TestCase):
    def test_soviet_union_is_included_and_values_are_ordered(self):
        years = build_years()
        self.assertEqual([row['year'] for row in years], list(range(1970, 1976)))
        for row in years:
            self.assertEqual(len(row['top10']), 10)
            self.assertIn('SUN', [entry['code'] for entry in row['top10']])
            values = [entry['value'] for entry in row['top10']]
            self.assertEqual(values, sorted(values, reverse=True))

    def test_transition_settles_on_source_values(self):
        years = build_years()
        for first, second in zip(years, years[1:]):
            settled = transition_rows(first['top10'], second['top10'], 1)
            visible = sorted((row for row in settled if row['opacity'] > 0), key=lambda row: row['position'])
            self.assertEqual([row['code'] for row in visible], [row['code'] for row in second['top10']])
            self.assertEqual([row['value'] for row in visible], [row['value'] for row in second['top10']])

    def test_digits_settle_exactly(self):
        self.assertEqual(rolling_text(1073.303), '1,073.3')
        self.assertEqual(rolling_text(433.412461), '433.4')

    def test_number_roll_handles_blank_padding(self):
        for index in range(100):
            image = number_image(999.9, 1000.0, index / 100, '#59A8FF')
            self.assertEqual(image.size, (297, 60))

    def test_unchanged_values_keep_rolling(self):
        first = number_image(433.4, 433.4, 0.1, '#F56268')
        second = number_image(433.4, 433.4, 0.55, '#F56268')
        self.assertIsNotNone(ImageChops.difference(first, second).convert('RGB').getbbox())

    def test_last_frame_reaches_exact_annual_endpoint(self):
        self.assertEqual(annual_progress(YEAR_SECONDS - 1 / FPS), 1)
        self.assertGreater(annual_progress(2.7), annual_progress(2.6))
        self.assertLess(annual_progress(2.7), 1)

    def test_counter_uses_stationary_glyphs(self):
        first = counter_image(123.41, '#F56268')
        second = counter_image(123.44, '#F56268')
        self.assertEqual(first.tobytes(), second.tobytes())
        self.assertEqual(first.size, (297, 60))
        changed = counter_image(123.5, '#F56268')
        self.assertNotEqual(first.tobytes(), changed.tobytes())


if __name__ == '__main__':
    unittest.main()
