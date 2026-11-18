import math

from PIL import Image, ImageDraw, ImageFilter, ImageChops

from power_aura import aura_state
from render_full import WIDTH, HEIGHT, TOP, ROW_GAP, bar_geometry


def flame_layer(shot):
    canvas=Image.new('RGBA',(290,1040))
    strength=aura_state(shot)['strength']
    elapsed=shot['elapsed']
    palettes=[((20,55,190),(40,150,255),(165,235,255)),
              ((135,30,100),(255,115,175),(255,220,240)),
              ((130,10,20),(245,45,35),(255,180,105)),
              ((160,20,5),(255,100,15),(255,220,90))]
    palette=palettes[shot['index']]
    for index in range(14):
        phase=(elapsed*0.36+index/14)%1
        center=28+(index*53)%238
        bottom=1040-phase*820
        length=(150+90*math.sin(index*1.7+elapsed*1.2))*max(0.2,strength)
        sway=math.sin(index*2+elapsed*3)*25
        for band,(width,color) in enumerate(zip((30,18,8),palette)):
            draw=ImageDraw.Draw(canvas)
            points=[]
            for step in range(16):
                fraction=step/15
                vertical=bottom-length*fraction
                horizontal=center+sway*fraction+math.sin(fraction*8-elapsed*4+index)*9*fraction
                taper=width*(1-fraction)**0.65
                points.append((horizontal-taper,vertical))
            for step in range(15,-1,-1):
                fraction=step/15
                vertical=bottom-length*fraction
                horizontal=center+sway*fraction+math.sin(fraction*8-elapsed*4+index)*9*fraction
                points.append((horizontal+width*(1-fraction)**0.65,vertical))
            opacity=round((105+band*35)*strength*math.sin(math.pi*phase)**0.45)
            draw.polygon(points,fill=(*color,opacity))
    sparks=ImageDraw.Draw(canvas)
    for index in range(32):
        phase=(elapsed*0.3+index/32)%1
        horizontal=25+(index*71)%245+math.sin(elapsed*2+index)*9
        vertical=1030-phase*1030
        opacity=round(180*strength*(1-phase))
        sparks.line((horizontal,vertical+7,horizontal+2,vertical-3),fill=(*palette[2],opacity),width=2)
    glow=canvas.filter(ImageFilter.GaussianBlur(10))
    glow.putalpha(glow.getchannel('A').point(lambda amount:round(amount*0.65)))
    canvas=Image.alpha_composite(glow,canvas)
    output=Image.new('RGBA',(WIDTH,HEIGHT))
    output.alpha_composite(canvas,(790,430))
    return output


def apply_side_fire(image,state,shot):
    layer=flame_layer(shot)
    mask=Image.new('L',image.size,255)
    draw=ImageDraw.Draw(mask)
    for row in state['render_rows']:
        if row['position']>=10 or row['value_usd']<=0:
            continue
        top=TOP+int(row['position']*ROW_GAP)
        geometry=bar_geometry(row,state)
        draw.rectangle((int(geometry['number_x'])-3,top+48,int(geometry['number_x'])+220,top+104),fill=0)
        draw.rectangle((75,top-3,460,top+49),fill=0)
    layer.putalpha(ImageChops.multiply(layer.getchannel('A'),mask))
    return Image.alpha_composite(image.convert('RGBA'),layer)
