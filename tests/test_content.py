"""페이지 근거·별 표시·점수표 규칙 시험(checks/content.py). C3 소유."""
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from checks import content  # noqa: E402
from helpers import ROOT, page, paged, toc  # noqa: E402


class Scores(unittest.TestCase):
    GIST = '<li data-src="p2">가</li><li data-src="p2 p3">나</li><li data-src="p3">다</li><li data-src="p3 p4">라</li>'

    def test_expected_marks(self):
        rows = {x["id"]: x for x in content.page_scores(paged(self.GIST, {}))}
        self.assertTrue(rows["p1"]["excluded"])
        self.assertEqual((rows["p2"]["N"], rows["p2"]["R"], rows["p2"]["expect"]), (1, 2, "key"))
        self.assertEqual((rows["p3"]["N"], rows["p3"]["R"], rows["p3"]["expect"]), (1, 3, "core"))
        self.assertEqual((rows["p4"]["N"], rows["p4"]["expect"]), (0, ""))

    def test_matching_marks_ok(self):
        self.assertEqual(content.score_violations(paged(self.GIST, {2: "key", 3: "core"})), [])

    def test_mismatch_violation(self):
        fails = content.score_violations(paged(self.GIST, {2: "core"}))
        self.assertTrue(any(f.startswith("p2 표시 ★") for f in fails))
        self.assertTrue(any(f.startswith("p3 표시 -") for f in fails))

    def test_missing_data_src(self):
        fails = content.score_violations(paged('<li>근거 없음</li>', {}))
        self.assertTrue(any("data-src" in f for f in fails))

    def test_branch_breaks_tie(self):
        html = paged('<li data-src="p2">가</li><li data-src="p3">나</li>', {}).replace(
            '<section class="page" id="p3"><h2>구조 B</h2>', '<section class="page" id="p3"><h2>구조 B</h2><svg><polygon points="0,0 1,1"/></svg>')
        rows = {x["id"]: x for x in content.page_scores(html)}
        self.assertEqual((rows["p3"]["B"], rows["p3"]["expect"], rows["p2"]["expect"]), (1, "core", "key"))

    def test_key_needs_half_of_core(self):
        gist = '<li data-src="p2">가</li>' + '<li data-src="p3">나</li>' * 3
        rows = {x["id"]: x for x in content.page_scores(paged(gist, {}))}
        self.assertEqual((rows["p3"]["expect"], rows["p2"]["expect"]), ("core", ""))

    def test_conclusion_and_appendix_excluded(self):
        rows = content.page_scores(paged('<li data-src="p2">가</li><li data-src="p3">나</li>', {},
                                       ("요약", "결론", "부록 A", "구조")))
        self.assertTrue(all(x["expect"] == "" for x in rows))

    def test_demo_figure_not_counted_in_branches(self):
        fig = ('<figure id="d1" data-anim="구조"><svg><polygon points="0,0 1,1"/></svg>'
               '<pre class="mermaid">flowchart LR\n A{판단} --> B[가]</pre></figure>')
        html = paged('<li data-src="p2">가</li>', {}).replace(
            "<h2>구조 A</h2>", "<h2>구조 A</h2>" + fig + '<svg><polygon points="0,0 1,1"/></svg>')
        rows = {x["id"]: x for x in content.page_scores(html)}
        self.assertEqual(rows["p2"]["B"], 1)

class Stars(unittest.TestCase):
    def test_one_core_two_key_ok(self):
        self.assertEqual(content.star_violations(toc("core", "key", "key", "")), [])

    def test_two_core(self):
        self.assertTrue(any("★ 핵심 페이지 2개" in f for f in content.star_violations(toc("core", "core"))))

    def test_three_key(self):
        fails = content.star_violations(toc("core", "key", "key", "key"))
        self.assertTrue(any("☆ 중요 페이지 3개" in f for f in fails))
        self.assertTrue(any("별 표시 페이지 4개" in f for f in fails))

    def test_key_without_core(self):
        self.assertTrue(any("★이 없다" in f for f in content.star_violations(toc("key"))))



class PageName(unittest.TestCase):
    def test_sec_read_first(self):
        body = '<p class="sec">구조 A</p><h2>요약 기준이 A보다 12% 낮다</h2>'
        self.assertEqual(content.page_name(body), "구조 A")

    def test_h2_without_sec(self):
        self.assertEqual(content.page_name("<h2>구조 <b>A</b></h2>"), "구조 A")

    def test_sec_name_overrides_h2(self):
        html = paged('<li data-src="p2">가</li>', {}).replace(
            "<h2>구조 A</h2>", '<p class="sec">구조 A</p><h2>요약하면 A가 12% 빠르다</h2>')
        rows = {x["id"]: x for x in content.page_scores(html)}
        self.assertEqual((rows["p2"]["title"], rows["p2"]["excluded"], rows["p2"]["expect"]), ("구조 A", False, "core"))

    def test_h2_summary_still_excluded_without_sec(self):
        html = paged('<li data-src="p2">가</li>', {}).replace("<h2>구조 A</h2>", "<h2>요약 A</h2>")
        rows = {x["id"]: x for x in content.page_scores(html)}
        self.assertTrue(rows["p2"]["excluded"])

    def test_violation_names_sec(self):
        html = page(body='<section class="page" id="p1"><p class="sec">구조 A</p><h2>A가 빠르다</h2><p>글</p></section>')
        self.assertEqual(content.page_violations(html), ["근거 없는 페이지(표·도표·핵심 수치 없음): 구조 A"])


if __name__ == "__main__":
    unittest.main()
