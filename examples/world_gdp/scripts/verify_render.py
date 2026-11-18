import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from paths import OUTPUT


def main():
    parser = argparse.ArgumentParser(description='Probe and fully decode a generated GDP video')
    parser.add_argument('video', type=Path)
    parser.add_argument('--duration', type=float, required=True)
    args = parser.parse_args()
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format',
                                              '-of', 'json', str(args.video)]))
    stream = next((entry for entry in probe['streams'] if entry['codec_type'] == 'video'), None)
    if stream is None:
        raise SystemExit('No video stream')
    if (stream['width'], stream['height'], stream['r_frame_rate']) != (1080, 1920, '30/1'):
        raise SystemExit('Unexpected resolution or frame rate')
    if abs(float(probe['format']['duration']) - args.duration) > 1 / 30:
        raise SystemExit('Unexpected duration')
    if int(stream['nb_frames']) != round(args.duration * 30):
        raise SystemExit('Unexpected frame count')
    subprocess.run(['ffmpeg', '-v', 'error', '-i', str(args.video), '-f', 'null', '-'], check=True)
    report = {'video': str(args.video.resolve()), 'duration_seconds': float(probe['format']['duration']),
              'resolution': [1080, 1920], 'fps': 30, 'frames': int(stream['nb_frames']),
              'audio_streams': sum(entry['codec_type'] == 'audio' for entry in probe['streams']),
              'sha256': hashlib.sha256(args.video.read_bytes()).hexdigest(), 'full_decode': 'FFmpeg exit 0'}
    (OUTPUT / f'{args.video.stem}-verification.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
