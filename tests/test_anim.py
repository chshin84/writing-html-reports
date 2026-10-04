"""애니메이션·차트 스크립트 규칙 시험(checks/anim.py). C1 소유."""
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from checks import anim  # noqa: E402
from helpers import ROOT, anim_page, has, page  # noqa: E402
import json
import tempfile

sys.path.insert(0, str(ROOT / "eval"))
import harness  # noqa: E402  (C0 소유, 읽기 전용으로 가져다 쓴다)
import measure  # noqa: E402
from helpers import cdn  # noqa: E402

CSS = (ROOT / "report-base.css").read_text(encoding="utf-8") + (ROOT / "report-demo.css").read_text(encoding="utf-8")
PAGER_JS = """document.documentElement.classList.add('js');
addEventListener('DOMContentLoaded',function(){var P=[].slice.call(document.querySelectorAll('.page'));
function show(k){P.forEach(function(p,j){p.classList.toggle('on',j===k)})}
window.showPage=show;var m=/^#p(\\d+)$/.exec(location.hash);show(m?parseInt(m[1],10)-1:0)});"""


def engine_doc(body, script, paged=False):
    js = (ROOT / "report-charts.js").read_text(encoding="utf-8") + "\n" + (ROOT / "report-peeps.js").read_text(encoding="utf-8")
    js = f"/* BEGIN report-charts 시험 */\n{js}\n/* END report-charts */"  # 엔진 주석의 'RC.demo('를 호출 수에서 빼려고 관리 블록으로 감싼다
    pager = f"<script>{PAGER_JS}</script>" if paged else ""
    return (f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>엔진 시험</title><style>{CSS}</style>'
            f'{cdn("echarts")}{cdn("mermaid")}{cdn("gsap")}<script>{js}</script>{pager}</head>'
            f'<body><main class="doc{" paged" if paged else ""}">{body}</main><script>{script}</script></body></html>')


MMD = """<figure id="d1" data-anim="구조"><figcaption><span class="t">흐름</span></figcaption>
<pre class="mermaid">flowchart TD
  A[주문 접수] --> B{한도 검증}
  B -->|예| C[체결]
  B -->|아니오| D[거부]</pre><p class="src">자료: 시험</p></figure>"""


def mmd_steps(spec):
    """spec: [(단계 이름, 문장, 노드, 색 또는 None)] → RC.demo 호출문."""
    items = ",".join(
        "{name:%s,text:%s,play:function(tl,$){RC.fx.mark(tl,$(%s)%s);}}"
        % (json.dumps(n, ensure_ascii=False), json.dumps(t, ensure_ascii=False), json.dumps(node),
           f",{json.dumps(c)}" if c else "") for n, t, node, c in spec)
    return f"RC.demo(document.getElementById('d1'),[{items}]);"


FLOW = [("시나리오 A · 접수", "주문을 접수합니다.", "A", None), ("시나리오 A · 검증", "한도 이내입니다.", "B", None),
        ("시나리오 A · 체결", "주문을 체결합니다.", "C", None)]


