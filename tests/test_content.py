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


SEC = '<p class="sec">절</p>'
MSG = "(.gloss 용어나 처음 나온 곳의 괄호 풀이를 둔다)"


def new_doc(body):
    """새 규약 문서(.sec 사용)."""
    return page(body=SEC + body)


class Abbr(unittest.TestCase):
    def test_glossed_ok(self):
        html = new_doc('<p>API를 쓴다.</p><dl class="gloss"><div><dt>API</dt><dd>응용 프로그램 인터페이스</dd></div></dl>')
        self.assertEqual(content.abbr_violations(html), [])

    def test_paren_ok(self):
        self.assertEqual(content.abbr_violations(new_doc("<p>API(응용 프로그램 인터페이스)를 쓴다. API는 빠르다.</p>")), [])

    def test_paren_around_ok(self):
        self.assertEqual(content.abbr_violations(new_doc("<p>상장지수펀드(ETF)와 상장지수증권 (ETN)을 산다.</p>")), [])

    def test_bare_paren_is_not_gloss(self):
        self.assertEqual(content.abbr_violations(new_doc("<p>(ETF)를 산다.</p>")), ["약어 풀이 없음: ETF" + MSG])

    def test_unglossed(self):
        self.assertEqual(content.abbr_violations(new_doc("<p>API를 쓴다. 그 뒤 API(설명)를 본다.</p>")),
                         ["약어 풀이 없음: API" + MSG])

    def test_reported_once_in_order(self):
        self.assertEqual(content.unglossed(new_doc("<p>SDK와 API와 SDK를 쓴다.</p>")), ["SDK", "API"])

    def test_abbr_with_period_and_particle(self):
        self.assertEqual(content.unglossed(new_doc("<p>끝은 API.</p><p>ETF를 산다.</p>")), ["API", "ETF"])

    def test_paren_after_tag(self):
        self.assertEqual(content.abbr_violations(new_doc("<p><b>API</b>(응용 프로그램 인터페이스)</p>")), [])

    def test_slash_joined_abbrs(self):
        self.assertEqual(content.unglossed(new_doc("<p>ETF/ETN을 산다.</p>")), ["ETF", "ETN"])

    def test_block_boundary_paragraph(self):
        self.assertEqual(content.unglossed(new_doc("<p>상장지수펀드</p><p>(ETF)를 산다.</p>")), ["ETF"])

    def test_block_boundary_list_item(self):
        self.assertEqual(content.unglossed(new_doc("<ul><li>상장지수펀드</li><li>(ETF)</li></ul>")), ["ETF"])

    def test_block_boundary_table_cell(self):
        html = new_doc("<table><tr><td>상장지수펀드</td><td>(ETF)</td></tr></table>")
        self.assertEqual(content.unglossed(html), ["ETF"])

    def test_paren_across_inline_tag_ok(self):
        self.assertEqual(content.unglossed(new_doc("<p>상장지수펀드(<b>ETF</b>)</p>")), [])

    def test_old_has_same(self):
        old = new_doc("<p>API를 쓴다.</p>")
        new = new_doc("<p>API를 쓴다. ETF도 쓴다.</p>")
        self.assertEqual(content.abbr_violations(new, old), ["약어 풀이 없음: ETF" + MSG])

    def test_old_not_new_convention_still_subtracts(self):
        self.assertEqual(content.abbr_violations(new_doc("<p>API</p>"), page(body="<p>API</p>")), [])

    def test_not_new_convention(self):
        self.assertEqual(content.abbr_violations(page(body="<p>API를 쓴다.</p>")), [])

    def test_wrapup_mark_is_new_convention(self):
        html = page(body="<p>API</p>").replace('<main class="doc">', '<main class="doc" data-kind="wrapup">')
        self.assertEqual(content.abbr_violations(html), ["약어 풀이 없음: API" + MSG])


class AbbrExcluded(unittest.TestCase):
    def ok(self, body):
        self.assertEqual(content.abbr_violations(new_doc(body)), [], body)

    def test_code(self):
        self.ok("<p><code>API</code></p>")

    def test_pre(self):
        self.ok("<pre>API CLI</pre>")

    def test_mermaid(self):
        self.ok('<pre class="mermaid">flowchart LR\n A --> B</pre>')

    def test_script(self):
        self.ok("<script>var s = 'API';</script>")

    def test_svg(self):
        self.ok("<svg><text>API</text></svg>")

    def test_digit_tokens(self):
        self.ok("<p>G1과 Q4와 HTML5</p>")

    def test_file_name_piece(self):
        self.ok("<p>SKILL.md와 README.txt를 읽는다.</p>")

    def test_path_with_extension(self):
        self.ok("<p>docs/API.md를 읽는다.</p>")

    def test_single_letter_slash(self):
        self.ok("<p>A/B 시험</p>")

    def test_hyphen_identifier_piece(self):
        self.ok("<p>lens-API와 PR-12와 X-API-KEY</p>")

    def test_length_bounds(self):
        self.ok("<p>A와 ABCDEFG</p>")


