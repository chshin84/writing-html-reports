# C2 페이지 틀·CSS 구현 plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 공통 CSS와 템플릿을 고쳐 색 대비·색각 구분·390 폭 표·용어 목록·페이지 번호·주소 앵커 결함을 없애고, 절 이름 + 결론 제목 틀과 C3용 화면 요소(바뀐 칸·확인 상태·대체됨 배너)를 만든다.

**Architecture:** 결함은 되도록 `report-base.css`에서 고치며, 이 파일은 `build.py`가 관리 블록으로 모든 문서에 복사하므로 고정 견본에도 반영된다. 페이지 전환(`hashchange`)만 `template-paged.html`의 문서 스크립트에서 고친다. 결론 제목 검사는 `checks/style.py`의 새 규칙 함수로 두고 `RULES`에 원본 대조 방식 `old`로 등록한다.

**Tech Stack:** CSS(Chromium 기준, `:has()`·`subgrid`·`fit-content()`), Python 3 표준 라이브러리(`re`, `html.parser`), unittest, Python Playwright 1.63.0 헤드리스 Chromium(C0 하네스 `eval/`가 사용).

**Spec:** `docs/superpowers/specs/2026-10-04-c2-page-frame-design.md` (상위 설계 `docs/superpowers/specs/2026-10-04-report-quality-architecture-design.md`, 측정 도구 설계 `docs/superpowers/specs/2026-10-04-c0-eval-harness-design.md`)

## Global Constraints

- 고칠 수 있는 파일: `report-base.css`, `template.html`, `template-paged.html`, `checks/style.py`, `보고서-규격.md`, `tests/test_style.py`, 이 plan과 그 리뷰 기록. 그 밖의 파일은 읽기만 하고, 고쳐야 하면 작업을 멈추고 L2에게 BLOCKED로 알린다.
- 관리 블록(`/* BEGIN report-base … */`~`/* END report-base */`, `/* BEGIN report-charts … */`~`/* END report-charts */`)은 손으로 고치지 않는다. `report-base.css`를 고친 뒤 `python build.py template.html`과 `python build.py template-paged.html`로 다시 채운다.
- 작업 폴더는 `D:/projects/Structure/whr-c2`(브랜치 `c2-page-frame`)이고 모든 명령을 이 폴더에서 Bash로 실행한다. 측정 출력은 저장소 밖 `C:/Users/ho381/AppData/Local/Temp/c2w`에 두며, 명령마다 앞에 `W=C:/Users/ho381/AppData/Local/Temp/c2w;`를 붙인다(이하 `$W`). 이 경로에는 저장소 이름이 없다.
- 토큰은 밝은 테마 `:root`, `@media (prefers-color-scheme:dark)` 안 `:root:not([data-theme="light"])`, `:root[data-theme="dark"]`를 함께 고치고 기존 토큰 이름은 지우지 않는다. 값은 지금처럼 `#rrggbb`로 쓴다. C0 측정기 `eval/probe.js`의 색 정규화는 1×1 캔버스를 거치며, 캔버스가 읽지 못하는 표기에서 직전 색을 돌려줄 수 있다고 L1이 알렸다(이 plan에서 재현하지는 않았다).
- `--accent-2`: 두 테마에서 `--paper`·`--tint` 대비 3:1 이상, `--accent`와 대비 1.5:1 이상.
- `--s1`은 `--accent`와 같은 값. `--s2`~`--s4`는 두 테마에서 `--paper`·`--tint` 대비 3:1 이상. 제2색각 모의 변환(Machado 2009) 뒤 `--s1`~`--s4` 쌍마다 CIE76 색차 15 이상.
- `--ink-3`: 밝은 테마 `--tint` 대비 4.5:1 이상.
- 금지 서식(`checks/style.py`): 그라데이션, 그림자, 둥근 모서리(3px 이상), 왼쪽 색 띠(3px 이상), 토큰 밖 색 리터럴. 새 CSS도 이 규칙을 지킨다.
- 결론 제목: `<p class="sec">`가 있는 `section.page`의 직계 `h2`는 공백 포함 40자 이하이고 문장 어미로 끝난다. `.sec`은 명사구 검사(18자 이하)를 받는다.
- 확인 상태의 `data-state` 값은 `run`·`infer`·`assume`이고, 글자는 각각 '실행으로 확인함'·'추론함'·'가정함'을 작성자가 마크업에 쓴다. 이 값 이름은 C3 spec과의 계약이므로 바꾸지 않는다(L1 추가 지시).
- 문서·주석·커밋 메시지는 한국어 문어체로 쓴다. 커밋은 각 Task의 커밋 단계에 적힌 명령 그대로 만들며, 메시지 끝에 `Co-Authored-By`·`Claude-Session` 두 줄이 붙는다.
- 병합·push·main 변경은 하지 않는다.

## Review Focus

- **기존 문서의 `h2`:** `.sec`이 없는 페이지형 문서와 고정 견본은 결론 제목 검사를 받지 않고 명사구 검사만 받아야 한다. Task 2의 `test_page_without_sec_keeps_noun_check`가 이 조건을 고정한다.
- **요약 상자 안의 `h2`:** `.sec` 페이지 안에 `.gist` 같은 묶음이 있어도 그 안의 `h2`는 직계가 아니므로 결론 제목 검사를 받지 않는다. Task 2의 `test_nested_h2_is_not_conclusion`이 고정한다.
- **제목 안의 태그와 문자 참조:** `<h2>수익률이 <b>3.2%</b> 올랐다</h2>`나 `&lt;`가 있어도 글자 수와 어미를 바르게 세고, 원본 대조도 같은 글자로 한다. Task 2의 `test_inline_markup_in_title`과 `test_original_with_markup_is_kept`가 고정한다.
- **`#pN` 모양이 아닌 앵커:** 주소 끝이 `#top`으로 바뀌면 페이지를 바꾸지 않는다. Task 4 Step 6의 `hash_check.py`가 고정한다.
- **용어 목록의 두 마크업:** `dt`·`dd`를 바로 나열한 목록과 `div`로 묶은 목록이 모두 용어 옆에 풀이를 붙이고 위 괘선이 한 줄로 이어진다. Task 3 Step 5의 `gloss_check.py`가 고정한다.

