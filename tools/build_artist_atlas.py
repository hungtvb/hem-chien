"""Build optional 2D artist overlays without touching procedural fallback atlases.

Input: art-source/{minh,linh}/{pose}/{00,01,02,03}.png (RGBA 448x360).
Output: assets/sprites/artist/manifest.json and nonempty *-overlay.png atlases.

Art review is a separate human sign-off: these are technical and animation gates.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageStat

ROOT = Path(__file__).resolve().parents[1]
FIGHTERS = ('minh', 'linh')
POSES = ('idle', 'walk', 'jump', 'crouch', 'block', 'lp', 'hp', 'lk', 'hk', 'special', 'super', 'hit')
FRAME_COUNT = 4
WIDTH, HEIGHT = 448, 360
ANCHOR = (224, 326)
MOVING = {'idle', 'walk', 'jump', 'lp', 'hp', 'lk', 'hk', 'special', 'super'}


class SpriteValidationError(ValueError):
    """A sprite was incomplete, incorrectly aligned, or improperly exported."""


def inspect_frame(path: Path, pose: str):
    try:
        with Image.open(path) as opened:
            if opened.mode != 'RGBA' or opened.size != (WIDTH, HEIGHT):
                raise SpriteValidationError(f'{path}: require RGBA {WIDTH}x{HEIGHT}, got {opened.mode} {opened.size}')
            img = opened.copy()
    except (OSError, SyntaxError) as exc:
        raise SpriteValidationError(f'{path}: unreadable image: {exc}') from exc
    alpha = img.getchannel('A')
    bounds = alpha.getbbox()
    if bounds is None:
        raise SpriteValidationError(f'{path}: transparent/empty frame')
    left, top, right, bottom = bounds
    if left < 3 or top < 3 or right > WIDTH - 3 or bottom > HEIGHT - 3:
        raise SpriteValidationError(f'{path}: artwork clipped against tile edges: {bounds}')
    if ImageStat.Stat(alpha).sum[0] < 20000:
        raise SpriteValidationError(f'{path}: artwork has too little visible content')
    if pose in ('idle', 'walk', 'block', 'crouch') and bottom < 245:
        raise SpriteValidationError(f'{path}: standing/crouch pose appears misaligned: bounds {bounds}')
    return img


def build(source: Path, output: Path):
    """Validate all supplied frames first, then publish overlays and manifest."""
    overlays = {}
    manifest = {
        'schemaVersion': 1,
        'artStatus': 'technical-only-human-art-approval-required',
        'tileSize': [WIDTH, HEIGHT],
        'grid': [FRAME_COUNT, len(POSES)],
        'anchorPx': list(ANCHOR),
        'characters': {},
    }
    for fighter in FIGHTERS:
        painted = []
        atlas = Image.new('RGBA', (WIDTH * FRAME_COUNT, HEIGHT * len(POSES)), (0, 0, 0, 0))
        for row, pose in enumerate(POSES):
            folder = source / fighter / pose
            if not folder.exists():
                continue
            expected = [folder / f'{i:02d}.png' for i in range(FRAME_COUNT)]
            existing = sorted(p.name for p in folder.iterdir() if p.is_file())
            if existing != [p.name for p in expected]:
                raise SpriteValidationError(f'{folder}: expected exactly {[p.name for p in expected]}, got {existing}')
            frames = [inspect_frame(path, pose) for path in expected]
            if pose in MOVING and len({hashlib.sha256(img.tobytes()).digest() for img in frames}) < 2:
                raise SpriteValidationError(f'{folder}: moving animation has four identical frames')
            for column, img in enumerate(frames):
                atlas.paste(img, (column * WIDTH, row * HEIGHT))
            painted.append(pose)
        if painted:
            overlays[fighter] = atlas
        manifest['characters'][fighter] = {
            'poses': painted,
            'atlas': f'assets/sprites/artist/{fighter}-overlay.png' if painted else None,
        }
    output.mkdir(parents=True, exist_ok=True)
    for fighter in FIGHTERS:
        path = output / f'{fighter}-overlay.png'
        if fighter in overlays:
            overlays[fighter].save(path, optimize=True)
        elif path.exists():
            path.unlink()  # stale artwork must not leak into the release
    (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'art-source')
    parser.add_argument('--output', type=Path, default=ROOT / 'assets/sprites/artist')
    args = parser.parse_args()
    manifest = build(args.source, args.output)
    print('Artist atlas import:', ', '.join(f'{k}: {len(v["poses"])} poses' for k, v in manifest['characters'].items()))
    print('PRODUCTION ART STATUS: not approved by automated tests')


if __name__ == '__main__':
    main()
