# C1 애니메이션 엔진 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 엔진(`report-charts.js`)과 애니메이션 스타일(`report-demo.css`)을 고쳐 단계 체류 시간, 1단계 시작, 두 재생 방식, 시나리오 묶기, 현재 노드 옆 설명 상자, 판정 스틱맨, 화면 안 유지, 390 폭 도식 글자, 선 차트 이름표를 구현하고, 소유 견본 결함과 `시각화.md`를 고친다.

**Architecture:** `RC.demo`는 단계마다 하위 타임라인(`sub`)을 만들어 작성자의 `play(sub, $)`에 넘긴다. 하위 타임라인은 주 타임라인(`fig._rcTl`)에 차례로 붙는다. 엔진은 단계마다 주 타임라인을 처음부터 다시 옮겨 그 단계 구간의 화면 상태를 모은다. 모은 상태로 글자 수 n과 글 완료 시각, 현재 노드, 설명 상자 위치를 정하고 재생 방식에 맞춰 단계 길이를 정한다. 조작 버튼과 화면 안 스크롤은 주 타임라인의 갱신 콜백이 처리한다.

**Tech Stack:** 브라우저 JavaScript(GSAP 3.15.0·Mermaid 11.17.2·ECharts 6.1.0 CDN), Python 3 unittest, Python Playwright 1.63.0 헤드리스 Chromium.

**Spec:** `docs/superpowers/specs/2026-10-04-c1-animation-engine-design.md` (상위 설계 `docs/superpowers/specs/2026-10-04-report-quality-architecture-design.md`, 측정 도구 설계 `docs/superpowers/specs/2026-10-04-c0-eval-harness-design.md`)

## 용어

- **고정 견본:** `bench/fixed/`의 HTML 사본이다. 호출 코드를 바꾸지 않고 `eval/rebuild.py`로 현재 엔진을 넣어 다시 빌드한다.
- **C0 하네스:** 판정 도구다. `eval/gates.py`가 기계 판정을, `eval/shoot.py`가 장면을, `eval/probe.js`(문서 안 `__c0` 함수)가 화면 수집을 맡는다.
- **n:** 한 단계에서 figure 안에 새로 보이게 된 글의 글자 수다. 공백은 빼고 숫자 묶음은 1자로 센다. 자막과 설명 상자 글과 숫자 칸을 모두 센다.
- **note-near·active-visible:** C0 하네스의 판정 항목이다. 앞은 설명 상자가 현재 노드에서 48px 안에 있고 무대 요소와 겹치지 않는지, 뒤는 두 요소가 1280×800 창 안에 있는지 본다.
- **04-rules 흐름도:** 고정 견본 `bench/fixed/04-rules.html`의 `d-flow`다. Mermaid 흐름도이고 28단계, 시나리오 묶음 5개다.
- **상자 묶음:** 자동 설명 상자와 그 옆 스틱맨을 함께 감싼 직사각형이다. 엔진은 이 직사각형 단위로 위치를 찾는다.

## Global Constraints

- 고칠 수 있는 파일은 `report-charts.js`, `report-demo.css`, `report-peeps.js`, `tools/build-peeps.py`, `checks/anim.py`, `시각화.md`, `tests/sample-anim.html`, `tests/sample-viz.html`, `tests/test_anim.py`, `tests/test_peeps.py`, 이 plan과 그 리뷰 기록이다. 그 밖의 파일은 읽기만 하고, 고쳐야 하면 작업을 멈추고 보고한다.
- 기존 RC 함수(`RC.demo`, `RC.fx.*`, `RC.icon`, `RC.note`, `RC.focus`, `RC.check`, `RC.chart`)의 인자는 그대로 동작해야 한다. 새 기능은 선택 인자로만 추가한다. `RC.check`의 판정 규칙은 바꾸지 않는다.
- `.demo-ctl button`은 이전·재생·다음·처음부터 순서를 유지한다. 재생이 끝나면 재생 버튼의 글이 '재생'으로 돌아간다.
- 자동 재생의 각 단계는 글이 다 나온 뒤 1초 + n÷8초 이상, 그 값 + 3초 이하로 머문다.
- 단계 넘김의 단계 연출은 0.4~2.5초다. 자동 재생의 머무는 시간은 타임라인 안에 두고 `gsap.delayedCall`로 만들지 않는다.
- 재생 방식은 주소의 `?rc-mode=auto|step`으로 고르고, 인자가 없으면 상수 `DEFAULT_MODE = 'step'`을 쓴다. figure에 `data-rc-mode`를 단다.
- 자동 설명 상자는 `g.rc-note`이고 폭은 220px이다. 단계의 `text`만 넣고 바로 보인다. figure에서 `RC.note`를 한 번도 만들지 않았을 때만 둔다.
- 자동 설명 상자는 현재 노드 경계에서 48px 안에 둔다. 무대 요소와 겹치지 않고 SVG 표시 범위 안에 드는 쪽을 오른쪽·왼쪽·아래·위 순서로 고르고, 네 쪽 모두 없으면 두지 않고 자막을 보인다.
- 자동 스틱맨은 `g.rc-icon`이고 Mermaid 마름모 노드의 고민(`person`)과 판정(`person-done`·`person-fail`)에만 쓴다. figure에서 `RC.icon`을 한 번도 만들지 않았을 때만 둔다. `person-guide`는 자동으로 두지 않는다.
- 색은 토큰 이름(`tok('accent')`, `RC.color('s1')`)으로만 참조한다.
- 고정 견본의 단계 수나 노드 이름에 기대는 분기를 두지 않는다.
- 문서·주석·커밋 메시지는 한국어 문어체다. 커밋 메시지 끝에 `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`와 `Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F` 두 줄을 붙인다.
- 시험 명령은 워크트리 루트(`D:/projects/Structure/whr-c1`)에서 `python -B -m unittest discover -s tests`다. 화면 시험은 Python Playwright 헤드리스 Chromium만 쓰고 Playwright MCP는 쓰지 않는다.
- 판정 실패를 고치는 시도는 실패 항목마다 3번까지 한다. 세 번째에도 실패하면 원인과 결정할 것을 리포트에 적고 다음 단계로 간다.

## Review Focus

- **숨은 페이지의 figure:** 처음에 숨은 페이지에 있던 애니메이션도 그 페이지로 넘기면 설명 상자가 노드 옆에 있어야 한다. Task 5의 숨은 페이지 시험으로 확인한다.
- **같은 요소를 여러 단계에서 다루는 문서의 되감기:** 한 아이콘을 두 단계에서 `RC.fx.pop`하는 문서에서 '이전'을 누르면 그 단계의 모습으로 돌아가야 한다. Task 2의 되감기 시험으로 확인한다.
- **'이전'·'처음부터' 뒤의 상태:** 설명 상자 글과 `data-rc-active`와 스틱맨이 돌아간 단계의 상태와 같아야 한다. Task 6의 되감기 시험으로 확인한다.
- **재생 중 버튼 연타:** 재생 중에 버튼을 연달아 눌러도 두 단계가 동시에 진행되지 않아야 한다. Task 1의 연타 시험으로 확인한다.
- **인쇄:** 인쇄할 때 스크롤 상자와 최소 폭이 풀려야 한다. Task 8의 인쇄 매체 시험으로 확인한다.

## 설계 결정

**하위 타임라인.** 단계마다 `gsap.timeline()`을 따로 만들어 `play`에 넘긴다. 단계 넘김에서 연출이 2.43초를 넘으면 하위 타임라인의 `timeScale`로 2.43초에 맞추고, 0.43초보다 짧으면 빈 구간으로 늘린다. 사이 띄움 0.02초를 더하면 단계 구간은 0.45~2.45초다. 이 구조에서 작성자의 `at` 인자는 단계 안 시각으로 해석된다. 숫자 절대 위치(`tl.to(e, v, 3.2)`)는 단계 시작 기준이 되고, 앞 단계에서 만든 라벨은 뒤 단계에서 찾을 수 없다. 고정 견본에는 둘 다 없고, `시각화.md`에 이 규칙을 적는다.

**처음부터 다시 옮기는 표본 수집.** 엔진은 단계마다 주 타임라인을 시각 0으로 되감은 뒤 그 단계 직전까지 앞으로 옮기고, 그다음 단계 구간을 0.05초 간격으로 옮긴다. `RC.fx.pop`·`RC.fx.draw`는 빌드할 때 타임라인 밖에서 `gsap.set`을 실행한다. 되감기를 거치면 그 설정이 끼어도 앞 단계 트윈이 다시 렌더되어 화면 상태가 맞는다. 빌드가 끝나면 시각 0으로 되감아 처음 상태를 만든다. 빌드 중 seek 때문에 작성자의 `tl.call` 콜백은 여러 번 실행된다.

**n의 계산.** 보이는 글의 판정은 C0 하네스의 정의를 계산된 스타일로 옮긴 것이다. 엔진은 `display`, `visibility`, 조상의 `clip-path`, figure까지의 불투명도 곱, 글자색 알파를 본다. 면적 1px² 조건은 숨은 페이지에서 잴 수 없어 뺀다. 자막은 타임라인 밖 글이므로 단계 끝에 설명 상자가 보이지 않을 때만 자막 글자 수를 더한다. 머무는 시간에는 측정 간격을 흡수하는 여유 0.3초를 더한다.

**처음 상태.** 문서를 열면 타임라인 시각 0, 단계 표시 `0/N`, 자막 빈 글이다. '처음부터'도 이 상태로 돌아가고 시나리오 범위를 '전체'로 되돌린다. 그래서 처음 누른 '재생'이나 '다음'이 1단계 연출부터 보인다.

**현재 노드 표시.** `data-rc-active`는 단계 끝 시각에 그 단계의 현재 노드로 옮긴다. 강조 표시는 닫힌 도형(`rect`·`polygon`·`circle`·`ellipse`)에만 준다. 글자와 선에 채움을 입히면 글과 선이 흐려지기 때문이다. 작성자가 그 단계에 그 도형에 준 속성은 덮어쓰지 않는다. 작성자가 인라인 스타일이나 속성으로 준 채움(`none` 제외)도 덮어쓰지 않는다. 작성자가 `tl.to`로 테두리 색을 준 적이 있는 도형은 지나온 노드가 되어도 그 색을 유지하고 두께만 1.5px로 줄인다. 작성자가 색을 준 적이 없는 도형만 보조 강조색으로 바꾼다.

**판정 스틱맨.** 판정 스틱맨의 색은 spec대로 이번 단계의 강조 색만 본다. 이번 단계에서 작성자가 현재 노드에 준 테두리 색이 `neg` 토큰 값이면 `person-fail`, 아니면 `person-done`이다. 스틱맨은 자동 설명 상자 옆에 두므로, 자동 설명 상자가 없는 figure나 상자를 두지 못한 단계에는 고민 스틱맨을 두지 않는다.

**시나리오 선택.** spec은 시나리오를 고르면 첫 단계로 옮기고 그 시나리오 끝에서 재생을 멈춘다고 정한다. 이 문장을 '고르면 그 시나리오를 처음부터 재생한다'로 해석한다. 멈출 지점을 정한 문장이 재생을 전제하기 때문이다.

**설명 상자 위치와 RC.check의 일치.** 장애물은 단계 구간을 0.25초 간격으로 옮기며 모은 합집합이다. 상자가 단계 시작부터 보이므로, 초점 틀이 움직이는 도중의 위치도 피해야 하기 때문이다. Mermaid 무대의 선은 C0 하네스처럼 선 위 점으로 보고, 직접 그린 무대의 선은 `RC.check`처럼 경계 상자를 1.5px 넓혀 본다. 위치 계산은 따로 `try`로 감싸고, 예외가 나면 그 단계에 상자를 두지 않는다.

