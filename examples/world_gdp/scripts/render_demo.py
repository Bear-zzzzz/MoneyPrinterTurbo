import json
import math
import subprocess
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from paths import PROJECT, DATA, OUTPUT, ASSETS


ROOT = OUTPUT
WIDTH, HEIGHT, FPS = 1080, 1920, 30
YEAR_SECONDS, TRANSITION_SECONDS = 3.2, 3.2
START, GAP = 445, 105
BAR_LEFT, BAR_RIGHT = 260, 1010
STYLES = {
    'USA': ('美国', '#59A8FF'), 'SUN': ('苏联', '#F56268'),
    'JPN': ('日本', '#F0A0BD'), 'DEU': ('西德', '#E5BE68'),
    'FRA': ('法国', '#9A8AE8'), 'GBR': ('英国', '#5DD6CE'),
    'ITA': ('意大利', '#72C692'), 'CHN': ('中国', '#E88745'),
    'CAN': ('加拿大', '#E8ABCD'), 'IND': ('印度', '#C6CD70'),
    'BRA': ('巴西', '#69D998'),
}
EVENTS = {
    1970: ('不扩散核武器条约生效', '核不扩散进入国际条约框架'),
    1971: ('联合国大会通过第2758号决议', '恢复中华人民共和国在联合国的合法权利'),
    1972: ('斯德哥尔摩人类环境会议', '环境议题进入全球合作议程'),
    1973: ('石油禁运与能源危机', '国际能源供应和价格受到冲击'),
    1974: ('罗马世界粮食会议', '各国讨论粮食安全与国际合作'),
    1975: ('赫尔辛基最后文件签署', '欧洲安全与合作进程的重要节点'),
}


@lru_cache(maxsize=30)
def font(size):
    return ImageFont.truetype(str(PROJECT / 'resource/fonts/STHeitiMedium.ttc'), size)


def text(draw, position, content, size=30, color='#E7EEF8', anchor=None):
    draw.text(position, content, font=font(size), fill=color, anchor=anchor)


def rolling_text(value):
    return f'{value:,.1f}'


def annual_progress(elapsed):
    return min(1, max(0, elapsed / (TRANSITION_SECONDS - 1 / FPS)))


def build_years():
    wb = json.loads((DATA / 'raw/worldbank-gdp.json').read_text())
    metadata = json.loads((DATA / 'raw/worldbank-countries.json').read_text())[1]
    eligible = {row['id'] for row in metadata if row['region']['id'] != 'NA'}
    historical = json.loads((DATA / 'un-historical-gdp.json').read_text())['records']
    identities = {'USSR (Former)': 'SUN', 'Czechoslovakia (Former)': 'CSK', 'Yugoslavia (Former)': 'YUG'}
    successor_codes = {'RUS', 'UKR', 'BLR', 'MDA', 'EST', 'LVA', 'LTU', 'ARM', 'AZE',
                       'GEO', 'KAZ', 'KGZ', 'TJK', 'TKM', 'UZB', 'CZE', 'SVK', 'SVN',
                       'HRV', 'BIH', 'MKD', 'SRB', 'MNE', 'XKX'}
    output = []
    for year in range(1970, 1976):
        values = [{'code': row['countryiso3code'], 'value': row['value'] / 1e9,
                   'status': 'source_published', 'source': 'World Bank'}
                  for row in wb[1] if row['date'] == str(year)
                  and row['countryiso3code'] in eligible - successor_codes
                  and row['value'] is not None and row['value'] > 0]
        for row in historical:
            if row['country'] in identities and str(year) in row['values_usd']:
                values.append({'code': identities[row['country']],
                               'value': row['values_usd'][str(year)] / 1e9,
                               'status': 'source_published', 'source': 'UN National Accounts'})
        selected = sorted(values, key=lambda row: (-row['value'], row['code']))[:10]
        output.append({'year': year, 'top10': selected, 'event': EVENTS[year],
                       'certified_complete_world_ranking': False})
    return output


def transition_rows(previous, current, fraction):
    eased = max(0, min(1, fraction))
    eased = eased * eased * (3 - 2 * eased)
    old = {row['code']: (index, row) for index, row in enumerate(previous)}
    new = {row['code']: (index, row) for index, row in enumerate(current)}
    output = []
    for code in sorted(set(old) | set(new)):
        old_position, old_record = old.get(code, (10.4, new[code][1])) if code not in old else old[code]
        new_position, new_record = new.get(code, (10.4, old_record))
        value = old_record['value'] + (new_record['value'] - old_record['value']) * eased
        if fraction >= 1:
            value = new_record['value']
        opacity = eased if code not in old else (1 - eased if code not in new else 1)
        output.append({'code': code, 'value': value,
                       'position': old_position + (new_position - old_position) * eased,
                       'opacity': opacity, 'rank_change': old_position - new_position,
                       'new_entry': code not in old})
    return output


