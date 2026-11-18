import argparse
import json
import math
import subprocess
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from full_data import STYLES, build_dataset, save_dataset
from render_demo import font
from motion import build_tracks, composite_subpixel, sample_track
from paths import OUTPUT, ASSETS


ROOT = OUTPUT
WIDTH, HEIGHT, FPS = 1080, 1920, 30
YEAR_SECONDS = 1.6
SCREEN_COPY = 'GDP · 亿美元'
DISPLAY_DIVISOR = 1e8
AXIS_HEADROOM = 1.08
TOP, ROW_GAP = 385, 110
BAR_LEFT, BAR_RIGHT = 85, 780
EVENT_FONT_SIZE, EVENT_LINE_CHARACTERS = 46, 11
INTERVAL_FRAMES = round(YEAR_SECONDS * FPS)


def label(draw, position, content, size, color='#EFF5FF', anchor=None):
    draw.text(position, content, font=font(size), fill=color, anchor=anchor)


def frame_state(seconds, dataset):
    years = dataset['years']
    frame_index = min(len(years) * INTERVAL_FRAMES - 1, max(0, round(seconds * FPS)))
    segment = frame_index // INTERVAL_FRAMES
    local_frame = frame_index % INTERVAL_FRAMES
    current = years[segment]
    previous = years[max(0, segment - 1)]
    fraction = (local_frame + 1) / INTERVAL_FRAMES if segment else 1
    coordinate = max(0,(frame_index-(INTERVAL_FRAMES-1))/INTERVAL_FRAMES)
    signature = tuple(tuple((row['code'],row['value_usd']) for row in year['candidates'] if row['code'] in STYLES) for year in years)
    tracks = build_tracks(signature,tuple(sorted(STYLES)))
    old = {row['code']: row for row in previous['candidates']}
    new = {row['code']: row for row in current['candidates']}
    values = []
    render_rows = []
    for code, track in tracks.items():
        amount = sample_track(track['values'],track['value_slopes'],coordinate)
        position = sample_track(track['positions'],track['position_slopes'],coordinate)
        first = old.get(code,{'value_usd':0,'status':'missing'})
        second = new.get(code,{'value_usd':0,'status':first['status']})
        row = {'code':code,'value_usd':amount,'status':second['status'],
               'old_value_usd':first['value_usd'],'new_value_usd':second['value_usd'],
               'position':position}
        render_rows.append(row)
        if amount > 0:
            values.append(row)
    values.sort(key=lambda row: (-row['value_usd'], row['code']))
    chosen = values[:10]
    missing_colors = {row['code'] for row in current['top10']} - set(STYLES)
    if missing_colors:
        raise ValueError(f'Missing country styles: {missing_colors}')
    ceiling = chosen[0]['value_usd'] * AXIS_HEADROOM
    return {'year': current['year'], 'rows': chosen, 'render_rows':render_rows,'fraction': fraction,
            'axis_max_usd': ceiling, 'event': current['event']}