**숨은 페이지의 위치 계산.** figure가 `display:none` 조상 안에 있으면, 단계를 만드는 동안만 그 조상을 화면 밖 절대 위치로 펼쳤다가 같은 작업 안에서 되돌린다. 한 작업 안에서 끝나므로 화면에 그려지지 않는다. 펼친 뒤에도 무대에 화면 좌표가 없으면 위치 계산을 건너뛴다.

**스틱맨 크기와 방향.** 자동 스틱맨은 56×56으로 그리고 노드에서 먼 쪽에 둔다. 오른쪽 위치면 상자 오른쪽, 왼쪽 위치면 상자 왼쪽, 위·아래 위치면 상자 오른쪽이다.

리포트의 '상위 설계·spec과 다르게 정한 점'에는 다음 결정을 적는다. 현재 노드 강조를 닫힌 도형으로 한정한 것, 자동 스틱맨을 자동 설명 상자에 묶은 것, 시나리오 선택을 재생으로 해석한 것, 보임 판정에서 면적 조건을 뺀 것이다.

## 파일 구조

- `report-charts.js`는 엔진 원본이다. 문서에 관리 블록으로 들어가는 한 파일이므로 나누지 않고, 새 코드를 기능 단위 함수로 둔다.
- `report-demo.css`에는 자막 숨김(`.demo-cap.rc-off`)과 시나리오 줄(`.demo-scen`)과 스크롤 상자(`.rc-scroll`) 규칙을 더한다.
- `tests/test_anim.py`에는 엔진 화면 시험 클래스(`Engine*`, `SampleSelfCheck`)를 더한다. 화면 시험은 `eval/harness.py`의 `Session`, `eval/probe.js`의 `__c0`, `eval/measure.py`를 읽기 전용으로 가져다 쓴다.
- `tests/sample-anim.html`에서는 전후 전환의 기준선 막대와 손익 선 그래프의 축을 고친다.
- `tests/sample-viz.html`에서는 호출 코드를 바꾸지 않고 관리 블록만 다시 채운다.
- `시각화.md`에서는 표시 시간, 재생 방식, 자동 설명 상자, 스틱맨, 시나리오 묶기, 390 폭, 선 차트, RC 함수 표를 고친다.
- `checks/anim.py`, `report-peeps.js`, `tools/build-peeps.py`, `tests/test_peeps.py`는 바꾸지 않는다.

## 시험 도우미

Task 1이 `tests/test_anim.py` 맨 앞 import 아래에 다음 도우미를 추가한다. 뒤 Task는 이 이름을 그대로 쓴다.

```python
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
```

`measure.source_facts`는 관리 블록 밖의 `RC.demo(` 호출만 센다. `self.sess.open`은 C0 수집 함수(`__c0.dwellSamples`, `step1`, `stepAnim`, `noteSteps`, `layout`, `toStep`, `ends`, `svgFontSteps`)를 문서에 넣는다.

---

### Task 1: 재생 방식과 1단계 시작

**Files:**
- Modify: `report-charts.js` (211~218행의 글 규칙 주석과 상수, `RC.demo` 전체)
- Modify: `report-demo.css`
- Test: `tests/test_anim.py`

**Interfaces:**
- Consumes: 없음
- Produces: 상수 `DEFAULT_MODE`, `STEP_MIN = 0.43`, `STEP_MAX = 2.43`, `HOLD_PAD = 0.3`; 함수 `playMode()`, `holdFor(n)`, `textRules(L, s, fig)`; 전역 `demoStep`(빌드 중 단계 기록 `{last, mark}`); `RC.demo` 안의 `info[i] = {start, active, noteOn, n, done, pause, color, diamond, note, think}`와 함수 `show(i)`, `sync()`, `go(i, animate)`, `play()`, `stop()`, `seekTo(t)`, `rewindTo(t)`. 뒤 Task는 아래 골격의 `/* Task N */` 주석 위치에 코드를 넣는다.

- [ ] **Step 1: 시험 도우미와 실패하는 시험을 쓴다**

`tests/test_anim.py`에 위 '시험 도우미'와 다음 시험을 넣는다.

```python
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
```

- [ ] **Step 2: 시험이 실패하는지 확인한다**

Run: `python -B -m unittest tests.test_anim.EngineMode -v`
Expected: `test_default_mode_is_step_and_attribute`가 `None != 'step'`으로, `test_initial_time_zero_and_buttons`가 시각이 0이 아니어서 FAIL.

- [ ] **Step 3: 엔진을 고친다**

`report-charts.js`의 글 규칙 상수(216~218행)를 다음으로 바꾼다.

```js
  var TEXT_MAX = 1, CHAR_MAX = 30;
  function chars(s) { return String(s).replace(/\d[\d,.]*/g, '#').replace(/\s/g, '').length; }
  function holdFor(n) { return 1 + n / 8; } // 글이 다 나온 뒤 머무는 시간의 하한(초). 상한은 이 값 + 3초다
  var HOLD_PAD = 0.3; // 측정 간격(0.05초)과 반올림을 흡수하는 여유
  var DEFAULT_MODE = 'step'; // 주소에 ?rc-mode가 없을 때의 재생 방식. L1이 실측 뒤 바꿀 수 있다
  var STEP_MIN = 0.43, STEP_MAX = 2.43; // 단계 넘김의 단계 연출 길이. 사이 띄움 0.02초를 더하면 0.45~2.45초다
  function playMode() { var m = /[?&]rc-mode=(auto|step)(?:&|$)/.exec(location.search); return m ? m[1] : DEFAULT_MODE; }
  var demoStep = null; // RC.demo가 단계를 만드는 동안 $로 마지막에 조회한 요소(last)와 mark·spot이 받은 요소(mark)를 적는다
```

211~215행 주석의 '표시 시간' 문장을 "자동 재생에서는 단계의 글이 다 나온 뒤 1초 + 글자 수 ÷ 8초 이상 머문다. 글자 수에는 자막과 설명 상자와 숫자 칸이 모두 든다"로 바꾼다.

기존 체류 계산(356~372행의 `holds`·`need`)과 `tick` 함수와 마지막 `go(0, false)`는 지운다. 356~368행의 글 규칙 검사는 다음 함수로 옮긴다.

```js
  function textRules(L, s, fig) { // 글 등장 1초 규칙과 설명 상자 30자 규칙(작성자 글만 센다)
    if (!L.beats.length) return;
    L.beats.sort(function (a, b) { return a[0] - b[0]; });
    var merged = [L.beats[0].slice()];
    L.beats.slice(1).forEach(function (b) { // 이어지거나 겹치는 글 등장은 한 덩어리로 본다
      var m = merged[merged.length - 1];
      if (b[0] <= m[1] + 0.05) m[1] = Math.max(m[1], b[1]); else merged.push(b.slice());
    });
    merged.forEach(function (m) {
      if (m[1] - m[0] > TEXT_MAX + 0.001) issue('[' + fig.id + '] "' + s.name + '" 단계의 글 등장이 1초를 넘는다(' + (m[1] - m[0]).toFixed(2) + '초)');
    });
    var n = 0; L.fin.forEach(function (v) { n += chars(v); });
    if (n > CHAR_MAX) issue('[' + fig.id + '] "' + s.name + '" 단계의 설명이 30자를 넘는다(' + n + '자)');
  }
```

`RC.demo`의 `if (typeof gsap === 'undefined')` 줄 앞에 `var mode = playMode(); fig.dataset.rcMode = mode;`를 넣고, `RC.ready.then(function () { … })` 본문을 다음 골격으로 바꾼다.

```js
    RC.ready.then(function () {
      var find = function (name) {
        var hit = fig.querySelector('[id="' + name + '"]');
        if (hit) return hit;
        var re = new RegExp('-flowchart-' + name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '-\\d+$');
        var nodes = fig.querySelectorAll('g.node');
        for (var i = 0; i < nodes.length; i++) {
          if (re.test(nodes[i].id)) return nodes[i].querySelector('rect, polygon, path') || nodes[i];
        }
        return null;
      };
      var rec = { last: null, mark: null };
      var $ = function (name) { var e = find(name); if (e && demoStep === rec) rec.last = e; return e; };
      var tl = gsap.timeline({ paused: true }), ends = [], info = [], auto = mode === 'auto';
      function rewindTo(t) { tl.seek(0, false); tl.seek(t, false); } // 처음부터 다시 옮겨 빌드 중 gsap.set이 끼어도 화면 상태를 맞춘다
      /* Task 2: capPrev */
      /* Task 4: memo, prevActive */
      /* Task 5: stage, restore, box, vb */
      /* Task 6: usePeep, hideNext, prevIt, NEG */
      try {
        steps.forEach(function (s, i) {
          var start = tl.duration(), pre = Math.max(0, start - 0.01), sub = gsap.timeline();
          stepLog = { beats: [], fin: new Map() };
          rec.last = rec.mark = null; demoStep = rec;
          try { s.play(sub, $); } finally { demoStep = null; }
          var L = stepLog; stepLog = null;
          textRules(L, s, fig);
          tl.add(sub, start);
          if (!auto && sub.duration() > STEP_MAX) sub.timeScale(sub.duration() / STEP_MAX);
          var it = { start: start, active: rec.mark || rec.last, noteOn: false, n: 0, done: start, pause: 0.3,
                     color: undefined, diamond: false, note: null, think: null };
          /* Task 4: it.color, it.diamond, styleNodes */
          /* Task 6: 앞 단계 스틱맨 숨김과 판정 스틱맨 */
          var animEnd = Math.max(sub.endTime(), tl.duration());
          rewindTo(pre);
          /* Task 5: 자동 상자 위치와 it.noteOn */
          /* Task 6: 고민 스틱맨 */
          /* Task 2: 글 표본으로 it.n·it.done 계산 */
          var end = auto ? Math.max(animEnd, it.done + holdFor(it.n) + HOLD_PAD) : Math.max(animEnd, start + STEP_MIN);
          if (end > tl.duration()) tl.to({}, { duration: end - tl.duration() });
          tl.addLabel('e' + i, end); ends.push(end);
          it.pause = Math.max(0.3, it.done + holdFor(it.n) + HOLD_PAD - end);
          info.push(it);
          tl.to({}, { duration: 0.02 }); // 다음 단계의 즉시 설정이 이 단계의 끝 시각과 겹쳐 미리 실행되지 않게 띄운다
        });
      } catch (e) { // 단계 코드가 틀리면 동작하지 않는 버튼 대신 단계 설명 목록을 보인다
        console.error('RC.demo', e);
        tl.kill();
        fig.classList.add('demo-static');
        /* Task 5: restore() */
        return;
      }
      /* Task 5: restore() */
      rewindTo(0); // 빌드를 끝낸 화면을 처음 상태로 맞춘다
      var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches, last = steps.length - 1;
      var at = null, tw = null, timer = null, quiet = true, pend = null, from = 0, to = last, saved = -1, activeEl = null;
      function stepAt(t) { if (t <= 1e-6) return -1; var i = 0; while (i < last && ends[i] < t - 1e-6) i++; return i; }
      function startOf(i) { return i > 0 ? ends[i - 1] : 0; }
      function label(i) { return i < 0 ? '0/' + steps.length : (i + 1) + '/' + steps.length; } // Task 3이 시나리오 표시로 바꾼다
      function show(i) {
        at = i;
        cnt.textContent = label(i);
        cap.textContent = i < 0 ? '' : steps[i].name + ': ' + steps[i].text;
        cap.classList.toggle('rc-off', i >= 0 && info[i].noteOn);
        bPrev.disabled = i < 0;
        bNext.disabled = i === last;
        pend = quiet || i < 0 ? null : i;
      }
      function sync() {
        var t = tl.time(), i = stepAt(t);
        if (i !== at) show(i);
        /* Task 4: data-rc-active 옮기기 */
        /* Task 7: pend 처리(keepInView) */
      }
      function stop() {
        tl.pause();
        if (tw) { tw.kill(); tw = null; }
        if (timer) { timer.kill(); timer = null; }
        bPlay.textContent = '재생';
      }
      function seekTo(t) { tl.seek(t, false); sync(); } // seek의 두 번째 인자 false: 바로 옮겨도 글자 효과(onUpdate)가 끝 상태를 그린다
      function go(i, animate) {
        stop();
        if (i < 0) { seekTo(0); return; }
        if (animate && !reduce) { seekTo(startOf(i)); tw = tl.tweenTo(ends[i], { onComplete: function () { tw = null; } }); }
        else seekTo(ends[i]);
      }
      function play() {
        if (at >= to || at < from - 1) seekTo(startOf(from));
        bPlay.textContent = '일시정지';
        if (auto && !reduce) { tw = tl.tweenTo(ends[to], { onComplete: stop }); return; }
        (function next() { // 단계 넘김: 한 단계를 재생하고 체류 시간 규칙만큼 쉰 뒤 다음 단계로 간다
          var i = at + 1;
          var rest = function () {
            if (i >= to) { stop(); return; }
            timer = gsap.delayedCall(reduce ? holdFor(info[i].n) + HOLD_PAD : info[i].pause, next);
          };
          if (reduce) { seekTo(ends[i]); rest(); }
          else tw = tl.tweenTo(ends[i], { onComplete: function () { tw = null; rest(); } });
        })();
      }
      tl.eventCallback('onUpdate', sync);
      bPrev.onclick = function () { go(at - 1, false); };
      bNext.onclick = function () { go(Math.min(last, at + 1), true); };
      bReset.onclick = function () { /* Task 3: whole() */ go(-1); };
      bPlay.onclick = function () { if (tw || timer || tl.isActive()) stop(); else play(); };
      /* Task 3: 시나리오 버튼 */
      new ResizeObserver(function () { if (fig.clientWidth === 0) stop(); }).observe(fig); // 다른 페이지로 넘기면 멈춘다
      addEventListener('beforeprint', function () { saved = at; stop(); quiet = true; seekTo(ends[last]); });
      addEventListener('afterprint', function () { go(saved, false); quiet = false; });
      seekTo(0); quiet = false;
      fig._rcTl = tl; fig.dataset.rcReady = '1'; // C0 하네스와 RC.check가 쓴다
      /* Task 8: watchFit(fig) */
    });
```

