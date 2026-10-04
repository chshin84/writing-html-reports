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


RUN = '<span class="state" data-state="run">실행으로 확인함</span>'
INFER = '<span class="state" data-state="infer">추론함</span>'


class RunSource(unittest.TestCase):
    """실행 확인 줄(data-state="run")에 원자료(code 요소, 파일:줄, 커밋 해시)가 같은 줄에 있는지 본다."""

    def fails(self, line, old=None):
        html = wrapup(f"<ul>{line}</ul>" + PARTS_ALL)
        return content.run_source_violations(html, None if old is None else wrapup(f"<ul>{old}</ul>" + PARTS_ALL))

    def test_code_ok(self):
        self.assertEqual(self.fails(f"<li>{RUN} 시험 18건 통과(<code>python -m pytest</code>)</li>"), [])

    def test_file_line_ok(self):
        self.assertEqual(self.fails(f"<li>{RUN} 검사 함수가 있다(checks/content.py:120)</li>"), [])

    def test_commit_ok(self):
        self.assertEqual(self.fails(f"<li>{RUN} 커밋 b2cfc00에서 바뀌었다</li>"), [])

    def test_table_row_ok(self):
        row = f"<table><tr><td>{RUN} 단위 시험</td><td><code>python -m pytest</code></td></tr></table>"
        self.assertEqual(content.run_source_violations(wrapup(row + PARTS_ALL)), [])

    def test_missing(self):
        self.assertEqual(self.fails(f"<li>{RUN} 설계대로 동작한다</li>"),
                         ["실행 확인 줄에 원자료 없음: 실행으로 확인함 설계대로 동작한다"])

    def test_plain_path_is_not_source(self):
        self.assertEqual(len(self.fails(f"<li>{RUN} spec docs/a-design.md를 읽었다</li>")), 1)

    def test_doc_path_code_is_not_source(self):
        self.assertEqual(len(self.fails(f"<li>{RUN} 기준값은 0.5다(<code>docs/a-design.md</code>)</li>")), 1)

    def test_doc_path_with_line_ok(self):
        self.assertEqual(self.fails(f"<li>{RUN} 기준값은 0.5다(<code>docs/a-design.md:42</code>)</li>"), [])

    def test_unclosed_items_are_separate_lines(self):
        self.assertEqual(len(self.fails(f"<li>{RUN} 설계대로 동작한다<li>{RUN} 시험(<code>python -m pytest</code>)")), 1)

    def test_old_has_other_violation(self):
        self.assertEqual(len(self.fails(f"<li>{RUN} 경계 조건 B도 맞다</li>", f"<li>{RUN} 경계 조건 A가 맞다</li>")), 1)

    def test_paged_violation(self):
        pages = "".join(f'<section class="page" id="p{i}" data-part="{p}"><h2>절</h2><ul><li>{RUN} 동작한다</li></ul></section>'
                        for i, p in enumerate(PART_IDS, 1))
        self.assertEqual(len(content.run_source_violations(wrapup(pages))), 5)

    def test_infer_not_checked(self):
        self.assertEqual(self.fails(f"<li>{INFER} 설계대로 동작한다</li>"), [])

    def test_old_same(self):
        line = f"<li>{RUN} 설계대로 동작한다</li>"
        self.assertEqual(self.fails(line, line), [])

    def test_new_convention_not_wrapup(self):
        self.assertEqual(content.run_source_violations(new_doc(f"<ul><li>{RUN} 글</li></ul>")), [])


