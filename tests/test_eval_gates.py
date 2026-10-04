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

    def test_cvd_unreadable_token_fails(self):  # F6: 읽지 못한 토큰은 조용히 빠지지 않고 실패로 드러난다
        r = layout.cvd_item({"s1": "#000000", "s2": "#ffffff", "s3": "oklch(0.5 0.1 250)", "s4": ""})
        self.assertEqual(r["status"], "fail")
        self.assertEqual(r["detail"], {"unreadable": {"s3": "oklch(0.5 0.1 250)"}})

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

    def test_text_over_fully_transparent_shape_is_measured_on_page(self):
        svg = ('<figure><svg viewBox="0 0 700 100" width="100%"><rect x="0" y="0" width="700" height="100" fill="#111418" fill-opacity="0"/>'
               '<text x="10" y="50" font-size="30" style="fill:#3F4650">글자</text></svg></figure>')
        r = self.items(doc(svg), {"contrast-text"})
        self.assertEqual(r["contrast-text"]["status"], "pass")
        self.assertEqual(r["contrast-text"]["value"]["unmeasurable"], 0)

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

    def test_hidden_svg_icon_glyph_not_counted(self):  # F1: 투명도 0으로 숨긴 아이콘 글자는 측정하지 않는다
        svg = ('<figure><svg viewBox="0 0 300 100" width="300" height="100"><text x="10" y="30" font-size="14">보이는 글자</text>'
               '<g opacity="0" transform="scale(0.3)"><text x="10" y="60" font-size="11">₩</text></g></svg></figure>')
        r = self.items(doc(svg), {"svg-font-390"})
        self.assertEqual(r["svg-font-390"]["value"]["count"], 1)
        self.assertEqual(r["svg-font-390"]["status"], "pass")

    def test_modern_color_token_normalized(self):  # F6: oklch 토큰도 rgba로 정규화해 cvd에 넣는다
        r = self.items(doc("<p>글</p>", css=":root{--s1: oklch(0.5 0.1 250)}"), {"cvd"})
        self.assertTrue(r["cvd"]["value"]["tokens"]["s1"].startswith("rgba("), r["cvd"]["value"]["tokens"])

    def test_canvas_unsupported_token_not_carried_over(self):  # 캔버스가 받지 않는 표기가 앞 토큰의 색을 물려받지 않는다
        r = self.items(doc("<p>글</p>", css=":root{color-scheme:light;--s1: oklch(0.5 0.1 250);--s2: light-dark(#000000, #ffffff)}"), {"cvd"})
        self.assertEqual(r["cvd"]["value"]["tokens"]["s2"].replace(" ", ""), "rgb(0,0,0)", r["cvd"]["value"]["tokens"])

    def test_color_mix_text_measured(self):  # F6: color-mix로 만든 글자색도 측정한다
        r = self.items(doc('<p style="color:color-mix(in srgb, #000 80%, #fff)">섞은 색 글자</p>'), {"contrast-text"})
        self.assertEqual(r["contrast-text"]["value"]["unmeasurable"], 0)
        self.assertEqual(r["contrast-text"]["status"], "pass")

    def test_smooth_scroll_disabled_by_probe(self):  # F7: 부드러운 스크롤 문서에서도 scrollTo가 즉시 이동한다
        Path(self.tmp.name, "doc.html").write_text(doc('<div style="height:3000px">긴 글</div>', css="html{scroll-behavior:smooth}"),
                                                  encoding="utf-8")
        with harness.Session(self.tmp.name) as s:
            page, _ = s.open("doc.html", 0)
            try:
                self.assertEqual(page.evaluate("() => { scrollTo(0, 500); return scrollY; }"), 500)
            finally:
                page.close()

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


