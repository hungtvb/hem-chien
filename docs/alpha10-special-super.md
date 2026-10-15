# Hẻm Chiến Alpha 1.0 — Special & Super sprite pass

## Scope

Add four illustrated keyframes per pose for `special` and `super`, for Minh and Linh: 16 new RGBA 448×360 images. Master sources are `art-masters/{minh,linh}-concept.webp`; renderer is `tools/build_special_frames.py`. The technical sprites combine a concept-derived cutout with rigged limb motion and procedural energy arcs.

- **Minh:** red/orange heated uppercut and short-range energy punch.
- **Linh:** blue/cyan wind kicks with sweeping crescent arcs.
- Four animation phases: anticipation, contact, follow-through, recovery.
- Gameplay hitboxes, damage, input, combo cancel, simulation FPS and movement unchanged.
- Keep existing fallback atlases, retaining resilience when an artist atlas is missing.

### Quality gate

`python tools/build_special_frames.py && python tools/build_artist_atlas.py && python tools/test_alpha10.py`

Checks unique keyframes, transparency, 3px clipping margins, 24/24 artist pose coverage, Chromium asset loads, Special activation, 85 HP heavy punch and JavaScript errors. CI must reproduce binary assets unchanged after re-generating.

### Art review

**Not hand-drawn frame-by-frame production art.** This pass completes the coverage of all 12 states per character with coherent concept-derived animation. The anatomy/warping artifacts remain and need an artist's independent frame drawings for a final HD release. Passing CI does not constitute aesthetic approval.
