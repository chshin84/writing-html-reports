"""build.py 시험. 실행: python -B -m unittest discover -s tests -v (스킬 폴더에서)"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
CSS = "<style>\n/* BEGIN report-base (시험) */\n/* END report-base */\n</style>"
CHARTS = "<script>\n/* BEGIN report-charts 시험 */\n/* END report-charts */\n</script>"


def cdn(lib, ver):
    return f'<script src="https://cdn.jsdelivr.net/npm/{lib}@{ver}/dist/{lib}.min.js"></script>'


def build(path):
    return subprocess.run([sys.executable, "-B", str(ROOT / "build.py"), str(path)],
                          capture_output=True, text=True, encoding="utf-8", env=ENV)


class Build(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / "doc.html"

    def tearDown(self):
        self.dir.cleanup()

    def write(self, head):
        self.path.write_text(f"<html><head>{head}</head><body></body></html>", encoding="utf-8")

    def test_idempotent_with_charts(self):
        self.write(CSS + cdn("echarts", "6.1.0") + cdn("mermaid", "11.17.2") + cdn("gsap", "3.15.0") + CHARTS)
        r1 = build(self.path)
        first = self.path.read_bytes()
        r2 = build(self.path)
        self.assertEqual(r1.returncode, 0, r1.stderr)
        self.assertIn("연결 코드 반영", r1.stdout)
        self.assertEqual(first, self.path.read_bytes())
        self.assertEqual(r2.returncode, 0)
        text = self.path.read_text(encoding="utf-8")
        self.assertIn("report-charts for echarts@6.1.0", text)
        self.assertIn("/* BEGIN report-charts echarts@6.1.0 mermaid@11.17.2 gsap@3.15.0", text)

    def test_document_without_charts_gets_css_only(self):
        self.write(CSS + "<script>var x=1;</script>")
        r = build(self.path)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("연결 코드", r.stdout)
        self.assertIn("<script>var x=1;</script>", self.path.read_text(encoding="utf-8"))

    def test_rc_call_without_marker_stops(self):
        self.write(CSS + "<script>RC.chart(document.getElementById('c'),{});</script>")
        before = self.path.read_bytes()
        r = build(self.path)
        self.assertEqual(r.returncode, 1)
        self.assertIn("report-charts", r.stderr)
        self.assertEqual(before, self.path.read_bytes())

    def test_version_mismatch_stops(self):
        self.write(CSS + cdn("echarts", "6.0.0") + CHARTS)
        before = self.path.read_bytes()
        r = build(self.path)
        self.assertEqual(r.returncode, 1)
        self.assertIn("echarts", r.stderr)
        self.assertEqual(before, self.path.read_bytes())


if __name__ == "__main__":
    unittest.main()
