"""Alpha 0.7 concept-derived cutout animation prototype (NOT frame-by-frame hand drawn).

Renders a limited idle/walk pass from two manually isolated, transparent masters.
Source masters are concept-art cutouts, with a consistent (224,326) foot anchor.
This tool intentionally never edits the existing vector fallback atlases.
Requires Pillow, numpy, opencv-python-headless.
"""
from __future__ import annotations
from pathlib import Path
import math
import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MASTER_DIR=ROOT/'art-masters'
TARGET=ROOT/'art-source'
WIDTH,HEIGHT=448,360
ANCHOR=(224,326)


def generate(master: Image.Image, pose: str, index: int, character: str) -> Image.Image:
    # Warp a *single* art master; this produces prototype keyframes, not hand-drawn poses.
    src=master.convert('RGBA')
    # Preserve realistic proportions from the concept source; upscale only slightly.
    width=round(src.width*0.98);height=round(src.height*0.98)
    src=src.resize((width,height),Image.Resampling.LANCZOS)
    rgba=np.asarray(src).copy()
    hh,ww=rgba.shape[:2]
    yy,xx=np.indices((hh,ww),dtype=np.float32)
    phase=2*math.pi*index/4
    center=ww*.50
    hip=hh*.46
    # Smooth deformation; feet move more than the head during walking.
    side=np.tanh((xx-center)/15)
    lower=np.maximum(yy-hip,0)/max(hh-hip,1)
    if pose=='idle':
        dx=1.5*math.sin(phase)*(1-yy/hh)+.55*math.cos(phase)*(yy/hh)
        dy=1.2*math.cos(phase)*(1-yy/hh)
        bob=round(1.1*math.cos(phase))
    elif pose=='walk':
        # Counterphase forward/back steps with a small bounce and torso lean.
        stride=14.0*math.sin(phase)
        dx=(-3.0*math.sin(phase)*(1-lower) - stride*side*(lower**1.1))
        knee=np.exp(-((yy-hh*.69)/(hh*.19))**2)
        dy=-(3.0*math.sin(phase)*side*knee + 3.5*abs(math.sin(phase))) * lower
        bob=-round(3.0*abs(math.sin(phase)))
    else:
        raise ValueError(pose)
    newx=xx-dx.astype(np.float32)
    newy=yy-dy.astype(np.float32)
    warped=cv2.remap(rgba,newx.astype(np.float32),newy.astype(np.float32),interpolation=cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT,borderValue=(0,0,0,0))
    alpha=warped[:,:,3]
    # Preserve clean transparent edges, do not matte against white.
    warped[alpha==0,:3]=0
    sprite=Image.fromarray(warped,'RGBA')
    result=Image.new('RGBA',(WIDTH,HEIGHT),(0,0,0,0))
    # Anchor center is stable for all frames, and feet stay on the gameplay floor.
    x=ANCHOR[0]-ww//2
    y=ANCHOR[1]-hh+bob
    result.alpha_composite(sprite,(x,y))
    return result


def build():
    total=0
    for fighter in ('minh','linh'):
        path=MASTER_DIR/f'{fighter}-concept.webp'
        with Image.open(path) as source:
            assert source.mode=='RGBA',f'{fighter}: source must be RGBA'
            for pose in ('idle','walk'):
                directory=TARGET/fighter/pose
                directory.mkdir(parents=True,exist_ok=True)
                for frame in range(4):
                    img=generate(source,pose,frame,fighter)
                    assert img.getchannel('A').getbbox(),(fighter,pose,frame)
                    img.save(directory/f'{frame:02d}.png',optimize=True)
                    total+=1
    print(f'ALPHA 0.7: generated {total} concept-derived animation frames (not hand-drawn frames)')

if __name__=='__main__':
    build()
