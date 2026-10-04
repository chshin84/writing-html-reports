"""서식·라벨·스크립트 주소 규칙 시험(checks/style.py). C2 소유. 실행: python -B -m unittest discover -s tests -v"""
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from checks import style  # noqa: E402
from helpers import cdn, has, page  # noqa: E402
import re  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "eval"))
from measure import contrast, cvd_pairs, delta_e76, parse_color  # noqa: E402

CSS = (Path(__file__).resolve().parent.parent / "report-base.css").read_text(encoding="utf-8")
HEADS = (r":root\{", r':root:not\(\[data-theme="light"\]\)\{', r':root\[data-theme="dark"\]\{')
NAMES = {"paper", "ink", "ink-2", "ink-3", "rule", "hair", "tint", "accent", "accent-2", "neg", "s1", "s2", "s3", "s4"}


def token_blocks():
    """토큰 정의(밝음, prefers 어두움, data-theme 어두움)의 {이름: #rrggbb}."""
    out = []
    for head in HEADS:
        body = re.search(head + r"([^}]*)\}", CSS).group(1)
        out.append(dict(re.findall(r"--([\w-]+):\s*(#[0-9A-Fa-f]{6})\b", body)))
    return out


def cr(a, b):
    return contrast(parse_color(a), parse_color(b))


class Tokens(unittest.TestCase):
    def test_names_kept_and_dark_blocks_equal(self):
        light, dark, dark2 = token_blocks()
        for block in (light, dark):
            self.assertLessEqual(NAMES, set(block))
        self.assertEqual(dark, dark2)

    def test_chg_background(self):
        for t in token_blocks()[:2]:
            self.assertGreaterEqual(delta_e76(parse_color(t["chg"]), parse_color(t["tint"])), 5)
            for ink in ("ink", "ink-2"):
                self.assertGreaterEqual(cr(t[ink], t["chg"]), 4.5, ink)

    def test_accent_2(self):
        for t in token_blocks()[:2]:
            for bg in ("paper", "tint"):
                self.assertGreaterEqual(cr(t["accent-2"], t[bg]), 3.0, bg)
            self.assertGreaterEqual(cr(t["accent-2"], t["accent"]), 1.5)

    def test_series_contrast(self):
        for t in token_blocks()[:2]:
            self.assertEqual(t["s1"].upper(), t["accent"].upper())
            for s in ("s2", "s3", "s4"):
                for bg in ("paper", "tint"):
                    self.assertGreaterEqual(cr(t[s], t[bg]), 3.0, (s, bg))

    def test_series_cvd_with_accent_2(self):
        for t in token_blocks()[:2]:
            pairs = cvd_pairs({s: parse_color(t[s]) for s in ("s1", "s2", "s3", "s4", "accent-2")})
            self.assertGreaterEqual(min(de for _, _, de in pairs), 15, pairs)

    def test_baseline_grey_vs_s1(self):
        light = token_blocks()[0]
        self.assertGreaterEqual(cr(light["s4"], light["s1"]), 3.0)

    def test_ink_3_on_tint(self):
        light = token_blocks()[0]
        self.assertGreaterEqual(cr(light["ink-3"], light["tint"]), 4.5)


class Movement(unittest.TestCase):
    def test_animation_false_in_script_is_not_movement(self):
        self.assertFalse(has(style.style_violations(page(script="RC.chart(b,{animation:false})")), "움직임"))

    def test_css_transition_is_movement(self):
        self.assertTrue(has(style.style_violations(page(style="a{transition:opacity 1s}")), "움직임"))

    def test_inline_style_animation_is_movement(self):
        self.assertTrue(has(style.style_violations(page(body='<p style="animation:x 1s">가</p>')), "움직임"))

    def test_intersection_observer_is_movement(self):
        self.assertTrue(has(style.style_violations(page(script="new IntersectionObserver(f)")), "움직임"))