---

### Task 1: 색 토큰

**Files:**
- Modify: `report-base.css:3-27` (토큰 정의)
- Modify: `template.html`, `template-paged.html` (관리 블록 재빌드만)
- Test: `tests/test_style.py`

**Interfaces:**
- Consumes: `eval/measure.py`의 `parse_color(s)`, `contrast(c1, c2)`, `cvd_pairs(colors: dict) -> [(a, b, de)]`(읽기만 한다).
- Produces: `tests/test_style.py`의 `token_blocks() -> list[dict[str, str]]`(밝음, prefers 어두움, data-theme 어두움 순서)와 `cr(a, b) -> float`. Task 4가 `--chg` 시험에 다시 쓴다.

L2가 `eval/measure.py` 함수로 측정해 정한 값이다. 색상 계열은 그대로 두고 Lab 명도만 바꿨다. 탐색 조건은 spec 기준에 더해 `--accent-2`도 색각 쌍에 넣었고(ECharts 다섯째 계열), 밝은 `--s4`와 `--s1`의 대비를 3:1 이상으로 두었다(애니메이션 견본이 회색 기준선 `--s4`를 짙은 `--s1`로 바꾼다). 어두운 테마의 `--s4`·`--s1` 대비는 원래 1.49라 그보다 낮아지지 않게만 두었다.

| 토큰 | 테마 | 이전 | 이후 | 측정값 |
|---|---|---|---|---|
| `--accent-2` | 밝음 | `#8FA3BC` | `#5E7189` | `--paper` 5.00, `--tint` 4.54, `--accent`와 2.30 |
| `--s2` | 밝음 | `#5E8C7E` | `#437163` | `--paper` 5.55, `--tint` 5.04 |
| `--s4` | 밝음 | `#8A8F98` | `#868B94` | `--paper` 3.42, `--tint` 3.11, `--s1`과 3.35 |
| `--ink-3` | 밝음 | `#6B7280` | `#686F7C` | `--tint` 4.59 |
| `--accent-2` | 어두움 | `#4B5E78` | `#5B6E89` | `--paper` 3.45, `--tint` 3.14, `--accent`와 2.53 |
| `--s2` | 어두움 | `#86B5A6` | `#90C0B1` | `--paper` 8.86, `--tint` 8.07 |
| `--s4` | 어두움 | `#8D949E` | `#838993` | `--paper` 5.10, `--tint` 4.64, `--s1`과 1.71 |

색각 색차 최솟값(`--s1`~`--s4`와 `--accent-2`)은 밝음 15.51, 어두움 16.40이고 둘 다 `--s4`·`--accent-2` 쌍이다. 밝은 `--s4`를 `#555A62`로 낮추는 안은 기각했다. `--s1`과 대비가 1.65로 떨어져 애니메이션 기준선 구분이 사라진다. 밝은 `--s4`를 푸른 회색 `#7A8AA2`로 옮기는 안도 기각했다. `--accent-2`와 거의 같아진다. 어두운 `--ink-3`는 `#8D949E`로 그대로 둔다.

- [ ] **Step 1: 실패하는 시험을 쓴다**

`tests/test_style.py`의 `from helpers import …` 줄 아래에 다음을 더한다.

```python
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
```

- [ ] **Step 2: 시험이 실패하는지 확인한다**

Run: `python -B -m unittest tests.test_style -v`
Expected: 다음 시험이 FAIL이다.
- `test_accent_2`: `2.58…`이 3.0보다 작다.
- `test_series_contrast`: 밝은 `--s4`·`--tint`의 `2.95…`가 3.0보다 작다.
- `test_series_cvd_with_accent_2`: 최솟값 `8.39`가 15보다 작다.
- `test_ink_3_on_tint`: `4.39…`가 4.5보다 작다.

`test_names_kept_and_dark_blocks_equal`과 `test_baseline_grey_vs_s1`(지금 3.53)은 PASS다.

- [ ] **Step 3: 토큰 값을 바꾼다**

`report-base.css`의 `:root` 블록에서 `--ink-3`를 `#686F7C`로, `--accent-2`를 `#5E7189`로, `--s2`를 `#437163`으로, `--s4`를 `#868B94`로 바꾼다. 어두운 두 블록에서 `--accent-2`를 `#5B6E89`로, `--s2`를 `#90C0B1`로, `--s4`를 `#838993`으로 바꾼다. 어두운 `--ink-3:#8D949E`는 그대로 둔다.

- [ ] **Step 4: 시험이 통과하는지 확인한다**

Run: `python -B -m unittest tests.test_style -v`
Expected: 모든 시험 PASS.

- [ ] **Step 5: 관리 블록을 다시 빌드하고 템플릿 판정을 확인한다**

Run: `python build.py template.html && python build.py template-paged.html`
Run: `W=C:/Users/ho381/AppData/Local/Temp/c2w; mkdir -p $W && python eval/gates.py template.html template-paged.html --only layout --judge-hash-nav --out $W/t1.json > /dev/null; echo $?`
Expected: `$W/t1.json`에서 두 문서·두 테마의 `contrast-text`, `contrast-graphic`, `cvd`가 모두 `pass`다. 종료 코드는 아직 `page-number`·`hash-nav` 실패로 1이다.

- [ ] **Step 6: 커밋한다**

```bash
git add report-base.css template.html template-paged.html tests/test_style.py
git commit -m "C2: 색 토큰의 대비와 색각 구분을 기준에 맞춘다" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F"
```

### Task 2: 결론 제목 검사

**Files:**
- Modify: `checks/style.py` (import, 새 파서·규칙 함수, `LABEL_TAGS`, `label_violations`, `RULES`)
- Test: `tests/test_style.py`

