# Hẻm Chiến Alpha 0.6 — Artist sprite pipeline

## Trạng thái thực tế

**Chưa nghiệm thu hand-drawn HD.** Alpha 0.6 chỉ cung cấp quy trình nạp asset 2D do họa sĩ/AI tạo, kiểm tra ảnh, và fallback an toàn. Atlas `assets/sprites/minh-atlas.png` và `linh-atlas.png` vẫn là hình procedurally rendered của Alpha 0.5; hai atlas này **không bị ghi đè** bởi importer.

## Cấu trúc và tiêu chuẩn đầu vào

```text
art-source/
  minh/
    idle/
      00.png
      01.png
      02.png
      03.png
    walk/
      00.png ... 03.png
  linh/
    idle/
      00.png ... 03.png
```

Các pose hợp lệ theo thứ tự: `idle`, `walk`, `jump`, `crouch`, `block`, `lp`, `hp`, `lk`, `hk`, `special`, `super`, `hit`.

- Một pose có **đúng bốn frame** PNG RGBA **448×360**; không được để một pose thiếu frame.
- Phải có nền trong suốt thực sự, không có bảng chữ, background, crop chân hoặc viền cắt vào mép.
- Tất cả frame cùng tỉ lệ nhân vật, hướng sang phải, **anchor tại (224,326)** tính từ góc trái trên canvas frame.
- Frame 00→03 phải có thay đổi hình cho idle/walk/attack; giữ nguyên khuôn mặt và thiết kế trang phục.
- Chỉ vẽ nhân vật, không bake hiệu ứng đánh/trúng đòn vào cơ thể nếu có thể tách VFX độc lập.
- Không mirror nguồn: engine flip canvas khi nhân vật quay mặt trái. Không để chữ trên quần áo có hướng phải đọc, trừ khi xử lý texture gương.

## Build

```bash
python3 -m pip install Pillow
python3 tools/build_artist_atlas.py
python3 -m unittest discover -s tools -p 'test_artist_atlas.py' -v
```

Build xuất `assets/sprites/artist/manifest.json` và, nếu có pose mới, file `assets/sprites/artist/{minh,linh}-overlay.png`. Các pose **chưa có artwork** là ô RGBA hoàn toàn trong suốt. Runtime chỉ sử dụng overlay cho pose được liệt kê trong manifest và chỉ sau khi ảnh tải xong; mọi pose khác dùng atlas Alpha 0.5, rồi fallback sang Canvas vector nếu cần.

Bản build hiện tại có **0/24 pose artwork được nhập** (12 pose × 2 nhân vật). Đây là tình trạng đúng và chủ động, tránh thay atlas bằng tranh concept poster không phù hợp.

## Nghiệm thu art riêng biệt

Các bài kiểm thử tự động chỉ xác nhận định dạng, size, nền, clipping, tính đầy đủ, sự khác biệt của các keyframe và ổn định khi render. Art lead vẫn phải duyệt: đúng concept Minh/Linh, tỷ lệ giải phẫu, biểu cảm, nét viền, tính liên tục animation và tư thế đọc rõ ở kích thước gameplay. **CI PASS không đồng nghĩa art đạt hand-drawn HD.**

## Kiểm thử runtime

Mở DevTools, thực thi `window.__combatDebug()` và kiểm tra `artistReady` và `artistPoseCoverage`. Không có artwork thì `artistPoseCoverage.minh`/`.linh` đều rỗng. Nếu thêm bốn frame `idle` cho Minh và chạy lại importer, chỉ Minh-idle được lấy từ overlay; các trạng thái còn lại không thay đổi.

## Lưu ý CI

`tools/export_sprites.py` vẫn có thể bake các placeholder cũ cho kiểm tra hồi quy. Nó không được phép ghi vào `assets/sprites/artist/`. Chỉ `tools/build_artist_atlas.py` được quyền tạo overlay và manifest, tránh việc workflow tái tạo vector đè lên tranh mới.
