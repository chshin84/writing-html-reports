"""C0 명령 시험: rebuild·shoot·고정 견본·체크리스트·프롬프트. 실행: python -B -m unittest discover -s tests"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
CSS = "<style>\n/* BEGIN report-base (시험) */\n/* END report-base */\n</style>"


def run(*args):
    return subprocess.run([sys.executable, "-B", *map(str, args)], capture_output=True, text=True,
                          encoding="utf-8", env=ENV)


def digest(folder):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(folder).iterdir())}


class Bench(unittest.TestCase):
    def test_sources_match_files(self):
        rows = json.loads((ROOT / "bench/fixed/SOURCES.json").read_text(encoding="utf-8"))
        self.assertEqual({r["file"] for r in rows}, {"04-rules.html", "03-groups.html", "session-report.html",
                                                     "sample-anim.html", "sample-viz.html"})
        for r in rows:
            data = (ROOT / "bench/fixed" / r["file"]).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), r["sha256"], r["file"])


class Rebuild(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.bench = Path(self.tmp.name, "bench")
        self.out = Path(self.tmp.name, "out")
        self.bench.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_build_failure_code_passes_through_and_bench_unchanged(self):
        import rebuild
        (self.bench / "bad.html").write_text("<html><head></head><body></body></html>", encoding="utf-8")
        before = digest(self.bench)
        self.assertEqual(rebuild.main([str(self.out)], bench=self.bench), 1)  # build.py가 표시 없는 문서에서 1로 끝난다
        self.assertEqual(digest(self.bench), before)

    def test_success_fills_blocks_from_worktree(self):
        import rebuild
        (self.bench / "ok.html").write_text(f"<html><head>{CSS}</head><body></body></html>", encoding="utf-8")
        before = digest(self.bench)
        self.assertEqual(rebuild.main([str(self.out)], bench=self.bench), 0)
        built = (self.out / "ok.html").read_text(encoding="utf-8")
        self.assertIn((ROOT / "report-base.css").read_text(encoding="utf-8")[:200], built)
        self.assertEqual(digest(self.bench), before)

    def test_block_mismatch_fails(self):
        import rebuild
        p = Path(self.tmp.name, "x.html")
        p.write_text("<style>\n/* BEGIN report-base (시험) */\n낡은 내용\n/* END report-base */\n</style>", encoding="utf-8")
        self.assertEqual(rebuild.mismatches(p), ["report-base"])


class Shoot(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def test_named_files_and_index(self):
        from test_eval_gates import FAKE_RC, GOOD, PAGER, PAGE_JS, STAGE, doc
        body = (PAGER + '<section class="page" id="p1"><p class="pno">1 / 2</p><p>첫 페이지</p></section>'
                f'<section class="page" id="p2"><p class="pno">2 / 2</p>{STAGE}</section>')
        script = PAGE_JS + "window.FAKE = " + json.dumps(GOOD, ensure_ascii=False) + ";" + FAKE_RC + "RC.demo(document.getElementById('d'), []);"
        src = Path(self.tmp.name, "doc.html")
        src.write_text(doc(body, script), encoding="utf-8")
        out = Path(self.tmp.name, "shots")
        r = run(ROOT / "eval/shoot.py", src, out)
        self.assertEqual(r.returncode, 0, r.stderr)
        names = {p.name for p in out.iterdir()}
        for n in ("p1-1280.png", "p1-390.png", "p2-1280.png", "p2-390.png", "p1.txt", "p2.txt",
                  "d-s1.png", "d-s2.png", "index.json"):
            self.assertIn(n, names)
        idx = json.loads((out / "index.json").read_text(encoding="utf-8"))
        steps = [x for x in idx if x["kind"] == "step"]
        self.assertEqual([(x["figure"], x["step"], x["seconds"]) for x in steps], [("d", 1, 3.5), ("d", 2, 3.5)])
        self.assertIn("첫 페이지", (out / "p1.txt").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