`report-demo.css`의 `.demo-cap` 줄 뒤에 다음을 추가한다.

```css
.demo-cap{min-height:1.5em}
.demo-cap.rc-off{visibility:hidden}
```

- [ ] **Step 4: 시험이 통과하는지 확인한다**

Run: `python -B -m unittest tests.test_anim -v`
Expected: `EngineMode`의 모든 시험과 기존 시험이 PASS.

- [ ] **Step 5: 커밋한다**

```bash
git add report-charts.js report-demo.css tests/test_anim.py
git commit -m "C1: 재생 방식 두 가지와 1단계 시작을 엔진에 넣는다" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F"
```

### Task 2: 자동 재생의 체류 시간

**Files:**
- Modify: `report-charts.js` (새 함수 `ownText`·`seen`·`textPool`·`texts`·`sameTexts`·`sampleStep`, 골격의 `/* Task 2 */` 위치)
- Test: `tests/test_anim.py`

**Interfaces:**
- Consumes: Task 1의 단계 루프, `rewindTo`, `holdFor`, `HOLD_PAD`, `chars`
- Produces: `ownText(e) → 글`, `seen(e, fig) → bool`, `textPool(fig) → 요소 배열`, `texts(fig, pool) → Map<요소, 글>`, `sampleStep(tl, fig, from, to, before, pool) → {done, n}`, `it.n`, `it.done`

- [ ] **Step 1: 실패하는 시험을 쓴다**

```python
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
```

- [ ] **Step 2: 시험이 실패하는지 확인한다**

Run: `python -B -m unittest tests.test_anim.EngineDwell -v`
Expected: `test_caption_only_steps_meet_rule`과 `test_stage_text_counts`가 FAIL. Task 1에서는 `it.n`이 0이라 머무는 시간이 1.3초뿐이다.

- [ ] **Step 3: 엔진을 고친다**

`RC.color` 정의 앞(차트 코드보다 앞)에 다음 함수를 둔다. Task 5와 Task 8도 이 함수를 쓴다. `seen`은 `fig` 위 조상을 보지 않는다. 숨은 페이지(`display:none` 조상)에서도 표본을 모으기 위해서다.

```js
  var SKIP_TXT = /^(SCRIPT|STYLE|TITLE|NOSCRIPT)$/;
  function ownText(e) {
    var s = '';
    for (var i = 0; i < e.childNodes.length; i++) if (e.childNodes[i].nodeType === 3) s += e.childNodes[i].nodeValue;
    return s.replace(/\s+/g, ' ').trim();
  }
  function seen(e, fig) { // C0 하네스의 보임 판정을 계산된 스타일로 옮긴 것이다. 숨은 페이지에서도 쓰도록 면적 조건은 뺀다
    var o = 1, c0 = getComputedStyle(e);
    if (c0.visibility === 'hidden' || c0.visibility === 'collapse') return false;
    for (var n = e; n && n !== fig.parentElement; n = n.parentElement) {
      var c = n === e ? c0 : getComputedStyle(n);
      if (c.display === 'none' || (c.clipPath && c.clipPath !== 'none')) return false;
      o *= +c.opacity;
    }
    if (o <= 0.05) return false;
    var col = c0[e instanceof SVGElement ? 'fill' : 'color'];
    return !/^(transparent|none)$|,\s*0\)$/.test(col);
  }
  function textPool(fig) { // 표본마다 다시 찾지 않도록 글을 가질 수 있는 요소를 단계마다 한 번 모은다. 조작 줄·단계 목록·자막·시나리오 줄은 뺀다
    return [].filter.call(fig.querySelectorAll('*'), function (e) {
      return !SKIP_TXT.test(e.tagName) && !e.closest('.demo-ctl, .demo-steps, .demo-cap, .demo-scen, defs');
    });
  }
  function texts(fig, pool) { // figure 안 보이는 글 요소와 그 글
    var m = new Map();
    pool.forEach(function (e) { var t = ownText(e); if (t && seen(e, fig)) m.set(e, t); });
    return m;
  }
  function sameTexts(a, b) {
    if (a.size !== b.size) return false;
    var ok = true;
    a.forEach(function (v, k) { if (b.get(k) !== v) ok = false; });
    return ok;
  }
  function sampleStep(tl, fig, from, to, before, pool) { // from~to를 0.05초 간격으로 옮기며 글이 마지막으로 바뀐 시각(done)과 새 글자 수(n)를 구한다
    var prev = before, done = from, ts = [];
    for (var t = from; t < to - 1e-9; t += 0.05) ts.push(t);
    ts.push(to);
    ts.forEach(function (t) { tl.seek(t, false); var cur = texts(fig, pool); if (!sameTexts(prev, cur)) done = t; prev = cur; });
    var n = 0;
    prev.forEach(function (v, e) { if (before.get(e) !== v) n += chars(v); });
    return { done: done, n: n };
  }
```

골격의 `/* Task 2: capPrev */` 위치에 `var capPrev = null;`을 넣고, `/* Task 2: 글 표본 … */` 위치에 다음을 넣는다.

```js
          var pool = textPool(fig);
          rewindTo(pre);
          var before = texts(fig, pool), smp = sampleStep(tl, fig, start, animEnd, before, pool), capText = s.name + ': ' + s.text;
          it.n = smp.n; it.done = smp.done;
          if (!it.noteOn && capPrev !== capText) { it.n += chars(capText); it.done = Math.max(it.done, start + 0.05); } // 자막은 타임라인 밖 글이라 따로 센다
          capPrev = it.noteOn ? null : capText;
          if (auto && animEnd - it.done > holdFor(it.n) + 3) console.warn('RC.demo: [' + fig.id + '] "' + s.name + '" 단계는 글이 끝난 뒤 연출이 길어 체류 상한을 넘는다');
```

- [ ] **Step 4: 시험이 통과하는지 확인한다**

Run: `python -B -m unittest tests.test_anim -v`
Expected: 모두 PASS.

- [ ] **Step 5: 커밋한다**

```bash
git add report-charts.js tests/test_anim.py
git commit -m "C1: 자동 재생 체류 시간을 1초 + n÷8초 규칙으로 맞춘다" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F"
```

### Task 3: 시나리오 묶기

**Files:**
- Modify: `report-charts.js` (조작 줄 생성부, `label`, 골격의 `/* Task 3 */` 위치, 새 함수 `scenarioGroups`)
- Modify: `report-demo.css`
- Test: `tests/test_anim.py`

**Interfaces:**
- Consumes: Task 1의 `show`, `play`, `stop`, `go`, `seekTo`, `startOf`, `from`, `to`
- Produces: `scenarioGroups(steps) → {of: [묶음 또는 null], list: [{name, from, to}]}`, `whole()`, `.demo-scen` 줄(버튼 글은 '전체'와 묶음 이름)

- [ ] **Step 1: 실패하는 시험을 쓴다**

```python
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
```

두 시험은 2단계 끝으로 옮긴 뒤 '이전'을 눌러 1단계 끝에서 단계 표시를 읽는다.

- [ ] **Step 2: 시험이 실패하는지 확인한다**

Run: `python -B -m unittest tests.test_anim.EngineScenario -v`
Expected: `test_counter_and_row`가 `'1/13' != '시나리오 A 1/7'`로 FAIL.

- [ ] **Step 3: 엔진과 CSS를 고친다**

`RC.demo` 앞에 다음 함수를 둔다.

```js
  var SCEN = /^(시나리오 [^·]+?) · (.+)$/;
  function scenarioGroups(steps) { // '시나리오 X · Y' 단계를 이어진 구간끼리 X로 묶는다. 다른 이름은 묶지 않는다
    var of = [], list = [];
    steps.forEach(function (s, i) {
      var m = SCEN.exec(s.name || ''), g = list[list.length - 1];
      if (!m) { of.push(null); return; }
      if (!g || g.name !== m[1] || g.to !== i - 1) { g = { name: m[1], from: i, to: i }; list.push(g); } else g.to = i;
      of.push(g);
    });
    return { of: of, list: list };
  }
```

`RC.demo`의 `var src = …`와 `[ctl, cap, list].forEach(…)` 두 줄을 다음으로 바꾼다.

```js
    var groups = scenarioGroups(steps), scen = null;
    if (groups.list.length >= 2 && steps.length > 12) { // 조작 줄 아래 별도 줄. 조작 버튼 순서를 바꾸지 않는다
      scen = el('div', 'demo-scen');
      [null].concat(groups.list).forEach(function (g) {
        var b = el('button', g ? null : 'on', g ? g.name : '전체');
        b.type = 'button'; b._rcGroup = g; scen.appendChild(b);
      });
    }
    var src = fig.querySelector('.src');
    [ctl, scen, cap, list].forEach(function (n) { if (n) fig.insertBefore(n, src); });
```

골격의 `label`을 바꾼다.

```js
      function label(i) {
        if (i < 0) return '0/' + steps.length;
        var g = groups.of[i];
        return g ? g.name + ' ' + (i - g.from + 1) + '/' + (g.to - g.from + 1) : (i + 1) + '/' + steps.length;
      }
```

골격의 `/* Task 3: whole() */` 위치에 `whole();`을, `/* Task 3: 시나리오 버튼 */` 위치에 다음을 넣는다. `function whole`은 함수 선언이라 `bReset.onclick`에서 먼저 써도 동작한다.