@lru_cache(maxsize=20)
def flag(code):
    with Image.open(ASSETS / f'flags/{code}.png') as image:
        image = image.convert('RGBA')
        image.thumbnail((66, 43), Image.Resampling.LANCZOS)
        output = Image.new('RGBA', (66, 43))
        output.alpha_composite(image, ((66 - image.width) // 2, (43 - image.height) // 2))
        return output


def number_image(previous, current, progress, color):
    old_string = rolling_text(previous).rjust(9)
    new_string = rolling_text(current).rjust(9)
    tile = Image.new('RGBA', (297, 60))
    draw = ImageDraw.Draw(tile)
    for index, (old_digit, new_digit) in enumerate(zip(old_string, new_string)):
        horizontal = index * 33
        if not new_digit.isdigit() or progress >= 1:
            draw.text((horizontal, 8), new_digit, font=font(39), fill=color)
        else:
            phase = progress % 1
            if old_digit.strip():
                draw.text((horizontal, int(8 - 60 * phase)), old_digit, font=font(39), fill=color)
            draw.text((horizontal, int(68 - 60 * phase)), new_digit, font=font(39), fill=color)
    return tile


def counter_image(value, color):
    tile = Image.new('RGBA', (297, 60))
    draw = ImageDraw.Draw(tile)
    for index, character in enumerate(rolling_text(value).rjust(9)):
        draw.text((index * 33, 8), character, font=font(39), fill=color)
    return tile


def background():
    image = Image.new('RGB', (WIDTH, HEIGHT), '#060B14')
    draw = ImageDraw.Draw(image)
    for horizontal in range(0, WIDTH, 80):
        draw.line((horizontal, 0, horizontal, HEIGHT), fill='#0B1423')
    for vertical in range(0, HEIGHT, 80):
        draw.line((0, vertical, WIDTH, vertical), fill='#0B1423')
    text(draw, (66, 90), '世界 GDP · TOP 10', 65)
    text(draw, (70, 180), '1970—1975  /  历史国家动态排名 DEMO', 27, '#91A6BF')
    text(draw, (70, 228), '含苏联 · 跨来源试排，历史覆盖仍在核验', 27, '#E5BE68')
    text(draw, (70, 370), '国家 / 当时身份', 25, '#91A6BF')
    text(draw, (1010, 370), '名义 GDP · 十亿美元', 25, '#91A6BF', 'ra')
    for rank in range(10):
        text(draw, (46, START + rank * GAP + 24), f'{rank + 1:02d}', 29, '#637791', 'mm')
        draw.line((78, START + rank * GAP + 87, 1010, START + rank * GAP + 87), fill='#192539')
    text(draw, (70, 1516), '1970', 25, '#91A6BF')
    text(draw, (1010, 1516), '1975', 25, '#91A6BF', 'ra')
    text(draw, (70, 1795), '来源：World Bank＋UN；不含 BGM / 配音', 25, '#91A6BF')
    text(draw, (70, 1840), '横条刻度固定0—1800；过渡非真实月度数据', 25, '#91A6BF')
    return image


def render_frame(seconds, years, base):
    segment = min(len(years) - 1, int(seconds / YEAR_SECONDS))
    elapsed = seconds - segment * YEAR_SECONDS
    current = years[segment]
    previous = years[max(0, segment - 1)]
    fraction = annual_progress(elapsed) if segment else 1
    active = segment > 0 and fraction < 1
    now = transition_rows(previous['top10'], current['top10'], fraction)
    image = base.copy().convert('RGBA')
    draw = ImageDraw.Draw(image)
    text(draw, (62, 282), str(current['year']), 77, '#64E6D2')
    text(draw, (1010, 316), '年度切换' if active else '年度数据', 31, '#64E6D2', 'ra')
    panel = Image.new('RGBA', (WIDTH, 10 * GAP))
    maximum = 1800
    glow = Image.new('RGBA', panel.size)
    glow_draw = ImageDraw.Draw(glow)
    for row in sorted(now, key=lambda item: abs(item['rank_change'])):
        if row['opacity'] <= 0:
            continue
        code = row['code']
        name, color = STYLES[code]
        vertical = row['position'] * GAP
        shift = 0
        if active and abs(row['rank_change']) > 0.1 and not row['new_entry']:
            shift = 40 * math.sin(fraction * math.pi) * (1 if row['rank_change'] > 0 else -1)
        layer = Image.new('RGBA', (WIDTH, GAP - 8))
        layer_draw = ImageDraw.Draw(layer)
        layer.alpha_composite(flag(code), (int(82 + shift), 4))
        text(layer_draw, (162 + shift, 7), name, 36, color)
        length = max(2, (BAR_RIGHT - BAR_LEFT) * row['value'] / maximum)
        layer_draw.rounded_rectangle((BAR_LEFT, 62, BAR_LEFT + length, 81), radius=5, fill=color)
        layer.alpha_composite(counter_image(row['value'], color), (713, 0))
        if active and row['rank_change'] > 0.1:
            text(layer_draw, (430, 7), '新进榜' if row['new_entry'] else '位次上升', 21, '#64E6D2')
            glow_draw.line((BAR_LEFT, vertical + 73, BAR_LEFT + length, vertical + 73), fill=color, width=13)
            layer_draw.line((BAR_LEFT + length, 56, BAR_LEFT + length, 88), fill='#F5FFFF', width=2)
        if row['opacity'] < 1:
            layer.putalpha(layer.getchannel('A').point(lambda value: int(value * row['opacity'])))
        panel.alpha_composite(layer, (0, int(vertical)))
    panel = Image.alpha_composite(glow.filter(ImageFilter.GaussianBlur(8)), panel)
    image.alpha_composite(panel, (0, START))
    draw = ImageDraw.Draw(image)
    progress = min(1, seconds / (YEAR_SECONDS * len(years) - 1))
    draw.line((70, 1489, 1010, 1489), fill='#22334A', width=5)
    draw.line((70, 1489, 70 + 940 * progress, 1489), fill='#64E6D2', width=5)
    event_color = '#E5BE68'
    draw.rounded_rectangle((65, 1580, 1015, 1750), radius=16, fill='#111C2D', outline='#304259')
    text(draw, (90, 1595), f'{current["year"]} · 国际大事', 24, event_color)
    text(draw, (90, 1640), current['event'][0], 37)
    text(draw, (90, 1700), current['event'][1], 26, '#91A6BF')
    if active:
        burst = math.sin(fraction * math.pi) * 8
        draw.line((65, 1580, 1015, 1580), fill=event_color, width=max(1, int(burst)))
    return image.convert('RGB')


def main():
    years = build_years()
    entrants = {row['code'] for year in years for row in year['top10']}
    for code in entrants:
        assert code in STYLES
        flag(code)
    for year in years:
        assert year['year'] in EVENTS
    (ROOT / 'v3-rankings.json').write_text(json.dumps({'unit': 'billion current USD',
        'not_certified_complete_global_ranking': True,
        'historical_notes': ['Includes USSR, former Czechoslovakia and Yugoslavia as candidates; only ten largest available entries displayed.',
                             'German series labeled West Germany for this demo; geographic completeness including East Germany remains under review.',
                             'All years sampled here have source-published USSR values; the separate 1960s model backcast is not used in this demo.',
                             'Annual values settle to source numbers; transition values are animation only.'],
        'styles': STYLES, 'years': years}, ensure_ascii=False, indent=2))
    (ROOT / 'v3-animation.json').write_text(json.dumps({
        'continuous_digit_roll': False, 'number_mode': 'stationary count-up/count-down',
        'numeric_column_x': 713, 'digit_baseline_y': 8,
        'annual_interval_seconds': YEAR_SECONDS, 'duration_seconds': YEAR_SECONDS * len(years),
        'annual_endpoints': 'Exact source value at last frame of each annual interval',
        'intermediate_values': 'Animation interpolation, not monthly observations',
        'first_year': 'Source values remain unchanged; no fictitious initial increase',
        'decreasing_data': 'Count down to the actual lower endpoint, never force monotonic increase',
        'bgm': False, 'voiceover': False,
    }, ensure_ascii=False, indent=2))
    output = ROOT / 'world-gdp-top10-1970-1975-counter-v3.mp4'
    duration = YEAR_SECONDS * len(years)
    frame_count = round(duration * FPS)
    command = ['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-f', 'rawvideo',
               '-pix_fmt', 'rgb24', '-s', f'{WIDTH}x{HEIGHT}', '-r', str(FPS), '-i', 'pipe:0',
               '-an', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18',
               '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(output)]
    base = background()
    previews = []
    with subprocess.Popen(command, stdin=subprocess.PIPE) as encoder:
        try:
            for frame_index in range(frame_count):
                image = render_frame(frame_index / FPS, years, base)
                encoder.stdin.write(image.tobytes())
                if frame_index in (60, 174, 462, 558):
                    image.save(ROOT / f'v3-frame-{frame_index:03d}.png')
                    previews.append(image.resize((270, 480), Image.Resampling.LANCZOS))
                if frame_index % FPS == 0:
                    print(f'Rendered {frame_index // FPS}/{duration:.1f}s', flush=True)
        finally:
            encoder.stdin.close()
        if encoder.wait() != 0:
            raise RuntimeError('FFmpeg failed')
    preview = Image.new('RGB', (1080, 480))
    for index, image in enumerate(previews):
        preview.paste(image, (index * 270, 0))
    preview.save(ROOT / 'v3-preview.png')
    print(output, flush=True)


if __name__ == '__main__':
    main()
