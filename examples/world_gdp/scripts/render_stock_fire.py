import hashlib
import json
import subprocess
from pathlib import Path

from PIL import Image

from full_data import build_dataset
from render_full import FPS,WIDTH,HEIGHT,base_image,frame_state,render_frame
from stock_fire import load_stock_frames,compose_stock_fire
from paths import OUTPUT, ASSETS


ROOT=OUTPUT
DURATION=5
START_GLOBAL=78.0


def main():
    source=ASSETS/'local-only/mixkit-3759.mp4'
    if not source.is_file():
        raise SystemExit('Missing licensed local asset. Run: python examples/world_gdp/scripts/fetch_stock_fire.py')
    frames=load_stock_frames(source)
    dataset=build_dataset()
    base=base_image()
    output=ROOT/'world-gdp-stock-fire-v16-preview.mp4'
    presentation={'header_opacity':1,'scene_opacity':0,'strength':0.7,'codes':['CHN'],
                  'caption':'','kind':'stock-preview'}
    command=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{WIDTH}x{HEIGHT}',
             '-r',str(FPS),'-i','pipe:0','-an','-c:v','libx264','-preset','veryfast','-crf','18',
             '-pix_fmt','yuv420p','-movflags','+faststart',str(output)]
    preview=Image.new('RGB',(1080,480))
    with subprocess.Popen(command,stdin=subprocess.PIPE) as encoder:
        try:
            for index in range(DURATION*FPS):
                local=index/FPS
                seconds=START_GLOBAL+local
                state=frame_state(seconds,dataset)
                image=render_frame(seconds,dataset,base,presentation)
                final=compose_stock_fire(image,state,frames,local,'CHN').convert('RGB')
                encoder.stdin.write(final.tobytes())
                if index in (15,45,75,135):
                    final.save(ROOT/f'v16-frame-{index:04d}.png')
                    column=(15,45,75,135).index(index)
                    preview.paste(final.resize((270,480)),(column*270,0))
        finally:
            encoder.stdin.close()
        if encoder.wait()!=0:
            raise RuntimeError('Stock fire preview encoder failed')
    preview.save(ROOT/'v16-stock-fire-preview.png')
    record={'created_on':'2026-11-18','output':output.name,'duration_seconds':DURATION,
            'global_time_range':[START_GLOBAL,START_GLOBAL+DURATION],'focus_country':'CHN',
            'source_title':'Burning flames on a black background','provider':'Mixkit','asset_id':3759,
            'source_page':'https://mixkit.co/free-stock-video/burning-flames-on-a-black-background-3759/',
            'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'license':'Mixkit Stock Video Free License','license_record':'references/free-license.html',
            'terms_record':'references/terms.html','original_has_alpha':False,
            'alpha_method':'Black-background matte, maxRGB alpha with unpremultiplied foreground; no native-alpha claim',
            'crop_source_pixels':[350,240,580,480],'uniform_tile_size':[53,44],
            'placement':'Repeat actual stock tiles along bar upper edge, stagger source frame, edge feather, clip bar length, mask digits and names',
            'original_assets_excluded_from_share_backup':True,'full_film_updated':False,'audio_streams':0}
    (ROOT/'v16-stock-fire.json').write_text(json.dumps(record,ensure_ascii=False,indent=2))
    print(output,flush=True)


if __name__=='__main__':
    main()
