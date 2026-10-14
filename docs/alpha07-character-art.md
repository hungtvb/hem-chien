# Alpha 0.7 — Minh & Linh concept-cutout animation prototype

## What actually ships

**This is not production-approved hand-drawn keyframe art.** The art masters are transparent full-body cutouts from the project's generated concept sheet. Their colors, proportions, apparel and facial features are higher quality than the original procedural ink/cel placeholders. A scripted 2D deformation creates four slightly different Idle frames and four Walk frames per character. The latter are provisional motion studies, not eight separately illustrated poses.

Master source: `art-masters/{minh,linh}-concept.webp` (RGBA transparent), extracted from a Hẻm Chiến concept board generated for this project. The source concept uses AI-assisted illustration. Do not label these assets as painted by a human artist.

## Frame specs and integration

- Characters: Minh (red jacket) and Linh (white-blue combat uniform)
- Animated pose coverage: Idle and Walk, each 4 RGBA frames at 448×360 px
- Anchor: (224, 326), gameplay facing right; engine mirrors when facing left
- Incomplete moves (`lp`, `hp`, `lk`, `hk`, `block`, `hit`, `super`, ...) use the original Alpha 0.5 ink/cel atlas via Alpha 0.6's per-pose fallback
- The main simulation stays at 60 Hz; illustration timing is controlled by combat state, not by image generation
- The `artStatus` intentionally remains `technical-only-human-art-approval-required`

## Rebuild + test

```bash
python -m pip install Pillow numpy opencv-python-headless playwright
python -m playwright install chromium
python tools/build_concept_frames.py
python tools/build_artist_atlas.py
python -m unittest discover -s tools -p 'test_artist_atlas.py' -v
python tools/test_alpha07.py
```

CI regenerates `art-source/{minh,linh}/{idle,walk}/*.png`, verifies browser loading, action state and HP. On a **main** push, it commits the atlas outputs so Vercel can serve them as static files. This generator does not write into the legacy fallback atlases.

## Art approval remaining

1. Dedicated side-facing turnaround sheets, not only front-facing concept cutouts.
2. Separate hand-drawn poses with feet planted and true alternating walk steps.
3. Independent cleanups for arms, knees, shoes and cloth overlap across all frames.
4. Frame-by-frame rig/texture consistency and anti-clipping at gameplay camera zoom.
5. Eventually replace the remaining ten states per character and get a human art review.

CI passing demonstrates compatibility, not human art sign-off.
