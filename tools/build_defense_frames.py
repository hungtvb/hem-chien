"""Alpha 0.9 concept-cutout animation (NOT frame-by-frame hand-drawn art)."""
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
from build_artist_atlas import ANCHOR, HEIGHT, WIDTH, inspect_frame
from build_attack_frames import GEOMETRY, move_piece, part_mask

ROOT = Path(__file__).resolve().parents[1]
POSES = ('crouch', 'jump', 'block', 'hit')


def keyframe(master, who, pose, i):
    src = np.array(master.convert('RGBA'))
    h, w = src.shape[:2]
    x0, y0 = ANCHOR[0] - w//2, ANCHOR[1] - h
    progress = (0, .45, 1, .38)[i]
    if pose == 'block':
        geom = GEOMETRY[who]['arm']
        mask = part_mask(master.size, geom['poly'], blur=.8)
        body = src.copy()
        body[:,:,3] = (src[:,:,3].astype('uint16') * (255-mask.astype('uint16'))//255).astype('uint8')
        out = Image.new('RGBA', (WIDTH,HEIGHT))
        out.alpha_composite(Image.fromarray(body), (x0,y0))
        px,py = x0+geom['pivot'][0],y0+geom['pivot'][1]
        ImageDraw.Draw(out).ellipse((px-12,py-10,px+13,py+14), fill=GEOMETRY[who]['sleeve'])
        ang=(-55,-91,-118,-88)[i]
        shift=((0,0),(-2,-2),(-3,-5),(-2,-2))[i]
        out.alpha_composite(Image.fromarray(move_piece(src,mask,geom['pivot'],ang,*shift),'RGBA'))
        return out
    yy,xx = np.indices((h,w), dtype=np.float32)
    if pose == 'crouch':
        sy=.70-.15*progress; sx=1.07+.08*progress
        offset=(13+11*progress)*(1-yy/h)**1.4; bob=0
    elif pose == 'jump':
        # Engine applies jump height; keep image anchored instead of doubling the lift.
        sy=.86-.08*progress; sx=1+.035*progress
        offset=(10+13*progress)*(yy/h-.4); bob=-round(3+5*progress)
    elif pose == 'hit':
        sy=1-.035*progress; sx=1
        offset=-(7+34*progress)*(1-yy/h)**1.6; bob=0
    else:
        raise ValueError(pose)
    sample_y = h+(yy-h)/sy
    sample_x = w/2+(xx-w/2-offset)/sx
    rgba = cv2.remap(src,sample_x.astype('float32'),sample_y.astype('float32'),
                     interpolation=cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT,
                     borderValue=(0,0,0,0))
    rgba[rgba[:,:,3]==0,:3]=0
    out = Image.new('RGBA',(WIDTH,HEIGHT))
    out.alpha_composite(Image.fromarray(rgba,'RGBA'),(x0,y0+bob))
    if pose=='hit' and i in (1,2):
        d=ImageDraw.Draw(out,'RGBA');cx,cy=x0+int(w*.54),y0+int(h*.33)
        d.line(((cx-13,cy-18),(cx-4,cy-6)),fill=(255,213,177,160),width=3)
        d.line(((cx+14,cy-13),(cx+2,cy+3)),fill=(242,77,70,150),width=3)
    return out


def build():
    count=0
    for who in ('minh','linh'):
        with Image.open(ROOT/'art-masters'/f'{who}-concept.webp') as master:
            assert master.mode=='RGBA'
            for pose in POSES:
                folder=ROOT/'art-source'/who/pose
                folder.mkdir(parents=True,exist_ok=True)
                for i in range(4):
                    dest=folder/f'{i:02d}.png'
                    keyframe(master,who,pose,i).save(dest,optimize=True)
                    inspect_frame(dest,pose)
                    count+=1
    print(f'Alpha 0.9: {count} cutout frames, NOT independent hand-drawn art')


if __name__=='__main__':
    build()
