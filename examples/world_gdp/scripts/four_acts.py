import math
import random

from PIL import Image, ImageDraw, ImageFilter

from full_data import STYLES
from motion import composite_subpixel
from render_full import BAR_LEFT, BAR_RIGHT, DISPLAY_DIVISOR, FPS, HEIGHT, TOP, ROW_GAP, WIDTH, base_image, bar_geometry, flag_asset, font, frame_state, numeric_tile, render_frame
from storyboard import fade_envelope


DURATION=30
ACT_SECONDS=7.5


def knot_seconds(year):
    return ((year-1960+1)*48-1)/FPS


def build_four_acts(dataset):
    years={row['year']:row for row in dataset['years']}
    peaks=[]
    for year in dataset['years']:
        top=year['top10']
        if year['year']>=1970 and top[0]['code']=='USA' and all(row['status']=='provider_reported' for row in top[:2]):
            peaks.append({'year':year['year'],'ratio':top[0]['value_usd']/top[1]['value_usd'],'runnerup':top[1]['code']})
    peak=max(peaks,key=lambda row:row['ratio'])
    soviet=next(row for row in years[1991]['top10'] if row['code']=='SUN')
    crossing=None
    for index in range(round(knot_seconds(2009)*FPS),round(knot_seconds(2011)*FPS)+1):
        state=frame_state(index/FPS,dataset)
        values={row['code']:row['value_usd'] for row in state['render_rows']}
        if values['CHN']>=values['JPN']:
            crossing=index/FPS
            break
    if crossing is None:
        raise ValueError('CHN/JPN crossing missing')
    return {
        'duration_seconds':DURATION,'usa_peak':peak,
        'usa_peak_scope':'Saved1970–2025 annual Top10 with provider-reported leader and runner-up; not certified complete historical world coverage',
        'soviet_last':soviet,'soviet_last_position':next(index for index,row in enumerate(years[1991]['top10']) if row['code']=='SUN'),
        'crossing_global_seconds':crossing,
        'crossing_note':'Frame-sampled animation crossing, not actual historical date',
        'acts':[
            {'code':'USA','focus_codes':['USA'],'period':[peak['year']-3,peak['year']],'title':'美国 · 一骑绝尘','color':'#59A8FF'},
            {'code':'JPN','focus_codes':['JPN'],'period':[1985,2001],'title':'日本 · 疾速追赶','color':'#F0A0BD'},
            {'code':'SUN','focus_codes':['SUN'],'period':[1990,1992],'title':'苏联 · 时代落幕','color':'#F56268'},
            {'code':'CHN','focus_codes':['CHN','JPN'],'period':[2001,2012],'title':'中国 · 追赶与超越','color':'#FF9B50'},
        ],
        'caveats':['Nominal currentUSD changes are not actual economic growth rates.',
                    'Japan nominalUSD GDP keeps actual source path through1995 peak; no fabricated1990 stop.',
                    'USSR1991 GDP is user-authorized estimate; final number is held while identity disappears, never counted tozero.',
                    'Four periods are edited time jumps, not a continuous30second history timeline.',
                    'Ranking coverage remains historically incomplete; flag-era limitations retained.'],
    }


