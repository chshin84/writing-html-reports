"""check.py 규칙 시험. 실행: python -B -m unittest discover -s tests -v (스킬 폴더에서)"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
import check  # noqa: E402

PINNED = {"echarts": "6.1.0", "mermaid": "11.17.2", "gsap": "3.15.0"}


def cdn(lib, ver=None):
    return f'<script src="https://cdn.jsdelivr.net/npm/{lib}@{ver or PINNED[lib]}/dist/{lib}.min.js"></script>'


def page(style="", head="", body="", script=""):
    return ('<!doctype html><html lang="ko"><head><title>시험 문서</title>'
            f"<style>{style}</style>{head}</head><body><main class=\"doc\">{body}</main>"
            f"<script>{script}</script></body></html>")


def has(fails, name):
    return any(f.startswith(name) for f in fails)


class Movement(unittest.TestCase):
    def test_animation_false_in_script_is_not_movement(self):
        self.assertFalse(has(check.style_violations(page(script="RC.chart(b,{animation:false})")), "움직임"))

    def test_css_transition_is_movement(self):
        self.assertTrue(has(check.style_violations(page(style="a{transition:opacity 1s}")), "움직임"))

    def test_inline_style_animation_is_movement(self):
        self.assertTrue(has(check.style_violations(page(body='<p style="animation:x 1s">가</p>')), "움직임"))

    def test_intersection_observer_is_movement(self):
        self.assertTrue(has(check.style_violations(page(script="new IntersectionObserver(f)")), "움직임"))


class Scripts(unittest.TestCase):
    def test_managed_block_is_excluded(self):
        block = ("<script>/* BEGIN report-charts echarts@6.1.0 mermaid@11.17.2 gsap@3.15.0 */\n"
                 "gsap.to(x,{repeat:-1}); var c='#123456';\n/* END report-charts */</script>")
        self.assertEqual(check.script_violations(page(head=block)), [])

    def test_chart_animation_true(self):
        self.assertTrue(has(check.script_violations(page(script="RC.chart(b,{animation: true})")), "차트 애니메이션"))

    def test_chart_animation_false_ok(self):
        self.assertEqual(check.script_violations(page(script="RC.chart(b,{animation: false})")), [])

    def test_disallowed_src(self):
        html = page(head='<script src="https://unpkg.com/echarts@6.1.0/dist/echarts.min.js"></script>')
        self.assertTrue(has(check.script_violations(html), "허용 밖 스크립트"))

    def test_unpinned_src(self):
        self.assertTrue(has(check.script_violations(page(head=cdn("echarts", "6"))), "버전 미고정"))

    def test_pinned_src_ok(self):
        head = cdn("echarts") + cdn("mermaid") + cdn("gsap")
        self.assertEqual(check.script_violations(page(head=head)), [])

    def test_unpinned_module_import(self):
        html = page(head="<script type=\"module\">import mermaid from "
                         "'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs'</script>")
        self.assertTrue(has(check.script_violations(html), "버전 미고정"))

    def test_gsap_direct_call(self):
        self.assertTrue(has(check.script_violations(page(script="gsap.to(a,{x:1})")), "GSAP 직접 호출"))

    def test_repeat_with_spaces(self):
        self.assertTrue(has(check.script_violations(page(script="tl.to(a,{repeat : -1})")), "GSAP 직접 호출"))

    def test_timeline_calls_ok(self):
        self.assertEqual(check.script_violations(page(script="tl.to(a,{x:1}).set(b,{y:0})")), [])

    def test_chart_decoration(self):
        for js in ("{shadowBlur:4}", "{borderRadius:4}", "{borderRadius:[0,4,4,0]}"):
            self.assertTrue(has(check.script_violations(page(script=js)), "차트 장식"), js)
        self.assertEqual(check.script_violations(page(script="{borderRadius:2}")), [])
        self.assertEqual(check.script_violations(page(script="{shadowBlur: 0}")), [])

    def test_script_color_literal(self):
        for js in ("{color:'#1F3A5F'}", "{border:'1px solid #123456'}", "var c=`#abcdef`;"):
            self.assertTrue(has(check.script_violations(page(script=js)), "스크립트·도식 색 리터럴"), js)

    def test_query_selector_id_is_not_color(self):
        self.assertEqual(check.script_violations(page(script="document.querySelector('#abc')")), [])

    def test_mermaid_style_and_hex(self):
        body = '<pre class="mermaid">flowchart LR\n  A[가] --> B[나]\n  style A fill:#f9f</pre>'
        self.assertTrue(has(check.script_violations(page(body=body)), "스크립트·도식 색 리터럴"))
        body2 = '<pre class="mermaid">flowchart LR\n  A[가] --> B[나]\n  classDef hot stroke-width:2px</pre>'
        self.assertTrue(has(check.script_violations(page(body=body2)), "스크립트·도식 색 리터럴"))

    def test_mermaid_class_attr_order(self):
        body = '<pre id="m1" class="mermaid">flowchart LR\n  A[가]\n  style A fill:#f9f</pre>'
        self.assertTrue(has(check.script_violations(page(body=body)), "스크립트·도식 색 리터럴"))

    def test_plain_page_without_scripts_ok(self):
        self.assertEqual(check.script_violations(page(body="<p>가</p>")), [])


class Banned(unittest.TestCase):
    def test_banned_word_in_script_string(self):
        fails = check.banned_violations(page(script="var s={name:'부분 합계'};"))
        self.assertTrue(any("'부분'" in f for f in fails))

    def test_banned_word_in_managed_block_is_ignored(self):
        block = "<script>/* BEGIN report-charts x */\nvar s='부분';\n/* END report-charts */</script>"
        self.assertEqual(check.banned_violations(page(head=block)), [])


ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def run_check(*paths):
    return subprocess.run([sys.executable, "-B", str(ROOT / "check.py"), *map(str, paths)],
                          capture_output=True, text=True, encoding="utf-8", env=ENV)


class Templates(unittest.TestCase):
    def test_templates_pass(self):
        for name in ("template.html", "template-paged.html"):
            r = run_check(ROOT / name)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class DemoCount(unittest.TestCase):
    def run_page(self, n):
        body = "".join(f'<figure id="d{i}" data-anim="구조"><svg></svg></figure>' for i in range(n))
        script = "".join(f"RC.demo(document.getElementById('d{i}'),[]);" for i in range(n))
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "doc.html"
            f.write_text(page(body=body, script=script), encoding="utf-8")
            return run_check(f)

    def test_four_demos_violation(self):
        r = self.run_page(4)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("동작 예시 4개", r.stdout)

    def test_three_demos_ok(self):
        self.assertEqual(self.run_page(3).returncode, 0)


def toc(*classes):
    links = " · ".join(f'<a href="#p{i}" class="{c}">{i}. 절</a>' for i, c in enumerate(classes, 1))
    return page(body=f'<p class="toc">{links}</p>')


def paged(gist, marks, titles=("요약", "구조 A", "구조 B", "구조 C")):
    toc = " · ".join(f'<a href="#p{i}" class="{marks.get(i, "")}">{i}. {t}</a>' for i, t in enumerate(titles, 1))
    secs = [f'<section class="page" id="p1"><h2>{titles[0]}</h2><div class="gist"><ul>{gist}</ul></div></section>']
    secs += [f'<section class="page" id="p{i}"><h2>{t}</h2><table><tr><td>가</td></tr></table></section>'
             for i, t in enumerate(titles[1:], 2)]
    return page(body=f'<p class="toc">{toc}</p>' + "".join(secs))


class Scores(unittest.TestCase):
    GIST = '<li data-src="p2">가</li><li data-src="p2 p3">나</li><li data-src="p3">다</li><li data-src="p3 p4">라</li>'

    def test_expected_marks(self):
        rows = {x["id"]: x for x in check.page_scores(paged(self.GIST, {}))}
        self.assertTrue(rows["p1"]["excluded"])
        self.assertEqual((rows["p2"]["N"], rows["p2"]["R"], rows["p2"]["expect"]), (1, 2, "key"))
        self.assertEqual((rows["p3"]["N"], rows["p3"]["R"], rows["p3"]["expect"]), (1, 3, "core"))
        self.assertEqual((rows["p4"]["N"], rows["p4"]["expect"]), (0, ""))

    def test_matching_marks_ok(self):
        self.assertEqual(check.score_violations(paged(self.GIST, {2: "key", 3: "core"})), [])

    def test_mismatch_violation(self):
        fails = check.score_violations(paged(self.GIST, {2: "core"}))
        self.assertTrue(any(f.startswith("p2 표시 ★") for f in fails))
        self.assertTrue(any(f.startswith("p3 표시 -") for f in fails))

    def test_missing_data_src(self):
        fails = check.score_violations(paged('<li>근거 없음</li>', {}))
        self.assertTrue(any("data-src" in f for f in fails))

    def test_branch_breaks_tie(self):
        html = paged('<li data-src="p2">가</li><li data-src="p3">나</li>', {}).replace(
            '<section class="page" id="p3"><h2>구조 B</h2>', '<section class="page" id="p3"><h2>구조 B</h2><svg><polygon points="0,0 1,1"/></svg>')
        rows = {x["id"]: x for x in check.page_scores(html)}
        self.assertEqual((rows["p3"]["B"], rows["p3"]["expect"], rows["p2"]["expect"]), (1, "core", "key"))

    def test_key_needs_half_of_core(self):
        gist = '<li data-src="p2">가</li>' + '<li data-src="p3">나</li>' * 3
        rows = {x["id"]: x for x in check.page_scores(paged(gist, {}))}
        self.assertEqual((rows["p3"]["expect"], rows["p2"]["expect"]), ("core", ""))

    def test_conclusion_and_appendix_excluded(self):
        rows = check.page_scores(paged('<li data-src="p2">가</li><li data-src="p3">나</li>', {},
                                       ("요약", "결론", "부록 A", "구조")))
        self.assertTrue(all(x["expect"] == "" for x in rows))


def anim_page(sections, typ="구조"):
    """sections: [(section 클래스, 페이지 id, figure id 목록)]"""
    body = "".join(
        f'<section class="{c}" id="{p}"><h2>절 {p}</h2>'
        + "".join(f'<figure id="{f}" data-anim="{typ}"><svg></svg></figure>' for f in figs)
        + "</section>" for c, p, figs in sections)
    script = "".join(f"RC.demo(document.getElementById('{f}'),[]);" for _, _, figs in sections for f in figs)
    return page(body=body, script=script)


class Anim(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(check.anim_violations(anim_page([("page core", "p2", ["d1"])])), [])

    def test_missing_type(self):
        html = page(body='<figure id="d1"><svg></svg></figure>', script="RC.demo(document.getElementById('d1'),[]);")
        self.assertTrue(any("유형 누락" in f for f in check.anim_violations(html)))

    def test_waiting_type(self):
        fails = check.anim_violations(anim_page([("page core", "p2", ["d1"])], typ="선별"))
        self.assertTrue(any("견본 대기" in f for f in fails))

    def test_unknown_type(self):
        fails = check.anim_violations(anim_page([("page core", "p2", ["d1"])], typ="회전"))
        self.assertTrue(any("목록에 없다" in f for f in fails))

    def test_two_on_one_page(self):
        fails = check.anim_violations(anim_page([("page core", "p2", ["d1", "d2"])]))
        self.assertTrue(any("페이지당 1개" in f for f in fails))

    def test_unstarred_page(self):
        fails = check.anim_violations(anim_page([("page", "p2", ["d1"])]))
        self.assertTrue(any("별 표시 없는 페이지" in f for f in fails))

    def test_demo_without_figure_id(self):
        fails = check.anim_violations(page(body="<p>가</p>", script="RC.demo(a,[]);"))
        self.assertTrue(any("getElementById" in f for f in fails))


class Stars(unittest.TestCase):
    def test_one_core_two_key_ok(self):
        self.assertEqual(check.star_violations(toc("core", "key", "key", "")), [])

    def test_two_core(self):
        self.assertTrue(any("★ 핵심 페이지 2개" in f for f in check.star_violations(toc("core", "core"))))

    def test_three_key(self):
        fails = check.star_violations(toc("core", "key", "key", "key"))
        self.assertTrue(any("☆ 중요 페이지 3개" in f for f in fails))
        self.assertTrue(any("별 표시 페이지 4개" in f for f in fails))

    def test_key_without_core(self):
        self.assertTrue(any("★이 없다" in f for f in check.star_violations(toc("key"))))


class Original(unittest.TestCase):
    def test_script_violation_already_in_original_is_note_only(self):
        with tempfile.TemporaryDirectory() as d:
            html = page(body="<p>가</p>", script="gsap.to(a,{x:1})")
            new, old = Path(d) / "new.html", Path(d) / "old.html"
            new.write_text(html, encoding="utf-8")
            old.write_text(html, encoding="utf-8")
            r = run_check(new, old)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("참고: 원본에 있던 스크립트 위반", r.stdout)

    def test_anim_violation_already_in_original_is_note_only(self):
        with tempfile.TemporaryDirectory() as d:
            html = anim_page([("page", "p2", ["d1"])])
            new, old = Path(d) / "new.html", Path(d) / "old.html"
            new.write_text(html, encoding="utf-8")
            old.write_text(html, encoding="utf-8")
            r = run_check(new, old)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("참고: 원본에 있던 애니메이션 위반", r.stdout)

    def test_new_anim_violation_counts_even_with_original(self):
        with tempfile.TemporaryDirectory() as d:
            new, old = Path(d) / "new.html", Path(d) / "old.html"
            new.write_text(anim_page([("page", "p2", ["d1"]), ("page", "p3", ["d2"])]), encoding="utf-8")
            old.write_text(anim_page([("page", "p2", ["d1"])]), encoding="utf-8")
            r = run_check(new, old)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("p3 별 표시 없는 페이지", r.stdout)


if __name__ == "__main__":
    unittest.main()
