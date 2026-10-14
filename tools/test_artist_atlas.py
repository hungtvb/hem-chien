"""Regression tests for partial high-quality sprite import and safety fallbacks."""
import json
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageDraw
from build_artist_atlas import build, SpriteValidationError, WIDTH, HEIGHT


class ImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.src = root / 'art-source'
        self.out = root / 'out'

    def frame(self, pose='idle', index=0):
        dest = self.src / 'minh' / pose
        dest.mkdir(parents=True, exist_ok=True)
        img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
        painter = ImageDraw.Draw(img)
        painter.ellipse((160 + index, 75, 265 + index, 310), fill=(205, 48, 49, 255))
        img.save(dest / f'{index:02d}.png')

    def pose(self, pose='idle'):
        for index in range(4):
            self.frame(pose, index)

    def test_empty_project_is_valid_fallback(self):
        manifest = build(self.src, self.out)
        self.assertEqual(manifest['characters']['linh']['poses'], [])
        self.assertEqual(manifest['characters']['minh']['poses'], [])
        self.assertFalse((self.out / 'minh-overlay.png').exists())

    def test_partial_import_has_transparent_other_poses(self):
        self.pose()
        manifest = build(self.src, self.out)
        self.assertEqual(manifest['characters']['minh']['poses'], ['idle'])
        self.assertEqual(manifest['characters']['linh']['poses'], [])
        with Image.open(self.out / 'minh-overlay.png') as sheet:
            self.assertEqual(sheet.size, (1792, 4320))
            self.assertGreater(sheet.getpixel((210, 200))[3], 0)
            self.assertEqual(sheet.getpixel((210, 360 + 200))[3], 0)
        self.assertEqual(json.loads((self.out / 'manifest.json').read_text())['grid'], [4, 12])
        # Repeated builds produce the same manifest and nonempty overlay.
        first = (self.out / 'manifest.json').read_bytes()
        build(self.src, self.out)
        self.assertEqual(first, (self.out / 'manifest.json').read_bytes())

    def test_incomplete_pose_rejected(self):
        self.frame()
        with self.assertRaisesRegex(SpriteValidationError, 'expected exactly'):
            build(self.src, self.out)
        self.assertFalse((self.out / 'manifest.json').exists())

    def test_duplicate_animation_rejected(self):
        self.pose()
        frame = (self.src / 'minh' / 'idle' / '00.png').read_bytes()
        for i in range(1, 4):
            (self.src / 'minh' / 'idle' / f'{i:02d}.png').write_bytes(frame)
        with self.assertRaisesRegex(SpriteValidationError, 'identical'):
            build(self.src, self.out)

    def test_wrong_size_rejected(self):
        self.pose()
        Image.new('RGBA', (400, 360), (255, 0, 0, 255)).save(self.src / 'minh' / 'idle' / '03.png')
        with self.assertRaisesRegex(SpriteValidationError, 'require RGBA'):
            build(self.src, self.out)

    def test_clipped_art_rejected(self):
        self.pose()
        path = self.src / 'minh' / 'idle' / '03.png'
        with Image.open(path) as opened:
            img = opened.copy()
        ImageDraw.Draw(img).rectangle((0, 200, 20, 280), fill=(255, 0, 0, 255))
        img.save(path)
        with self.assertRaisesRegex(SpriteValidationError, 'clipped'):
            build(self.src, self.out)


if __name__ == '__main__':
    unittest.main()
