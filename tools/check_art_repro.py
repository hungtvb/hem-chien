"""Semantic reproducibility gate for cross-runner rendered PNG sprite assets.

OpenCV/Pillow builds can encode slightly different PNG bytes across runners.
Require identical manifest and perceptually equivalent pixels instead.
"""
import io
import json
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SCOPES = ['art-source', 'assets/sprites/artist']


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, check=True, capture_output=True).stdout


def validate():
    tracked = [p for p in git('ls-files', '--', *SCOPES).decode().splitlines()
               if p.endswith('.png') or p.endswith('manifest.json')]
    extras = [p for p in git('ls-files', '--others', '--exclude-standard', '--', *SCOPES).decode().splitlines()
              if p.endswith('.png') or p.endswith('manifest.json')]
    if extras:
        raise AssertionError(f'Uncommitted generated assets: {extras[:8]}')
    verified=0
    for name in tracked:
        path=ROOT/name
        before=git('show', f'HEAD:{name}')
        after=path.read_bytes()
        if before == after:
            continue
        if name.endswith('.json'):
            assert json.loads(before) == json.loads(after), f'Manifest changed: {name}'
            continue
        with Image.open(io.BytesIO(before)) as a, Image.open(io.BytesIO(after)) as b:
            assert a.size == b.size and a.mode == b.mode == 'RGBA', (name,a.size,b.size)
            arr_a=np.asarray(a,dtype=np.int16)
            arr_b=np.asarray(b,dtype=np.int16)
            diff=arr_a-arr_b
            mae=float(np.abs(diff).mean())
            mse=float(np.square(diff.astype(np.float32)).mean())
            mask_a=arr_a[:,:,3]>127
            mask_b=arr_b[:,:,3]>127
            inter=np.logical_and(mask_a,mask_b).sum()
            union=np.logical_or(mask_a,mask_b).sum()
            iou=inter/max(union,1)
            print(f'Pixel drift {name}: MAE={mae:.4f}, MSE={mse:.4f}, alphaIoU={iou:.6f}')
            assert mae < 1.0 and mse < 6.0 and iou > .99, f'Artwork reproducibility failure: {name}'
            verified+=1
    print(f'Alpha09 reproducibility: PASS ({len(tracked)} tracked assets, {verified} pixel-variant PNG files)')


if __name__ == '__main__':
    validate()