FAKE_RC = r"""
window.RC = { demo: function (fig, steps) {
  var cfg = window.FAKE, ends = [], t = 0;
  cfg.steps.forEach(function (s) { t += s.dur; ends.push(t); });
  var note = fig.querySelector('.rc-note'), nt = note && note.querySelector('span'), cap = document.createElement('p');
  cap.className = 'demo-cap'; fig.appendChild(cap);
  function render(x) {
    var i = 0; while (i < ends.length - 1 && x > ends[i] + 1e-9) i++;
    var s = cfg.steps[i], start = i ? ends[i - 1] : 0;
    cap.textContent = s.cap || '';
    if (nt) nt.textContent = x >= start + (s.textAt || 0) - 1e-9 ? (s.note || '') : '';
    if (note) { note.setAttribute('opacity', s.at ? 1 : 0); if (s.at) note.setAttribute('transform', 'translate(' + s.at[0] + ',' + s.at[1] + ')'); }
    [].forEach.call(fig.querySelectorAll('[data-rc-active]'), function (e) { e.removeAttribute('data-rc-active'); });
    if (s.active) document.getElementById(s.active).setAttribute('data-rc-active', '');
  }
  var tl = { _t: 0, labels: {}, duration: function () { return ends[ends.length - 1]; }, time: function () { return this._t; },
    seek: function (x) { if (typeof x === 'string') x = this.labels[x]; this._t = x; render(x); return this; } };
  ends.forEach(function (e, i) { tl.labels['e' + i] = e; });
  var raf = null;
  function run(to) { cancelAnimationFrame(raf); var t0 = performance.now(), from = tl._t;
    (function f() { var x = Math.min(to, from + (performance.now() - t0) / 1000); tl.seek(x); if (x < to) raf = requestAnimationFrame(f); })(); }
  var ctl = document.createElement('div'); ctl.className = 'demo-ctl';
  ['이전', '재생', '다음', '처음부터'].forEach(function (n) { var b = document.createElement('button'); b.textContent = n; ctl.appendChild(b); });
  fig.appendChild(ctl);
  var b = ctl.querySelectorAll('button'), cur = function () { var i = 0; while (i < ends.length - 1 && tl._t > ends[i] + 1e-9) i++; return i; };
  b[1].onclick = function () { run(tl.duration()); };
  b[2].onclick = function () { var i = tl._t < ends[0] - 1e-9 ? 0 : Math.min(ends.length - 1, cur() + 1); run(ends[i]); };
  b[3].onclick = function () { cancelAnimationFrame(raf); tl.seek(cfg.startAt); };
  tl.seek(cfg.startAt);
  fig._rcTl = tl; fig.dataset.rcReady = '1';
} };
"""
STAGE = ('<figure id="d"><svg viewBox="0 0 600 300" width="600" height="300">'
         '<rect id="n1" x="20" y="20" width="120" height="40" fill="#fff" stroke="#111"/>'
         '<rect id="n2" x="20" y="200" width="120" height="40" fill="#fff" stroke="#111"/>'
         '<g class="rc-note" opacity="0"><rect width="160" height="40" fill="#fff"/>'
         '<foreignObject width="160" height="40"><div style="font-size:13px"><span></span></div></foreignObject></g>'
         '</svg><p class="src">자료</p></figure>')


def fake_doc(cfg, extra_body=""):
    return doc(STAGE + extra_body, "window.FAKE = " + json.dumps(cfg, ensure_ascii=False) + ";" + FAKE_RC
               + "RC.demo(document.getElementById('d'), []);")


GOOD = {"startAt": 0, "steps": [
    {"dur": 3.5, "textAt": 0.3, "cap": "", "note": "첫 단계 글", "at": [160, 20], "active": "n1"},
    {"dur": 3.5, "textAt": 0.3, "cap": "", "note": "둘째 글", "at": [160, 200], "active": "n2"}]}