**Interfaces:**
- Consumes: 없음(`checks/common.py`는 바꾸지 않는다).
- Produces: `style.conclusion_titles(html) -> list[tuple[int, str]]`(`.sec` 페이지 직계 `h2`의 문서 안 시작 위치와 공백을 하나로 줄인 글자), `style.conclusion_violations(new_html, old_html=None) -> list[str]`(위반 문장은 `결론 제목이 규격에 맞지 않음(…): …`로 시작), `RULES`에 `(conclusion_violations, "old")`.

- [ ] **Step 1: 변경 전 규칙 검사 결과를 기록한다**

Run: `W=C:/Users/ho381/AppData/Local/Temp/c2w; mkdir -p $W/pre && for f in template.html template-paged.html bench/fixed/*.html; do python check.py $f > $W/pre/$(basename $f).txt; done; cat $W/pre/*.txt | grep "위반"`
Expected: 모든 문서가 `위반 0건`이다. Step 5에서 같은 결과와 비교한다.

- [ ] **Step 2: 실패하는 시험을 쓴다**

`tests/test_style.py`에 더한다(`check`는 저장소 루트의 `check.py`이고 루트는 이미 `sys.path`에 있다).

```python
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
```

- [ ] **Step 3: 시험이 실패하는지 확인한다**

Run: `python -B -m unittest tests.test_style -v`
Expected: `test_sec_gets_noun_check`는 셋째 단언에서 FAIL이다(지금 `label_violations`가 `OK_TITLE` `h2`를 명사구 위반으로 잡는다). `ConclusionTitle`의 나머지 시험은 `AttributeError: module 'checks.style' has no attribute 'conclusion_violations'`(또는 `conclusion_titles`)로 ERROR다.

- [ ] **Step 4: 규칙을 구현한다**

`checks/style.py` 맨 위의 `import re` 줄 아래에 `from html.parser import HTMLParser`를 더한다.

`HANGUL = re.compile(...)` 줄 앞에 다음을 둔다.

```python
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
TITLE_MAX = 40  # 결론 제목은 공백 포함 40자 이하
SENTENCE_END = re.compile(r"[가-힣]다\.?$")


class _Heads(HTMLParser):
    """모든 h2의 (시작 위치, 글자)와, section.page마다 직계 <p class="sec"> 유무와 직계 h2를 모은다."""

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.starts = [0] + [m.end() for m in re.finditer("\n", html)]
        self.stack, self.pages, self.h2, self.cur = [], [], [], None
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        cls = (dict(attrs).get("class") or "").split()
        top = self.stack[-1] if self.stack else None
        if tag == "h2":
            line, col = self.getpos()
            self.cur = {"start": self.starts[line - 1] + col, "text": ""}
            self.h2.append(self.cur)
        if top and top[1] is not None:  # 바로 위가 section.page면 직계 자식이다
            pg = self.pages[top[1]]
            if tag == "p" and "sec" in cls:
                pg["sec"] = True
            elif tag == "h2":
                pg["h2"].append(self.cur)
        if tag == "section" and "page" in cls:
            self.pages.append({"sec": False, "h2": []})
            self.stack.append((tag, len(self.pages) - 1))
        else:
            self.stack.append((tag, None))

    def handle_endtag(self, tag):
        if tag == "h2":
            self.cur = None
        for i in range(len(self.stack) - 1, -1, -1):  # 닫는 태그가 빠진 요소는 함께 닫는다
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self.cur is not None:
            self.cur["text"] += data


def _squash(text):
    return re.sub(r"\s+", " ", text).strip()


def conclusion_titles(html):
    """<p class="sec">가 있는 section.page의 직계 h2: [(문서 안 시작 위치, 공백을 하나로 줄인 글자)]."""
    return [(h["start"], _squash(h["text"])) for p in _Heads(html).pages if p["sec"] for h in p["h2"]]


def conclusion_violations(new_html, old_html=None):
    """결론 제목(.sec 페이지의 직계 h2)은 공백 포함 40자 이하이고 문장 어미 '다'로 끝나야 한다.
    원본을 주면 원본의 h2와 같은 글자인 제목은 위반으로 세지 않는다(기존 문서의 본문 문장은 고치지 않는다).
    원본 h2도 같은 파서로 읽어 두 글자의 정규화가 같다."""
    old = {_squash(h["text"]) for h in _Heads(old_html).h2} if old_html is not None else set()
    out = []
    for _, t in conclusion_titles(new_html):
        if t in old:
            continue
        why = []
        if len(t) > TITLE_MAX:
            why.append(f"{len(t)}자(기준 {TITLE_MAX}자)")
        if not SENTENCE_END.search(t):
            why.append("문장 어미 없음")
        if why:
            out.append(f"결론 제목이 규격에 맞지 않음({', '.join(why)}): {t[:60]}")
    return out
```

`LABEL_TAGS`, `LABEL_MAX`, `label_violations`를 다음으로 바꾼다. 바뀐 점은 `.sec` 글을 라벨로 더 보는 것과 결론 제목의 시작 위치를 건너뛰는 것이다. 판정 줄은 지금 코드와 같다.

