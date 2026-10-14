"""Alpha 0.8: cutout/rig-based attack keyframes from approved concept cutouts.

Frames are NON-hand-drawn, use a fixed 448x360 transparent canvas and stable foot anchor.
They are a temporary continuity improvement versus switching to procedural placeholders.
"""
from __future__ import annotations
import math
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from build_artist_atlas import WIDTH, HEIGHT, ANCHOR

ROOT = Path(__file__).resolve().parents[1]
GEOMETRY = {
    'minh': {
      'arm': {'poly':[(105,44),(121,48),(136,69),(146,110),(142,153),(120,164),(114,127),(111,96),(97,59)],'pivot':(107,61)},
      'leg': {'poly':[(80,118),(114,123),(132,168),(138,226),(137,285),(99,290),(93,230),(83,183),(77,145)],'pivot':(91,138)},
      'skin':'#d99474','sleeve':'#be3036','pants':'#222330'
    },
    'linh': {
      'arm': {'poly':[(85,59),(103,63),(119,85),(130,109),(141,133),(147,151),(131,160),(113,134),(97,115),(90,91),(78,76)],'pivot':(96,77)},
      'leg': {'poly':[(65,117),(98,127),(113,168),(114,229),(106,274),(84,295),(56,265),(60,212),(62,154)],'pivot':(81,145)},
      'skin':'#e4baa0','sleeve':'#2862ab','pants':'#d7dce8'
    }
}
STATES = ('lp','hp','lk','hk')

def part_mask(size, coords, blur=.7):
    mask=Image.new('L',size,0)
    ImageDraw.Draw(mask).polygon(coords,fill=255)
    if blur: mask=mask.filter(ImageFilter.GaussianBlur(blur))
    return np.array(mask,dtype=np.uint8)

def over(dst, src):
    base=Image.fromarray(dst,'RGBA');base.alpha_composite(Image.fromarray(src,'RGBA'))
    return np.asarray(base).copy()

def move_piece(arr, mask, pivot, angle, dx=0, dy=0):
    component=arr.copy(); component[:,:,3] = (component[:,:,3].astype(np.uint16)*mask.astype(np.uint16)//255).astype(np.uint8)
    piece=np.zeros((HEIGHT,WIDTH,4),dtype=np.uint8)
    # place original cutout at standard anchor before transform
    left=ANCHOR[0]-arr.shape[1]//2;top=ANCHOR[1]-arr.shape[0]
    piece[top:top+arr.shape[0],left:left+arr.shape[1]]=component
    center=(left+pivot[0],top+pivot[1])
    M=cv2.getRotationMatrix2D(center,angle,1.0)
    M[0,2]+=dx;M[1,2]+=dy
    return cv2.warpAffine(piece,M,(WIDTH,HEIGHT),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))

def make(master,who,state,i):
    src=np.asarray(master.convert('RGBA')).copy()
    conf=GEOMETRY[who]
    part='arm' if state in ('lp','hp') else 'leg'
    geom=conf[part]
    mask=part_mask(master.size,geom['poly'])
    # phases: windup, contact, follow-through, recover
    angle={ 'lp':[-12,70,52,8], 'hp':[-21,79,62,13], 'lk':[-8,46,39,9], 'hk':[-14,63,49,12] }[state][i]
    extra={ 'lp':[0,12,8,0], 'hp':[-1,22,12,2], 'lk':[0,14,11,1], 'hk':[-3,23,16,2] }[state][i]
    dx=extra
    dy={ 'lp':[0,-3,-2,0], 'hp':[2,-9,-5,0], 'lk':[1,-4,-2,0], 'hk':[4,-12,-6,0] }[state][i]
    # draw body first, keeping outlines of the body visible through the moving limb;
    # leave masked region transparent and place clean synthesized underpaint at the joint.
    underneath=src.copy()
    underneath[:,:,3]=(underneath[:,:,3].astype(np.float32)*(255-mask)/255).astype(np.uint8)
    baseline=np.zeros((HEIGHT,WIDTH,4),dtype=np.uint8)
    left=ANCHOR[0]-src.shape[1]//2;top=ANCHOR[1]-src.shape[0]
    baseline[top:top+src.shape[0],left:left+src.shape[1]] = underneath
    pic=Image.fromarray(baseline,'RGBA')
    painter=ImageDraw.Draw(pic,'RGBA')
    px=left+geom['pivot'][0];py=top+geom['pivot'][1]
    # shaded bridging fabric around the joint, narrower than the original limb.
    color=conf['sleeve'] if part=='arm' else conf['pants']
    painter.ellipse((px-11,py-8,px+12,py+13),fill=color)
    pic_arr=np.array(pic)
    moved=move_piece(src,mask,geom['pivot'],angle,dx,dy)
    combined=Image.fromarray(over(pic_arr,moved),'RGBA')
    # attack visual: small transparent swoosh as standalone gesture (not a projectile)
    if i in (1,2):
        draw=ImageDraw.Draw(combined,'RGBA')
        ext=28 if state in ('lp','lk') else 50
        if part=='arm':
            yy=py-16 if i==1 else py-8
            bounds=(px+37, yy-14,px+100+ext,yy+22)
        else:
            yy=py-46 if i==1 else py-32
            bounds=(px+54, yy-18,px+120+ext,yy+36)
        accent=(245,86,55,165) if who=='minh' else (69,190,250,175)
        draw.arc(bounds,195,330,fill=accent,width=3 if i==2 else 5)
    # Keep the key pose grounded: crop-safe master-scale placement.
    return combined

def build():
    count=0
    for who in ('minh','linh'):
        master=Image.open(ROOT/'art-masters'/f'{who}-concept.webp').convert('RGBA')
        for state in STATES:
            folder=ROOT/'art-source'/who/state
            folder.mkdir(parents=True,exist_ok=True)
            for i in range(4):
                f=make(master,who,state,i)
                f.save(folder/f'{i:02d}.png',optimize=True)
                count+=1
    print('Alpha 0.8:',count,'attack keyframes (concept-cutout deformation, NOT independent hand-drawn art)')

if __name__=='__main__':build()