```js
      function whole() { // 시나리오 범위를 '전체'로 되돌린다
        from = 0; to = last;
        if (scen) [].forEach.call(scen.children, function (x) { x.classList.toggle('on', !x._rcGroup); });
      }
      if (scen) [].forEach.call(scen.children, function (b) {
        b.onclick = function () { // 시나리오를 고르면 첫 단계부터 재생해 그 시나리오 끝에서 멈춘다. '전체'는 처음 상태로 돌아간다
          var g = b._rcGroup;
          if (!g) { whole(); go(-1); return; }
          [].forEach.call(scen.children, function (x) { x.classList.toggle('on', x === b); });
          from = g.from; to = g.to;
          stop(); seekTo(startOf(from)); play();
        };
      });
```

`report-demo.css`에 다음 세 줄을 추가한다.

```css
.demo-scen{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px;font-size:13px}
.demo-scen button{font:inherit;font-size:13px;background:var(--paper);color:var(--ink-2);border:1px solid var(--hair);padding:2px 10px;cursor:pointer}
.demo-scen button.on{color:var(--ink);border-color:var(--ink-3)}
```

기존 정적 목록 숨김 줄과 인쇄 블록은 다음으로 바꾼다.

```css
.demo-static .demo-ctl,.demo-static .demo-cap,.demo-static .demo-scen{display:none}
@media print{
  .demo-ctl,.demo-cap,.demo-scen{display:none}
  .demo-steps{display:block}
}
```

- [ ] **Step 4: 시험이 통과하는지 확인한다**

Run: `python -B -m unittest tests.test_anim -v`
Expected: 모두 PASS.

- [ ] **Step 5: 커밋한다**

```bash
git add report-charts.js report-demo.css tests/test_anim.py
git commit -m "C1: '시나리오 X · Y' 단계를 묶어 단계 표시와 시나리오 선택에 쓴다" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F"
```

### Task 4: 현재 노드 결정과 표시

**Files:**
- Modify: `report-charts.js` (`RC.fx.mark`, `RC.fx.spot`, 골격의 `/* Task 4 */` 위치, 새 함수 `authorSet`·`closedShape`·`mmdShape`·`ownFill`·`styleNodes`)
- Test: `tests/test_anim.py`

**Interfaces:**
- Consumes: Task 1의 `demoStep`, `rec`, `it`, `sync`, `ends`, `info`
- Produces: `it.active`, `it.color`(작성자가 이번 단계에 현재 노드에 준 테두리 색 또는 `undefined`), `it.diamond`(Mermaid 마름모 여부), `authorSet(sub, e, keys) → {키: 값} 또는 null`, `mmdShape(e) → bool`, `data-rc-active` 속성

- [ ] **Step 1: 실패하는 시험을 쓴다**

```python
class EngineActive(EngineCase):
    def active_at(self, p, i):
        return self.js(p, """([i]) => { const f = document.getElementById('d1'); f._rcTl.seek('e' + i, false);
          return [...f.querySelectorAll('[data-rc-active]')].map(e => (e.closest('g.node') || e).id.replace(/.*flowchart-/, '').replace(/-\\d+$/, '')); }""", [i])

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

    def test_active_moves_at_step_end(self):  # data-rc-active는 단계 끝 시각에 옮긴다
        p = self.open(MMD, mmd_steps(FLOW))
        r = self.js(p, """() => { const f = document.getElementById('d1'), tl = f._rcTl;
          const id = () => [...f.querySelectorAll('[data-rc-active]')].map(e => e.closest('g.node').id.replace(/.*flowchart-/, '').replace(/-\\d+$/, ''));
          tl.seek(tl.labels.e0 + 0.05, false); const mid = id(); tl.seek('e1', false); return [mid, id()]; }""")
        self.assertEqual(r, [["A"], ["B"]])
```

- [ ] **Step 2: 시험이 실패하는지 확인한다**

Run: `python -B -m unittest tests.test_anim.EngineActive -v`
Expected: `data-rc-active`가 없어 `[] != ['B']`로 FAIL.

- [ ] **Step 3: 엔진을 고친다**

`RC.fx.mark`가 받은 요소를 적는다.

```js
    mark: function (tl, e, color, at) {
      if (demoStep) demoStep.mark = e && e.length != null && !e.tagName ? e[e.length - 1] : e;
      return tl.to(e, { stroke: tok(color || 'accent'), strokeWidth: 2, duration: 0.3 }, at);
    },
```

`spot`의 `var c = …` 줄 앞에 `if (demoStep) demoStep.mark = e;`를 넣는다.

`RC.demo` 앞에 다음 함수를 둔다. `memo.author`는 엔진 표시를 정한 뒤에 갱신하므로, 같은 단계에서 작성자가 처음 색을 준 노드는 `authorSet`이 막는다.

```js
  function authorSet(sub, e, keys) { // 이번 단계에서 작성자가 요소 e에 준 속성 값. 없으면 null
    if (!e) return null;
    var hit = null;
    sub.getChildren(true, true, false).forEach(function (t) {
      if (t.targets().indexOf(e) < 0) return;
      keys.forEach(function (k) {
        var v = t.vars[k] != null ? t.vars[k] : t.vars.attr && t.vars.attr[k];
        if (v != null) { hit = hit || {}; hit[k] = v; }
      });
    });
    return hit;
  }
  function closedShape(e) { return !!(e && /^(rect|polygon|circle|ellipse)$/i.test(e.tagName) && !e.closest('.rc-note, .rc-icon, .rc-focus')); }
  function mmdShape(e) { return !!(e && e.closest && e.closest('pre.mermaid svg g.node')); }
  function ownFill(e) { var f = e.style.fill || e.getAttribute('fill'); return !!f && f !== 'none'; } // 작성자가 인라인 스타일·속성으로 준 채움
  function styleNodes(tl, sub, cur, prev, at, memo) { // 닫힌 도형에 현재·지나온 노드 표시를 한다. 작성자가 준 색은 덮어쓰지 않는다
    var A = tok('accent'), K = ['stroke', 'strokeWidth', 'fill', 'fillOpacity'];
    if (closedShape(prev) && prev !== cur) {
      var s = authorSet(sub, prev, K) || {}, v = { duration: 0.3 };
      if (s.stroke == null && !memo.author.has(prev)) v.stroke = tok('accent-2'); // 작성자가 tl.to로 색을 준 적이 있으면 그 색을 둔다
      if (s.strokeWidth == null) v.strokeWidth = 1.5;
      if (s.fill == null && s.fillOpacity == null && memo.fill.has(prev)) { v.fill = memo.fill.get(prev).fill; v.fillOpacity = memo.fill.get(prev).op; }
      tl.to(prev, v, at);
    }
    if (closedShape(cur)) {
      var c = authorSet(sub, cur, K) || {}, w = { duration: 0.3 };
      if (c.stroke == null && !memo.author.has(cur)) w.stroke = A;
      if (c.strokeWidth == null) w.strokeWidth = 2;
      if (c.fill == null && c.fillOpacity == null && !ownFill(cur)) {
        if (!memo.fill.has(cur)) { var cs = getComputedStyle(cur); memo.fill.set(cur, { fill: cs.fill, op: +cs.fillOpacity }); }
        w.fill = A; w.fillOpacity = 0.08;
      }
      tl.to(cur, w, at);
    }
    sub.getChildren(true, true, false).forEach(function (t) { // 작성자가 tl.to·tl.set으로 테두리 색을 준 요소를 기억한다
      var v = t.vars.stroke != null ? t.vars.stroke : t.vars.attr && t.vars.attr.stroke;
      if (v != null) t.targets().forEach(function (e) { memo.author.add(e); });
    });
  }
```

골격의 `/* Task 4: memo, prevActive */` 위치에 `var memo = { author: new Set(), fill: new Map() }, prevActive = null;`을 넣고, `/* Task 4: it.color … */` 위치에 다음을 넣는다.

```js
          var set = authorSet(sub, it.active, ['stroke']);
          it.color = set ? set.stroke : undefined;
          it.diamond = mmdShape(it.active) && it.active.tagName.toLowerCase() === 'polygon';
          styleNodes(tl, sub, it.active, prevActive, start, memo);
          prevActive = it.active;
```

골격 `sync`의 `/* Task 4 */` 위치에 다음을 넣는다. 단계 i 안에서는 앞 단계의 현재 노드를 두고, 단계 끝 시각에 이번 단계의 현재 노드로 옮긴다.

```js
        var a = i < 0 ? null : t >= ends[i] - 1e-6 ? info[i].active : i > 0 ? info[i - 1].active : null;
        if (a !== activeEl) {
          if (activeEl) activeEl.removeAttribute('data-rc-active');
          activeEl = a;
          if (a) a.setAttribute('data-rc-active', '');
        }
```

- [ ] **Step 4: 시험이 통과하는지 확인한다**

Run: `python -B -m unittest tests.test_anim -v`
Expected: 모두 PASS.

- [ ] **Step 5: 커밋한다**

```bash
git add report-charts.js tests/test_anim.py
git commit -m "C1: 단계마다 현재 노드를 정해 data-rc-active와 강조 표시를 단다" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F"
```

### Task 5: 자동 설명 상자와 자막 숨김

**Files:**
- Modify: `report-charts.js` (`RC.note`, `RC.icon`, 골격의 `/* Task 5 */` 위치, 새 함수 `own`·`peepEl`·`reveal`·`autoNote`·`noteHeight`·`userBox`·`obstacles`·`freeAt`·`placeUnit`·`showNote`)
- Test: `tests/test_anim.py`

**Interfaces:**
- Consumes: Task 1~4의 `it.active`, `it.diamond`, `animEnd`, `start`, `pre`, `rewindTo`; Task 2의 `seen`
- Produces: `authored = {note: WeakSet<figure>, icon: WeakSet<figure>}`, `peepEl(svg, name, x, y, size) → g.rc-icon`, `placeUnit(a, nh, peepW, obs, vb) → {side, u, note: {x, y}, peep: {x, y}} 또는 null`, `it.note`, `it.noteOn`, 상수 `NOTE_W = 220`, `GAP = 8`, `PEEP = 56`

- [ ] **Step 1: 실패하는 시험을 쓴다**

```python
SIDE = """<figure id="d1" data-anim="구조"><svg viewBox="0 0 600 300" width="600" height="300">
<rect id="a" x="40" y="120" width="100" height="40" fill="none" stroke="currentColor"/></svg></figure>"""


class EngineNote(EngineCase):
    def judged(self, p):
        r = self.js(p, "id => __c0.noteSteps(id)", "d1")
        return measure.note_steps(r["steps"], r["view"])

    def test_auto_note_beside_node_and_caption_hidden(self):
        p = self.open(MMD, mmd_steps(FLOW))
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
        body = f'<section class="page" id="p1"><p>첫 페이지</p></section><section class="page core" id="p2">{MMD}</section>'
        p = self.open(body, mmd_steps(FLOW), paged=True)  # p1로 열려 figure는 숨은 상태에서 만들어진다
        self.js(p, "() => { showPage(1); scrollTo(0, 0); }")
        for s in self.judged(p):
            self.assertTrue(s["near"], s)
```

- [ ] **Step 2: 시험이 실패하는지 확인한다**

Run: `python -B -m unittest tests.test_anim.EngineNote -v`
Expected: `test_auto_note_beside_node_and_caption_hidden`이 '보이는 설명 상자 없음'으로 FAIL.

- [ ] **Step 3: 엔진을 고친다**

`var SVGNS` 줄 아래에 다음을 둔다.

