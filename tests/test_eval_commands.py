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

    def test_reopen_not_ready_figure_skipped(self):  # F2: 다시 연 탭이 준비되지 않은 figure는 단계 장면을 생략하고 기록한다
        from test_eval_gates import FAKE_RC, GOOD, STAGE, doc
        # 1280 컨텍스트에서 세 번째로 열 때(장면 목록 → figure 목록 → figure 다시 열기) 정적 목록으로 물러나게 한다
        script = ("window.FAKE = " + json.dumps(GOOD, ensure_ascii=False) + ";" + FAKE_RC
                  + "var k = +(localStorage.c0k || 0) + 1; localStorage.c0k = k; var f = document.getElementById('d');"
                  + "if (innerWidth === 1280 && k >= 3) f.classList.add('demo-static'); else RC.demo(f, []);")
        src = Path(self.tmp.name, "doc.html")
        src.write_text(doc(STAGE, script), encoding="utf-8")
        out = Path(self.tmp.name, "shots")
        r = run(ROOT / "eval/shoot.py", src, out)
        self.assertEqual(r.returncode, 0, r.stderr)
        idx = json.loads((out / "index.json").read_text(encoding="utf-8"))
        self.assertEqual([x for x in idx if x["kind"] != "page"],
                         [{"kind": "skipped", "figure": "d", "reason": "다시 연 탭에서 data-rc-ready가 오지 않았다"}])
        self.assertFalse((out / "d-s1.png").exists())

    def test_nonempty_out_stops_without_deleting(self):  # F9: 비어 있지 않은 출력 폴더면 지우지 않고 멈춘다
        src = Path(self.tmp.name, "doc.html")
        src.write_text("<p>글</p>", encoding="utf-8")
        out = Path(self.tmp.name, "shots")
        out.mkdir()
        (out / "old.png").write_bytes(b"old")
        r = run(ROOT / "eval/shoot.py", src, out)
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("비어 있지 않다", r.stderr)
        self.assertEqual([p.name for p in out.iterdir()], ["old.png"])
        self.assertEqual((out / "old.png").read_bytes(), b"old")


DEFECTS = ["애니메이션 단계가 읽기 전에 넘어간다", "설명이 도형에서 떨어져 하단 자막으로만 나온다",
           "강조 노드와 설명을 한 화면에서 함께 볼 수 없다", "현재 노드와 지나온 노드가 구분되지 않는다",
           "390 폭에서 표를 읽기 어렵거나 가로 스크롤 단서가 없다", "페이지 번호가 두 번 보인다", "용어 풀이 배치가 깨진다",
           "제목만 읽으면 논지가 보이지 않는다", "같은 사실을 불릿·도식·표로 반복한다", "결정 요청에 권장안이 없다",
           "전후 비교의 기준선이 끝 장면에서 사라진다", "불릿과 표의 내용이 서로 다르다", "근거 없는 주장이 있다"]


class Checklist(unittest.TestCase):
    def test_items_cover_defects_and_labels(self):
        import checklist_vote as cv
        items = cv.load_items(ROOT / "eval/checklist.md")
        self.assertGreaterEqual(len(items), 13)
        self.assertEqual(len({i["id"] for i in items}), len(items))
        for i in items:
            self.assertIn(i["category"], {"사용자 만족도", "심미성", "구성", "이해 용이성", "논리 전개"})
            self.assertIn(i["target"], {"motion", "layout", "content"})
        for d in DEFECTS:
            self.assertTrue(any(d in i["defect"] for i in items), d)

    def test_majority_and_coverage(self):
        import checklist_vote as cv
        self.assertEqual(cv.majority(["예", "예", "아니오"]), "예")
        self.assertEqual(cv.majority(["예", "아니오", "해당 없음"]), "아니오")
        self.assertEqual(cv.majority(["해당 없음"] * 3), "해당 없음")
        self.assertFalse(cv.stable(["예", "예", "아니오"]))
        items = [{"id": "a", "target": "motion"}, {"id": "b", "target": "motion"}, {"id": "c", "target": "layout"}]
        run = lambda a, b, c: [{"id": "a", "answer": a, "evidence": ""}, {"id": "b", "answer": b, "evidence": ""}, {"id": "c", "answer": c, "evidence": ""}]
        per = cv.answers({"s": [run("예", "아니오", "해당 없음"), run("예", "아니오", "해당 없음"), run("예", "예", "해당 없음")]})
        t = cv.tally(per, items)
        self.assertEqual(t["coverage"]["s"], {"motion": 0.5, "layout": None, "content": None})
        self.assertEqual(t["samples"]["s"]["b"]["majority"], "아니오")
        self.assertFalse(t["samples"]["s"]["b"]["stable"])
        fixed = cv.merge(per, {"s": {"b": ["예", "예", "예"]}})
        self.assertEqual(cv.tally(fixed, items)["coverage"]["s"]["motion"], 1.0)
        self.assertNotIn("x", cv.tally({"s": {"x": ["예"] * 3}}, items)["samples"]["s"])  # 뺀 항목은 묶지 않는다

    def test_input_validation(self):  # F8: 실행 결과 수와 답의 표기를 검사한다
        import checklist_vote as cv
        with tempfile.TemporaryDirectory() as tmp:
            def write(folder, sample, k, ans):
                d = Path(tmp, folder)
                d.mkdir(exist_ok=True)
                (d / f"{sample}-run{k}.json").write_text(json.dumps(
                    [{"id": i, "answer": a, "evidence": ""} for i, a in ans.items()], ensure_ascii=False), encoding="utf-8")
                return d
            for k in (1, 2):
                two = write("two", "s", k, {"a": "예"})
            with self.assertRaisesRegex(ValueError, "s"):
                cv.load_runs(two)
            for k in (1, 2, 3):
                dot = write("dot", "s", k, {"a": "예." if k == 2 else "예"})
            with self.assertRaisesRegex(ValueError, "예\."):
                cv.load_runs(dot)
            for k in (1, 2, 3):
                good = write("good", "s", k, {"a": "예", "b": "해당 없음"})
            self.assertEqual(cv.load_runs(good)["s"]["b"], ["해당 없음"] * 3)
            for k in (1, 2, 3):  # 보정 폴더는 항목마다 답이 3개여야 한다
                part = write("part", "s", k, {"a": "아니오"} if k < 3 else {"b": "예"})
            with self.assertRaisesRegex(ValueError, "a"):
                cv.load_runs(part, partial=True)
            for k in (1, 2, 3):
                okp = write("okp", "s", k, {"a": "아니오"})
            self.assertEqual(cv.load_runs(okp, partial=True), {"s": {"a": ["아니오"] * 3}})


class Prompts(unittest.TestCase):
    SLOTS = {"checklist-review.md": "{{CHECKLIST}}", "comprehension.md": "{{QUESTIONS}}",
             "planted-error.md": "{{ERROR_HINT_SCOPE}}", "title-link.md": "{{STAGE}}"}

    def test_slots_only_no_answers(self):
        for name, slot in self.SLOTS.items():
            text = (ROOT / "eval/prompts" / name).read_text(encoding="utf-8")
            self.assertIn("{{INPUT_DIR}}", text, name)
            self.assertIn(slot, text, name)
            for banned in ("정답:", "정답은", "모범 답", "answer key", "심은 오류는"):
                self.assertNotIn(banned, text, name)
            self.assertNotIn("writing-html-reports", text, name)
            self.assertNotIn("whr-c0", text, name)


if __name__ == "__main__":
    unittest.main()