PART_IDS = ("changed", "achieved", "remaining", "decisions", "verification")
PARTS_ALL = "".join(f'<section data-part="{p}"><h2>절</h2></section>' for p in PART_IDS)


def wrapup(body, head='<p class="basis">기준: 커밋 b2cfc00</p>'):
    return page(body=head + body).replace('<main class="doc">', '<main class="doc" data-kind="wrapup">')


class Parts(unittest.TestCase):
    def test_all_present(self):
        self.assertEqual(content.parts_violations(wrapup(PARTS_ALL)), [])

    def test_missing(self):
        body = PARTS_ALL.replace('data-part="decisions"', 'data-part="x"')
        self.assertEqual(content.parts_violations(wrapup(body)), ["마무리 보고서 필수 절 없음: decisions(결정 요청)"])

    def test_old_missing_same(self):
        body = PARTS_ALL.replace('data-part="decisions"', 'data-part="x"')
        self.assertEqual(content.parts_violations(wrapup(body), wrapup(body)), [])

    def test_new_convention_not_wrapup(self):
        self.assertEqual(content.parts_violations(new_doc("<p>글</p>")), [])

    def test_not_new_convention(self):
        self.assertEqual(content.parts_violations(page(body=PARTS_ALL.replace('data-part="decisions"', ""))), [])

    def test_parts_on_page_sections(self):
        pages = "".join(f'<section class="page" id="p{i}" data-part="{p}"><h2>절</h2><table></table></section>'
                        for i, p in enumerate(PART_IDS, 1))
        self.assertEqual(content.parts_violations(wrapup(pages)), [])

    def test_parts_need_page_shape(self):
        pages = "".join(f'<section class="page" id="p{i}" data-part="{p}"><h2>절</h2><table></table></section>'
                        for i, p in enumerate(PART_IDS[:4], 1))
        pages += '<section data-part="verification" class="page" id="p5"><h2>절</h2></section>'
        self.assertEqual(content.parts_violations(wrapup(pages)), ["마무리 보고서 필수 절 없음: verification(검증 범위)"])


class Basis(unittest.TestCase):
    def fails(self, head):
        return content.basis_violations(wrapup(PARTS_ALL, head))

    def test_hash_ok(self):
        self.assertEqual(self.fails('<p class="basis">기준: 커밋 b2cfc00</p>'), [])

    def test_md_path_ok(self):
        self.assertEqual(self.fails('<p class="basis">기준: <code>docs/specs/a-design.md</code></p>'), [])

    def test_file_path_ok(self):
        self.assertEqual(self.fails('<p class="basis">원자료 data/raw.csv</p>'), [])

    def test_known_extension_name_ok(self):
        self.assertEqual(self.fails('<p class="basis">원자료 성과표.xlsx</p>'), [])

    def test_basis_hash_before_hangul(self):
        self.assertEqual(self.fails('<p class="basis">b2cfc00커밋 기준</p>'), [])

    def test_missing(self):
        self.assertEqual(self.fails(""), ["원본 기준 없음: 문서 머리(첫 section 끝 앞)에 p.basis가 없다"])

    def test_after_first_section(self):
        html = wrapup(PARTS_ALL + '<p class="basis">b2cfc00</p>', "")
        self.assertEqual(content.basis_violations(html), ["원본 기준 없음: 문서 머리(첫 section 끝 앞)에 p.basis가 없다"])

    def test_inside_first_page_ok(self):
        body = '<section class="page" id="p1"><div class="doc-head"><p class="basis">커밋 b2cfc00</p></div></section>'
        self.assertEqual(content.basis_violations(wrapup(body, "")), [])

    def test_no_reference(self):
        self.assertEqual(self.fails('<p class="basis">기준: 어제 회의 3.5절</p>'),
                         ["원본 기준에 커밋 해시·.md 경로·파일 경로가 없다: 기준: 어제 회의 3.5절"])

    def test_digits_and_abbrev_rejected(self):
        self.assertEqual(len(self.fails('<p class="basis">기준: 20261004 회의(e.g. 주간 점검), U.S 자료</p>')), 1)

    def test_short_hex_rejected(self):
        self.assertEqual(len(self.fails('<p class="basis">abc12</p>')), 1)

    def test_old_same(self):
        html = wrapup(PARTS_ALL, "")
        self.assertEqual(content.basis_violations(html, html), [])

    def test_new_convention_not_wrapup(self):
        self.assertEqual(content.basis_violations(new_doc("<p>글</p>")), [])

    def test_not_new_convention(self):
        self.assertEqual(content.basis_violations(page(body="<p>글</p>")), [])


class FixedNoFalsePositive(unittest.TestCase):
    """새 규칙은 고정 견본과 template.html(새 규약 문서가 아님)에 위반을 내지 않는다."""

    def test_zero(self):
        files = sorted((ROOT / "bench" / "fixed").glob("*.html")) + [ROOT / "template.html"]
        for f in files:
            html = f.read_text(encoding="utf-8")
            for fn in (content.abbr_violations, content.parts_violations, content.basis_violations):
                self.assertEqual(fn(html), [], f"{f.name} {fn.__name__}")


if __name__ == "__main__":
    unittest.main()
