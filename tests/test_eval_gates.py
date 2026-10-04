"""C0 판정 항목 시험(합성 HTML, 외부 네트워크 없음). 실행: python -B -m unittest discover -s tests"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
import harness  # noqa: E402
import layout  # noqa: E402
import measure  # noqa: E402
import rules  # noqa: E402

ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
BASE_CSS = (ROOT / "report-base.css").read_text(encoding="utf-8")
PAGER = ('<nav class="pager"><button id="prev">이전</button><span class="cnt" id="cnt"></span>'
         '<button id="next">다음</button></nav>')
PAGE_JS = """addEventListener('DOMContentLoaded',function(){var P=[].slice.call(document.querySelectorAll('.page')),i=0;
function show(k){i=k;P.forEach(function(p,j){p.style.display=j===i?'':'none'});document.getElementById('cnt').textContent=(i+1)+' / '+P.length}
var m=/^#p(\\d+)$/.exec(location.hash);show(m?parseInt(m[1],10)-1:0)});"""


def doc(body, script="", css=""):
    return (f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>{BASE_CSS}{css}</style></head>'
            f'<body><main class="doc">{body}</main><script>{script}</script></body></html>')


class Pure(unittest.TestCase):
    def test_font_item(self):
        r = layout.font_item("svg-font-390", "motion", [{"px": 9.4, "text": "가"}, {"px": 14, "text": "나"}])
        self.assertEqual((r["status"], r["value"]["min_px"], r["value"]["small"]), ("fail", 9.4, 1))
        self.assertEqual(layout.font_item("svg-font-390", "motion", [])["status"], "pass")

    def test_contrast_text_unmeasurable_not_failed(self):
        recs = [{"text": "가", "px": 16, "weight": 400, "svg": False, "fg": "rgb(0, 0, 0)", "bg": "rgb(255, 255, 255)", "why": None},
                {"text": "나", "px": 16, "weight": 400, "svg": False, "fg": "rgb(0, 0, 0)", "bg": None, "why": "반투명이나 그림 바탕"}]
        r = layout.contrast_text_item(recs)
        self.assertEqual((r["status"], r["value"]["unmeasurable"]), ("pass", 1))

    def test_contrast_text_large_exception(self):
        grey = {"text": "가", "weight": 400, "svg": False, "fg": "#8a8f98", "bg": "#ffffff", "why": None}
        self.assertEqual(layout.contrast_text_item([dict(grey, px=16)])["status"], "fail")
        self.assertEqual(layout.contrast_text_item([dict(grey, px=24)])["status"], "pass")

    def test_contrast_graphic_bar(self):
        r = layout.contrast_graphic_item([{"kind": "fill", "name": "막대", "fg": "rgb(143, 163, 188)", "bg": "rgb(255, 255, 255)"}])
        self.assertEqual(r["status"], "fail")
        self.assertAlmostEqual(r["value"]["min_ratio"], 2.58, places=2)

    def test_cvd_item(self):
        self.assertEqual(layout.cvd_item({"s1": "#000000", "s2": "#ffffff"})["status"], "pass")
        self.assertEqual(layout.cvd_item({"s1": "#c83c3c", "s2": "#c83c3d"})["status"], "fail")

    def test_overflow_figure_table(self):
        lay = {"p1": {"width": 390, "scrollWidth": 420, "figures": [{"name": "svg", "box": [16, 0, 420, 10], "scroll": False}],
                      "cells": [{"w": 40, "text": "가"}, {"w": 75, "text": "나"}]}}
        self.assertEqual(layout.overflow_item(lay)["status"], "fail")
        self.assertEqual(layout.figure_item(lay)["status"], "fail")
        self.assertEqual(layout.table_item(lay)["status"], "fail")
        lay["p1"].update(scrollWidth=390, figures=[{"name": "svg", "box": [16, 0, 374, 10], "scroll": True}], cells=[{"w": 75, "text": "나"}])
        self.assertEqual([layout.overflow_item(lay)["status"], layout.figure_item(lay)["status"], layout.table_item(lay)["status"]], ["pass"] * 3)

    def test_page_number_item(self):
        self.assertEqual(layout.page_number_item({"p1": ["1 / 2", "1 / 2"], "p2": ["2 / 2"]}, 2)["status"], "fail")
        self.assertEqual(layout.page_number_item({"p1": ["1 / 2", "1/28"], "p2": ["2 / 2"]}, 2)["status"], "pass")


class Browser(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def items(self, html, wanted, dark=False):
        p = Path(self.tmp.name, "doc.html")
        p.write_text(html, encoding="utf-8")
        facts = measure.source_facts(html)
        with harness.Session(self.tmp.name) as s:
            if dark:
                return {i["id"]: i for i in layout.dark_items(s, "doc.html", facts, wanted, None)}
            return {i["id"]: i for i in layout.light_items(s, "doc.html", facts, wanted, None)}

    def test_svg_text_and_foreign_object_fonts_at_390(self):
        svg = ('<figure><svg viewBox="0 0 700 100" width="100%"><text x="0" y="20" font-size="14">글자</text>'
               '<foreignObject x="0" y="40" width="300" height="40"><div style="font-size:14px">이름표</div></foreignObject></svg></figure>')
        r = self.items(doc(svg), {"svg-font-390", "html-font-390"})
        self.assertEqual(r["svg-font-390"]["status"], "fail")
        self.assertEqual(r["svg-font-390"]["value"]["count"], 2)
        self.assertLess(r["svg-font-390"]["value"]["min_px"], 11)
        self.assertEqual(r["html-font-390"]["status"], "pass")

    def test_hidden_page_small_text_not_counted_and_page_number(self):
        svg = ('<figure><svg viewBox="0 0 700 100" width="100%"><text x="0" y="20" font-size="14">작은 도식 글자</text></svg></figure>')
        body = (PAGER + '<section class="page" id="p1"><p class="pno">1 / 2</p><p>본문</p></section>'
                f'<section class="page" id="p2"><p class="pno">2 / 2</p><p style="font-size:8px">작은 글</p>{svg}</section>')
        html = doc(body, PAGE_JS)
        r = self.items(html, {"html-font-390", "svg-font-390", "page-number", "hash-nav"})
        self.assertEqual(r["html-font-390"]["status"], "fail")  # 2페이지의 8px 글자는 2페이지를 열었을 때 한 번만 잡힌다
        self.assertEqual(r["html-font-390"]["value"]["small"], 1)
        self.assertEqual(r["svg-font-390"]["value"]["count"], 1)  # 1페이지를 열었을 때 숨은 SVG 글자(0px)는 세지 않는다
        self.assertGreater(r["svg-font-390"]["value"]["min_px"], 5)
        self.assertEqual(r["page-number"]["status"], "fail")  # 막대 .cnt와 .pno가 함께 보인다
        self.assertEqual(r["hash-nav"]["status"], "fail")  # hashchange 처리가 없다
        self.assertTrue(r["hash-nav"]["value"]["open_with_hash"])
        self.assertTrue(r["hash-nav"]["value"]["recorded_only"])

    def test_scroll_box_allows_wide_figure(self):
        wide = '<svg viewBox="0 0 800 100" width="800" height="100"><text x="0" y="50" font-size="14">넓은 도식</text></svg>'
        inside = self.items(doc(f'<div style="overflow-x:auto"><figure>{wide}</figure></div>'), {"figure-overflow-390"})
        outside = self.items(doc(f"<figure>{wide}</figure>"), {"figure-overflow-390"})
        hidden = self.items(doc(f'<div style="overflow-x:hidden"><figure>{wide}</figure></div>'), {"figure-overflow-390"})
        self.assertEqual(inside["figure-overflow-390"]["status"], "pass")
        self.assertEqual(outside["figure-overflow-390"]["status"], "fail")
        self.assertEqual(hidden["figure-overflow-390"]["status"], "fail")  # hidden은 스크롤 상자가 아니다

    def test_root_overflow_hidden_fails(self):
        r = self.items(doc('<div style="width:600px">넓은 상자</div>', css="body{overflow-x:hidden}"), {"overflow-390"})
        self.assertEqual(r["overflow-390"]["status"], "fail")

    def test_scroll_box_table_measured_and_overflow(self):
        narrow = "".join(f'<td style="width:40px;min-width:40px;max-width:40px">{i}</td>' for i in range(3))
        body = (f'<div class="tbl"><table style="table-layout:fixed;width:120px"><tr>{narrow}</tr></table></div>'
                '<div style="width:600px">넓은 상자</div>')
        r = self.items(doc(body), {"table-col-390", "overflow-390"})
        self.assertEqual(r["overflow-390"]["status"], "fail")
        self.assertEqual(r["table-col-390"]["status"], "fail")  # 스크롤 상자 안의 40px 셀도 측정한다
        self.assertEqual(r["table-col-390"]["value"]["cells"], 3)

    def test_svg_items_not_applicable_without_svg(self):
        r = self.items(doc("<p>글</p>"), {"svg-font-390", "figure-overflow-390", "page-number", "hash-nav"})
        self.assertEqual({k: v["status"] for k, v in r.items()}, dict.fromkeys(r, "n/a"))

    def test_dark_theme_tokens_change(self):
        r = self.items(doc("<p>글</p>"), {"cvd", "contrast-text"}, dark=True)
        self.assertEqual(r["cvd"]["value"]["tokens"]["s1"].lower(), "#9db7d8")
        self.assertEqual(r["contrast-text"]["status"], "pass")

    def test_svg_text_background_from_shape(self):
        def page(color):  # report-base.css의 'svg text{fill:var(--ink)}'보다 앞서게 style 속성으로 준다
            return doc('<figure><svg viewBox="0 0 300 100" width="300"><rect x="0" y="0" width="300" height="100" fill="#111418"/>'
                       f'<text x="10" y="50" font-size="16" style="fill:{color}">어두운 바탕 글자</text></svg></figure>')
        self.assertEqual(self.items(page("#3F4650"), {"contrast-text"})["contrast-text"]["status"], "fail")
        self.assertEqual(self.items(page("#FFFFFF"), {"contrast-text"})["contrast-text"]["status"], "pass")

    def test_translucent_text_blended_not_unmeasurable(self):
        r = self.items(doc('<p style="opacity:0.3">흐린 글자</p>'), {"contrast-text"})
        self.assertEqual(r["contrast-text"]["status"], "fail")
        self.assertEqual(r["contrast-text"]["value"]["unmeasurable"], 0)


class Rules(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.html = Path(self.tmp.name, "doc.html")

    def tearDown(self):
        self.tmp.cleanup()

    def test_rule_items_report_violations(self):
        self.html.write_text("<html><body><p>그냥 쓴다</p></body></html>", encoding="utf-8")
        r = {i["id"]: i for i in rules.rule_items(self.html, {"rules-all", "rules-layout", "rules-motion"})}
        self.assertEqual(r["rules-all"]["status"], "fail")
        self.assertTrue(any("그냥" in v for v in r["rules-all"]["detail"]))

    def test_base_checks_also_run(self):
        self.html.write_text("<html><body><p>글</p></body></html>", encoding="utf-8")
        base = Path(self.tmp.name, "base", "checks")
        shutil.copytree(ROOT / "checks", base)
        shutil.copy(ROOT / "금지어.md", base.parent / "금지어.md")
        (base / "anim.py").write_text((ROOT / "checks/anim.py").read_text(encoding="utf-8").replace(
            "RULES = [", "def always(html):\n    return ['기준 규칙 위반']\n\n\nRULES = [(always, 'plain'),"), encoding="utf-8")
        r = {i["id"]: i for i in rules.rule_items(self.html, {"rules-motion", "rules-all"}, base_checks=base)}
        self.assertEqual(r["rules-motion"]["status"], "fail")
        self.assertEqual(r["rules-motion"]["value"]["base"], 1)

    def test_base_checks_without_banned_file_stops(self):
        self.html.write_text("<html><body><p>글</p></body></html>", encoding="utf-8")
        base = Path(self.tmp.name, "nobanned", "checks")
        shutil.copytree(ROOT / "checks", base)
        with self.assertRaises(RuntimeError):
            rules.rule_items(self.html, {"rules-all"}, base_checks=base)


if __name__ == "__main__":
    unittest.main()
