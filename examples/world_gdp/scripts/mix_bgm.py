import argparse
import json
import math
import subprocess
from pathlib import Path
from paths import OUTPUT


ROOT = OUTPUT
TRACK_NAMES = ['CHASHKAKEFIRA - BARRETE!', 'CHASHKAKEFIRA - COLLAR!', 'Lunak - PASSO FUNK']


def build_filter(duration):
    if not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 3:
        raise ValueError('Video must be longer than three seconds')
    crossfade = 0.6
    segment = (duration + 2 * crossfade) / 3
    filters = []
    for index in range(3):
        filters.append(f'[{index + 1}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,'
                       f'loudnorm=I=-15:TP=-1.5:LRA=8,atrim=duration={segment:.6f},'
                       f'asetpts=PTS-STARTPTS[a{index}]')
    filters.append('[a0][a1]acrossfade=d=0.6:c1=tri:c2=tri[ab]')
    filters.append('[ab][a2]acrossfade=d=0.6:c1=tri:c2=tri,'
                   f'atrim=duration={duration:.3f},afade=t=in:d=0.25,'
                   f'afade=t=out:st={duration - 0.8:.3f}:d=0.8,'
                   'alimiter=limit=0.95:level=false:latency=true[bgm]')
    return ';'.join(filters)


def probe(path):
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)],
                            check=True, capture_output=True, text=True, timeout=30)
    return json.loads(result.stdout)


def main():
    parser = argparse.ArgumentParser(description='Mix exactly the three user-supplied music files at normal tempo')
    parser.add_argument('--video', type=Path, default=ROOT / 'world-gdp-four-country-clean-v15-demo.mp4')
    parser.add_argument('--music', type=Path, nargs=3, required=True,
                        metavar=('BARRETE', 'COLLAR', 'PASSO_FUNK'))
    parser.add_argument('--offsets', type=float, nargs=3, default=[0, 0, 0])
    parser.add_argument('--output', type=Path, default=ROOT / 'world-gdp-four-country-clean-bgm.mp4')
    args = parser.parse_args()
    for path in [args.video, *args.music]:
        if not path.is_file():
            parser.error(f'Missing local file: {path}')
    if any(not math.isfinite(value) or value < 0 for value in args.offsets):
        parser.error('Music offsets must be finite and nonnegative')
    output = args.output.resolve()
    if output.exists() or output in {args.video.resolve(), *(path.resolve() for path in args.music)}:
        parser.error('Output must be a new file, distinct from all inputs')
    video_info = probe(args.video)
    duration = float(video_info['format']['duration'])
    command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-n', '-i', str(args.video)]
    for path, offset in zip(args.music, args.offsets):
        info = probe(path)
        if not any(stream['codec_type'] == 'audio' for stream in info['streams']):
            parser.error(f'No audio stream: {path}')
        if offset >= float(info['format']['duration']):
            parser.error(f'Offset beyond track duration: {path}')
        command.extend(['-stream_loop', '-1', '-ss', str(offset), '-i', str(path)])
    command.extend(['-filter_complex', build_filter(duration), '-map', '0:v:0', '-map', '[bgm]',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-t', str(duration),
                    '-movflags', '+faststart', str(output)])
    subprocess.run(command, check=True, timeout=max(120, int(duration * 6)))
    result = probe(output)
    if not any(stream['codec_type'] == 'audio' for stream in result['streams']):
        raise RuntimeError('Mixed video contains no audio')
    (ROOT / 'v4-music-mix.json').write_text(json.dumps({
        'track_order': TRACK_NAMES, 'local_files': [str(path.resolve()) for path in args.music],
        'offsets_seconds': args.offsets, 'output': str(output), 'normal_music_tempo': True,
        'crossfade_seconds': 0.6, 'loudness_target_lufs': -15, 'filter': build_filter(duration),
        'track_identity': 'Filenames/order supplied by user; not independently identified',
    }, ensure_ascii=False, indent=2))
    print(output)


if __name__ == '__main__':
    main()