@lru_cache(maxsize=40)
def flag_asset(code, year):
    asset = code
    if code == 'BRA' and year <= 1991 and (ASSETS / 'flags/BRA_1968_1992.png').exists():
        asset = 'BRA_1968_1992'
    if code == 'ESP' and year <= 1976 and (ASSETS / 'flags/ESP_1945_1977.png').exists():
        asset = 'ESP_1945_1977'
    if code == 'ESP' and 1977 <= year <= 1980 and (ASSETS / 'flags/ESP_1977_1981.png').exists():
        asset = 'ESP_1977_1981'
    if code == 'RUS' and year <= 1993 and (ASSETS / 'flags/RUS_1991_1993.png').exists():
        asset = 'RUS_1991_1993'
    with Image.open(ASSETS / f'flags/{asset}.png') as source:
        image = source.convert('RGBA')
    image.thumbnail((70, 46), Image.Resampling.LANCZOS)
    output = Image.new('RGBA', (70, 46))
    output.alpha_composite(image, ((70 - image.width) // 2, (46 - image.height) // 2))
    return output


@lru_cache(maxsize=1024)
def numeric_tile(value, color):
    content = f'{value:,.1f}'
    tile = Image.new('RGBA', (len(content) * 23 + 4, 50))
    draw = ImageDraw.Draw(tile)
    for index, character in enumerate(content):
        draw.text((index * 23, 8), character, font=font(34), fill=color)
    return tile


def bar_geometry(row, state):
    end = BAR_LEFT + (BAR_RIGHT - BAR_LEFT) * row['value_usd'] / state['axis_max_usd']
    return {'bar_end': end, 'number_x': end + 12, 'number_y': 50}


def base_image():
    image = Image.new('RGB', (WIDTH, HEIGHT), '#050A12')
    draw = ImageDraw.Draw(image)
    for position in range(0, WIDTH, 90):
        draw.line((position, 0, position, HEIGHT), fill='#0B1421')
    for position in range(0, HEIGHT, 90):
        draw.line((0, position, WIDTH, position), fill='#0B1421')
    label(draw, (85, 265), SCREEN_COPY, 29, '#9EB2CC')
    for index in range(10):
        vertical = TOP + index * ROW_GAP + 94
        draw.line((BAR_LEFT, vertical, 1005, vertical), fill='#16253A')
    return image


def split_headline(content, maximum=21):
    lines = []
    for paragraph in content.splitlines():
        if len(paragraph) > maximum:
            clauses = paragraph.split('，')
            if len(clauses) == 2 and all(0 < len(clause) <= maximum for clause in clauses):
                lines.extend(clauses)
                continue
            quote = paragraph.find('“')
            if 0 < quote <= maximum and len(paragraph) - quote <= maximum:
                lines.extend((paragraph[:quote], paragraph[quote:]))
                continue
        width = maximum
        if maximum < len(paragraph) <= maximum * 2 and len(paragraph) - maximum <= 4:
            width = math.ceil(len(paragraph) / 2)
        lines.extend(paragraph[index:index + width] for index in range(0, len(paragraph), width))
    return lines


def render_frame(seconds, dataset, base, presentation=None):
    state = frame_state(seconds, dataset)
    headline = presentation.get('headline_override',state['event']['headline']) if presentation else state['event']['headline']
    image = base.copy().convert('RGBA')
    header = Image.new('RGBA',(WIDTH,235))
    header_draw = ImageDraw.Draw(header)
    label(header_draw, (72, 97), str(state['year']), 123, '#75EFDA')
    if headline:
        header_draw.rounded_rectangle((420, 80, 1015, 222), radius=12, fill='#151B28', outline='#53472D', width=2)
        header_draw.line((426, 100, 426, 203), fill='#E7C47D', width=4)
        for index, line in enumerate(split_headline(headline, EVENT_LINE_CHARACTERS)):
            header_draw.text((440, 94 + index * 59), line, font=font(EVENT_FONT_SIZE), fill='#FFE2A0', stroke_width=1, stroke_fill='#FFE2A0')
    if presentation:
        header.putalpha(header.getchannel('A').point(lambda amount:round(amount*presentation['header_opacity'])))
    image.alpha_composite(header)
    if presentation and presentation['scene_opacity']>0:
        scene_layer=Image.new('RGBA',image.size)
        scene_draw=ImageDraw.Draw(scene_layer)
        color='#F07A91' if presentation['kind']=='crisis' else '#75EFDA'
        scene_draw.rounded_rectangle((415,246,1015,291),radius=8,fill='#162638')
        label(scene_draw,(430,252),presentation['caption'],28,color)
        scene_layer.putalpha(scene_layer.getchannel('A').point(lambda amount:round(amount*presentation['scene_opacity'])))
        image.alpha_composite(scene_layer)
    draw = ImageDraw.Draw(image)
    draw.line((85, 232, 1005, 232), fill='#254257', width=2)
    leader = state['rows'][0]
    leader_color = STYLES[leader['code']][1]
    draw.line((85, 232, 260, 232), fill=leader_color, width=4)
    draw.line((BAR_LEFT, 335, BAR_RIGHT, 335), fill='#254257', width=2)
    for fraction in (0, 0.5, 1):
        horizontal = BAR_LEFT + (BAR_RIGHT - BAR_LEFT) * fraction
        amount = state['axis_max_usd'] * fraction / DISPLAY_DIVISOR
        draw.line((horizontal, 328, horizontal, 342), fill='#91A6BF', width=2)
        label(draw, (horizontal, 305), f'{amount:,.0f}', 24, '#91A6BF',
              anchor='lt' if fraction == 0 else ('rt' if fraction == 1 else 'mt'))
    panel = Image.new('RGBA', (WIDTH, 10 * ROW_GAP))
    glow = Image.new('RGBA', panel.size)
    glow_draw = ImageDraw.Draw(glow)
    fraction = state['fraction']
    pulse = math.sin(fraction * math.pi)
    for row in sorted(state['render_rows'],key=lambda item:item['position'],reverse=True):
        if row['position'] >= 10 or row['value_usd'] <= 0:
            continue
        code = row['code']
        if presentation and code in presentation.get('hidden_codes',[]):
            continue
        name, color, _ = STYLES[code]
        if code == 'DEU' and state['year'] < 1990:
            name = '西德'
        position = row['position'] * ROW_GAP
        layer = Image.new('RGBA', (WIDTH, ROW_GAP - 5))
        layer_draw = ImageDraw.Draw(layer)
        layer.alpha_composite(flag_asset(code, state['year']), (85, 0))
        label(layer_draw, (174, 3), name, 37, color)
        number = round(row['value_usd'] / DISPLAY_DIVISOR, 1)
        geometry = bar_geometry(row, state)
        composite_subpixel(layer,numeric_tile(number, color),(geometry['number_x'], geometry['number_y']))
        length = geometry['bar_end'] - BAR_LEFT
        layer_draw.rounded_rectangle((BAR_LEFT, 63, geometry['bar_end'], 87), radius=5, fill=color)
        if presentation and presentation['strength']>0:
            strength=presentation['strength']
            if code in presentation['codes']:
                highlight=Image.new('RGBA',layer.size)
                highlight_draw=ImageDraw.Draw(highlight)
                highlight_draw.rounded_rectangle((78,0,1020,100),radius=9,outline=color,width=3)
                highlight_draw.line((BAR_LEFT,75,geometry['bar_end'],75),fill=color,width=18)
                highlight=highlight.filter(ImageFilter.GaussianBlur(5))
                highlight.putalpha(highlight.getchannel('A').point(lambda amount:round(amount*0.7*strength)))
                layer=Image.alpha_composite(highlight,layer)
                layer_draw=ImageDraw.Draw(layer)
                layer_draw.line((geometry['bar_end'],59,geometry['bar_end'],91),fill=(235,255,255,round(255*strength)),width=3)
                layer_draw.line((80,2,260,2),fill=(235,255,255,round(210*strength)),width=2)
            elif presentation['codes']:
                layer.putalpha(layer.getchannel('A').point(lambda amount:round(amount*(1-0.28*strength))))
            if presentation['kind']=='crisis':
                layer_draw.line((80,100,1005,100),fill=(180,65,90,round(100*strength)),width=2)
        if pulse > 0:
            delta = abs(row['new_value_usd'] - row['old_value_usd']) / max(1, row['old_value_usd'])
            strength = min(1, delta * 5) * pulse
            if strength > 0.03:
                glow_draw.line((BAR_LEFT, position + 75, BAR_LEFT + length, position + 75), fill=color,
                               width=max(3, int(10 * strength)))
                layer_draw.line((BAR_LEFT + length, 61, BAR_LEFT + length, 89), fill='#EBFFFF', width=2)
        if row['position'] > 9:
            opacity = 10-row['position']
            layer.putalpha(layer.getchannel('A').point(lambda amount:round(amount*opacity)))
        composite_subpixel(panel,layer,(0,position))
    panel = Image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(6)), panel)
    image.alpha_composite(panel, (0, TOP))
    draw = ImageDraw.Draw(image)
    progress = min(1, seconds / (len(dataset['years']) * YEAR_SECONDS - 1 / FPS))
    draw.line((85, 1580, 1005, 1580), fill='#20364D', width=4)
    draw.line((85, 1580, 85 + 920 * progress, 1580), fill=leader_color, width=4)
    return image.convert('RGB')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--duration', type=float, help='Optional short render for checking')
    parser.add_argument('--start-year', type=int, default=1960)
    args = parser.parse_args()
    dataset = save_dataset()
    if args.start_year != 1960:
        dataset = {**dataset, 'years': [row for row in dataset['years'] if row['year'] >= args.start_year]}
    if not dataset['years']:
        parser.error('Start year outside dataset')
    duration = args.duration if args.duration is not None else len(dataset['years']) * YEAR_SECONDS
    if duration <= 0 or duration > len(dataset['years']) * YEAR_SECONDS:
        parser.error('Duration outside dataset')
    output = ROOT / ('world-gdp-history-v9-test.mp4' if args.duration is not None else
                     'world-gdp-1960-2025-history-smooth-motion-2x-v9-picture.mp4')
    entrants = {row['code'] for year in dataset['years'] for row in year['top10']}
    for code in entrants:
        flag_asset(code, dataset['years'][0]['year'])
    base = base_image()
    frame_count = round(duration * FPS)
    command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo',
               '-pix_fmt', 'rgb24', '-s', f'{WIDTH}x{HEIGHT}', '-r', str(FPS), '-i', 'pipe:0',
               '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
               '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(output)]
    preview_indices = {round(seconds * FPS) for seconds in (1.56, 18.5, 50.5, 82.5, duration - 1 / FPS)
                       if 0 <= seconds < duration}
    thumbnails = []
    with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
        try:
            for frame_index in range(frame_count):
                image = render_frame(frame_index / FPS, dataset, base)
                encoder.stdin.write(image.tobytes())
                if frame_index in preview_indices:
                    image.save(ROOT / f'v9-frame-{frame_index:04d}.png')
                    thumbnails.append(image.resize((270, 480), Image.Resampling.LANCZOS))
                if frame_index % (FPS * 10) == 0:
                    print(f'Rendered {frame_index / FPS:.0f}/{duration:.1f}s', flush=True)
        finally:
            encoder.stdin.close()
        if encoder.wait() != 0:
            raise RuntimeError('FFmpeg encoding failed')
    if thumbnails:
        preview = Image.new('RGB', (270 * len(thumbnails), 480))
        for index, thumbnail in enumerate(thumbnails):
            preview.paste(thumbnail, (270 * index, 0))
        preview.save(ROOT / 'v9-preview.png')
    (ROOT / 'v9-animation.json').write_text(json.dumps({
        'period': [dataset['years'][0]['year'], dataset['years'][-1]['year']],
        'year_seconds': YEAR_SECONDS, 'speed_vs_v3': 2, 'duration_seconds': duration,
        'fps': FPS, 'resolution': [WIDTH, HEIGHT], 'rank_numbers_visible': False,
        'explanatory_prose_visible': False, 'essential_unit_label': SCREEN_COPY,
        'numeric_animation': 'Continuous monotone cubic Hermite GDP tracks across annual knots, exact endpoints, no repeated boundary frame; direct count-up/count-down with subpixel bar-tail placement',
        'number_position': 'bar endpoint +12px, row y50, 34px fixed-width glyphs; bar axis x85..780 reserves right margin',
        'timeline': 'Annual GDP values are endpoints; in-between are only animation interpolation',
        'rank_animation': 'Monotone cubic annual ordinal trajectories, offscreen rank capped at10.5, subpixel rows and faded clipped entries/exits; visual subannual rank is animation not observation',
        'display_divisor_usd': DISPLAY_DIVISOR,
        'axis': 'Zero baseline; interpolated current leader × 1.08, continuous numeric 亿美元 ticks; no staged expansion',
        'axis_headroom_factor': AXIS_HEADROOM,
        'leader_bar_fraction': 1 / AXIS_HEADROOM,
        'axis_annual_maxima_usd': [year['top10'][0]['value_usd'] * AXIS_HEADROOM for year in dataset['years']],
        'events': 'User-approved representative historical events, 30 selected years, other years blank; 1991 explicitly two lines',
        'event_position': 'Prominent top-right accented panel x420..1015 y80..222, 46px titles, balanced wrap at 11 chars; no bottom event text',
        'reference_video': 'BV1CuEK6KEEN; layout reference only, no video/audio reused',
        'output': str(output.name), 'bgm_status': 'Awaiting the three requested local audio files',
    }, ensure_ascii=False, indent=2))
    print(output, flush=True)


if __name__ == '__main__':
    main()
