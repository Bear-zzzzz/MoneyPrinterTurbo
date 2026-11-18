import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageChops

from render_full import WIDTH, HEIGHT, TOP, ROW_GAP, bar_geometry


def aura_state(shot):
    elapsed=shot['elapsed']
    release=shot['crossing_local_seconds'] if shot['index']==3 else (3.5 if shot['index']==2 else 1.0)
    delta=elapsed-release
    if delta<0:
        phase='charge'
        strength=0.22+0.4*max(0,min(1,elapsed/release))
    elif delta<0.9:
        phase='burst'
        strength=1-0.25*delta/0.9
    else:
        phase='sustain'
        strength=0.7+0.08*math.sin(elapsed*2)
    if shot['index']==1 and shot['phase']=='cooldown':
        strength*=max(0,1-(elapsed-3.8)/1.4)
        phase='extinguished'
    if shot['index']==2 and delta>0:
        strength*=max(0,1-delta/2.5)
    return {'phase':phase,'strength':strength,'release':release,'burst_age':max(0,delta),
            'burst_active':0<=delta<0.9}


def aura_particles(age,seed):
    generator=random.Random(seed+1200)
    particles=[]
    for index in range(72):
        angle=generator.uniform(0,math.tau)
        distance=(80+generator.uniform(150,650))*age
        particles.append({'angle':angle,'distance':distance,'radius':generator.uniform(2,6),'index':index})
    return particles


def power_layer(state,shot):
    effect=aura_state(shot)
    layer=Image.new('RGBA',(WIDTH,HEIGHT))
    draw=ImageDraw.Draw(layer)
    strength=effect['strength']
    color=tuple(int(shot['color'][index:index+2],16) for index in (1,3,5))
    hero=(885,1700)
    generator=random.Random(1200+shot['index'])
    for side in (-1,1):
        outer=[]
        inner=[]
        for index in range(30):
            vertical=1880-index*22
            taper=0.3+0.7*math.sin(index/29*math.pi)
            flow=math.sin(index*1.6-shot['elapsed']*5)
            distance=(50+110*taper+generator.uniform(0,32)+flow*20)*strength
            outer.append((hero[0]+side*distance,vertical))
            inner.append((hero[0]+side*(30+24*taper)*strength,vertical))
        draw.polygon(outer+inner[::-1],fill=(*color,round(130*strength)))
        draw.line(outer,fill=(*color,round(205*strength)),width=4)
        draw.line(inner,fill=(235,250,255,round(140*strength)),width=3)
    for index in range(18):
        phase=(shot['elapsed']*0.35+index/18)%1
        vertical=1890-phase*720
        horizontal=790+((index*47)%250)
        draw.line((horizontal,vertical+25,horizontal+12*math.sin(index),vertical-25),fill=(*color,round(165*strength)),width=2+(index%3))
    if effect['burst_active']:
        age=effect['burst_age']
        decay=(1-age/0.9)*strength
        for index in range(3):
            radius=35+age*390+index*27
            draw.ellipse((hero[0]-radius,hero[1]-radius,hero[0]+radius,hero[1]+radius),outline=(*color,round(200*decay)),width=8-index*2)
        for index in range(28):
            angle=index/28*math.tau
            first=90+age*110
            second=first+100+age*170
            draw.line((hero[0]+math.cos(angle)*first,hero[1]+math.sin(angle)*first,
                       hero[0]+math.cos(angle)*second,hero[1]+math.sin(angle)*second),fill=(*color,round(150*decay)),width=2+(index%3))
        for particle in aura_particles(age,shot['index']):
            horizontal=hero[0]+math.cos(particle['angle'])*particle['distance']
            vertical=hero[1]+math.sin(particle['angle'])*particle['distance']
            radius=particle['radius']
            draw.ellipse((horizontal-radius,vertical-radius,horizontal+radius,vertical+radius),fill=(255,235,190,round(200*decay)))
    focus=['USA','JPN','SUN','CHN'][shot['index']]
    row=next(row for row in state['render_rows'] if row['code']==focus)
    if row['position']<10 and row['value_usd']>0 and not(focus=='SUN' and shot['dissolve']>0):
        end=bar_geometry(row,state)['bar_end']
        vertical=TOP+row['position']*ROW_GAP+75
        for direction in (-1,1):
            points=[]
            for index in range(25):
                horizontal=85+(end-85)*index/24
                amplitude=(12+abs(math.sin(index*1.4-shot['elapsed']*7))*23)*strength
                points.append((horizontal,vertical+direction*amplitude))
            draw.line(points,fill=(*color,round(200*strength)),width=3)
        draw.line((85,vertical,end,vertical),fill=(230,250,255,round(110*strength)),width=4)
    glow=layer.filter(ImageFilter.GaussianBlur(12))
    glow.putalpha(glow.getchannel('A').point(lambda amount:round(amount*0.8)))
    layer=Image.alpha_composite(glow,layer)
    layer.putalpha(layer.getchannel('A').point(lambda amount:min(210,amount)))
    return layer


def apply_power_aura(image,state,shot):
    layer=power_layer(state,shot)
    mask=Image.new('L',image.size,255)
    draw=ImageDraw.Draw(mask)
    draw.rectangle((0,0,WIDTH,350),fill=0)
    draw.rectangle((80,1632,815,1785),fill=0)
    draw.rectangle((825,1660,970,1755),fill=0)
    for row in state['render_rows']:
        if row['position']>=10 or row['value_usd']<=0:
            continue
        top=TOP+int(row['position']*ROW_GAP)
        geometry=bar_geometry(row,state)
        draw.rectangle((75,top-3,460,top+49),fill=0)
        draw.rectangle((int(geometry['number_x'])-3,top+48,int(geometry['number_x'])+215,top+104),fill=0)
    layer.putalpha(ImageChops.multiply(layer.getchannel('A'),mask))
    return Image.alpha_composite(image.convert('RGBA'),layer)
