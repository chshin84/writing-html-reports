# C3 보고서 내용 규격 구현 plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 마무리 보고서 규칙 문서(`마무리-보고서.md`)를 새로 쓰고, SKILL.md에 새 제목 체계와 C0 하네스 완료 기준을 넣는다. `checks/content.py`에는 약어 풀이(`abbr_violations`)·필수 절(`parts_violations`)·원본 기준(`basis_violations`) 검사와 `.sec` 페이지 이름 읽기를 추가한다. 마지막으로 이 규칙을 모두 갖춘 견본 `examples/wrapup.html`을 만든다.

**Architecture:** `abbr_violations`·`parts_violations`·`basis_violations`는 `checks/content.py`의 `RULES`에 원본 대조 방식 `old`로 등록한다. 각 함수는 먼저 새 규약 문서인지 판별하고, 아니면 빈 목록을 돌려준다. 수정 전 문서가 주어지면 그 문서에서 같은 검사를 판별 없이 실행해 겹치는 위반을 뺀다. 페이지 이름 읽기는 도우미 `page_name` 하나로 모아 `page_violations`와 `page_scores`가 함께 쓴다. SKILL.md에는 마무리 보고서 판별 기준과 포인터만 두고, 세부 규칙은 `마무리-보고서.md`에 둔다.

**Tech Stack:** Python 3 표준 라이브러리(`re`, `html.parser`), unittest, C0 하네스(`eval/gates.py`, `eval/shoot.py`, Python Playwright 헤드리스 Chromium).

**Spec:** `docs/superpowers/specs/2026-10-04-c3-content-rules-design.md`(상위 설계 `docs/superpowers/specs/2026-10-04-report-quality-architecture-design.md`, 측정 도구 `docs/superpowers/specs/2026-10-04-c0-eval-harness-design.md`, 페이지 틀 `docs/superpowers/specs/2026-10-04-c2-page-frame-design.md`)

## Global Constraints

- **워크트리:** `D:/projects/Structure/whr-c3`(브랜치 `c3-content-rules`)에서 절대 경로로 작업한다. `D:/projects/Structure/` 아래의 다른 폴더는 읽지 않는다.
- **소유 파일:** `SKILL.md`, `마무리-보고서.md`(새 파일), `checks/content.py`, `tests/test_content.py`, `examples/**`(새 폴더), 이 plan과 리뷰 기록이다. 그 밖의 파일은 읽기만 하고, 고쳐야 하면 멈추고 BLOCKED로 돌려준다.
- **읽지 않는 파일:** `template-paged.html`, `eval/prompts/checklist-review.md`, `eval/checklist_vote.py`. 이 세션의 권한 판정이 읽기를 거부했다. 구현자도 열지 않고, 새로 쓰는 시험과 명령도 이 파일을 읽지 않는다.
- **보류 자료:** 평가용 보류 자료는 찾지 않는다.
- **시험 명령:** 워크트리 루트에서 `python -B -m unittest discover -s tests`를 실행한다. 시작 시점 결과는 137개 통과(건너뜀 1)다.
- **화면 측정:** Python Playwright 헤드리스 Chromium(eval/ 도구)만 쓴다. Playwright MCP 도구는 쓰지 않는다. 로컬 서버는 eval/harness.py가 빈 포트로 띄우고 끈다.
- **명령 셸:** 명령 예시는 Git Bash 문법이다.
- **문서 규칙:** 문서·주석·커밋 메시지는 한국어 문어체다. 에이전트원칙 `C:/Users/ho381/.claude/disciplined-coder/agent-principles.md`와 한국어 규칙 `C:/Users/ho381/.claude/plugins/cache/chshin-tools/disciplined-coder/4edfe8ef3073/skills/lens-readability/domain-korean.md`를 읽고 따른다. SKILL.md와 마무리-보고서.md는 이 저장소 스킬 문서의 문체(절 제목 명사구, 표, 굵은 라벨 불릿)를 따른다.
- **커밋 꼬리말:** 커밋 메시지 끝에 `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`과 `Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F`를 붙인다.
- **산출 계약:** 브랜치까지만 만든다. 병합·push·main 변경은 하지 않는다.
- **C2 클래스 계약:** `p.sec`(절 이름), `td.chg`(바뀐 칸), `<span class="state" data-state="run|infer|assume">글자</span>`(확인 상태), `<div class="superseded"><b>대체됨</b> …</div>`(대체됨 배너). 화면 모양은 C2 병합 전이라 확인하지 않는다.
- **용어:** '수정 전 문서'는 check.py가 둘째 인자로 받는 HTML(`old_html`)이다. '원본 기준'은 보고서 머리의 `p.basis`가 적는 커밋·spec·원자료 경로다.

## 이 plan이 정한 해석

spec이 정하지 않았거나 이 워크트리 사정으로 다르게 정한 점이다. 리포트의 'spec·상위 설계와 다르게 정한 점'으로 옮긴다.

**견본의 출발점.** spec은 `template-paged.html`을 복사해 견본을 만들라고 한다. 그러나 이 세션의 권한 판정이 그 파일 읽기를 거부했다. 그래서 견본은 `report-base.css`의 페이지형 클래스와 `보고서-규격.md`의 구성 요소 규칙으로 직접 쓰고, 페이지 전환 스크립트도 견본에 짧게 직접 쓴다. 관리 블록은 `python build.py examples/wrapup.html`로 채운다. 템플릿 스크립트로 바꿀지는 L1이 병합 뒤 정한다.

**새 규약 문서 판별.** `class` 토큰에 `sec`이 있는 `<p>`가 있거나 `<main>`에 `data-kind="wrapup"`이 있으면 새 규약 문서다. 필수 절·원본 기준 검사는 `data-kind="wrapup"`이 있을 때만 적용한다.

**페이지형 문서의 `data-part`.** `PAGE_ID` 정규식(`checks/common.py`)은 `<section class="page…" id="pN"` 다음의 첫 `</section>`까지를 페이지 본문으로 읽는다. 그래서 페이지 안에 `section`을 중첩하면 페이지 본문이 잘리고, 속성 순서가 다르면 페이지로 인식되지 않는다. 마무리 보고서는 `data-part`를 페이지 `section`에 `class`·`id` 뒤 속성으로 둔다(`<section class="page" id="p2" data-part="changed">`). 페이지형 문서(`PAGE_ID`에 맞는 페이지가 있는 문서)에서 필수 절 검사는 `PAGE_ID` 모양의 여는 태그에 있는 `data-part`만 센다. 단일 문서에서는 모든 `<section data-part>`를 센다.

