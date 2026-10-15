# Hẻm Chiến — Alpha 0.9 Defense & Mobility

Four-frame prototype animations for crouch, jump, block and hit for both Minh and Linh (32 PNG RGBA 448×360). This increases artist overlay coverage from 12/24 to **20/24** states; special and super retain procedural fallback.

## Status

The source is a pair of existing concept cutouts, transformed using nonlinear deformation, arm rotation and mild hit-glints. **This is NOT independent frame-by-frame hand-drawn art.** Guard and crouch postures remain subject to human art-direction review.

## Reproduce

```sh
pip install Pillow numpy opencv-python-headless playwright
python -m playwright install chromium
python tools/build_defense_frames.py
python tools/build_artist_atlas.py
python -m unittest discover -s tools -p test_artist_atlas.py -v
python tools/test_alpha08.py
python tools/test_alpha09.py
```

The two fallback atlases and combat hitboxes are untouched. The importer generates partial artist overlays from art-source, retaining foot anchor (224,326). CI verifies both visual coverage and combat HP regression; manually review sprite proportions, action readability and pose transitions before marking production artwork complete.