```python
LABEL_TAGS = re.compile(r'<(title|h1|h2|h3|caption|th)\b[^>]*>(.*?)</\1>|<span class="(?:t|k)">(.*?)</span>'
                        r'|<p class="sec">(.*?)</p>', re.S)
LABEL_MAX = {"title": 24, "h1": 24}  # 나머지 라벨(절 이름 .sec 포함)은 18자


def label_violations(html):
    """제목·소제목·표 머리·도표 제목·절 이름(.sec)이 명사구인지 본다. 문장 어미, 질문형 어미,
    목적격 조사(을·를), 콜론 뒤 문장, 세 어절 이상 앞의 관형절, 길이 초과를 검출한다.
    결론 제목(.sec 페이지의 직계 h2)은 conclusion_violations가 보므로 여기서 뺀다."""
    out = []
    skip = {start for start, _ in conclusion_titles(html)}
    for m in LABEL_TAGS.finditer(html):
        if m.start() in skip:
            continue
        tag, inner, span, sec = m.groups()
        t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", inner or span or sec or "")).strip()
        letters = re.findall(r"[A-Za-z가-힣]", t)
        if not HANGUL.search(t) or "${" in t or len(HANGUL.findall(t)) * 2 < len(letters):
            continue  # 코드·자료 형태 이름이 주가 되는 라벨은 보지 않는다
        words = t.split(" ")
        why = []
        if re.search(r"(?:다|요|까|나|지|죠)[.?!]?$", t):
            why.append("문장·질문형 어미")
        if any(re.search(r"[가-힣](?:을|를)$", w) for w in words[:-1]):
            why.append("목적어가 있는 절")
        if re.search(r":\s*\S+\s+\S+\s+\S+", t):
            why.append("콜론 뒤 문장")
        adn = [len(w) > 1 and bool(re.search(r"[가-힣](?:한|된|는|던|린|운|난|날|할|든|은|른|만든)$", w))
               for w in words]
        # 논항(조사 붙은 어절)을 거느린 관형형이나, '결과·과정' 같은 넓은 말을 꾸미는 관형형은 절이다
        if any(adn[i] and re.search(r"[가-힣](?:이|가|을|를|에|에서|으로|로)$", words[i - 1])
               for i in range(1, len(words) - 1)) or (
                len(words) >= 2 and adn[-2] and words[-1] in ("결과", "과정", "것", "점", "방법", "내용")):
            why.append("명사 앞 관형절")
        limit = LABEL_MAX.get(tag, 18)
        core = re.sub(r"\s*\([^)]*\)", "", t)  # 괄호 속 기간·단위는 길이에서 뺀다
        if len(core) > limit:
            why.append(f"{len(core)}자(기준 {limit}자)")
        if why:
            out.append(f"라벨이 명사구가 아님({', '.join(why)}): {t[:60]}")
    return out
```

`RULES` 끝에 `(conclusion_violations, "old"),`를 더한다.

`h2` 시작 위치는 `HTMLParser.getpos()`(줄, 열)를 문서 안 위치로 바꾼 값이고, `LABEL_TAGS.finditer`의 `m.start()`와 같은 `<` 위치를 가리킨다. `test_sentence_title_passes_both_rules`가 이 일치를 고정한다.

- [ ] **Step 5: 시험과 규칙 검사를 확인한다**

Run: `python -B -m unittest discover -s tests`
Expected: 전체 PASS.
Run: `W=C:/Users/ho381/AppData/Local/Temp/c2w; mkdir -p $W/post && for f in template.html template-paged.html bench/fixed/*.html; do python check.py $f > $W/post/$(basename $f).txt; done; diff -r $W/pre $W/post && echo same`
Expected: `same`(고정 견본과 템플릿에는 아직 `.sec`이 없다).

- [ ] **Step 6: 커밋한다**

```bash
git add checks/style.py tests/test_style.py
git commit -m "C2: 절 이름이 있는 페이지의 결론 제목 검사를 더한다" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F"
```

### Task 3: 페이지 틀 CSS(페이지 번호·용어 목록·넓은 표)

**Files:**
- Modify: `report-base.css` (정의 목록 절, 페이지형 절, `@media (max-width:760px)` 블록, 새 `@media screen and (max-width:760px)` 블록)
- Modify: `template.html`, `template-paged.html` (관리 블록 재빌드만)

**Interfaces:**
- Consumes: Task 1의 토큰.
- Produces: 클래스 이름은 바꾸지 않는다(`.pno`, `.gloss`, `.tbl`).

CSS 변경은 단위 시험 대신 C0 하네스와 Playwright 스크립트로 확인한다. 실패하는 측정을 먼저 보고, 고친 뒤 통과를 본다.

- [ ] **Step 1: 실패하는 측정을 확인한다**

Run: `W=C:/Users/ho381/AppData/Local/Temp/c2w; python eval/rebuild.py $W/t3a && python eval/gates.py $W/t3a/*.html --only layout --out $W/t3a.json > /dev/null; echo $?`
Expected: 종료 코드 1. `$W/t3a.json`에서 모든 고정 견본의 `page-number`가 페이지마다 2로 `fail`이고, `03-groups`(최소 39.6px)와 `session-report`(최소 34.5px)의 `table-col-390`이 `fail`이다.

- [ ] **Step 2: 페이지 번호 CSS를 고친다**

`report-base.css`의 `.pno{…}` 줄 바로 아래에 더한다.

```css
@media screen{.js .pno{display:none}} /* 스크립트가 도는 화면에서는 넘김 막대의 번호만 보인다. 인쇄와 스크립트 없는 화면에서는 보인다 */
```

- [ ] **Step 3: 용어 목록 CSS를 고친다**

`/* 정의 목록 */` 주석과 그 아래 `.gloss` 네 줄을 다음으로 바꾼다. 열 간격을 두지 않고 풀이 칸의 왼쪽 안쪽 여백으로 띄워, `dt`·`dd`를 바로 나열한 목록에서도 위 괘선이 한 줄로 이어지게 한다.

```css
/* 정의 목록: 용어 열은 내용 폭과 14em 중 작은 값이고 풀이가 바로 옆에 온다. 목록 위에 '용어' 머리글을 보인다 */
.gloss{display:grid;grid-template-columns:fit-content(14em) 1fr;margin:24px 0 0}
.gloss::before{content:"용어";grid-column:1/-1;font-size:13px;font-weight:600;color:var(--ink-2);padding-bottom:6px}
.gloss>dt,.gloss>dd,.gloss>div{padding:10px 0;border-top:1px solid var(--hair)}
.gloss>div{grid-column:1/-1;display:grid;grid-template-columns:subgrid}
.gloss>div>dt,.gloss>div>dd{padding-top:0;padding-bottom:0}
.gloss dt{font-weight:600}
.gloss dd{margin:0;padding-left:24px;color:var(--ink-2);font-size:14.5px}
```

`@media (max-width:760px)` 블록 안의 `.gloss{grid-template-columns:1fr}` 줄을 다음 두 줄로 바꾼다.

```css
  .gloss,.gloss>div{grid-template-columns:1fr}
  .gloss>dd{border-top:0;padding-top:0}.gloss dd{padding-left:0}
```

