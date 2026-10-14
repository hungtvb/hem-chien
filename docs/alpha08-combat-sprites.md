# Hẻm Chiến Alpha 0.8 — Combat Cutout Keyframes

## Mục tiêu và nghiệm thu

- Hoàn thành bốn trạng thái chiến đấu `lp`, `hp`, `lk`, `hk` cho cả Minh và Linh, mỗi trạng thái đúng 4 keyframe PNG RGBA 448×360, anchor (224,326).
- Bảo toàn Idle, Walk từ Alpha 0.7. Độ phủ art tăng từ **4/24** lên **12/24** pose (6/12 trên mỗi nhân vật).
- Giữ engine, move data, hitbox và nguyên tắc fallback của Alpha 0.6/0.7.
- Kiểm thử importer + gameplay E2E: Heavy Punch gây 85 damage; toàn bộ overlay và fallback tải được.

## Chất lượng hình ảnh (không được nhầm lẫn)

**Các frame Alpha 0.8 là cutout keyframe làm bằng affine rotation/compositing từ cùng character master của Alpha 0.7, KHÔNG phải frame hand-drawn độc lập.** Các vùng khớp gập đôi khi có thể lộ seam và ánh sáng chưa đồng nhất. Các vệt quét tay/chân mô phỏng chuyển động, không thay đổi hitbox.

## Tái tạo asset

```sh
pip install pillow numpy opencv-python-headless
python tools/build_concept_frames.py
python tools/build_attack_frames.py
python tools/build_artist_atlas.py
python -m unittest discover -s tools -p 'test_artist_atlas.py' -v
python tools/test_alpha08.py  # requires Playwright + Chromium
```

Các script chỉ ghi `art-source/{minh,linh}/{idle,walk,lp,hp,lk,hk}` và overlay tại `assets/sprites/artist/`. Không sửa hai atlas procedural fallback của Alpha 0.5.

## Next art tasks

- Hand-drawn keyframe độc lập có pose giải phẫu rõ và silhouette đặc trưng theo style guide.
- Animations `block`, `hit`, `jump`, `crouch`, `special`, `super` chưa có artwork overlay; vẫn fallback.
- Review art thủ công tại kích thước render 1280×720 và nâng số frame nếu animation đấm/đá thiếu mượt.