class SummarySource(unittest.TestCase):
    """머리말·요약 줄(첫 data-part 절 앞의 .gist 항목과 확인 상태가 붙은 줄)에 보이는 근거 위치가 있는지 본다."""

    def fails(self, gist, head="", old=None):
        def doc(g):
            return wrapup(f'{head}<div class="gist"><h2>요약</h2><ul>{g}</ul></div>' + PARTS_ALL)
        return content.summary_source_violations(doc(gist), None if old is None else doc(old))

    def test_link_ok(self):
        html = wrapup('<div class="gist"><ul><li data-src="p2">결론이다(<a href="#p2">바뀐 것</a>)</li></ul></div>'
                      + PARTS_ALL.replace('data-part="changed"', 'id="p2" data-part="changed"'))
        self.assertEqual(content.summary_source_violations(html), [])

    def test_dangling_link(self):
        self.assertEqual(len(self.fails('<li>결론이다(<a href="#p9">없는 절</a>)</li>')), 1)

    def test_external_link_ok(self):
        self.assertEqual(self.fails('<li>결론이다(<a href="https://example.com/log">실행 기록</a>)</li>'), [])

    def test_gist_title_is_not_section(self):
        self.assertEqual(len(self.fails("<li>결론이다(「요약」)</li>")), 1)

    def test_gist_paragraph_not_checked(self):
        html = wrapup('<div class="gist"><p>아래는 결론입니다.</p><ul><li>결론(「남은 일」)</li></ul></div>' + PARTS_ALL)
        self.assertEqual(content.summary_source_violations(html), [])

    def test_paged_violation(self):
        p1 = '<section class="page" id="p1"><div class="gist"><ul><li data-src="p2">결론이다</li></ul></div></section>'
        pages = "".join(f'<section class="page" id="p{i}" data-part="{p}"><h2>절</h2></section>'
                        for i, p in enumerate(PART_IDS, 2))
        self.assertEqual(content.summary_source_violations(wrapup(p1 + pages)), ["요약 줄에 근거 위치 없음: 결론이다"])

    def test_section_name_ok(self):
        self.assertEqual(self.fails("<li>결론이다(「결정 요청」 참조)</li>"), [])

    def test_unknown_section_name(self):
        self.assertEqual(len(self.fails("<li>결론이다(「없는 절」 참조)</li>")), 1)

    def test_code_ok(self):
        self.assertEqual(self.fails("<li>결론이다(<code>logs/run.txt</code>)</li>"), [])

    def test_commit_or_path_ok(self):
        self.assertEqual(self.fails("<li>결론이다(커밋 b2cfc00, docs/a-design.md)</li>"), [])

    def test_data_src_alone_is_hidden(self):
        self.assertEqual(self.fails('<li data-src="p2">결론이다</li>'),
                         ["요약 줄에 근거 위치 없음: 결론이다"])

    def test_head_line_with_state(self):
        head = f'<header class="doc-head"><p class="lede">{INFER} 33개 시도가 모두 빠진다</p></header>'
        self.assertEqual(self.fails('<li>결론이다(「남은 일」)</li>', head),
                         [f"요약 줄에 근거 위치 없음: 추론함 33개 시도가 모두 빠진다"])

    def test_head_line_without_state_not_checked(self):
        head = '<header class="doc-head"><p class="lede">이 보고서는 무엇을 했는가?</p></header>'
        self.assertEqual(self.fails('<li>결론이다(「남은 일」)</li>', head), [])

    def test_body_section_not_checked(self):
        html = wrapup('<div class="gist"><ul><li>결론(「남은 일」)</li></ul></div>'
                      + PARTS_ALL.replace("<h2>절</h2>", f"<h2>절</h2><ul><li>{INFER} 근거 없는 줄</li></ul>"))
        self.assertEqual(content.summary_source_violations(html), [])

    def test_old_same(self):
        self.assertEqual(self.fails("<li>결론이다</li>", old="<li>결론이다</li>"), [])

    def test_new_convention_not_wrapup(self):
        html = new_doc('<div class="gist"><ul><li>결론이다</li></ul></div>')
        self.assertEqual(content.summary_source_violations(html), [])


class FixedNoFalsePositive(unittest.TestCase):
    """새 규칙은 고정 견본과 template.html(새 규약 문서가 아님)에 위반을 내지 않는다."""

    def test_zero(self):
        files = sorted((ROOT / "bench" / "fixed").glob("*.html")) + [ROOT / "template.html"]
        for f in files:
            html = f.read_text(encoding="utf-8")
            for fn in (content.abbr_violations, content.parts_violations, content.basis_violations,
                       content.run_source_violations, content.summary_source_violations):
                self.assertEqual(fn(html), [], f"{f.name} {fn.__name__}")

    def test_source_rules_zero_on_samples(self):
        """원자료·근거 위치 규칙은 마무리 보고서 견본에 위반을 내지 않는다.
        template-paged.html은 마무리 보고서 표시가 없어 적용 대상이 아님을 확인한다."""
        for f in (ROOT / "template-paged.html", ROOT / "examples" / "wrapup.html"):
            html = f.read_text(encoding="utf-8")
            for fn in (content.run_source_violations, content.summary_source_violations):
                self.assertEqual(fn(html), [], f"{f.name} {fn.__name__}")


if __name__ == "__main__":
    unittest.main()