- [ ] **Step 4: 넓은 표 CSS를 고친다**

`@media print{` 블록 바로 앞에 새 블록을 더한다. `screen`으로 감쌌으므로 인쇄에는 적용되지 않는다(인쇄에서 단서를 숨기는 수단이다).

```css
@media screen and (max-width:760px){
  .tbl th,.tbl td{min-width:56px}
  .tbl:has(tr>:nth-child(4))::before{content:"옆으로 밀어 볼 수 있습니다";display:block;font-size:12.5px;color:var(--ink-3);padding-bottom:4px}
}
```

- [ ] **Step 5: 고정 견본·템플릿 측정과 용어 목록 측정을 실행한다**

Run: `python build.py template.html && python build.py template-paged.html`
Run: `W=C:/Users/ho381/AppData/Local/Temp/c2w; python eval/rebuild.py $W/t3b && python eval/gates.py $W/t3b/*.html --only layout --out $W/t3b.json > /dev/null; echo $?`
Expected: 종료 코드 0. `page-number`는 모든 페이지 1, `table-col-390`의 `min_w`는 56 이상, `overflow-390` 통과, `hash-nav`는 `recorded_only: true`로 기록만 된다.

`C:/Users/ho381/AppData/Local/Temp/c2w/gloss_check.py`를 아래 내용으로 만들고 저장소 폴더에서 `python C:/Users/ho381/AppData/Local/Temp/c2w/gloss_check.py`로 실행한다.

```python
"""용어 목록 두 마크업의 배치 측정. 1280 폭: 같은 행이고 풀이가 용어 오른쪽 24px 뒤, 위 괘선이 이어짐. 390 폭: 풀이가 용어 아래."""
import re
from pathlib import Path
from playwright.sync_api import sync_playwright

css = re.search(r"/\* BEGIN report-base[^*]*\*/\n(.*?)/\* END report-base \*/",
                Path("template.html").read_text(encoding="utf-8"), re.S).group(1)
body = ('<dl class="gloss" id="flat"><dt>짧은 용어</dt><dd>풀이 문장입니다.</dd><dt>둘째 용어</dt><dd>풀이입니다.</dd></dl>'
        '<dl class="gloss" id="wrap"><div><dt>짧은 용어</dt><dd>풀이 문장입니다.</dd></div></dl>')
html = f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>{css}</style></head><body><main class="doc">{body}</main></body></html>'
JS = """id => [...document.querySelectorAll('#' + id + ' dt')].map(dt => { const dd = dt.nextElementSibling,
  a = dt.getBoundingClientRect(), b = dd.getBoundingClientRect(), s = getComputedStyle(dd);
  return {dtR: a.right, dtB: a.bottom, dtT: a.top, ddL: b.left + parseFloat(s.paddingLeft), ddBoxL: b.left, ddT: b.top}; })"""
with sync_playwright() as p:
    b = p.chromium.launch()
    for w in (1280, 390):
        pg = b.new_page(viewport={"width": w, "height": 800})
        pg.set_content(html)
        for gid in ("flat", "wrap"):
            for r in pg.evaluate(JS, gid):
                if w == 1280:
                    ok = abs(r["dtT"] - r["ddT"]) <= 2 and 0 <= r["ddL"] - r["dtR"] <= 30 and abs(r["ddBoxL"] - r["dtR"]) <= 1
                else:
                    ok = r["ddT"] >= r["dtB"] - 1
                print(w, gid, "OK" if ok else "FAIL", {k: round(v, 1) for k, v in r.items()})
        pg.close()
    b.close()
```

Expected: 모든 줄이 `OK`다. 1280 폭의 셋째 조건(`ddBoxL`이 `dtR`과 1px 안)은 두 칸 사이에 열 간격이 없어 괘선이 이어진다는 뜻이다.

- [ ] **Step 6: 커밋한다**

```bash
git add report-base.css template.html template-paged.html
git commit -m "C2: 페이지 번호 중복·용어 목록 배치·390 폭 표를 CSS로 고친다" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F"
```

### Task 4: 제목 틀·주소 앵커·C3용 화면 요소

**Files:**
- Modify: `report-base.css` (토큰 정의에 `--chg`, 페이지형 절에 `.sec`, 주석성 문단 절, 표 절, 새 확인 상태 줄)
- Modify: `template-paged.html` (문서 스크립트, 1·2페이지 마크업)
- Modify: `template.html` (관리 블록 재빌드만)
- Test: `tests/test_style.py`

**Interfaces:**
- Consumes: Task 1의 `token_blocks()`, `cr()`, `eval/measure.py`의 `delta_e76`; Task 2의 `conclusion_titles`, `conclusion_violations`.
- Produces: C3가 쓰는 클래스 `td.chg`, `span.state[data-state="run|infer|assume"]`, `div.superseded`, 페이지 머리 `p.sec`, 토큰 `--chg`.

- [ ] **Step 1: 실패하는 시험을 쓴다**

`tests/test_style.py`의 `from measure import …` 줄을 `from measure import contrast, cvd_pairs, delta_e76, parse_color  # noqa: E402`로 바꾸고, `Tokens` 클래스에 다음을 더한다.

```python
    def test_chg_background(self):
        for t in token_blocks()[:2]:
            self.assertGreaterEqual(delta_e76(parse_color(t["chg"]), parse_color(t["tint"])), 5)
            for ink in ("ink", "ink-2"):
                self.assertGreaterEqual(cr(t[ink], t["chg"]), 4.5, ink)
```

`ConclusionTitle` 뒤에 템플릿 시험을 더한다.

```python
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
```

- [ ] **Step 2: 시험이 실패하는지 확인한다**

Run: `python -B -m unittest tests.test_style -v`
Expected: `test_chg_background`가 `KeyError: 'chg'`로 ERROR이고, `PagedTemplate`의 세 시험이 FAIL이다(`test_title_frame`은 결론 제목 0개, 나머지는 문자열 없음).

- [ ] **Step 3: CSS를 더한다**