def shot_at(seconds, design, dataset):
    seconds=min(DURATION-1/FPS,max(0,seconds))
    index=min(3,int(seconds/ACT_SECONDS))
    elapsed=seconds-index*ACT_SECONDS
    act=design['acts'][index]
    fraction=elapsed/(ACT_SECONDS-1/FPS)
    start,end=act['period']
    global_seconds=knot_seconds(start)+(knot_seconds(end)-knot_seconds(start))*fraction
    phase='lead' if index==0 else ('catchup' if index==1 else ('dissolve' if index==2 else 'pursuit'))
    title=act['title']
    dissolve=0
    if index==1:
        if elapsed<3.8:
            global_seconds=knot_seconds(1985)+(knot_seconds(1995)-knot_seconds(1985))*elapsed/3.8
        else:
            global_seconds=knot_seconds(1995)+(knot_seconds(2001)-knot_seconds(1995))*(elapsed-3.8)/(ACT_SECONDS-1/FPS-3.8)
            phase='cooldown'
            title='日本 · 追赶势头转弱'
    if index==2:
        if elapsed<3.5:
            global_seconds=knot_seconds(1990)+(knot_seconds(1991)-knot_seconds(1990))*elapsed/3.5
        else:
            global_seconds=knot_seconds(1991)+(knot_seconds(1992)-knot_seconds(1991))*(elapsed-3.5)/(ACT_SECONDS-1/FPS-3.5)
            dissolve=min(1,(elapsed-3.5)/2.1)
            title='苏联解体 · 国家退出'
    crossing_local=(design['crossing_global_seconds']-knot_seconds(2001))/(knot_seconds(2012)-knot_seconds(2001))*(ACT_SECONDS-1/FPS)
    if index==3 and elapsed>=crossing_local:
        phase='overtake'
        title='中国 · 超越日本'
    opacity=fade_envelope(elapsed,ACT_SECONDS-1/FPS,0.4)
    caption=f'{start}—{end} · '+{'USA':'领先格局','JPN':'名义美元GDP轨迹','SUN':'历史国家退出','CHN':'快速追赶与位次交替'}[act['code']]
    presentation={'header_opacity':1,'scene_opacity':1,'strength':0.95,
                  'codes':act['focus_codes'],'caption':caption,'kind':'country',
                  'headline_override':title,'hidden_codes':['SUN'] if index==2 and elapsed>=3.5 else []}
    return {'index':index,'elapsed':elapsed,'fraction':fraction,'global_seconds':global_seconds,
            'opacity':opacity,'range_caption':caption,'presentation':presentation,'phase':phase,
            'color':act['color'],'dissolve':dissolve,'crossing_local_seconds':crossing_local,
            'soviet_display_usd':design['soviet_last']['value_usd'],
            'soviet_estimated':design['soviet_last']['status']=='estimated'}


def fracture_particles(progress):
    generator=random.Random(1991)
    pieces=[]
    for index in range(60):
        speed=generator.uniform(80,480)
        horizontal=generator.uniform(-110,380)
        pieces.append({'index':index,'dx':horizontal*progress,'dy':speed*progress+480*progress**2,
                       'rotation':generator.uniform(-110,110)*progress,'opacity':max(0,1-progress)**0.6})
    return pieces


def draw_energy(image, state, shot):
    layer=Image.new('RGBA',image.size)
    draw=ImageDraw.Draw(layer)
    code=['USA','JPN','SUN','CHN'][shot['index']]
    rows={row['code']:row for row in state['render_rows']}
    if code not in rows:
        return image
    row=rows[code]
    if row['position']>=10 or (code=='SUN' and shot['dissolve']>0):
        return image
    end=bar_geometry(row,state)['bar_end']
    vertical=TOP+row['position']*ROW_GAP+75
    cooling=min(1,max(0,(shot['elapsed']-3.6)/1.1)) if code=='JPN' else 0
    intensity=1-0.85*cooling
    color=shot['color']
    left=BAR_LEFT+((shot['elapsed']*0.6)%1)*(end-BAR_LEFT)
    for offset,width in ((0,14),(-10,6),(10,6)):
        draw.line((max(BAR_LEFT,left-70),vertical+offset,min(end,left+70),vertical+offset),fill=color,width=width)
    if code in ('USA','JPN','CHN'):
        for index in range(24):
            phase=(shot['elapsed']*0.45+index/24)%1
            horizontal=BAR_LEFT+phase*(end-BAR_LEFT)
            height=vertical+math.sin(index*2.4+shot['elapsed']*2)*16
            radius=2+(index%3)
            draw.ellipse((horizontal-radius,height-radius,horizontal+radius,height+radius),fill=color)
        draw.line((BAR_LEFT,vertical-18,end,vertical-18),fill=color,width=2)
        draw.line((BAR_LEFT,vertical+18,end,vertical+18),fill=color,width=2)
    blurred=layer.filter(ImageFilter.GaussianBlur(7))
    blurred.putalpha(blurred.getchannel('A').point(lambda amount:round(amount*0.65*intensity)))
    layer.putalpha(layer.getchannel('A').point(lambda amount:round(amount*0.38*intensity)))
    image=Image.alpha_composite(image,blurred)
    image=Image.alpha_composite(image,layer)
    if code=='CHN':
        delta=shot['elapsed']-shot['crossing_local_seconds']
        if 0<=delta<1.1:
            ring=Image.new('RGBA',image.size)
            ring_draw=ImageDraw.Draw(ring)
            radius=12+130*delta
            opacity=round(170*(1-delta/1.1))
            ring_draw.ellipse((end-radius,vertical-radius,end+radius,vertical+radius),outline=(255,170,80,opacity),width=5)
            image=Image.alpha_composite(image,ring)
    return image


