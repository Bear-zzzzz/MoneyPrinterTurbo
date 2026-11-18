import unittest

from full_data import build_dataset
from four_acts import build_four_acts,shot_at,render_four_frame
from render_full import base_image,frame_state,bar_geometry,TOP,ROW_GAP
from bar_flame import bar_flame_layer,apply_bar_flame


class BarFlameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset=build_dataset()
        cls.design=build_four_acts(cls.dataset)

    def test_flame_attached_to_bar_not_right_column(self):
        for seconds in (1.15,9,24,28.5):
            shot=shot_at(seconds,self.design,self.dataset)
            state=frame_state(shot['global_seconds'],self.dataset)
            row=next(row for row in state['render_rows'] if row['code']==self.design['acts'][shot['index']]['code'])
            bounds=bar_flame_layer(state,shot).getbbox()
            top=TOP+row['position']*ROW_GAP
            self.assertIsNotNone(bounds)
            self.assertGreaterEqual(bounds[0],84)
            self.assertLessEqual(bounds[2],bar_geometry(row,state)['bar_end']+10)
            self.assertGreaterEqual(bounds[1],top+49)
            self.assertLessEqual(bounds[3],top+103)

    def test_numeric_pixels_unchanged(self):
        shot=shot_at(28.5,self.design,self.dataset)
        state=frame_state(shot['global_seconds'],self.dataset)
        base=base_image().convert('RGBA')
        image=apply_bar_flame(base,state,shot)
        for row in state['render_rows']:
            if row['position']<10 and row['value_usd']>0:
                top=TOP+int(row['position']*ROW_GAP)
                left=int(bar_geometry(row,state)['number_x'])-3
                box=(left,top+48,left+220,top+104)
                self.assertEqual(image.crop(box).tobytes(),base.crop(box).tobytes())
        self.assertNotEqual(image.tobytes(),base.tobytes())

    def test_flames_extinguish_and_no_bottom_content(self):
        for seconds in (14,20):
            shot=shot_at(seconds,self.design,self.dataset)
            state=frame_state(shot['global_seconds'],self.dataset)
            self.assertIsNone(bar_flame_layer(state,shot).getbbox())
        base=base_image()
        image=render_four_frame(1.15,self.dataset,base,self.design,bar_flame=True)
        self.assertIsNone(bar_flame_layer(frame_state(shot_at(1.15,self.design,self.dataset)['global_seconds'],self.dataset),shot_at(1.15,self.design,self.dataset)).crop((790,385,1080,1480)).getbbox())
        self.assertEqual(image.crop((0,1600,1080,1920)).tobytes(),base.crop((0,1600,1080,1920)).tobytes())

    def test_clean_mode_has_no_flame_or_ambient_energy(self):
        from render_full import render_frame
        from four_acts import draw_dissolution
        shot=shot_at(1.15,self.design,self.dataset)
        state=frame_state(shot['global_seconds'],self.dataset)
        base=base_image()
        expected=draw_dissolution(render_frame(shot['global_seconds'],self.dataset,base,shot['presentation']).convert('RGBA'),state,shot,self.design).convert('RGB')
        actual=render_four_frame(1.15,self.dataset,base,self.design,clean=True)
        self.assertEqual(actual.tobytes(),expected.tobytes())


if __name__=='__main__':
    unittest.main()
