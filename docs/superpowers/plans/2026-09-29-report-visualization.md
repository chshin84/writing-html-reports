# 보고서 시각화 확장 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `writing-html-reports` 스킬이 ECharts 차트·Mermaid 도식·GSAP 동작 예시를 규격 안에서 쓰게 하고, 검사기와 build.py가 이를 지원하게 한다.

**Architecture:** 연결 코드 `report-charts.js`를 build.py가 문서의 BEGIN/END report-charts 표시 사이에 삽입한다. 문서는 CDN에서 고정 버전 라이브러리를 로드하고, `</main>` 뒤의 문서 스크립트에서 `RC.chart`·`RC.ma`·`RC.color`·`RC.demo`를 호출한다. check.py는 HTML 원문에서 CSS·문서 스크립트·Mermaid 원문을 따로 읽어 규격 위반을 검출한다.

**Tech Stack:** Python 3.12 표준 라이브러리(`unittest`, `re`), ECharts 6.1.0, Mermaid 11.17.2, GSAP 3.15.0(jsDelivr), 헤드리스 Edge, Playwright MCP 도구(`mcp__plugin_playwright_playwright__*`).

**Spec:** `docs/superpowers/specs/2026-09-28-report-visualization-design.md`

## Global Constraints

- 설치된 스킬 폴더 `C:/Users/CHSHIN/.claude/skills/writing-html-reports`(아래 `$S`)는 작업 중에 고치지 않는다. Task 1 Step 1이 `$S`의 저장소에서 `viz` 브랜치의 git worktree(같은 저장소를 다른 폴더에 꺼낸 작업 사본)를 세션 scratchpad 아래 `wt-viz`(아래 `$W`)에 만든다. Task 1~7의 모든 명령은 `$W`에서 실행하고, Task 7을 통과한 뒤에만 `$S`에 병합한다. 과제 사이에 다른 세션이 절반만 바뀐 스킬을 쓰지 않게 하기 위해서다.
- 명령은 Bash 도구로 실행한다. Bash 도구는 호출 사이에 셸 변수를 유지하지 않으므로, 명령마다 앞에 `W=<wt-viz 절대 경로>; OUT=<scratchpad 절대 경로>; E="/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"; cd "$W"`를 붙인다.
- CDN 주소는 `https://cdn.jsdelivr.net/npm/echarts@6.1.0/dist/echarts.min.js`, `https://cdn.jsdelivr.net/npm/mermaid@11.17.2/dist/mermaid.min.js`, `https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js` 세 개로 고정한다.
- 색은 토큰(`var(--…)` 또는 `RC.color('이름')`)만 쓰고, 문서 스크립트와 Mermaid 원문에 `#xxxxxx` 색을 쓰지 않는다.
- 모서리는 직각이다. 그림자·그라데이션·진입 애니메이션·자동 반복을 쓰지 않는다.
- 움직임은 `RC.demo` 안에서만 쓴다. 동작 예시는 키 입력을 처리하지 않는다.
- 파이썬은 `python -B`로 실행해 `__pycache__`를 만들지 않는다. 한국어 출력을 받는 subprocess에는 `PYTHONIOENCODING=utf-8`을 준다.
- 사람이 읽는 한국어 문구는 '-습니다'체나 '-다'체 문어로 쓰고, `금지어.md`의 금지어를 쓰지 않는다.
- 브라우저 시험은 `$W`를 기준으로 한 `python -B -m http.server 8765` 서버로 연다. 서버가 필요한 과제(Task 1, Task 5, Task 7)는 과제 첫머리에서 서버를 백그라운드로 켜고 과제 끝에서 끈다. 임시 시험 파일은 `tests/_tmp-*.html`로 만들고 커밋하지 않는다.
- 스크린샷과 PDF는 세션 scratchpad(`$OUT`)에 저장한다.
- 브라우저 시험 식은 연결 코드 준비를 기다리도록 `RC.ready.then(…)` 안에서 평가한다.

## spec과 다르게 정한 사항

아래 사항은 spec을 구현하면서 정했으며, 같은 내용을 spec 본문에도 반영한다.

- **BEGIN 표시의 버전:** 대상 버전의 원본은 `report-charts.js` 첫 줄이다. build.py가 BEGIN 표시에 그 버전을 적어 넣고, 문서의 CDN 주소 버전을 같은 값과 대조한다. spec의 'BEGIN 표시 버전과 CDN 버전 대조'와 같은 결과이며, 버전을 한 곳에만 적기 위한 방식이다.
- **`play`의 두 번째 인자:** `play(tl, $)`의 `$('이름')`은 figure 안의 `#이름` 요소나 Mermaid 노드를 돌려준다. Mermaid 도식을 동작 예시의 무대로 쓰려면 노드를 찾는 수단이 필요하다.
- **판단 마름모 노드:** Mermaid 노드는 직각 상자와 함께 판단 마름모(`{텍스트}`)를 허용한다. 흐름도의 분기를 나타내는 표준 모양이고, 2026-09-28 사용자 검토 때 알렸다.
- **GSAP 로드 실패:** 동작 예시는 실패 문구 대신 단계 설명 목록을 보인다. 목록이 같은 내용을 글로 전달하므로 독자에게 더 유용하다.
- **색 리터럴 검출 범위:** 문서 스크립트에서는 따옴표나 백틱 문자열 안의 `#`16진 색만 검출하고, `querySelector`·`getElementById` 인자는 뺀다. 요소 id 선택자(`'#abc'`)의 오검출을 방지하기 위해서다.
- **추가 파일:** build.py 시험 `tests/test_build.py`와 `.gitignore`의 임시 파일 규칙을 추가한다.
- **SKILL.md description:** 차트·도식·동작 예시 요청에서도 이 스킬이 열리도록 description에 시각화 대상을 추가한다.
- **스킬 동작 시험 프롬프트:** 모델이 자료를 지어내지 않도록 거래대금 값을 주고, 결과 판정을 위해 저장 경로와 완료 기준 실행을 지시한다. 문서 형식(단일·페이지형)은 지정하지 않는다.
- **원본 스크립트의 위반:** 기존 HTML 수정 작업에서 원본에 이미 있던 스크립트 규칙 위반은 금지어처럼 참고로만 출력한다.
- **연결 코드 없는 RC 호출:** build.py는 문서가 `RC.` 함수를 호출하는데 연결 코드 표시가 없으면 멈춘다.

## Review Focus

- **Mermaid 원문의 `<` 문자:** `B{금액 &lt; 한도}`처럼 `<`를 `&lt;`로 적으면 도식에 `<`로 표시되어야 한다. Task 5의 견본 p4와 동작 시험에 포함한다.
- **한 페이지의 동작 예시 두 개:** 한 예시의 버튼을 눌러도 다른 예시의 단계 표시는 바뀌지 않아야 한다. Task 5의 견본 p5와 동작 시험에 포함한다.
- **좁은 화면(폭 390px):** 차트 SVG 폭이 차트 상자 폭을 넘지 않고 페이지에 가로 스크롤이 생기지 않아야 한다. Task 5 동작 시험에 포함한다.
- **라이브러리 하나의 로드 실패:** GSAP 주소가 틀려도 차트와 도식은 그려지고, 동작 예시는 단계 설명 목록으로 바뀌어야 한다. Task 5 동작 시험에 포함한다.
- **시각화가 없는 문서:** report-charts 표시와 CDN 태그가 없는 문서도 build.py와 check.py를 그대로 통과해야 한다. Task 2와 Task 3의 시험에 포함한다.

---

### Task 1: 가정 확인 (숨은 페이지의 Mermaid, 헤드리스 PDF의 beforeprint, Mermaid 노드 id 형식)

작업용 worktree를 만들고, spec의 두 가정과 `RC.demo`의 `$` 조회 함수가 기대하는 Mermaid 노드 형식을 측정한다. 시험 파일은 버리는 시험물이며 커밋하지 않는다.

**Files:**
- Create(임시): `tests/_tmp-probe.html`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: 없음
- Produces: `$W` worktree(`viz` 브랜치)와 네 측정 결과. (a) 숨은 요소에서 그린 Mermaid SVG의 크기가 보이는 요소의 크기와 같고 숨은 요소 전용 글자가 상자 밖으로 넘치지 않는지, (b) 헤드리스 Edge `--print-to-pdf`에서 `beforeprint`가 발생하는지, (c) flowchart 노드 `A`의 `<g>` id가 `-A-`를 포함하는지, (d) `[ ]` 노드의 `<g>` 안에 `rect`가 있는지. (c)나 (d)가 아니면 Task 4 Step 1의 `$` 함수와 Task 5 견본의 `querySelector('rect')`를 측정한 형식으로 바꾼다.

- [ ] **Step 1: worktree 만들기와 `.gitignore` 갱신**

Run:
```bash
S="C:/Users/CHSHIN/.claude/skills/writing-html-reports"; W=<scratchpad>/wt-viz
git -C "$S" status --short
git -C "$S" worktree add -b viz "$W"
cd "$W" && git log --oneline -1
```
Expected: `status`가 아무것도 출력하지 않고, worktree가 만들어지며, 마지막 줄이 `$S`의 최신 커밋과 같다.

`$W/.gitignore` 전체를 아래로 바꾼다.

```
__pycache__/
tests/_tmp-*
```

- [ ] **Step 2: 시험 파일 작성**

`tests/_tmp-probe.html`:

```html
<!doctype html>
<html lang="ko"><head><meta charset="utf-8"><title>probe</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<style>body{font-family:"Pretendard Variable",sans-serif}#hid{display:none}</style>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11.17.2/dist/mermaid.min.js"></script>
</head><body>
<div id="vis"><pre class="mermaid">flowchart LR
  A[주문 접수] --> B{금액 &lt; 한도} --> C[체결]</pre></div>
<div id="hid"><pre class="mermaid">flowchart LR
  A[퇴직연금 편입] --> B{듀레이션 &lt; 목표} --> C[리밸런싱]</pre></div>
<script>
addEventListener('beforeprint', function () { var p = document.createElement('p'); p.textContent = 'BEFOREPRINT-FIRED'; document.body.appendChild(p); });
mermaid.initialize({ startOnLoad: false, theme: 'base' });
document.fonts.ready.then(function () {
  var pres = [].slice.call(document.querySelectorAll('pre.mermaid'));
  return pres.reduce(function (p, pre, i) {
    var src = pre.textContent;
    return p.then(function () { return mermaid.render('m' + i, src); }).then(function (r) { pre.innerHTML = r.svg; });
  }, Promise.resolve());
}).then(function () { document.title = 'rendered'; });
</script>
</body></html>
```