```js
  var authored = { note: new WeakSet(), icon: new WeakSet() }; // 작성자가 RC.note·RC.icon을 만든 figure. 자동 상자·스틱맨을 두지 않는다
  function own(kind, svg) { var f = svg && svg.closest && svg.closest('figure'); if (f) authored[kind].add(f); }
  function peepEl(svg, name, x, y, size) { // 스틱맨 그림. (x, y)는 중심, size는 한 변이다. 처음에는 투명하다
    var P = window.RC_PEEPS, body = P.figures[name].replace(/class="pk"/g, 'fill="' + tok('ink') + '"').replace(/class="pw"/g, 'fill="' + tok('paper') + '"');
    var src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="' + P.viewBox + '">' + body + '</svg>');
    var pg = sv('g', { 'class': 'rc-icon', opacity: 0, 'data-rc-peep': name }, svg);
    sv('image', { x: x - size / 2, y: y - size / 2, width: size, height: size, href: src }, pg);
    return pg;
  }
```

`RC.icon`의 첫 줄을 `own('icon', svg); var P = window.RC_PEEPS;`로 바꾸고, 스틱맨 분기 본문을 `return peepEl(svg, name, x, y, 80);`로 바꾼다. `RC.note`의 첫 줄 뒤에 `own('note', svg);`을 넣는다.

`RC.demo` 앞에 자동 상자 함수를 둔다.

```js
  var NOTE_W = 220, GAP = 8, PEEP = 56;
  function reveal(fig) { // 숨은 페이지의 figure를 계산하는 동안만 화면 밖에 펼친다. 되돌리는 함수를 돌려준다
    var undo = [];
    for (var k = 0; k < 6 && !fig.getClientRects().length; k++) {
      var n = fig;
      while (n && n !== document.body && getComputedStyle(n).display !== 'none') n = n.parentElement;
      if (!n || n === document.body) break;
      undo.push([n, n.getAttribute('style')]);
      var w = (n.parentElement && n.parentElement.clientWidth) || document.documentElement.clientWidth;
      n.style.cssText += ';display:block !important;position:absolute !important;left:-99999px !important;top:0 !important;width:' + w + 'px !important';
    }
    return function () { undo.reverse().forEach(function (u) { if (u[1] == null) u[0].removeAttribute('style'); else u[0].setAttribute('style', u[1]); }); };
  }
  function autoNote(svg) { // 자동 설명 상자 하나를 만들어 단계마다 글과 위치만 바꾼다
    var g = sv('g', { 'class': 'rc-note', opacity: 0 }, svg);
    var rect = sv('rect', { x: 0, y: 0, width: NOTE_W, height: 30, style: 'fill:' + tok('paper') + ';stroke:' + tok('hair') }, g);
    var fo = sv('foreignObject', { x: 0, y: 0, width: NOTE_W, height: 30 }, g);
    var div = document.createElement('div'), t = document.createElement('span');
    div.style.cssText = 'padding:6px 8px;font:12.5px/1.45 var(--sans);color:var(--ink);word-break:keep-all';
    div.appendChild(t); fo.appendChild(div);
    return { g: g, rect: rect, fo: fo, div: div, t: t, text: '' };
  }
  function noteHeight(box, text) {
    box.t.textContent = text;
    var h = box.div.offsetHeight;
    box.t.textContent = box.text;
    return h ? Math.ceil(h) + 1 : 18 * Math.ceil(chars(text) * 13 / 204) + 13;
  }
  function userBox(inv, e) { // 화면 경계 상자를 무대 좌표로 바꾼다
    var r = e.getBoundingClientRect(), a = new DOMPoint(r.left, r.top).matrixTransform(inv), b = new DOMPoint(r.right, r.bottom).matrixTransform(inv);
    return { l: Math.min(a.x, b.x), t: Math.min(a.y, b.y), r: Math.max(a.x, b.x), b: Math.max(a.y, b.y) };
  }
  var STAGE_GEOM = 'text, rect, polygon, circle, ellipse, path, line, polyline, foreignObject, image';
  function obstacles(svg, fig, into) { // 무대 요소(도형·글자·간선·간선 이름표·보이는 아이콘)의 상자와 간선 점을 무대 좌표로 into에 더한다
    var inv = svg.getScreenCTM().inverse(), dots = !!svg.closest('pre.mermaid'); // Mermaid 선은 점으로(C0 하네스), 직접 그린 무대의 선은 경계 상자로(RC.check) 본다
    [].forEach.call(svg.querySelectorAll(STAGE_GEOM), function (e) {
      if (e.closest('.rc-note, defs, marker, clipPath, mask, pattern') || !seen(e, fig)) return;
      var c = getComputedStyle(e), tag = e.tagName.toLowerCase();
      var line = tag === 'line' || tag === 'polyline' || (tag === 'path' && (c.fill === 'none' || /,\s*0\)$/.test(c.fill)));
      if (line && dots && e.getTotalLength) {
        var m = e.getScreenCTM(), L = e.getTotalLength();
        for (var s = 0; s <= L; s += 3) { var p = e.getPointAtLength(s); into.pts.push(new DOMPoint(p.x, p.y).matrixTransform(m).matrixTransform(inv)); }
        return;
      }
      var b = userBox(inv, e), k = line ? 1.5 : 0;
      if ((b.r - b.l) * (b.b - b.t) >= 1 || line) into.boxes.push({ l: b.l - k, t: b.t - k, r: b.r + k, b: b.b + k });
    });
    return into;
  }
  function freeAt(u, obs) {
    var l = u.l - 3, t = u.t - 3, r = u.r + 3, b = u.b + 3;
    for (var i = 0; i < obs.boxes.length; i++) { var o = obs.boxes[i]; if (Math.min(r, o.r) - Math.max(l, o.l) > 0.5 && Math.min(b, o.b) - Math.max(t, o.t) > 0.5) return false; }
    for (var k = 0; k < obs.pts.length; k++) { var p = obs.pts[k]; if (p.x >= l && p.x <= r && p.y >= t && p.y <= b) return false; }
    return true;
  }
  function placeUnit(a, nh, peepW, obs, vb) { // 상자 묶음(상자 폭 220, 높이 nh, 스틱맨 칸 폭 peepW)의 위치를 오른쪽·왼쪽·아래·위 순서로 찾는다. 표시 범위 vb 안에서만 찾는다
    var w = NOTE_W + peepW, h = Math.max(nh, peepW ? PEEP : 0);
    function sweep(lo, hi, mid) { var v = [mid]; for (var d = 6; mid - d >= lo || mid + d <= hi; d += 6) { if (mid + d <= hi) v.push(mid + d); if (mid - d >= lo) v.push(mid - d); } return v; }
    function at(side, ux, uy, nx) { return { side: side, u: { l: ux, t: uy, r: ux + w, b: uy + h }, note: { x: nx, y: uy }, peep: { x: nx === ux ? ux + NOTE_W + 4 : ux, y: uy } }; }
    var ys = sweep(a.t - h + 10, a.b - 10, (a.t + a.b - h) / 2), xs = sweep(a.l - NOTE_W + 10, a.r - 10, (a.l + a.r - NOTE_W) / 2);
    var sides = [
      ys.map(function (y) { return at(0, a.r + GAP, y, a.r + GAP); }),                   // 오른쪽: 노드 | 상자 | 스틱맨
      ys.map(function (y) { return at(1, a.l - GAP - w, y, a.l - GAP - NOTE_W); }),      // 왼쪽: 스틱맨 | 상자 | 노드
      xs.map(function (x) { return at(2, x, a.b + GAP, x); }),                          // 아래: 상자 | 스틱맨
      xs.map(function (x) { return at(3, x, a.t - GAP - h, x); })                       // 위
    ];
    for (var s = 0; s < 4; s++) for (var i = 0; i < sides[s].length; i++) {
      var c = sides[s][i];
      if (c.u.l >= vb.l && c.u.t >= vb.t && c.u.r <= vb.r && c.u.b <= vb.b && freeAt(c.u, obs)) return c;
    }
    return null;
  }
  function showNote(tl, box, at, p, text, h) { // 단계 시작에 자동 상자의 글과 위치를 바꾼다. p가 null이면 숨긴다
    if (!p) { tl.set(box.g, { opacity: 0 }, at); return; }
    var prev = box.text, o = { v: 0 };
    tl.set(box.g, { x: p.x, y: p.y, opacity: 1 }, at);
    tl.set([box.rect, box.fo], { attr: { height: h } }, at);
    tl.to(o, { v: 1, duration: 0.01, onUpdate: function () { box.t.textContent = o.v > 0 ? text : prev; } }, at); // 되감으면 앞 단계 글로 돌아간다
    box.text = text;
  }
```

골격의 `/* Task 5: stage, restore, box, vb */` 위치에 다음을 넣는다.

```js
      var stage = fig.querySelector('svg'), restore = reveal(fig);
      var box = stage && !authored.note.has(fig) && !stage.querySelector('.rc-note') ? autoNote(stage) : null;
      var vbv = stage && stage.viewBox && stage.viewBox.baseVal && stage.viewBox.baseVal.width ? stage.viewBox.baseVal : null;
      var vb = vbv ? { l: vbv.x, t: vbv.y, r: vbv.x + vbv.width, b: vbv.y + vbv.height } : null;
```

골격의 `/* Task 5: 자동 상자 위치와 it.noteOn */` 위치에 다음을 넣는다.

```js
          if (box && vb && it.active && stage.contains(it.active) && stage.getScreenCTM()) {
            try { // 위치 계산이 실패해도 그 단계에 상자를 두지 않을 뿐 애니메이션은 만든다
              var obs = { boxes: [], pts: [] }, ots = [];
              for (var ot = start; ot < animEnd - 1e-9; ot += 0.25) ots.push(ot);
              ots.push(animEnd);
              ots.forEach(function (t) { tl.seek(t, false); obstacles(stage, fig, obs); });
              var a = userBox(stage.getScreenCTM().inverse(), it.active), nh = noteHeight(box, s.text);
              var peepW = usePeep && it.diamond ? PEEP + 4 : 0;
              it.note = placeUnit(a, nh, peepW, obs, vb);
              showNote(tl, box, start, it.note && it.note.note, s.text, nh);
            } catch (err) { console.error('RC.demo: 자동 설명 상자 위치 계산', err); it.note = null; tl.set(box.g, { opacity: 0 }, start); }
            rewindTo(pre);
          } else if (box) tl.set(box.g, { opacity: 0 }, start);
          var authorNotes = [].filter.call(fig.querySelectorAll('.rc-note'), function (n) { return !box || n !== box.g; });
          if (authorNotes.length) { tl.seek(animEnd, false); it.noteOn = authorNotes.some(function (n) { return seen(n, fig); }); rewindTo(pre); } // 작성자 상자가 단계 끝에 보이는지
          if (it.note) it.noteOn = true;
```

골격의 `/* Task 6: usePeep … */` 위치에는 Task 6이 정의를 넣기 전까지 `var usePeep = false;`를 둔다. 이 위치는 Task 5의 `box` 정의 아래다. 골격의 `/* Task 5: restore() */` 두 위치에 `restore();`를 넣는다.

- [ ] **Step 4: 시험이 통과하는지 확인한다**

Run: `python -B -m unittest tests.test_anim -v`
Expected: 모두 PASS.

- [ ] **Step 5: 커밋한다**

```bash
git add report-charts.js tests/test_anim.py
git commit -m "C1: 작성자 설명 상자가 없는 figure에 현재 노드 옆 자동 설명 상자를 둔다" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F"
```

### Task 6: 마름모 판정 스틱맨

**Files:**
- Modify: `report-charts.js` (골격의 `/* Task 6 */` 위치)
- Test: `tests/test_anim.py`

**Interfaces:**
- Consumes: Task 4의 `it.diamond`, `it.color`; Task 5의 `peepEl`, `it.note.peep`, `authored.icon`, `box`, `stage`
- Produces: `g.rc-icon[data-rc-peep]` 요소(`person`, `person-done`, `person-fail`), `it.think`(고민 스틱맨의 왼쪽 위 좌표 또는 null)

