import math

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from motion import composite_subpixel
from power_aura import aura_state
from render_full import WIDTH,HEIGHT,TOP,ROW_GAP,BAR_LEFT,bar_geometry


def bar_flame_layer(state,shot):
    output=Image.new('RGBA',(WIDTH,HEIGHT))
    code=['USA','JPN','SUN','CHN'][shot['index']]
    row=next(row for row in state['render_rows'] if row['code']==code)
    strength=aura_state(shot)['strength']
    if strength<=0 or row['position']>=10 or row['value_usd']<=0 or (code=='SUN' and shot['dissolve']>0):
        return output
    end=bar_geometry(row,state)['bar_end']
    length=end-BAR_LEFT
    canvas=Image.new('RGBA',(max(1,math.ceil(length)+9),52))
    color=tuple(int(shot['color'][index:index+2],16) for index in (1,3,5))
    draw=ImageDraw.Draw(canvas)
    elapsed=shot['elapsed']
    count=max(3,round(length/14))
    for index in range(count):
        phase=elapsed*5+index*1.73
        center=(index+0.5)/count*length
        width=5+3*math.sin(phase+0.8)**2
        height=(6+13*math.sin(phase)**2)*strength
        lean=math.sin(phase*0.7)*4
        upper=[(center-width,20),(center-width*0.6,20-height*0.4),
               (center+lean,20-height),(center+width*0.45,20-height*0.5),(center+width,20)]
        draw.polygon(upper,fill=(*color,round(215*strength)))
        draw.polygon([(center-width*0.4,20),(center+lean*0.6,20-height*0.65),(center+width*0.4,20)],fill=(255,240,185,round(190*strength)))
        lower=[(center-width,37),(center+lean,37+height*0.55),(center+width,37)]
        draw.polygon(lower,fill=(*color,round(170*strength)))
    for index in range(14):
        fraction=(elapsed*0.7+index/14)%1
        horizontal=fraction*length
        vertical=18-6*math.sin(index+elapsed*4)**2
        draw.line((horizontal-3,vertical+2,horizontal+2,vertical),fill=(255,240,205,round(180*strength)),width=2)
    draw.line((0,20,length,20),fill=(*color,round(190*strength)),width=3)
    draw.line((0,37,length,37),fill=(*color,round(160*strength)),width=2)
    draw.polygon([(length-5,20),(length+7,25),(length+3,32),(length-5,37)],fill=(*color,round(180*strength)))
    glow=canvas.filter(ImageFilter.GaussianBlur(2))
    glow.putalpha(glow.getchannel('A').point(lambda amount:round(amount*0.5)))
    canvas=Image.alpha_composite(glow,canvas)
    composite_subpixel(output,canvas,(BAR_LEFT,TOP+row['position']*ROW_GAP+50))
    return output


def apply_bar_flame(image,state,shot):
    layer=bar_flame_layer(state,shot)
    mask=Image.new('L',image.size,255)
    draw=ImageDraw.Draw(mask)
    for row in state['render_rows']:
        if row['position']>=10 or row['value_usd']<=0:
            continue
        top=TOP+int(row['position']*ROW_GAP)
        draw.rectangle((75,top-3,460,top+49),fill=0)
        geometry=bar_geometry(row,state)
        draw.rectangle((int(geometry['number_x'])-3,top+48,int(geometry['number_x'])+220,top+104),fill=0)
    layer.putalpha(ImageChops.multiply(layer.getchannel('A'),mask))
    return Image.alpha_composite(image.convert('RGBA'),layer)
