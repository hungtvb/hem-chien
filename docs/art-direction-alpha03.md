# Hẻm Chiến — Alpha 0.3 Art Direction (WIP)

## Character identity

- **Minh / Thiết Quyền**: red cropped jacket, light inner shirt, dark pants, taped fists, strong grounded stance; orange-red kinetic highlights.
- **Linh / Phong Ảnh**: white-and-blue Vovinam/taekwondo-inspired costume, high black ponytail, cloth sashes, agile fighting stance; cyan-blue wind trails.
- Portraits are crops from project-generated **concept artwork**. They serve HUD and Super panels only, and are not a replacement for animation master art.

## Production acceptance criteria

1. Independent full-body turnaround masters for both characters, front/side/back; preserve faces and costume across key poses.
2. One ground-contact anchor per animation. No foot sliding or head/torso proportion drift.
3. Master drawings in RGBA with consistent outlines, shading, and transparent alpha.
4. Sprite atlas specification: 4 columns × 12 pose rows; cell 448×360; match collision data in `game.js`.
5. Normal attack poses read clearly at 1280×720; keep hitbox/hurtbox separate from raster content.
6. Art must be checked at **actual gameplay scale**, not just on a presentation board.
7. Animation needs true in-between drawings and cleanup passes; procedural afterimage/transforms are not substitutes.

## Alpha 0.3 scope

Implemented: cropped 320px illustrated portraits, Super cut-in, action afterimages, idle breathing, walk lean, reduced-motion key (`M`), automated browser check. Unchanged: Alpha 0.2 sprite vector atlas and 60Hz fixed simulation.

**Status: VISUAL WIP / HAND-DRAWN FRAMES NOT ACCEPTED.**
