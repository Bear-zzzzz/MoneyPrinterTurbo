import unittest

from full_data import build_dataset
from render_full import base_image, frame_state, render_frame, font
from storyboard import build_storyboard, fade_envelope, presentation_at, START_SECONDS, DURATION


class StoryboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset = build_dataset()
        cls.story = build_storyboard(cls.dataset)

    def test_fades_rise_hold_and_fall(self):
        self.assertEqual(fade_envelope(0,1.6,0.2),0)
        self.assertEqual(fade_envelope(0.2,1.6,0.2),1)
        self.assertEqual(fade_envelope(0.8,1.6,0.2),1)
        self.assertEqual(fade_envelope(1.6,1.6,0.2),0)
        self.assertLess(fade_envelope(0.1,1.6,0.2),1)
        self.assertEqual(fade_envelope(-1,1.6,0.2),0)

    def test_focus_comes_from_reported_endpoint_data(self):
        self.assertEqual(self.story['absolute_focus']['code'],'CHN')
        self.assertEqual(self.story['relative_focus']['code'],'RUS')
        self.assertGreater(self.story['absolute_focus']['increase_usd'],0)
        self.assertGreater(self.story['relative_focus']['ratio'],1)
        self.assertEqual(self.story['comparison_scope'],'2012 Top10 with complete provider-reported annual records from2001 through2012')

    def test_crossing_is_derived_from_actual_animation(self):
        crossing=self.story['crossing_seconds']
        def amounts(local):
            return {row['code']:row['value_usd'] for row in frame_state(START_SECONDS+local,self.dataset)['render_rows']}
        before,after=amounts(crossing-1/30),amounts(crossing)
        self.assertLess(before['CHN'],before['JPN'])
        self.assertGreaterEqual(after['CHN'],after['JPN'])

    def test_scene_alpha_returns_to_unmodified_main_chart(self):
        presentation=presentation_at(DURATION-1/30,self.story)
        self.assertEqual(presentation['strength'],0)
        self.assertEqual(presentation['scene_opacity'],0)
        self.assertLess(presentation['header_opacity'],1)
        self.assertEqual(presentation_at(0,self.story)['header_opacity'],0)

    def test_fade_does_not_modify_numeric_chart_when_no_spotlight(self):
        seconds=START_SECONDS+9.5
        original=render_frame(seconds,self.dataset,base_image())
        faded=render_frame(seconds,self.dataset,base_image(),presentation_at(9.5,self.story))
        self.assertEqual(original.crop((0,385,1080,1485)).tobytes(),faded.crop((0,385,1080,1485)).tobytes())
        self.assertEqual(DURATION,19.2)

    def test_focus_metrics_visible_without_overflow(self):
        absolute=next(scene for scene in self.story['scenes'] if scene['kind']=='absolute')
        relative=next(scene for scene in self.story['scenes'] if scene['kind']=='relative')
        self.assertIn('亿美元',absolute['title'])
        self.assertIn('7.20倍',relative['title'])
        for scene in self.story['scenes']:
            self.assertLess(font(28).getlength(scene['title']),570)


if __name__ == '__main__':
    unittest.main()
