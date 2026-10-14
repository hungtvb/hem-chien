# Alpha 0.5 — Sprite Production Notes

**Scope:** Vector ink/cel refinement of the current gameplay placeholders, not final artist-painted HD sprites.

## Fixed runtime contract

- 12 actions × 4 frames; row-major, PNG RGBA.
- Tile: `448 × 360` px; atlas: `1792 × 4320` px.
- World-space fighter position is the foot origin. Input, hitboxes and hurtboxes are independent of sprite pixels.
- Sprites render flipped for left-facing fighters. The source art faces right.
- `crouch` and `super` have separate tile-origin corrections to avoid clipping. Do not trim these corrections without re-running QA.
- Use `tools/export_sprites.py` to bake atlases and `tools/check_sprite_quality.py` to check cropping/transparency.
- `tools/build_sprite_references.py` extracts canonical idle reference poses and the JSON manifest.

## QA acceptance

Every atlas row must contain four non-empty images, with no occupied pixels touching any tile boundary. `tools/test_alpha04.py` remains the combat regression test, and `tools/test_visual.py` verifies the browser loads both atlases.

## Art handoff

Artists can substitute painted PNG frames for each tile while retaining the manifest, file names, row order, tile dimensions and per-frame anchor. The refined ink renderer is the provisional reference only: **frame-by-frame hand-drawn HD remains unimplemented**.
