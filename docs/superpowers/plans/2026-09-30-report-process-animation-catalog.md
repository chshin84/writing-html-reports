# 보고서 작성 과정과 애니메이션 목록 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 보고서 작성 과정(0~6단계)과 애니메이션 목록을 스킬에 넣고, 스틱맨을 Open Peeps 상반신 그림으로 바꾸며, check.py가 애니메이션 유형과 배치를 검사하게 한다.

**Architecture:** 인물 그림은 로컬 원본 zip에서 `tools/build-peeps.py`가 만든 생성물 `report-peeps.js`이고, build.py가 연결 코드 블록에 함께 넣는다. `RC.icon`은 이름이 `RC_PEEPS`에 있으면 그 그림을 80×80으로 그린다. check.py는 `ANIM_TYPES` 목록을 원본으로 두고 `anim_violations`로 figure의 `data-anim`과 페이지 배치를 검사하며, 핵심 페이지 점수의 B는 애니메이션 figure를 빼고 센다.

**Tech Stack:** Python 3.12 표준 라이브러리(unittest, zipfile, json, re), 브라우저 JavaScript(GSAP 3.15.0 타임라인), SVG.

**Spec:** `docs/superpowers/specs/2026-09-30-report-process-animation-catalog-design.md`

## Global Constraints

- 저장소 루트는 `C:\Users\CHSHIN\.claude\skills\writing-html-reports`이고, 아래 경로는 모두 이 루트 기준이다.
- CDN 버전은 echarts@6.1.0, mermaid@11.17.2, gsap@3.15.0에 고정한다.
- 문서 스크립트와 SVG의 색은 토큰(`RC.color('이름')`, `var(--이름)`)만 쓰고 `#xxxxxx` 색은 쓰지 않는다.
- 움직임은 `RC.demo`의 `play(tl, $)` 안에서 `tl.to`·`tl.set`과 `RC.fx`로만 쓰고 `gsap.`을 직접 호출하지 않는다. `repeat`·`yoyo`를 문서 스크립트에 쓰지 않는다.
- 설명 상자 글은 30자 이하, 글 등장 1초 이내, 표시 시간 min(1 + 글자 수 ÷ 10, 4)초다(연결 코드가 강제한다).
- 문서 스크립트의 글자열도 금지어 검사 대상이다(`금지어.md`).
- 애니메이션은 별 표시 페이지당 1개, 파일당 최대 3개다.
- 애니메이션 목록의 유형 이름과 상태는 `구조`·`전후 전환`·`규칙 적용 재생`이 '사용 가능', `선별`·`표본 누적`·`충격 적용`·`분해 합산`이 '견본 대기'다.
- 스틱맨 네 가지: `person`(분기, crossed_arms-1, Suspicious), `person-guide`(안내, pointing_finger-1, Explaining), `person-done`(완료, robot_dance-1, Smile Big), `person-fail`(실패, resting-2, Tired). 머리는 Short 2, 크기는 상반신 80×80, 잘라 내는 viewBox는 `0 150 1500 1500`이다.
- 스틱맨 배치: 스틱맨 중심은 설명 상자 x에서 48을 뺀 x와 설명 상자 y에 32를 더한 y에 둔다. 물음표는 스틱맨과 같은 x, 설명 상자 y에서 22를 뺀 y에 둔다. `RC.check`는 스틱맨을 그림 모양이 아니라 80×80 사각형 경계로 판정하므로, 이 배치는 사각형끼리 닿지 않게 정한 값이다.
- 용어: 버튼으로 단계를 넘기는 재생 요소 전체를 '애니메이션'이라 부르고, '동작 예시'라는 옛 이름은 SKILL.md 머리 설명(description)의 검색어에만 괄호로 남긴다.
- 원본 묶음(`assets/open-peeps-src/`)은 git에 넣지 않는다.
- 단위 시험 명령: `python -B -m unittest discover -s tests` (저장소 루트에서).
- 커밋 메시지는 한국어로 쓰고 끝에 다음 두 줄을 붙인다.
  `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`
  `Claude-Session: https://claude.ai/code/session_011bEydASHZ29CUABXZ6fja6`

## 설계와 다른 점

- **그림자 제거 없음:** 설계는 '발밑 그림자 제거'를 적었으나 고른 Open Peeps 조각 아홉 개를 측정한 결과 채움 색이 `#000000`과 `#FFFFFF`뿐이고 그림자가 없다. 그래서 그 단계는 두지 않고, 다른 채움 색이나 그라데이션이 나오면 멈추는 방어만 둔다.
- **새 견본 파일:** 설계는 전후 전환·규칙 적용 재생 견본을 `tests/sample-viz.html`에 넣기로 했으나, 그 파일에는 이미 애니메이션이 2개 있어 파일당 3개 상한을 넘는다. 두 견본은 새 파일 `tests/sample-anim.html`에 둔다. 목록의 '사용 가능' 뜻은 'tests 폴더의 견본 파일에 견본이 있고 `RC.check`를 통과한 상태'로 적는다.
- **페이지 규칙의 범위:** '페이지당 1개'와 '별 없는 페이지' 검사는 `section.page`가 있는 페이지형 문서에만 적용한다. 단일 문서에는 별 표시가 없기 때문이다.
- **인수 시험 방식:** 02 원본이 사용자에 의해 지워져 시험 사본을 다시 생성할 수 없다. 인수 시험은 `02-과정과-결론.skill-test.html`을 직접 고쳐 실행한다.

## Review Focus

- **어두운 화면:** 스틱맨의 선과 바탕 색은 만들 때 토큰 값을 읽으므로, 어두운 화면에서는 선이 밝은 색이고 바탕이 어두운 색이어야 한다. 작업 3 Step 5가 네 가지 스틱맨을 모두 어두운 화면에서 스크린샷으로 확인한다.
- **인쇄와 정지 상태:** 인쇄하면 마지막 단계로 이동하므로, 마지막 프레임이 결론 수치(31%, 43%, 22bp, 16bp)를 보여야 한다. 작업 6 Step 4가 마지막 단계의 글자를 확인한다.
- **figure를 변수로 넘긴 RC.demo:** `RC.demo(fig, …)`처럼 id 없이 넘기면 유형을 확인할 수 없으므로 위반으로 알려야 한다. 작업 4의 `test_demo_without_figure_id`가 이 입력을 시험한다.
- **애니메이션 figure 안의 Mermaid 판단 노드:** 애니메이션이 Mermaid로 그려져도 그 판단 노드는 B에서 빠져야 한다. 작업 5의 시험이 Mermaid `{…}` 노드를 포함한다.
- **원본 묶음이 없는 PC:** 다른 PC에는 zip이 없으므로, 생성 재현 시험만 건너뛰고 나머지 시험은 통과해야 한다. 작업 1의 `skipUnless`가 이 조건을 처리한다.

---

### 작업 1: 인물 그림 생성물

**Files:**
- Create: `tools/build-peeps.py`
- Create: `report-peeps.js` (생성물)
- Create: `assets/LICENSE-open-peeps.md`
- Test: `tests/test_peeps.py`

**Interfaces:**
- Produces: `report-peeps.js` 한 줄 머리 주석 뒤 `window.RC_PEEPS = {"figures": {이름: SVG 조각 문자열}, "viewBox": "0 150 1500 1500"};`. SVG 조각의 채움은 `class="pk"`(선 색)과 `class="pw"`(바탕 색)로 표시하고 색 값은 없다.
- Produces: `python tools/build-peeps.py [출력 경로]` (출력 경로를 생략하면 `report-peeps.js`).

- [ ] **Step 1: 실패하는 시험을 쓴다**

`tests/test_peeps.py`:

```python
"""인물 그림 생성물 시험. 실행: python -B -m unittest discover -s tests -v (스킬 폴더에서)"""
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PEEPS = ROOT / "report-peeps.js"
ZIP = ROOT / "assets" / "open-peeps-src" / "Flat Assets.zip"
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def load(path):
    text = path.read_text(encoding="utf-8")
    m = re.search(r"window\.RC_PEEPS = (\{.*\});\s*$", text, re.S)
    return text, json.loads(m.group(1))


class Peeps(unittest.TestCase):
    def test_four_figures_and_crop(self):
        text, data = load(PEEPS)
        self.assertEqual(sorted(data["figures"]), ["person", "person-done", "person-fail", "person-guide"])
        self.assertEqual(data["viewBox"], "0 150 1500 1500")
        self.assertTrue(text.startswith("/* report-peeps"))

    def test_no_color_literals(self):
        _, data = load(PEEPS)
        for name, svg in data["figures"].items():
            self.assertNotRegex(svg, r"#[0-9A-Fa-f]{3,6}\b", name)
            self.assertNotRegex(svg, r'fill="(?!none")', name)
            self.assertIn('class="pk"', svg, name)
            self.assertIn('class="pw"', svg, name)

    def test_size_budget(self):
        self.assertLess(PEEPS.stat().st_size, 130_000)

    @unittest.skipUnless(ZIP.exists(), "원본 묶음이 이 PC에 없다")
    def test_regenerates_identically(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "peeps.js"
            r = subprocess.run([sys.executable, "-B", str(ROOT / "tools" / "build-peeps.py"), str(out)],
                               capture_output=True, text=True, encoding="utf-8", env=ENV)
            self.assertEqual(r.returncode, 0, r.stderr)
            same = lambda p: p.read_bytes().replace(b"\r\n", b"\n")  # git이 체크아웃 때 줄바꿈을 바꿔도 비교가 흔들리지 않게 한다
            self.assertEqual(same(out), same(PEEPS))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 시험이 실패하는지 확인한다**

Run: `python -B -m unittest tests.test_peeps -v`
Expected: FAIL (`report-peeps.js`가 없어 FileNotFoundError)

- [ ] **Step 3: 생성 스크립트를 쓴다**

`tools/build-peeps.py`:

```python
"""Open Peeps 원본 묶음에서 스틱맨 네 가지를 조합해 report-peeps.js로 쓴다.

사용법: python tools/build-peeps.py [출력 경로]   (원본: assets/open-peeps-src/Flat Assets.zip)
원본의 채움 색은 검은색·흰색 두 가지라고 가정하고, 다른 색이나 그라데이션이 나오면 멈춘다.
"""
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "open-peeps-src" / "Flat Assets.zip"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "report-peeps.js"
ATOMS = "Flat Assets/Separate Atoms/"
HEAD = "Short 2"
CROP = "0 150 1500 1500"  # 머리 위부터 허리까지(상반신)
PEEPS = {  # 아이콘 이름: (자세, 표정)
    "person": ("crossed_arms-1", "Suspicious"),
    "person-guide": ("pointing_finger-1", "Explaining"),
    "person-done": ("robot_dance-1", "Smile Big"),
    "person-fail": ("resting-2", "Tired"),
}
FILL = {"#000000": "pk", "#FFFFFF": "pw"}  # pk: 선 색 토큰(ink), pw: 바탕 토큰(paper)
NUM = re.compile(r"-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?")


