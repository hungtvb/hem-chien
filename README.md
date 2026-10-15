# HẺM CHIẾN — Web PC Fighting Prototype Alpha 0.9

Prototype có thể chơi trên trình duyệt desktop, dùng **HTML5 Canvas + JavaScript thuần** để chạy offline, không phụ thuộc CDN. Đây là phiên bản kiểm chứng combat; hệ thống được thiết kế để có thể chuyển sang Phaser/TypeScript khi chốt vertical slice.

## Chạy

Mở trực tiếp `index.html` trên Chromium, Chrome, Firefox, Edge, hoặc chạy local web server:

```bash
python -m http.server 8000
# Truy cập http://localhost:8000
```

## Điều khiển

- **P1 (Minh)**: A/D di chuyển, W nhảy, S ngồi; J/K đấm nhẹ/nặng; U/I đá nhẹ/nặng; Q special; E super (300 Momentum).
- **Đỡ đòn**: giữ nút lùi; giữ lùi + S để chặn đòn thấp.
- **P2 (Linh)** trong chế độ 2 người: các phím mũi tên di chuyển; 1/2/4/5 tấn công; 0 special; 9 super.
- **P** tạm dừng, **R** làm lại trận.
- Chọn AI dễ/vừa/khó; chọn chế độ Training để HP được hồi khi hạ gục.

## Đã làm

- Sân đấu Phố Đêm Sài Gòn dạng PNG 1600×900 được sinh từ script Pillow trong `tools/generate_stage.py`.
- Hai nhân vật Minh/Linh với **12 pose vector sprite placeholder** cùng màu trang phục và silhouette thống nhất; animation theo pose.
- Combat update fixed-step 60Hz, movement/jump, attack state startup/active/recovery, hit checks, block + low guard, hit/block stun, knockback, hitstop, particle sparks, screen shake, HP/meter, 99s timer, KO, thắng 2 hiệp, đấu AI hoặc local 2P.
- HUD và điều khiển dành cho Web PC; hạn chế hiện tượng auto-repeat input.

## Giới hạn đã biết

- **Không phải sprite HD vẽ tay final**. Nhân vật hiện là vector illustration tạm, chưa phải bộ frame production-ready. Atlas xuất từ prototype là tài liệu mẫu để định nghĩa quy trình sprite.
- Các chiêu Q/E là shortcut phục vụ gameplay test, **chưa cài input 236/623 và cancel chain** theo GDD v0.2.
- AI dạng rule-based, chưa hoàn thiện footsies; chưa có throws, air normals, hitbox theo animation frame chính xác, replay, online, đào tạo combo, âm thanh và gamepad chuyên dụng.
- Hình học gameplay hiện dạng tầm đánh x-axis + độ cao; cần thay bằng hitbox/hurtbox dữ liệu riêng khi production.
- Frame data một số đòn khác với bản GDD thử nghiệm nếu cần tối ưu playfeel; mọi số liệu cần playtest cân bằng.

## Sprite Atlas

Các atlas `assets/minh-sprite-atlas.png` và `assets/linh-sprite-atlas.png` nằm trong gói demo phát hành riêng, không bắt buộc để chạy game từ source. Có thể tạo lại bằng hàm `window.makeSpriteAtlas(kind)` trong DevTools sau khi mở game. Thứ tự: idle, walk, jump, crouch, block, lp, hp, lk, hk, special, super, hit (4 cột × 3 hàng; cell 448×360).

## Cấu trúc

- `index.html`, `styles.css`, `game.js`: prototype chơi được.
- `assets/saigon-night.png`: background minh họa, được build bằng `python tools/generate_stage.py`.
- Sprite được vẽ bằng Canvas trực tiếp trong `game.js` (pose-atlas và concept PNG là asset tham khảo riêng; không bắt buộc để chạy).
- `tools/generate_stage.py`: sinh lại stage bằng Pillow.

## Milestone tiếp theo

1. Chốt 2 character turnaround master chính thức, tạo sprite master PSD/Krita có layer rõ.
2. Thay 12 pose vector bằng sprite hand-drawn HD, trước tiên idle/walk/light/heavy.
3. Định nghĩa box frame-by-frame qua JSON, motion input, combo cancel, throw và các special riêng của từng nhân vật.
4. Chạy benchmark atlas VRAM và fix bug gameplay qua playtest.

## Alpha 0.3 (visual polish pass) — Sprite animation pipeline (interim)

- 12 states × 4 keyed frames, sprite atlas pre-baked 1792×4320 RGBA PNG for Minh and Linh.
- Baked with `python tools/export_sprites.py`; runtime loads `assets/sprites/{minh,linh}-atlas.png`.
- Hitboxes and hurtboxes are independent world-space rectangles; press **H** to inspect collision; press **V** to compare vector renderer vs sprite atlas.
- Fallback vector animation remains active if the PNG atlas is missing.
- Sprite atlas currently originates from the **vector placeholder**, not final hand-drawn HD art. Artists can replace atlases without changing the combat system.

