# HẺM CHIẾN — Web PC Fighting Prototype Alpha 0.1

Prototype có thể chơi trên trình duyệt desktop, dùng **HTML5 Canvas + JavaScript thuần** để chạy offline, không phụ thuộc CDN. Đây là phiên bản kiểm chứng combat; hệ thống được thiết kế để có thể chuyển sang Phaser/TypeScript khi chốt vertical slice.

## Chơi trực tuyến

Bản production: https://hem-chien.vercel.app/

Tự động kiểm thử trong GitHub Actions: JavaScript/Python syntax, Playwright combat smoke test và HTTP smoke test trang production.

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