토큰에 `--chg`를 더한다. 밝은 `:root`에서는 `--tint:#F4F4F1;` 뒤에 ` --chg:#E6ECF4;`를, 어두운 두 블록에서는 `--tint:#1D2024;` 뒤에 ` --chg:#26313F;`를 넣는다. 밝음 측정값은 `--tint`와 색차 6.7, `--ink` 대비 15.54, `--ink-2` 대비 8.02다. 어두움 측정값은 10.6, 11.03, 7.35다.

`/* 주석성 문단 … */` 주석과 그 아래 `.aside` 세 줄을 다음으로 바꾼다.

```css
/* 주석성 문단과 대체됨 배너: 굵은 머리말과 위 괘선으로 구분하고 상자나 왼쪽 색 띠를 쓰지 않는다 */
.aside,.superseded{margin:16px 0;padding-top:10px;border-top:1px solid var(--hair);font-size:15px;color:var(--ink-2)}
.aside>b:first-child{color:var(--ink)}
.aside.warn>b:first-child,.superseded>b:first-child{color:var(--neg)}
```

표 절의 `tr.pick td:first-child{box-shadow:none}` 줄 아래에 더한다.

```css
td.chg{font-weight:600;background:var(--chg)} /* 전후 표의 바뀐 칸 */

/* 확인 상태: 글자는 작성자가 마크업에 쓴다(실행으로 확인함·추론함·가정함). data-state는 테두리 색만 고른다 */
.state[data-state]{display:inline-block;font-size:12.5px;line-height:1.5;color:var(--ink-2);border:1px solid var(--hair);padding:0 6px;white-space:nowrap}
.state[data-state="run"]{border-color:var(--accent)}
.state[data-state="infer"]{border-color:var(--s3)}
.state[data-state="assume"]{border-color:var(--neg)}
```

페이지형 절의 `.pno{…}` 줄 앞에 더한다.

```css
.page>.sec{font-size:13px;font-weight:600;line-height:1.5;color:var(--accent);margin:0 0 4px} /* 절 이름: 목차 링크 글과 같다. 바로 아래 h2가 결론 제목이다 */
```

- [ ] **Step 4: `template-paged.html`을 고친다**

문서 스크립트(관리 블록 뒤 `<script>`)의 마지막 줄 `  var m=/^#p(\d+)$/.exec(location.hash);show(m?parseInt(m[1],10)-1:0)});` 앞에 다음 줄을 더한다. `show()`가 부르는 `replaceState`는 `hashchange`를 일으키지 않으므로 되먹임이 없다.

```js
  addEventListener('hashchange',function(){var h=/^#p(\d+)$/.exec(location.hash);if(h)show(parseInt(h[1],10)-1)});
```

1페이지의 `</header>` 바로 뒤에 다음 줄을 넣는다.

```html
<div class="superseded"><b>대체됨</b> 원본 문서나 spec이 바뀐 문서에만 둡니다. 새 문서의 위치와 바뀐 날짜를 적습니다.</div>
```

1페이지 `.gist` 블록을 닫는 `</div>` 뒤(1페이지 `</section>` 앞)에 다음 줄을 넣는다.

```html
<dl class="gloss"><dt>절 이름</dt><dd>목차 링크와 같은 짧은 명사구입니다. 페이지 머리 맨 위에 작게 보입니다.</dd><dt>결론 제목</dt><dd>그 페이지의 결론을 수치와 함께 한 문장으로 적은 제목입니다.</dd></dl>
```

2페이지의 `<h2>절 이름</h2>`를 다음 두 줄로 바꾼다. 제목을 '결론'으로 시작하지 않는 까닭은 `checks/content.py`의 `page_scores`가 '요약·결론·부록'으로 시작하는 제목의 페이지를 핵심 페이지 후보에서 빼기 때문이다. 그러면 목차 ★ 표시와 평가가 달라 위반이 난다.

```html
<p class="sec">절 이름</p>
<h2>이 페이지의 결론을 수치와 함께 한 문장으로 적습니다</h2>
```

2페이지의 2열 표(`<div class="tbl"><table>`부터 `</table></div>`까지)를 다음 4열 전후 표로 바꾼다.

```html
<div class="tbl"><table>
  <caption>변경 전후 (바뀐 칸은 굵게)</caption>
  <thead><tr><th>항목</th><th class="n">변경 전</th><th class="n">변경 후</th><th>확인 상태</th></tr></thead>
  <tbody>
    <tr><td>항목 설명</td><td class="n">1.00</td><td class="n chg">1.20</td><td><span class="state" data-state="run">실행으로 확인함</span></td></tr>
    <tr><td>항목 설명</td><td class="n">0.80</td><td class="n">0.80</td><td><span class="state" data-state="infer">추론함</span></td></tr>
    <tr><td>항목 설명</td><td class="n">2.40</td><td class="n chg">2.10</td><td><span class="state" data-state="assume">가정함</span></td></tr>
  </tbody>
</table></div>
```

- [ ] **Step 5: 시험과 규칙 검사가 통과하는지 확인한다**

Run: `python build.py template.html && python build.py template-paged.html`
Run: `python -B -m unittest discover -s tests`
Expected: 전체 PASS.
Run: `python check.py template.html; python check.py template-paged.html`
Expected: 두 문서 모두 `위반 0건`.

- [ ] **Step 6: 템플릿을 측정하고 앵커 동작을 확인한다**

Run: `W=C:/Users/ho381/AppData/Local/Temp/c2w; python eval/gates.py template.html template-paged.html --only layout --judge-hash-nav --out $W/t4.json > /dev/null; echo $?`
Expected: 종료 코드 0. `template-paged.html`의 `hash-nav`가 `open_with_hash: true, hash_change: true`다.

`C:/Users/ho381/AppData/Local/Temp/c2w/hash_check.py`를 아래 내용으로 만들고 저장소 폴더에서 `python C:/Users/ho381/AppData/Local/Temp/c2w/hash_check.py`로 실행한다.