class Motion(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def items(self, html, wanted, mode=None):
        import motion
        Path(self.tmp.name, "doc.html").write_text(html, encoding="utf-8")
        facts = measure.source_facts(html)
        with harness.Session(self.tmp.name) as s:
            return {i["id"]: i for i in motion.motion_items(s, "doc.html", facts, wanted, mode)}

    def test_good_fake_passes(self):
        r = self.items(fake_doc(GOOD), {"dwell", "step1", "note-near", "active-visible"})
        self.assertEqual({k: v["status"] for k, v in r.items()}, dict.fromkeys(r, "pass"), json.dumps(r, ensure_ascii=False)[:800])

    def test_short_dwell_and_skipped_step1_fail(self):
        cfg = {"startAt": 0.32, "steps": [dict(s, dur=0.32, textAt=0.0) for s in GOOD["steps"]]}
        cfg["steps"][0]["cap"], cfg["steps"][1]["cap"] = "시나리오 가 · 후보: 실행할지 정합니다.", "시나리오 가 · 요청: 직접 요청이 있습니다."
        r = self.items(fake_doc(cfg), {"dwell", "step1"})
        self.assertEqual(r["dwell"]["status"], "fail")
        self.assertEqual(r["step1"]["status"], "fail")

    def test_note_missing_or_far_fails(self):
        cfg = json.loads(json.dumps(GOOD))
        cfg["steps"][0]["at"] = None
        cfg["steps"][1]["at"] = [200, 200]  # 현재 노드 오른쪽 끝(140)에서 60px
        r = self.items(fake_doc(cfg), {"note-near"})
        self.assertEqual(r["note-near"]["status"], "fail")
        steps = r["note-near"]["detail"]["d"]
        self.assertEqual(steps[0]["why"], "보이는 설명 상자 없음")
        self.assertEqual(steps[1]["distance"], 60)

    def test_active_offscreen_fails(self):
        r = self.items(fake_doc(GOOD, '<div style="height:10px"></div>').replace('height="300"', 'height="300" style="margin-top:0"')
                       .replace('y="200" width="120"', 'y="900" width="120"').replace('viewBox="0 0 600 300"', 'viewBox="0 0 600 1000"')
                       .replace('height="300"', 'height="1000"').replace("[160, 200]", "[160, 900]"), {"active-visible"})
        self.assertEqual(r["active-visible"]["status"], "fail")

    def test_no_active_attribute_is_unmeasurable(self):
        cfg = json.loads(json.dumps(GOOD))
        for s in cfg["steps"]:
            s["active"] = None
        r = self.items(fake_doc(cfg), {"note-near", "active-visible"})
        self.assertEqual({k: v["status"] for k, v in r.items()}, {"note-near": "unmeasurable", "active-visible": "unmeasurable"})

    def test_static_fallback_unmeasurable_and_no_demo_na(self):
        engine = (ROOT / "report-charts.js").read_text(encoding="utf-8")
        html = doc('<figure id="d"><svg></svg><p class="src">자료</p></figure>',
                   engine + "\nRC.demo(document.getElementById('d'), [{name: '가', text: '나', play: function () {}}]);")
        r = self.items(html, {"dwell", "step1", "note-near"})
        self.assertEqual({v["status"] for v in r.values()}, {"unmeasurable"})
        r = self.items(doc("<p>글</p>"), {"dwell", "step1"})
        self.assertEqual({v["status"] for v in r.values()}, {"n/a"})

    def test_step_mode(self):
        cfg = json.loads(json.dumps(GOOD))
        r = self.items(fake_doc(cfg), {"step-anim", "dwell"}, mode="step")
        self.assertEqual(r["dwell"]["status"], "n/a")
        self.assertEqual(r["step-anim"]["status"], "fail")  # 가짜의 '다음' 연출이 3.5초라 2.5초를 넘는다
        self.assertTrue(r["step-anim"]["value"]["d"]["held"])


class MotionPure(unittest.TestCase):
    def test_reopen_not_ready_is_unmeasurable(self):  # F2: 다시 연 탭이 준비되지 않으면 그 figure의 항목은 측정 불가다
        import motion
        want = ["dwell", "step-anim", "step1", "note-near", "active-visible"]
        rows = motion.figure_rows("d", "auto", want, lambda script, arg: None)
        self.assertEqual(rows["step-anim"][1], "n/a")
        for i in ("dwell", "step1", "note-near", "active-visible"):
            self.assertEqual(rows[i], ("d", "unmeasurable", None, "다시 연 탭에서 data-rc-ready가 오지 않았다"), i)

    def test_judge_step1_uses_timeline(self):  # F3: 벽시계가 0.3초여도 타임라인 거리가 0.1초면 실패다
        import motion
        r = {"initial": 0, "e0": 0.1, "reached": True, "seconds": 0.3, "timeScale": 1}
        self.assertFalse(motion.judge_step1(r))
        self.assertTrue(motion.judge_step1(dict(r, e0=0.5)))
        self.assertFalse(motion.judge_step1(dict(r, e0=0.5, timeScale=4)))  # 4배속이면 실제 0.125초다

    def test_judge_step_anim_uses_timeline(self):  # F3: 단계 길이는 타임라인 기준이고, '다음'을 못 누르면 실패다
        import motion
        ok = {"lengths": [1.0, 1.0], "deltas": [1.0, 1.0], "held": True, "steps": 2, "timeScale": 1}
        self.assertTrue(motion.judge_step_anim(ok)[0])
        self.assertFalse(motion.judge_step_anim(dict(ok, deltas=[3.5, 1.0]))[0])
        self.assertFalse(motion.judge_step_anim(dict(ok, deltas=[0.1, 1.0]))[0])  # 벽시계 1.0초여도 타임라인 0.1초면 실패
        stuck = motion.judge_step_anim({"lengths": [], "deltas": [], "held": None, "steps": 3, "timeScale": 1})
        self.assertEqual(stuck, (False, "'다음'을 누를 수 없었다"))


class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def run_gates(self, *args):
        return subprocess.run([sys.executable, "-B", str(ROOT / "eval/gates.py"), *map(str, args)],
                              capture_output=True, text=True, encoding="utf-8", env=ENV)

    def test_env_fail_in_one_file_still_measures_other(self):
        good = Path(self.tmp.name, "good.html")
        bad = Path(self.tmp.name, "bad.html")
        good.write_text(doc("<p>글</p>"), encoding="utf-8")
        bad.write_text(doc('<script src="http://127.0.0.1:9/x.js"></script><p>글</p>'), encoding="utf-8")
        out = Path(self.tmp.name, "r.json")
        r = self.run_gates(good, bad, "--only", "layout", "--out", out)
        self.assertEqual(r.returncode, 2, r.stderr)
        recs = json.loads(out.read_text(encoding="utf-8"))
        envs = {(Path(x["file"]).name, x["theme"]): x["env"] for x in recs}
        self.assertEqual(envs[("good.html", "light")], "ok")
        self.assertEqual(envs[("bad.html", "light")], "env-fail")
        self.assertTrue(all(i["target"] == "layout" for x in recs for i in x["items"]))

    def test_record_shape_and_exit_code(self):
        p = Path(self.tmp.name, "a.html")
        p.write_text(doc("<p>글</p>"), encoding="utf-8")
        r = self.run_gates(p, "--mode", "auto")
        recs = json.loads(r.stdout)
        self.assertEqual([(x["mode"], x["theme"]) for x in recs], [("auto", "light"), ("auto", "dark")])
        light = recs[0]
        self.assertEqual([i["id"] for i in light["items"]], measure.ORDER)
        self.assertEqual({i["id"] for i in recs[1]["items"]}, measure.THEMED)
        for i in light["items"]:
            self.assertIn(i["status"], ("pass", "fail", "unmeasurable", "n/a"))
        import gates
        self.assertEqual(r.returncode, gates.exit_code(recs))

    def test_missing_file_is_error_record(self):  # F4: 문서 열기 전 예외도 측정기 오류(3)로 남긴다
        r = self.run_gates(Path(self.tmp.name, "없는 문서.html"))
        self.assertEqual(r.returncode, 3, r.stderr)
        recs = json.loads(r.stdout)
        self.assertEqual([(Path(x["file"]).name, x["env"], x["theme"], x["items"]) for x in recs],
                         [("없는 문서.html", "error", "light", [])])
        self.assertIn("FileNotFoundError", recs[0]["error"])

    def test_exit_code_rules(self):
        import gates
        ok = {"env": "ok", "items": [{"status": "pass", "value": {}}], "load_errors": [], "render_fail": []}
        hn = dict(ok, items=[{"status": "fail", "value": {"recorded_only": True}}])
        self.assertEqual(gates.exit_code([ok]), 0)
        self.assertEqual(gates.exit_code([hn]), 0)  # 기록만 하는 hash-nav 실패는 빼고 센다
        self.assertEqual(gates.exit_code([dict(ok, render_fail=["pre: 시각화를 불러오지 못했습니다"])]), 1)
        self.assertEqual(gates.exit_code([dict(ok, env="error", items=[]), dict(ok, env="env-fail", items=[])]), 2)
        self.assertEqual(gates.exit_code([dict(ok, env="error", items=[])]), 3)


if __name__ == "__main__":
    unittest.main()