- [ ] **Step 3: 서버 실행**

Run(Bash 도구 `run_in_background`): `cd "$W" && python -B -m http.server 8765`
Expected: `curl -s -o /dev/null -w "%{http_code}" http://localhost:8765/tests/_tmp-probe.html`이 `200`을 출력한다.

- [ ] **Step 4: 숨은 요소의 크기와 노드 형식 측정**

`#vis`와 `#hid`는 같은 모양의 도식에 서로 다른 한글 낱말을 쓴다. 숨은 요소에만 있는 글자의 글꼴 조각이 늦게 로드되는 조건을 재현하기 위해서다. Playwright로 `http://localhost:8765/tests/_tmp-probe.html`을 열고 제목이 `rendered`가 될 때까지 기다린 뒤 아래 식을 평가한다(`browser_evaluate`).

```js
() => {
  document.getElementById('hid').style.display = 'block';
  const size = id => { const s = document.querySelector('#' + id + ' svg').getBoundingClientRect(); return [Math.round(s.width), Math.round(s.height)]; };
  const nodes = [...document.querySelectorAll('#hid g.node')];
  const overflow = nodes.some(g => {
    const box = g.querySelector('rect,polygon,path'), lab = g.querySelector('.label, text');
    return box && lab && lab.getBoundingClientRect().width > box.getBoundingClientRect().width + 1;
  });
  return {
    vis: size('vis'), hid: size('hid'), ids: nodes.map(g => g.id), overflow,
    rectInA: !!document.querySelector('#hid g.node[id*="-A-"] rect'),
    hasLt: document.querySelector('#hid svg').textContent.includes('듀레이션 < 목표')
  };
}
```

Expected:
- **크기:** `vis`와 `hid`의 폭 차이가 도식 글자 차이 범위(±40px) 안이고 높이가 같다.
- **넘침:** `overflow`가 `false`다.
- **노드 형식:** `ids`에 `-A-`를 포함한 id가 있고 `rectInA`가 `true`다.
- **문자 `<`:** `hasLt`가 `true`다.

`overflow`가 `true`이거나 높이가 다르면 멈추고 사용자에게 알린다. 대체 방식은 spec에 정해져 있지 않으므로 사용자와 정한다. 노드 형식이 다르면 측정한 형식을 기록하고 Task 4 Step 1의 `$` 함수와 Task 5 견본의 `querySelector('rect')`를 그 형식에 맞춘다.

- [ ] **Step 5: 헤드리스 PDF의 beforeprint 측정**

Run:
```bash
"$E" --headless=new --disable-gpu --no-pdf-header-footer --virtual-time-budget=8000 --print-to-pdf="$(cygpath -w "$OUT")\\probe.pdf" "http://localhost:8765/tests/_tmp-probe.html"
OUT="$OUT" python -B -c "import os,pypdf;r=pypdf.PdfReader(os.path.join(os.environ['OUT'],'probe.pdf'));print('BEFOREPRINT-FIRED' in ''.join(p.extract_text() for p in r.pages))"
```
Expected: `True` 또는 `False`가 출력된다. 값을 기록한다. `False`이면 Task 5 인쇄 시험은 인쇄용 CSS만으로 판정한다.

- [ ] **Step 6: 결과 보고와 정리**

네 결과를 사용자에게 보고한다. 서버 백그라운드 작업을 종료하고 `tests/_tmp-probe.html`을 지운 뒤 `.gitignore`만 커밋한다.

```bash
rm tests/_tmp-probe.html
git add .gitignore && git commit -m "임시 시험 파일을 커밋 대상에서 뺀다"
```

---

### Task 2: check.py 규칙 변경

**Files:**
- Modify: `check.py`
- Create: `tests/test_check.py`

**Interfaces:**
- Consumes: 없음
- Produces: `check.doc_scripts(html) -> str`(report-charts 표시 밖 `<script>` 내용), `check.mermaid_sources(html) -> str`, `check.script_urls(html) -> list[str]`, `check.script_strings(html) -> str`, `check.script_violations(html) -> list[str]`. `main()`이 `script_violations`를 함께 실행한다. 위반 메시지는 `"<규칙 이름>: N건 — 예: …"` 형식이다.

- [ ] **Step 1: 실패하는 시험 작성**

`tests/test_check.py`:

```python
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


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 시험이 실패하는지 확인**

Run: `python -B -m unittest discover -s tests -v`
Expected: FAIL. `AttributeError: module 'check' has no attribute 'script_violations'`와 함께 `test_animation_false_in_script_is_not_movement`, `test_banned_word_in_script_string`, `test_script_violation_already_in_original_is_note_only`가 실패한다.

- [ ] **Step 3: check.py 수정**

`check.py` 모듈 설명의 4행(`규격 위반(만듦새)과 …`)을 아래로 바꾼다.

```python
규격 위반(만듦새)과 페이지형 문서의 근거 없는 페이지와 라벨(제목·표 머리·도표 제목)의 명사구 여부와 한국어 금지어와 시각화 스크립트·Mermaid 원문의 규격 위반을 검사하고, 원본이 있으면 내용 보존(본문 문장·숫자)도 검사한다.
```

`EMOJI = …` 줄 아래에 추가한다.

```python
CHARTS_BLOCK = re.compile(r"/\* BEGIN report-charts[^*]*\*/.*?/\* END report-charts \*/", re.S)
LIB_URL = re.compile(r"^https://cdn\.jsdelivr\.net/npm/(?:echarts|mermaid|gsap)@([^/]+)/")
```

`style_violations`의 움직임 줄을 아래로 바꾼다.

```python
    rule("움직임", re.findall(r"(?:@keyframes\s+\w+|transition\s*:[^;}]+|animation\s*:[^;}]+)", css)
         + re.findall(r"IntersectionObserver", html))
```

`style_violations` 함수 바로 뒤에 추가한다.

```python
def doc_scripts(html):
    """문서 스크립트: report-charts 표시 밖 <script>의 내용. 연결 코드는 build.py가 관리하므로 보지 않는다."""
    return "\n".join(re.findall(r"<script\b[^>]*>(.*?)</script>", CHARTS_BLOCK.sub("", html), re.S))


def mermaid_sources(html):
    return "\n".join(re.findall(r'<pre class="mermaid[^"]*"[^>]*>(.*?)</pre>', html, re.S))


def script_urls(html):
    """<script src>와 문서 스크립트의 import 주소."""
    js = doc_scripts(html)
    return (re.findall(r'<script\b[^>]*\bsrc="([^"]+)"', html)
            + re.findall(r"""\bimport\b[^'"()]*?\bfrom\s*['"]([^'"]+)['"]""", js)
            + re.findall(r"""\bimport\s*\(\s*['"]([^'"]+)['"]""", js)
            + re.findall(r"""\bimport\s+['"]([^'"]+)['"]""", js))


def script_strings(html):
    """문서 스크립트의 따옴표 문자열. 금지어 검사에 넣는다."""
    found = re.findall(r"""'((?:[^'\\\n]|\\.)*)'|"((?:[^"\\\n]|\\.)*)"|`([^`]*)`""", doc_scripts(html))
    return " ".join(a or b or c for a, b, c in found)


def script_violations(html):
    """시각화 스크립트와 Mermaid 원문의 규격 위반."""
    js, mmd, out = doc_scripts(html), mermaid_sources(html), []

    def rule(name, hits):
        if hits:
            out.append(f"{name}: {len(hits)}건 — 예: {hits[0][:80]}")

    urls = script_urls(html)
    rule("차트 애니메이션", re.findall(r"animation\s*:\s*true", js))
    rule("허용 밖 스크립트", [u for u in urls if not LIB_URL.match(u)])
    rule("버전 미고정", [u for u in urls if LIB_URL.match(u) and not re.fullmatch(r"\d+\.\d+\.\d+", LIB_URL.match(u).group(1))])
    rule("GSAP 직접 호출(play(tl, $) 안에서는 tl.to·tl.set을 쓴다)",
         re.findall(r"\bgsap\.\w+", js) + re.findall(r"\b(?:repeat\s*:\s*-?\s*[1-9]|yoyo\s*:\s*true)", js))
    rule("차트 장식", re.findall(r"shadowBlur\s*:\s*(?!0+(?:\.0+)?(?![\d.]))[^,}\s]+", js)
         + [m for m in re.findall(r"borderRadius\s*:\s*(\[[^\]]*\]|[\d.]+)", js)
            if any(float(n) >= 3 for n in re.findall(r"\d+(?:\.\d+)?", m))])
    js_no_ids = re.sub(r"""(?:querySelector(?:All)?|getElementById)\(\s*['"`][^'"`]*['"`]""", "", js)
    rule("스크립트·도식 색 리터럴",
         re.findall(r"""['"`][^'"`\n]*?(#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3}))\b""", js_no_ids)
         + re.findall(r"#[0-9a-fA-F]{3,8}\b", mmd)
         + re.findall(r"(?m)^\s*(?:style|classDef)\b.*$", mmd))
    return out
```

`all_text`를 아래로 바꾼다.

```python
def all_text(html):
    return visible_text(html) + " " + visible_text(html, SvgText) + " " + script_strings(html)
```

`main()`의 `fails = …` 줄을 아래로 바꾼다. 원본에 이미 있던 스크립트 규칙 위반은 규칙 이름으로 대조해 참고로만 출력한다. 기존 HTML 수정 작업은 원본 스크립트를 바꾸지 않기 때문이다.

```python
    scripts = script_violations(new)
    if old is not None:
        old_rules = {f.split(":")[0] for f in script_violations(old)}
        kept = [f for f in scripts if f.split(":")[0] in old_rules]
        if kept:
            print(f"참고: 원본에 있던 스크립트 위반(원본 스크립트는 고치지 않는다) — {kept}")
        scripts = [f for f in scripts if f not in kept]
    fails = (style_violations(new) + scripts + label_violations(new)
             + page_violations(new) + banned_violations(new, old))