- [ ] **Step 1: 실패하는 시험을 쓴다**

```python
class EnginePeep(EngineCase):
    def peeps(self, p, i):
        return self.js(p, """([i]) => { const f = document.getElementById('d1'); f._rcTl.seek('e' + i, false);
          return [...f.querySelectorAll('.rc-icon')].filter(g => +getComputedStyle(g).opacity > 0.05).map(g => g.dataset.rcPeep).sort(); }""", [i])

    def test_think_then_done(self):
        p = self.open(MMD, mmd_steps(FLOW))
        self.assertEqual([self.peeps(p, i) for i in range(3)], [[], ["person"], ["person-done"]])

    def test_neg_step_after_diamond_fails(self):  # 판정 색은 이번 단계의 강조 색으로 정한다
        spec = [FLOW[0], ("시나리오 A · 검증", "한도를 넘습니다.", "B", None), ("시나리오 A · 거부", "주문을 거부합니다.", "D", "neg")]
        p = self.open(MMD, mmd_steps(spec))
        self.assertEqual([self.peeps(p, i) for i in range(3)], [[], ["person"], ["person-fail"]])

    def test_neg_non_diamond_has_no_peep(self):
        spec = [("가", "거부합니다.", "D", "neg"), ("나", "접수합니다.", "A", None)]
        p = self.open(MMD, mmd_steps(spec))
        self.assertEqual([self.peeps(p, i) for i in range(2)], [[], []])

    def test_author_icon_means_no_auto_peep(self):
        script = "RC.ready.then(function(){RC.icon(document.querySelector('#d1 svg'),'check',10,10);" + mmd_steps(FLOW) + "});"
        p = self.open(MMD, script)
        self.assertEqual([g for i in range(3) for g in self.peeps(p, i) if g], [])

    def test_prev_and_reset_restore_state(self):  # '이전'·'처음부터' 뒤 설명 상자 글·현재 노드·스틱맨이 그 단계 상태다
        p = self.open(MMD, mmd_steps(FLOW))
        r = self.js(p, """() => { const f = document.getElementById('d1'), b = f.querySelectorAll('.demo-ctl button');
          const st = () => ({note: f.querySelector('svg .rc-note').textContent.trim(),
            act: [...f.querySelectorAll('[data-rc-active]')].map(e => e.closest('g.node').id.replace(/.*flowchart-/, '').replace(/-\\d+$/, '')),
            peep: [...f.querySelectorAll('.rc-icon')].filter(g => +getComputedStyle(g).opacity > 0.05).map(g => g.dataset.rcPeep)});
          f._rcTl.seek('e2', false); b[0].click(); const one = st(); b[3].click(); const zero = st();
          return {one, zero: {act: zero.act, peep: zero.peep, op: +getComputedStyle(f.querySelector('svg .rc-note')).opacity}}; }""")
        self.assertEqual(r["one"], {"note": "한도 이내입니다.", "act": ["B"], "peep": ["person"]})
        self.assertEqual(r["zero"], {"act": [], "peep": [], "op": 0})
```

`test_author_icon_means_no_auto_peep`은 Mermaid SVG가 그려진 뒤 아이콘을 만들어야 하므로 `RC.ready.then` 안에서 부른다. 선 아이콘 `check`에는 `data-rc-peep`이 없어 걸러지고, 자동 스틱맨이 하나라도 있으면 목록에 남는다. `measure.source_facts`는 이 호출문에서도 `RC.demo(`를 1개로 센다.

- [ ] **Step 2: 시험이 실패하는지 확인한다**

Run: `python -B -m unittest tests.test_anim.EnginePeep -v`
Expected: `test_think_then_done`이 `[[], [], []]`로 FAIL.

- [ ] **Step 3: 엔진을 고친다**

골격의 `/* Task 6: usePeep, hideNext, prevIt, NEG */` 위치의 `var usePeep = false;`를 다음으로 바꾼다.

```js
      var usePeep = !!(box && window.RC_PEEPS && !authored.icon.has(fig) && !stage.querySelector('.rc-icon')); // 작성자 아이콘이 없을 때만 자동 스틱맨을 둔다
      var hideNext = [], prevIt = null, NEG = tok('neg');
```

골격의 `/* Task 6: 앞 단계 스틱맨 숨김과 판정 스틱맨 */` 위치에 다음을 넣는다.

```js
          if (hideNext.length) tl.set(hideNext, { opacity: 0 }, start);
          hideNext = [];
          if (prevIt && prevIt.think) { // 바로 앞 단계의 마름모 옆 스틱맨을 판정으로 바꾼다. 색은 이번 단계의 강조 색으로 정한다
            var vd = peepEl(stage, it.color === NEG ? 'person-fail' : 'person-done', prevIt.think.x + PEEP / 2, prevIt.think.y + PEEP / 2, PEEP);
            tl.set(vd, { opacity: 1 }, start); hideNext.push(vd);
          }
```

골격의 `/* Task 6: 고민 스틱맨 */` 위치에 다음을 넣는다.

```js
          it.think = usePeep && it.diamond && it.note ? it.note.peep : null;
          if (it.think) {
            var th = peepEl(stage, 'person', it.think.x + PEEP / 2, it.think.y + PEEP / 2, PEEP);
            tl.set(th, { opacity: 1 }, start); hideNext.push(th);
          }
          prevIt = it;
```

- [ ] **Step 4: 시험이 통과하는지 확인한다**

Run: `python -B -m unittest tests.test_anim -v`
Expected: 모두 PASS.

- [ ] **Step 5: 커밋한다**

```bash
git add report-charts.js tests/test_anim.py
git commit -m "C1: Mermaid 마름모 단계에 고민·판정 스틱맨을 자동으로 둔다" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F"
```

### Task 7: 화면 안 유지

**Files:**
- Modify: `report-charts.js` (골격 `sync`의 `/* Task 7 */` 위치, 새 함수 `keepInView`)
- Test: `tests/test_anim.py`

**Interfaces:**
- Consumes: Task 1의 `pend`, `quiet`, `info[i].start`; Task 4의 `it.active`; Task 5의 `it.noteOn`
- Produces: `keepInView(fig, it, reduce)`

- [ ] **Step 1: 실패하는 시험을 쓴다**

```python
TALL = """<div style="height:300px"></div><figure id="d1" data-anim="구조"><svg viewBox="0 0 400 1600" width="400" height="1600">
<rect id="top" x="20" y="20" width="100" height="40" fill="none" stroke="currentColor"/>
<rect id="bot" x="20" y="1500" width="100" height="40" fill="none" stroke="currentColor"/></svg></figure><div style="height:2000px"></div>"""
TALL_JS = ("RC.demo(document.getElementById('d1'),[{name:'가',text:'위 상자입니다.',play:function(tl,$){tl.to($('top'),{strokeWidth:2,duration:0.3});}},"
           "{name:'나',text:'아래 상자입니다.',play:function(tl,$){tl.to($('bot'),{strokeWidth:2,duration:0.3});}}]);")


class EngineScroll(EngineCase):
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
```

- [ ] **Step 2: 시험이 실패하는지 확인한다**

Run: `python -B -m unittest tests.test_anim.EngineScroll -v`
Expected: `test_scrolls_when_figure_on_screen`이 아래 상자가 창 밖이라 FAIL.

- [ ] **Step 3: 엔진을 고친다**

`RC.demo` 앞에 다음 함수를 둔다. 발동 조건(figure가 화면과 일부라도 겹칠 때)은 spec이 정한 값이다. 부드러운 스크롤은 C0 하네스가 스크롤이 멈출 때까지 기다리므로 판정에 영향이 없다.

```js
  function keepInView(fig, it, reduce) { // 현재 노드와 설명 상자가 창 밖이면 가장 가까운 위치로 옮긴다. figure가 화면과 겹칠 때만 한다
    var f = fig.getBoundingClientRect(), H = innerHeight, M = 16;
    if (!f.width || f.bottom <= 0 || f.top >= H) return;
    var els = [it.active].concat(it.noteOn ? [].slice.call(fig.querySelectorAll('.rc-note')) : []).filter(Boolean);
    var rs = els.map(function (e) { return e.getBoundingClientRect(); }).filter(function (r) { return r.width || r.height; });
    if (!rs.length) return;
    var how = reduce ? 'auto' : 'smooth', sb = it.active && it.active.closest && it.active.closest('.rc-scroll');
    var top = Math.min.apply(null, rs.map(function (r) { return r.top; })), bot = Math.max.apply(null, rs.map(function (r) { return r.bottom; }));
    var dy = bot - top > H - 2 * M || top < M ? top - M : bot > H - M ? bot - H + M : 0;
    if (sb) { // 390 폭 스크롤 상자 안에서는 가로로도 옮긴다
      var s = sb.getBoundingClientRect(), lf = Math.min.apply(null, rs.map(function (r) { return r.left; })), rt = Math.max.apply(null, rs.map(function (r) { return r.right; }));
      var dx = rt - lf > s.width || lf < s.left ? lf - s.left - M : rt > s.right ? rt - s.right + M : 0;
      if (dx) sb.scrollBy({ left: dx, behavior: how });
    }
    if (dy) scrollBy({ top: dy, behavior: how });
  }
```

골격 `sync`의 `/* Task 7 */` 위치에 다음을 넣는다. 설명 상자는 단계 시작에 위치를 옮기므로 단계 시작 시각을 지난 뒤에 한 번 판정한다.

```js
        if (pend !== null && t >= info[pend].start + 1e-3) { var k = pend; pend = null; keepInView(fig, info[k], reduce); }
```

- [ ] **Step 4: 시험이 통과하는지 확인한다**

Run: `python -B -m unittest tests.test_anim -v`
Expected: 모두 PASS.

- [ ] **Step 5: 커밋한다**

```bash
git add report-charts.js tests/test_anim.py
git commit -m "C1: 단계가 바뀌면 현재 노드와 설명 상자를 화면 안으로 옮긴다" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F"
```

### Task 8: 390 폭 SVG 글자와 스크롤 상자

**Files:**
- Modify: `report-charts.js` (새 함수 `scaleOf`·`fitSvg`·`watchFit`, `RC.ready` 뒤 연결, 골격의 `/* Task 8 */` 위치)
- Modify: `report-demo.css`
- Test: `tests/test_anim.py`

**Interfaces:**
- Consumes: Task 2의 `ownText`
- Produces: `fitSvg(fig)`, `watchFit(fig)`, 감싸는 상자 `div.rc-scroll`

- [ ] **Step 1: 실패하는 시험을 쓴다**

```python
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

    def test_animated_note_text_at_390(self):  # 자동 설명 상자 글도 390 폭에서 11px 이상이다
        p = self.open(MMD, mmd_steps(FLOW), width=390)
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
```

`self.open(WIDE, "")`는 `RC.demo` 호출이 없는 문서다. `measure.source_facts`가 0을 돌려주므로 준비 대기만 한다.

- [ ] **Step 2: 시험이 실패하는지 확인한다**

Run: `python -B -m unittest tests.test_anim.EngineFit -v`
Expected: `test_390_min_width_scroll_box`가 약 5.2px 글자로 FAIL.

- [ ] **Step 3: 엔진과 CSS를 고친다**

`RC.ready` 정의 뒤에 다음을 둔다.

