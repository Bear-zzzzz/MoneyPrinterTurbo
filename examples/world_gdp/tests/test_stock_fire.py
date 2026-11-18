import unittest

import numpy as np
from PIL import Image

from stock_fire import black_to_alpha, tile_strip, attach_strip, compose_stock_fire
from render_full import frame_state, base_image, bar_geometry, TOP, ROW_GAP
from full_data import build_dataset


class StockFireTests(unittest.TestCase):
    def test_black_is_transparent_and_foreground_preserved(self):
        source=Image.fromarray(np.array([[[0,0,0],[200,100,20],[255,220,100]]],dtype=np.uint8))
        rgba=black_to_alpha(source)
        self.assertEqual(rgba.getpixel((0,0))[3],0)
        result=Image.alpha_composite(Image.new('RGBA',rgba.size),rgba)
        for horizontal in (1,2):
            pixel=np.asarray(result)[0,horizontal].astype(float)
            rgb=pixel[:3]*pixel[3]/255
            self.assertTrue(np.max(np.abs(rgb.astype(float)-np.asarray(source)[0,horizontal].astype(float)))<12)

    def test_tiles_are_repeated_and_clipped_not_stretched(self):
        source=Image.new('RGBA',(20,10),(255,100,0,255))
        frames=[source]
        strip=tile_strip(frames,73,0)
        self.assertEqual(strip.size,(73,10))
        self.assertGreater(strip.getchannel('A').getextrema()[1],0)

    def test_bar_attachment_and_protected_numbers(self):
        data=build_dataset(); state=frame_state(80.5,data)
        row=next(row for row in state['render_rows'] if row['code']=='CHN')
        source=Image.new('RGBA',(30,44),(255,180,0,220))
        strip=tile_strip([source],int(bar_geometry(row,state)['bar_end']-85),0)
        layer=attach_strip(strip,row,state)
        bounds=layer.getbbox()
        self.assertLessEqual(bounds[2],bar_geometry(row,state)['bar_end']+1)
        self.assertGreaterEqual(bounds[1],TOP+row['position']*ROW_GAP+42-1)
        base=base_image().convert('RGBA')
        final=compose_stock_fire(base,state,[source],0,'CHN')
        self.assertEqual(base.crop((790,0,1080,1920)).tobytes(),final.crop((790,0,1080,1920)).tobytes())
        self.assertEqual(base.crop((0,1600,1080,1920)).tobytes(),final.crop((0,1600,1080,1920)).tobytes())
        for country in state['render_rows']:
            if country['position']<10 and country['value_usd']>0:
                top=TOP+int(country['position']*ROW_GAP)
                left=int(bar_geometry(country,state)['number_x'])-3
                box=(left,top+48,left+220,top+104)
                self.assertEqual(base.crop(box).tobytes(),final.crop(box).tobytes())


if __name__=='__main__':
    unittest.main()