def rounded(m):
    v = f"{float(m.group(0)):.1f}".rstrip("0").rstrip(".")
    v = "0" if v in ("-0", "") else v
    nxt = m.string[m.end():m.end() + 1]
    return v + (" " if nxt and nxt in ".0123456789" else "")  # 반올림으로 경계가 붙지 않게 띄운다


def inner(z, name):
    s = z.read(ATOMS + name).decode("utf-8")
    s = re.sub(r"^.*?<svg[^>]*>", "", s, flags=re.S).rsplit("</svg>", 1)[0]
    s = re.sub(r"<title>.*?</title>|<desc>.*?</desc>|<!--.*?-->", "", s, flags=re.S)
    if re.search(r"Gradient|<image|style=", s):
        sys.exit(f"{name}: 그라데이션·이미지·style 속성이 있다. 처리하지 않는다")
    s = re.sub(r'\sid="[^"]*"', "", s)

    def color(m):
        v = m.group(1).upper()
        if v == "NONE":
            return m.group(0)
        if v not in FILL:
            sys.exit(f"{name}: 처리하지 않는 채움 색 {v}")
        return f' class="{FILL[v]}"'
    s = re.sub(r'\sfill="([^"]*)"', color, s)
    s = re.sub(r'\b(d|points|transform)="([^"]*)"', lambda a: f'{a.group(1)}="{NUM.sub(rounded, a.group(2))}"', s)
    return re.sub(r"\s+", " ", s).strip()


def peep(z, pose, face):
    return (f'<g transform="translate(-121,634)">{inner(z, f"pose/standing/{pose}.svg")}</g>'
            f'<g transform="translate(404,180)">{inner(z, f"head/{HEAD}.svg")}'
            f'<g transform="translate(159,186)">{inner(z, f"face/{face}.svg")}</g></g>')


if not SRC.exists():
    sys.exit(f"원본 묶음이 없다: {SRC} (assets/LICENSE-open-peeps.md의 주소에서 다시 받는다)")
with zipfile.ZipFile(SRC) as z:
    data = {"figures": {k: peep(z, *v) for k, v in PEEPS.items()}, "viewBox": CROP}
js = ("/* report-peeps: Open Peeps(Pablo Stanley, CC0 1.0) 조각을 조합한 스틱맨 그림이다. 생성물이므로 손으로 고치지 않고 "
      "tools/build-peeps.py를 실행한다 */\n"
      "window.RC_PEEPS = " + json.dumps(data, ensure_ascii=False, sort_keys=True) + ";\n")
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write(js)
print(f"{OUT}: 스틱맨 {len(data['figures'])}개, {len(js.encode('utf-8')):,}바이트")
```

- [ ] **Step 4: 생성물을 만들고 시험을 통과시킨다**

Run: `python -B tools/build-peeps.py`
Expected: `…report-peeps.js: 스틱맨 4개, N바이트` 출력. N은 90,000~100,000 사이다(계획 검수 때 같은 코드로 측정한 값은 91,486이다).

Run: `python -B -m unittest tests.test_peeps -v`
Expected: 4개 모두 PASS

- [ ] **Step 4-1: 네 그림이 사람 모양인지 눈으로 확인한다**

단위 시험은 생성물의 형식만 보므로, 조합 좌표나 반올림이 틀려 팔다리가 어긋나도 통과한다. 작업 폴더(scratchpad)에 아래 파일을 만들어 헤드리스 Edge로 찍는다.

```python
# scratchpad/peeps-sheet.py — 작업 폴더에서 실행한다
import json, re, pathlib
t = pathlib.Path(r"C:/Users/CHSHIN/.claude/skills/writing-html-reports/report-peeps.js").read_text(encoding="utf-8")
d = json.loads(re.search(r"window\.RC_PEEPS = (\{.*\});", t, re.S).group(1))
cells = "".join(
    f'<figure style="margin:8px;text-align:center"><svg width="160" height="160" viewBox="{d["viewBox"]}">'
    + d["figures"][k].replace('class="pk"', 'fill="#111418"').replace('class="pw"', 'fill="#FFFFFF"')
    + f"</svg><figcaption>{k}</figcaption></figure>" for k in sorted(d["figures"]))
pathlib.Path("peeps-sheet.html").write_text(f'<body style="display:flex">{cells}</body>', encoding="utf-8")
```

Run: `python peeps-sheet.py` 뒤 `"/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" --headless=new --disable-gpu --window-size=760,240 --screenshot=<작업 폴더 절대경로>\peeps-sheet.png "file:///<작업 폴더 절대경로>/peeps-sheet.html"`
Expected: 네 그림 모두 머리부터 허리까지의 사람이 얼굴 표정과 함께 보이고, 머리가 잘리거나 팔이 몸에서 떨어져 있지 않다. 이 미리 보기의 색 값은 확인용이며 생성물에는 들어가지 않는다. 확인한 뒤 `peeps-sheet.py`, `.html`, `.png`를 지운다.

- [ ] **Step 5: 라이선스 문서를 쓴다**

체크섬을 구한다.

Run: `python -c "import hashlib,pathlib;[print(p.name, hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(pathlib.Path('assets/open-peeps-src').iterdir())]"`

`assets/LICENSE-open-peeps.md` (체크섬 칸에는 위 명령의 출력을 그대로 옮긴다):

```markdown
# Open Peeps 출처와 라이선스

`report-peeps.js`의 스틱맨 네 가지는 Pablo Stanley의 Open Peeps 조각을 조합해 만든 생성물이다. Open Peeps는 CC0 1.0(공공 영역 헌정)으로 공개되어 출처 표시 없이 수정과 재배포를 할 수 있다.

- 공식 사이트: https://www.openpeeps.com/
- 다시 받는 주소: https://gum.co/openpeeps (가격 칸에 0을 넣는다)
- 원본 보관 위치: `assets/open-peeps-src/` (git에서 제외, 이 PC에만 있다)

| 원본 파일 | SHA-256 |
|---|---|
| (Step 5 명령 출력의 파일 이름) | (같은 줄의 해시) |

| 아이콘 이름 | 자세 | 표정 | 머리 |
|---|---|---|---|
| `person` | pose/standing/crossed_arms-1 | face/Suspicious | head/Short 2 |
| `person-guide` | pose/standing/pointing_finger-1 | face/Explaining | head/Short 2 |
| `person-done` | pose/standing/robot_dance-1 | face/Smile Big | head/Short 2 |
| `person-fail` | pose/standing/resting-2 | face/Tired | head/Short 2 |

원본이 사라지면 위 주소에서 다시 받아 SHA-256이 같은지 확인한 뒤 `assets/open-peeps-src/`에 두고 `python tools/build-peeps.py`를 실행한다.
```

- [ ] **Step 6: 전체 시험을 실행한다**

Run: `python -B -m unittest discover -s tests`
Expected: 45개(기존 41 + 새 4) OK

- [ ] **Step 7: 커밋한다**

```bash
git add tools/build-peeps.py report-peeps.js assets/LICENSE-open-peeps.md tests/test_peeps.py
git commit -m "스틱맨 그림 생성물(report-peeps.js)과 생성 스크립트, 출처·라이선스 문서를 추가한다"
```

### 작업 2: 연결 코드와 build.py에 스틱맨 연결

**Files:**
- Modify: `report-charts.js` (머리 주석 1~5행, `ICONS.person` 142~146행, `RC.icon` 163~170행)
- Modify: `build.py`
- Modify(재빌드): `template.html`, `template-paged.html`, `tests/sample-viz.html`
- Test: `tests/test_build.py`

**Interfaces:**
- Consumes: `window.RC_PEEPS` (작업 1)
- Produces: `RC.icon(svg, 'person' | 'person-guide' | 'person-done' | 'person-fail', x, y)` → `<g class="rc-icon">` 안에 80×80 `<svg>`를 (x, y) 중심에 두고 돌려준다. 처음 투명도 0.

- [ ] **Step 1: 실패하는 시험을 쓴다**

`tests/test_build.py`의 `Build` 클래스에 추가한다.

```python
    def test_peeps_inserted_in_chart_block(self):
        self.write(CSS + cdn("echarts", "6.1.0") + cdn("mermaid", "11.17.2") + cdn("gsap", "3.15.0") + CHARTS)
        r = build(self.path)
        self.assertEqual(r.returncode, 0, r.stderr)
        text = self.path.read_text(encoding="utf-8")
        block = text[text.index("/* BEGIN report-charts"):text.index("/* END report-charts */")]
        self.assertIn("window.RC_PEEPS", block)
```

- [ ] **Step 2: 시험이 실패하는지 확인한다**

Run: `python -B -m unittest tests.test_build -v`
Expected: `test_peeps_inserted_in_chart_block` FAIL (`window.RC_PEEPS` 없음)

- [ ] **Step 3: build.py가 스틱맨 데이터를 함께 넣게 한다**

`build.py` 머리 설명의 report-charts 줄 다음에 한 줄을 추가한다.

```python
  같은 블록에 report-peeps.js(스틱맨 그림 데이터)를 이어 넣는다.