```js
  /* 도식 글자: 화면상 11px보다 작아지면 figure 안 가로 스크롤 상자에 넣고 SVG 최소 폭을 글자가 11px이 되는 폭으로 정한다 */
  var MIN_PX = 11;
  function scaleOf(m) { return m ? Math.sqrt(Math.abs(m.a * m.d - m.b * m.c)) : 0; }
  function fitSvg(fig) {
    [].forEach.call(fig.querySelectorAll('svg'), function (svg) {
      if (svg.parentElement.closest('svg') || svg.closest('[_echarts_instance_]') || !svg.getAttribute('viewBox')) return; // ECharts는 상자 폭대로 그려 글자가 줄지 않는다
      var keep = svg.style.minWidth;
      svg.style.minWidth = '';
      var w = svg.getBoundingClientRect().width;
      if (!w) { svg.style.minWidth = keep; return; } // 숨은 페이지(폭 0)는 보일 때 다시 계산한다
      var small = Infinity;
      [].forEach.call(svg.querySelectorAll('text, tspan, foreignObject *'), function (e) {
        if (e.closest('defs') || !ownText(e)) return;
        var host = e instanceof SVGElement ? e : e.closest('foreignObject'), k = scaleOf(host.getScreenCTM());
        if (k) small = Math.min(small, parseFloat(getComputedStyle(e).fontSize) * k);
      });
      if (!(small < MIN_PX)) return;
      if (!svg.parentElement.classList.contains('rc-scroll')) {
        var box = document.createElement('div');
        box.className = 'rc-scroll';
        svg.parentNode.insertBefore(box, svg);
        box.appendChild(svg);
      }
      svg.style.minWidth = Math.ceil(w * MIN_PX / small) + 1 + 'px';
    });
  }
  function watchFit(fig) { // 페이지가 보일 때와 창 크기가 바뀔 때 다시 계산한다
    if (fig._rcFit) { fitSvg(fig); return; }
    fig._rcFit = true;
    var w = -1;
    new ResizeObserver(function () { if (fig.clientWidth && fig.clientWidth !== w) { w = fig.clientWidth; fitSvg(fig); } }).observe(fig);
  }
  RC.ready.then(function () { [].forEach.call(document.querySelectorAll('figure'), watchFit); });
```

골격의 `/* Task 8: watchFit(fig) */` 위치에 `watchFit(fig);`를 넣는다. 자동 상자 글이 생긴 뒤 다시 계산하기 위해서다.

`report-demo.css`에 다음 두 줄을 추가한다.

```css
.rc-scroll{overflow-x:auto;max-width:100%}
.rc-scroll>svg{display:block}
```

Task 3이 만든 `@media print` 블록 안 마지막에 다음 두 줄을 넣는다.

```css
  .rc-scroll{overflow:visible}
  .rc-scroll>svg{min-width:0 !important}
```

- [ ] **Step 4: 시험이 통과하는지 확인한다**

Run: `python -B -m unittest tests.test_anim -v`
Expected: 모두 PASS.

- [ ] **Step 5: 커밋한다**

```bash
git add report-charts.js report-demo.css tests/test_anim.py
git commit -m "C1: 390 폭에서 도식 글자가 11px보다 작아지면 스크롤 상자와 최소 폭을 둔다" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F"
```

### Task 9: 선 차트 계열 직접 이름표와 표식

**Files:**
- Modify: `report-charts.js` (`RC.chart`, 새 함수 `lineLabels`)
- Test: `tests/test_anim.py`

**Interfaces:**
- Consumes: 없음
- Produces: 선 계열이 둘 이상인 옵션의 빈 값에 `endLabel`·`symbol`·`grid.right`를 채우는 `lineLabels(option)`

- [ ] **Step 1: 실패하는 시험을 쓴다**

```python
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
```

- [ ] **Step 2: 시험이 실패하는지 확인한다**

Run: `python -B -m unittest tests.test_anim.EngineChart -v`
Expected: `test_two_lines_get_end_labels_and_shapes`가 `[False, False]`로 FAIL.

- [ ] **Step 3: 엔진을 고친다**

`RC.chart` 앞에 다음 함수를 두고, `RC.chart`의 `option.animation = false;` 다음 줄에서 `lineLabels(option);`을 부른다.

```js
  var SHAPES = ['circle', 'rect', 'triangle', 'diamond', 'roundRect', 'pin'];
  function lineLabels(option) { // 선 계열이 둘 이상이면 선 끝에 계열 이름을 달고 계열마다 표식 모양을 다르게 한다. 작성자가 준 값은 두고 빈 값만 채운다
    var lines = (option.series || []).filter(function (s) { return s.type === 'line'; });
    if (lines.length < 2) return;
    lines.forEach(function (s, k) {
      if (s.symbol == null) s.symbol = SHAPES[k % SHAPES.length];
      if (s.showSymbol == null) s.showSymbol = true;
      if (s.symbolSize == null) s.symbolSize = 6;
      if (s.endLabel == null) s.endLabel = { show: true, formatter: '{a}', color: tok('ink-2'), fontSize: 12, distance: 6 };
    });
    [].concat(option.grid || (option.grid = {})).forEach(function (g) { // 이름표가 잘리지 않게 오른쪽 여백을 둔다
      if (g.right == null || (typeof g.right === 'number' && g.right < 72)) g.right = 72;
    });
  }
```

- [ ] **Step 4: 시험이 통과하는지 확인한다**

Run: `python -B -m unittest tests.test_anim -v`
Expected: 모두 PASS.

- [ ] **Step 5: 커밋한다**

```bash
git add report-charts.js tests/test_anim.py
git commit -m "C1: 선 계열이 둘 이상인 차트에 계열 이름표와 표식 모양을 단다" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F"
```

### Task 10: 소유 견본의 결함과 자기 판정

**Files:**
- Modify: `tests/sample-anim.html` (무대 `st-shift`·`st-rule`과 관리 블록)
- Modify: `tests/sample-viz.html` (관리 블록만)
- Test: `tests/test_anim.py`

**Interfaces:**
- Consumes: Task 1~9의 엔진, 시험 도우미의 `open_file`
- Produces: 기준선 막대(`b-a0`·`b-b0`·`b-c0`)와 손익 축 글자가 있는 견본, 견본 애니메이션의 `RC.check` 통과

- [ ] **Step 1: 실패하는 시험을 쓴다**

```python
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
```

- [ ] **Step 2: 시험이 실패하는지 확인한다**

Run: `python -B -m unittest tests.test_anim.SampleSelfCheck -v`
Expected: `test_baseline_bars_and_axes_in_sample`과 `test_managed_blocks_match_engine`이 FAIL. `test_sample_anim_and_viz_pass`는 견본에 옛 엔진이 들어 있으므로 이 단계에서는 결과를 판단에 쓰지 않는다.

- [ ] **Step 3: 견본을 고치고 관리 블록을 다시 채운다**

`tests/sample-anim.html`의 `st-shift` 무대에서 viewBox를 `0 0 700 300`으로 바꾸고, `v-c` 글자 뒤에 다음을 넣는다. 위쪽 막대는 기준선 길이에서 제안안 길이로 바뀌고, 아래 얇은 막대는 끝 장면에도 기준선 값을 남긴다.

```html
    <rect id="b-a0" x="110" y="164" width="400" height="6" style="fill:var(--s4)"/>
    <rect id="b-b0" x="110" y="214" width="200" height="6" style="fill:var(--s4)"/>
    <rect id="b-c0" x="110" y="264" width="200" height="6" style="fill:var(--s4)"/>
    <text x="110" y="292" font-size="12">아래 얇은 막대는 기준선입니다</text>
```

`st-rule` 무대에서 viewBox를 `0 0 720 280`으로 바꾸고, 0bp 눈금 글자(`<text x="52" y="204" …>0</text>`) 뒤에 다음을 넣는다. 0bp는 y=200이고 1bp는 3이며, 1개월은 x 56이다.

```html
    <text x="52" y="174" font-size="12" text-anchor="end">10</text>
    <text x="52" y="144" font-size="12" text-anchor="end">20</text>
    <text x="52" y="114" font-size="12" text-anchor="end">30</text>
    <text x="52" y="84" font-size="12" text-anchor="end">40</text>
    <text x="20" y="84" font-size="12" text-anchor="middle">bp</text>
    <path d="M60 232V236M172 232V236M284 232V236M396 232V236M508 232V236M620 232V236" fill="none" style="stroke:var(--hair)"/>
    <text x="60" y="252" font-size="12" text-anchor="middle">0</text>
    <text x="172" y="252" font-size="12" text-anchor="middle">2</text>
    <text x="284" y="252" font-size="12" text-anchor="middle">4</text>
    <text x="396" y="252" font-size="12" text-anchor="middle">6</text>
    <text x="508" y="252" font-size="12" text-anchor="middle">8</text>
    <text x="620" y="252" font-size="12" text-anchor="middle">10</text>
    <text x="660" y="252" font-size="12">개월</text>
```

호출 코드는 바꾸지 않는다. 그다음 관리 블록을 다시 채운다.

Run: `python build.py tests/sample-anim.html tests/sample-viz.html`
Expected: 두 파일 모두 `기준 CSS 반영, 연결 코드 반영`

- [ ] **Step 4: 시험이 통과하는지 확인한다**

Run: `python -B -m unittest tests.test_anim -v`
Expected: 모두 PASS. `RC.check`가 실패하면 `overlapSamples`를 읽고, 축 글자가 겹친 것이면 축 글자의 x·y만 옮긴다. 엔진의 자동 상자 위치 문제이면 Task 5의 함수를 고친다. 같은 실패를 고치는 시도는 3번까지 하고, 그래도 실패하면 원인을 리포트에 적고 다음 Task로 간다.

- [ ] **Step 5: 커밋한다**

```bash
git add tests/sample-anim.html tests/sample-viz.html tests/test_anim.py
git commit -m "C1: 견본의 기준선 막대와 손익 축을 고치고 관리 블록을 다시 채운다" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F"
```

### Task 11: 시각화.md와 엔진 주석 갱신

**Files:**
- Modify: `시각화.md`
- Modify: `report-charts.js` (4행 주석)
- Modify: `tests/sample-anim.html`, `tests/sample-viz.html` (관리 블록 재빌드)
- Test: `tests/test_anim.py` (`ListSync`, `SampleSelfCheck.test_managed_blocks_match_engine`)

**Interfaces:**
- Consumes: Task 1~9의 동작
- Produces: 새 동작을 적은 규칙 문서

- [ ] **Step 1: 시각화.md를 고친다**

'시각화' 절의 공통 규칙 목록 끝(`- **움직임:** …` 뒤)에 다음 두 불릿을 더한다.

```markdown
- **390 폭 도식:** 도식 글자가 화면상 11px보다 작아지면 엔진이 figure 안에 가로 스크롤 상자를 두고 SVG 최소 폭을 정한다. 인쇄에서는 스크롤 상자와 최소 폭이 풀린다.
- **선 차트 이름표:** 선 계열이 둘 이상이면 엔진이 선 끝에 계열 이름을 달고 계열마다 표식 모양을 다르게 한다. 작성자가 준 `endLabel`·`symbol`은 그대로 둔다.
```

RC 함수 표의 `RC.demo` 행 끝에 다음 문장을 덧붙인다.

```markdown
 주소의 `?rc-mode=auto|step`으로 재생 방식을 고르고, figure에 `data-rc-mode`를, 단계 끝의 현재 노드에 `data-rc-active`를 단다
```

'애니메이션' 절의 준비 목록 '모든 분기' 불릿 끝에 다음 문장을 덧붙인다.

```markdown
 이름이 '시나리오 X · Y'인 단계는 X로 묶여 단계 표시가 '시나리오 A 2/4'처럼 보이고, 묶음이 둘 이상이고 단계가 12개를 넘으면 조작 줄 아래에 시나리오 선택 줄이 생긴다.
```

'아이콘' 불릿의 `` `person-guide`는 시나리오 첫 단계의 안내, `` 부분을 다음으로 바꾼다.