```python
"""template-paged.html의 앵커 동작과 390 폭 단서 확인. 로컬 서버를 빈 포트로 띄우고 끝나면 끈다."""
import functools
import http.server
import threading
from playwright.sync_api import sync_playwright

srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(http.server.SimpleHTTPRequestHandler, directory="."))
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{srv.server_address[1]}/template-paged.html"
SHOWN = "id => document.getElementById(id).getBoundingClientRect().height > 0"
CUE = "() => getComputedStyle(document.querySelector('#p2 .tbl'), '::before').content"
try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 800})
        pg.goto(url + "#p2", wait_until="networkidle")
        pg.evaluate("() => { location.hash = '#top'; }")
        pg.wait_for_timeout(500)
        print("#top 뒤 p2 보임:", pg.evaluate(SHOWN, "p2"), "p1 보임:", pg.evaluate(SHOWN, "p1"))
        pg.evaluate("() => { location.hash = '#p1'; }")
        pg.wait_for_timeout(500)
        print("#p1 뒤 p1 보임:", pg.evaluate(SHOWN, "p1"))
        print("1280 단서:", pg.evaluate(CUE))
        pg.close()
        pg = b.new_page(viewport={"width": 390, "height": 844})
        pg.goto(url + "#p2", wait_until="networkidle")
        print("390 단서:", pg.evaluate(CUE))
        pg.emulate_media(media="print")
        print("390 인쇄 단서:", pg.evaluate(CUE))
        b.close()
finally:
    srv.shutdown()
```

Expected: `#top 뒤 p2 보임: True p1 보임: False`, `#p1 뒤 p1 보임: True`, `1280 단서: none`, `390 단서: "옆으로 밀어 볼 수 있습니다"`, `390 인쇄 단서: none`.

- [ ] **Step 7: 커밋한다**

```bash
git add report-base.css template.html template-paged.html tests/test_style.py
git commit -m "C2: 절 이름·결론 제목 틀, 주소 앵커 이동, C3용 화면 요소를 템플릿에 넣는다" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F"
```

### Task 5: 보고서 규격 문서

**Files:**
- Modify: `보고서-규격.md` (「구성 요소 규칙」 표, 「검사기가 검출하는 위반」 문단)

**Interfaces:**
- Consumes: Task 1~4의 클래스·토큰 이름과 검사 규칙.
- Produces: C3의 SKILL.md가 가리킬 규격 행.

- [ ] **Step 1: 구성 요소 규칙 표를 고친다**

`| 페이지 넘김 |`으로 시작하는 행 전체를 다음 줄로 바꾼다.