**원본 기준의 판정.** '머리'는 첫 `</section>`보다 앞이다. 페이지형 문서의 머리말(`.doc-head`)이 첫 페이지 `section` 안에 있기 때문이다. 커밋 해시는 숫자와 a~f 문자가 함께 든 7~40자 소문자 16진수다. 숫자만 된 값(날짜 등)은 해시로 보지 않는다. 파일 경로는 `/`나 `\`가 든 경로 가운데 확장자(영문자로 시작하는 1~6자)가 붙은 것이거나, 알려진 확장자(md·html·csv·json·py·txt·xlsx·pdf·yaml·yml)가 붙은 이름이다. 판정은 `p.basis`의 태그를 지운 글로 한다.

**약어 토큰.** 영문자·숫자·`_`로 시작하고 끝나며 그 사이에 `.`·`/`·`\`·`-`를 둘 수 있는 연속 글자를 토큰 하나로 읽는다. 토큰 전체가 대문자 2~6자일 때만 약어다. 그래서 숫자가 섞인 토큰(`G1`), 파일 이름(`SKILL.md`), 하이픈 식별자(`lens-API`)는 약어가 아니다. 문장 끝 마침표(`API.`)는 토큰에 붙지 않는다.

**약어 풀이의 인정 범위.** 인정하는 풀이는 세 가지다. `.gloss`(`<dl class="gloss">`)의 `dt` 글에 나온 약어, 약어가 처음 나온 곳 바로 뒤(공백 하나까지)에 `(`나 `（`가 오는 형식, 약어가 처음 나온 곳이 풀이 바로 뒤 괄호 안인 형식('상장지수펀드(ETF)')이다. 마지막 형식은 spec에 없지만 한국어 보고서에서 가장 흔한 표기라 인정한다(plan 리뷰 반영). 글 추출은 `code`·`pre`(Mermaid 포함)·`script`·`svg`·`style`·`title` 안을 건너뛴다.

**수정 전 문서 대조.** 수정 전 문서에서는 새 규약 판별 없이 같은 검사를 실행해, 그 문서에도 있는 위반(같은 약어, 같은 빠진 절, 같은 원본 기준 결함 종류)을 뺀다.

**규칙의 배치.** spec 「작업 과정의 변경」의 결정 먼저·원본 기준·대체됨 배너·질문과 용어 먼저·원격 게시는 '마무리 보고서를 새로 만들 때' 적용한다. 그래서 이 규칙은 `마무리-보고서.md`에만 두고 SKILL.md에는 포인터만 둔다. 상위 설계는 이 항목을 마무리 보고서로 한정하지 않지만, 규칙 문서 배치는 C3 spec을 따른다. 시각 검토 단계는 spec대로 SKILL.md 완료 기준에 둔다.

**완료 기준의 체크리스트 검토 횟수.** SKILL.md 완료 기준의 체크리스트 검토는 1회다. '아니오' 항목은 고치거나, 고치지 않은 이유를 보고에 적는다. spec 「검증」 5의 3회 다수결은 이 브랜치의 자가 점검에만 쓴다.

**자가 점검의 방식.** 자가 점검에서 고치는 대상은 견본(`examples/wrapup.html`)뿐이다. 규칙 문서를 고칠 이유가 나오면 리포트에 적는다. 견본 하나에 맞춘 규칙을 만들지 않기 위해서다. 검토자 지시문은 Task 7 Step 6의 고정 문안이며, 공식 프롬프트(`eval/prompts/checklist-review.md`)와 다르다는 점을 리포트에 적는다.

**템플릿 오탐 확인.** spec 「검증」 3은 두 템플릿에 새 규칙을 실행하라고 한다. `template-paged.html`은 읽지 않는 파일이라 `template.html`만 확인하고, `template-paged.html`은 L1의 확인 항목으로 리포트에 넘긴다. C2가 병합되면 `template-paged.html`은 `p.sec`가 들어가 새 규약 문서가 되므로, 그 뒤에는 약어 검사가 템플릿과 템플릿을 복사한 모든 페이지형 보고서에 적용된다. 이 점도 리포트에 적는다.

## Review Focus

- **속성 순서가 틀린 페이지 `section`:** `<section data-part="changed" class="page" id="p2">`는 `PAGE_ID`가 페이지로 보지 않는다. 페이지형 문서에서는 이 `data-part`를 세지 않아 '필수 절 없음'이 나와야 한다(Task 3 시험 `test_parts_need_page_shape`).
- **'풀이(약어)' 표기:** '상장지수펀드(ETF)'는 풀이된 약어다(Task 2 시험 `test_paren_around_ok`).
- **문장 끝 마침표와 한글 조사가 붙은 약어:** 'API.'·'API를'도 약어로 읽는다(Task 2 시험 `test_abbr_with_period_and_particle`).
- **태그로 나뉜 약어와 괄호 풀이:** `<b>API</b>(응용 프로그램 인터페이스)`는 추출 글에 공백이 생겨도 풀이로 인정한다(Task 2 시험 `test_paren_after_tag`).
- **결론 제목이 '요약'으로 시작하는 `.sec` 페이지:** 페이지 이름은 `.sec`에서 읽으므로 후보에서 빠지지 않는다(Task 1 시험 `test_sec_name_overrides_h2`).

## 파일 구조

| 파일 | 책임 | Task |
|---|---|---|
| `checks/content.py` | 페이지 이름 도우미, 새 규약 판별, 약어 풀이·필수 절·원본 기준 규칙과 `RULES` 등록 | 1, 2, 3 |
| `tests/test_content.py` | 위 규칙의 단위 시험과 고정 견본·`template.html` 오탐 시험 | 1, 2, 3 |
| `마무리-보고서.md` | 마무리 보고서 전용 규칙 | 4 |
| `SKILL.md` | 마무리 보고서 판별과 포인터, 제목 체계, 확인 상태, 반복 금지, C0 하네스 완료 기준 | 5 |
| `examples/wrapup.html` | 페이지형 마무리 보고서 견본(가상 작업) | 6 |

---

### Task 1: `.sec` 페이지 이름 읽기

**Files:**
- Modify: `checks/content.py`(`page_violations`, `page_scores`)
- Test: `tests/test_content.py`

**Interfaces:**
- Produces: `content.SEC`(정규식, 그룹 1이 `p.sec`의 안쪽 HTML), `content.strip_tags(s) -> str`(태그를 지우고 공백을 하나로 줄인 글), `content.page_name(body: str) -> str`(`.sec` 글, 없으면 첫 `h1`·`h2` 글, 둘 다 없으면 빈 문자열)

- [ ] **Step 1: 실패하는 시험을 쓴다**

같은 파일의 import 줄을 `from helpers import ROOT, page, paged, toc  # noqa: E402`로 바꾼다. `Stars` 클래스 뒤에 추가한다.

```python
class PageName(unittest.TestCase):
    def test_sec_read_first(self):
        body = '<p class="sec">구조 A</p><h2>요약 기준이 A보다 12% 낮다</h2>'
        self.assertEqual(content.page_name(body), "구조 A")

    def test_h2_without_sec(self):
        self.assertEqual(content.page_name("<h2>구조 <b>A</b></h2>"), "구조 A")

    def test_sec_name_overrides_h2(self):
        html = paged('<li data-src="p2">가</li>', {}).replace(
            "<h2>구조 A</h2>", '<p class="sec">구조 A</p><h2>요약하면 A가 12% 빠르다</h2>')
        rows = {x["id"]: x for x in content.page_scores(html)}
        self.assertEqual((rows["p2"]["title"], rows["p2"]["excluded"], rows["p2"]["expect"]), ("구조 A", False, "core"))

    def test_h2_summary_still_excluded_without_sec(self):
        html = paged('<li data-src="p2">가</li>', {}).replace("<h2>구조 A</h2>", "<h2>요약 A</h2>")
        rows = {x["id"]: x for x in content.page_scores(html)}
        self.assertTrue(rows["p2"]["excluded"])

    def test_violation_names_sec(self):
        html = page(body='<section class="page" id="p1"><p class="sec">구조 A</p><h2>A가 빠르다</h2><p>글</p></section>')
        self.assertEqual(content.page_violations(html), ["근거 없는 페이지(표·도표·핵심 수치 없음): 구조 A"])
```

- [ ] **Step 2: 시험이 실패하는지 확인한다**

Run: `python -B -m unittest tests.test_content -v`
Expected: `test_sec_read_first`·`test_h2_without_sec`는 `AttributeError: module 'checks.content' has no attribute 'page_name'`, `test_sec_name_overrides_h2`·`test_violation_names_sec`는 `AssertionError`로 실패한다. `test_h2_summary_still_excluded_without_sec`는 기존 동작을 고정하는 시험이라 이 단계에서도 통과한다.

- [ ] **Step 3: 최소 구현을 쓴다**

`checks/content.py`의 `EVIDENCE` 정의 뒤에 추가한다.

```python
SEC = re.compile(r'<p\b[^>]*\bclass="(?:[^"]*\s)?sec(?:\s[^"]*)?"[^>]*>(.*?)</p>', re.S)  # 절 이름(C2 계약)
HEAD = re.compile(r"<h[12][^>]*>(.*?)</h[12]>", re.S)


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


def page_name(body):
    """페이지 이름: 절 이름(p.sec)이 있으면 그 글, 없으면 첫 h1·h2의 글이다."""
    m = SEC.search(body) or HEAD.search(body)
    return strip_tags(m.group(1)) if m else ""
```

`page_violations`에서 `h = re.search(...)`, `name = ...`, `out.append(...)` 세 줄을 아래 두 줄로 바꾼다.

```python
        name = page_name(body) or body[:40]
        out.append(f"근거 없는 페이지(표·도표·핵심 수치 없음): {name[:40]}")
```

`page_scores`의 `h = …`와 `title = …` 두 줄을 `title = page_name(body)` 한 줄로 바꾼다. `page_scores` 독스트링 첫 줄은 "핵심 페이지 평가. 요약·결론·부록 페이지는 후보에서 뺀다. 페이지 이름은 p.sec, 없으면 첫 h1·h2에서 읽는다."로 바꾼다.

- [ ] **Step 4: 시험이 통과하는지 확인한다**

Run: `python -B -m unittest tests.test_content -v`
Expected: 모든 시험 통과.

- [ ] **Step 5: 커밋한다**

```bash
git add checks/content.py tests/test_content.py
git commit -m "C3: 페이지 이름을 절 이름(.sec)에서 먼저 읽는다

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F"
```

### Task 2: 약어 풀이 규칙

**Files:**
- Modify: `checks/content.py`
- Test: `tests/test_content.py`

**Interfaces:**
- Consumes: `content.SEC`, `content.strip_tags`(Task 1)
- Produces: `content.WRAPUP`(정규식), `content.is_new_doc(html) -> bool`, `content.unglossed(html) -> list[str]`(판별 없이 풀이 없는 약어를 처음 나온 순서로 한 번씩), `content.abbr_violations(html, old_html=None) -> list[str]`. 위반 문장 형식은 `"약어 풀이 없음: {약어}(.gloss 용어나 처음 나온 곳의 괄호 풀이를 둔다)"`이다. `RULES`에 `(abbr_violations, "old")`를 추가한다. 시험 도우미 `new_doc(body)`와 상수 `SEC`·`MSG`를 `tests/test_content.py`에 둔다.

- [ ] **Step 1: 실패하는 시험을 쓴다**

`tests/test_content.py`에 추가한다.

```python
SEC = '<p class="sec">절</p>'
MSG = "(.gloss 용어나 처음 나온 곳의 괄호 풀이를 둔다)"


def new_doc(body):
    """새 규약 문서(.sec 사용)."""
    return page(body=SEC + body)


class Abbr(unittest.TestCase):
    def test_glossed_ok(self):
        html = new_doc('<p>API를 쓴다.</p><dl class="gloss"><div><dt>API</dt><dd>응용 프로그램 인터페이스</dd></div></dl>')
        self.assertEqual(content.abbr_violations(html), [])

    def test_paren_ok(self):
        self.assertEqual(content.abbr_violations(new_doc("<p>API(응용 프로그램 인터페이스)를 쓴다. API는 빠르다.</p>")), [])

    def test_paren_around_ok(self):
        self.assertEqual(content.abbr_violations(new_doc("<p>상장지수펀드(ETF)와 상장지수증권 (ETN)을 산다.</p>")), [])

    def test_bare_paren_is_not_gloss(self):
        self.assertEqual(content.abbr_violations(new_doc("<p>(ETF)를 산다.</p>")), ["약어 풀이 없음: ETF" + MSG])

    def test_unglossed(self):
        self.assertEqual(content.abbr_violations(new_doc("<p>API를 쓴다. 그 뒤 API(설명)를 본다.</p>")),
                         ["약어 풀이 없음: API" + MSG])

    def test_reported_once_in_order(self):
        self.assertEqual(content.unglossed(new_doc("<p>SDK와 API와 SDK를 쓴다.</p>")), ["SDK", "API"])

    def test_abbr_with_period_and_particle(self):
        self.assertEqual(content.unglossed(new_doc("<p>끝은 API.</p><p>ETF를 산다.</p>")), ["API", "ETF"])

    def test_paren_after_tag(self):
        self.assertEqual(content.abbr_violations(new_doc("<p><b>API</b>(응용 프로그램 인터페이스)</p>")), [])

    def test_old_has_same(self):
        old = new_doc("<p>API를 쓴다.</p>")
        new = new_doc("<p>API를 쓴다. ETF도 쓴다.</p>")
        self.assertEqual(content.abbr_violations(new, old), ["약어 풀이 없음: ETF" + MSG])

    def test_old_not_new_convention_still_subtracts(self):
        self.assertEqual(content.abbr_violations(new_doc("<p>API</p>"), page(body="<p>API</p>")), [])

    def test_not_new_convention(self):
        self.assertEqual(content.abbr_violations(page(body="<p>API를 쓴다.</p>")), [])

    def test_wrapup_mark_is_new_convention(self):
        html = page(body="<p>API</p>").replace('<main class="doc">', '<main class="doc" data-kind="wrapup">')
        self.assertEqual(content.abbr_violations(html), ["약어 풀이 없음: API" + MSG])


class AbbrExcluded(unittest.TestCase):
    def ok(self, body):
        self.assertEqual(content.abbr_violations(new_doc(body)), [], body)

    def test_code(self):
        self.ok("<p><code>API</code></p>")

    def test_pre(self):
        self.ok("<pre>API CLI</pre>")

    def test_mermaid(self):
        self.ok('<pre class="mermaid">flowchart LR\n A --> B</pre>')

    def test_script(self):
        self.ok("<script>var s = 'API';</script>")

    def test_svg(self):
        self.ok("<svg><text>API</text></svg>")

    def test_digit_tokens(self):
        self.ok("<p>G1과 Q4와 HTML5</p>")

    def test_file_name_piece(self):
        self.ok("<p>SKILL.md와 README.txt를 읽는다.</p>")

    def test_hyphen_identifier_piece(self):
        self.ok("<p>lens-API와 PR-12와 X-API-KEY</p>")

    def test_length_bounds(self):
        self.ok("<p>A와 ABCDEFG</p>")
```

- [ ] **Step 2: 시험이 실패하는지 확인한다**

Run: `python -B -m unittest tests.test_content -v`
Expected: `Abbr`·`AbbrExcluded` 시험이 `AttributeError: module 'checks.content' has no attribute 'abbr_violations'`(또는 `'unglossed'`)로 실패한다.

- [ ] **Step 3: 최소 구현을 쓴다**

`checks/content.py` 맨 위 import를 `from checks.common import PAGE_ID, TOC, TextOnly, visible_text`로 바꾸고, `RULES` 앞에 넣는다.

```python
WRAPUP = re.compile(r'<main\b[^>]*\bdata-kind="wrapup"')  # 마무리 보고서 표시
TOKEN = re.compile(r"[A-Za-z0-9_](?:[A-Za-z0-9_./\\-]*[A-Za-z0-9_])?")
ABBR = re.compile(r"[A-Z]{2,6}")
GLOSS = re.compile(r'<dl\b[^>]*\bclass="(?:[^"]*\s)?gloss(?:\s[^"]*)?"[^>]*>(.*?)</dl>', re.S)
PAREN_AFTER = re.compile(r"\s?[(（]")  # 약어(풀이)
PAREN_BEFORE = re.compile(r"[^\s()（）]\s?[(（]\s?$")  # 풀이(약어)의 여는 괄호까지
PAREN_CLOSE = re.compile(r"\s?[)）]")


def is_new_doc(html):
    """새 규약 문서: 절 이름(p.sec)을 쓰거나 마무리 보고서 표시가 있다. 새 검사는 이 문서에만 적용한다."""
    return bool(SEC.search(html) or WRAPUP.search(html))


class ProseText(TextOnly):
    """code·pre·script·svg·style·title 밖의 글. 약어 검사용이다."""
    SKIP = ("code", "pre", "script", "svg", "style", "title")

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1


def abbrs(text):
    """(약어, 시작, 끝) 목록. 숫자·점·하이픈이 섞인 토큰 전체는 약어가 아니다."""
    return [(m.group(), m.start(), m.end()) for m in TOKEN.finditer(text) if ABBR.fullmatch(m.group())]


def unglossed(html):
    """풀이 없는 약어를 처음 나온 순서로 한 번씩 돌려준다. 새 규약 판별은 하지 않는다."""
    text = visible_text(html, ProseText)
    glossed = {a for block in GLOSS.findall(html) for dt in re.findall(r"<dt\b[^>]*>(.*?)</dt>", block, re.S)
               for a, _, _ in abbrs(strip_tags(dt))}
    seen, out = set(), []
    for a, start, end in abbrs(text):
        if a in seen:
            continue
        seen.add(a)
        around = PAREN_BEFORE.search(text[max(0, start - 4):start]) and PAREN_CLOSE.match(text, end)
        if a not in glossed and not PAREN_AFTER.match(text, end) and not around:
            out.append(a)
    return out


def abbr_violations(html, old_html=None):
    """새 규약 문서에서 풀이 없는 영문 약어(대문자 2~6자)를 검출한다. 수정 전 문서에도 풀이 없던 약어는 뺀다."""
    if not is_new_doc(html):
        return []
    old = set(unglossed(old_html)) if old_html is not None else set()
    return [f"약어 풀이 없음: {a}(.gloss 용어나 처음 나온 곳의 괄호 풀이를 둔다)" for a in unglossed(html) if a not in old]
```

`RULES`에 `(abbr_violations, "old"),`를 추가한다. 파일 독스트링은 "페이지 근거·핵심 페이지(별) 표시·점수표·새 규약 문서(약어 풀이·마무리 보고서) 규칙. C3(보고서 내용 규격) 소유."로 바꾼다.

- [ ] **Step 4: 시험이 통과하는지 확인한다**

Run: `python -B -m unittest tests.test_content -v`
Expected: 모든 시험 통과.

- [ ] **Step 5: 커밋한다**

```bash
git add checks/content.py tests/test_content.py
git commit -m "C3: 새 규약 문서의 약어 풀이 검사를 추가한다

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F"
```

### Task 3: 필수 절·원본 기준 규칙과 오탐 시험

**Files:**
- Modify: `checks/content.py`
- Test: `tests/test_content.py`

**Interfaces:**
- Consumes: `content.WRAPUP`, `content.strip_tags`, 시험 도우미 `new_doc`(Task 1·2)
- Produces: `content.PARTS`(사전, `data-part` 값 → 절 이름, 순서는 changed·achieved·remaining·decisions·verification), `content.parts_violations(html, old_html=None) -> list[str]`(위반 형식 `"마무리 보고서 필수 절 없음: {값}({절 이름})"`), `content.basis_violations(html, old_html=None) -> list[str]`(위반 형식 `"원본 기준 없음: 문서 머리(첫 section 끝 앞)에 p.basis가 없다"` 또는 `"원본 기준에 커밋 해시·.md 경로·파일 경로가 없다: {글 앞 40자}"`). `RULES`에 둘 다 `old`로 추가한다.

- [ ] **Step 1: 실패하는 시험을 쓴다**

`tests/test_content.py`에 추가한다.

```python
PART_IDS = ("changed", "achieved", "remaining", "decisions", "verification")
PARTS_ALL = "".join(f'<section data-part="{p}"><h2>절</h2></section>' for p in PART_IDS)


def wrapup(body, head='<p class="basis">기준: 커밋 b2cfc00</p>'):
    return page(body=head + body).replace('<main class="doc">', '<main class="doc" data-kind="wrapup">')


class Parts(unittest.TestCase):
    def test_all_present(self):
        self.assertEqual(content.parts_violations(wrapup(PARTS_ALL)), [])

    def test_missing(self):
        body = PARTS_ALL.replace('data-part="decisions"', 'data-part="x"')
        self.assertEqual(content.parts_violations(wrapup(body)), ["마무리 보고서 필수 절 없음: decisions(결정 요청)"])

    def test_old_missing_same(self):
        body = PARTS_ALL.replace('data-part="decisions"', 'data-part="x"')
        self.assertEqual(content.parts_violations(wrapup(body), wrapup(body)), [])

    def test_new_convention_not_wrapup(self):
        self.assertEqual(content.parts_violations(new_doc("<p>글</p>")), [])

    def test_not_new_convention(self):
        self.assertEqual(content.parts_violations(page(body=PARTS_ALL.replace('data-part="decisions"', ""))), [])

    def test_parts_on_page_sections(self):
        pages = "".join(f'<section class="page" id="p{i}" data-part="{p}"><h2>절</h2><table></table></section>'
                        for i, p in enumerate(PART_IDS, 1))
        self.assertEqual(content.parts_violations(wrapup(pages)), [])

    def test_parts_need_page_shape(self):
        pages = "".join(f'<section class="page" id="p{i}" data-part="{p}"><h2>절</h2><table></table></section>'
                        for i, p in enumerate(PART_IDS[:4], 1))
        pages += '<section data-part="verification" class="page" id="p5"><h2>절</h2></section>'
        self.assertEqual(content.parts_violations(wrapup(pages)), ["마무리 보고서 필수 절 없음: verification(검증 범위)"])


class Basis(unittest.TestCase):
    def fails(self, head):
        return content.basis_violations(wrapup(PARTS_ALL, head))

    def test_hash_ok(self):
        self.assertEqual(self.fails('<p class="basis">기준: 커밋 b2cfc00</p>'), [])

    def test_md_path_ok(self):
        self.assertEqual(self.fails('<p class="basis">기준: <code>docs/specs/a-design.md</code></p>'), [])

    def test_file_path_ok(self):
        self.assertEqual(self.fails('<p class="basis">원자료 data/raw.csv</p>'), [])

    def test_known_extension_name_ok(self):
        self.assertEqual(self.fails('<p class="basis">원자료 성과표.xlsx</p>'), [])

    def test_basis_hash_before_hangul(self):
        self.assertEqual(self.fails('<p class="basis">b2cfc00커밋 기준</p>'), [])

    def test_missing(self):
        self.assertEqual(self.fails(""), ["원본 기준 없음: 문서 머리(첫 section 끝 앞)에 p.basis가 없다"])

    def test_after_first_section(self):
        html = wrapup(PARTS_ALL + '<p class="basis">b2cfc00</p>', "")
        self.assertEqual(content.basis_violations(html), ["원본 기준 없음: 문서 머리(첫 section 끝 앞)에 p.basis가 없다"])

    def test_inside_first_page_ok(self):
        body = '<section class="page" id="p1"><div class="doc-head"><p class="basis">커밋 b2cfc00</p></div></section>'
        self.assertEqual(content.basis_violations(wrapup(body, "")), [])

    def test_no_reference(self):
        self.assertEqual(self.fails('<p class="basis">기준: 어제 회의 3.5절</p>'),
                         ["원본 기준에 커밋 해시·.md 경로·파일 경로가 없다: 기준: 어제 회의 3.5절"])

    def test_digits_and_abbrev_rejected(self):
        self.assertEqual(len(self.fails('<p class="basis">기준: 20261004 회의(e.g. 주간 점검), U.S 자료</p>')), 1)

    def test_short_hex_rejected(self):
        self.assertEqual(len(self.fails('<p class="basis">abc12</p>')), 1)

    def test_old_same(self):
        html = wrapup(PARTS_ALL, "")
        self.assertEqual(content.basis_violations(html, html), [])

    def test_new_convention_not_wrapup(self):
        self.assertEqual(content.basis_violations(new_doc("<p>글</p>")), [])

    def test_not_new_convention(self):
        self.assertEqual(content.basis_violations(page(body="<p>글</p>")), [])


class FixedNoFalsePositive(unittest.TestCase):
    """새 규칙은 고정 견본과 template.html(새 규약 문서가 아님)에 위반을 내지 않는다."""

    def test_zero(self):
        files = sorted((ROOT / "bench" / "fixed").glob("*.html")) + [ROOT / "template.html"]
        for f in files:
            html = f.read_text(encoding="utf-8")
            for fn in (content.abbr_violations, content.parts_violations, content.basis_violations):
                self.assertEqual(fn(html), [], f"{f.name} {fn.__name__}")
```

- [ ] **Step 2: 시험이 실패하는지 확인한다**

Run: `python -B -m unittest tests.test_content -v`
Expected: `Parts`·`FixedNoFalsePositive`는 `AttributeError: … 'parts_violations'`, `Basis`는 `AttributeError: … 'basis_violations'`로 실패한다.

- [ ] **Step 3: 최소 구현을 쓴다**

`checks/content.py`의 `abbr_violations` 뒤에 추가한다.

```python
PARTS = {"changed": "바뀐 것", "achieved": "처음 요청 대비 달성", "remaining": "남은 일",
         "decisions": "결정 요청", "verification": "검증 범위"}
PAGE_OPEN = re.compile(r'<section class="page[^"]*" id="p\d+"([^>]*)>')  # PAGE_ID와 같은 모양의 여는 태그
PART = re.compile(r'\bdata-part="([^"]+)"')
BASIS = re.compile(r'<p\b[^>]*\bclass="(?:[^"]*\s)?basis(?:\s[^"]*)?"[^>]*>(.*?)</p>', re.S)
REF = re.compile(
    r"(?<![0-9A-Za-z])(?=[0-9a-f]*[0-9])(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}(?![0-9A-Za-z])"  # 커밋 해시
    r"|[\w.-]*[/\\][\w./\\-]*\w\.[A-Za-z]\w{0,5}(?![0-9A-Za-z])"  # 확장자가 붙은 경로
    r"|[\w-]+\.(?:md|html|csv|json|py|txt|xlsx|pdf|yaml|yml)(?![0-9A-Za-z])")  # 알려진 확장자가 붙은 이름


def _missing_parts(html):
    """페이지형 문서는 PAGE_ID 모양의 페이지 section에 있는 data-part만 센다(그 밖의 페이지는 장면·점수에서 빠진다)."""
    opens = PAGE_OPEN.findall(html)
    attrs = opens if opens else re.findall(r"<section\b([^>]*)>", html)
    found = {m for a in attrs for m in PART.findall(a)}
    return [p for p in PARTS if p not in found]


def parts_violations(html, old_html=None):
    """마무리 보고서(data-kind="wrapup")에 다섯 필수 절(data-part)이 모두 있는지 본다. 수정 전 문서에도 없던 절은 뺀다."""
    if not WRAPUP.search(html):
        return []
    old = set(_missing_parts(old_html)) if old_html is not None else set()
    return [f"마무리 보고서 필수 절 없음: {p}({PARTS[p]})" for p in _missing_parts(html) if p not in old]


def _basis_problems(html):
    m = BASIS.search(html)
    end = html.find("</section>")
    if not m or (end != -1 and m.start() > end):
        return ["원본 기준 없음: 문서 머리(첫 section 끝 앞)에 p.basis가 없다"]
    text = strip_tags(m.group(1))
    if not REF.search(text):
        return [f"원본 기준에 커밋 해시·.md 경로·파일 경로가 없다: {text[:40]}"]
    return []


def basis_violations(html, old_html=None):
    """마무리 보고서 머리의 원본 기준(p.basis)에 커밋 해시·.md 경로·파일 경로가 있는지 본다. 수정 전 문서에도 있던 결함은 뺀다."""
    if not WRAPUP.search(html):
        return []
    old = {f.split(":")[0] for f in _basis_problems(old_html)} if old_html is not None else set()
    return [f for f in _basis_problems(html) if f.split(":")[0] not in old]
```

`RULES`에 `(parts_violations, "old"),`와 `(basis_violations, "old"),`를 추가한다.

- [ ] **Step 4: 시험이 통과하는지 확인한다**

Run: `python -B -m unittest tests.test_content -v`
Expected: 모든 시험 통과.

Run: `python -B -m unittest discover -s tests`
Expected: `OK (skipped=1)`, 실패 0. 시험 수는 137보다 많다.

- [ ] **Step 5: 커밋한다**

```bash
git add checks/content.py tests/test_content.py
git commit -m "C3: 마무리 보고서의 필수 절·원본 기준 검사를 추가한다

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F"
```

### Task 4: `마무리-보고서.md`

**Files:**
- Create: `마무리-보고서.md`

**Interfaces:**
- Consumes: Task 2·3의 규칙 이름과 위반 문장, C2 클래스 계약
- Produces: SKILL.md(Task 5)와 견본(Task 6)이 가리키는 `마무리-보고서.md`. 절 제목은 아래 목록과 글자까지 같게 둔다.

- [ ] **Step 1: 파일을 쓴다**

파일 첫 줄은 `# 마무리 보고서 규칙`이다. 그 아래 머리말 문단에는 세 가지를 쓴다. 이 파일은 마무리 보고서(작업을 끝내고 결과·남은 일·결정 사항을 알리는 보고서)를 새로 만들 때만 쓴다. SKILL.md의 규칙과 함께 적용한다. 견본은 `$S/examples/wrapup.html`이다. 절 제목과 각 절의 내용은 다음과 같다. spec 문장을 근거로 쓰되 설계 이유는 한 문장으로 줄인다.

- **`## 적용 범위`:** 새로 만들 때만 적용한다. 기존 HTML을 고치는 작업에서는 적용하지 않고, 해당 결함을 보고로만 알린다(본문 문장과 숫자를 바꾸지 않는 수정 규칙 때문). 문서는 `<main class="doc" data-kind="wrapup">`로 표시한다. 이 표시가 있으면 check.py가 필수 절·원본 기준·약어 풀이를 검사한다.
- **`## 필수 절`:** spec 「마무리 보고서의 필수 절」 표(절 이름, `data-part`, 내용 열)를 옮긴다. 해당 사항이 없는 절은 '해당 없음' 한 줄로 끝낸다. 표시 위치는 다음과 같다. 페이지형 문서는 페이지 `section`에 `class`·`id` 다음 속성으로 둔다(`<section class="page" id="p2" data-part="changed">`). 단일 문서는 `<section data-part="…">`를 쓴다. 페이지 안에 `section`을 중첩하지 않고 속성 순서를 바꾸지 않는다(check.py가 그 페이지를 인식하지 못한다).
- **`## 절마다 쓰는 형식`:** 굵은 라벨 불릿으로 절마다 형식을 적는다. **바뀐 것:** 변경 전·변경 후 열이 있는 표를 쓰고 바뀐 칸은 `<td class="chg">`로 둔다. **처음 요청 대비 달성:** 처음 요청 항목마다 행을 두고 열은 요청 항목·결과(달성·일부 달성·미달성)·근거다. **남은 일:** 항목마다 처분(지금 함·미룸·하지 않음), 권장안, 예정 시점을 쓴다. **결정 요청:** 결정 메모와 결정 기록(ADR, 결정과 그 맥락·기각한 대안을 남기는 문서 형식) 관행을 따른다. 정할 사항마다 선택지, 권장안과 그 이유, 기각한 대안과 그 이유를 쓴다. 이미 정한 사항은 '결정한 사항'으로 기각한 대안과 함께 같은 절에 둔다. **검증 범위:** 실행으로 확인한 사항(명령과 출력)과 확인하지 않은 사항을 나눠 적는다.
- **`## 결정 먼저`:** SKILL.md 2단계(파일 내용 정리)의 요약 결론 확인에서 미결정 사항이 나오면 보고서를 쓰기 전에 하나씩 결정받는다. 결정 결과는 결정 요청 절의 '결정한 사항'으로 옮긴다. 사용자에게 물을 수 없는 실행자(서브에이전트)는 미결정 사항을 결정 요청 절에 그대로 둔다.
- **`## 질문과 용어 먼저`:** 파일 첫머리(`.lede` 첫 문장)에 그 파일이 답하는 독자의 질문을 보인다. 핵심 용어는 처음 쓰기 전(애니메이션은 재생 전)에 `.gloss`나 괄호로 풀이한다. 약어 풀이로 인정하는 형식은 `.gloss`의 `dt`, '약어(풀이)', '풀이(약어)'다.
- **`## 원본 기준과 대체됨 배너`:** 머리말에 `<p class="basis">`로 기준(커밋, spec 경로, 원자료 파일 경로 중 하나 이상)을 적는다. check.py는 첫 `</section>` 앞의 `p.basis`에 커밋 해시(숫자와 a~f 문자가 함께 든 7~40자 소문자 16진수)나 파일 경로(`/`·`\`가 든 경로나 md·html·csv·json·py·txt·xlsx·pdf·yaml·yml 이름)가 있는지 검사한다. 새 보고서가 옛 보고서를 대체하면 새 보고서를 만드는 세션이 옛 보고서 머리에 `<div class="superseded"><b>대체됨</b> 새 문서 경로와 바뀐 이유</div>`를 단다.
- **`## 확인 상태와 원자료`:** 마무리 보고서는 내부 검토 문서이므로 결론 줄마다 `<span class="state" data-state="run|infer|assume">`과 글자를 둔다. 상태 표의 행은 `run`(실행으로 확인함: 같은 줄에 명령·출력·커밋·파일 줄이 있을 때만), `infer`(추론함), `assume`(가정함)이다. 외부 독자 문서에는 쓰지 않는다(SKILL.md 「독자 구분」).
- **`## 원격 게시`:** 원격에서 열 수 있게 게시하기 전에 민감 정보(사내 이름, 경로, 수치의 공개 여부)를 점검한다. 점검 결과를 보이며 사용자 확인을 받고, 확인을 받은 뒤 게시한다. 게시할 때마다 확인한다.
- **`## 완료 전 확인`:** SKILL.md 완료 기준과 함께 적용한다. check.py가 검출하는 위반 문장('마무리 보고서 필수 절 없음', '원본 기준 없음', '원본 기준에 커밋 해시·.md 경로·파일 경로가 없다', '약어 풀이 없음')을 표로 적는다. check.py가 보지 못하는 사항(권장안 이유의 타당성, 확인 상태와 원자료의 일치)은 직접 확인한다고 적는다.

- [ ] **Step 2: 절 제목을 확인한다**

Run: `grep -n "^#" 마무리-보고서.md`
Expected: 정확히 다음 줄이 이 순서로 나온다. `# 마무리 보고서 규칙`, `## 적용 범위`, `## 필수 절`, `## 절마다 쓰는 형식`, `## 결정 먼저`, `## 질문과 용어 먼저`, `## 원본 기준과 대체됨 배너`, `## 확인 상태와 원자료`, `## 원격 게시`, `## 완료 전 확인`. `###`는 없다.

Run: `for s in 'data-part="changed"' 'class="chg"' 'data-state="run' 'class="superseded"' 'class="basis"' 'data-kind="wrapup"'; do printf '%s ' "$s"; grep -c -F "$s" 마무리-보고서.md; done`
Expected: 모든 줄의 수가 1 이상.

- [ ] **Step 3: 금지어를 확인한다**

Run: ``python -B -c "import re,sys; sys.path.insert(0,'.'); from checks import common; t=open('마무리-보고서.md',encoding='utf-8').read(); t=re.sub(r'\`[^\`]*\`','',t); print(dict(common.banned_hits(t, common.banned_rules())))"``
Expected: `{}`. 백틱 안(코드)은 지우고 검사한다. 출현이 있으면 그 낱말을 금지어 표의 대신 쓰는 말로 고친다.

- [ ] **Step 4: 커밋한다**

```bash
git add 마무리-보고서.md
git commit -m "C3: 마무리 보고서 전용 규칙 문서를 추가한다

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F"
```

### Task 5: SKILL.md 개정

**Files:**
- Modify: `SKILL.md`

**Interfaces:**
- Consumes: `마무리-보고서.md`의 절 제목(Task 4), `examples/wrapup.html` 경로(Task 6에서 만든다)
- Produces: 새 제목 체계와 C0 하네스 완료 기준

- [ ] **Step 1: 개정 전 금지어 수를 기록한다**

Run: ``python -B -c "import re,sys; sys.path.insert(0,'.'); from checks import common; t=open('SKILL.md',encoding='utf-8').read(); t=re.sub(r'\`[^\`]*\`','',t); print(dict(common.banned_hits(t, common.banned_rules())))"``
Expected: 사전 하나가 출력된다. 이 값을 보고서 파일에 적어 둔다.

- [ ] **Step 2: 고칠 대목을 고친다**

아래 대목만 고친다. 다른 대목의 문장은 바꾸지 않는다.

- **「작업 방식」 표:** 행을 추가한다. 조건 칸은 '마무리 보고서 작성(작업을 끝내고 결과·남은 일·결정 사항을 알리는 보고서)', 시작점 칸은 '페이지형이면 `$S/template-paged.html`, 아니면 `$S/template.html`을 복사하고 `<main>`에 `data-kind="wrapup"`을 붙인다', 본문 글 칸은 '`$S/마무리-보고서.md`를 읽고 따른다. 견본은 `$S/examples/wrapup.html`이다'.
- **「작업 과정」 2단계 행:** 확인 방법 칸 끝에 '마무리 보고서는 미결정 사항을 쓰기 전에 하나씩 결정받는다(`마무리-보고서.md` 「결정 먼저」)'를 덧붙인다.
- **「글쓰기 규칙」 표의 `<title>`·`h1`·`h2` 행:** 두 행으로 나눈다. 첫 행의 요소 칸은 '`<title>`, `h1`, 단일 문서의 `h2`, 페이지형 문서의 절 이름(`p.sec`)과 결론 없는 페이지의 `h2` (목차)'이고, 형태 칸은 지금 문장을 유지한다. 둘째 행의 요소 칸은 '페이지형 문서에서 `p.sec` 아래의 `h2` (결론 제목)'이고, 형태 칸은 '`TITLE-LAYERS`·`TITLE-CLAIM`의 본문 제목. 주어와 서술어를 갖춘 결론 한 문장으로 쓰고 수치·기간·비교를 넣는다. 40자 이하'다. 이어지는 `.lede`·절 첫 문장 행의 요소 칸 앞에 '단일 문서의'를 붙인다.
- **「페이지 구성」 '후보' 불릿:** 괄호 안 '제목이 \'요약·결론·부록\'으로 시작하는 페이지'를 '페이지 이름이 \'요약·결론·부록\'으로 시작하는 페이지. 페이지 이름은 `p.sec`, 없으면 첫 `h1`·`h2`의 글이다'로 바꾼다.
- **「페이지 구성」 순서 목록:** 목록 앞 문장 '이 순서가 `TITLE-CLAIM`의 \'결론 한 문장\' 형식보다 우선한다. 한 문장으로 압축한 결론은 전달이 안 된다는 사용자 지시에 따른 형식이다.'를 '결론 제목 한 문장은 `TITLE-LAYERS`를 따르고, 그 아래 여러 줄 불릿은 압축한 소제목 대신 결론을 풀어 쓰라는 2026-09-27 사용자 지시를 따른다.'로 바꾼다. 목록은 다음 순서로 바꾼다. 1 `p.sec`: 절 이름. 목차(`.toc`) 링크 글과 같은 명사구. 2 `h2`: 결론 제목. 이 페이지의 결론 한 문장. 3 `ul.pts`: 결론 불릿. 제목의 결론을 여러 줄로 풀고 수치와 조건을 넣는다. 줄마다 한 가지만 쓴다. 4~7은 지금의 근거·중요 포인트·유의사항·출처 항목을 그대로 둔다. 목록 뒤에 '결론이 없는 페이지(요약, `class="page list"`인 절차·목록·부록)는 `p.sec` 없이 명사구 `h2`만 둔다.'를 넣는다.
- **「페이지 구성」 끝:** 굵은 라벨 불릿 두 개를 추가한다. **반복 금지:** 한 페이지에서 결론 불릿·도식·표가 같은 사실을 반복하지 않는다. 도식은 표로 보이기 어려운 구조·흐름·동작을 보일 때만 둔다. 도식의 형태와 그리는 방법은 `$S/시각화.md`가 정한다. **확인 상태와 원자료(내부 검토 문서):** 결론 줄마다 `<span class="state" data-state="run|infer|assume">`과 글자(실행으로 확인함·추론함·가정함)를 쓴다. `run`은 같은 줄에 명령·출력·커밋·파일 줄이 있을 때만 쓴다. 외부 독자 문서에는 쓰지 않는다.
- **「독자 구분」 표 내부 검토 문서 행:** 쓰는 방식 칸 끝에 '결론 줄마다 확인 상태를 표시한다(「페이지 구성」의 확인 상태와 원자료)'를 덧붙인다.
- **「완료 기준」 3:** 헤드리스 Edge 단계(설명 문장과 명령 줄)를 다음으로 바꾼다. '`python $S/eval/gates.py <파일>.html` → 종료 코드 0. 실패 항목은 결과 JSON에서 `"status": "fail"`인 항목이다. 이어서 `python $S/eval/shoot.py <파일>.html <빈 임시 폴더>`로 장면과 글을 만들고, 그 폴더와 `$S/eval/checklist.md`만 받은 검토 서브에이전트가 체크리스트를 1회 확인한다. \'아니오\' 항목은 고치거나 고치지 않은 이유를 보고에 적는다.'
- **「완료 기준」 4 목차 읽기·결론 읽기:** 목차 읽기는 '**목차 읽기:** 단일 문서는 `h1`·`h2`와 `.toc`, 페이지형 문서는 `.toc`와 `p.sec`만 모아 읽어 목차로 읽히는지 확인한다.'로 바꾼다. 결론 읽기는 '**결론 읽기:** 단일 문서는 절의 첫 문장, 페이지형 문서는 결론 제목(`p.sec` 아래 `h2`)만 모아 읽어 논지가 결론까지 이어지는지(`TITLE-PROOF`) 확인한다.'로 바꾼다. 용어 풀이 불릿 끝에 '새 규약 문서(`p.sec`나 `data-kind="wrapup"`이 있는 문서)는 check.py가 풀이 없는 영문 약어를 검출한다.'를 덧붙인다.
- **「흔한 실수」 '라벨에 내용을 넣음':** 첫 문장 앞에 '목차 라벨(`<title>`·`h1`·단일 문서의 `h2`·`p.sec`·결론 없는 페이지의 `h2`)에'를 넣어 대상을 한정한다. '결론은 절의 첫 문장에 쓴다.'를 '단일 문서의 결론은 절의 첫 문장에, 페이지형 문서의 결론은 `p.sec` 아래 `h2`에 한 문장으로 쓴다.'로 바꾼다. 마지막 문장 '완료 전에 … 확인한다.'는 '완료 전에 완료 기준 4의 목차 읽기와 결론 읽기를 한다.'로 바꾼다.

- [ ] **Step 3: 고친 결과를 확인한다**

Run: ``grep -n "형식보다 우선한다\|목차(\`.toc\`)와 같은 명사구\|헤드리스 Edge\|msedge" SKILL.md``
Expected: 출력 없음.

Run: `for s in 'data-kind="wrapup"' '마무리-보고서.md' 'examples/wrapup.html' 'eval/gates.py' 'eval/shoot.py' 'p.sec' 'data-state=' '반복 금지' '2026-09-27'; do printf '%s ' "$s"; grep -c -F "$s" SKILL.md; done`
Expected: 모든 줄의 수가 1 이상.

Run: Step 1과 같은 금지어 명령.
Expected: 낱말마다 수가 Step 1의 값 이하.

- [ ] **Step 4: 커밋한다**

```bash
git add SKILL.md
git commit -m "C3: SKILL.md에 제목 체계·마무리 보고서·C0 하네스 완료 기준을 넣는다

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F"
```

### Task 6: 견본 `examples/wrapup.html`

**Files:**
- Create: `examples/wrapup.html`

**Interfaces:**
- Consumes: Task 1~3 규칙, `마무리-보고서.md`(Task 4), SKILL.md 페이지 구성(Task 5), C2 클래스 계약
- Produces: spec 「검증」 1·2·5의 대상 문서

- [ ] **Step 1: 견본을 쓴다**

`template-paged.html`은 열지 않는다(Global Constraints). 문서 구조는 다음과 같다.

- **머리:** `<!doctype html><html lang="ko">`, `<meta charset="utf-8">`, viewport 메타, 24자 이하 명사구 `<title>`, `<style>`과 그 안의 두 줄 `/* BEGIN report-base */`·`/* END report-base */`(줄바꿈으로 나눈다). CDN 스크립트·RC 함수·문서 전용 CSS는 쓰지 않는다.
- **본문 틀:** `<main class="doc paged" data-kind="wrapup">` 안에 `<nav class="pager">`(이전 버튼, `<span class="cnt"></span>`, 다음 버튼), `<p class="toc">`(페이지마다 `<a href="#pN">N. 절 이름</a>`, 가운뎃점으로 나열), 페이지 6개를 둔다. 별 표시는 링크의 `class="core"`·`class="key"`로만 하고 ★·☆ 문자는 쓰지 않는다(이모지 위반).
- **p1 요약:** `<section class="page summary" id="p1">`. `.sec` 없이 `.pno`, `div.doc-head`(소속·날짜 줄 `p.meta`, `h1`, `p.basis`, 첫 문장이 독자의 질문인 `.lede`), `.keyfig`(각 `div`에 `data-src`와 `span.k`·`span.v`), `div.gist`(명사구 `h2` '요약', 결론 `li`마다 `data-src`), `dl.gloss`(약어와 내부 용어 풀이)를 둔다.
- **p2~p6:** 각각 `<section class="page" id="pN" data-part="…">`이며 순서는 changed·achieved·remaining·decisions·verification이다. 각 페이지는 `.pno`, `p.sec`(목차 링크 글과 같은 명사구), `h2`(40자 이하 결론 한 문장, 수치 포함), `ul.pts`(결론 줄마다 `span.state`와 글자, `run` 줄에는 같은 줄의 `code` 명령·출력·커밋·파일), `p.blk` '근거'와 `table`, `p.blk` '중요 포인트'+`ul.pts`, `p.blk.warn` '유의사항'+`ul.pts`, `p.blk` '출처'+`ul.pts.src-list` 순서다.
- **바뀐 것 페이지:** 변경 전·변경 후 열 표를 두고 바뀐 칸은 `td.chg`로 둔다.
- **결정 요청 페이지:** 정할 사항마다 선택지·권장안과 이유·기각한 대안과 이유가 보이는 표를 두고, '결정한 사항' 행을 하나 이상 둔다.
- **내용:** 가상의 작업(예: 가상 팀의 월간 성과 표 생성 스크립트 개선)이며 `.lede`와 출처 줄에 가상이라고 밝힌다. 사내 이름·실제 경로·실제 수치를 쓰지 않는다. 불릿은 결론, 표는 근거 수치로 나눠 같은 사실을 되풀이하지 않는다. 영문 약어는 `.gloss`에 두거나 처음 나온 곳에서 괄호로 풀이한다.
- **문서 스크립트:** `</main>` 뒤 `<script>` 하나. `document.documentElement.classList.add('js')`를 실행하고, 주소 끝이 `#pN`이면 그 페이지, 아니면 첫 페이지에 `on` 클래스를 단다. 목차 링크 `on` 표시, `.cnt`의 'N / 6', 이전·다음 버튼, 좌우 화살표 키(`ArrowLeft`·`ArrowRight`), `hashchange` 처리를 넣는다. 색 리터럴과 금지어를 쓰지 않는다.

- [ ] **Step 2: 관리 블록을 채운다**

Run: `python build.py examples/wrapup.html`
Expected: `examples/wrapup.html: 기준 CSS 반영`

- [ ] **Step 3: 규칙 검사를 실행한다**

Run: `python check.py examples/wrapup.html`
Expected: 위반이 모두 `라벨이 명사구가 아님(`으로 시작하고, 각 위반 글이 p2~p6의 `p.sec` 아래 `h2` 글과 같다. 이 위반을 이 plan에서 '결론 제목 라벨 위반'이라 부른다. 점수표의 평가와 목차 표시가 다르면 목차 링크의 `class`를 평가대로 고치고 다시 실행한다. 다른 위반이 있으면 견본을 고친다.

- [ ] **Step 4: 구조를 확인한다**

Run: `for s in 'class="chg"' 'data-state="run"' 'data-state="infer"' 'data-state="assume"' '결정한 사항' 'class="gloss"' 'hashchange' 'ArrowRight'; do printf '%s ' "$s"; grep -c -F "$s" examples/wrapup.html; done`
Expected: 모든 줄의 수가 1 이상.

Run: `python eval/gates.py examples/wrapup.html --only layout --judge-hash-nav --out <스크래치패드>/wrapup-layout.json`
Expected: 결과 JSON에서 `hash-nav` 항목이 `pass`다. 다른 layout 항목(`page-number`, `rules-layout` 등)의 실패는 C2 병합 전 CSS와 결론 제목 라벨 위반 때문일 수 있으므로 기록만 한다.

- [ ] **Step 5: 커밋한다**

```bash
git add examples/wrapup.html
git commit -m "C3: 페이지형 마무리 보고서 견본을 추가한다

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F"
```

### Task 7: spec 「검증」 실행과 리포트(L2가 직접)

**Files:**
- Modify: 자가 점검에서 고칠 일이 생기면 `examples/wrapup.html`만 고친다.

**Interfaces:**
- Consumes: Task 1~6의 산출물
- Produces: 최종 응답 본문의 리포트

- [ ] **Step 1: 규칙 검사** — `python check.py examples/wrapup.html`. 기대: 위반이 결론 제목 라벨 위반뿐이다.
- [ ] **Step 2: 기계 판정** — `python eval/gates.py examples/wrapup.html --only content`. 기대: `rules-all`의 `detail`이 결론 제목 라벨 위반뿐이다.
- [ ] **Step 3: 고정 견본 오탐** — `python -B -m unittest tests.test_content.FixedNoFalsePositive -v`가 통과한다. 이 시험이 고정 견본과 `template.html`에서 규칙별 0건을 확인한다.
- [ ] **Step 4: 실제 글의 약어 후보** — 판별 없이 `unglossed`를 고정 견본에 실행해, 새 규약 문서였다면 나왔을 약어 목록을 리포트에 적는다. 이 목록은 규칙의 오탐 범주를 판단하는 참고이며 판정 기준이 아니다.

```bash
python -B -c "
import sys; sys.path.insert(0,'.')
from pathlib import Path
from checks import content
for f in sorted(Path('bench/fixed').glob('*.html')):
    print(f.name, content.unglossed(f.read_text(encoding='utf-8')))
"
```

- [ ] **Step 5: 단위 시험** — `python -B -m unittest discover -s tests`. 기대: `OK (skipped=1)`.
- [ ] **Step 6: 자가 점검** — `python -B -c "import tempfile; print(tempfile.mkdtemp())"`로 저장소 이름이 없는 빈 폴더를 만들고 `python eval/shoot.py examples/wrapup.html <폴더>/shots`로 찍는다. `eval/checklist.md`의 머리말 문단과 content 항목 네 행(`titles-tell-story`, `no-triple-repeat`, `decision-recommend`, `claims-sourced`)만 옮긴 `checklist.md`를 `<폴더>`에 만든다. 서로 독립된 검토 서브에이전트 3개에게 다음 고정 지시문만 준다. "`<폴더>/shots`의 PNG 장면, txt 글, index.json만 보고 `<폴더>/checklist.md`의 항목마다 '예'·'아니오'·'해당 없음'과 이유 한 문장을 JSON 목록 `[{"id", "answer", "reason"}]`으로 답하라. 다른 파일은 열지 마라." 항목별 다수결로 충족률(다수결 '예' 수 ÷ '해당 없음'이 아닌 항목 수)을 계산한다. 85% 미만이면 '아니오' 이유를 근거로 `examples/wrapup.html`만 고쳐 `C3: 견본을 자가 점검 지적대로 고친다` 메시지로 커밋하고, 새 빈 폴더로 다시 찍는다. 이 차례는 3번까지다. 세 번째에도 85% 미만이면 결과를 리포트에 적고 작업을 끝낸다. 규칙 문서를 고칠 이유는 리포트에 적는다.
- [ ] **Step 7: 리포트** — 최종 응답 본문에 다음을 싣는다. 상태(DONE 또는 BLOCKED), 변경 파일, 시험 결과, 기계 판정과 고정 견본 오탐 결과(Step 3·4), Task 6 Step 4의 layout 판정 기록, 자가 점검 차례별 결과, plan 리뷰에서 기능적 변화가 있었던 반영, spec·상위 설계와 다르게 정한 점(「이 plan이 정한 해석」 전부와 `template-paged.html` 미확인), 브랜치 이름 `c3-content-rules`.

## 자체 점검

- **spec 범위:** 규칙 문서 배치(Task 4·5), 필수 절(Task 3·4), 작업 과정 변경(Task 4·5), 제목 체계(Task 5), 확인 상태와 반복 금지(Task 4·5), 새 규칙과 페이지 이름 읽기(Task 1~3), 견본(Task 6), 검증 1~5와 산출 계약(Task 7)에 대응한다.
- **이름 일관성:** `page_name`, `strip_tags`, `SEC`, `WRAPUP`, `is_new_doc`, `unglossed`, `abbr_violations`, `parts_violations`, `basis_violations`, `PARTS`가 Task 사이에 같은 이름으로 쓰인다.

<!-- spec-review: passed -->
