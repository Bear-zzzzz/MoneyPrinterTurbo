import unittest

from full_data import build_dataset
from four_acts import build_four_acts, shot_at, fracture_particles, render_four_frame, DURATION
from render_full import FPS, base_image, frame_state


class FourActTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset=build_dataset()
        cls.design=build_four_acts(cls.dataset)

    def test_four_distinct_acts_and_data_driven_us_lead(self):
        self.assertEqual(DURATION,30)
        self.assertEqual([act['code'] for act in self.design['acts']],['USA','JPN','SUN','CHN'])
        self.assertEqual(self.design['usa_peak']['year'],2007)
        self.assertAlmostEqual(self.design['usa_peak']['ratio'],3.1297860036972196)

    def test_timeline_jumps_have_explicit_ranges_and_black_transition(self):
        for seconds in (0,7.5,15,22.5):
            shot=shot_at(seconds,self.design,self.dataset)
            self.assertIn('—',shot['range_caption'])
            self.assertEqual(shot['opacity'],0)
        for seconds in (1,9,16,24):
            self.assertGreater(shot_at(seconds,self.design,self.dataset)['opacity'],0.9)

    def test_soviet_final_number_never_animates_to_zero(self):
        for seconds in (19,20,21,22):
            shot=shot_at(seconds,self.design,self.dataset)
            if shot['dissolve']>0:
                self.assertIn('SUN',shot['presentation']['hidden_codes'])
                self.assertEqual(shot['soviet_display_usd'],self.design['soviet_last']['value_usd'])
                self.assertGreater(shot['soviet_display_usd'],0)
                self.assertTrue(shot['soviet_estimated'])
        self.assertNotIn('RUS',self.design['acts'][2]['focus_codes'])

    def test_particles_are_repeatable_and_displacement_increases(self):
        first=fracture_particles(0.2)
        self.assertEqual(first,fracture_particles(0.2))
        later=fracture_particles(0.8)
        self.assertGreater(sum(abs(item['dy']) for item in later),sum(abs(item['dy']) for item in first))

    def test_source_values_and_leader_geometry_not_fabricated(self):
        for index in range(900):
            shot=shot_at(index/FPS,self.design,self.dataset)
            state=frame_state(shot['global_seconds'],self.dataset)
            self.assertAlmostEqual(state['rows'][0]['value_usd']/state['axis_max_usd'],1/1.08)
        self.assertEqual(shot_at(10,self.design,self.dataset)['phase'],'catchup')
        self.assertEqual(shot_at(14,self.design,self.dataset)['phase'],'cooldown')

    def test_frame_size_and_transition_is_black(self):
        image=render_four_frame(0,self.dataset,base_image(),self.design)
        self.assertEqual(image.size,(1080,1920))
        self.assertIsNone(image.getbbox())


if __name__=='__main__':
    unittest.main()