```markdown
| 페이지 넘김 | 이전·다음 글자 버튼과 페이지 표시(`.pager`), 화살표 키, 주소 끝 `#pN`으로 바꾸면 그 페이지로 이동. 스크립트가 도는 화면에서는 넘김 막대에만 번호가 보이고, 인쇄하면 페이지마다 나누고 본문 첫 줄 번호(`.pno`)를 보임 | 슬라이드 전환 효과, 점 모양 페이지 표시 |
```

그 행 바로 아래에 다음 행을 더한다.

```markdown
| 절 이름 | 결론 페이지 머리 맨 위의 작은 글(`<p class="sec">`). 목차 링크 글과 같은 명사구, 18자 이하 | 큰 절 번호, 색 바탕 띠 |
| 결론 제목 | `.sec` 바로 아래 `<h2>`. 그 페이지의 결론 한 문장(공백 포함 40자 이하, 문장 어미 '다'로 끝남)이고 그 아래 요점 목록(`.pts`)이 세부를 푼다. 요약 페이지와 `page list` 페이지는 `.sec` 없이 명사구 `<h2>`만 둠 | 주제 이름만 쓴 제목, 질문형 제목 |
| 용어 목록 | `dl.gloss`. 용어 옆에 풀이를 붙이고(용어 열은 내용 폭과 14em 중 작은 값), 760px 이하에서는 용어 아래에 풀이. 목록 위 '용어' 머리글은 CSS가 보임 | 용어와 풀이를 반씩 나눈 두 칸 |
| 넓은 표 | 스크롤 상자(`.tbl`) 안에 둠. 760px 이하 화면에서 칸 최소 폭 56px, 넘치면 가로로 밂. 4열 이상 표에는 '옆으로 밀어 볼 수 있습니다' 단서를 CSS가 보이고 인쇄에서는 숨김 | 글자 단위로 잘린 열, 그림자 단서 |
| 바뀐 칸 | 전후 표의 바뀐 칸에 `td.chg`(굵은 글과 보조 바탕 `--chg`) | 색 글자만으로 표시 |
| 확인 상태 | `<span class="state" data-state="run">실행으로 확인함</span>`. 글자(실행으로 확인함·추론함·가정함)는 마크업에 쓰고, `data-state`(`run`·`infer`·`assume`)는 테두리 색만 고름 | CSS로 만든 글자, 색 알약 배지 |
| 대체됨 배너 | `<div class="superseded"><b>대체됨</b> …</div>`. 위 괘선과 굵은 머리말(`.aside.warn`과 같은 형식) | 왼쪽 색 띠 상자, 색 바탕 상자 |
```

- [ ] **Step 2: 검사기 문단을 고친다**

「검사기가 검출하는 위반」 문단에서 `라벨이 명사구인지(문장 어미·절·길이)도 검출한다.` 바로 뒤에 다음 문장을 넣는다.

```markdown
절 이름(`.sec`)이 있는 페이지의 결론 제목은 명사구 검사 대신 길이(공백 포함 40자 이하)와 문장 어미를 검출하고, 원본을 함께 주면 원본에 있던 제목은 위반으로 세지 않는다.
```

- [ ] **Step 3: 확인하고 커밋한다**

Run: `python -B -m unittest discover -s tests`
Expected: 전체 PASS(문서만 바꾸었으므로 변화 없음).
Run: `git diff 보고서-규격.md | grep '^+' | grep -E '짚|훑|맞대|띄우|세우|세운|자리|부분|영역|경우|갖고|돌리|그냥|쯤|걸|담'`
Expected: 출력이 없다. 출력이 있으면 그 낱말을 금지어 표(`C:/Users/ho381/.claude/disciplined-coder/korean-banned-words.md`)의 오른쪽 낱말로 바꾼다. 같은 표의 제외 목록에 든 낱말(예: `부담`, `담당`)은 바꾸지 않는다.

```bash
git add 보고서-규격.md
git commit -m "C2: 보고서 규격에 제목 틀과 C3용 화면 요소 행을 더한다" -m "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F"
```

### Task 6: 검증과 리포트(spec 「검증」 1~6)

**Files:** 없음(측정만 하고 출력은 `$W`에 둔다). L2가 직접 실행한다.

- [ ] **Step 1: 관리 블록을 다시 빌드한다**

Run: `python build.py template.html && python build.py template-paged.html && git status --short`
Expected: `git status --short` 출력이 없다(Task 4에서 이미 재빌드했다).

- [ ] **Step 2: 고정 견본을 기계 판정한다**

Run: `W=C:/Users/ho381/AppData/Local/Temp/c2w; python eval/rebuild.py $W/fixed && python eval/gates.py $W/fixed/*.html --only layout --out $W/fixed.json > /dev/null; echo $?`
Expected: 종료 코드 0.

- [ ] **Step 3: 템플릿을 기계 판정한다**

Run: `W=C:/Users/ho381/AppData/Local/Temp/c2w; python eval/gates.py template.html template-paged.html --only layout --judge-hash-nav --out $W/tpl.json > /dev/null; echo $?`
Expected: 종료 코드 0.

- [ ] **Step 4: 기준 커밋 규칙으로도 검사한다**

Run: `W=C:/Users/ho381/AppData/Local/Temp/c2w; mkdir -p $W/base && git archive a1552b9 checks 금지어.md | tar -x -C $W/base && python eval/gates.py template.html template-paged.html $W/fixed/*.html --only layout --base-checks $W/base/checks --out $W/base.json > /dev/null; echo $?`
Expected: `$W/base.json`의 `rules-layout` 항목에서 기준 규칙 위반이 `template-paged.html`의 결론 제목 하나(`라벨이 명사구가 아님(…): 이 페이지의 결론을 수치와 함께 한 문장으로 적습니다`)뿐이고, 다른 문서의 기준 규칙 위반은 0건이다. 이 목록을 리포트에 그대로 옮긴다.

- [ ] **Step 5: 규칙 검사를 실행한다**

Run: `python check.py template.html; python check.py template-paged.html`
Expected: 두 문서 모두 `위반 0건`.

- [ ] **Step 6: 단위 시험을 실행한다**

Run: `python -B -m unittest discover -s tests`
Expected: 전체 통과.

- [ ] **Step 7: 체크리스트 자가 점검을 한다**

Run: `W=C:/Users/ho381/AppData/Local/Temp/c2w; for f in template.html template-paged.html $W/fixed/*.html; do n=$(basename $f .html); python eval/shoot.py $f $W/shots-1/$n; done`

검토 서브에이전트 셋을 따로 실행한다. 각자에게 `$W/shots-1` 폴더 경로와 `eval/checklist.md` 내용만 준다. 검토자는 `layout` 항목(`table-cols-390`, `table-scroll-cue-390`, `single-page-number`, `glossary-layout`)에 문서마다 '예'·'아니오'·'해당 없음'과 근거로 답한다. '용어' 머리글과 스크롤 단서는 CSS 글자라 `.txt`에 없고 장면 이미지에만 있다는 점을 검토자에게 알린다. 문서·항목마다 세 결과의 다수결을 내고, 충족률 = '예' 수 ÷ ('예' + '아니오') 수를 계산한다.

Expected: 충족률 85% 이상. 못 미치면 '아니오' 근거를 읽어 CSS로 고칠 수 있는 원인을 고치고 `shots-2`, `shots-3`으로 다시 점검한다. 세 번째에도 못 미치면 그 결과를 리포트에 적고 끝낸다.

- [ ] **Step 8: 리포트를 쓴다**

리포트는 저장소에 커밋하지 않고 L2의 최종 응답 본문에 싣는다. 항목은 변경 파일과 시험 결과, 바꾼 토큰의 이전·이후 값과 대비·색차(Task 1 표), 고정 견본·템플릿의 기계 판정 결과(Step 2·3·4), 체크리스트 자가 점검 결과(Step 7), plan 리뷰에서 기능적 변화가 있었던 반영, spec·상위 설계와 다르게 정한 점, 브랜치 이름(`c2-page-frame`)이다.

## 리뷰 반영 기록

2026-10-04 plan 리뷰(`docs/superpowers/reviews/2026-10-04-c2-page-frame-plan-review.md`)로 다음 설계를 바꿨다.

- **토큰:** 밝은 `--s4`를 `#555A62`로 낮추면 애니메이션 기준선 회색과 `--s1`의 대비가 1.65로 무너지고, 어두운 `--s4`·`--accent-2` 색각 색차가 14.1이었다. `--s2`·`--s4`·`--accent-2`를 함께 다시 탐색했고, 시험에 `--accent-2` 색각 쌍과 기준선 대비를 넣었다.
- **견본 결론 제목:** '결론'으로 시작하면 `checks/content.py`가 그 페이지를 핵심 후보에서 빼므로 '이 페이지의 결론을…'으로 바꿨다.
- **원본 대조:** 원본 `h2`도 같은 HTML 파서로 읽어 정규화 경로를 하나로 했다.
- **선택자 범위:** 표 칸 최소 폭은 `.tbl` 안으로, 절 이름은 `.page>.sec`으로, 확인 상태 기본 모양은 `.state[data-state]`로 좁혔다.
- **용어 목록:** 열 간격 대신 풀이 칸 왼쪽 여백을 써 괘선이 끊기지 않게 했다.
- **인쇄 단서:** 단서 규칙을 `screen`으로 감싸 인쇄에서 숨게 했고, 쓰지 않는 `sticky`를 뺐다.
- **검증:** 기준 커밋 규칙 검사 단계와 리포트 단계를 더했다.

<!-- spec-review: passed -->
