import unittest

from full_data import build_dataset
from four_acts import build_four_acts, shot_at
from render_full import base_image, frame_state, bar_geometry
from power_aura import aura_state, aura_particles, power_layer, apply_power_aura


class PowerAuraTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset=build_dataset()
        cls.design=build_four_acts(cls.dataset)

    def test_charge_burst_and_sustain(self):
        self.assertEqual(aura_state(shot_at(0.3,self.design,self.dataset))['phase'],'charge')
        self.assertEqual(aura_state(shot_at(1.15,self.design,self.dataset))['phase'],'burst')
        self.assertEqual(aura_state(shot_at(3,self.design,self.dataset))['phase'],'sustain')
        self.assertGreater(aura_state(shot_at(1.15,self.design,self.dataset))['strength'],aura_state(shot_at(0.3,self.design,self.dataset))['strength'])

    def test_japan_extinguishes_and_china_crossing_bursts(self):
        self.assertLess(aura_state(shot_at(14,self.design,self.dataset))['strength'],0.12)
        template=shot_at(25,self.design,self.dataset)
        seconds=22.5+template['crossing_local_seconds']+0.15
        self.assertEqual(aura_state(shot_at(seconds,self.design,self.dataset))['phase'],'burst')

    def test_particles_deterministic_and_outward(self):
        self.assertEqual(aura_particles(0.3,1),aura_particles(0.3,1))
        first,later=aura_particles(0.1,1),aura_particles(0.5,1)
        self.assertGreater(sum(item['distance'] for item in later),sum(item['distance'] for item in first))

    def test_overlay_preserves_headers_flags_and_numbers(self):
        shot=shot_at(1.15,self.design,self.dataset)
        state=frame_state(shot['global_seconds'],self.dataset)
        base=base_image().convert('RGBA')
        final=apply_power_aura(base,state,shot)
        self.assertEqual(base.crop((0,0,1080,350)).tobytes(),final.crop((0,0,1080,350)).tobytes())
        for row in state['render_rows']:
            if row['position']>=10 or row['value_usd']<=0:
                continue
            top=385+int(row['position']*110)
            geometry=bar_geometry(row,state)
            box=(int(geometry['number_x'])-3,top+48,int(geometry['number_x'])+215,top+104)
            self.assertEqual(base.crop(box).tobytes(),final.crop(box).tobytes())
        self.assertNotEqual(base.tobytes(),final.tobytes())

    def test_effect_is_large_but_has_no_global_flash(self):
        shot=shot_at(1.15,self.design,self.dataset)
        state=frame_state(shot['global_seconds'],self.dataset)
        layer=power_layer(state,shot)
        self.assertGreater(layer.getbbox()[3]-layer.getbbox()[1],900)
        self.assertLessEqual(layer.getchannel('A').getextrema()[1],210)


if __name__=='__main__':
    unittest.main()