```

- [ ] **Step 4: 시험 통과 확인**

Run: `python -B -m unittest discover -s tests -v`
Expected: 모든 시험 OK.

- [ ] **Step 5: 기존 동작 회귀 확인**

Run: `python -B check.py template.html; python -B check.py template-paged.html`
Expected: 두 줄 모두 `위반 0건`.

- [ ] **Step 6: 커밋**

```bash
git add check.py tests/test_check.py
git commit -m "check.py에 시각화 스크립트·Mermaid 규칙을 추가하고 움직임 검사를 CSS로 좁힌다"
```

---

### Task 3: build.py 연결 코드 삽입과 버전 대조

`report-charts.js`가 아직 없으므로 첫 줄만 있는 파일을 먼저 만든다. 본문은 Task 4에서 채운다.

**Files:**
- Modify: `build.py`
- Create: `report-charts.js`(첫 줄만)
- Create: `tests/test_build.py`

**Interfaces:**
- Consumes: 없음
- Produces: `report-charts.js`의 첫 줄 형식 `/* report-charts for echarts@6.1.0 mermaid@11.17.2 gsap@3.15.0`. build.py는 이 줄에서 대상 버전을 읽는다. 성공 출력은 `<파일>: 기준 CSS 반영` 또는 `<파일>: 기준 CSS 반영, 연결 코드 반영`이다. 버전이 다르면 파일을 고치지 않고 종료 코드 1로 멈춘다.

- [ ] **Step 1: `report-charts.js` 첫 줄 작성**

```js
/* report-charts for echarts@6.1.0 mermaid@11.17.2 gsap@3.15.0 */
```

- [ ] **Step 2: 실패하는 시험 작성**

`tests/test_build.py`:

```python
"""build.py 시험. 실행: python -B -m unittest discover -s tests -v (스킬 폴더에서)"""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
CSS = "<style>\n/* BEGIN report-base (시험) */\n/* END report-base */\n</style>"
CHARTS = "<script>\n/* BEGIN report-charts 시험 */\n/* END report-charts */\n</script>"


def cdn(lib, ver):
    return f'<script src="https://cdn.jsdelivr.net/npm/{lib}@{ver}/dist/{lib}.min.js"></script>'


def build(path):
    return subprocess.run([sys.executable, "-B", str(ROOT / "build.py"), str(path)],
                          capture_output=True, text=True, encoding="utf-8", env=ENV)


