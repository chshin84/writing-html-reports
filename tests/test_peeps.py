"""인물 그림 생성물 시험. 실행: python -B -m unittest discover -s tests -v (스킬 폴더에서)"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PEEPS = ROOT / "report-peeps.js"
ZIP = ROOT / "assets" / "open-peeps-src" / "Flat Assets.zip"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def load(path):
    text = path.read_text(encoding="utf-8")
    m = re.search(r"window\.RC_PEEPS = (\{.*\});\s*$", text, re.S)
    return text, json.loads(m.group(1))


class Peeps(unittest.TestCase):
    def test_four_figures_and_crop(self):
        text, data = load(PEEPS)
        self.assertEqual(sorted(data["figures"]), ["person", "person-done", "person-fail", "person-guide"])
        self.assertEqual(data["viewBox"], "0 150 1500 1500")
        self.assertTrue(text.startswith("/* report-peeps"))

    def test_no_color_literals(self):
        _, data = load(PEEPS)
        for name, svg in data["figures"].items():
            self.assertNotRegex(svg, r"#[0-9A-Fa-f]{3,6}\b", name)
            self.assertNotRegex(svg, r'fill="(?!none")', name)
            self.assertIn('class="pk"', svg, name)
            self.assertIn('class="pw"', svg, name)

    def test_size_budget(self):
        self.assertLess(PEEPS.stat().st_size, 130_000)

    @unittest.skipUnless(ZIP.exists(), "원본 묶음이 이 PC에 없다")
    def test_regenerates_identically(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "peeps.js"
            r = subprocess.run([sys.executable, "-B", str(ROOT / "tools" / "build-peeps.py"), str(out)],
                               capture_output=True, text=True, encoding="utf-8", env=ENV)
            self.assertEqual(r.returncode, 0, r.stderr)
            same = lambda p: p.read_bytes().replace(b"\r\n", b"\n")  # git이 체크아웃 때 줄바꿈을 바꿔도 비교가 흔들리지 않게 한다
            self.assertEqual(same(out), same(PEEPS))


if __name__ == "__main__":
    unittest.main()
