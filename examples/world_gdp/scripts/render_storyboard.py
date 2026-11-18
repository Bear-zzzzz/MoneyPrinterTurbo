import json
import subprocess
from pathlib import Path

from PIL import Image

from full_data import build_dataset
from render_full import FPS, WIDTH, HEIGHT, base_image, render_frame
from storyboard import START_SECONDS, DURATION, build_storyboard, presentation_at
from paths import OUTPUT


ROOT=OUTPUT


def main():
    dataset=build_dataset()
    story=build_storyboard(dataset)
    output=ROOT/'world-gdp-2001-2012-storyboard-v10-demo.mp4'
    base=base_image()
    command=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24',
             '-s',f'{WIDTH}x{HEIGHT}','-r',str(FPS),'-i','pipe:0','-an','-c:v','libx264',
             '-preset','veryfast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(output)]
    preview_indices={round(seconds*FPS) for seconds in (0.1,1,3,7.5,11.9,story['crossing_seconds'],17.8,19.1)}
    previews=[]
    with subprocess.Popen(command,stdin=subprocess.PIPE) as encoder:
        try:
            for index in range(round(DURATION*FPS)):
                local=index/FPS
                image=render_frame(START_SECONDS+local,dataset,base,presentation_at(local,story))
                encoder.stdin.write(image.tobytes())
                if index in preview_indices:
                    image.save(ROOT/f'v10-story-frame-{index:04d}.png')
                    previews.append(image.resize((270,480),Image.Resampling.LANCZOS))
                if index%120==0:
                    print(f'Rendered {local:.1f}/{DURATION:.1f}s',flush=True)
        finally:
            encoder.stdin.close()
        if encoder.wait()!=0:
            raise RuntimeError('FFmpeg storyboard encoding failed')
    preview=Image.new('RGB',(1080,960))
    for index,image in enumerate(previews):
        preview.paste(image,((index%4)*270,(index//4)*480))
    preview.save(ROOT/'v10-storyboard-preview.png')
    (ROOT/'v10-storyboard.json').write_text(json.dumps({**story,'output':output.name,
        'fps':FPS,'resolution':[WIDTH,HEIGHT],'header_fade_seconds':0.2,'scene_fade_seconds':0.3,
        'bgm':'Awaiting three actual requested audio files','status':'Demo for style approval, not full-film rollout'},ensure_ascii=False,indent=2))
    (ROOT/'v10-demo-source-years.json').write_text(json.dumps([row for row in dataset['years'] if 2001<=row['year']<=2012],ensure_ascii=False,indent=2))
    print(output,flush=True)


if __name__=='__main__':
    main()
