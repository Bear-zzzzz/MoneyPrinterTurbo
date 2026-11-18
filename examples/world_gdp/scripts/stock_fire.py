import math
import subprocess

import numpy as np
from PIL import Image, ImageChops, ImageDraw

from motion import composite_subpixel
from render_full import WIDTH,HEIGHT,TOP,ROW_GAP,BAR_LEFT,bar_geometry


def black_to_alpha(source):
    pixels=np.asarray(source.convert('RGB')).astype(np.float32)
    maximum=pixels.max(axis=2)
    alpha=np.where(maximum>6,maximum,0)
    rgb=np.divide(pixels*255,np.maximum(maximum[...,None],1))
    rgba=np.concatenate((rgb,alpha[...,None]),axis=2)
    return Image.fromarray(np.clip(rgba,0,255).astype(np.uint8))


def load_stock_frames(path):
    command=['ffmpeg','-v','error','-ss','2','-i',str(path),'-t','7',
             '-vf','crop=580:480:350:240,scale=53:44:flags=lanczos,fps=30',
             '-f','rawvideo','-pix_fmt','rgb24','pipe:1']
    result=subprocess.run(command,check=True,capture_output=True,timeout=120)
    pixels=np.frombuffer(result.stdout,dtype=np.uint8).reshape((-1,44,53,3))
    if len(pixels)<150:
        raise ValueError('At least five seconds of stock footage are required')
    return [black_to_alpha(Image.fromarray(frame)) for frame in pixels]


def tile_strip(frames,length,seconds):
    length=max(1,round(length))
    width,height=frames[0].size
    output=Image.new('RGBA',(length,height))
    overlap=max(2,width//8)
    step=max(1,width-overlap)
    for index,left in enumerate(range(0,length,step)):
        frame_index=min(len(frames)-1,max(0,round(seconds*30+index*4)))
        tile=frames[frame_index].copy()
        alpha=np.asarray(tile.getchannel('A')).astype(np.float32)
        weights=np.ones(width,dtype=np.float32)
        if index>0:
            weights[:overlap]=np.linspace(0,1,overlap)
        weights[-overlap:]=np.linspace(1,0,overlap)
        tile.putalpha(Image.fromarray((alpha*weights[None,:]).astype(np.uint8)))
        output.alpha_composite(tile,(left,0))
    return output


def attach_strip(strip,row,state):
    output=Image.new('RGBA',(WIDTH,HEIGHT))
    top=TOP+row['position']*ROW_GAP+86-strip.height
    composite_subpixel(output,strip,(BAR_LEFT,top))
    return output


def compose_stock_fire(image,state,frames,seconds,code):
    row=next(row for row in state['render_rows'] if row['code']==code)
    if row['position']>=10 or row['value_usd']<=0:
        return image.convert('RGBA')
    length=bar_geometry(row,state)['bar_end']-BAR_LEFT
    strip=tile_strip(frames,length,seconds)
    layer=attach_strip(strip,row,state)
    mask=Image.new('L',image.size,255)
    draw=ImageDraw.Draw(mask)
    for country in state['render_rows']:
        if country['position']>=10 or country['value_usd']<=0:
            continue
        top=TOP+int(country['position']*ROW_GAP)
        geometry=bar_geometry(country,state)
        draw.rectangle((75,top-3,460,top+43),fill=0)
        draw.rectangle((math.floor(geometry['number_x'])-3,top+48,math.floor(geometry['number_x'])+220,top+104),fill=0)
    layer.putalpha(ImageChops.multiply(layer.getchannel('A'),mask))
    return Image.alpha_composite(image.convert('RGBA'),layer)
