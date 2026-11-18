import unittest

from full_data import build_dataset
from four_acts import build_four_acts, render_four_frame, shot_at
from render_full import base_image, frame_state, bar_geometry
from side_fire import flame_layer, apply_side_fire


class SideFireTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset=build_dataset()
        cls.design=build_four_acts(cls.dataset)

    def test_fire_confined_to_right_and_not_bottom(self):
        shot=shot_at(1.15,self.design,self.dataset)
        layer=flame_layer(shot)
        bounds=layer.getbbox()
        self.assertGreaterEqual(bounds[0],790)
        self.assertGreaterEqual(bounds[1],420)
        self.assertLessEqual(bounds[3],1480)
        self.assertIsNone(layer.crop((0,1500,1080,1920)).getbbox())

    def test_flames_repeatable_but_animate(self):
        shot=shot_at(2,self.design,self.dataset)
        self.assertEqual(flame_layer(shot).tobytes(),flame_layer(shot).tobytes())
        self.assertNotEqual(flame_layer(shot).tobytes(),flame_layer(shot_at(2.1,self.design,self.dataset)).tobytes())

    def test_bottom_card_flag_and_decorations_removed(self):
        base=base_image()
        for seconds in (1.15,14,19.5,28.5):
            image=render_four_frame(seconds,self.dataset,base,self.design,side_fire=True)
            self.assertEqual(image.crop((0,1600,1080,1920)).tobytes(),base.crop((0,1600,1080,1920)).tobytes())

    def test_digits_and_header_masked(self):
        shot=shot_at(1.15,self.design,self.dataset)
        state=frame_state(shot['global_seconds'],self.dataset)
        base=base_image().convert('RGBA')
        image=apply_side_fire(base,state,shot)
        self.assertEqual(image.crop((0,0,1080,350)).tobytes(),base.crop((0,0,1080,350)).tobytes())
        for row in state['render_rows']:
            if row['position']<10 and row['value_usd']>0:
                top=385+int(row['position']*110)
                left=int(bar_geometry(row,state)['number_x'])-3
                box=(left,top+48,left+220,top+104)
                self.assertEqual(image.crop(box).tobytes(),base.crop(box).tobytes())


if __name__=='__main__':
    unittest.main()
