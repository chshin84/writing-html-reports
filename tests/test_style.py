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
from measure import contrast, cvd_pairs, parse_color  # noqa: E402

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


if __name__ == "__main__":
    unittest.main()