def draw_dissolution(image, state, shot, design):
    if shot['index']!=2 or 'SUN' not in shot['presentation']['hidden_codes']:
        return image
    progress=shot['dissolve']
    row={**design['soviet_last'],'position':design['soviet_last_position']}
    geometry=bar_geometry(row,state)
    top=TOP+row['position']*ROW_GAP
    fragment_source=Image.new('RGBA',(WIDTH,105))
    draw=ImageDraw.Draw(fragment_source)
    fragment_source.alpha_composite(flag_asset('SUN',1991),(85,0))
    draw.rounded_rectangle((85,63,geometry['bar_end'],87),radius=5,fill='#F56268')
    layer=Image.new('RGBA',image.size)
    pieces=fracture_particles(progress)
    rectangles=[]
    for vertical in range(2):
        for horizontal in range(4):
            rectangles.append((85+horizontal*18,vertical*24,85+(horizontal+1)*18,(vertical+1)*24))
    for index in range(36):
        first=85+(geometry['bar_end']-85)*index/36
        second=85+(geometry['bar_end']-85)*(index+1)/36
        rectangles.append((round(first),63,round(second)+1,87))
    for index,rectangle in enumerate(rectangles):
        particle=pieces[index]
        tile=fragment_source.crop(rectangle)
        tile.putalpha(tile.getchannel('A').point(lambda amount:round(amount*particle['opacity'])))
        tile=tile.rotate(particle['rotation'],resample=Image.Resampling.BICUBIC,expand=True)
        composite_subpixel(layer,tile,(rectangle[0]+particle['dx'],top+rectangle[1]+particle['dy']))
    if progress<0.7:
        hold=Image.new('RGBA',(WIDTH,105))
        hold_draw=ImageDraw.Draw(hold)
        hold_draw.text((174,3),'苏联',font=font(37),fill='#F56268')
        composite_subpixel(hold,numeric_tile(round(row['value_usd']/DISPLAY_DIVISOR,1),'#F56268'),(geometry['number_x'],50))
        hold.putalpha(hold.getchannel('A').point(lambda amount:round(amount*(1-progress/0.7))))
        composite_subpixel(layer,hold,(0,top))
    return Image.alpha_composite(image,layer)