### Regenerate art assets
```bash
python3 -m pip install playwright
python3 -m playwright install chromium
python3 tools/export_sprites.py
```

## Alpha 0.3 — visual polish (WIP)

- Added illustrated character portraits used by HUD and Super cut-in; derived from the project's internal concept board.
- Added action-specific afterimage trails, idle breath, walk leaning, contact-frame squash/stretch; visuals do not affect hitboxes or frame data.
- `M`: toggle reduced-motion presentation; `H` hitbox debug; `V` atlas/vector switch.
- Both character atlases remain 48 pose-frames of the Alpha 0.2 **vector placeholder**. This milestone does **not** claim production-ready hand-drawn HD animation.
- No changes to simulation tick, hit/stun balance, collision, or AI.

## Alpha 0.4 — Animation timelines / hit-confirm cancel / Training telemetry

- Timeline durations for idle, walk, jump, crouch, block and hit are defined as **simulation-tick counts**, independent from the sprite atlas. A 4-frame illustration can now hold frames for different durations.
- Hit/block-confirmed cancel routing: `LP→LP/LK/Special`, `LK→HP/Special`, `HP/HK→Special/Super` during a limited cancel window. Whiffed attacks cannot cancel. Super still costs 300 Momentum.
- Training Mode now displays last damage/combo, frame counter, current action, hitstun and whether a cancel is available. Toggle the panel with **T**.
- KO visually selects the knockdown/hit pose rather than the default idle.
- **Important**: Current atlases remain vector-derived placeholders. Newly generated concept boards are not sprite-ready (not isolated, high-resolution transparent character frames), so they were not substituted into gameplay.

### Regression checks

`node --check game.js` and `python tools/test_alpha04.py` (requires Playwright + Chromium). Tests cover hit-confirm cancel, whiff cancel denial, atlas readiness and training telemetry.

## Alpha 0.5 — Ink-cel Sprite Pass

- Bộ sprite nhân vật được vẽ thêm chi tiết khuôn mặt, mắt, lông mày, tóc, cổ áo, nếp vải, dây giày, bo cổ tay và giáp bảo hộ.
- Bảo toàn 12 pose × 4 animation tiles (448×360 px/tile), hitbox và logic combat của Alpha 0.4.
- CI dùng `tools/export_sprites.py` để bake lại atlas từ cùng renderer, và dùng `tools/check_sprite_quality.py` để kiểm tra alpha channel, bounding boxes và chống clipping.
- **Chưa phải frame-by-frame hand-drawn HD hoàn chỉnh**: đây là ink/cel-shaded procedural art pass nhằm nâng chất lượng sprite placeholder trước khi được thay bằng art do họa sĩ dựng.

## Alpha 0.6 — Import artwork từng pose (đang chờ hình nhân vật được duyệt)

- Thêm pipeline `tools/build_artist_atlas.py` cho PNG RGBA 448×360, 4 frame/pose, 12 pose/nhân vật.
- Runtime hỗ trợ overlay artist theo **từng pose**, tự fallback về atlas Alpha 0.5 cho tất cả pose chưa có art. Không thay đổi hitboxes, combo hay camera.
- Importer không ghi đè hai atlas vector-placeholder đang chạy. Workflow riêng `artist-sprites.yml` kiểm tra định dạng và khả năng tái tạo artifact.
- **Hiện không có sprite hand-drawn mới được duyệt trong production** (0/24 pose). Chi tiết đầu vào và nghiệm thu tại `docs/alpha06-artist-import.md`.

## Alpha 0.8 — Combat sprites

Bổ sung 32 frame LP/HP/LK/HK bằng biến dạng cutout từ master Alpha 0.7; mỗi nhân vật có 6/12 pose overlay (idle, walk, lp, hp, lk, hk). Build lại với `python tools/build_attack_frames.py` và `python tools/build_artist_atlas.py`. Chi tiết và giới hạn artwork: [docs/alpha08-combat-sprites.md](docs/alpha08-combat-sprites.md). Đây chưa phải frame hand-drawn riêng lẻ.

## Alpha 0.9 — Defense, Mobility & Hit Reaction Sprites

- 32 concept-derived cutout keyframes: `jump`, `crouch`, `block`, `hit` for Minh and Linh, 4 PNG RGBA frames per state.
- Combined concept sprite coverage: **20/24** poses. `special` and `super` deliberately retain the procedural fallback.
- Rebuild via `python tools/build_defense_frames.py && python tools/build_artist_atlas.py`.
- Test via `python tools/test_alpha09.py`; the existing attack E2E remains in regression CI.
- Human art review is still required: these are **cutout/warped sprite prototypes**, NOT fully hand-drawn frame-by-frame animation.
- See `docs/alpha09-defense-sprites.md` for limitations and pipeline.

Production: https://hem-chien.vercel.app/