```markdown
`person-guide`는 시나리오 첫 단계의 안내이며 기본으로 쓰지 않고 직접 그린 무대에서 안내가 꼭 필요할 때만 쓴다.
```

글 규칙 목록의 '표시 시간' 불릿을 다음으로 바꾼다.

```markdown
- **표시 시간:** 자동 재생에서는 단계의 글이 다 나온 뒤 1초 + 글자 수 ÷ 8초 이상, 그 값 + 3초 이하로 머문다. 글자 수에는 자막과 설명 상자 글과 숫자 칸이 모두 든다. 엔진이 이 시간을 계산하므로 문서가 머무는 시간을 따로 넣지 않는다.
```

글 규칙 목록 뒤, '애니메이션 함수는 다음과 같다' 문장 앞에 다음 문단과 표를 넣는다.

```markdown
재생 방식은 두 가지이고, 주소 끝의 `?rc-mode=auto` 또는 `?rc-mode=step`으로 고른다. 주소에 값이 없으면 단계 넘김이다. 두 방식 모두 처음 상태는 1단계 연출 전이고, '처음부터'가 이 상태로 돌아간다.

| 방식 | '다음' | '재생' |
|---|---|---|
| 자동 재생 | 한 단계를 머무는 시간까지 재생한다 | 끝까지 이어서 재생한다 |
| 단계 넘김 | 한 단계의 연출만 재생하고 멈춘다(연출은 엔진이 0.4~2.5초로 맞춘다) | 단계 사이에 표시 시간 규칙만큼 쉬며 이어서 재생한다 |

`RC.note`를 쓰지 않은 figure에는 엔진이 자동 설명 상자를 둔다. 상자에는 단계의 `text`가 들어가고, 상자는 현재 노드 옆 220px 폭으로 나타난다. 현재 노드는 `play` 안에서 `$`로 마지막에 조회한 요소이고, `RC.fx.mark`·`RC.fx.spot`이 받은 요소가 우선한다. 상자는 무대 요소와 겹치지 않는 쪽을 오른쪽·왼쪽·아래·위 순서로 고르고, 네 쪽 모두 맞지 않으면 상자 없이 자막을 보인다. 설명 상자가 보이는 단계에서는 자막을 숨긴다.

Mermaid 애니메이션에서 `RC.icon`을 쓰지 않으면, 엔진이 현재 노드가 판단 마름모인 단계에 고민 스틱맨을 상자 옆에 두고, 다음 단계에 판정 스틱맨으로 바꾼다. 다음 단계의 강조 색이 `neg`이면 실패 스틱맨이다. 엔진은 현재 노드(닫힌 도형)에 강조색 2px 테두리와 옅은 채움을, 지나온 노드에 1.5px 테두리를 준다. 작성자가 색을 준 노드는 그 색을 유지하고, 색을 주지 않은 노드만 보조 강조색으로 바뀐다.
```

함수 표 뒤의 `` `at`은 GSAP 위치 인자다. `` 문단을 다음으로 바꾼다.

```markdown
`at`은 GSAP 위치 인자이고 단계 안 시각으로 해석된다. 생략하면 앞 효과 뒤에, `'<'`이면 앞 효과와 함께 시작한다. 숫자를 주면 단계 시작에서 잰 시각이고, 앞 단계에서 만든 라벨은 쓸 수 없다.
```

'흔한 실수' 절의 기존 불릿은 그대로 둔다. 애니메이션 유형 표는 바꾸지 않는다(`ListSync` 시험이 대조한다).

- [ ] **Step 2: 엔진 주석을 고치고 관리 블록을 다시 채운다**

`report-charts.js` 4행의 `RC.demo(figure, 단계 배열),`를 `RC.demo(figure, 단계 배열: 주소 ?rc-mode=auto|step으로 재생 방식을 고른다),`로 바꾼다.

Run: `python build.py tests/sample-anim.html tests/sample-viz.html`
Expected: 두 파일 모두 `기준 CSS 반영, 연결 코드 반영`

- [ ] **Step 3: 시험과 금지어 검사를 실행한다**

Run: `python -B -m unittest tests.test_anim -v`
Expected: `ListSync`와 `test_managed_blocks_match_engine`을 포함해 모두 PASS.

Run:
```bash
python - <<'EOF'
import re, subprocess
table = open("C:/Users/ho381/.claude/disciplined-coder/korean-banned-words.md", encoding="utf-8").read()
rows = [l for l in table.splitlines() if l.startswith("| `")]
diff = subprocess.run(["git", "diff", "-U0", "--", "시각화.md"], capture_output=True, text=True, encoding="utf-8").stdout
added = re.sub(r"`[^`]*`", "", "\n".join(l[1:] for l in diff.splitlines() if l.startswith("+") and not l.startswith("+++")))  # 코드와 인용은 대상이 아니다
for r in rows:
    cols = [c.strip() for c in r.strip("|").split("|")]
    words, skips = re.findall(r"`([^`]+)`", cols[0]), re.findall(r"`([^`]+)`", cols[4]) if len(cols) > 4 else []
    for w in words:
        for m in re.finditer(re.escape(w), added):
            around = added[max(0, m.start() - 6):m.end() + 6]
            if not any(s in around for s in skips):
                print("금지어:", w, "…", around.replace("\n", " "))
EOF
```
Expected: 출력 없음. 출력이 있으면 그 낱말을 금지어 표의 오른쪽 말로 바꾸고 다시 실행한다.

- [ ] **Step 4: 커밋한다**

```bash
git add 시각화.md report-charts.js tests/sample-anim.html tests/sample-viz.html
git commit -m "C1: 시각화.md에 재생 방식·표시 시간·자동 설명 상자·스틱맨·시나리오 묶기를 적는다" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F"
```

### Task 12: spec 「검증」 실행과 리포트 자료 모으기

**Files:**
- Modify: 판정 실패를 고치면 그 실패를 낸 Task의 파일. 엔진을 고치면 `tests/sample-anim.html`, `tests/sample-viz.html`을 다시 빌드한다.
- 리포트는 저장소에 쓰지 않는다. L2의 최종 응답 본문에 싣는다.

**Interfaces:**
- Consumes: Task 1~11의 결과
- Produces: 두 방식의 기계 판정 JSON, 체크리스트 3회 결과와 충족률, 리포트 본문

- [ ] **Step 1: 고정 견본을 다시 빌드하고 기계 판정(자동 재생)을 실행한다**

Run:
```bash
SP=$(python -c "import tempfile; print(tempfile.mkdtemp(prefix='c1-'))")
echo "$SP"
python eval/rebuild.py "$SP/fixed"
python eval/gates.py "$SP/fixed/04-rules.html" "$SP/fixed/03-groups.html" "$SP/fixed/sample-anim.html" "$SP/fixed/sample-viz.html" --only motion --mode auto --out "$SP/auto.json"
```
Expected: 종료 코드 0. 1이면 `auto.json`에서 실패 항목을 읽는다. 작성자가 고정한 설명 상자(`RC.note`를 쓰는 sample-anim의 `d-shift`·`d-rule`, sample-viz의 `d-order`)의 `note-near` 실패는 예외로 figure 이름과 단계별 거리(`detail`의 `distance`)를 기록한다. 04-rules의 `note-near`가 '보이는 설명 상자 없음'으로 실패하면 spec의 위치 규칙(표시 범위 안)과 판정 기준이 맞지 않는다는 뜻이므로, 단계와 노드를 기록하고 BLOCKED로 올릴 질문으로 리포트에 적는다. 그 밖의 실패는 해당 Task의 코드를 고치고 Step 1을 다시 실행한다. 같은 항목을 고치는 시도는 3번까지 한다.

- [ ] **Step 2: 기계 판정(단계 넘김)을 실행한다**

Run: `python eval/gates.py "$SP/fixed/04-rules.html" "$SP/fixed/03-groups.html" "$SP/fixed/sample-anim.html" "$SP/fixed/sample-viz.html" --only motion --mode step --out "$SP/step.json"`
Expected: Step 1과 같은 기준.

- [ ] **Step 3: 단위 시험을 실행한다**

Run: `python -B -m unittest discover -s tests`
Expected: `OK`. CDN 실패로 건너뛴 시험(`skipped`)이 엔진 시험에 없어야 한다.

- [ ] **Step 4: 장면을 만든다**

Run:
```bash
SHOT=$(python -c "import tempfile; print(tempfile.mkdtemp(prefix='shots-'))")
for m in auto step; do for f in 04-rules 03-groups sample-anim sample-viz; do
  python eval/shoot.py "$SP/fixed/$f.html" "$SHOT/$m/$f" --mode $m
done; done
```
Expected: 실행마다 `장면 N개를 … 남겼다`. `$SHOT`은 저장소 이름이 없는 임시 경로다.

- [ ] **Step 5: 체크리스트 자가 점검을 실행한다**

`eval/prompts/checklist-review.md`의 틀에서 `{{INPUT_DIR}}`에 장면 폴더(`$SHOT/<방식>/<견본>`)를, `{{CHECKLIST}}`에 `eval/checklist.md` 표의 `motion` 항목 id·질문과 표 앞 용어 풀이 문단을 넣는다. 견본·방식마다 새 서브에이전트를 3번 실행하고, 결과 JSON을 `$SP/check1/<방식>-<견본>-run<k>.json`(k=1~3)으로 저장한다. 서브에이전트에는 그 장면 폴더와 채운 프롬프트만 준다.

Run: `python eval/checklist_vote.py "$SP/check1" "$SP/check1-vote.json"`
Expected: 출력 JSON의 `motion` 충족률이 0.85 이상. 못 미치면 '아니오' 항목의 근거를 읽고 엔진을 고친 뒤 Step 1부터 다시 하고 `check2`, `check3`으로 반복한다. 세 번째에도 못 미치면 리포트에 적고 끝낸다.

- [ ] **Step 6: 준비 시간을 확인한다**

Run: `python -c "import sys, time; sys.path.insert(0,'eval'); import harness; from pathlib import Path; f=Path(sys.argv[1]); s=harness.Session(f.parent).__enter__(); t=time.time(); p,ok=s.open(f.name,1,1280,'light',None,'p2'); print('준비', ok, round(time.time()-t,1), '초'); s.__exit__(None,None,None)" "$SP/fixed/04-rules.html"`
Expected: `준비 True`와 10초 이하. 넘으면 원인(표본 수)을 리포트에 적는다.

- [ ] **Step 7: 마지막 수정을 커밋하고 브랜치 상태를 확인한다**

```bash
git add report-charts.js report-demo.css 시각화.md tests/sample-anim.html tests/sample-viz.html tests/test_anim.py
git commit -m "C1: 기계 판정과 자가 점검에서 나온 결함을 고친다" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F"
git status --short
git log --oneline main..HEAD
```
Expected: 고친 파일이 없으면 커밋은 '변경 없음'으로 끝난다. 작업 트리는 정리되고 C1 커밋만 남는다. 병합·push는 하지 않는다.

- [ ] **Step 8: 리포트 본문을 쓴다**

L2의 최종 응답 본문에 다음 항목을 이 이름으로 쓴다. 저장소에는 쓰지 않는다.

- **변경 파일과 시험 결과:** `git diff --stat main..HEAD`와 Step 3의 출력
- **두 방식의 기계 판정 결과와 작성자 설명 상자 예외:** `auto.json`·`step.json`의 항목별 결과, 예외 figure와 거리
- **체크리스트 자가 점검 결과:** 차례마다 `motion` 충족률과 '아니오' 항목
- **plan 리뷰에서 기능적 변화가 있었던 반영**
- **상위 설계·spec과 다르게 정한 점:** '설계 결정' 절 마지막 문단의 목록
- **브랜치 이름:** `c1-animation-engine`

<!-- spec-review: passed -->