def render_four_frame(seconds,dataset,base,design,power_aura=False,side_fire=False,bar_flame=False,clean=False):
    shot=shot_at(seconds,design,dataset)
    state=frame_state(shot['global_seconds'],dataset)
    image=render_frame(shot['global_seconds'],dataset,base,shot['presentation']).convert('RGBA')
    if not bar_flame and not clean:
        image=draw_energy(image,state,shot)
    image=draw_dissolution(image,state,shot,design)
    if clean:
        image=image.convert('RGB')
        return Image.blend(Image.new('RGB',image.size),image,shot['opacity'])
    if side_fire or bar_flame:
        if bar_flame:
            from bar_flame import apply_bar_flame
            image=apply_bar_flame(image,state,shot)
        else:
            from side_fire import apply_side_fire
            image=apply_side_fire(image,state,shot)
        image=image.convert('RGB')
        return Image.blend(Image.new('RGB',image.size),image,shot['opacity'])
    aura=Image.new('RGBA',image.size)
    aura_draw=ImageDraw.Draw(aura)
    color=shot['color']
    for radius in (180,130,80):
        aura_draw.ellipse((830-radius,1700-radius,830+radius,1700+radius),outline=color,width=16)
    aura=aura.filter(ImageFilter.GaussianBlur(22))
    aura.putalpha(aura.getchannel('A').point(lambda amount:round(amount*0.38)))
    image=Image.alpha_composite(image,aura)
    draw=ImageDraw.Draw(image)
    footer_top=1610
    draw.rounded_rectangle((80,footer_top,1005,1810),radius=18,fill='#101D2D',outline=shot['color'],width=2)
    if shot['index']==0:
        values={row['code']:row['value_usd'] for row in state['rows']}
        ratio=values['USA']/state['rows'][1]['value_usd']
        metric=f'美国 / 第二名  {ratio:.2f}倍'
        detail='蓝色领跑 · 差距拉开'
    elif shot['index']==1:
        metric='疾速追赶' if shot['phase']=='catchup' else '追赶势头转弱'
        detail='美元名义总量 · 不是实际经济增速'
    elif shot['index']==2:
        metric='国家解体，身份退出' if shot['dissolve']>0 else '苏联 · 最后的阶段'
        detail='国家退出不等于GDP归零'
    else:
        values={row['code']:row['value_usd'] for row in state['render_rows']}
        metric='超越日本 · 位居第二' if shot['phase']=='overtake' else '中国 · 快速追赶'
        detail=f'中日GDP比值  {values["CHN"]/values["JPN"]:.2f}'
    draw.text((110,1640),metric,font=font(55),fill=shot['color'],stroke_width=1)
    draw.text((110,1733),detail,font=font(32),fill='#BBCBE0')
    hero=Image.new('RGBA',(150,105))
    asset=flag_asset(design['acts'][shot['index']]['code'],state['year']).resize((140,92),Image.Resampling.LANCZOS)
    hero.alpha_composite(asset,(5,5))
    if shot['index']==2 and shot['dissolve']>0:
        particles=fracture_particles(shot['dissolve'])
        shatter=Image.new('RGBA',image.size)
        for index in range(20):
            horizontal,vertical=index%5,index//5
            tile=hero.crop((horizontal*30,vertical*26,(horizontal+1)*30,(vertical+1)*26))
            particle=particles[index]
            tile.putalpha(tile.getchannel('A').point(lambda amount:round(amount*particle['opacity'])))
            tile=tile.rotate(particle['rotation'],resample=Image.Resampling.BICUBIC,expand=True)
            composite_subpixel(shatter,tile,(825+horizontal*30+particle['dx']*0.45,1655+vertical*26+particle['dy']*0.3))
        image=Image.alpha_composite(image,shatter)
    else:
        image.alpha_composite(hero,(825,1655))
    accent=Image.new('RGBA',image.size)
    accent_draw=ImageDraw.Draw(accent)
    sweep=85+((shot['elapsed']*0.35)%1)*910
    accent_draw.line((max(85,sweep-120),1607,min(1005,sweep+120),1607),fill=color,width=6)
    accent_draw.line((80,1625,80,1780),fill=color,width=5)
    accent_draw.arc((782,1621,1004,1843),20+shot['elapsed']*35,170+shot['elapsed']*35,fill=color,width=4)
    image=Image.alpha_composite(image,accent)
    if shot['index']==1 and shot['phase']=='cooldown':
        tint=Image.new('RGBA',image.size,(30,60,110,18))
        image=Image.alpha_composite(image,tint)
    if power_aura:
        from power_aura import apply_power_aura
        image=apply_power_aura(image,state,shot)
    image=image.convert('RGB')
    return Image.blend(Image.new('RGB',image.size),image,shot['opacity'])
