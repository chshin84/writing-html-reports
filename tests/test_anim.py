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

    def test_active_moves_at_step_end(self):  # data-rc-active는 단계 끝 시각에 옮긴다
        p = self.open(MMD, mmd_steps(FLOW))
        r = self.js(p, """() => { const f = document.getElementById('d1'), tl = f._rcTl;
          const id = () => [...f.querySelectorAll('[data-rc-active]')].map(e => e.closest('g.node').id.replace(/.*flowchart-/, '').replace(/-\\d+$/, ''));
          tl.seek(tl.labels.e0 + 0.05, false); const mid = id(); tl.seek('e1', false); const e1 = id(); tl.seek('e2', false); return [mid, e1, id()]; }""")
        self.assertEqual(r, [["A"], ["B"], ["C"]])  # 단계 끝마다 정확히 하나



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
          return {note: n ? +getComputedStyle(n).opacity : 0, cap: getComputedStyle(f.querySelector('.demo-cap')).visibility}; }""")
        self.assertEqual(r, {"note": 0, "cap": "visible"})

    def test_hidden_page_figure_gets_note_when_shown(self):
        body = f'<section class="page" id="p1"><p>첫 페이지</p></section><section class="page core" id="p2">{MMD_WIDE}</section>'
        p = self.open(body, mmd_steps(FLOW), paged=True)  # p1로 열려 figure는 숨은 상태에서 만들어진다
        self.js(p, "() => { showPage(1); scrollTo(0, 0); }")
        for s in self.judged(p):
            self.assertTrue(s["near"], s)


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
        self.assertEqual(self.js(p, "() => document.querySelector('#d1 svg').parentElement.className"), "rc-scroll")

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