class ScriptStyle(unittest.TestCase):
    def test_disallowed_src(self):
        html = page(head='<script src="https://unpkg.com/echarts@6.1.0/dist/echarts.min.js"></script>')
        self.assertTrue(has(style.script_style_violations(html), "허용 밖 스크립트"))

    def test_unpinned_src(self):
        self.assertTrue(has(style.script_style_violations(page(head=cdn("echarts", "6"))), "버전 미고정"))

    def test_pinned_src_ok(self):
        head = cdn("echarts") + cdn("mermaid") + cdn("gsap")
        self.assertEqual(style.script_style_violations(page(head=head)), [])

    def test_unpinned_module_import(self):
        html = page(head="<script type=\"module\">import mermaid from "
                         "'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs'</script>")
        self.assertTrue(has(style.script_style_violations(html), "버전 미고정"))
    def test_script_color_literal(self):
        for js in ("{color:'#1F3A5F'}", "{border:'1px solid #123456'}", "var c=`#abcdef`;"):
            self.assertTrue(has(style.script_style_violations(page(script=js)), "스크립트·도식 색 리터럴"), js)

    def test_query_selector_id_is_not_color(self):
        self.assertEqual(style.script_style_violations(page(script="document.querySelector('#abc')")), [])

    def test_mermaid_style_and_hex(self):
        body = '<pre class="mermaid">flowchart LR\n  A[가] --> B[나]\n  style A fill:#f9f</pre>'
        self.assertTrue(has(style.script_style_violations(page(body=body)), "스크립트·도식 색 리터럴"))
        body2 = '<pre class="mermaid">flowchart LR\n  A[가] --> B[나]\n  classDef hot stroke-width:2px</pre>'
        self.assertTrue(has(style.script_style_violations(page(body=body2)), "스크립트·도식 색 리터럴"))

    def test_mermaid_class_attr_order(self):
        body = '<pre id="m1" class="mermaid">flowchart LR\n  A[가]\n  style A fill:#f9f</pre>'
        self.assertTrue(has(style.script_style_violations(page(body=body)), "스크립트·도식 색 리터럴"))

    def test_plain_page_without_scripts_ok(self):
        self.assertEqual(style.script_style_violations(page(body="<p>가</p>")), [])


import check  # noqa: E402

OK_TITLE = "검토한 문서 12건 중 10건이 기준을 통과했다"


def sec_page(title, sec="검토 결과", extra=""):
    return page(body=f'<section class="page" id="p2"><p class="pno">2 / 2</p><p class="sec">{sec}</p>'
                     f'<h2>{title}</h2>{extra}<ul class="pts"><li>가</li></ul></section>')


