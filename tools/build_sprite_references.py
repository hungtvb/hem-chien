"""Produce consistent idle reference PNGs and a machine-readable frame atlas manifest."""
import json
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/sprites/reference';OUT.mkdir(parents=True,exist_ok=True)
POSES=['idle','walk','jump','crouch','block','lp','hp','lk','hk','special','super','hit']
manifest={'revision':'alpha-0.5-ink-cel','art_status':'vector-ink-placeholder','tile_size':[448,360],'columns':4,'rows':len(POSES),'anchor_px':[224,326], 'poses':{p:i for i,p in enumerate(POSES)},'characters':{}}
for name in ('minh','linh'):
    path=ROOT/'assets/sprites'/f'{name}-atlas.png'
    im=Image.open(path).convert('RGBA')
    idle=im.crop((0,0,448,360))
    idle.save(OUT/f'{name}-idle.png',optimize=True)
    manifest['characters'][name]={'atlas':f'assets/sprites/{name}-atlas.png','reference':f'assets/sprites/reference/{name}-idle.png'}
(ROOT/'assets/sprites/atlas-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print('Generated sprite references and atlas manifest')
