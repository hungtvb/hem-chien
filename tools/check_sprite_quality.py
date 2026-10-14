"""Alpha 0.5 ink/cel atlas quality gate (not a hand-drawn art approval)."""
from pathlib import Path
from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parents[1]
TILE_W, TILE_H = 448, 360
POSES = ('idle','walk','jump','crouch','block','lp','hp','lk','hk','special','super','hit')


def validate(kind):
    path = ROOT / 'assets' / 'sprites' / f'{kind}-atlas.png'
    with Image.open(path) as im:
        assert im.mode == 'RGBA', (kind, 'not RGBA')
        assert im.size == (4*TILE_W, len(POSES)*TILE_H), (kind, im.size)
        im.load()
        assert im.getpixel((2, 2))[3] == 0, f'{kind}: atlas corner not transparent'
        areas = []
        colors = set()
        for row, pose in enumerate(POSES):
            for col in range(4):
                cell = im.crop((col*TILE_W,row*TILE_H,(col+1)*TILE_W,(row+1)*TILE_H))
                alpha = cell.getchannel('A')
                bbox = alpha.getbbox()
                assert bbox, (kind, pose, col, 'empty tile')
                l,t,r,b = bbox
                assert l>=3 and r<=TILE_W-3 and t>=3 and b<=TILE_H-3, (kind, pose,col,bbox,'clipped')
                pixels = ImageStat.Stat(alpha).sum[0]
                assert pixels > 1_000_000, (kind,pose,col, 'too few painted pixels')
                areas.append((r-l)*(b-t))
                colors.update(cell.getpixel((x,y))[:3] for x in range(100,350,31) for y in range(40,325,29) if cell.getpixel((x,y))[3]>128)
        assert len(colors)>12, (kind, 'weak color variety',len(colors))
        print(f'{kind}: PASS {len(areas)} tiles · {len(colors)} sampled colors · alpha transparent · no tile-edge clipping')


if __name__=='__main__':
    for fighter in ('minh','linh'):
        validate(fighter)