class ConclusionTitle(unittest.TestCase):
    NAME = "결론 제목이 규격에 맞지 않음"

    def test_sentence_title_passes_both_rules(self):
        html = sec_page(OK_TITLE)
        self.assertEqual(style.conclusion_violations(html), [])
        self.assertEqual(style.label_violations(html), [])

    def test_forty_chars_pass_and_forty_one_fail(self):
        t40 = "가" * 38 + "했다"
        self.assertEqual(len(t40), 40)
        self.assertEqual(style.conclusion_violations(sec_page(t40)), [])
        fails = style.conclusion_violations(sec_page("가" + t40))
        self.assertTrue(has(fails, self.NAME))
        self.assertIn("41자", fails[0])

    def test_spaces_count(self):
        t = "가 " * 19 + "했다"  # 공백 포함 40자
        self.assertEqual(style.conclusion_violations(sec_page(t)), [])
        self.assertTrue(has(style.conclusion_violations(sec_page(" 나" + t)), self.NAME))

    def test_no_sentence_ending_fails(self):
        fails = style.conclusion_violations(sec_page("검토 결과 요약"))
        self.assertTrue(has(fails, self.NAME))
        self.assertIn("문장 어미", fails[0])

    def test_sec_with_extra_class_gets_noun_check(self):
        html = page(body=f'<section class="page" id="p2"><p class="pno">2 / 2</p><p class="sec lead">결과를 정리했다</p>'
                         f'<h2>{OK_TITLE}</h2></section>')
        self.assertTrue(has(style.label_violations(html), "라벨이 명사구가 아님"))

    def test_unclosed_p_before_h2_keeps_h2_direct_child(self):
        html = page(body=f'<section class="page" id="p2"><p class="pno">2 / 2<p class="sec">검토 결과<h2>{OK_TITLE}</h2></section>')
        self.assertEqual([t for _, t in style.conclusion_titles(html)], [OK_TITLE])
        self.assertEqual(style.conclusion_violations(html), [])
        self.assertEqual(style.label_violations(html), [])

    def test_sec_gets_noun_check(self):
        self.assertTrue(has(style.label_violations(sec_page(OK_TITLE, sec="결과를 정리했다")), "라벨이 명사구가 아님"))
        self.assertTrue(has(style.label_violations(sec_page(OK_TITLE, sec="가" * 19)), "라벨이 명사구가 아님"))
        self.assertEqual(style.label_violations(sec_page(OK_TITLE, sec="가" * 18)), [])

    def test_page_without_sec_keeps_noun_check(self):
        html = page(body=f'<section class="page" id="p2"><h2>{OK_TITLE}</h2></section>')
        self.assertEqual(style.conclusion_violations(html), [])
        self.assertTrue(has(style.label_violations(html), "라벨이 명사구가 아님"))

    def test_gist_and_list_pages_are_not_checked(self):
        html = page(body='<section class="page" id="p1"><div class="gist"><h2>요약</h2><ul><li>가</li></ul></div></section>'
                         '<section class="page list" id="p3"><h2>참고 자료</h2></section>')
        self.assertEqual(style.conclusion_violations(html), [])
        self.assertEqual(style.label_violations(html), [])

    def test_nested_h2_is_not_conclusion(self):
        html = sec_page(OK_TITLE, extra='<div class="gist"><h2>요약</h2></div>')
        self.assertEqual([t for _, t in style.conclusion_titles(html)], [OK_TITLE])
        self.assertEqual(style.label_violations(html), [])

    def test_inline_markup_in_title(self):
        html = sec_page("수익률이 <b>3.2%</b> 올라 기준 &lt;5%를 지켰다")
        self.assertEqual(style.conclusion_titles(html)[0][1], "수익률이 3.2% 올라 기준 <5%를 지켰다")
        self.assertEqual(style.conclusion_violations(html), [])

    def test_title_already_in_original_is_kept(self):
        long_t = "가" * 45
        new, old = sec_page(long_t), page(body=f"<section><h2>{long_t}</h2></section>")
        self.assertEqual(style.conclusion_violations(new, old), [])
        self.assertTrue(has(style.conclusion_violations(new, page(body="<h2>다른 제목</h2>")), self.NAME))
        self.assertEqual(check.run_rule(style.conclusion_violations, "old", new, old), [])

    def test_original_with_markup_is_kept(self):
        t = "기준 &lt; 5%를 <b>지켰" + "다" * 40 + "</b>"
        new, old = sec_page(t), page(body=f"<section><h2>{t}</h2></section>")
        self.assertEqual(style.conclusion_violations(new, old), [])

    def test_registered_as_old(self):
        self.assertIn((style.conclusion_violations, "old"), style.RULES)

TEMPLATE_PAGED = (Path(__file__).resolve().parent.parent / "template-paged.html").read_text(encoding="utf-8")


class PagedTemplate(unittest.TestCase):
    def test_title_frame(self):
        self.assertEqual(len(style.conclusion_titles(TEMPLATE_PAGED)), 1)
        self.assertEqual(style.conclusion_violations(TEMPLATE_PAGED), [])
        self.assertIn('<a href="#p2" class="core">2. 절 이름</a>', TEMPLATE_PAGED)
        self.assertIn('<p class="sec">절 이름</p>', TEMPLATE_PAGED)

    def test_c3_elements(self):
        for state, text in (("run", "실행으로 확인함"), ("infer", "추론함"), ("assume", "가정함")):
            self.assertIn(f'<span class="state" data-state="{state}">{text}</span>', TEMPLATE_PAGED)
            self.assertIn(f'.state[data-state="{state}"]', CSS)
        self.assertRegex(TEMPLATE_PAGED, r'<td class="[^"]*\bchg\b')
        self.assertIn('<div class="superseded"><b>대체됨</b>', TEMPLATE_PAGED)

    def test_hashchange_handler(self):
        self.assertIn("addEventListener('hashchange'", TEMPLATE_PAGED)


if __name__ == "__main__":
    unittest.main()
