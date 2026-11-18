import math
from functools import lru_cache

from PIL import Image


def monotone_slopes(values):
    if len(values) == 1:
        return (0,)
    differences = [new-old for old,new in zip(values,values[1:])]
    if len(values) == 2:
        return (differences[0], differences[0])
    slopes = [0] * len(values)
    for index in range(1,len(values)-1):
        left, right = differences[index-1:index+1]
        if left * right > 0:
            slopes[index] = 2 * left * right / (left+right)
    for endpoint, first, second in ((0,differences[0],differences[1]),(-1,differences[-1],differences[-2])):
        slope = (3*first-second)/2
        if slope*first <= 0:
            slope = 0
        elif first*second <= 0 and abs(slope) > abs(3*first):
            slope = 3*first
        slopes[endpoint] = slope
    return tuple(slopes)


def sample_track(values, slopes, coordinate):
    coordinate = min(len(values)-1,max(0,coordinate))
    index = int(coordinate)
    if coordinate == index:
        return values[index]
    fraction = coordinate-index
    amount = ((2*fraction**3-3*fraction**2+1)*values[index]
              +(fraction**3-2*fraction**2+fraction)*slopes[index]
              +(-2*fraction**3+3*fraction**2)*values[index+1]
              +(fraction**3-fraction**2)*slopes[index+1])
    return min(max(values[index:index+2]),max(min(values[index:index+2]),amount))


@lru_cache(maxsize=8)
def build_tracks(signature, codes):
    years = [{code:amount for code,amount in entries} for entries in signature]
    ranks = []
    for entries in years:
        ordered = sorted(entries,key=lambda code:(-entries[code],code))
        ranks.append({code:min(index,10.5) for index,code in enumerate(ordered)})
    tracks = {}
    for code in codes:
        values = tuple(year.get(code,0) for year in years)
        positions = tuple(year.get(code,10.5) for year in ranks)
        tracks[code] = {'values':values,'value_slopes':monotone_slopes(values),
                        'positions':positions,'position_slopes':monotone_slopes(positions)}
    return tracks


def composite_subpixel(target, image, position):
    horizontal, vertical = position
    left, top = math.floor(horizontal), math.floor(vertical)
    fraction_x, fraction_y = horizontal-left, vertical-top
    if fraction_x or fraction_y:
        image = image.transform((image.width+1,image.height+1), Image.Transform.AFFINE,
                                (1,0,-fraction_x,0,1,-fraction_y),Image.Resampling.BICUBIC)
    target.alpha_composite(image,(left,top))
