"""Alpha 1.0: render four concept-cutout FX keyframes for each fighter's Special/Super.

The output is technical cutout animation, not independently drawn hand-drawn HD art.
Inputs are stable master character images; output is per-pose 448x360 RGBA.
"""
from __future__ import annotations
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
from build_attack_frames import make as attack_pose
from build_artist_atlas import WIDTH, HEIGHT, inspect_frame

ROOT=Path(__file__).resolve().parents[1]
POSES=('special','super')
FIGHTERS=('minh','linh')
PALETTES={
 'minh':{'core':(255,229,163,255),'bright':(255,125,66,245),'mid':(242,57,47,180),'glow':(255,59,27,75)},
 'linh':{'core':(235,252,255,255),'bright':(94,220,255,245),'mid':(38,123,255,190),'glow':(40,91,251,80)}
}

def energy_layer(kind:str,pose:str,phase:int)->Image.Image:
    """Separate bright rim and blurred light layers with bounded alpha."""
    pal=PALETTES[kind]
    art=Image.new('RGBA',(WIDTH,HEIGHT))
    d=ImageDraw.Draw(art,'RGBA')
    strength=(.45,.9,1.,.55)[phase]
    if pose=='special':
        cx,cy=313,156 if kind=='minh' else 174
        length=(25,61,82,38)[phase]
        # Tight swirling shockwave by hands for Minh; rising curved wind kick for Linh.
        for k in range(7):
            theta=(k-3)*.18
            span=length*(1-abs(k-3)*.09)
            yy=cy+math.sin(theta)*24
            p=[(cx-17,yy+12),(cx+span*.36,yy+12+theta*24),(cx+span,yy+theta*38),(cx+span*.42,yy-9+theta*24)]
            d.polygon(p,fill=(*pal['mid'][:3],int(37*strength)))
        for j in range(6):
            spread=13+j*7
            endx=min(WIDTH-18,cx+length+(j%2)*7)
            yy=cy+(j-2.5)*11
            d.arc((cx-18,yy-spread,endx,yy+spread),194,337,fill=pal['bright'],width=2+j%2)
        d.ellipse((cx-17,cy-15,cx+16,cy+15),outline=pal['core'],width=3)
    else:
        cx,cy=267,146
        scale=(.57,.83,1.,.8)[phase]
        for k in range(4):
            r=int((58+18*k)*scale)
            rect=(cx-r-25,cy-r//2,cx+r+15,cy+r//2)
            d.arc(rect,196+k*3,341-k*2,fill=pal['bright'] if k<2 else pal['mid'],width=6 if k<2 else 3)
        for i in range(21):
            theta=math.radians(200+i*6.8+phase*9)
            radius=(45+i%5*13)*scale
            x=min(398,cx+math.cos(theta)*radius*1.30)
            y=cy+math.sin(theta)*radius*.71
            dx=9+24*scale
            dy=-5+7*math.sin(theta)
            d.line((x,y,min(423,x+dx),y+dy),fill=pal['bright'] if i%3 else pal['core'],width=2+(i%3==0))
        # Shockwave impact arc, confined to the sprite tile.
        d.arc((175,65,408,290),260,340,fill=pal['core'],width=5)
    # Soft glow behind crisp strokes; preserve detailed ink lineart.
    blur=art.filter(ImageFilter.GaussianBlur(8 if pose=='super' else 5))
    blur.putalpha(blur.getchannel('A').point(lambda v:int(v*.63)))
    result=Image.new('RGBA',(WIDTH,HEIGHT))
    result.alpha_composite(blur)
    result.alpha_composite(art)
    return result


def create(master:Image.Image,kind:str,pose:str,phase:int)->Image.Image:
    assert kind in FIGHTERS and pose in POSES and phase in range(4)
    # A readable contact pose with two distinct strike families.
    base=attack_pose(master,kind, 'hp' if kind=='minh' else 'hk',phase)
    fx=energy_layer(kind,pose,phase)
    # Trailing glow stays behind inked character; bright streaks on top.
    out=Image.new('RGBA',(WIDTH,HEIGHT))
    out.alpha_composite(fx)
    out.alpha_composite(base)
    halo=fx.copy()
    halo.putalpha(halo.getchannel('A').point(lambda a:int(a*.74)))
    out.alpha_composite(halo)
    return out


def build():
    for kind in FIGHTERS:
        with Image.open(ROOT/'art-masters'/f'{kind}-concept.webp') as master:
            master=master.convert('RGBA')
            for pose in POSES:
                folder=ROOT/'art-source'/kind/pose
                folder.mkdir(parents=True,exist_ok=True)
                for phase in range(4):
                    path=folder/f'{phase:02d}.png'
                    create(master,kind,pose,phase).save(path,optimize=True)
                    inspect_frame(path,pose)
    print('Alpha 1.0: 16 technical special/super cutout keyframes (not independently hand-drawn).')

if __name__=='__main__':build()
