import json
import argparse
import subprocess
from pathlib import Path

from PIL import Image

from full_data import build_dataset
from four_acts import DURATION, build_four_acts, render_four_frame, shot_at
from render_full import FPS, WIDTH, HEIGHT, base_image
from paths import OUTPUT


ROOT=OUTPUT


def main():
    parser=argparse.ArgumentParser()
    modes=parser.add_mutually_exclusive_group()
    modes.add_argument('--power-aura',action='store_true')
    modes.add_argument('--side-fire',action='store_true')
    modes.add_argument('--bar-flame',action='store_true')
    modes.add_argument('--clean',action='store_true')
    args=parser.parse_args()
    version='v15' if args.clean else ('v14' if args.bar_flame else ('v13' if args.side_fire else ('v12' if args.power_aura else 'v11')))
    dataset=build_dataset()
    design=build_four_acts(dataset)
    style='clean' if args.clean else ('bar-flame' if args.bar_flame else ('side-fire' if args.side_fire else ('power-aura' if args.power_aura else 'cinematic')))
    output=ROOT/f'world-gdp-four-country-{style}-{version}-demo.mp4'
    base=base_image()
    command=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24',
             '-s',f'{WIDTH}x{HEIGHT}','-r',str(FPS),'-i','pipe:0','-an','-c:v','libx264',
             '-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(output)]
    preview_frames={round(seconds*FPS) for seconds in (1.15,3,8.65,14,18.75,19.5,24,28.5)} if args.power_aura else {round(seconds*FPS) for seconds in (1.5,6,9,14,17,19.5,24,28.5)}
    previews=[]
    timeline=[]
    with subprocess.Popen(command,stdin=subprocess.PIPE) as encoder:
        try:
            for index in range(round(DURATION*FPS)):
                seconds=index/FPS
                shot=shot_at(seconds,design,dataset)
                image=render_four_frame(seconds,dataset,base,design,power_aura=args.power_aura,side_fire=args.side_fire,bar_flame=args.bar_flame,clean=args.clean)
                encoder.stdin.write(image.tobytes())
                timeline.append({'frame':index,'seconds':seconds,'act':shot['index'],
                                 'global_seconds':shot['global_seconds'],'phase':shot['phase'],'dissolve':shot['dissolve'],
                                 'opacity':shot['opacity'],'soviet_display_usd':shot['soviet_display_usd'] if shot['index']==2 else None})
                if index in preview_frames:
                    image.save(ROOT/f'{version}-frame-{index:04d}.png')
                    previews.append(image.resize((270,480),Image.Resampling.LANCZOS))
                if index%120==0:
                    print(f'Rendered {seconds:.0f}/{DURATION}s',flush=True)
        finally:
            encoder.stdin.close()
        if encoder.wait()!=0:
            raise RuntimeError('Four-act FFmpeg encoding failed')
    preview=Image.new('RGB',(1080,960))
    for index,image in enumerate(previews):
        preview.paste(image,((index%4)*270,(index//4)*480))
    preview.save(ROOT/f'{version}-four-acts-preview.png')
    (ROOT/f'{version}-four-acts.json').write_text(json.dumps({**design,'output':output.name,'fps':FPS,'power_aura':args.power_aura,'side_fire':args.side_fire,
        'clean':args.clean,'clean_note':'Flames and ambient energy removed; focus, text and Soviet identity dissolve retained' if args.clean else '',
        'bar_flame':args.bar_flame,'bar_flame_note':'Narrow animated flame tongues attached to focus GDP bar edges/tail, follows bar geometry; no right-column ambient flames or bottom cards' if args.bar_flame else '',
        'side_fire_note':'Right-only rising burning flames and sparks, x790..1080 y430..1470; bottom cards/hero flags/decorations removed; numbers protected' if args.side_fire else '',
        'effect_note':'Charge, single burst, sustained flames, rings and sparks; protected text/numeric regions, no whole-frame strobe or shake' if args.power_aura else '',
        'resolution':[WIDTH,HEIGHT],'full_film_updated':False,'bgm':'Awaiting requested actual music files'},ensure_ascii=False,indent=2))
    (ROOT/f'{version}-frame-timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2))
    print(output,flush=True)


if __name__=='__main__':
    main()