```

`CHARTS = …` 줄 다음에 추가한다.

```python
PEEPS = (HERE / "report-peeps.js").read_text(encoding="utf-8")
```

채우는 줄을 바꾼다.

```python
        out = CHART_BLOCK.sub(lambda m: MARK + CHARTS + "\n" + PEEPS + m.group(1), out)
```

- [ ] **Step 4: RC.icon에 스틱맨을 넣고 옛 졸라맨 그리기를 지운다**

`report-charts.js` 5행의 `'동작 예시' 절`을 `'애니메이션' 절`로 바꾼다.

142~146행 `person: function (g, x, y) { // 졸라맨 … },` 다섯 줄을 지운다.

129행 주석을 다음으로 바꾼다.

```js
  /* 애니메이션 아이콘: 스틱맨(Open Peeps 상반신 80×80, report-peeps.js)과 1px 선으로 그린 상태 표시. (x, y)는 아이콘 중심이고, 처음에는 투명하다 */
```

`RC.icon` 함수 전체를 다음으로 바꾼다.

```js
  RC.icon = function (svg, name, x, y) {
    var P = window.RC_PEEPS;
    if (svg && P && P.figures[name]) { // 스틱맨: 선은 ink, 바탕은 paper 토큰으로 칠한다
      var pg = sv('g', { 'class': 'rc-icon', opacity: 0 }, svg);
      var box = sv('svg', { x: x - 40, y: y - 40, width: 80, height: 80, viewBox: P.viewBox }, pg);
      box.innerHTML = P.figures[name];
      [].forEach.call(box.querySelectorAll('.pk'), function (e) { e.setAttribute('fill', tok('ink')); });
      [].forEach.call(box.querySelectorAll('.pw'), function (e) { e.setAttribute('fill', tok('paper')); });
      return pg;
    }
    if (!svg || !ICONS[name]) { console.error('RC.icon: 무대가 없거나 없는 아이콘 이름 ' + name); return null; }
    var c = tok(ICON_COLOR[name] || 'ink');
    var g = sv('g', { 'class': 'rc-icon', fill: 'none', stroke: c, 'stroke-width': 1, opacity: 0 }, svg);
    ICONS[name](g, x, y);
    [].forEach.call(g.querySelectorAll('text'), function (t) { t.style.fill = c; }); // svg text의 기본 글자색 규칙보다 앞서게 한다
    return g;
  };
```

`think` 함수 주석의 '졸라맨'이 있으면 '스틱맨'으로 바꾼다.

`report-charts.js`에 남은 '동작 예시'(주석 4·129·172·200·208·316·433행, 오류 문구 438·466·468행)를 모두 '애니메이션'으로 바꾼다. 조사는 '동작 예시가'를 '애니메이션이'로, '동작 예시를'을 '애니메이션을'로 맞춘다. 바꾼 뒤 `grep -n "동작 예시" report-charts.js`의 출력이 없어야 한다.

- [ ] **Step 5: 시험과 재빌드를 실행한다**

Run: `python -B -m unittest discover -s tests`
Expected: 46개 OK

Run: `python -B build.py template.html template-paged.html tests/sample-viz.html`
Expected: 세 파일 모두 `기준 CSS 반영, 연결 코드 반영`

Run: `python -B check.py template.html && python -B check.py template-paged.html && python -B check.py tests/sample-viz.html`
Expected: 세 파일 모두 `위반 0건`

이 시점에는 `tests/sample-viz.html` 4쪽의 스틱맨이 80×80으로 커져 배치가 겹친다. check.py와 단위 시험은 브라우저 겹침을 보지 못하므로 통과한다. 그래서 작업 2와 작업 3은 끊지 않고 이어서 실행하고, 작업 3 Step 4의 겹침 판정을 통과하기 전에는 원격 저장소에 올리지 않는다. 작업 2 커밋 메시지에도 '구조 견본 배치는 다음 커밋에서 맞춘다'를 적는다.

- [ ] **Step 6: 커밋한다**

```bash
git add build.py report-charts.js tests/test_build.py template.html template-paged.html tests/sample-viz.html
git commit -m "RC.icon이 스틱맨 네 가지(Open Peeps 상반신 80×80)를 그리고 build.py가 그림 데이터를 연결 코드와 함께 넣는다(구조 견본 배치는 다음 커밋에서 맞춘다)"
```

### 작업 3: 구조 견본을 스틱맨으로 다시 배치

**Files:**
- Modify: `tests/sample-viz.html` (4쪽 `<svg class="stage" id="st-order" …>` 여는 태그, 문서 스크립트의 `var fx = RC.fx, st = …`부터 `d-order`의 `RC.demo(…);`까지)

**Interfaces:**
- Consumes: `RC.icon(st, 'person' | 'person-guide' | 'person-done' | 'person-fail', x, y)` (작업 2)

- [ ] **Step 1: 무대 위쪽을 넓힌다**

`<svg class="stage" id="st-order" viewBox="0 85 820 275"` → `<svg class="stage" id="st-order" viewBox="0 40 820 320"`

- [ ] **Step 2: 아이콘과 단계 코드를 바꾼다**

문서 스크립트에서 `var fx = RC.fx, st = document.getElementById('st-order');`부터 `d-order` 동작 예시의 `]);`까지를 다음으로 바꾼다.

```js
var fx = RC.fx, st = document.getElementById('st-order');
// 스틱맨(80×80)과 설명 상자는 한 쌍으로 도형 위에 둔다. 스틱맨 중심 = (상자 x − 48, 상자 y + 32), 물음표 = (스틱맨 x, 상자 y − 22)
var ic = {
  guide: RC.icon(st, 'person-guide', 60, 110), who: RC.icon(st, 'person', 222, 110), ask: RC.icon(st, 'question', 222, 56),
  ok: RC.icon(st, 'check', 222, 56), nx: RC.icon(st, 'cross', 222, 56),
  pass: RC.icon(st, 'person-done', 222, 110), fail: RC.icon(st, 'person-fail', 222, 110),
  won: RC.icon(st, 'coin', 450, 102), done: RC.icon(st, 'person-done', 570, 110), no: RC.icon(st, 'cross', 356, 320)
};
var nt = RC.note(st, 190, 64), fr = RC.focus(st), all = Object.keys(ic).map(function (k) { return ic[k]; });
// 단계 순서: 직전 쌍 지우기 → 도형에 초점 → 스틱맨과 설명 상자 → (판단이면) 고민·판정·표정 교체 → (나가는 엣지가 있으면) 엣지와 이동
RC.demo(document.getElementById('d-order'), [
  { name: '시나리오 A · 주문 접수', text: '고객 주문을 접수해 한도 검증으로 넘깁니다.', play: function (tl, $) {
    fx.clear(tl, nt, all); tl.set($('tok'), { opacity: 1, attr: { cx: 140, cy: 230 } }); fx.spot(tl, fr, $('s-acc'));
    fx.pair(tl, nt, ic.guide, 108, 78, '주문 A: 삼성전자 10주 × 72,000원 =', 0.5); fx.count(tl, nt.n, 0, 720000, '원', 0.4);
    fx.draw(tl, $('o-a'), 0.4); fx.follow(tl, $('tok'), $('o-a'), 0.4, '<'); } },
  { name: '시나리오 A · 한도 검증', text: '주문 금액이 한도 이내라 통과시켜 체결로 넘깁니다.', play: function (tl, $) {
    fx.clear(tl, nt, all); fx.spot(tl, fr, $('s-chk'));
    fx.pair(tl, nt, [ic.who, ic.ask], 270, 78, '주문 720,000원 < 한도', 0.4); fx.count(tl, nt.n, 0, 1000000, '원 ?', 0.4);
    fx.think(tl, ic.who, ic.ask); fx.swap(tl, ic.ask, ic.ok); fx.swap(tl, ic.who, ic.pass);
    fx.type(tl, nt.n, '1,000,000원 → 통과', 0.2, '<');
    tl.to($('l-pass'), { fill: RC.color('accent'), duration: 0.3 }, '<'); tl.set($('tok'), { attr: { cx: 345, cy: 230 } });
    fx.draw(tl, $('o-b'), 0.4); fx.follow(tl, $('tok'), $('o-b'), 0.4, '<'); } },
  { name: '시나리오 A · 체결', text: '거래소에서 체결된 주문을 정산으로 넘깁니다.', play: function (tl, $) {
    fx.clear(tl, nt, all); fx.spot(tl, fr, $('s-exe'));
    fx.pair(tl, nt, ic.won, 468, 78, '체결 72,000원 × 10주 =', 0.4); fx.count(tl, nt.n, 0, 720000, '원', 0.4);
    tl.set($('tok'), { attr: { cx: 540, cy: 230 } }); fx.draw(tl, $('o-c'), 0.4); fx.follow(tl, $('tok'), $('o-c'), 0.4, '<'); } },
  { name: '시나리오 A · 정산', text: '결제일에 대금과 주식을 주고받습니다.', play: function (tl, $) {
    fx.clear(tl, nt, all); fx.spot(tl, fr, $('s-set'));
    fx.pair(tl, nt, ic.done, 618, 78, 'T+2 결제일에 대금과 주식 교환', 0.6); } },
  { name: '시나리오 B · 주문 접수', text: '한도보다 큰 주문을 접수해 한도 검증으로 넘깁니다.', play: function (tl, $) {
    fx.clear(tl, nt, all); fx.unspot(tl, fr, [$('s-acc'), $('s-chk'), $('s-exe'), $('s-set')]);
    fx.undraw(tl, [$('o-a'), $('o-b'), $('o-c')]); tl.set($('l-pass'), { fill: RC.color('ink') });
    tl.set($('tok'), { attr: { cx: 140, cy: 230 } }); fx.spot(tl, fr, $('s-acc'));
    fx.pair(tl, nt, ic.guide, 108, 78, '주문 B: 삼성전자 25주 × 60,000원 =', 0.5); fx.count(tl, nt.n, 0, 1500000, '원', 0.4);
    fx.draw(tl, $('o-a'), 0.4); fx.follow(tl, $('tok'), $('o-a'), 0.4, '<'); } },
  { name: '시나리오 B · 한도 검증', text: '주문 금액이 한도를 넘어 거부로 넘깁니다.', play: function (tl, $) {
    fx.clear(tl, nt, all); fx.spot(tl, fr, $('s-chk'));
    fx.pair(tl, nt, [ic.who, ic.ask], 270, 78, '주문 1,500,000원 < 한도', 0.4); fx.count(tl, nt.n, 0, 1000000, '원 ?', 0.4);
    fx.think(tl, ic.who, ic.ask); fx.swap(tl, ic.ask, ic.nx); fx.swap(tl, ic.who, ic.fail); fx.shake(tl, ic.fail);
    fx.type(tl, nt.n, '1,000,000원 → 초과', 0.2, '<');
    tl.to($('l-over'), { fill: RC.color('neg'), duration: 0.3 }, '<'); tl.set($('tok'), { attr: { cx: 270, cy: 270 } });
    fx.draw(tl, $('o-r'), 0.3); fx.follow(tl, $('tok'), $('o-r'), 0.3, '<'); } },
  { name: '시나리오 B · 거부', text: '주문을 거부하고 고객에게 한도 부족을 안내합니다.', play: function (tl, $) {
    fx.clear(tl, nt, all); fx.spot(tl, fr, $('s-rej'), 'neg');
    fx.pair(tl, nt, ic.no, 374, 288, '한도 초과 → 주문 거부, 고객에게 안내', 0.6); fx.shake(tl, ic.no, '<0.35'); } }
]);
```

- [ ] **Step 3: 빌드와 검사기를 실행한다**

Run: `python -B build.py tests/sample-viz.html && python -B check.py tests/sample-viz.html`
Expected: `위반 0건`

- [ ] **Step 4: 겹침 판정을 실행한다**

저장소 루트에서 서버를 실행한다(백그라운드): `python -B -m http.server 8772`
Playwright로 `http://localhost:8772/tests/sample-viz.html#p4`를 열고 실행한다.

```js
async () => { await RC.ready; const r = await RC.check('d-order'); return JSON.stringify({pass: r.pass, error: r.error, of: r.overlapFrames, s: (r.overlapSamples || []).slice(0, 4), issues: r.issues}); }
```

Expected: `"pass":true`. 스틱맨은 80×80 사각형 경계로 판정되므로, 그림끼리 닿지 않아 보여도 사각형이 겹치면 실패한다. 겹침이 나오면 `overlapSamples`가 가리키는 아이콘의 x를 옮겨 Global Constraints의 스틱맨 배치 규칙 안에서 조정하고 다시 판정한다. 조정을 세 번 해도 통과하지 않으면 멈추고, 겹침 표본과 시도한 좌표를 사용자에게 알린다.

- [ ] **Step 5: 어두운 화면에서 네 스틱맨을 확인한다**

Playwright에서 `browser_emulate_media`로 `colorScheme: 'dark'`를 설정하고 페이지를 새로 연 뒤, 아래 네 시점마다 `d-order` figure 스크린샷을 찍는다. 시점은 1단계 끝(`person-guide`), 2단계의 고민 도중(`person`), 2단계 끝(`person-done`), 6단계 끝(`person-fail`)이다.

```js
async (t) => { await RC.ready; const f = document.getElementById('d-order'); const L = f._rcTl.labels; f._rcTl.seek(t === 'think' ? L.e0 + 1.2 : L[t], false); return 'ok'; }
```

이 함수에 `'e0'`, `'think'`, `'e1'`, `'e5'`를 차례로 넘긴다(Playwright `browser_evaluate`의 함수 본문에 값을 직접 넣어 네 번 실행한다).

Expected: 네 스크린샷 모두 스틱맨의 선이 밝은 색, 안쪽 바탕이 어두운 색으로 보인다. `think` 시점에 `person`이 보이지 않으면 1.2를 0.9~1.5 사이에서 바꿔 다시 찍는다. 확인한 뒤 `colorScheme: 'light'`로 되돌린다.

- [ ] **Step 6: 브라우저를 닫고 서버를 종료한다**

Playwright `browser_close`를 실행하고, PowerShell `Stop-Process -Id <서버 PID>`로 서버를 끈다. `~/.playwright-mcp` 폴더를 지운다.

- [ ] **Step 7: 커밋한다**

```bash
git add tests/sample-viz.html
git commit -m "구조 견본(주문 처리 과정)을 스틱맨 80×80 배치로 바꾸고 판정 결과에 따라 스틱맨 표정을 바꾼다"
```

### 작업 4: check.py 애니메이션 유형·배치 검사

**Files:**
- Modify: `check.py` (`star_violations` 다음에 `ANIM_TYPES`, `anim_violations` 추가, `main()` 연결)
- Modify: `template.html`, `template-paged.html` (`<figure id="d-flow">`에 `data-anim="구조"`)
- Modify: `tests/sample-viz.html` (`<figure id="d-order">`, `<figure id="d-mmd">`에 `data-anim="구조"`)
- Test: `tests/test_check.py`

**Interfaces:**
- Produces: `check.ANIM_TYPES: dict[str, str]` (유형 이름 → '사용 가능'|'견본 대기')
- Produces: `check.anim_violations(html: str) -> list[str]`

- [ ] **Step 1: 실패하는 시험을 쓴다**

`tests/test_check.py`의 `DemoCount.run_page`를 다음으로 바꾼다.

```python
    def run_page(self, n):
        body = "".join(f'<figure id="d{i}" data-anim="구조"><svg></svg></figure>' for i in range(n))
        script = "".join(f"RC.demo(document.getElementById('d{i}'),[]);" for i in range(n))
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "doc.html"
            f.write_text(page(body=body, script=script), encoding="utf-8")
            return run_check(f)
```

`class Stars` 앞에 추가한다.

```python
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
```

`class Original`에 추가한다.

```python
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
```

- [ ] **Step 2: 시험이 실패하는지 확인한다**

Run: `python -B -m unittest tests.test_check -v`
Expected: `Anim` 7개와 새 `Original` 시험 2개가 `AttributeError: module 'check' has no attribute 'anim_violations'` 또는 FAIL

- [ ] **Step 3: anim_violations를 구현한다**

`check.py`의 `star_violations` 함수 다음에 추가한다. `PAGE_ID`는 이 함수보다 뒤에 정의되어 있으므로 함수 안에서 이름으로만 참조한다(호출 시점에는 정의되어 있다).

```python
ANIM_TYPES = {  # 애니메이션 목록. SKILL.md '애니메이션' 절의 표와 같아야 한다(tests의 ListSync가 확인한다)
    "구조": "사용 가능", "전후 전환": "사용 가능", "규칙 적용 재생": "사용 가능",
    "선별": "견본 대기", "표본 누적": "견본 대기", "충격 적용": "견본 대기", "분해 합산": "견본 대기",
}
DEMO_ID = re.compile(r"\bRC\.demo\s*\(\s*document\.getElementById\(\s*['\"]([^'\"]+)['\"]\s*\)")


def anim_violations(html):
    """애니메이션 figure의 유형(data-anim)과 배치를 본다. 페이지 규칙은 페이지형 문서에만 적용한다."""
    scripts = doc_scripts(html)
    calls = len(re.findall(r"\bRC\.demo\s*\(", scripts))
    ids = DEMO_ID.findall(scripts)
    out = []
    if calls > len(ids):
        out.append(f"RC.demo 호출 {calls - len(ids)}개가 figure를 document.getElementById('figure id')로 넘기지 않는다(유형을 확인할 수 없다)")
    figs = {}
    for attrs in re.findall(r"<figure\b([^>]*)>", html):
        m = re.search(r'\bid="([^"]+)"', attrs)
        if m:
            figs[m.group(1)] = attrs
    for fid in ids:
        attrs = figs.get(fid)
        if attrs is None:
            out.append(f"애니메이션 figure가 없다: {fid}")
            continue
        t = re.search(r'\bdata-anim="([^"]*)"', attrs)
        if not t:
            out.append(f"애니메이션 유형 누락: {fid}에 data-anim이 없다")
        elif t.group(1) not in ANIM_TYPES:
            out.append(f"허용 밖 애니메이션 유형: {fid}의 '{t.group(1)}'은 목록에 없다")
        elif ANIM_TYPES[t.group(1)] != "사용 가능":
            out.append(f"허용 밖 애니메이션 유형: {fid}의 '{t.group(1)}'은 {ANIM_TYPES[t.group(1)]} 상태다(견본을 먼저 만든다)")
    for cls, pid, body in PAGE_ID.findall(html):
        n = sum(f'id="{fid}"' in body for fid in ids)
        if n > 1:
            out.append(f"{pid} 애니메이션 {n}개(페이지당 1개)")
        if n and not ({"core", "key"} & set(cls.split())):
            out.append(f"{pid} 별 표시 없는 페이지의 애니메이션(★·☆ 페이지에만 둔다)")
    return out
```

`main()`에서 `scores = score_violations(new, show=True)` 줄 앞에 추가한다. 원본 비교는 기존 `script_violations`의 '콜론 앞 규칙 이름 일치'가 아니라 설계 본문대로 '같은 문구 일치'로 한다. 애니메이션 위반 문구에는 figure id와 페이지 id가 들어 있어, 규칙 이름만 비교하면 원본에 없던 새 figure의 위반까지 참고로 빠지기 때문이다.

```python
    anims = anim_violations(new)
    if old is not None:
        old_anims = set(anim_violations(old))
        kept = [f for f in anims if f in old_anims]
        if kept:
            print(f"참고: 원본에 있던 애니메이션 위반(수정 작업이라 위반으로 세지 않는다) — {kept}")
        anims = [f for f in anims if f not in old_anims]
```

`fails = (…)` 식에 `+ anims`를 `star_violations(new)` 다음에 넣는다.

```python
    fails = (style_violations(new) + scripts + star_violations(new) + anims + scores + label_violations(new)
             + page_violations(new) + banned_violations(new, old))
```

- [ ] **Step 4: 기존 애니메이션 figure에 유형을 적는다**

`template.html`, `template-paged.html`: `<figure id="d-flow">` → `<figure id="d-flow" data-anim="구조">`
`tests/sample-viz.html`: `<figure id="d-order">` → `<figure id="d-order" data-anim="구조">`, `<figure id="d-mmd">` → `<figure id="d-mmd" data-anim="구조">`

- [ ] **Step 5: 시험과 검사기를 실행한다**

Run: `python -B -m unittest discover -s tests`
Expected: 55개 OK

Run: `python -B check.py template.html && python -B check.py template-paged.html && python -B check.py tests/sample-viz.html`
Expected: 세 파일 모두 `위반 0건`

- [ ] **Step 6: 커밋한다**

```bash
git add check.py tests/test_check.py template.html template-paged.html tests/sample-viz.html
git commit -m "check.py가 애니메이션 유형(data-anim)과 페이지당·별 없는 페이지 배치를 검사한다"
```

### 작업 5: 핵심 페이지 점수 B에서 애니메이션 figure 제외

**Files:**
- Modify: `check.py` (`page_scores`의 B 계산, 290행 설명)
- Test: `tests/test_check.py`

**Interfaces:**
- Consumes: 없음
- Produces: `page_scores`의 `B`가 `data-anim` figure 안의 `<polygon>`과 Mermaid `{…}` 노드를 세지 않는다.

- [ ] **Step 1: 실패하는 시험을 쓴다**

`tests/test_check.py`의 `Scores` 클래스에 추가한다.

```python
    def test_demo_figure_not_counted_in_branches(self):
        fig = ('<figure id="d1" data-anim="구조"><svg><polygon points="0,0 1,1"/></svg>'
               '<pre class="mermaid">flowchart LR\n A{판단} --> B[가]</pre></figure>')
        html = paged('<li data-src="p2">가</li>', {}).replace(
            "<h2>구조 A</h2>", "<h2>구조 A</h2>" + fig + '<svg><polygon points="0,0 1,1"/></svg>')
        rows = {x["id"]: x for x in check.page_scores(html)}
        self.assertEqual(rows["p2"]["B"], 1)
```

- [ ] **Step 2: 시험이 실패하는지 확인한다**

Run: `python -B -m unittest tests.test_check.Scores -v`
Expected: `test_demo_figure_not_counted_in_branches` FAIL (`3 != 1`)

- [ ] **Step 3: B 계산을 고친다**

`check.py`의 `WEIGHT = …` 줄 다음에 추가한다.

```python
ANIM_FIG = re.compile(r'<figure\b[^>]*\bdata-anim="[^"]*"[^>]*>.*?</figure>', re.S)
```

`page_scores` 설명의 B 줄을 바꾼다.

```python
    B 구조 복잡도: 이 페이지 정지 도식의 판단 분기 수(polygon 마름모, Mermaid {…} 노드). 애니메이션 figure는 세지 않는다.
```

루프 안의 `mermaid = …` 줄과 `"B": …` 줄을 다음으로 바꾼다.

```python
        static = ANIM_FIG.sub("", body)  # 애니메이션이 자기 페이지 점수를 올리지 않게 뺀다
        mermaid = " ".join(re.findall(r'<pre\b[^>]*\bclass="[^"]*\bmermaid\b[^"]*"[^>]*>(.*?)</pre>', static, re.S))
```

```python
             "B": len(re.findall(r"<polygon\b", static)) + len(re.findall(r"\w\{[^}\n]*\}", mermaid)),
```

- [ ] **Step 4: 시험을 실행한다**

Run: `python -B -m unittest discover -s tests`
Expected: 56개 OK

Run: `python -B check.py template-paged.html && python -B check.py tests/sample-viz.html`
Expected: 두 파일 모두 `위반 0건`(점수표의 별 평가와 표시가 여전히 같다)

- [ ] **Step 5: 커밋한다**

```bash
git add check.py tests/test_check.py
git commit -m "핵심 페이지 점수의 분기 수 B에서 애니메이션 figure 안의 마름모를 뺀다"
```

### 작업 6: 전후 전환·규칙 적용 재생 견본

**Files:**
- Create: `tests/sample-anim.html`

**Interfaces:**
- Consumes: `RC.icon`의 스틱맨 네 가지, `RC.note`, `RC.fx.clear/pair/say/count/draw/shake`, `RC.demo`, `RC.check`

- [ ] **Step 1: 템플릿을 복사해 본문을 바꾼다**

`template-paged.html`을 `tests/sample-anim.html`로 복사한다. `<title>…</title>`을 `<title>애니메이션 견본</title>`으로 바꾸고, `<main class="doc paged">`부터 파일 끝 `</html>`까지를 다음으로 바꾼다.

```html
<main class="doc paged">
<nav class="pager"><button id="prev" type="button">이전</button><span class="cnt" id="cnt"></span><button id="next" type="button">다음</button><span>화살표 키로도 넘깁니다</span></nav>
<p class="toc"><a href="#p1">1. 요약</a> · <a href="#p2" class="core">2. 모델 비중 변화</a> · <a href="#p3" class="key">3. 손절 규칙 효과</a></p>

<section class="page" id="p1"><p class="pno">1 / 3</p>
<header class="doc-head">
  <p class="doc-meta">시험용 견본 · 2026년 9월</p>
  <h1>애니메이션 견본</h1>
  <p class="lede">전후 전환과 규칙 적용 재생 애니메이션을 가상 자료로 보여 줍니다.</p>
  <div class="keyfig">
    <div data-src="p2"><span class="k">모델 A 비중</span><span class="v">50% → 31%</span><span class="d">가상 자료</span></div>
    <div data-src="p3"><span class="k">손절 효과</span><span class="v">−16bp</span><span class="d">가상 자료</span></div>
  </div>
</header>
<div class="gist">
  <h2>요약</h2>
  <ul>
    <li data-src="p2"><b>비중:</b> 제안안은 모델 A 비중을 50%에서 31%로 낮추고 모델 C 비중을 25%에서 43%로 높입니다.</li>
    <li data-src="p3"><b>손절:</b> 고정 손절은 회복 구간을 놓쳐 누적 손익을 38bp에서 22bp로 16bp 줄입니다.</li>
  </ul>
</div>
</section>

<section class="page core" id="p2"><p class="pno">2 / 3</p>
<h2>모델 비중 변화</h2>
<ul class="pts">
  <li>제안안은 모델 A 비중을 50%에서 31%로 낮추고 모델 C 비중을 25%에서 43%로 높입니다.</li>
  <li>모델 B 비중은 25%에서 26%로 거의 그대로입니다.</li>
</ul>
<p class="blk"><b>근거</b></p>
<figure id="d-shift" data-anim="전후 전환">
  <figcaption><span class="t">모델별 비중 (애니메이션)</span><span class="u">회색은 기준선, 짙은 색은 제안안</span></figcaption>
  <svg class="stage" id="st-shift" viewBox="0 0 700 290" width="100%" role="img" aria-label="모델별 비중 변화">
    <text x="30" y="155" font-size="14">모델 A</text>
    <text x="30" y="205" font-size="14">모델 B</text>
    <text x="30" y="255" font-size="14">모델 C</text>
    <rect id="b-a" x="110" y="138" width="400" height="24" style="fill:var(--s4)"/>
    <rect id="b-b" x="110" y="188" width="200" height="24" style="fill:var(--s4)"/>
    <rect id="b-c" x="110" y="238" width="200" height="24" style="fill:var(--s4)"/>
    <text id="v-a" x="530" y="155" font-size="14">50%</text>
    <text id="v-b" x="530" y="205" font-size="14">25%</text>
    <text id="v-c" x="530" y="255" font-size="14">25%</text>
  </svg>
  <p class="src">자료: 시험용 가상 자료</p>
</figure>
<div class="tbl"><table>
  <caption>모델별 비중(%)</caption>
  <thead><tr><th>모델</th><th class="n">기준선</th><th class="n">제안안</th></tr></thead>
  <tbody>
    <tr><td>모델 A</td><td class="n">50</td><td class="n">31</td></tr>
    <tr><td>모델 B</td><td class="n">25</td><td class="n">26</td></tr>
    <tr><td>모델 C</td><td class="n">25</td><td class="n">43</td></tr>
  </tbody>
</table></div>
<p class="blk"><b>중요 포인트</b></p>
<ul class="pts"><li><b>쏠림:</b> 비슷하게 움직이는 모델 A의 비중이 줄어 한 모델에 대한 쏠림이 낮아집니다.</li></ul>
<p class="blk warn"><b>유의사항</b></p>
<ul class="pts"><li><b>가상 자료:</b> 이 페이지의 수치는 견본용 가상 자료입니다.</li></ul>
<p class="blk"><b>출처</b></p>
<ul class="pts src-list"><li><b>시험용 가상 자료</b> — tests/sample-anim.html</li></ul>
</section>

<section class="page key" id="p3"><p class="pno">3 / 3</p>
<h2>손절 규칙 효과</h2>
<ul class="pts">
  <li>고정 손절은 회복 구간을 놓쳐 누적 손익을 38bp에서 22bp로 16bp 줄입니다.</li>
  <li>손절은 고점 대비 10bp 넘게 떨어진 4개월째에 발동하고 2개월 뒤 재진입합니다.</li>
</ul>
<p class="blk"><b>근거</b></p>
<figure id="d-rule" data-anim="규칙 적용 재생">
  <figcaption><span class="t">누적 손익 (애니메이션)</span><span class="u">단위: bp, 가상 자료 10개월</span></figcaption>
  <svg class="stage" id="st-rule" viewBox="0 0 720 260" width="100%" role="img" aria-label="손절 규칙 적용 재생">
    <path d="M60 200H620" fill="none" style="stroke:var(--hair)"/>
    <text x="52" y="204" font-size="12" text-anchor="end">0</text>
    <path id="r-base" d="M60 200L116 176L172 155L228 182L284 206L340 185L396 158L452 134L508 116L564 101L620 86" fill="none" style="stroke:var(--s1);stroke-width:1.5"/>
    <path id="r-1" d="M60 200L116 176L172 155L228 182L284 206" fill="none" style="stroke:var(--neg);stroke-width:2"/>
    <path id="r-2" d="M284 206L396 206L452 182L508 164L564 149L620 134" fill="none" style="stroke:var(--neg);stroke-width:2"/>
    <text id="lb-base" x="628" y="90" font-size="12" opacity="0">규칙 없음 38</text>
    <text id="lb-rule" x="628" y="138" font-size="12" opacity="0">고정 손절 22</text>
    <circle id="stop" class="rc-token" cx="284" cy="206" r="5" style="fill:var(--neg)" opacity="0"/>
  </svg>
  <p class="src">자료: 시험용 가상 자료</p>
</figure>
<div class="tbl"><table>
  <caption>누적 손익(bp)</caption>
  <thead><tr><th>구분</th><th class="n">4개월째</th><th class="n">10개월째</th></tr></thead>
  <tbody>
    <tr><td>규칙 없음</td><td class="n">−2</td><td class="n">38</td></tr>
    <tr><td>고정 손절</td><td class="n">−2</td><td class="n">22</td></tr>
  </tbody>
</table></div>
<p class="blk"><b>중요 포인트</b></p>
<ul class="pts"><li><b>회복 구간:</b> 손절 뒤 2개월 동안 누적 손익이 −2bp에서 14bp로 회복했지만 고정 손절은 그 구간을 보유하지 않았습니다.</li></ul>
<p class="blk warn"><b>유의사항</b></p>
<ul class="pts"><li><b>가상 자료:</b> 이 페이지의 수치는 견본용 가상 자료입니다.</li></ul>
<p class="blk"><b>출처</b></p>
<ul class="pts src-list"><li><b>시험용 가상 자료</b> — tests/sample-anim.html</li></ul>
</section>

</main>
<script>
var fx = RC.fx;
/* 전후 전환: 막대 하나가 한 단계다. 기준선(회색)에서 제안안(짙은 색)으로 길이와 값이 바뀐다. 1% = 8 */
(function () {
  var st = document.getElementById('st-shift'), nt = RC.note(st, 190, 64);
  var ic = { guide: RC.icon(st, 'person-guide', 150, 50), done: RC.icon(st, 'person-done', 150, 50) };
  var all = [ic.guide, ic.done];
  function grow(tl, $, bar, val, from, to) {
    tl.to($(bar), { attr: { width: to * 8 }, fill: RC.color('s1'), duration: 0.6 });
    fx.count(tl, $(val), from, to, '%', 0.4, '<');
  }
  RC.demo(document.getElementById('d-shift'), [
    { name: '전후 전환 · 모델 A', text: '비슷한 변형 7개를 한 묶음으로 보아 비중을 줄입니다.', play: function (tl, $) {
      fx.clear(tl, nt, all); fx.pair(tl, nt, ic.guide, 198, 18, '모델 A: 비슷한 변형 7개', 0.4); grow(tl, $, 'b-a', 'v-a', 50, 31); } },
    { name: '전후 전환 · 모델 B', text: '다른 모델과 따로 움직여 비중이 거의 그대로입니다.', play: function (tl, $) {
      fx.clear(tl, nt, all); fx.say(tl, nt, 198, 18, '모델 B: 거의 그대로', 0.4); grow(tl, $, 'b-b', 'v-b', 25, 26); } },
    { name: '전후 전환 · 모델 C', text: '따로 움직이는 모델 C가 가장 큰 비중을 받습니다.', play: function (tl, $) {
      fx.clear(tl, nt, all); fx.pair(tl, nt, ic.done, 198, 18, '모델 C: 따로 움직여 비중 증가', 0.4); grow(tl, $, 'b-c', 'v-c', 25, 43); } }
  ]);
})();
/* 규칙 적용 재생: 규칙 없는 경로를 먼저 그리고, 손절 발동·재진입 대기·결과를 차례로 보인다 */
(function () {
  var st = document.getElementById('st-rule'), nt = RC.note(st, 190, 64);
  var ic = { guide: RC.icon(st, 'person-guide', 100, 40), fail: RC.icon(st, 'person-fail', 236, 40),
    who: RC.icon(st, 'person', 348, 40), end: RC.icon(st, 'person-fail', 460, 40) };
  var all = Object.keys(ic).map(function (k) { return ic[k]; });
  RC.demo(document.getElementById('d-rule'), [
    { name: '규칙 적용 재생 · 규칙 없음', text: '규칙 없이 보유했을 때의 누적 손익을 그립니다.', play: function (tl, $) {
      fx.clear(tl, nt, all); fx.pair(tl, nt, ic.guide, 148, 8, '규칙 없이 보유한 누적 손익', 0.4);
      fx.count(tl, nt.n, 0, 38, 'bp', 0.4); fx.draw(tl, $('r-base'), 0.8, '<'); tl.to($('lb-base'), { opacity: 1, duration: 0.3 }); } },
    { name: '규칙 적용 재생 · 손절 발동', text: '고점 대비 10bp 넘게 떨어진 4개월째에 청산합니다.', play: function (tl, $) {
      fx.clear(tl, nt, all); fx.pair(tl, nt, ic.fail, 284, 8, '고점 15 → -2bp, 손절 발동', 0.5);
      fx.draw(tl, $('r-1'), 0.6, '<'); tl.to($('stop'), { opacity: 1, duration: 0.2 }); fx.shake(tl, ic.fail, '<'); } },
    { name: '규칙 적용 재생 · 재진입 대기', text: '2개월 기다린 뒤 다시 보유하지만 회복 구간을 놓칩니다.', play: function (tl, $) {
      fx.clear(tl, nt, all); fx.pair(tl, nt, ic.who, 396, 8, '2개월 대기 뒤 재진입', 0.4); fx.draw(tl, $('r-2'), 0.8, '<'); } },
    { name: '규칙 적용 재생 · 결과', text: '손절을 적용한 누적 손익이 규칙 없음보다 16bp 작습니다.', play: function (tl, $) {
      fx.clear(tl, nt, all); fx.pair(tl, nt, ic.end, 508, 8, '손절 적용 누적 22bp, 차이', 0.4);
      fx.count(tl, nt.n, 0, 16, 'bp 손해', 0.4); tl.to($('lb-rule'), { opacity: 1, duration: 0.3 }, '<'); } }
  ]);
})();
</script>
</body>
</html>
```

- [ ] **Step 2: 빌드와 검사기를 실행한다**

Run: `python -B build.py tests/sample-anim.html && python -B check.py tests/sample-anim.html`
Expected: 점수표에서 p2 평가 ★·표시 ★, p3 평가 ☆·표시 ☆, `위반 0건`. 금지어나 라벨 위반이 나오면 해당 글만 고친다.

- [ ] **Step 3: 겹침 판정을 실행한다**

저장소 루트에서 서버를 실행한다(백그라운드): `python -B -m http.server 8772`
Playwright로 `http://localhost:8772/tests/sample-anim.html#p2`를 열어 `RC.check('d-shift')`, 목차의 3쪽 링크를 누른 뒤 `RC.check('d-rule')`을 실행한다.

```js
async () => { await RC.ready; const a = await RC.check('d-shift'); document.querySelector('.toc a[href="#p3"]').click(); await new Promise(r => setTimeout(r, 300)); const b = await RC.check('d-rule'); const f = r => ({pass: r.pass, error: r.error, of: r.overlapFrames, s: (r.overlapSamples || []).slice(0, 4), issues: r.issues}); return JSON.stringify({shift: f(a), rule: f(b)}); }
```

Expected: 두 결과 모두 `"pass":true`. 글 규칙 위반(`issues`)이 나오면 설명 상자 글을 줄이거나 타이핑 시간을 줄인다. 겹침이 나오면 설명 상자와 스틱맨을 도식 위쪽 띠(y 0~84) 안에서 옮긴다.

- [ ] **Step 4: 마지막 프레임이 결론 수치를 보이는지 확인한다**

```js
async () => { const t = id => { const f = document.getElementById(id); f._rcTl.seek(f._rcTl.duration(), false); return f.querySelector('svg').textContent.replace(/\s+/g, ' '); }; document.querySelector('.toc a[href="#p2"]').click(); const a = t('d-shift'); document.querySelector('.toc a[href="#p3"]').click(); const b = t('d-rule'); return a + ' | ' + b; }
```

Expected: 앞부분에 `31%`, `26%`, `43%`, 뒷부분에 `규칙 없음 38`, `고정 손절 22`, `16bp 손해`가 들어 있다.

- [ ] **Step 5: 브라우저를 닫고 서버를 종료한다**

Playwright `browser_close`, PowerShell `Stop-Process -Id <서버 PID>`, `~/.playwright-mcp` 폴더 삭제.

- [ ] **Step 6: 커밋한다**

```bash
git add tests/sample-anim.html
git commit -m "전후 전환·규칙 적용 재생 애니메이션 견본(tests/sample-anim.html)을 추가한다"
```

### 작업 7: SKILL.md·보고서-규격.md 갱신과 목록 일치 시험

**Files:**
- Modify: `SKILL.md` ('작업 방식' 절 뒤에 '작업 과정' 절 추가, '동작 예시' 절 → '애니메이션' 절, '완료 기준' 절)
- Modify: `보고서-규격.md` ('검사기가 검출하는 위반' 절)
- Test: `tests/test_check.py`

**Interfaces:**
- Consumes: `check.ANIM_TYPES` (작업 4)

- [ ] **Step 1: 실패하는 시험을 쓴다**

`tests/test_check.py`의 `class Original` 앞에 추가한다.

```python
class ListSync(unittest.TestCase):
    def test_skill_table_matches_check(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        sec = text.split("\n## 애니메이션\n", 1)[1].split("\n## ", 1)[0]
        rows = {}
        for line in sec.splitlines():
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            if line.startswith("|") and len(cols) >= 2 and cols[-1] in ("사용 가능", "견본 대기"):
                rows[cols[0]] = cols[-1]
        self.assertEqual(rows, check.ANIM_TYPES)
```

- [ ] **Step 2: 시험이 실패하는지 확인한다**

Run: `python -B -m unittest tests.test_check.ListSync -v`
Expected: FAIL (`IndexError`: '## 애니메이션' 절이 아직 없다)

- [ ] **Step 3: '작업 과정' 절을 추가한다**

`SKILL.md`의 '작업 방식' 절 끝 문장 `문서 전용 CSS는 표시 뒤에 쓰고, 색은 토큰(`var(--…)`)만 쓴다.` 다음에 추가한다.

```markdown
## 작업 과정

보고서는 0~6단계를 차례로 거쳐 만들고, 0·1·2단계와 새 애니메이션 유형 등록에서 사용자 승인을 받는다. 앞 단계의 산출물이 뒤 단계의 입력이므로 순서를 바꾸지 않는다.

| 단계 | 산출물 | 확인 방법 | 사용자 승인 |
|---|---|---|---|
| 0. 독자와 전달 방식 | 독자, 전달 방식(발표·사전 배포·인쇄·오프라인) | 대화에서 사용자 확인 | 필요 |
| 1. 묶음 분할 | 파일 목록과 파일마다 답하는 독자의 질문 하나 | 문서 간 기간·수치·용어 일치 대조 | 필요 |
| 2. 파일 내용 정리 | 요약 결론, 결론별 근거 페이지(`data-src`), 핵심 수치 출처 | check.py가 `data-src` 누락을 검출 | 필요(요약 결론) |
| 3. 페이지 내용 정리 | '페이지 구성' 절 순서의 페이지 | check.py가 근거 없는 페이지를 검출 | 불필요 |
| 4. 시각화 | '시각화' 절 기준표에 따른 차트·도식 | 완료 기준의 시각화 점검 | 불필요 |
| 5. 핵심 페이지 | ★·☆ 표시 | check.py 점수표 | 불필요 |
| 6. 애니메이션 | 별 표시 페이지마다 1개 또는 없음 | `RC.check` 통과, 완료 기준의 애니메이션 선택 보고 | 새 유형 등록 때만 필요 |

인쇄로 전달하는 문서는 6단계를 생략하고, 정지 도식이나 표가 결론을 보여 준다. 오프라인으로 여는 문서는 4·6단계에서 CDN 도구를 쓰지 않고 정지 SVG와 표만 쓴다. 발표 자료는 발표자가 '다음' 버튼으로 한 단계씩 넘긴다.

1단계는 '파일 하나가 독자의 질문 하나에 답한다'를 기준으로 나눈다. 여러 파일에 같은 수치가 나오면 원천 자료 하나에서 가져온다.

기존 HTML을 고치는 작업은 본문 문장과 숫자를 바꾸지 않는다('작업 방식' 절). 이 작업에서 5단계 결과는 참고로만 알린다. 4·6단계는 시각화와 애니메이션을 추가하지 않고 후보 목록만 보고한다.
```

- [ ] **Step 4: '동작 예시' 절을 '애니메이션' 절로 바꾼다**

`## 동작 예시` 제목과 그 바로 아래 문단(`동작 예시는 HTML 파일 하나…4쪽(주문 처리 과정)이다.`)을 다음으로 바꾼다.

```markdown
## 애니메이션

애니메이션은 아래 목록의 유형만 쓰고, 별 표시 페이지(★·☆, '페이지 구성' 절의 평가)마다 하나까지 둔다. HTML 파일 하나에는 모두 3개를 넘지 않는다. figure에 `data-anim="유형 이름"`을 적고, `RC.demo(document.getElementById('figure id'), 단계 배열)`로 만든다. check.py가 유형 누락, 목록 밖·견본 대기 유형, 페이지당 2개 이상, 별 없는 페이지의 애니메이션, 파일당 4개 이상을 검출한다.

| 유형 | 보여 주는 것 | 내용 신호 | 마지막 프레임 | 쓰지 않는 조건 | 견본 | 상태 |
|---|---|---|---|---|---|---|
| 구조 | 예시 1건이 처리 과정과 분기를 지나는 순서 | 흐름도, 판단 분기가 있는 과정 | 마지막 도형의 처리 결과 | 3단계 미만 | `tests/sample-viz.html` 4쪽 | 사용 가능 |
| 전후 전환 | 같은 항목의 값이 기준선에서 제안안으로 바뀌는 변화 | 결론이 'A에서 B로'의 비교 | 제안안의 값과 변화량 | 항목 2개 미만 | `tests/sample-anim.html` 2쪽 | 사용 가능 |
| 규칙 적용 재생 | 규칙이 시간 순서대로 발동해 경로를 바꾸는 과정 | '~하면 ~한다' 규칙과 시계열 | 규칙 적용 전후의 누적값 차이 | 발동 시점이 없음 | `tests/sample-anim.html` 3쪽 | 사용 가능 |
| 선별 | 후보 N개가 기준을 거쳐 소수만 남는 과정 | 후보 수와 통과 수 | 남은 개수 | 후보 5개 미만(표로 둔다) | 없음 | 견본 대기 |
| 표본 누적 | 시행이 쌓이며 확률이 드러나는 과정 | 확률, 검정력, 모의실험 N회 | 해당 결과의 비율 | 시행별 결과가 없음 | 없음 | 견본 대기 |
| 충격 적용 | 시나리오를 보유에 적용한 손익 | 스트레스, 금리 충격 | 시나리오별 손익 범위 | 시나리오 2개 미만 | 없음 | 견본 대기 |
| 분해 합산 | 원천별 값이 쌓여 총계가 되는 과정 | 원천별 값의 합으로 이루어진 총계 | 총계와 비교 대상의 차이 | 원천 2개 미만 | 없음 | 견본 대기 |

'사용 가능'은 tests 폴더의 견본 파일에 견본이 있고 그 견본이 `RC.check`를 통과한 상태다. 목록은 `check.py`의 `ANIM_TYPES`와 같아야 하며, 단위 시험이 두 목록을 대조한다.

별 표시 페이지마다 다음 순서로 하나를 고른다.

1. 페이지 내용이 목록의 내용 신호에 해당하는 유형을 후보로 모은다. 후보가 없으면 애니메이션을 만들지 않는다.
2. 마지막 프레임이 페이지 결론(`ul.pts` 첫 줄)의 수치를 보여 주는 후보만 남긴다.
3. 여럿이 남으면 결론의 수치를 더 많이 보여 주는 후보를 고르고, 그래도 같으면 목록 순서를 따른다.
4. 고른 유형이 '견본 대기'이면 적용하지 않고 보고에서 제안한다. 사용자가 승인하면 견본을 먼저 만들어 '사용 가능'으로 바꾼 뒤 적용한다.

목록에 없는 유형이 필요하면 표의 칸을 모두 채워 사용자에게 제안한다. 승인을 받으면 견본을 만들고 `RC.check`를 통과시킨 뒤 이 표와 `check.py`의 `ANIM_TYPES`에 함께 추가한다.

모든 유형은 아래 공통 규칙과 이 절 뒤쪽의 무대 배치·글 규칙을 따른다.

- **예시 데이터:** 설명 상자에 보여 줄 값을 문서의 자료에서 먼저 발췌한다.
- **정지 상태:** 인쇄하거나 재생하지 않는 독자도 결론을 읽을 수 있도록, 마지막 프레임 또는 함께 둔 표가 페이지 결론의 수치를 보여 준다.

구조 유형은 다음을 더 지킨다. 분기가 있는 전체 견본은 `$S/tests/sample-viz.html` 4쪽(주문 처리 과정)이다.
```

- [ ] **Step 5: 아이콘과 판정 규칙을 스틱맨에 맞게 고친다**

'쌍 배치' 항목을 다음으로 바꾼다.

```markdown
- **쌍 배치:** 아이콘(`RC.icon`)과 설명 상자(`RC.note`)는 한 쌍으로 붙여 연출 중인 도형 바로 옆(보통 위)에 둔다. 한 번에 한 쌍만 보인다. 스틱맨 중심은 (설명 상자 x − 48, 설명 상자 y + 32)이고, 물음표는 (스틱맨 x, 설명 상자 y − 22)다. 도식 위쪽에 높이 약 110의 띠를 비워 두고, 모자라면 무대를 넓힌다.
```

'아이콘' 항목을 다음으로 바꾼다.

```markdown
- **아이콘:** 상태는 `RC.icon`의 아이콘으로만 표시하고 컬러 이모지는 쓰지 않는다. 스틱맨(Open Peeps 상반신 80×80)은 네 가지다. `person-guide`는 시나리오 첫 단계의 안내, `person`은 판단 도형의 고민, `person-done`은 통과·완료, `person-fail`은 거부·실패에 쓴다. 1px 선 아이콘은 `question`, `check`, `cross`, `doc`, `coin`이다.
```

`play` 순서 5번 항목을 다음으로 바꾼다.

```markdown
5. 판단 도형이면 `RC.fx.think`로 스틱맨이 고민한 뒤 `RC.fx.swap`으로 물음표를 판정 아이콘(✓·✕)으로 바꾸고, 스틱맨도 `RC.fx.swap`으로 `person-done`(통과)이나 `person-fail`(거부)로 바꾼다. 실패 스틱맨은 `RC.fx.shake`로 흔든다. 판정 글은 `RC.fx.type(tl, 설명 상자.n, 글, 시간, '<')`로 붙인다.
```

함수 표의 두 행을 바꾼다.

```markdown
| `RC.icon(무대, 이름, x, y)` | 아이콘을 (x, y) 중심에 만들고 요소를 돌려준다. 스틱맨은 80×80, 선 아이콘은 약 24×24다. 처음에는 보이지 않는다 |
```

```markdown
| `RC.fx.think(tl, person, question, at)` | 스틱맨이 고개를 갸웃하고 물음표가 깜빡인다(약 0.8초) |
```

- [ ] **Step 6: 완료 기준을 고친다**

'완료 기준' 절 4번 목록의 '동작 예시 판정' 항목을 다음으로 바꾸고, 그 뒤에 '애니메이션 선택 보고' 항목을 추가한다.

```markdown
   - **애니메이션 판정:** 문서가 있는 폴더에서 `python -B -m http.server <포트>`를 실행하고, Playwright로 문서를 열어 애니메이션마다 `RC.check('figure id')`를 실행한다. 페이지형 문서는 애니메이션이 있는 페이지로 이동(`#p3` 등)한 뒤 실행한다. 결과가 `pass: true`(겹침 프레임 0, 글 규칙 위반 0)여야 한다. 확인이 끝나면 브라우저를 닫고 서버를 종료한다.
   - **애니메이션 선택 보고:** 보고에 별 표시 페이지마다 한 줄씩 '페이지, 후보 유형, 고른 유형, 마지막 프레임이 보여 주는 결론 수치'를 적는다. 애니메이션을 만들지 않은 페이지는 그 이유를 적는다.
```

- [ ] **Step 7: 보고서-규격.md 검출 목록을 고친다**

'검사기가 검출하는 위반' 절의 문장 `목차의 ★·☆ 표시가 평가와 다르거나 요약 결론에 근거 페이지(`data-src`)가 없거나 별 표시·동작 예시가 상한(★ 1개, ☆ 2개, 합계 3개)을 넘으면 검출한다.`를 다음으로 바꾼다.

```markdown
목차의 ★·☆ 표시가 평가와 다르거나 요약 결론에 근거 페이지(`data-src`)가 없거나 별 표시·동작 예시가 상한(★ 1개, ☆ 2개, 합계 3개)을 넘으면 검출한다. 애니메이션은 유형(`data-anim`) 누락, 목록 밖·견본 대기 유형, 한 페이지에 2개 이상, 별 표시 없는 페이지의 배치를 검출한다.
```

- [ ] **Step 7-1: 남은 '동작 예시' 표현을 '애니메이션'으로 바꾼다**

Global Constraints의 용어 규칙대로, 같은 재생 요소를 두 이름으로 부르지 않게 아래 문장을 바꾼다. 왼쪽 글자를 찾아 오른쪽 글자로 바꾼다.

| 파일 | 찾을 글자 | 바꿀 글자 |
|---|---|---|
| SKILL.md 머리 설명 | `동작 예시 애니메이션이 필요한` | `애니메이션(동작 예시 포함)이 필요한` |
| SKILL.md '시각화' 절 첫 문단 | `동작 예시(버튼으로 단계를 넘기는 애니메이션)를 묶어 가리키고` | `애니메이션(버튼으로 단계를 넘기는 재생 요소)을 묶어 가리키고` |
| SKILL.md '시각화' 기준표 | `\| 처리 과정의 동작 예시 \| 동작 예시 \| Mermaid 또는 SVG + \`RC.demo\` \| 3단계 미만이면 정지 도식으로 쓴다 \|` | `\| 과정·전후 변화·규칙 적용처럼 단계로 보여 줄 내용 \| 애니메이션('애니메이션' 절 목록의 유형) \| SVG + \`RC.demo\` \| '애니메이션' 절 목록의 쓰지 않는 조건 \|` |
| SKILL.md 함수 표 `RC.demo` 행 | `로 동작 예시를 만든다.` | `로 애니메이션을 만든다.` |
| SKILL.md '시각화' 절 끝 문단 | `견본 세 개(차트, 흐름도, 동작 예시)를` | `견본 세 개(차트, 흐름도, 애니메이션)를` |
| SKILL.md '애니메이션' 절 함수 표 제목 | `동작 예시 함수는 다음과 같다.` | `애니메이션 함수는 다음과 같다.` |
| SKILL.md 함수 표 `RC.check` 행 | `동작 예시가 만들어지지 않았거나` | `애니메이션이 만들어지지 않았거나` |
| 보고서-규격.md '도표' 행 | `차트·도식·동작 예시가 모두` | `차트·도식·애니메이션이 모두` |
| template.html, template-paged.html, tests/sample-viz.html 도표 제목 | `(동작 예시)</span>` | `(애니메이션)</span>` |
| 보고서-규격.md '움직임' 행 | `동작 예시(\`RC.demo\`)의 단계 재생만 허용하고, 조작 버튼을 반드시 둔다. 작성 규칙은 SKILL.md '동작 예시' 절에 있다` | `애니메이션(\`RC.demo\`)의 단계 재생만 허용하고, 조작 버튼을 반드시 둔다. 작성 규칙은 SKILL.md '애니메이션' 절에 있다` |

표 안의 `\|`는 표 칸 구분이 아니라 찾을 글자 속의 세로선이다.

- [ ] **Step 8: 시험과 검사를 실행한다**

Run: `python -B -m unittest discover -s tests`
Expected: 57개 OK

Run: `grep -n "졸라맨" SKILL.md report-charts.js 보고서-규격.md`
Expected: 출력 없음

Run: `grep -n "동작 예시" SKILL.md report-charts.js 보고서-규격.md`
Expected: SKILL.md 머리 설명의 `애니메이션(동작 예시 포함)` 한 줄만 나온다

- [ ] **Step 9: 커밋한다**

```bash
git add SKILL.md 보고서-규격.md tests/test_check.py template.html template-paged.html tests/sample-viz.html
git commit -m "SKILL.md에 작업 과정(0~6단계)과 애니메이션 목록·선택 규칙을 넣고 목록 일치 시험을 추가한다"
```

### 작업 8: 인수 시험과 마무리

**Files:**
- Modify(저장소 밖): `D:\projects\bond-meta-backtest\제안서v2.1\02-과정과-결론.skill-test.html`

- [ ] **Step 1: 시험 사본에 유형을 적고 다시 빌드한다**

시험 사본의 `<figure id="d-pipe">` → `<figure id="d-pipe" data-anim="구조">`, `<figure id="d-hrp">` → `<figure id="d-hrp" data-anim="구조">`로 바꾸고 `python -B build.py <시험 사본>`을 실행한다.

- [ ] **Step 2: 점수표를 확인한다**

Run: `python -B check.py <시험 사본>`
Expected: 점수표 p9 줄이 `N1 R1 B0 C2 D0 = 11`, 평가 ★·표시 ★. p4 평가 ☆·표시 ☆. `위반 0건`.

- [ ] **Step 3: 스틱맨 배치를 새 크기에 맞춘다**

시험 사본 문서 스크립트에서 `RC.icon(st, 'person', …)`과 `RC.icon(st, 'question', …)` 좌표를 Global Constraints의 배치 규칙(스틱맨 = 상자 x − 48, 상자 y + 32, 물음표 = 스틱맨 x, 상자 y − 22)으로 바꾼다. 파이프라인 무대의 상자 x 최솟값을 96으로 올리고(`Math.max(96, …)`), 두 무대의 viewBox 위쪽을 물음표가 들어가도록 넓힌다(파이프라인 `0 60 880 300`, HRP `0 60 880 340`).

- [ ] **Step 4: 겹침 판정을 실행한다**

`D:\projects\bond-meta-backtest\제안서v2.1`에서 `python -B -m http.server 8773`을 실행하고, Playwright로 `#p4`에서 `RC.check('d-pipe')`, `#p9`에서 `RC.check('d-hrp')`를 실행한다.
Expected: 두 결과 모두 `"pass":true`. 실패하면 겹침 표본이 가리키는 아이콘·설명 상자 좌표를 옮겨 다시 판정한다.

- [ ] **Step 5: 전체 검증을 다시 실행한다**

Run: `python -B -m unittest discover -s tests`
Expected: 57개 OK

Run: `python -B check.py template.html && python -B check.py template-paged.html && python -B check.py tests/sample-viz.html && python -B check.py tests/sample-anim.html`
Expected: 네 파일 모두 `위반 0건`

`report-peeps.js` 실제 크기를 측정해 보고에 적는다: `python -c "import os;print(os.path.getsize('report-peeps.js'))"`

- [ ] **Step 6: 작업 흔적을 정리한다**

Playwright 브라우저를 닫고, 서버 프로세스를 `Stop-Process`로 끄고, `~/.playwright-mcp` 폴더를 지운다. 이 계획을 쓰기 전 설계 단계에서 만든 작업 폴더(scratchpad) 파일도 지운다. 대상은 인물 그림 후보를 비교한 `stick`·`peeps` 폴더, 02 시험 사본을 만들 때 쓴 `add_demos.py`·`rebuild.sh`, 한국어 답변 훅 초안 `korean-reply-check.py`·`install-korean-hook.py`다. 훅 초안 두 파일은 사용자가 설치를 마쳤는지 먼저 묻고, 설치했거나 설치하지 않기로 했을 때만 지운다. 각 이름이 작업 폴더에 실제로 있는지 `ls`로 확인한 뒤 있는 것만 지우고, 지운 목록을 보고에 적는다. 시험 사본은 사용자 폴더에 그대로 둔다.

<!-- spec-review: passed -->