class Build(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / "doc.html"

    def tearDown(self):
        self.dir.cleanup()

    def write(self, head):
        self.path.write_text(f"<html><head>{head}</head><body></body></html>", encoding="utf-8")

    def test_idempotent_with_charts(self):
        self.write(CSS + cdn("echarts", "6.1.0") + cdn("mermaid", "11.17.2") + cdn("gsap", "3.15.0") + CHARTS)
        r1 = build(self.path)
        first = self.path.read_bytes()
        r2 = build(self.path)
        self.assertEqual(r1.returncode, 0, r1.stderr)
        self.assertIn("연결 코드 반영", r1.stdout)
        self.assertEqual(first, self.path.read_bytes())
        self.assertEqual(r2.returncode, 0)
        text = self.path.read_text(encoding="utf-8")
        self.assertIn("report-charts for echarts@6.1.0", text)
        self.assertIn("/* BEGIN report-charts echarts@6.1.0 mermaid@11.17.2 gsap@3.15.0", text)

    def test_document_without_charts_gets_css_only(self):
        self.write(CSS + "<script>var x=1;</script>")
        r = build(self.path)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("연결 코드", r.stdout)
        self.assertIn("<script>var x=1;</script>", self.path.read_text(encoding="utf-8"))

    def test_rc_call_without_marker_stops(self):
        self.write(CSS + "<script>RC.chart(document.getElementById('c'),{});</script>")
        before = self.path.read_bytes()
        r = build(self.path)
        self.assertEqual(r.returncode, 1)
        self.assertIn("report-charts", r.stderr)
        self.assertEqual(before, self.path.read_bytes())

    def test_version_mismatch_stops(self):
        self.write(CSS + cdn("echarts", "6.0.0") + CHARTS)
        before = self.path.read_bytes()
        r = build(self.path)
        self.assertEqual(r.returncode, 1)
        self.assertIn("echarts", r.stderr)
        self.assertEqual(before, self.path.read_bytes())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: 시험이 실패하는지 확인**

Run: `python -B -m unittest tests.test_build -v`
Expected: `test_idempotent_with_charts`, `test_version_mismatch_stops`, `test_rc_call_without_marker_stops`가 FAIL. 지금 build.py는 연결 코드를 모른다.

- [ ] **Step 4: build.py 전체 교체**

```python
"""개선본 HTML의 BEGIN/END 표시 사이를 기준 파일로 다시 채운다.

사용법: python build.py <html>...  (여러 번 실행해도 결과가 같다)
- report-base: <style> 안의 표시를 report-base.css로 채운다. 이 표시는 필수다.
- report-charts: <script> 안의 표시를 report-charts.js로 채운다. 표시가 있는 문서만 채운다.
  문서의 CDN 주소 버전이 report-charts.js 첫 줄의 대상 버전과 다르면 채우지 않고 멈춘다.
  문서가 RC 함수를 호출하는데 이 표시가 없어도 멈춘다.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
BASE = (HERE / "report-base.css").read_text(encoding="utf-8")
CHARTS = (HERE / "report-charts.js").read_text(encoding="utf-8")
LIBS = dict(re.findall(r"(echarts|mermaid|gsap)@([\d.]+)", CHARTS.splitlines()[0]))
MARK = ("/* BEGIN report-charts " + " ".join(f"{k}@{v}" for k, v in LIBS.items())
        + " (build.py가 채운다. 손으로 고치지 않는다) */\n")
BLOCK = re.compile(r"(/\* BEGIN report-base[^*]*\*/\n).*?(/\* END report-base \*/)", re.S)
CHART_BLOCK = re.compile(r"/\* BEGIN report-charts[^*]*\*/\n.*?(/\* END report-charts \*/)", re.S)
CDN_VER = re.compile(r"cdn\.jsdelivr\.net/npm/(echarts|mermaid|gsap)@([^/\"']+)/")
RC_CALL = re.compile(r"\bRC\.(?:chart|demo|ma|color)\s*\(")

for name in sys.argv[1:]:
    p = Path(name)
    html = p.read_text(encoding="utf-8")
    if not BLOCK.search(html):
        sys.exit(f"{name}: BEGIN/END report-base 표시가 없다")
    out = BLOCK.sub(lambda m: m.group(1) + BASE + m.group(2), html)
    charts = bool(CHART_BLOCK.search(out))
    if not charts and RC_CALL.search(out):
        sys.exit(f"{name}: RC 함수를 호출하는데 BEGIN/END report-charts 표시가 없다. 템플릿의 연결 코드 <script>를 넣는다")
    if charts:
        wrong = {k: v for k, v in CDN_VER.findall(out) if LIBS.get(k) != v}
        if wrong:
            sys.exit(f"{name}: CDN 버전 {wrong}이 연결 코드의 대상 버전 {LIBS}과 다르다. 채우지 않았다")
        out = CHART_BLOCK.sub(lambda m: MARK + CHARTS + m.group(1), out)
    p.write_text(out, encoding="utf-8")
    print(f"{name}: 기준 CSS 반영" + (", 연결 코드 반영" if charts else ""))
```

- [ ] **Step 5: 시험 통과 확인**

Run: `python -B -m unittest discover -s tests -v`
Expected: `test_check`와 `test_build` 모두 OK.

- [ ] **Step 6: 커밋**

```bash
git add build.py report-charts.js tests/test_build.py
git commit -m "build.py가 연결 코드를 삽입하고 CDN 버전을 대조한다"
```

---

### Task 4: 연결 코드와 시각화 CSS

**Files:**
- Modify: `report-charts.js`(본문 작성)
- Modify: `report-base.css`

**Interfaces:**
- Consumes: Task 1의 Mermaid 노드 id 형식, Task 3의 첫 줄 형식
- Produces: 전역 `RC` 객체. `RC.ready: Promise`(DOM 준비, 글꼴 로드, Mermaid 렌더 완료), `RC.color(name: string) -> string`, `RC.ma(values: number[], n: number) -> (number|null)[]`, `RC.chart(box: HTMLElement, option: object) -> EChartsInstance|null`, `RC.demo(fig: HTMLElement, steps: {name: string, text: string, play: (tl, $) => void}[]) -> null`. `$(name)`은 figure 안에서 `#name` 요소나 Mermaid 노드 `g.node[id*="-name-"]`를 돌려준다. CSS 클래스는 `.viz`, `.viz-fail`, `pre.mermaid.rendered`, `.demo`, `.demo-static`, `.demo-ctl`, `.demo-cap`, `.demo-steps`다.

- [ ] **Step 1: `report-charts.js` 전체 작성**

```js
/* report-charts for echarts@6.1.0 mermaid@11.17.2 gsap@3.15.0
   보고서 시각화 연결 코드. build.py가 문서의 BEGIN/END report-charts 사이에 채운다. 원본은 이 파일이고, 문서 안에서 고치지 않는다.
   함수: RC.chart(상자, 옵션), RC.color(토큰 이름), RC.ma(값 배열, n), RC.demo(figure, 단계 배열). 규칙은 SKILL.md '시각화' 절에 있다. */
(function () {
  var root = document.documentElement;
  var FAIL = '시각화를 불러오지 못했습니다';
  var PRINT_W = 688; // A4 본문 폭(210mm - 좌우 여백 28mm)의 px 값
  var RC = window.RC = {};

  function tok(name) { return getComputedStyle(root).getPropertyValue('--' + name).trim(); }
  function fail(box) { box.textContent = FAIL; box.classList.add('viz-fail'); }
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  RC.color = function (name) {
    var v = tok(name);
    if (!v) console.error('RC.color: 없는 토큰 이름 ' + name);
    return v;
  };

  RC.ma = function (values, n) {
    var out = [], sum = 0;
    for (var i = 0; i < values.length; i++) {
      sum += values[i];
      if (i >= n) sum -= values[i - n];
      out.push(i >= n - 1 ? Math.round(sum / n * 1e8) / 1e8 : null);
    }
    return out;
  };

  /* 차트 */
  var themed = false, charts = [];
  function registerTheme() {
    if (themed) return;
    themed = true;
    var ink = tok('ink'), ink3 = tok('ink-3'), hair = tok('hair'), rule = tok('rule');
    var axis = { axisLine: { lineStyle: { color: rule } }, axisTick: { lineStyle: { color: rule } },
      axisLabel: { color: ink3 }, splitLine: { show: false } };
    echarts.registerTheme('report', {
      color: [tok('s1'), tok('s2'), tok('s3'), tok('s4'), tok('accent-2')],
      backgroundColor: 'transparent',
      textStyle: { fontFamily: tok('sans'), color: ink },
      categoryAxis: axis, timeAxis: axis,
      valueAxis: { axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: ink3 },
        splitLine: { lineStyle: { color: hair } } },
      legend: { textStyle: { color: ink3 }, icon: 'rect', itemWidth: 12, itemHeight: 8 },
      tooltip: { backgroundColor: tok('paper'), borderColor: hair, borderWidth: 1, textStyle: { color: ink },
        extraCssText: 'box-shadow:none;border-radius:0' },
      line: { symbol: 'none', lineStyle: { width: 1.5 } },
      bar: { itemStyle: { borderRadius: 0 } },
      pie: { itemStyle: { borderColor: tok('paper'), borderWidth: 1 } },
      candlestick: { itemStyle: { color: tok('neg'), color0: tok('s1'), borderColor: tok('neg'), borderColor0: tok('s1') } }
    });
  }
  RC.chart = function (box, option) {
    if (!box) { console.error('RC.chart: 차트 상자가 없다'); return null; }
    if (typeof echarts === 'undefined') { fail(box); return null; }
    try {
      registerTheme();
      var w = box.clientWidth || document.querySelector('main.doc').clientWidth; // 숨은 페이지는 폭이 0이다
      var h = box.clientHeight || parseFloat(getComputedStyle(box).height) || 320;
      var chart = echarts.init(box, 'report', { renderer: 'svg', width: w, height: h });
      option.animation = false;
      if (!option.tooltip) {
        var pie = (option.series || []).some(function (s) { return s.type === 'pie'; });
        option.tooltip = { trigger: pie ? 'item' : 'axis' };
      }
      chart.setOption(option);
    } catch (e) { // 차트 하나의 오류가 뒤의 시각화를 막지 않게 한다
      console.error('RC.chart', e);
      if (chart) chart.dispose();
      fail(box);
      return null;
    }
    charts.push({ chart: chart, box: box, h: h });
    new ResizeObserver(function () {
      if (box.clientWidth > 0 && box.clientWidth !== chart.getWidth()) chart.resize({ width: box.clientWidth, height: h });
    }).observe(box);
    return chart;
  };
  addEventListener('beforeprint', function () {
    charts.forEach(function (it) { it.chart.resize({ width: PRINT_W, height: it.h }); });
  });
  addEventListener('afterprint', function () {
    charts.forEach(function (it) {
      if (it.box.clientWidth > 0) it.chart.resize({ width: it.box.clientWidth, height: it.h });
    });
  });

  /* 도식 */
  function renderMermaid() {
    var pres = [].slice.call(document.querySelectorAll('pre.mermaid'));
    if (!pres.length) return null;
    if (typeof mermaid === 'undefined') { pres.forEach(fail); return null; }
    mermaid.initialize({
      startOnLoad: false, theme: 'base', securityLevel: 'strict', fontFamily: tok('sans'),
      flowchart: { curve: 'linear' },
      themeVariables: {
        fontFamily: tok('sans'), fontSize: '14px', background: tok('paper'), textColor: tok('ink'),
        primaryColor: tok('paper'), primaryTextColor: tok('ink'), primaryBorderColor: tok('ink'),
        secondaryColor: tok('tint'), tertiaryColor: tok('paper'), lineColor: tok('ink-2'),
        clusterBkg: tok('paper'), clusterBorder: tok('hair'), edgeLabelBackground: tok('paper'),
        actorBkg: tok('paper'), actorBorder: tok('ink'), actorTextColor: tok('ink'), actorLineColor: tok('hair'),
        signalColor: tok('ink'), signalTextColor: tok('ink'),
        noteBkgColor: tok('tint'), noteBorderColor: tok('hair'), noteTextColor: tok('ink')
      }
    });
    return pres.reduce(function (p, pre, i) {
      var src = pre.textContent;
      return p.then(function () { return mermaid.render('rc-mermaid-' + i, src); })
        .then(function (r) { pre.innerHTML = r.svg; pre.classList.add('rendered'); }, function () { fail(pre); });
    }, Promise.resolve());
  }
  RC.ready = new Promise(function (res) {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', res); else res();
  }).then(function () { return document.fonts ? document.fonts.ready : null; }).then(renderMermaid);

  /* 동작 예시 */
  RC.demo = function (fig, steps) {
    fig.classList.add('demo');
    var ctl = el('div', 'demo-ctl'), cap = el('p', 'demo-cap'), list = el('ol', 'demo-steps');
    var bPrev = el('button', null, '이전'), bPlay = el('button', null, '재생'),
        bNext = el('button', null, '다음'), bReset = el('button', null, '처음부터'), cnt = el('span', 'cnt');
    [bPrev, bPlay, bNext, bReset].forEach(function (b) { b.type = 'button'; ctl.appendChild(b); });
    ctl.appendChild(cnt);
    steps.forEach(function (s) {
      var li = el('li');
      li.appendChild(el('b', null, s.name));
      li.appendChild(document.createTextNode(' ' + s.text));
      list.appendChild(li);
    });
    var src = fig.querySelector('.src');
    [ctl, cap, list].forEach(function (n) { fig.insertBefore(n, src); });
    if (typeof gsap === 'undefined') { fig.classList.add('demo-static'); return null; }

    RC.ready.then(function () {
      var $ = function (name) {
        return fig.querySelector('[id="' + name + '"]') || fig.querySelector('g.node[id*="-' + name + '-"]');
      };
      var tl = gsap.timeline({ paused: true }), ends = [];
      try {
        steps.forEach(function (s, i) { s.play(tl, $); tl.addLabel('e' + i); ends.push(tl.duration()); });
      } catch (e) { // 단계 코드가 틀리면 동작하지 않는 버튼 대신 단계 설명 목록을 보인다
        console.error('RC.demo', e);
        tl.kill();
        fig.classList.add('demo-static');
        return;
      }
      var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
      var cur = 0, tw = null, timer = null, saved = 0, last = steps.length - 1;

      function show(i) {
        cur = i;
        cnt.textContent = (i + 1) + '/' + steps.length;
        cap.textContent = steps[i].name + ': ' + steps[i].text;
        bPrev.disabled = i === 0;
        bNext.disabled = i === last;
      }
      function stop() {
        tl.pause();
        if (tw) { tw.kill(); tw = null; }
        if (timer) { timer.kill(); timer = null; }
        bPlay.textContent = '재생';
      }
      function go(i, animate) {
        stop();
        if (animate && !reduce) tw = tl.tweenTo('e' + i, { onComplete: function () { tw = null; } });
        else tl.seek('e' + i);
        show(i);
      }
      function tick() {
        if (cur < last) { tl.seek('e' + (cur + 1)); show(cur + 1); timer = gsap.delayedCall(1.2, tick); } else stop();
      }
      function play() {
        if (cur === last) go(0, false);
        bPlay.textContent = '일시정지';
        if (reduce) timer = gsap.delayedCall(1.2, tick); else tl.play();
      }
      tl.eventCallback('onUpdate', function () { // 연속 재생 중에만 단계 표시를 따라가게 한다
        if (tw) return;
        var t = tl.time(), i = 0;
        while (i < last && ends[i] < t - 1e-6) i++;
        if (i !== cur) show(i);
      });
      tl.eventCallback('onComplete', function () { bPlay.textContent = '재생'; });
      bPrev.onclick = function () { go(Math.max(0, cur - 1), false); };
      bNext.onclick = function () { go(Math.min(last, cur + 1), true); };
      bReset.onclick = function () { go(0, false); };
      bPlay.onclick = function () { if (tl.isActive() || tw || timer) stop(); else play(); };
      new ResizeObserver(function () { if (fig.clientWidth === 0) stop(); }).observe(fig); // 다른 페이지로 넘기면 멈춘다
      addEventListener('beforeprint', function () { saved = cur; stop(); tl.seek('e' + last); });
      addEventListener('afterprint', function () { go(saved, false); });
      go(0, false);
    });
    return null;
  };
})();
```

Task 1 Step 4에서 측정한 노드 id가 `-A-` 형식이 아니면 `$` 함수의 두 번째 선택자를 측정한 형식으로 바꾼다.

- [ ] **Step 2: `report-base.css`에 시각화 규칙 추가**

`.brow .n{…}` 줄(102행) 뒤, `/* 번호 목록 형태의 단계 */` 앞에 추가한다.

```css

/* 시각화: 차트 상자, Mermaid 도식, 동작 예시. 규칙은 SKILL.md '시각화' 절에 있다 */
.viz{height:320px;margin-top:12px}
.viz-fail{display:flex;align-items:center;font-size:13px;color:var(--ink-3);border:1px solid var(--hair);padding:0 12px;min-height:48px}
pre.mermaid{margin:12px 0 0;font:inherit;font-size:13px;white-space:pre;overflow-x:auto;color:var(--ink-3)}
pre.mermaid.rendered{white-space:normal;text-align:center;color:var(--ink)}
pre.mermaid rect{rx:0;ry:0}
.demo-ctl{display:flex;flex-wrap:wrap;gap:6px 10px;align-items:center;margin-top:10px;font-size:13px;color:var(--ink-3)}
.demo-ctl button{font:inherit;font-size:13px;background:var(--paper);color:var(--ink);border:1px solid var(--hair);padding:3px 12px;cursor:pointer}
.demo-ctl button:disabled{color:var(--ink-3);cursor:default}
.demo-ctl .cnt{min-width:3.5em;color:var(--ink-2)}
.demo-cap{font-size:14.5px;color:var(--ink-2);margin:6px 0 0}
.demo-steps{display:none;font-size:13px;color:var(--ink-2);margin:8px 0 0;padding-left:1.4em}
.demo-static .demo-ctl,.demo-static .demo-cap{display:none}
.demo-static .demo-steps{display:block}
```

`@media print{…}` 블록의 `a{color:inherit;text-decoration:none}` 줄 뒤에 추가한다.

```css
  .demo-ctl,.demo-cap{display:none}
  .demo-steps{display:block}
  .viz{height:auto}
  .viz>div{width:100%!important;height:auto!important}
  .viz svg,pre.mermaid svg{width:100%;max-width:100%;height:auto}
```

ECharts의 SVG 렌더러는 svg를 고정 px 폭의 `div`로 감싸고 svg에 viewBox를 둔다. 그래서 인쇄에서는 감싸는 `div`의 폭을 풀어야 svg가 viewBox 비율대로 용지 폭에 맞춰 줄어든다.

- [ ] **Step 3: 검사기 회귀 확인**

Run: `python -B -m unittest discover -s tests -v`
Expected: 모두 OK. `report-base.css`에 둥근 모서리·그림자·색 리터럴·움직임이 없으므로 템플릿 시험도 통과한다.

- [ ] **Step 4: 커밋**

```bash
git add report-charts.js report-base.css
git commit -m "시각화 연결 코드(report-charts.js)와 시각화 CSS를 추가한다"
```

---

### Task 5: 템플릿, 견본, 브라우저 시험

**Files:**
- Modify: `template.html`, `template-paged.html`
- Create: `tests/sample-viz.html`
- Create(임시): `tests/_tmp-dark.html`, `tests/_tmp-nogsap.html`

**Interfaces:**
- Consumes: Task 3의 build.py, Task 4의 `RC` API와 CSS 클래스
- Produces: 시각화 견본이 든 두 템플릿과 페이지형 견본 `tests/sample-viz.html`(p1 요약, p2 시계열, p3 파이, p4 도식 두 개, p5 동작 예시 두 개)

- [ ] **Step 1: 두 템플릿의 `<head>`에 라이브러리와 연결 코드 표시 추가**

두 템플릿 모두 `</style>` 바로 뒤에 추가한다. `template-paged.html`에서는 기존 페이지 넘김 `<script>`보다 앞에 둔다.

```html
<script src="https://cdn.jsdelivr.net/npm/echarts@6.1.0/dist/echarts.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11.17.2/dist/mermaid.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
<script>
/* BEGIN report-charts (build.py가 채운다. 손으로 고치지 않는다) */
/* END report-charts */
</script>
```

- [ ] **Step 2: `template.html` 본문에 시각화 견본 추가**

`template.html`의 `<p class="aside"><b>주의사항.</b> …</p>` 줄 뒤, `</section>` 앞에 추가한다.

```html
  <figure>
    <figcaption><span class="t">월별 거래대금 (2026년 1~6월)</span><span class="u">단위: 조원, 선은 3개월 이동평균</span></figcaption>
    <div class="viz" id="c-trend"></div>
    <p class="src">자료: 출처를 적습니다.</p>
  </figure>
  <figure>
    <figcaption><span class="t">주문 처리 흐름</span><span class="u">접수에서 정산까지</span></figcaption>
    <pre class="mermaid">flowchart LR
  A[주문 접수] --> B{금액 &lt; 한도}
  B -->|통과| C[체결]
  B -->|초과| X[거부]
  C --> D[정산]</pre>
    <p class="src">자료: 출처를 적습니다.</p>
  </figure>
  <figure id="d-flow">
    <figcaption><span class="t">주문 검증 과정 (동작 예시)</span><span class="u">버튼으로 단계를 넘깁니다</span></figcaption>
    <svg class="stage" viewBox="0 0 640 110" width="100%" role="img" aria-label="주문 검증 과정">
      <line x1="190" y1="55" x2="230" y2="55" stroke="currentColor"/>
      <line x1="410" y1="55" x2="450" y2="55" stroke="currentColor"/>
      <rect id="v1" x="10" y="33" width="180" height="44" fill="none" stroke="currentColor"/>
      <rect id="v2" x="230" y="33" width="180" height="44" fill="none" stroke="currentColor"/>
      <rect id="v3" x="450" y="33" width="180" height="44" fill="none" stroke="currentColor"/>
      <text x="100" y="60" text-anchor="middle" font-size="14">주문 접수</text>
      <text x="320" y="60" text-anchor="middle" font-size="14">한도 검증</text>
      <text x="540" y="60" text-anchor="middle" font-size="14">체결 전송</text>
      <circle id="dot" cx="100" cy="95" r="5" fill="currentColor" opacity="0"/>
    </svg>
    <p class="src">자료: 출처를 적습니다.</p>
  </figure>
```

`</main>` 바로 뒤에 문서 스크립트를 추가한다.

```html
<script>
var vol = [21.4, 23.1, 19.8, 25.6, 27.2, 24.9];
RC.chart(document.getElementById('c-trend'), {
  grid: { left: 40, right: 16, top: 32, bottom: 28 },
  legend: { top: 0, left: 0 },
  xAxis: { type: 'category', data: ['1월', '2월', '3월', '4월', '5월', '6월'] },
  yAxis: { type: 'value' },
  series: [
    { name: '거래대금', type: 'bar', barWidth: '50%', data: vol },
    { name: '3개월 이동평균', type: 'line', data: RC.ma(vol, 3) }
  ]
});
function mark(tl, target) { tl.to(target, { stroke: RC.color('accent'), strokeWidth: 2, duration: 0.4 }); }
RC.demo(document.getElementById('d-flow'), [
  { name: '주문 접수', text: '고객 주문이 접수 단계에 들어옵니다.',
    play: function (tl, $) { tl.set($('dot'), { opacity: 1, attr: { cx: 100 } }); mark(tl, $('v1')); } },
  { name: '한도 검증', text: '주문 금액을 고객 한도와 비교합니다.',
    play: function (tl, $) { tl.to($('dot'), { attr: { cx: 320 }, duration: 0.8 }); mark(tl, $('v2')); } },
  { name: '체결 전송', text: '검증을 통과한 주문을 거래소로 보냅니다.',
    play: function (tl, $) { tl.to($('dot'), { attr: { cx: 540 }, duration: 0.8 }); mark(tl, $('v3')); } }
]);
</script>
```

- [ ] **Step 3: `template-paged.html` 본문에 같은 견본 추가**

`template-paged.html`의 p2에서 `<p class="blk"><b>근거</b></p>` 뒤, `<div class="tbl"><table>` 앞에 Step 2의 `<figure>` 세 개를 그대로 넣는다. `</main>` 바로 뒤에 Step 2의 문서 스크립트를 그대로 넣는다.

- [ ] **Step 4: 템플릿 빌드와 검사**

Run:
```bash
python -B build.py template.html template-paged.html
python -B check.py template.html; python -B check.py template-paged.html
```
Expected: `template.html: 기준 CSS 반영, 연결 코드 반영`, `template-paged.html: 기준 CSS 반영, 연결 코드 반영`, 두 검사 모두 `위반 0건`.

- [ ] **Step 5: 견본 `tests/sample-viz.html` 작성**

`template-paged.html`을 `tests/sample-viz.html`로 복사한다. 복사본의 `<title>`을 `시각화 시험 견본`으로 바꾸고, `<nav class="pager">`부터 파일 끝까지를 아래로 바꾼다.

```html
<nav class="pager"><button id="prev" type="button">이전</button><span class="cnt" id="cnt"></span><button id="next" type="button">다음</button><span>화살표 키로도 넘깁니다</span></nav>
<p class="toc"><a href="#p1">1. 요약</a> · <a href="#p2">2. 거래대금 추이</a> · <a href="#p3">3. 시장별 구성</a> · <a href="#p4">4. 주문 처리 구조</a> · <a href="#p5">5. 주문 검증 과정</a></p>

<section class="page" id="p1"><p class="pno">1 / 5</p>
<header class="doc-head">
  <p class="doc-meta">시험 견본 · 2026년 9월</p>
  <h1>시각화 시험 견본</h1>
  <p class="lede">이 문서는 연결 코드의 렌더링과 동작과 인쇄를 시험합니다.</p>
  <div class="keyfig">
    <div><span class="k">페이지 수</span><span class="v">5</span><span class="d">요약 포함</span></div>
    <div><span class="k">시각화</span><span class="v">6</span><span class="d">차트 2, 도식 2, 동작 예시 2</span></div>
  </div>
</header>
</section>

<section class="page" id="p2"><p class="pno">2 / 5</p>
<h2>거래대금 추이</h2>
<ul class="pts"><li>6월 거래대금은 24.9조원으로 3개월 이동평균 25.9조원을 하회했습니다.</li></ul>
<p class="blk"><b>근거</b></p>
<figure>
  <figcaption><span class="t">월별 거래대금 (2026년 1~6월)</span><span class="u">단위: 조원, 선은 3개월 이동평균</span></figcaption>
  <div class="viz" id="c-trend"></div>
  <p class="src">자료: 시험용 가상 자료</p>
</figure>
<div class="tbl"><table>
  <caption>월별 거래대금 (조원)</caption>
  <thead><tr><th>월</th><th class="n">거래대금</th><th class="n">3개월 이동평균</th></tr></thead>
  <tbody>
    <tr><td>1월</td><td class="n">21.4</td><td class="n">–</td></tr>
    <tr><td>2월</td><td class="n">23.1</td><td class="n">–</td></tr>
    <tr><td>3월</td><td class="n">19.8</td><td class="n">21.43</td></tr>
    <tr><td>4월</td><td class="n">25.6</td><td class="n">22.83</td></tr>
    <tr><td>5월</td><td class="n">27.2</td><td class="n">24.20</td></tr>
    <tr><td>6월</td><td class="n">24.9</td><td class="n">25.90</td></tr>
  </tbody>
</table></div>
</section>

<section class="page" id="p3"><p class="pno">3 / 5</p>
<h2>시장별 구성</h2>
<ul class="pts"><li>6월 거래대금의 58%가 유가증권시장에서 발생했습니다.</li></ul>
<p class="blk"><b>근거</b></p>
<figure>
  <figcaption><span class="t">시장별 거래대금 비중 (2026년 6월)</span><span class="u">단위: %</span></figcaption>
  <div class="viz" id="c-share"></div>
  <p class="src">자료: 시험용 가상 자료</p>
</figure>
</section>

<section class="page" id="p4"><p class="pno">4 / 5</p>
<h2>주문 처리 구조</h2>
<ul class="pts">
  <li>주문은 접수·검증·체결·정산의 네 단계를 거칩니다.</li>
  <li>검증 단계는 주문 금액이 한도보다 작을 때만 주문을 체결로 넘깁니다.</li>
</ul>
<p class="blk"><b>근거</b></p>
<figure>
  <figcaption><span class="t">주문 처리 흐름</span><span class="u">접수에서 정산까지</span></figcaption>
  <pre class="mermaid">flowchart LR
  A[주문 접수] --> B{금액 &lt; 한도}
  B -->|통과| C[체결]
  B -->|초과| X[거부]
  C --> D[정산]</pre>
  <p class="src">자료: 시험용 가상 자료</p>
</figure>
<figure>
  <figcaption><span class="t">주문 호출 순서</span><span class="u">고객, 주문 시스템, 거래소</span></figcaption>
  <pre class="mermaid">sequenceDiagram
  participant 고객
  participant 주문 as 주문 시스템
  participant 거래소
  고객->>주문: 매수 주문
  주문->>거래소: 체결 요청
  거래소-->>주문: 체결 통보
  주문-->>고객: 체결 안내</pre>
  <p class="src">자료: 시험용 가상 자료</p>
</figure>
</section>

<section class="page" id="p5"><p class="pno">5 / 5</p>
<h2>주문 검증 과정</h2>
<ul class="pts"><li>주문은 접수 뒤 한도 검증을 통과해야 거래소로 전송됩니다.</li></ul>
<p class="blk"><b>근거</b></p>
<figure id="d-flow">
  <figcaption><span class="t">주문 검증 과정 (동작 예시)</span><span class="u">버튼으로 단계를 넘깁니다</span></figcaption>
  <svg class="stage" viewBox="0 0 640 110" width="100%" role="img" aria-label="주문 검증 과정">
    <line x1="190" y1="55" x2="230" y2="55" stroke="currentColor"/>
    <line x1="410" y1="55" x2="450" y2="55" stroke="currentColor"/>
    <rect id="v1" x="10" y="33" width="180" height="44" fill="none" stroke="currentColor"/>
    <rect id="v2" x="230" y="33" width="180" height="44" fill="none" stroke="currentColor"/>
    <rect id="v3" x="450" y="33" width="180" height="44" fill="none" stroke="currentColor"/>
    <text x="100" y="60" text-anchor="middle" font-size="14">주문 접수</text>
    <text x="320" y="60" text-anchor="middle" font-size="14">한도 검증</text>
    <text x="540" y="60" text-anchor="middle" font-size="14">체결 전송</text>
    <circle id="dot" cx="100" cy="95" r="5" fill="currentColor" opacity="0"/>
  </svg>
  <p class="src">자료: 시험용 가상 자료</p>
</figure>
<figure id="d-mmd">
  <figcaption><span class="t">정산 과정 (동작 예시)</span><span class="u">버튼으로 단계를 넘깁니다</span></figcaption>
  <pre class="mermaid">flowchart LR
  P[체결 확정] --> Q[대금 계산] --> R[결제]</pre>
  <p class="src">자료: 시험용 가상 자료</p>
</figure>
</section>

</main>
<script>
var vol = [21.4, 23.1, 19.8, 25.6, 27.2, 24.9];
RC.chart(document.getElementById('c-trend'), {
  grid: { left: 40, right: 16, top: 32, bottom: 28 },
  legend: { top: 0, left: 0 },
  xAxis: { type: 'category', data: ['1월', '2월', '3월', '4월', '5월', '6월'] },
  yAxis: { type: 'value' },
  series: [
    { name: '거래대금', type: 'bar', barWidth: '50%', data: vol },
    { name: '3개월 이동평균', type: 'line', data: RC.ma(vol, 3) }
  ]
});
RC.chart(document.getElementById('c-share'), {
  legend: { top: 0, left: 0 },
  series: [{ name: '시장별 비중', type: 'pie', radius: ['45%', '70%'], label: { formatter: '{b} {d}%' },
    data: [{ name: '유가증권시장', value: 58 }, { name: '코스닥시장', value: 35 }, { name: '코넥스시장', value: 7 }] }]
});
function mark(tl, target) { tl.to(target, { stroke: RC.color('accent'), strokeWidth: 2, duration: 0.4 }); }
RC.demo(document.getElementById('d-flow'), [
  { name: '주문 접수', text: '고객 주문이 접수 단계에 들어옵니다.',
    play: function (tl, $) { tl.set($('dot'), { opacity: 1, attr: { cx: 100 } }); mark(tl, $('v1')); } },
  { name: '한도 검증', text: '주문 금액을 고객 한도와 비교합니다.',
    play: function (tl, $) { tl.to($('dot'), { attr: { cx: 320 }, duration: 0.8 }); mark(tl, $('v2')); } },
  { name: '체결 전송', text: '검증을 통과한 주문을 거래소로 보냅니다.',
    play: function (tl, $) { tl.to($('dot'), { attr: { cx: 540 }, duration: 0.8 }); mark(tl, $('v3')); } }
]);
RC.demo(document.getElementById('d-mmd'), [
  { name: '체결 확정', text: '체결 내역을 확정합니다.', play: function (tl, $) { mark(tl, $('P').querySelector('rect')); } },
  { name: '대금 계산', text: '결제할 대금을 계산합니다.', play: function (tl, $) { mark(tl, $('Q').querySelector('rect')); } },
  { name: '결제', text: '대금과 증권을 주고받습니다.', play: function (tl, $) { mark(tl, $('R').querySelector('rect')); } }
]);
</script>
</body>
</html>
```

- [ ] **Step 6: 견본 빌드와 검사**

Run: `python -B build.py tests/sample-viz.html && python -B check.py tests/sample-viz.html && python -B -m unittest discover -s tests -v`
Expected: `기준 CSS 반영, 연결 코드 반영`, `위반 0건`, 시험 모두 OK.

- [ ] **Step 7: 서버 실행과 렌더링 시험(스크린샷)**

서버를 켠다(Bash 도구 `run_in_background`): `cd "$W" && python -B -m http.server 8765`. `curl -s -o /dev/null -w "%{http_code}" http://localhost:8765/tests/sample-viz.html`이 `200`을 출력하는지 확인한다.

다크 사본을 만들고, 페이지마다 밝은 모드와 다크 모드를 캡처한다.

```bash
sed 's/<html lang="ko">/<html lang="ko" data-theme="dark">/' tests/sample-viz.html > tests/_tmp-dark.html
for f in sample-viz _tmp-dark; do for p in 1 2 3 4 5; do
  "$E" --headless=new --disable-gpu --hide-scrollbars --window-size=1280,1400 --virtual-time-budget=8000 \
    --screenshot="$(cygpath -w "$OUT")\\$f-p$p.png" "http://localhost:8765/tests/$f.html#p$p"
done; done
```

Expected: 열 장의 PNG를 Read로 열어 아래 항목을 확인한다. 문제가 있으면 원인을 적고 Task 4의 해당 코드를 고친 뒤 다시 캡처한다.
- **그려짐:** 차트 두 개와 도식 두 개와 동작 예시 두 개가 모두 그려져 있다.
- **모양:** 막대와 노드가 직각이다.
- **색:** 계열 색이 토큰 색(남색·녹회색·황토색·회색)이다.
- **figure 구성:** 제목과 단위 줄과 출처 줄이 보인다.
- **다크 모드:** 다크 사본의 선과 글자가 어두운 바탕에서 읽힌다.

- [ ] **Step 8: 동작 시험(Playwright)**

`http://localhost:8765/tests/sample-viz.html`을 열고 아래를 차례로 확인한다. 페이지 이동 상태가 앞 항목에 이어지므로 순서대로 실행한다. 각 식은 `browser_evaluate`로 평가하고, 클릭은 식 안의 `.click()`으로 한다. 모든 식은 연결 코드 준비(`RC.ready`)를 기다린 뒤 실행된다.

1. 이동평균: `() => RC.ready.then(() => JSON.stringify(RC.ma([1,2,3,4],2)))` → `"[null,1.5,2.5,3.5]"`
2. 숨은 페이지 차트: `() => RC.ready.then(() => { document.getElementById('next').click(); return new Promise(r => setTimeout(() => { const b = document.getElementById('c-trend'); r([Math.round(b.querySelector('svg').getBoundingClientRect().width), b.clientWidth]); }, 500)); })` → 두 값의 차이가 1 이하
3. 숨은 페이지 도식과 `<` 문자: `() => RC.ready.then(() => { const n = document.getElementById('next'); n.click(); n.click(); const s = document.querySelector('#p4 pre.mermaid svg'); return [Math.round(s.getBoundingClientRect().width) > 0, s.textContent.includes('금액 < 한도')]; })` → `[true, true]`
4. 단계 넘김과 독립성: `() => RC.ready.then(() => { document.getElementById('next').click(); const f = document.getElementById('d-flow'), g = document.getElementById('d-mmd'); const next = f.querySelectorAll('.demo-ctl button')[2]; next.click(); next.click(); return new Promise(r => setTimeout(() => r([f.querySelector('.cnt').textContent, g.querySelector('.cnt').textContent]), 1500)); })` → `["3/3", "1/3"]`
5. 다음 뒤 재생: `() => RC.ready.then(() => { const b = document.getElementById('d-flow').querySelectorAll('.demo-ctl button'); b[3].click(); b[2].click(); return new Promise(r => setTimeout(() => { b[1].click(); const now = b[1].textContent; setTimeout(() => r([now, document.querySelector('#d-flow .cnt').textContent, b[1].textContent]), 2500); }, 2000)); })` → `["일시정지", "3/3", "재생"]`
6. Mermaid 노드 강조: `() => RC.ready.then(() => { document.getElementById('d-mmd').querySelectorAll('.demo-ctl button')[2].click(); return new Promise(r => setTimeout(() => r(getComputedStyle(document.querySelector('#d-mmd g.node[id*="-Q-"] rect')).stroke), 800)); })` → `rgb(31, 58, 95)`(밝은 모드의 `--accent`)
7. 페이지 이동 시 일시정지: `() => RC.ready.then(() => { const b = document.getElementById('d-flow').querySelectorAll('.demo-ctl button'); b[3].click(); b[1].click(); document.getElementById('prev').click(); return new Promise(r => setTimeout(() => { document.getElementById('next').click(); setTimeout(() => r(b[1].textContent), 300); }, 300)); })` → `"재생"`. 이전 페이지로 넘긴 뒤 300ms를 기다리는 이유는 `ResizeObserver`가 폭 0을 관측할 시간을 주기 위해서다.
8. 움직임 줄이기: `browser_emulate_media`로 `reducedMotion: "reduce"`를 켜고 `http://localhost:8765/tests/sample-viz.html#p5`를 다시 연 뒤 `() => RC.ready.then(() => { document.getElementById('d-flow').querySelectorAll('.demo-ctl button')[2].click(); return getComputedStyle(document.getElementById('v2')).stroke; })` → `rgb(31, 58, 95)`(전환 없이 즉시 끝 상태). 끝나면 `reducedMotion`을 `no-preference`로 되돌린다.
9. 좁은 화면: `browser_resize`로 390×800으로 바꾸고 `http://localhost:8765/tests/sample-viz.html#p2`를 다시 연 뒤 `() => RC.ready.then(() => new Promise(r => setTimeout(() => { const b = document.getElementById('c-trend'); r([b.querySelector('svg').getBoundingClientRect().width <= b.clientWidth + 1, document.documentElement.scrollWidth <= 390]); }, 800)))` → `[true, true]`. 끝나면 1280×900으로 되돌린다.
10. 라이브러리 로드 실패: `sed 's#gsap@3.15.0/dist/gsap.min.js#gsap@3.15.0/dist/none.js#' tests/sample-viz.html > tests/_tmp-nogsap.html`을 실행하고 `http://localhost:8765/tests/_tmp-nogsap.html#p5`를 연 뒤 `() => RC.ready.then(() => { const d = document.getElementById('d-flow'); document.getElementById('prev').click(); document.getElementById('prev').click(); document.getElementById('prev').click(); return new Promise(r => setTimeout(() => r([d.classList.contains('demo-static'), !!document.querySelector('#p4 pre.mermaid svg'), !!document.querySelector('#c-trend svg')]), 500)); })` → `[true, true, true]`

기대와 다르면 멈추고 원인과 사용자가 정할 것을 보고한다.

- [ ] **Step 9: 인쇄 시험**

Run:
```bash
"$E" --headless=new --disable-gpu --no-pdf-header-footer --virtual-time-budget=8000 \
  --print-to-pdf="$(cygpath -w "$OUT")\\sample-viz.pdf" "http://localhost:8765/tests/sample-viz.html"
```

Expected: PDF를 Read로 열어(`pages: "1-5"`) 아래 항목을 확인한다.
- **페이지 나눔:** 페이지마다 한 절이 인쇄된다.
- **폭:** 차트와 도식이 용지 폭 안에 있다.
- **동작 예시:** p5에서 조작 버튼과 설명 줄이 인쇄되지 않는다.
- **단계 목록:** p5에 동작 예시 두 개의 단계 설명 목록 여섯 줄이 인쇄된다.

차트가 용지 밖으로 넘치면 Task 1 Step 5의 `beforeprint` 측정 결과와 함께 보고하고, 인쇄 CSS의 `.viz>div` 규칙이 ECharts의 감싸는 `div`에 적용되었는지 확인한다.

- [ ] **Step 10: 정리와 커밋**

서버 백그라운드 작업을 종료한다.

```bash
rm -f tests/_tmp-dark.html tests/_tmp-nogsap.html
git add template.html template-paged.html tests/sample-viz.html
git commit -m "템플릿과 시험 견본에 차트·도식·동작 예시를 추가한다"
```

---

### Task 6: 지시 문서 갱신

**Files:**
- Modify: `SKILL.md`
- Modify: `보고서-규격.md`

**Interfaces:**
- Consumes: Task 4의 `RC` API, Task 2의 규칙 이름, Task 3의 build.py 출력 문구
- Produces: 모델이 따르는 '시각화' 절과 갱신한 완료 기준

- [ ] **Step 1: `SKILL.md` frontmatter description 갱신**

`description:` 줄을 아래로 바꾼다.

```yaml
description: HTML 보고서·검토 자료·제안서 페이지를 새로 만들거나, 기존 HTML 결과물의 만듦새를 고칠 때 연다. 차트(시계열·이동평균·파이·캔들)·도식(데이터 플로우·설계 구조·데이터 구조)·동작 예시 애니메이션이 필요한 HTML 보고서도 여기서 만든다. "AI가 만든 티가 난다", "보고서 규격대로", "검토용 HTML", "리서치 노트처럼", 결과를 HTML로 정리해 달라는 요청이 나오면 연다. 슬라이드(.pptx)와 웹 앱 화면은 대상이 아니다.
```

- [ ] **Step 2: 작업 방식 표의 '기존 HTML 수정' 행 갱신**

'기존 HTML 수정' 행의 '본문 글' 칸은 `고쳐 쓴다`로 끝난다. 그 뒤에 아래 문자열을 그대로 붙인다(앞의 마침표 포함, 칸 안의 다른 문장처럼 끝에는 마침표를 두지 않는다).

```
. 시각화는 추가하지 않고, '시각화' 절의 기준표에 해당하는 표를 보고에서 '시각화로 바꿀 수 있는 표' 목록으로 알린다
```

Run: `grep -c "고쳐 쓴다. 시각화는 추가하지 않고" SKILL.md`
Expected: `1`

- [ ] **Step 3: '## 시각화' 절 추가**

`## 페이지 구성` 절 끝(`도표를 불릿으로 옮겨 쓰지 않는다. …` 줄) 뒤, `## 독자 구분` 앞에 추가한다.

````markdown
## 시각화

새 문서에서 근거가 아래 기준표의 내용 유형에 해당하면, 표 대신 또는 표와 함께 해당 시각화를 쓴다. 시각화는 차트(ECharts), 도식(Mermaid 또는 직접 그린 SVG), 동작 예시(버튼으로 단계를 넘기는 애니메이션)를 묶어 가리키고, 모두 `figure`로 감싸는 도표다.

| 내용 유형 | 시각화 | 도구 | 쓰지 않는 조건 |
|---|---|---|---|
| 기간에 따른 값 변화(시계열) | 선 차트와 이동평균선 | ECharts + `RC.ma` | 시점이 4개 미만이면 표로 쓴다 |
| 시가·고가·저가·종가 | 캔들 차트와 거래량 막대 | ECharts | 조건 없이 쓴다 |
| 전체 중 구성비 | 파이(도넛) 차트 | ECharts | 항목이 6개를 넘거나 비율이 비슷하면 가로 막대로 쓴다 |
| 항목 간 크기 비교 | 가로 막대 차트 | ECharts 또는 `.bars`(CSS 막대 줄) | 값이 2~3개면 핵심 수치 줄(`.keyfig`)로 쓰고, 정확한 값 조회가 목적이면 표로 쓴다 |
| 두 변수의 관계 | 산점도 | ECharts | 조건 없이 쓴다 |
| 데이터 흐름과 처리 단계 | 흐름도 | Mermaid `flowchart` | 조건 없이 쓴다 |
| 모듈과 시스템 구조 | 블록 도식 | Mermaid `flowchart` + `subgraph` | 조건 없이 쓴다 |
| 주체 간 호출 순서 | 시퀀스 도식 | Mermaid `sequenceDiagram` | 조건 없이 쓴다 |
| 데이터 구조와 테이블 관계 | 클래스·ER 도식 | Mermaid `classDiagram`·`erDiagram` | 조건 없이 쓴다 |
| 상태 전이 | 상태 도식 | Mermaid `stateDiagram` | 조건 없이 쓴다 |
| 처리 과정의 동작 예시 | 동작 예시 | Mermaid 또는 SVG + `RC.demo` | 3단계 미만이면 정지 도식으로 쓴다 |

공통 규칙은 다음과 같다.

- **정확한 값 보존:** 독자가 값을 조회해야 하는 자료는 차트 아래에 표를 함께 둔다.
- **figure 구성:** 모든 시각화는 `figure` 안에 두고 도표 제목(`.t`), 단위·기간(`.u`), 본체, 출처 줄(`.src`)을 두며, 도표 제목과 축·범례는 `LABEL-NOUN`을 따른다.
- **도표 제목 위치:** 차트의 제목은 `figcaption .t`에만 쓰고 ECharts `title` 옵션은 쓰지 않는다.
- **도식 노드 모양:** Mermaid 노드는 직각 상자(`[텍스트]`)와 판단 마름모(`{텍스트}`)만 쓰고, 둥근 노드(`(텍스트)`, `([텍스트])`)와 `style`·`classDef`는 쓰지 않는다.
- **Mermaid 원문의 `<`:** 원문의 `<`는 `&lt;`로 적는다.
- **색:** 문서 스크립트의 색은 `RC.color('s1')`처럼 토큰 이름으로 받고 `#xxxxxx` 색은 쓰지 않는다.
- **장식 금지:** 3D, 그림자, 계열마다 채도 높은 색, 진입 애니메이션, 자동 반복(`repeat`, `yoyo`)을 쓰지 않는다.
- **움직임:** 움직임은 `RC.demo`의 `play(tl, $)` 안에서 `tl.to`·`tl.set`으로만 쓰고 `gsap.`을 직접 호출하지 않는다.

템플릿에는 스크립트가 세 층으로 들어 있다. `<head>`의 CDN 태그 세 줄과 연결 코드 `<script>`(BEGIN/END report-charts 표시)는 그대로 둔다. 연결 코드는 build.py가 `report-charts.js`에서 채워 넣는 `RC` 함수 모음이다. 문서마다 쓰는 문서 스크립트는 `</main>` 바로 뒤의 `<script>`에 둔다.

시각화가 하나도 없는 문서는 CDN 태그 세 줄과 연결 코드 `<script>`와 `</main>` 뒤 문서 스크립트를 모두 지운다. build.py는 문서 스크립트가 `RC` 함수를 호출하는데 연결 코드 표시가 없으면 멈춘다.

문서 스크립트가 쓰는 함수는 다음과 같다.

| 함수 | 쓰임 |
|---|---|
| `RC.chart(상자, 옵션)` | `<div class="viz" id="…">` 상자에 ECharts 옵션으로 차트를 그린다. 높이는 기본 320px이고 문서 전용 CSS로 바꾼다 |
| `RC.ma(값 배열, n)` | n개 이동평균 배열을 돌려준다. 앞의 n−1개는 `null`이다 |
| `RC.color(이름)` | 토큰 색 값을 돌려준다. 이름은 `s1`·`s2`·`s3`·`s4`·`accent`·`accent-2`·`neg`·`ink`·`ink-2`·`ink-3`·`hair`·`rule`·`paper`·`tint` 중 하나다 |
| `RC.demo(figure, 단계 배열)` | 단계 항목 `{name, text, play}`로 동작 예시를 만든다. `play(tl, $)`의 `$('이름')`은 figure 안에서 id가 `이름`인 요소나 Mermaid 노드 `이름`을 돌려준다 |

도식은 `<pre class="mermaid">` 안에 Mermaid 텍스트를 적으면 연결 코드가 그린다. 쓰는 방법은 `$S/template.html`의 견본 세 개(차트, 흐름도, 동작 예시)를 따른다.
````

Run: `grep -c "^## 시각화$" SKILL.md; grep -c "RC.demo(figure, 단계 배열)" SKILL.md`
Expected: `1`과 `1`

- [ ] **Step 4: 완료 기준 갱신**

완료 기준 1번 줄을 아래로 바꾼다.

```markdown
1. `python $S/build.py <파일>.html` → "기준 CSS 반영" 출력. 시각화가 있는 문서는 ", 연결 코드 반영"까지 출력된다. CDN 버전이 다르다는 오류가 나면 문서의 CDN 태그를 템플릿의 세 줄로 바꾼다.
```

완료 기준 3번의 `--virtual-time-budget=4000`을 `--virtual-time-budget=8000`으로 바꾼다.

Run: `grep -c "연결 코드 반영" SKILL.md; grep -c "virtual-time-budget=4000" SKILL.md`
Expected: `1`과 `0`

완료 기준 4번의 불릿 목록 끝(`- **문서 간 일치:** …` 뒤)에 추가한다.

```markdown
   - **시각화 점검(새 문서만):** 절의 결론이 추세·구성비·흐름·동작에 관한데 근거가 표뿐이면, '시각화' 절 기준표의 시각화로 바꾸거나 바꾸지 않은 이유를 보고에 적는다.
   - **시각화 글자 점검:** ECharts의 축 이름과 범례를 모아 읽어 명사구인지 확인한다. 이 글자는 check.py의 라벨 검사 대상이 아니다.
```

- [ ] **Step 5: 흔한 실수 갱신**

'BEGIN/END 안의 직접 수정' 항목을 아래로 바꾼다.

```markdown
- **BEGIN/END 안의 직접 수정:** 다음 build.py 실행 때 사라진다. 공통 CSS는 `report-base.css`에서, 연결 코드는 `report-charts.js`에서 수정한다.
```

Run: `grep -c "연결 코드는 .report-charts.js.에서 수정한다" SKILL.md`
Expected: `1`

- [ ] **Step 6: `보고서-규격.md` 갱신**

구성 요소 규칙 표의 세 행을 아래로 바꾼다.

```markdown
| 도표 | 제목, 단위·기간, 본체, 출처 줄(`figure`). 차트·도식·동작 예시가 모두 이 구성을 따르고, 차트는 ECharts 규격 테마(`RC.chart`)로 그린다 | 도표를 감싼 카드, 둥근 막대 |
| 도식(SVG) | Mermaid 규격 테마(직각 노드) 또는 직접 그린 SVG. 1px 선, 흰 바탕, 모서리 직각 | 파스텔 채움 상자, 둥근 상자(rx 3 이상), 둥근 Mermaid 노드 |
| 움직임 | 없음. 차트에서 값을 보여 주는 마우스오버 설명은 기능이므로 둔다. 동작 예시(`RC.demo`)의 단계 재생만 허용하고, 조작 버튼을 반드시 둔다 | 스크롤하면 떠오르는 효과, 장식용 hover 효과, 자동 반복 애니메이션, 차트 진입 애니메이션 |
```

'검사기가 검출하는 위반' 절의 첫 문장을 아래로 바꾼다.

```markdown
`check.py`는 둥근 모서리, 그림자, 그라데이션, CSS 움직임, 왼쪽 색 띠, 대문자 변환과 자간 확대, 허용 밖 웹폰트, 모노 글꼴 직접 지정, 알약 배지, 이모지, 토큰 밖 색 리터럴을 검출한다. 시각화에서는 차트 애니메이션, 허용 밖 스크립트, 버전 미고정 CDN 주소, GSAP 직접 호출과 자동 반복, 차트의 그림자와 둥근 막대, 문서 스크립트와 Mermaid 원문의 색 리터럴을 검출한다.
```

같은 절의 둘째 문장(`같은 폴더 금지어.md의 한국어 금지어도 검출한다.`)을 아래로 바꾼다.

```markdown
같은 폴더 `금지어.md`의 한국어 금지어도 검출하며, 대상에는 문서 스크립트의 문자열이 포함된다.
```

Run: `grep -c "RC.chart" 보고서-규격.md; grep -c "RC.demo" 보고서-규격.md; grep -c "GSAP 직접 호출" 보고서-규격.md`
Expected: 세 값 모두 `1` 이상

- [ ] **Step 7: 금지어 검사와 커밋**

Run: `python -B -c "import sys,re;sys.path.insert(0,'.');import check;[print(f,dict(check.banned_hits(re.sub(r'\`[^\`]*\`','',open(f,encoding='utf-8').read()),check.banned_rules()))) for f in ['SKILL.md','보고서-규격.md']]"`
Expected: 두 파일 모두 `{}`. 금지어가 나오면 대신 쓰는 말로 고친다.

```bash
git add SKILL.md 보고서-규격.md
git commit -m "SKILL.md와 보고서-규격.md에 시각화 규칙을 추가한다"
```

---

### Task 7: 스킬 동작 시험과 병합

**Files:**
- 없음(산출물은 세션 scratchpad에 둔다)

**Interfaces:**
- Consumes: Task 2~6의 완성된 스킬(`$W`)
- Produces: 통과 또는 실패 판정과 근거, 통과 시 `$S`에 병합된 `viz` 브랜치

- [ ] **Step 1: 서브에이전트 실행**

`general-purpose` 서브에이전트 하나에 아래 프롬프트를 준다. `<W>`는 worktree 절대 경로, `<OUT>`은 scratchpad 절대 경로다. 시각화 지시와 문서 형식(단일·페이지형) 지시는 주지 않는다.

```
<W>/SKILL.md 를 읽고 그 지시대로 작업하라. 이 파일 안의 $S 는 <W> 로 읽는다. 글쓰기 전에 같은 폴더의 글쓰기-규칙.md 도 읽어라.
요청: 월별 거래대금 12개월 자료와 주문 처리 흐름(접수→검증→체결→정산)을 정리한 검토 자료를 HTML로 만들어라.
거래대금 자료는 아래 값을 쓴다(단위 조원, 2025년 10월~2026년 9월): 22.1, 20.4, 23.8, 21.4, 23.1, 19.8, 25.6, 27.2, 24.9, 26.3, 28.0, 25.5
결과 파일은 <OUT>/skill-test.html 로 저장하고, SKILL.md 완료 기준의 build.py 와 check.py 를 실행해 출력 원문을 보고하라.
```

- [ ] **Step 2: 판정**

Run: `python -B check.py "$OUT/skill-test.html"`
Expected: `위반 0건`

`$OUT`을 기준으로 서버를 켠다(Bash 도구 `run_in_background`): `cd "$OUT" && python -B -m http.server 8766`. 이어서 캡처한다.

```bash
"$E" --headless=new --disable-gpu --hide-scrollbars --window-size=1280,3200 --virtual-time-budget=8000 \
  --screenshot="$(cygpath -w "$OUT")\\skill-test.png" "http://localhost:8766/skill-test.html"
```

결과 파일과 PNG를 열어 네 조건을 확인한다.
- **시계열:** 시계열 차트와 `RC.ma` 이동평균선이 있고 PNG에 그려져 있다.
- **흐름:** 주문 처리 흐름이 흐름도나 동작 예시로 그려져 있다.
- **과시각화 없음:** 기준표에 해당하지 않는 표를 시각화로 바꾸지 않았다.
- **검사기:** check.py 위반이 0건이다.

페이지형 문서라 첫 페이지만 캡처되면 `#p2`, `#p3`처럼 페이지 주소를 바꿔 다시 캡처한다. 서버 백그라운드 작업을 종료한다.

- [ ] **Step 3: 실패 시 처리**

조건을 하나라도 충족하지 못하면 원인에 해당하는 `SKILL.md` 문안을 `$W`에서 고치고 커밋한 뒤 Step 1부터 다시 실행한다. 두 번 실패하면 멈추고 사용자에게 두 결과와 원인을 보고한다. 병합은 하지 않는다.

- [ ] **Step 4: 병합과 결과 보고**

통과하면 설치된 스킬에 병합하고 worktree를 지운다.

```bash
git -C "$S" status --short
git -C "$S" merge --ff-only viz
git -C "$S" worktree remove "$W"
git -C "$S" branch -d viz
git -C "$S" log --oneline -3
```

Expected: `status`가 아무것도 출력하지 않고, 병합이 fast-forward로 끝나며, 마지막 로그의 첫 줄이 `viz` 브랜치의 마지막 커밋이다. `status`에 변경이 있으면 병합하지 않고 사용자에게 알린다.

사용자에게 판정과 check.py 출력 원문을 보고하고, GitHub 저장소 push 여부를 묻는다.

<!-- spec-review: passed -->