class EngineCase(unittest.TestCase):
    """합성 문서를 로컬 서버로 열어 엔진 동작을 본다. CDN을 열지 못하면 건너뛴다."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.sess = harness.Session(cls.tmp.name).__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.sess.__exit__(None, None, None)
        cls.tmp.cleanup()

    def open_file(self, name, html, mode=None, width=1280, page=None):
        Path(self.tmp.name, name).write_text(html, encoding="utf-8")
        try:
            p, ok = self.sess.open(name, measure.source_facts(html)["demo_calls"], width, "light", mode, page)
        except harness.EnvFail as e:
            self.skipTest(f"문서를 열지 못했다(CDN): {e}")
        self.addCleanup(p.close)
        self.assertTrue(ok, "data-rc-ready가 오지 않았다")
        return p

    def open(self, body, script, mode=None, width=1280, page=None, paged=False):
        return self.open_file(self.id().split(".")[-1] + ".html", engine_doc(body, script, paged), mode, width, page)

    def js(self, p, expr, arg=None):
        return p.evaluate(expr, arg)


class ScriptMotion(unittest.TestCase):
    def test_chart_animation_true(self):
        self.assertTrue(has(anim.script_motion_violations(page(script="RC.chart(b,{animation: true})")), "차트 애니메이션"))

    def test_chart_animation_false_ok(self):
        self.assertEqual(anim.script_motion_violations(page(script="RC.chart(b,{animation: false})")), [])

    def test_gsap_direct_call(self):
        self.assertTrue(has(anim.script_motion_violations(page(script="gsap.to(a,{x:1})")), "GSAP 직접 호출"))

    def test_repeat_with_spaces(self):
        self.assertTrue(has(anim.script_motion_violations(page(script="tl.to(a,{repeat : -1})")), "GSAP 직접 호출"))

    def test_timeline_calls_ok(self):
        self.assertEqual(anim.script_motion_violations(page(script="tl.to(a,{x:1}).set(b,{y:0})")), [])

    def test_chart_decoration(self):
        for js in ("{shadowBlur:4}", "{borderRadius:4}", "{borderRadius:[0,4,4,0]}"):
            self.assertTrue(has(anim.script_motion_violations(page(script=js)), "차트 장식"), js)
        self.assertEqual(anim.script_motion_violations(page(script="{borderRadius:2}")), [])
        self.assertEqual(anim.script_motion_violations(page(script="{shadowBlur: 0}")), [])



class Anim(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(anim.anim_violations(anim_page([("page core", "p2", ["d1"])])), [])

    def test_missing_type(self):
        html = page(body='<figure id="d1"><svg></svg></figure>', script="RC.demo(document.getElementById('d1'),[]);")
        self.assertTrue(any("유형 누락" in f for f in anim.anim_violations(html)))

    def test_waiting_type(self):
        fails = anim.anim_violations(anim_page([("page core", "p2", ["d1"])], typ="선별"))
        self.assertTrue(any("견본 대기" in f for f in fails))

    def test_unknown_type(self):
        fails = anim.anim_violations(anim_page([("page core", "p2", ["d1"])], typ="회전"))
        self.assertTrue(any("목록에 없다" in f for f in fails))

    def test_two_on_one_page(self):
        fails = anim.anim_violations(anim_page([("page core", "p2", ["d1", "d2"])]))
        self.assertTrue(any("페이지당 1개" in f for f in fails))

    def test_unstarred_page(self):
        fails = anim.anim_violations(anim_page([("page", "p2", ["d1"])]))
        self.assertTrue(any("별 표시 없는 페이지" in f for f in fails))

    def test_demo_without_figure_id(self):
        fails = anim.anim_violations(page(body="<p>가</p>", script="RC.demo(a,[]);"))
        self.assertTrue(any("getElementById" in f for f in fails))


def note_demo(fid, *calls):
    """calls: 단계마다 설명 상자를 옮기는 호출문 → RC.demo 호출문."""
    items = ",".join("{name:'단계%d',text:'설명입니다.',play:function(tl,$){%s}}" % (i, c) for i, c in enumerate(calls))
    return f"RC.demo(document.getElementById('{fid}'),[{items}]);"


class NoteFixed(unittest.TestCase):  # 설명 상자 위치: 모든 단계에서 같은 좌표에 둔 작성자 상자
    BODY = '<figure id="d1" data-anim="구조"><svg></svg></figure><figure id="d2" data-anim="구조"><svg></svg></figure>'

    def fails(self, script):
        return anim.note_fixed_violations(page(body=self.BODY, script="var nt=RC.note(st,190,64);" + script))

    def test_same_place_every_step(self):
        fails = self.fails(note_demo("d1", "fx.pair(tl, nt, ic.guide, 198, 18, '가', 0.4);",
                                     "fx.say(tl, nt, 198, 18, '나', 0.4);", "RC.fx.pair(tl,nt,[ic.a, ic.b],198,18,'다',0.4);"))
        self.assertEqual(len(fails), 1)
        self.assertTrue(has(fails, "설명 상자 고정 위치"))
        self.assertIn("d1", fails[0])

    def test_moving_note_ok(self):  # 단계마다 현재 노드 옆으로 옮기면 위반이 아니다. 같은 좌표가 일부 단계에만 있어도 된다
        self.assertEqual(self.fails(note_demo("d1", "fx.pair(tl, nt, ic.a, 108, 78, '가', 0.5);",
                                              "fx.pair(tl, nt, [ic.who, ic.ask], 270, 78, '나', 0.4);",
                                              "fx.pair(tl, nt, ic.a, 108, 78, '다', 0.5);")), [])

    def test_same_place_on_some_steps_ok(self):  # 상자를 쓴 단계만 같은 좌표이고 상자 없는 단계가 있으면 고정으로 보지 않는다
        self.assertEqual(self.fails(note_demo("d1", "fx.say(tl, nt, 198, 18, '가', 0.4);", "fx.say(tl, nt, 198, 18, '나', 0.4);",
                                              "tl.to($('a'),{x:1,duration:0.3});")), [])

    def test_single_call_or_variables_ok(self):  # 호출이 하나뿐이거나 좌표가 변수이면 판정하지 않는다
        self.assertEqual(self.fails(note_demo("d1", "fx.say(tl, nt, 198, 18, '가', 0.4);")), [])
        self.assertEqual(self.fails(note_demo("d1", "fx.say(tl, nt, x, y, '가', 0.4);", "fx.say(tl, nt, x, y, '나', 0.4);")), [])

    def test_demos_judged_separately(self):  # 다른 애니메이션의 같은 좌표는 합치지 않는다
        self.assertEqual(self.fails(note_demo("d1", "fx.say(tl, nt, 10, 10, '가', 0.4);", "fx.say(tl, nt, 50, 10, '나', 0.4);")
                                    + note_demo("d2", "fx.say(tl, nt, 10, 10, '가', 0.4);")), [])


class BaselineMark(unittest.TestCase):  # 전후 비교의 기준선: 전후 전환 figure는 기준선 도형에 data-rc-base를 단다
    def test_before_after_without_mark(self):
        html = page(body='<figure id="d1" data-anim="전후 전환"><svg><rect id="b"/></svg></figure>',
                    script="RC.demo(document.getElementById('d1'),[]);")
        fails = anim.baseline_mark_violations(html)
        self.assertEqual(len(fails), 1)
        self.assertTrue(has(fails, "전후 전환 기준선 표시 누락"))
        self.assertIn("d1", fails[0])

    def test_with_mark_ok(self):
        html = page(body='<figure id="d1" data-anim="전후 전환"><svg><rect id="b"/><rect id="b0" data-rc-base/></svg></figure>',
                    script="RC.demo(document.getElementById('d1'),[]);")
        self.assertEqual(anim.baseline_mark_violations(html), [])

    def test_other_type_not_judged(self):
        self.assertEqual(anim.baseline_mark_violations(anim_page([("page core", "p2", ["d1"])])), [])


class NewRulesOnSamples(unittest.TestCase):  # 새 규칙은 고정 견본 sample-anim에서만 위반을 낸다
    FILES = ["bench/fixed/03-groups.html", "bench/fixed/04-rules.html", "bench/fixed/sample-viz.html",
             "bench/fixed/session-report.html", "tests/sample-anim.html", "tests/sample-viz.html",
             "template.html", "template-paged.html"]

    def test_registered(self):
        self.assertIn((anim.note_fixed_violations, "exact"), anim.RULES)
        self.assertIn((anim.baseline_mark_violations, "exact"), anim.RULES)

    def test_only_fixed_sample_anim_violates(self):
        rules = (anim.note_fixed_violations, anim.baseline_mark_violations)
        for name in self.FILES:
            html = (ROOT / name).read_text(encoding="utf-8")
            self.assertEqual([f for r in rules for f in r(html)], [], name)
        html = (ROOT / "bench/fixed/sample-anim.html").read_text(encoding="utf-8")
        self.assertTrue(has(anim.note_fixed_violations(html), "설명 상자 고정 위치"))
        self.assertTrue(has(anim.baseline_mark_violations(html), "전후 전환 기준선 표시 누락"))


class ListSync(unittest.TestCase):
    def test_skill_table_matches_check(self):
        text = (ROOT / "시각화.md").read_text(encoding="utf-8")
        sec = text.split("\n## 애니메이션\n", 1)[1].split("\n## ", 1)[0]
        rows = {}
        for line in sec.splitlines():
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            if line.startswith("|") and len(cols) >= 2 and cols[-1] in ("사용 가능", "견본 대기"):
                rows[cols[0]] = cols[-1]
        self.assertEqual(rows, anim.ANIM_TYPES)

    def test_fx_table_lists_mark(self):  # 애니메이션 함수 표에 RC.fx.mark 줄이 있다
        text = (ROOT / "시각화.md").read_text(encoding="utf-8")
        self.assertIn("| `RC.fx.mark(tl, el, color, at)` |", text)



class EngineMode(EngineCase):
    def test_default_mode_is_step_and_attribute(self):
        p = self.open(MMD, mmd_steps(FLOW))
        self.assertEqual(self.js(p, "() => document.getElementById('d1').dataset.rcMode"), "step")

    def test_url_mode_auto(self):
        p = self.open(MMD, mmd_steps(FLOW), mode="auto")
        self.assertEqual(self.js(p, "() => document.getElementById('d1').dataset.rcMode"), "auto")

    def test_initial_time_zero_and_buttons(self):
        p = self.open(MMD, mmd_steps(FLOW))
        st = self.js(p, """() => { const f = document.getElementById('d1');
          return {t: f._rcTl.time(), btn: [...f.querySelectorAll('.demo-ctl button')].map(b => b.textContent),
                  cap: f.querySelector('.demo-cap').textContent}; }""")
        self.assertEqual(st, {"t": 0, "btn": ["이전", "재생", "다음", "처음부터"], "cap": ""})

    def test_step1_plays_in_both_modes(self):
        for mode in ("step", "auto"):
            p = self.open(MMD, mmd_steps(FLOW), mode=mode)
            r = self.js(p, "([id, m]) => __c0.step1(id, m)", ["d1", mode])
            self.assertTrue(r["reached"] and r["initial"] <= 0.05 and r["e0"] >= 0.2, (mode, r))

    def test_auto_next_runs_to_end_label(self):  # 자동 재생의 '다음'은 머무는 시간까지 재생한다
        p = self.open(MMD, mmd_steps(FLOW), mode="auto")
        r = self.js(p, "async () => { await __c0.toStep('d1', 0); const tl = document.getElementById('d1')._rcTl; return [tl.time(), tl.labels.e0]; }")
        self.assertAlmostEqual(r[0], r[1], places=3)
        self.assertGreater(r[1], 1.0)

    def test_step_mode_segments_and_hold(self):
        long_step = "{name:'긴 단계',text:'길게 움직입니다.',play:function(tl,$){tl.to($('A'),{strokeWidth:3,duration:4});}}"
        short_step = "{name:'짧은 단계',text:'바로 바뀝니다.',play:function(tl,$){tl.set($('B'),{strokeWidth:2});}}"
        p = self.open(MMD, f"RC.demo(document.getElementById('d1'),[{long_step},{short_step},{short_step}]);")
        r = self.js(p, "id => __c0.stepAnim(id)", "d1")
        ends = self.js(p, "() => __c0.ends(document.getElementById('d1')._rcTl)")
        segs = [ends[0]] + [b - a for a, b in zip(ends, ends[1:])]
        self.assertTrue(all(0.4 <= s <= 2.5 for s in segs), segs)
        self.assertTrue(r["held"], r)

    def test_button_mash_runs_one_step(self):
        p = self.open(MMD, mmd_steps(FLOW), mode="auto")
        t = self.js(p, """async () => { const f = document.getElementById('d1'), b = f.querySelectorAll('.demo-ctl button');
          b[1].click(); b[1].click(); b[1].click(); b[2].click(); b[2].click();
          await new Promise(r => setTimeout(r, 200));
          return {t: f._rcTl.time(), e: __c0.ends(f._rcTl), playing: b[1].textContent}; }""")
        self.assertLessEqual(t["t"], t["e"][1] + 1e-6)
        self.assertEqual(t["playing"], "재생")


class EngineDwell(EngineCase):
    def dwell(self, p):
        r = self.js(p, "id => __c0.dwellSamples(id)", "d1")
        return measure.dwell_steps([(t, s) for t, s in r["samples"]], r["ends"])

    def test_caption_only_steps_meet_rule(self):  # 무대 글이 없는 단계도 자막으로 n을 얻는다
        p = self.open(MMD, mmd_steps(FLOW), mode="auto")
        steps = self.dwell(p)
        self.assertTrue(all(s["ok"] for s in steps), steps)
        self.assertTrue(all(s["n"] > 0 for s in steps), steps)

    def test_stage_text_counts(self):  # 무대 글(숫자 칸 포함)과 작성자 설명 상자 글을 센다
        body = ('<figure id="d1" data-anim="구조"><svg viewBox="0 0 400 200" width="100%">'
                '<rect id="r" x="20" y="80" width="80" height="40" fill="none" stroke="currentColor"/>'
                '<text id="v" x="200" y="100" font-size="14">0</text></svg></figure>')
        script = ("var st=document.querySelector('#d1 svg'),nt=RC.note(st,180,40);"
                  "RC.demo(document.getElementById('d1'),[{name:'가',text:'첫 단계입니다.',play:function(tl,$){"
                  "RC.fx.say(tl,nt,200,20,'모델 A는 비슷한 변형 일곱 개',0.6);RC.fx.count(tl,$('v'),0,720000,'원',0.4);}},"
                  "{name:'나',text:'둘째 단계입니다.',play:function(tl,$){RC.fx.say(tl,nt,200,20,'둘째',0.2);}}]);")
        p = self.open(body, script, mode="auto")
        steps = self.dwell(p)
        self.assertTrue(all(s["ok"] for s in steps), steps)
        self.assertGreaterEqual(steps[0]["n"], 14)

    def test_rewind_keeps_popped_icon(self):  # 같은 아이콘을 두 단계에서 pop해도 '이전'으로 돌아가면 보인다
        body = ('<figure id="d1" data-anim="구조"><svg viewBox="0 0 400 200" width="100%">'
                '<rect id="r" x="20" y="80" width="80" height="40" fill="none" stroke="currentColor"/></svg></figure>')
        script = ("var st=document.querySelector('#d1 svg'),ic=RC.icon(st,'check',300,40);"
                  "RC.demo(document.getElementById('d1'),["
                  "{name:'가',text:'나타납니다.',play:function(tl,$){RC.fx.pop(tl,ic);$('r');}},"
                  "{name:'나',text:'사라집니다.',play:function(tl,$){tl.to(ic,{opacity:0,duration:0.2});$('r');}},"
                  "{name:'다',text:'다시 나타납니다.',play:function(tl,$){RC.fx.pop(tl,ic);$('r');}}]);")
        p = self.open(body, script)
        r = self.js(p, """() => { const f = document.getElementById('d1'), b = f.querySelectorAll('.demo-ctl button'), ic = f.querySelector('.rc-icon');
          f._rcTl.seek('e2', false); b[0].click(); b[0].click();
          return +getComputedStyle(ic).opacity; }""")
        self.assertGreater(r, 0.9)


def many(prefix_a="시나리오 A", prefix_b="시나리오 B", n_a=7, n_b=6):
    nodes = ["A", "B", "C", "D"]
    return ([(f"{prefix_a} · 단계{k}", f"가 단계 {k}입니다.", nodes[k % 4], None) for k in range(n_a)]
            + [(f"{prefix_b} · 단계{k}", f"나 단계 {k}입니다.", nodes[k % 4], None) for k in range(n_b)])


class EngineScenario(EngineCase):
    def test_counter_and_row(self):
        p = self.open(MMD, mmd_steps(many()), mode="auto")
        r = self.js(p, """() => { const f = document.getElementById('d1'); f._rcTl.seek('e1', false);
          f.querySelectorAll('.demo-ctl button')[0].click();
          return {cnt: f.querySelector('.demo-ctl .cnt').textContent,
                  scen: [...f.querySelectorAll('.demo-scen button')].map(x => x.textContent),
                  ctl: [...f.querySelectorAll('.demo-ctl button')].map(x => x.textContent),
                  inCtl: !!f.querySelector('.demo-ctl .demo-scen')}; }""")
        self.assertEqual(r["cnt"], "시나리오 A 1/7")
        self.assertEqual(r["scen"], ["전체", "시나리오 A", "시나리오 B"])
        self.assertEqual(r["ctl"], ["이전", "재생", "다음", "처음부터"])
        self.assertFalse(r["inCtl"])

    def test_select_scenario_stops_at_its_end_and_reset_returns_all(self):
        p = self.open(MMD, mmd_steps(many(n_a=7, n_b=6)), mode="step")
        r = self.js(p, """async () => { const f = document.getElementById('d1'), tl = f._rcTl, b = f.querySelectorAll('.demo-ctl button');
          [...f.querySelectorAll('.demo-scen button')].find(x => x.textContent === '시나리오 B').click();
          const first = tl.time();
          for (let k = 0; k < 400 && b[1].textContent !== '재생'; k++) await new Promise(r => setTimeout(r, 100));
          const out = {first, t: tl.time(), e: __c0.ends(tl), cnt: f.querySelector('.demo-ctl .cnt').textContent};
          b[3].click();
          out.after = {t: tl.time(), on: f.querySelector('.demo-scen button.on').textContent};
          return out; }""")
        self.assertAlmostEqual(r["first"], r["e"][6], places=3)
        self.assertAlmostEqual(r["t"], r["e"][12], places=3)
        self.assertEqual(r["cnt"], "시나리오 B 6/6")
        self.assertEqual(r["after"], {"t": 0, "on": "전체"})

    def test_no_row_when_12_steps_or_less(self):
        p = self.open(MMD, mmd_steps(many(n_a=3, n_b=3)))
        self.assertEqual(self.js(p, "() => document.querySelectorAll('#d1 .demo-scen').length"), 0)

    def test_x_dot_y_without_prefix_not_grouped(self):
        p = self.open(MMD, mmd_steps(many("전후 전환 A", "전후 전환 B")), mode="auto")
        r = self.js(p, """() => { const f = document.getElementById('d1'); f._rcTl.seek('e1', false);
          f.querySelectorAll('.demo-ctl button')[0].click();
          return {cnt: f.querySelector('.demo-ctl .cnt').textContent, row: f.querySelectorAll('.demo-scen').length}; }""")
        self.assertEqual(r, {"cnt": "1/13", "row": 0})

    def test_print_hides_row(self):  # 인쇄에서는 시나리오 줄을 숨긴다
        p = self.open(MMD, mmd_steps(many()))
        p.emulate_media(media="print")
        self.assertEqual(self.js(p, "() => getComputedStyle(document.querySelector('#d1 .demo-scen')).display"), "none")


class EngineActive(EngineCase):
    def active_at(self, p, i):
        r = self.js(p, """([i]) => { const f = document.getElementById('d1'); f._rcTl.seek('e' + i, false);
          return [...f.querySelectorAll('[data-rc-active]')].map(e => (e.closest('g.node') || e).id.replace(/.*flowchart-/, '').replace(/-\\d+$/, '')); }""", [i])
        self.assertEqual(len(r), 1, f"단계 {i} 끝에 data-rc-active가 정확히 하나여야 한다: {r}")  # C0는 하나만 허용한다
        return r

    def test_last_lookup_and_mark_priority(self):
        script = ("RC.demo(document.getElementById('d1'),["
                  "{name:'가',text:'조회만 합니다.',play:function(tl,$){tl.to($('A'),{strokeWidth:2,duration:0.3});$('B');}},"
                  "{name:'나',text:'mark를 씁니다.',play:function(tl,$){RC.fx.mark(tl,$('C'));$('D');}}]);")
        p = self.open(MMD, script)
        self.assertEqual(self.active_at(p, 0), ["B"])
        self.assertEqual(self.active_at(p, 1), ["C"])

    def test_spot_priority_on_drawn_stage(self):
        body = ('<figure id="d1" data-anim="구조"><svg viewBox="0 0 400 200" width="100%">'
                '<rect id="a" x="20" y="80" width="80" height="40" fill="none" stroke="currentColor"/>'
                '<rect id="b" x="200" y="80" width="80" height="40" fill="none" stroke="currentColor"/></svg></figure>')
        script = ("var st=document.querySelector('#d1 svg'),fr=RC.focus(st);RC.demo(document.getElementById('d1'),["
                  "{name:'가',text:'첫 단계입니다.',play:function(tl,$){RC.fx.spot(tl,fr,$('a'));$('b');}}]);")
        p = self.open(body, script)
        self.assertEqual(self.active_at(p, 0), ["a"])

    def test_current_and_past_style_keep_author_color(self):
        script = ("RC.demo(document.getElementById('d1'),["
                  "{name:'가',text:'첫 단계입니다.',play:function(tl,$){$('A');}},"
                  "{name:'나',text:'둘째 단계입니다.',play:function(tl,$){RC.fx.mark(tl,$('B'),'neg');}},"
                  "{name:'다',text:'셋째 단계입니다.',play:function(tl,$){$('C');}}]);")
        p = self.open(MMD, script)
        r = self.js(p, """() => { const f = document.getElementById('d1'), cs = e => getComputedStyle(e);
          const shape = n => [...f.querySelectorAll('g.node')].find(g => g.id.includes('-' + n + '-')).querySelector('rect, polygon');
          const col = n => { const d = document.createElement('i'); d.style.color = getComputedStyle(document.documentElement).getPropertyValue('--' + n); document.body.appendChild(d); const c = cs(d).color; d.remove(); return c; };
          f._rcTl.seek('e2', false);
          return {curW: cs(shape('C')).strokeWidth, curFill: +cs(shape('C')).fillOpacity, pastA: cs(shape('A')).stroke,
                  pastAW: cs(shape('A')).strokeWidth, pastB: cs(shape('B')).stroke, pastBW: cs(shape('B')).strokeWidth,
                  accent2: col('accent-2'), neg: col('neg')}; }""")
        self.assertEqual(r["curW"], "2px")
        self.assertAlmostEqual(r["curFill"], 0.08, places=2)
        self.assertEqual((r["pastA"], r["pastAW"]), (r["accent2"], "1.5px"))  # 작성자 색이 없던 노드는 보조 강조색
        self.assertEqual((r["pastB"], r["pastBW"]), (r["neg"], "1.5px"))     # 작성자가 준 neg 색은 유지한다

    def test_spot_unspot_keep_engine_highlight(self):  # spot·unspot 트윈은 작성자 색으로 보지 않는다
        body = ('<figure id="d1" data-anim="구조"><svg viewBox="0 0 400 200" width="100%">'
                '<rect id="a" x="20" y="80" width="80" height="40" fill="none" stroke="currentColor"/>'
                '<rect id="b" x="200" y="80" width="80" height="40" fill="none" stroke="currentColor"/></svg></figure>')
        script = ("var st=document.querySelector('#d1 svg'),fr=RC.focus(st);RC.demo(document.getElementById('d1'),["
                  "{name:'가',text:'첫 단계입니다.',play:function(tl,$){RC.fx.spot(tl,fr,$('a'));}},"
                  "{name:'나',text:'둘째 단계입니다.',play:function(tl,$){RC.fx.spot(tl,fr,$('b'));}},"
                  "{name:'다',text:'셋째 단계입니다.',play:function(tl,$){RC.fx.unspot(tl,fr,[$('a'),$('b')]);RC.fx.spot(tl,fr,$('a'));}},"
                  "{name:'라',text:'넷째 단계입니다.',play:function(tl,$){RC.fx.spot(tl,fr,$('b'));}}]);")
        p = self.open(body, script)
        r = self.js(p, """() => { const f = document.getElementById('d1'), cs = id => getComputedStyle(document.getElementById(id));
          const col = n => { const d = document.createElement('i'); d.style.color = getComputedStyle(document.documentElement).getPropertyValue('--' + n); document.body.appendChild(d); const c = getComputedStyle(d).color; d.remove(); return c; };
          const out = [];
          for (let i = 0; i < 4; i++) { f._rcTl.seek('e' + i, false);
            out.push([cs('a').stroke, cs('a').strokeWidth, cs('b').stroke, cs('b').strokeWidth]); }
          return {out, A: col('accent'), A2: col('accent-2'), K: col('ink')}; }""")
        A, A2 = r["A"], r["A2"]
        self.assertEqual(r["out"][0][:2], [A, "2px"])
        self.assertEqual(r["out"][1], [A2, "1.5px", A, "2px"])
        self.assertEqual(r["out"][2], [A, "2px", r["K"], "1px"])  # unspot이 처음 상태로 돌린 b를 지나온 노드 표시가 덮어쓰지 않는다
        self.assertEqual(r["out"][3], [A2, "1.5px", A, "2px"])

    def test_opaque_zero_blue_text_is_seen(self):  # 파랑 성분이 0인 불투명 글자색(rgb(200, 100, 0))도 보이는 글로 센다
        def e0(fill, name):  # 두 문서가 같은 파일 이름이면 브라우저 캐시가 앞 문서를 다시 줄 수 있어 이름을 나눈다
            body = ('<figure id="d1" data-anim="구조"><svg viewBox="0 0 400 200" width="100%">'
                    f'<text id="t" x="20" y="100" style="fill:{fill}"></text></svg></figure>')
            script = ("RC.demo(document.getElementById('d1'),[{name:'가',text:'첫 단계입니다.',play:function(tl){"
                      "RC.fx.type(tl,document.getElementById('t'),'ABCDEFGHIJKLMNOP',0.5);}}]);")
            p = self.open_file(name, engine_doc(body, script), mode="auto")
            return self.js(p, "() => document.getElementById('d1')._rcTl.labels.e0")
        self.assertGreater(e0("rgb(200, 100, 0)", "opaque_zero_blue.html") - e0("rgba(200, 100, 0, 0)", "clear_zero_blue.html"), 1.5)  # 16자 ÷ 8 = 2초 더 머문다

    def test_reset_reverts_time0_set_with_author_note(self):  # 작성자 설명 상자가 있어도 시각 0의 tl.set을 '처음부터'가 되돌린다
        body = ('<figure id="d1" data-anim="구조"><svg viewBox="0 0 400 200" width="100%">'
                '<rect id="a" x="20" y="80" width="80" height="40" fill="none" stroke="currentColor"/></svg></figure>')
        script = ("var st=document.querySelector('#d1 svg'),nt=RC.note(st,120,30);RC.demo(document.getElementById('d1'),["
                  "{name:'가',text:'첫 단계입니다.',play:function(tl,$){tl.set($('a'),{opacity:0.2});tl.to($('a'),{x:10,duration:0.3});}},"
                  "{name:'나',text:'둘째 단계입니다.',play:function(tl,$){tl.to($('a'),{x:20,duration:0.3});}}]);")
        p = self.open(body, script)
        r = self.js(p, """() => { const f = document.getElementById('d1'), a = document.getElementById('a');
          f._rcTl.seek('e1', false); const mid = +getComputedStyle(a).opacity;
          f.querySelectorAll('.demo-ctl button')[3].click(); return [mid, +getComputedStyle(a).opacity]; }""")
        self.assertEqual(r, [0.2, 1])

    def test_engine_fill_only_on_current_node(self):  # 다시 현재 노드가 된 노드에도 채움을 넣고, 시나리오 초기화(unmark) 뒤 앞 노드의 채움을 남기지 않는다
        nodes = "ABCDABC" + "ABDABC"
        items = ",".join(
            "{name:'시나리오 %s · 단계%d',text:'%s 노드입니다.',play:function(tl,$){%sRC.fx.mark(tl,$('%s'));}}"
            % ("A" if i < 7 else "B", i, n, "RC.fx.unmark(tl,['A','B','C','D'].map($));" if i in (0, 7) else "", n)
            for i, n in enumerate(nodes))
        p = self.open(MMD, f"RC.demo(document.getElementById('d1'),[{items}]);")
        r = self.js(p, """() => { const f = document.getElementById('d1'), tl = f._rcTl;
          const shapes = [...f.querySelectorAll('g.node')].map(g => [g.id.replace(/.*flowchart-/, '').replace(/-\\d+$/, ''), g.querySelector('rect, polygon')]);
          const st = k => { tl.seek(k, false); return shapes.filter(([n, e]) => Math.abs(+getComputedStyle(e).fillOpacity - 0.08) < 0.005).map(([n]) => n).join(''); };
          const fwd = [...Array(13).keys()].map(i => st('e' + i)), back = [...Array(13).keys()].reverse().map(i => st('e' + i)).reverse();
          [...f.querySelectorAll('.demo-scen button')].find(x => x.textContent === '시나리오 B').click();
          f.querySelectorAll('.demo-ctl button')[1].click();  // 재생을 멈춘다
          const scen = [st('e7'), st('e8')]; return {fwd, back, scen}; }""")
        self.assertEqual(r["fwd"], list(nodes))
        self.assertEqual(r["back"], list(nodes))
        self.assertEqual(r["scen"], ["A", "B"])

    def test_closed_shape_preferred_over_text(self):  # mark·spot이 없으면 그 단계에서 조회한 닫힌 도형 중 마지막 것이 글자보다 우선한다
        body = ('<figure id="d1" data-anim="구조"><svg viewBox="0 0 400 200" width="100%">'
                '<rect id="bar" x="20" y="80" width="40" height="100" style="fill:#888"/>'
                '<text id="val" x="20" y="70">31</text><text id="lbl" x="200" y="70">설명</text></svg></figure>')
        script = ("RC.demo(document.getElementById('d1'),["
                  "{name:'가',text:'막대가 자랍니다.',play:function(tl,$){tl.to($('bar'),{attr:{height:90},duration:0.3});$('val');}},"
                  "{name:'나',text:'글자만 조회합니다.',play:function(tl,$){$('lbl');}}]);")
        p = self.open(body, script)
        self.assertEqual(self.active_at(p, 0), ["bar"])
        self.assertEqual(self.active_at(p, 1), ["lbl"])

    def test_active_moves_at_step_end(self):  # data-rc-active는 단계 끝 시각에 옮긴다
        p = self.open(MMD, mmd_steps(FLOW))
        r = self.js(p, """() => { const f = document.getElementById('d1'), tl = f._rcTl;
          const id = () => [...f.querySelectorAll('[data-rc-active]')].map(e => e.closest('g.node').id.replace(/.*flowchart-/, '').replace(/-\\d+$/, ''));
          tl.seek(tl.labels.e0 + 0.05, false); const mid = id(); tl.seek('e1', false); const e1 = id(); tl.seek('e2', false); return [mid, e1, id()]; }""")
        self.assertEqual(r, [["A"], ["B"], ["C"]])  # 단계 끝마다 정확히 하나

    BARS = ('<figure id="d1" data-anim="구조"><svg viewBox="0 0 700 300" width="100%">'
            '<rect id="ba" x="110" y="60" width="400" height="24" style="fill:var(--s4)"/>'
            '<rect id="bb" x="110" y="140" width="200" height="24" style="fill:var(--s4)"/>'
            '<rect id="bc" x="110" y="220" width="200" height="24" fill="none" stroke="currentColor"/></svg></figure>')
    CORNERS = """() => { const f = document.getElementById('d1'), tl = f._rcTl, out = [];
      const near = (g, id) => { const r = document.getElementById(id).getBoundingClientRect();
        const ps = [...g.children].map(c => c.getBoundingClientRect());
        const l = Math.min(...ps.map(q => q.left)), rt = Math.max(...ps.map(q => q.right)), t = Math.min(...ps.map(q => q.top)), b = Math.max(...ps.map(q => q.bottom));
        return l < r.left && rt > r.right && t < r.top && b > r.bottom && l > r.left - 12 && rt < r.right + 12 && t > r.top - 12 && b < r.bottom + 12; };
      const at = k => { tl.seek(k, false); const g = f.querySelector('.rc-corner'), on = g && +getComputedStyle(g).opacity > 0.5;
        return on ? ['ba', 'bb', 'bc'].filter(id => near(g, id)).join('') || '?' : ''; };
      for (const k of ARGS) out.push(at(k)); return out; }"""

    def corners(self, p, keys):
        return self.js(p, self.CORNERS.replace("ARGS", json.dumps(keys)))

    def test_corners_on_opaque_current_node(self):  # 작성자 채움이 불투명한 현재 노드에만 꺾쇠를 두고, 지나오면 지운다. 되감기에서도 같다
        script = ("function grow(tl,$,id,w){tl.to($(id),{attr:{width:w},fill:RC.color('s1'),duration:0.6});}"
                  "RC.demo(document.getElementById('d1'),["
                  "{name:'가',text:'첫 막대입니다.',play:function(tl,$){grow(tl,$,'ba',248);}},"
                  "{name:'나',text:'둘째 막대입니다.',play:function(tl,$){grow(tl,$,'bb',208);}},"
                  "{name:'다',text:'채움 없는 막대입니다.',play:function(tl,$){tl.to($('bc'),{attr:{width:300},duration:0.3});}}]);")
        p = self.open(self.BARS, script)
        self.assertEqual(self.corners(p, ["e0", "e1", "e2", "e1", "e0"]), ["ba", "bb", "", "bb", "ba"])

    def test_corners_with_scenario_select_and_token(self):  # 시나리오를 고른 첫 단계에 앞 시나리오의 꺾쇠가 남지 않고, 이동 표식(rc-token)에는 꺾쇠를 두지 않는다
        body = self.BARS.replace('</svg>', '<circle id="tk" class="rc-token" cx="600" cy="150" r="5" style="fill:var(--neg)"/></svg>')
        items = []
        for i in range(13):
            sc, bar = ("A", "ba") if i < 7 else ("B", "bb")
            play = f"tl.to($('{bar}'),{{attr:{{width:{200 + i * 10}}},duration:0.3}});" if i not in (6, 7) else (
                "tl.to($('tk'),{attr:{cx:620},duration:0.3});" if i == 6 else "tl.to($('bc'),{attr:{width:250},duration:0.3});")
            items.append("{name:'시나리오 %s · 단계%d',text:'단계 %d입니다.',play:function(tl,$){%s}}" % (sc, i, i, play))
        p = self.open(body, f"RC.demo(document.getElementById('d1'),[{','.join(items)}]);")
        self.assertEqual(self.corners(p, ["e5", "e6", "e7", "e8"]), ["ba", "", "", "bb"])
        r = self.js(p, """() => { const f = document.getElementById('d1');
          f._rcTl.seek('e5', false);
          [...f.querySelectorAll('.demo-scen button')].find(x => x.textContent === '시나리오 B').click();
          f.querySelectorAll('.demo-ctl button')[1].click();  // 재생을 멈춘다
          const g = f.querySelector('.rc-corner'); return +getComputedStyle(g).opacity; }""")
        self.assertLess(r, 0.5)  # 시나리오 B 시작 화면에는 시나리오 A 막대의 꺾쇠가 없다

    def test_no_engine_corners_with_spot(self):  # RC.fx.spot이 초점 틀을 그리는 노드에는 엔진 꺾쇠를 겹쳐 그리지 않는다
        script = ("var st=document.querySelector('#d1 svg'),fr=RC.focus(st);RC.demo(document.getElementById('d1'),["
                  "{name:'가',text:'첫 막대입니다.',play:function(tl,$){RC.fx.spot(tl,fr,$('ba'));}},"
                  "{name:'나',text:'둘째 막대입니다.',play:function(tl,$){tl.to($('bb'),{attr:{width:208},duration:0.3});}}]);")
        p = self.open(self.BARS, script)
        self.assertEqual(self.corners(p, ["e0", "e1"]), ["", "bb"])

    DIMS = """() => { const f = document.getElementById('d1'), tl = f._rcTl;
      const op = id => +(+getComputedStyle(document.getElementById(id)).fillOpacity).toFixed(2);
      return ARGS.map(k => { tl.seek(k, false); return [op('ba'), op('bb')]; }); }"""

    def dims(self, p, keys):
        return self.js(p, self.DIMS.replace("ARGS", json.dumps(keys)))

    def test_passed_opaque_node_dimmed(self):  # 지나온 불투명 노드(꺾쇠를 받은 노드)는 채움을 흐리게 하고, 다시 현재 노드가 되면 원래 채움으로 돌린다. 되감기에서도 같다
        script = ("function grow(tl,$,id,w){tl.to($(id),{attr:{width:w},fill:RC.color('s1'),duration:0.6});}"
                  "RC.demo(document.getElementById('d1'),["
                  "{name:'가',text:'첫 막대입니다.',play:function(tl,$){grow(tl,$,'ba',248);}},"
                  "{name:'나',text:'둘째 막대입니다.',play:function(tl,$){grow(tl,$,'bb',208);}},"
                  "{name:'다',text:'첫 막대를 다시 봅니다.',play:function(tl,$){grow(tl,$,'ba',260);}},"
                  "{name:'라',text:'채움 없는 막대입니다.',play:function(tl,$){tl.to($('bc'),{attr:{width:300},duration:0.3});}}]);")
        p = self.open(self.BARS, script)
        D = 0.45
        self.assertEqual(self.dims(p, ["e0", "e1", "e2", "e3"]), [[1, 1], [D, 1], [1, D], [D, D]])
        self.assertEqual(self.dims(p, ["e2", "e1", "e0"]), [[1, D], [D, 1], [1, 1]])
        r = self.js(p, "() => { document.getElementById('d1')._rcTl.seek('e3', false); return +getComputedStyle(document.getElementById('bc')).fillOpacity; }")
        self.assertNotAlmostEqual(r, D, places=2)  # 작성자 채움이 없는 노드는 흐리게 하지 않는다

    def test_dim_base_is_step_end_opacity(self):  # 흐림 기준은 노드가 현재였던 단계 끝의 채움 불투명도다(그 단계가 0.3에서 1로 올린 값)
        body = self.BARS.replace('id="ba" x="110" y="60" width="400" height="24" style="fill:var(--s4)"',
                                 'id="ba" x="110" y="60" width="400" height="24" style="fill:var(--s4);fill-opacity:0.3"')
        script = ("RC.demo(document.getElementById('d1'),["
                  "{name:'가',text:'첫 막대입니다.',play:function(tl,$){tl.to($('ba'),{fillOpacity:1,duration:0.3});}},"
                  "{name:'나',text:'둘째 막대입니다.',play:function(tl,$){tl.to($('bb'),{attr:{width:208},duration:0.3});}},"
                  "{name:'다',text:'첫 막대를 다시 봅니다.',play:function(tl,$){tl.to($('ba'),{attr:{width:260},duration:0.3});}}]);")
        p = self.open(body, script)
        self.assertEqual(self.dims(p, ["e0", "e1", "e2"]), [[1, 1], [0.45, 1], [1, 0.45]])

    def test_dim_with_scenario_select(self):  # 시나리오를 고르면 그 시작 화면의 흐림 상태가 앞으로 재생한 상태와 같다
        items = []
        for i in range(13):
            sc, bar = ("A", "ba" if i % 2 == 0 else "bb") if i < 7 else ("B", "bb" if i % 2 else "ba")
            items.append("{name:'시나리오 %s · 단계%d',text:'단계 %d입니다.',play:function(tl,$){tl.to($('%s'),{attr:{width:%d},duration:0.3});}}"
                         % (sc, i, i, bar, 200 + i * 10))
        p = self.open(self.BARS, f"RC.demo(document.getElementById('d1'),[{','.join(items)}]);")
        fwd = self.dims(p, ["e6", "e7"])
        r = self.js(p, """() => { const f = document.getElementById('d1'), op = id => +(+getComputedStyle(document.getElementById(id)).fillOpacity).toFixed(2);
          f._rcTl.seek('e12', false);
          [...f.querySelectorAll('.demo-scen button')].find(x => x.textContent === '시나리오 B').click();
          f.querySelectorAll('.demo-ctl button')[1].click();  // 재생을 멈춘다
          return [op('ba'), op('bb')]; }""")
        self.assertEqual(fwd, [[1, 0.45], [0.45, 1]])  # e6: ba 현재, e7: bb 현재
        self.assertEqual(r, fwd[0])  # 시나리오 B 시작 시각은 e6 끝이다

    def test_no_dim_on_mermaid_and_spot(self):  # 엔진 채움을 받는 Mermaid 노드와 초점 틀 노드는 흐리게 하지 않는다
        p = self.open(MMD, mmd_steps(FLOW))
        r = self.js(p, """() => { const f = document.getElementById('d1'); f._rcTl.seek('e2', false);
          const shape = n => [...f.querySelectorAll('g.node')].find(g => g.id.includes('-' + n + '-')).querySelector('rect, polygon');
          return ['A', 'B'].map(n => +getComputedStyle(shape(n)).fillOpacity); }""")
        self.assertEqual(r, [1, 1])
        script = ("var st=document.querySelector('#d1 svg'),fr=RC.focus(st);RC.demo(document.getElementById('d1'),["
                  "{name:'가',text:'첫 막대입니다.',play:function(tl,$){RC.fx.spot(tl,fr,$('ba'));}},"
                  "{name:'나',text:'둘째 막대입니다.',play:function(tl,$){RC.fx.spot(tl,fr,$('bb'));}}]);")
        p = self.open_file("no_dim_spot.html", engine_doc(self.BARS, script))
        self.assertEqual(self.dims(p, ["e1"]), [[0, 0.08]])  # spot이 정한 채움(지나온 0, 현재 0.08) 그대로다


class EngineCheckRules(EngineCase):  # RC.check의 작성 규칙 항목: 작성자 상자 거리(noteFar)와 기준선 유지(baseLost)
    STAGE = ('<figure id="d1" data-anim="전후 전환"><svg viewBox="0 0 600 300" width="600" height="300">'
             '<rect id="a" x="40" y="200" width="100" height="40" style="fill:var(--s1)"/>'
             '<rect id="a0" x="40" y="244" width="100" height="6" style="fill:var(--s4)" BASE/>'
             '<rect id="b" x="300" y="200" width="100" height="40" style="fill:var(--s1)"/></svg></figure>')

    def check(self, body, script):
        p = self.open(body, script)
        p.set_default_timeout(120_000)
        return p.evaluate("() => RC.check('d1')")

    def test_author_note_far_fails(self):
        script = ("var st=document.querySelector('#d1 svg'),nt=RC.note(st,120,30);RC.demo(document.getElementById('d1'),["
                  "{name:'가',text:'첫 막대입니다.',play:function(tl,$){RC.fx.say(tl,nt,40,150,'가까운 상자',0.3);$('a');}},"
                  "{name:'나',text:'둘째 막대입니다.',play:function(tl,$){RC.fx.say(tl,nt,40,150,'먼 상자',0.3);$('b');}}]);")
        r = self.check(self.STAGE.replace("BASE", "data-rc-base"), script)
        self.assertFalse(r["pass"], r)
        self.assertEqual(len(r["noteFar"]), 1, r)  # 둘째 단계만 48px를 넘는다
        self.assertIn("2", r["noteFar"][0])

    def test_author_note_near_and_base_kept_pass(self):
        script = ("var st=document.querySelector('#d1 svg'),nt=RC.note(st,120,30);RC.demo(document.getElementById('d1'),["
                  "{name:'가',text:'첫 막대입니다.',play:function(tl,$){RC.fx.say(tl,nt,40,150,'가',0.3);tl.to($('a'),{attr:{width:120},duration:0.3});}},"
                  "{name:'나',text:'둘째 막대입니다.',play:function(tl,$){RC.fx.say(tl,nt,300,150,'나',0.3);tl.to($('b'),{attr:{width:80},duration:0.3});}}]);")
        r = self.check(self.STAGE.replace("BASE", "data-rc-base"), script)
        self.assertTrue(r["pass"], r)
        self.assertEqual((r["noteFar"], r["baseLost"]), ([], []))

    def test_base_overwritten_or_hidden_fails(self):
        for i, play in enumerate(("tl.to($('a0'),{attr:{width:60},duration:0.3});",  # 기준선 도형을 바뀐 값으로 덮어쓴다
                                  "tl.to($('a0'),{opacity:0,duration:0.3});")):    # 마지막 단계에서 기준선을 지운다
            script = ("RC.demo(document.getElementById('d1'),["
                      "{name:'가',text:'첫 막대입니다.',play:function(tl,$){tl.to($('a'),{attr:{width:120},duration:0.3});}},"
                      "{name:'나',text:'기준선을 바꿉니다.',play:function(tl,$){%s$('b');}}]);" % play)
            p = self.open_file(f"base_lost_{i}.html", engine_doc(self.STAGE.replace("BASE", "data-rc-base"), script))
            p.set_default_timeout(120_000)
            r = p.evaluate("() => RC.check('d1')")
            self.assertFalse(r["pass"], (i, r))
            self.assertEqual(len(r["baseLost"]), 1, (i, r))
            self.assertIn("a0", r["baseLost"][0])

    def test_no_mark_no_base_judgment(self):  # data-rc-base가 없는 figure는 기준선을 판정하지 않는다
        script = ("RC.demo(document.getElementById('d1'),["
                  "{name:'가',text:'기준선을 덮어씁니다.',play:function(tl,$){tl.to($('a0'),{attr:{width:60},duration:0.3});$('a');}}]);")
        r = self.check(self.STAGE.replace("BASE", ""), script)
        self.assertEqual(r["baseLost"], [], r)
        self.assertTrue(r["pass"], r)


# 상자 폭 220은 표시 범위(viewBox) 안에서만 찾는다. MMD는 viewBox 폭이 242라 어느 노드 옆에도 자리가 없어,
# D 아래에 자식 노드를 두어 폭을 넓힌 흐름도로 자동 상자를 본다. A·B·C 모두 한 쪽 이상에 자리가 난다
MMD_WIDE = MMD.replace("D[거부]", "D[거부]" + "".join(
    f"\n  D --> {k}[{v}]" for k, v in zip("EFGHIJ", ["보류", "재검토", "취소", "이관", "보고", "종결"])))
SIDE = """<figure id="d1" data-anim="구조"><svg viewBox="0 0 600 300" width="600" height="300">
<rect id="a" x="40" y="120" width="100" height="40" fill="none" stroke="currentColor"/></svg></figure>"""


class EngineNote(EngineCase):
    def judged(self, p):
        r = self.js(p, "id => __c0.noteSteps(id)", "d1")
        return measure.note_steps(r["steps"], r["view"])

    def test_auto_note_beside_node_and_caption_hidden(self):
        p = self.open(MMD_WIDE, mmd_steps(FLOW))
        for s in self.judged(p):
            self.assertTrue(s["near"] and s["visible"], s)
        r = self.js(p, """() => { const f = document.getElementById('d1');
          return {tag: f.querySelector('svg .rc-note').tagName, text: f.querySelector('svg .rc-note').textContent.trim(),
                  cap: getComputedStyle(f.querySelector('.demo-cap')).visibility}; }""")
        self.assertEqual(r, {"tag": "g", "text": "주문을 체결합니다.", "cap": "hidden"})

    def test_right_side_first(self):
        p = self.open(SIDE, "RC.demo(document.getElementById('d1'),[{name:'가',text:'오른쪽에 둡니다.',play:function(tl,$){$('a');}}]);")
        r = self.js(p, """() => { const f = document.getElementById('d1'); f._rcTl.seek('e0', false);
          return [f.querySelector('.rc-note').getBoundingClientRect().left, document.getElementById('a').getBoundingClientRect().right]; }""")
        self.assertGreater(r[0], r[1])

    def test_wider_gap_when_gap_8_blocked(self):  # 노드 바로 옆이 막히면 48px 안의 더 먼 간격에 둔다
        body = ('<figure id="d1" data-anim="구조"><svg viewBox="0 0 600 300" width="600" height="300">'
                '<rect id="a" x="40" y="120" width="100" height="40" fill="none" stroke="currentColor"/>'
                '<rect id="blk" x="148" y="100" width="4" height="80" fill="none" stroke="currentColor"/></svg></figure>')
        p = self.open(body, "RC.demo(document.getElementById('d1'),[{name:'가',text:'막대 너머에 둡니다.',play:function(tl,$){$('a');}}]);")
        r = self.js(p, """() => { const f = document.getElementById('d1'); f._rcTl.seek('e0', false);
          const n = f.querySelector('.rc-note'), nb = n.getBoundingClientRect(), b = document.getElementById('blk').getBoundingClientRect(),
                a = document.getElementById('a').getBoundingClientRect();
          return {op: +getComputedStyle(n).opacity, clear: nb.left - b.right, gap: nb.left - a.right}; }""")
        self.assertEqual(r["op"], 1)
        self.assertGreaterEqual(r["clear"], 2)
        self.assertTrue(8 < r["gap"] <= 44, r)
        for s in self.judged(p):
            self.assertTrue(s["near"], s)

    def test_author_note_means_no_auto_note(self):
        body = ('<figure id="d1" data-anim="구조"><svg viewBox="0 0 400 200" width="100%">'
                '<rect id="a" x="20" y="120" width="80" height="40" fill="none" stroke="currentColor"/></svg></figure>')
        script = ("var st=document.querySelector('#d1 svg'),nt=RC.note(st,150,40);RC.demo(document.getElementById('d1'),["
                  "{name:'가',text:'첫 단계입니다.',play:function(tl,$){RC.fx.say(tl,nt,200,20,'작성자 글',0.2);$('a');}}]);")
        p = self.open(body, script)
        self.assertEqual(self.js(p, "() => document.querySelectorAll('#d1 .rc-note').length"), 1)

    def test_no_place_shows_caption(self):  # 사방이 막힌 노드는 자동 상자 없이 자막을 보인다
        cells = "".join(f'<rect id="c{r}{c}" x="{c * 90}" y="{r * 50}" width="84" height="44" fill="none" stroke="currentColor"/>'
                        for r in range(9) for c in range(9))
        body = f'<figure id="d1" data-anim="구조"><svg viewBox="0 0 810 450" width="100%">{cells}</svg></figure>'
        script = ("RC.demo(document.getElementById('d1'),[{name:'가',text:'가운데 칸입니다.',play:function(tl,$){"
                  "tl.to($('c44'),{strokeWidth:2,duration:0.3});}}]);")
        p = self.open(body, script)
        r = self.js(p, """() => { const f = document.getElementById('d1'); f._rcTl.seek('e0', false);
          const n = f.querySelector('.rc-note');
          return {note: n && getComputedStyle(n).visibility !== 'hidden' ? +getComputedStyle(n).opacity : 0, cap: getComputedStyle(f.querySelector('.demo-cap')).visibility}; }""")
        self.assertEqual(r, {"note": 0, "cap": "visible"})  # 멀리 둘 자리도 없으면 상자를 숨긴다(visibility)
        self.assertEqual(self.js(p, "() => document.querySelector('#d1 svg').getAttribute('viewBox')"), "0 0 810 450")  # 넓혀도 자리가 없으면 넓히지 않는다

    def test_below_note_overlaps_node_horizontally(self):  # 아래·위 상자는 현재 노드와 가로 범위가 겹치고, 겹침이 가장 큰 위치에 둔다
        body = MMD.replace("""flowchart TD
  A[주문 접수] --> B{한도 검증}
  B -->|예| C[체결]
  B -->|아니오| D[거부]""", "flowchart LR\n  P[체결 확정] --> Q[대금 계산] --> R[결제]")
        spec = [("가", "체결 내역을 확정합니다.", "P", None), ("나", "결제할 대금을 계산합니다.", "Q", None), ("다", "대금과 증권을 주고받습니다.", "R", None)]
        p = self.open(body, mmd_steps(spec))
        r = self.js(p, """() => { const f = document.getElementById('d1'), tl = f._rcTl, n = f.querySelector('svg .rc-note');
          return [0, 1, 2].map(i => { tl.seek('e' + i, false); const a = f.querySelector('[data-rc-active]').getBoundingClientRect(), b = n.getBoundingClientRect();
            return {apart: b.top >= a.bottom - 0.5 || b.bottom <= a.top + 0.5, ov: Math.min(a.right, b.right) - Math.max(a.left, b.left), w: Math.min(a.width, b.width)}; }); }""")
        self.assertTrue(any(s["apart"] for s in r), r)  # 적어도 한 단계는 아래·위에 놓인다
        for s in r:
            if s["apart"]:
                self.assertGreater(s["ov"], s["w"] - 1, r)  # 노드 폭이 상자보다 좁으면 노드 전체가 상자 가로 범위 안에 든다

    def test_far_note_with_lead_line(self):  # 넓혀도 48px 안에 자리가 없으면 가장 가까운 빈 자리에 상자를 두고 보조선으로 잇는다
        body = ('<figure id="d1" data-anim="구조"><svg viewBox="0 0 800 400" width="800" height="400">'
                '<rect id="wall" x="0" y="100" width="200" height="200" fill="none" stroke="currentColor"/>'
                '<rect id="a" x="60" y="180" width="80" height="40" fill="none" stroke="currentColor"/></svg></figure>')
        p = self.open(body, "RC.demo(document.getElementById('d1'),[{name:'가',text:'멀리 둡니다.',play:function(tl,$){$('a');}}]);")
        r = self.js(p, """() => { const f = document.getElementById('d1'); f._rcTl.seek('e0', false);
          const n = f.querySelector('svg .rc-note'), box = n.querySelector('rect').getBoundingClientRect(), ln = n.querySelector('line.rc-lead'),
                w = document.getElementById('wall').getBoundingClientRect(), a = document.getElementById('a').getBoundingClientRect();
          const col = k => { const d = document.createElement('i'); d.style.color = getComputedStyle(document.documentElement).getPropertyValue('--' + k); document.body.appendChild(d); const c = getComputedStyle(d).color; d.remove(); return c; };
          const lb = ln && ln.getBoundingClientRect(), cs = ln && getComputedStyle(ln);
          return {op: +getComputedStyle(n).opacity, cap: getComputedStyle(f.querySelector('.demo-cap')).visibility,
                  clear: box.left - w.right, gap: box.left - a.right, vb: f.querySelector('svg').getAttribute('viewBox'),
                  lead: ln ? {shown: cs.display !== 'none', stroke: cs.stroke, ink3: col('ink-3'), w: cs.strokeWidth,
                              x0: Math.round(lb.left), x1: Math.round(lb.right), ar: Math.round(a.right), bl: Math.round(box.left)} : null}; }""")
        self.assertEqual((r["op"], r["cap"], r["vb"]), (1, "hidden", "0 0 800 400"))
        self.assertGreaterEqual(r["clear"], 2)
        self.assertLess(r["gap"], 90)  # 벽 바로 너머의 가장 가까운 자리
        L = r["lead"]
        self.assertTrue(L and L["shown"], r)
        self.assertEqual((L["stroke"], L["w"]), (L["ink3"], "1px"))
        self.assertEqual((L["x0"], L["x1"]), (L["ar"], L["bl"]))  # 노드 경계에서 상자 경계까지 잇는다

    def test_lead_hidden_on_near_steps(self):  # 48px 안에 둔 단계에서는 보조선을 숨긴다
        p = self.open(SIDE, "RC.demo(document.getElementById('d1'),[{name:'가',text:'오른쪽에 둡니다.',play:function(tl,$){$('a');}}]);")
        r = self.js(p, """() => { const f = document.getElementById('d1'); f._rcTl.seek('e0', false);
          const ln = f.querySelector('svg .rc-note line.rc-lead'); return !ln || getComputedStyle(ln).display === 'none'; }""")
        self.assertTrue(r)

    def test_hidden_page_figure_gets_note_when_shown(self):
        body = f'<section class="page" id="p1"><p>첫 페이지</p></section><section class="page core" id="p2">{MMD_WIDE}</section>'
        p = self.open(body, mmd_steps(FLOW), paged=True)  # p1로 열려 figure는 숨은 상태에서 만들어진다
        self.js(p, "() => { showPage(1); scrollTo(0, 0); }")
        for s in self.judged(p):
            self.assertTrue(s["near"], s)


VB_JS = """id => { const s = document.querySelector('#' + id + ' svg');
  return {vb: s.getAttribute('viewBox'), mw: s.style.maxWidth, w: s.getAttribute('width'), h: s.getAttribute('height')}; }"""
VB_STEPS_JS = """id => { const f = document.getElementById(id), tl = f._rcTl, s = f.querySelector('svg'), out = [];
  tl.seek(0, false); out.push(s.getAttribute('viewBox'));
  Object.keys(tl.labels).filter(k => /^e\\d+$/.test(k)).forEach(k => { tl.seek(k, false); out.push(s.getAttribute('viewBox')); });
  tl.seek(0, false); return out; }"""
FLAT = """<figure id="d1" data-anim="구조"><svg viewBox="0 0 400 60" width="400" height="60">
<rect id="a" x="170" y="10" width="60" height="40" fill="none" stroke="currentColor"/></svg></figure>"""


class EngineWiden(EngineCase):
    """자리 없는 단계가 있으면 빌드할 때 viewBox를 한 번만 넓힌다."""

    def judged(self, p):
        r = self.js(p, "id => __c0.noteSteps(id)", "d1")
        return measure.note_steps(r["steps"], r["view"])

    def test_widen_once_for_narrow_mermaid(self):  # 220px 상자가 들어갈 폭이 없는 Mermaid 도식도 모든 단계에 상자를 둔다
        before = self.js(self.open_file("widen_plain.html", engine_doc(MMD, "")), VB_JS, "d1")
        p = self.open(MMD, mmd_steps(FLOW))
        after = self.js(p, VB_JS, "d1")
        for s in self.judged(p):
            self.assertTrue(s["near"] and s["visible"], s)
        b, a = [float(v) for v in before["vb"].split()], [float(v) for v in after["vb"].split()]
        self.assertNotEqual(a, b)
        self.assertTrue(a[0] <= b[0] and a[1] <= b[1] and a[0] + a[2] >= b[0] + b[2] and a[1] + a[3] >= b[1] + b[3], (before, after))
        self.assertAlmostEqual(float(after["mw"][:-2]) / a[2], float(before["mw"][:-2]) / b[2], places=3)  # 데스크톱 배율을 지킨다
        self.assertEqual(set(self.js(p, VB_STEPS_JS, "d1")), {after["vb"]})  # 첫 장면부터 끝까지 같은 viewBox

    def test_rewind_restores_widened_positions(self):  # 넓힌 뒤 정한 위치·글이 되감기에서도 그 단계 상태로 돌아온다
        p = self.open(MMD, mmd_steps(FLOW))
        r = self.js(p, """() => { const f = document.getElementById('d1'), tl = f._rcTl, n = f.querySelector('svg .rc-note');
          const st = k => { tl.seek(k, false); const b = n.getBoundingClientRect();
            return [Math.round(b.left), Math.round(b.top), Math.round(b.height), n.textContent.trim(), +getComputedStyle(n).opacity]; };
          const fwd = ['e0', 'e1', 'e2'].map(st), back = ['e2', 'e1', 'e0'].map(st).reverse(); tl.seek(0, false); return [fwd, back]; }""")
        self.assertEqual(r[0], r[1])
        self.assertEqual([s[3] for s in r[0]], [t for _, t, _, _ in FLOW])
        self.assertEqual(len({(s[0], s[1]) for s in r[0]}), 3, r[0])  # 단계마다 제 노드 옆으로 옮긴다

    def test_height_only_when_width_not_needed(self):  # 위아래로 넓혀 자리가 생기면 폭(배율)은 그대로 둔다
        p = self.open(FLAT, "RC.demo(document.getElementById('d1'),[{name:'가',text:'아래에 둡니다.',play:function(tl,$){$('a');}}]);")
        r = self.js(p, VB_JS, "d1")
        x, y, w, h = [float(v) for v in r["vb"].split()]
        self.assertEqual((x, w), (0, 400))
        self.assertTrue(60 < h < 110 and y <= 0 and y + h >= 60, r)
        self.assertAlmostEqual(float(r["h"]) / h, 1, places=3)  # 높이 속성도 같은 비율로 늘려 배율을 지킨다
        self.assertAlmostEqual(float(r["w"]) / w, 1, places=3)
        for s in self.judged(p):
            self.assertTrue(s["near"] and s["visible"], s)

    def test_no_widen_when_room(self):
        p = self.open(SIDE, "RC.demo(document.getElementById('d1'),[{name:'가',text:'오른쪽에 둡니다.',play:function(tl,$){$('a');}}]);")
        self.assertEqual(self.js(p, VB_JS, "d1"), {"vb": "0 0 600 300", "mw": "", "w": "600", "h": "300"})


class EnginePeep(EngineCase):
    def peeps(self, p, i):
        return self.js(p, """([i]) => { const f = document.getElementById('d1'); f._rcTl.seek('e' + i, false);
          return [...f.querySelectorAll('.rc-icon')].filter(g => +getComputedStyle(g).opacity > 0.05).map(g => g.dataset.rcPeep).sort(); }""", [i])

    def test_think_then_done(self):
        p = self.open(MMD_WIDE, mmd_steps(FLOW))
        self.assertEqual([self.peeps(p, i) for i in range(3)], [[], ["person"], ["person-done"]])

    def test_neg_step_after_diamond_fails(self):  # 판정 색은 이번 단계의 강조 색으로 정한다
        spec = [FLOW[0], ("시나리오 A · 검증", "한도를 넘습니다.", "B", None), ("시나리오 A · 거부", "주문을 거부합니다.", "D", "neg")]
        p = self.open(MMD_WIDE, mmd_steps(spec))
        self.assertEqual([self.peeps(p, i) for i in range(3)], [[], ["person"], ["person-fail"]])

    def test_neg_non_diamond_has_no_peep(self):
        spec = [("가", "거부합니다.", "D", "neg"), ("나", "접수합니다.", "A", None)]
        p = self.open(MMD_WIDE, mmd_steps(spec))
        self.assertEqual([self.peeps(p, i) for i in range(2)], [[], []])

    def test_author_icon_means_no_auto_peep(self):
        script = "RC.ready.then(function(){RC.icon(document.querySelector('#d1 svg'),'check',10,10);" + mmd_steps(FLOW) + "});"
        p = self.open(MMD_WIDE, script)
        self.assertEqual([g for i in range(3) for g in self.peeps(p, i) if g], [])

    def test_prev_and_reset_restore_state(self):  # '이전'·'처음부터' 뒤 설명 상자 글·현재 노드·스틱맨이 그 단계 상태다
        p = self.open(MMD_WIDE, mmd_steps(FLOW))
        r = self.js(p, """() => { const f = document.getElementById('d1'), b = f.querySelectorAll('.demo-ctl button');
          const st = () => ({note: f.querySelector('svg .rc-note').textContent.trim(),
            act: [...f.querySelectorAll('[data-rc-active]')].map(e => e.closest('g.node').id.replace(/.*flowchart-/, '').replace(/-\\d+$/, '')),
            peep: [...f.querySelectorAll('.rc-icon')].filter(g => +getComputedStyle(g).opacity > 0.05).map(g => g.dataset.rcPeep)});
          f._rcTl.seek('e2', false); b[0].click(); const one = st(); b[3].click(); const zero = st();
          return {one, zero: {act: zero.act, peep: zero.peep, op: +getComputedStyle(f.querySelector('svg .rc-note')).opacity}}; }""")
        self.assertEqual(r["one"], {"note": "한도 이내입니다.", "act": ["B"], "peep": ["person"]})
        self.assertEqual(r["zero"], {"act": [], "peep": [], "op": 0})

    def test_note_without_peep_room_drops_peep(self):  # 상자만 들어가고 스틱맨 칸이 없으면 상자만 두고 스틱맨은 두지 않는다
        # 마름모 B 오른쪽에 상자 하나만 들어갈 빈칸(폭 232, 높이 60)을 남기고 나머지를 직사각형으로 막는다
        block = """RC.ready.then(function(){var s=document.querySelector('#d1 svg'),inv=s.getScreenCTM().inverse(),
          n=[].filter.call(s.querySelectorAll('g.node'),function(g){return /-flowchart-B-\\d+$/.test(g.id);})[0].querySelector('polygon'),
          r=n.getBoundingClientRect(),p=new DOMPoint(r.left,r.top).matrixTransform(inv),q=new DOMPoint(r.right,r.bottom).matrixTransform(inv),
          m=(p.y+q.y)/2,W=3000,L=q.x+5,R=q.x+232,T=m-30,B=m+30;
          function bx(x,y,w,h){var e=document.createElementNS('http://www.w3.org/2000/svg','rect');
            e.setAttribute('x',x);e.setAttribute('y',y);e.setAttribute('width',w);e.setAttribute('height',h);
            e.setAttribute('fill','none');e.setAttribute('stroke','currentColor');s.appendChild(e);}
          bx(p.x-W,p.y-W,W-1,2*W);bx(p.x-W,p.y-W,2*W,W-1);bx(p.x-W,q.y+1,2*W,W);
          bx(L,p.y-W,W,T-p.y+W);bx(L,B,W,W);bx(R,T,W,B-T);"""
        script = block + "RC.demo(document.getElementById('d1'),[{name:'가',text:'한도를 봅니다.',play:function(tl,$){RC.fx.mark(tl,$('B'));}}]);});"
        p = self.open(MMD_WIDE, script)
        r = self.js(p, """() => { const f = document.getElementById('d1'); f._rcTl.seek('e0', false);
          return {note: +getComputedStyle(f.querySelector('svg .rc-note')).opacity,
                  peep: [...f.querySelectorAll('.rc-icon')].filter(g => +getComputedStyle(g).opacity > 0.05).length}; }""")
        self.assertEqual(r, {"note": 1, "peep": 0})


# 자막 높이가 바뀔 때 브라우저의 스크롤 앵커링이 scrollY를 옮기지 않도록 끈다. 엔진이 옮긴 스크롤만 본다
TALL = """<style>html{overflow-anchor:none}</style><div style="height:300px"></div><figure id="d1" data-anim="구조"><svg viewBox="0 0 400 1600" width="400" height="1600">
<rect id="top" x="20" y="20" width="100" height="40" fill="none" stroke="currentColor"/>
<rect id="bot" x="20" y="1500" width="100" height="40" fill="none" stroke="currentColor"/></svg></figure><div style="height:2000px"></div>"""
TALL_JS = ("RC.demo(document.getElementById('d1'),[{name:'가',text:'위 상자입니다.',play:function(tl,$){tl.to($('top'),{strokeWidth:2,duration:0.3});}},"
           "{name:'나',text:'아래 상자입니다.',play:function(tl,$){tl.to($('bot'),{strokeWidth:2,duration:0.3});}}]);")


THREE = TALL.replace('<rect id="bot"', '<rect id="mid" x="20" y="800" width="100" height="40" fill="none" stroke="currentColor"/>\n<rect id="bot"')
THREE_JS = ("RC.demo(document.getElementById('d1'),["
            + ",".join("{name:'%s',text:'%s 상자입니다.',play:function(tl,$){tl.to($('%s'),{strokeWidth:2,duration:0.3});}}" % (n, n, k)
                       for n, k in (("가", "top"), ("나", "mid"), ("다", "bot"))) + "]);")


class EngineScroll(EngineCase):
    def test_next_scrolls_only_to_target_step(self):  # '다음'이 단계 시작으로 먼저 옮길 때 앞 단계로는 스크롤하지 않는다
        p = self.open(THREE, THREE_JS)
        r = self.js(p, """() => { scrollTo(0, 300); const f = document.getElementById('d1'), tl = f._rcTl, calls = [];
          const orig = window.scrollBy; window.scrollBy = function (o) { calls.push(o.top); };
          tl.seek(tl.labels.e0 + 0.01, false);  // 2단계 연출이 막 시작된 상태(단계 사이 띄움 안)
          f.querySelectorAll('.demo-ctl button')[2].click(); tl.seek(tl.labels.e2, false);
          window.scrollBy = orig; return calls.length; }""")
        self.assertEqual(r, 1)

    def test_scrolls_when_figure_on_screen(self):
        p = self.open(TALL, TALL_JS)
        self.assertEqual(self.js(p, "() => scrollY"), 0)  # 문서를 열 때는 스크롤하지 않는다
        r = self.js(p, "async () => { scrollTo(0, 300); await __c0.toStep('d1', 0); await __c0.toStep('d1', 1);"
                       " const b = document.getElementById('bot').getBoundingClientRect(); return [b.top, b.bottom, innerHeight]; }")
        self.assertTrue(0 <= r[0] and r[1] <= r[2], r)

    def test_no_scroll_when_figure_off_screen(self):
        p = self.open(TALL, TALL_JS)
        r = self.js(p, "async () => { scrollTo(0, 3500); const y = scrollY; const f = document.getElementById('d1');"
                       " f._rcTl.seek('e1', false); f._rcTl.seek('e0', false); await new Promise(r => setTimeout(r, 400)); return [y, scrollY]; }")
        self.assertEqual(r[0], r[1])


WIDE = """<figure id="d1" data-anim="구조"><figcaption><span class="t">넓은 무대</span></figcaption>
<svg viewBox="0 0 820 200" width="100%"><text x="10" y="100" font-size="12">작은 글자</text>
<rect id="a" x="300" y="80" width="80" height="40" fill="none" stroke="currentColor"/></svg><p class="src">자료: 시험</p></figure>"""


class EngineFit(EngineCase):
    def test_390_min_width_scroll_box(self):
        p = self.open(WIDE, "", width=390)
        lay = self.js(p, "() => __c0.layout()")
        self.assertTrue(all(f["px"] >= 11 for f in lay["svgFonts"]), lay["svgFonts"])
        self.assertLessEqual(lay["scrollWidth"], lay["width"])
        self.assertTrue(self.js(p, "() => document.querySelector('#d1 svg').parentElement.classList.contains('rc-scroll')"))

    def test_animated_note_text_at_390(self):  # 자동 설명 상자 글도 390 폭에서 11px 이상이다. MMD는 220px 상자가 들어갈 폭이 없어 MMD_WIDE를 쓴다
        p = self.open(MMD_WIDE, mmd_steps(FLOW), width=390)
        self.assertTrue(self.js(p, "() => !!document.querySelector('#d1 svg .rc-note')"))
        fonts = self.js(p, "id => __c0.svgFontSteps(id)", "d1")
        self.assertTrue(all(f["px"] >= 11 for f in fonts), [f for f in fonts if f["px"] < 11][:5])

    def test_hidden_page_skipped_then_fitted(self):
        body = f'<section class="page" id="p1"><p>첫 페이지</p></section><section class="page core" id="p2">{WIDE}</section>'
        p = self.open(body, "", width=390, paged=True)
        self.assertEqual(self.js(p, "() => document.querySelector('#d1 svg').style.minWidth"), "")
        r = self.js(p, "async () => { showPage(1); await new Promise(r => setTimeout(r, 300)); return document.querySelector('#d1 svg').style.minWidth; }")
        self.assertTrue(r.endswith("px") and float(r[:-2]) > 358, r)

    def test_print_releases_min_width(self):
        p = self.open(WIDE, "", width=390)
        p.emulate_media(media="print")
        r = self.js(p, "() => { const s = document.querySelector('#d1 svg'); return [getComputedStyle(s).minWidth, getComputedStyle(s.parentElement).overflowX]; }")
        self.assertEqual(r, ["0px", "visible"])

    CUE = """() => { const b = document.querySelector('#d1 .rc-scroll'); if (!b) return null;
      const s = getComputedStyle(b, '::before'); return [s.content, s.fontSize, s.color, s.paddingBottom]; }"""

    def test_scroll_cue_when_wider_than_box(self):  # 도식이 스크롤 상자보다 넓으면 넓은 표와 같은 글자 모양의 단서를 상자 위에 보인다
        p = self.open(WIDE, "", width=390)
        ink3 = self.js(p, "() => { const d = document.createElement('i'); d.style.color = 'var(--ink-3)'; document.body.appendChild(d); const c = getComputedStyle(d).color; d.remove(); return c; }")
        r = self.js(p, self.CUE)
        self.assertEqual(r, ['"도식이 화면보다 넓으면 옆으로 밀어 볼 수 있습니다"', "12.5px", ink3, "4px"])
        p.emulate_media(media="print")
        self.assertEqual(self.js(p, self.CUE)[0], "none")  # 인쇄에서는 숨긴다

    def test_scroll_cue_on_static_mermaid(self):  # 애니메이션이 아닌 Mermaid 도식도 같은 단서를 받는다
        p = self.open(MMD_WIDE.replace(' data-anim="구조"', ''), "", width=390)
        r = self.js(p, "() => { const b = document.querySelector('#d1 .rc-scroll'); return b && [b.scrollWidth > b.clientWidth, getComputedStyle(b, '::before').content]; }")
        self.assertEqual(r, [True, '"도식이 화면보다 넓으면 옆으로 밀어 볼 수 있습니다"'])

    def test_no_scroll_cue_when_svg_fits(self):  # 스크롤 상자가 남아도 도식이 들어맞으면 단서를 보이지 않는다
        p = self.open(WIDE.replace("0 0 820 200", "0 0 500 200").replace('x="300"', 'x="200"'), "", width=390)  # 700 폭에서는 글자가 11px을 넘는다
        p.set_viewport_size({"width": 700, "height": 900})
        r = self.js(p, "async () => { await new Promise(r => setTimeout(r, 300)); const b = document.querySelector('#d1 .rc-scroll'); "
                       "return [b.scrollWidth <= b.clientWidth, getComputedStyle(b, '::before').content]; }")
        self.assertEqual(r, [True, "none"])


CHART = '<figure><div class="viz" id="c1"></div></figure>'


class EngineChart(EngineCase):
    def option(self, series):
        js = ("window.ch=RC.chart(document.getElementById('c1'),{grid:{left:40,right:16,top:20,bottom:28},"
              "xAxis:{type:'category',data:['1월','2월','3월']},yAxis:{type:'value'},series:%s});" % series)
        p = self.open(CHART, js)
        return self.js(p, "() => { const o = ch.getOption(); return {s: o.series.map(s => [s.symbol, !!(s.endLabel && s.endLabel.show)]), right: o.grid[0].right}; }")

    def test_two_lines_get_end_labels_and_shapes(self):
        r = self.option("[{name:'가',type:'line',data:[1,2,3]},{name:'나',type:'line',data:[3,2,1]}]")
        self.assertEqual([x[1] for x in r["s"]], [True, True])
        self.assertNotEqual(r["s"][0][0], r["s"][1][0])
        self.assertGreaterEqual(r["right"], 72)

    def test_single_line_unchanged(self):
        r = self.option("[{name:'가',type:'bar',data:[1,2,3]},{name:'나',type:'line',data:[3,2,1]}]")
        self.assertEqual(r["s"][1][1], False)
        self.assertEqual(r["right"], 16)


    def test_long_lines_keep_symbol_unset(self):  # 점이 30개를 넘는 선은 표식 표시를 ECharts 기본값에 맡긴다
        js = ("var x=[],y1=[],y2=[];for(var i=0;i<100;i++){x.push(i);y1.push(i);y2.push(100-i);}"
              "window.opt={xAxis:{type:'category',data:x},yAxis:{type:'value'},series:[{name:'가',type:'line',data:y1},{name:'나',type:'line',data:y2}]};"
              "window.opt2={xAxis:{type:'category',data:[1,2,3]},yAxis:{type:'value'},series:[{name:'가',type:'line',data:[1,2,3]},{name:'나',type:'line',data:[3,2,1]}]};"
              "RC.chart(document.getElementById('c1'),opt);RC.chart(document.getElementById('c2'),opt2);")
        p = self.open('<figure><div class="viz" id="c1"></div><div class="viz" id="c2"></div></figure>', js)
        r = self.js(p, "() => [opt.series.map(s => [s.showSymbol === undefined, !!s.symbol, !!(s.endLabel && s.endLabel.show)]), opt2.series.map(s => s.showSymbol)]")
        self.assertEqual(r, [[[True, True, True], [True, True, True]], [True, True]])

    def test_single_series_object(self):  # series를 배열 아닌 객체 하나로 줘도 그린다
        js = "window.ch=RC.chart(document.getElementById('c1'),{series:{type:'pie',data:[{name:'가',value:1},{name:'나',value:2}]}});"
        p = self.open(CHART, js)
        self.assertEqual(self.js(p, "() => ch && ch.getOption().tooltip[0].trigger"), "item")

    def test_pie_scalar_radius_and_narrow_box(self):  # 반지름을 하나만 줘도, 상자가 210px보다 좁아도 파이를 그린다
        js = ("RC.chart(document.getElementById('c1'),{series:[{type:'pie',radius:'60%',data:[{name:'유가증권시장',value:58},{name:'코스닥시장',value:35}]}]});"
              "window.c2=RC.chart(document.getElementById('c2'),{series:[{type:'pie',radius:['40%','60%'],data:[{name:'가',value:1},{name:'나',value:2}]}]});")
        p = self.open('<figure><div class="viz" id="c1"></div><div class="viz" id="c2" style="width:180px"></div></figure>', js, width=390)
        r = self.js(p, """() => ['c1', 'c2'].map(id => [...document.querySelectorAll('#' + id + ' svg path')].filter(e => { const q = e.getBoundingClientRect(); return q.width > 5 && q.height > 5; }).length)""")
        self.assertTrue(all(n >= 2 for n in r), r)  # 조각 둘이 보인다
        self.assertTrue(all(float(v[:-1]) > 0 for v in self.js(p, "() => c2.getOption().series[0].radius")))

    def test_pie_labels_not_truncated_at_390(self):  # 좁은 화면에서도 파이 이름표를 '…'로 줄이지 않고 화면 안에 둔다. 작성자 formatter는 둔다
        js = ("window.opt={legend:{top:0,left:0},series:[{name:'시장별 비중',type:'pie',"
              "radius:['45%','70%'],label:{formatter:'{b} {d}%'},data:[{name:'유가증권시장',value:58},{name:'코스닥시장',value:35},{name:'코넥스시장',value:7}]}]};"
              "window.ch=RC.chart(document.getElementById('c1'),opt);")
        body = f'<section class="page" id="p1"><p>첫 페이지</p></section><section class="page core" id="p2">{CHART}</section>'
        p = self.open(body, js, width=390, page="p2", paged=True)  # 숨은 페이지에서 만든 차트가 보일 때 견본 장면처럼 '…'가 생겼다
        r = self.js(p, """() => { const ts = [...document.querySelectorAll('#c1 svg text')];
          return {fmt: [opt.series[0].label.formatter, opt.series[0].radius.join()], dots: ts.filter(t => /…|\.\.\./.test(t.textContent)).map(t => t.textContent),
                  pct: ts.map(t => t.textContent).join('').split('%').length - 1, whole: ts.filter(t => t.textContent === '유가증권시장').length,
                  out: ts.filter(t => { const q = t.getBoundingClientRect(); return q.width && (q.left < 0 || q.right > innerWidth); }).map(t => t.textContent)}; }""")
        self.assertEqual(r["fmt"], ["{b} {d}%", "45%,70%"])  # 문서가 넘긴 옵션은 바꾸지 않는다
        self.assertEqual(r["dots"], [])  # ECharts는 줄인 글자를 '...'로 그린다
        self.assertEqual(r["pct"], 3)     # 이름표 셋이 모두 그려진다(줄을 바꾸면 '%'는 한 번씩 나온다)
        self.assertEqual(r["out"], [])
        self.assertEqual(r["whole"], 2)   # 범례와 이름표 모두 이름을 낱말 중간에서 끊지 않는다
        p.set_viewport_size({"width": 1280, "height": 900})  # 넓어지면 작성자 반지름과 이름표로 돌아간다
        r = self.js(p, "async () => { await new Promise(r => setTimeout(r, 300)); const s = ch.getOption().series[0]; return [s.radius.join(), s.label.formatter]; }")
        self.assertEqual(r, ["45%,70%", "{b} {d}%"])


class SampleSelfCheck(EngineCase):
    def check(self, name, page, fid):
        p = self.open_file(name, (ROOT / "tests" / name).read_text(encoding="utf-8"), page=page)
        p.set_default_timeout(300_000)
        return p.evaluate("id => RC.check(id)", fid)

    def test_sample_anim_and_viz_pass(self):
        for name, page, fid in (("sample-anim.html", "p2", "d-shift"), ("sample-anim.html", "p3", "d-rule"),
                                ("sample-viz.html", "p4", "d-order"), ("sample-viz.html", "p5", "d-mmd")):
            r = self.check(name, page, fid)
            self.assertTrue(r.get("pass"), (fid, r))

    def test_baseline_bars_and_axes_in_sample(self):
        html = (ROOT / "tests" / "sample-anim.html").read_text(encoding="utf-8")
        for bar in ("b-a0", "b-b0", "b-c0"):
            self.assertIn(f'id="{bar}"', html)
        self.assertIn(">bp<", html)
        self.assertIn(">개월<", html)

    def test_managed_blocks_match_engine(self):  # 엔진을 고친 뒤 견본 관리 블록을 다시 채웠는지 본다
        js = (ROOT / "report-charts.js").read_text(encoding="utf-8")
        for name in ("sample-anim.html", "sample-viz.html"):
            self.assertIn(js, (ROOT / "tests" / name).read_text(encoding="utf-8"), name)


if __name__ == "__main__":
    unittest.main()
