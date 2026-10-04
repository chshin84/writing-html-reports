# C0 평가 하네스 구현 plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 고정 견본, 기계 판정 명령, 장면 명령, 재빌드 명령, 체크리스트와 프롬프트 틀, 최소 견본을 만들고 기준 커밋 `512d308`의 기준선을 `eval/baseline/`에 남긴다.

**Architecture:** 브라우저 밖의 순수 계산(`eval/measure.py`)과 브라우저 안의 원시값 수집(`eval/probe.js`)을 나눈다. 문서 열기와 측정 시작 조건은 `eval/harness.py` 하나가 맡는다. 판정 항목은 대상별 모듈(`eval/motion.py`, `eval/layout.py`, `eval/rules.py`)이 만들고, `eval/gates.py`는 이 모듈을 호출해 JSON으로 묶는다. `eval/shoot.py`와 `eval/rebuild.py`는 독립 명령이다.

**Tech Stack:** Python 3 표준 라이브러리, Python Playwright 1.63.0 헤드리스 Chromium, `http.server`, unittest.

**Spec:** `docs/superpowers/specs/2026-10-04-c0-eval-harness-design.md`(상위 설계 `docs/superpowers/specs/2026-10-04-report-quality-architecture-design.md`)

## Global Constraints

- **소유 파일:** spec이 정한 소유 파일은 `eval/**`, `bench/**`, `tests/test_eval_*.py`다. L1의 지시로 이 plan과 리뷰 기록도 고칠 수 있다. 그 밖의 파일은 읽기만 하고, 고쳐야 하면 멈추고 BLOCKED로 돌려준다.
- **저장소 밖 작업:** `D:/projects/Structure/lens-groups-report/`의 HTML을 읽어 `bench/fixed/`로 복사하는 일만 한다.
- **보류 자료:** 정답 질문, 심을 오류, 보류 견본은 만들지도 찾지도 않는다.
- **시험 명령:** 워크트리 루트에서 `python -B -m unittest discover -s tests`를 실행한다.
- **화면 측정 도구:** Python Playwright 1.63.0의 헤드리스 Chromium만 쓴다. Playwright MCP 도구는 쓰지 않는다.
- **로컬 서버:** `127.0.0.1`의 빈 포트(포트 0)로 띄우고, `with` 블록을 나가면 반드시 끈다.
- **환경 실패:** 측정 시작 조건이 15초 안에 갖춰지지 않거나 다른 출처(CDN)의 요청이 실패하면 환경 실패로 기록하고 종료 코드 2를 돌려준다.
- **명령 셸:** 명령 예시는 Git Bash 문법이다. PowerShell 리디렉션은 바이트를 바꾸므로 쓰지 않는다.
- **`<스크래치>`:** 세션 스크래치패드 아래의 `c0` 폴더(`C:/Users/ho381/AppData/Local/Temp/claude/D--projects-Structure-writing-html-reports/d5fb1593-166c-41a5-bca7-de1d08dffdcb/scratchpad/c0`)를 가리킨다. 코드에 넣을 때는 이 절대 경로로 바꾼다.
- **리포트:** L2가 L1에게 돌려주는 상세 보고다. 경로는 스크래치패드의 `report-c0.md`이고 브랜치에 커밋하지 않는다(Task 11).
- **화면 크기:** 1280×800과 390×844이다.
- **문서 규칙:** 문서·주석·커밋 메시지는 한국어 문어체로 쓴다. 에이전트원칙 `C:/Users/ho381/.claude/disciplined-coder/agent-principles.md`와 한국어 규칙 `C:/Users/ho381/.claude/plugins/cache/chshin-tools/disciplined-coder/4edfe8ef3073/skills/lens-readability/domain-korean.md`를 따른다.
- **커밋 꼬리말:** 커밋 메시지 끝에 `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`과 `Claude-Session: https://claude.ai/code/session_01C9ksw3MJCMHdeTziLawb2F`를 붙인다.

문턱값은 상위 설계의 표를 따른다. 체류 시간의 하한은 1 + n/8초이고 상한은 하한에 3초를 더한 값이다. n은 그 단계에서 새로 보인 글의 글자 수다(공백 제외, 숫자 묶음 1자). 단계 넘김의 연출 길이는 0.4초 이상 2.5초 이하이고 허용 오차는 0.1초다. 1단계는 처음 연 상태의 타임라인 시간이 0.05초 이하이고 첫 단계 끝까지 0.2초 이상 걸려야 한다. 설명 상자는 현재 노드에서 48px 이내다. 화면상 글자는 11px 이상, 390 폭 표 셀은 56px 이상이다. 글자 대비는 4.5:1이고 큰 글자는 3:1이다. 그래픽 대비는 3:1이다. 계열 색은 제2색각 모의 변환 뒤 CIE76 색차(Lab 색공간의 유클리드 거리)가 15 이상이다.

## 이 plan이 정한 해석

spec이 정하지 않은 점을 아래처럼 정한다. 리포트에 spec과 다르게 정한 점으로 옮긴다.

- **테마별 기록:** 밝은 테마 기록에는 모든 항목을 넣는다. 어두운 테마 기록에는 테마에 따라 값이 바뀌는 `contrast-text`·`contrast-graphic`·`cvd`만 넣는다.
- **계열 색 토큰:** `cvd`는 `--s1`~`--s4` 네 토큰을 쓴다.
- **굵은 글자:** 큰 글자 예외의 '굵은'은 `font-weight` 700 이상이다(WCAG 정의).
- **SVG 글자 측정 시점:** `svg-font-390`은 처음 연 상태의 글자에 더해, 애니메이션 figure의 단계 끝마다 보이는 글자를 함께 측정한다. 투명도 0인 글자도 화면에 그려지는 요소이면 측정한다.
- **그래픽 대비 측정 시점:** 처음 연 상태에 더해 애니메이션 figure의 단계 끝마다 노드 테두리를 측정한다. 지나온 노드 색이 바뀌는 엔진을 잡기 위해서다.
- **현재 노드의 조건:** 단계 끝마다 `.rc-note`·`.rc-icon` 밖의 보이는 `data-rc-active` 요소가 정확히 하나여야 한다. `data-rc-active`가 어느 단계에도 없으면 측정 불가이고, 한 단계라도 있으면 측정 가능으로 본다. 현재 노드가 없거나 둘 이상인 단계는 `note-near`·`active-visible` 실패로 센다.
- **설명 상자 판정의 단계 이동:** spec은 '재생 전에 한 번 스크롤하고 그 뒤의 스크롤은 엔진의 몫'이라고 정한다. 그래서 측정기는 타임라인을 직접 옮기지 않고 엔진의 '처음부터'와 '다음' 버튼으로 단계를 넘긴다. 누를 때마다 타임라인 시간과 창 스크롤이 300ms 동안 멈출 때까지(상한 10초) 기다린 뒤 측정한다. 엔진이 버튼 핸들러에 둔 스크롤과 자막 갱신이 그대로 반영된다.
- **장면의 단계 길이:** `shoot.py`는 `index.json`의 단계 장면마다 그 단계의 타임라인 길이(`seconds`, 연출과 머무는 시간의 합)를 적는다. 정지 장면만으로는 체류 시간 결함을 판정할 수 없기 때문이다.
- **단일 문서의 장면 이름:** 단일 문서는 화면 높이 단위 장면을 `v1`, `v2` …로 부르고, 보이는 글은 `doc.txt` 하나에 남긴다.
- **`rebuild.py`의 견본 폴더:** 시험에서 build.py 실패를 재현하려고 `main(argv, bench=None)` 함수 인자를 둔다. 명령줄 인자는 spec대로 `<출력 폴더>` 하나다.
- **관리 블록 대조 대상:** build.py가 report-charts 블록에 `report-peeps.js`를 이어 넣으므로 rebuild.py는 이 파일까지 대조한다.
- **기준 견본 대조의 근거:** 체크리스트 음성 대조에 쓰는 '견본별 알려진 결함'은 `docs/superpowers/research/2026-10-04-report-quality/visual-review-baseline.md`에서 옮겨 `eval/baseline/known-defects.json`에 둔다. 저장소에 이미 있는 공개 기록이므로 보류 자료에 들지 않는다. 검토자가 읽지 못하게 체크리스트 검토가 끝난 뒤에 쓴다.
- **방식 때문에 측정하지 않는 항목:** `--mode auto`의 `step-anim`과 `--mode step`의 `dwell`은 기록에서 빼지 않고 `n/a`로 두고, `detail`에 이유를 적는다. 모든 기록이 같은 항목 목록을 가져 비교하기 쉽게 하기 위해서다.
- **반투명 글자:** 요소의 불투명도가 1보다 작은 글자는 글자색의 알파에 불투명도를 곱해 바탕과 합성한 뒤 측정한다. spec이 정한 측정 불가(바탕을 정할 수 없음)만 측정 불가로 둔다.
- **보이는 요소:** `checkVisibility`와 조상 불투명도 0.05 초과에 더해, 경계 상자 면적이 1px² 이상이고 `clip-path`가 `none`이며 글자색(SVG는 `fill`)의 알파가 0이 아닌 요소만 보인다고 본다.
- **겹침 판정의 아이콘:** spec대로 스틱맨 아이콘(`image`를 가진 `.rc-icon`)만 무대 요소에서 뺀다. 선으로 그린 상태 아이콘은 무대 요소다.
- **SVG 밖 설명 상자의 글자:** 단계 끝마다 보이는 `.rc-note` 안의 글자는 SVG 안팎을 가리지 않고 `svg-font-390`에 넣는다.
- **스크롤 상자:** `overflow-x`가 `auto`나 `scroll`인 조상만 스크롤 상자로 본다. `html`이나 `body`의 `overflow-x`가 `hidden`·`clip`이면 `overflow-390`을 실패로 센다.
- **렌더 실패:** 엔진이 그림을 그리지 못해 `.viz-fail`을 붙인 요소는 측정 시작 조건에서 '준비됨'으로 받는다. 대신 기록의 `render_fail`에 남기고, 하나라도 있으면 종료 코드 1로 센다. 문서 결함을 환경 실패로 잘못 분류하지 않기 위해서다.
- **같은 출처 요청 실패:** 로컬 서버의 404 같은 같은 출처 실패는 환경 실패가 아니다. 기록의 `load_errors`에 남기고 종료 코드 1로 센다.
- **처리되지 않은 예외:** 측정 중 EnvFail 밖의 예외가 나면 그 기록의 `env`를 `error`로 하고 메시지를 남긴다. 종료 코드는 3이다(우선순위 2 > 3 > 1).
- **열린 페이지 확인:** 주소 끝 `#pN`으로 연 뒤 그 페이지가 보이지 않으면 환경 실패로 기록한다. 해시 처리가 없는 문서에서 다른 페이지를 재는 일을 막기 위해서다. `hash-nav`는 이 확인을 하지 않는다.
- **고정 견본의 hash-nav:** spec대로 기록만 한다. gates.py는 다른 항목과 같이 판정값을 남기되 `value.recorded_only`를 `true`로 두고, 종료 코드 계산에서 뺀다. L1이 `template-paged.html`이나 재생성본을 측정할 때는 `--judge-hash-nav`를 준다.
- **원문 사실의 계산:** 해당 없음을 정하는 원문 사실(RC.demo 호출 수, SVG 유무, 페이지 id)은 피평가 워크트리의 `checks/`에 기대지 않고 `eval/measure.py`가 직접 계산한다.
- **기계 판정 기준선 횟수:** 상위 설계 「평가 자료의 격리」가 고정 견본 기준선을 3회 측정한다고 적으므로, 방식마다 gates.py를 세 번 실행해 따로 남기고 항목별 일치를 기록한다.

## Review Focus

- **한글·공백이 든 파일 이름:** 주소를 만들 때 `urllib.parse.quote`로 인코딩해야 한다. Task 3의 시험이 `시험 문서.html`을 연다.
- **CDN 차단:** 외부 스크립트가 실패하면 엔진이 정적 목록으로 물러난다. 측정기는 이것을 측정 불가로 두지 않고 환경 실패로 기록해야 한다. Task 3의 시험이 닿지 않는 주소의 스크립트를 넣는다.
- **여러 문서 중 하나의 환경 실패:** 한 문서가 환경 실패여도 나머지 문서는 측정하고 종료 코드는 2다. Task 5의 시험이 두 문서를 함께 넘긴다.
- **예외 뒤 서버 정리:** 측정 중 예외가 나도 서버 포트가 닫혀야 한다. Task 3의 시험이 예외를 던진 뒤 같은 포트에 연결해 거부되는지 본다.
- **숨은 페이지의 그림:** 숨은 페이지의 SVG는 폭이 0이라 화면상 글자 크기가 0으로 나온다. 측정기는 페이지마다 그 페이지를 주소 끝 `#pN`으로 새로 연 뒤, 보이는 요소만 측정한다. Task 4의 시험은 2페이지에 SVG 글자와 8px HTML 글자를 함께 두고, 1페이지를 열었을 때 이 글자들이 세어지지 않는지 본다.

## 파일 구조

| 경로 | 책임 |
|---|---|
| `bench/fixed/*.html`, `bench/fixed/SOURCES.json` | 고정 견본 사본과 출처 기록 |
| `eval/measure.py` | 브라우저 없는 계산: 글자 수, 체류 시간, 색·대비, 색각 변환, 거리·겹침, 페이지 번호, 원문 사실, 항목 묶음 |
| `eval/probe.js` | 문서 안에서 원시값을 모으는 함수 `window.__c0` |
| `eval/harness.py` | 로컬 서버, 브라우저 세션, 문서 열기와 측정 시작 조건, 환경 실패 |
| `eval/motion.py` | `dwell`·`step-anim`·`step1`·`note-near`·`active-visible` |
| `eval/layout.py` | 390 폭 항목, 대비, 색각, 페이지 번호, 해시 이동 |
| `eval/rules.py` | 규칙 항목(`rules-motion`·`rules-layout`·`rules-all`)과 `--base-checks` |
| `eval/gates.py` | 기계 판정 명령 |
| `eval/shoot.py` | 장면 명령 |
| `eval/rebuild.py` | 재빌드 명령 |
| `eval/checklist.md`, `eval/checklist_vote.py` | 체크리스트와 3회 다수결·충족률 |
| `eval/prompts/*.md` | 체크리스트 검토, 이해도 시험, 심어 둔 오류, 제목 연결 틀 |
| `eval/validation/minimal-anim.html` | 현재 엔진으로 문턱값 일부를 지키는 최소 견본 |
| `eval/baseline/` | 기준선 결과 |
| `tests/test_eval_measure.py` | 순수 계산 시험 |
| `tests/test_eval_harness.py` | 문서 열기·환경 실패 시험(합성 HTML) |
| `tests/test_eval_gates.py` | 판정 항목과 명령 시험(합성 HTML, 가짜 타임라인) |
| `tests/test_eval_commands.py` | rebuild·shoot·고정 견본·체크리스트·프롬프트 시험 |

시험은 모두 합성 HTML만 쓰고 외부 네트워크를 쓰지 않는다. eval 모듈은 `sys.path`에 `eval/`을 넣어 가져온다.

---

### Task 1: 고정 견본과 재빌드 명령

**Files:**
- Create: `bench/fixed/04-rules.html`, `bench/fixed/03-groups.html`, `bench/fixed/session-report.html`, `bench/fixed/sample-anim.html`, `bench/fixed/sample-viz.html`, `bench/fixed/SOURCES.json`, `bench/.gitattributes`
- Create: `eval/rebuild.py`
- Test: `tests/test_eval_commands.py`

**Interfaces:**
- Consumes: 현재 워크트리의 `build.py`(실행만), `report-base.css`·`report-demo.css`·`report-charts.js`·`report-peeps.js`(읽기만)
- Produces: `python eval/rebuild.py <출력 폴더>`. 종료 코드 0(성공), build.py의 코드(빌드 실패), 1(관리 블록 불일치 또는 견본 없음). 함수 `main(argv=None, bench=None) -> int`, `mismatches(path) -> list[str]`.

- [ ] **Step 1: 고정 견본 복사와 출처 기록**

이 저장소는 `core.autocrlf=true`라 checkout 때 줄바꿈이 바뀐다. 고정 견본이 SHA-256과 계속 맞도록 `bench/.gitattributes`에 `* -text`를 둔다. 아래 명령은 Git Bash에서 실행한다.

```bash
printf '# 고정 견본은 바이트 그대로 보관한다. SOURCES.json의 SHA-256이 checkout 뒤에도 맞게 줄바꿈 변환을 끈다.\n* -text\n' > bench/.gitattributes
cd D:/projects/Structure/whr-c0
mkdir -p bench/fixed
for f in 04-rules 03-groups session-report; do cp "D:/projects/Structure/lens-groups-report/$f.html" bench/fixed/; done
git show 512d308:tests/sample-anim.html > bench/fixed/sample-anim.html
git show 512d308:tests/sample-viz.html > bench/fixed/sample-viz.html
python -B - <<'EOF'
import hashlib, json
from pathlib import Path
src = {"04-rules.html": "D:/projects/Structure/lens-groups-report/04-rules.html",
       "03-groups.html": "D:/projects/Structure/lens-groups-report/03-groups.html",
       "session-report.html": "D:/projects/Structure/lens-groups-report/session-report.html",
       "sample-anim.html": "tests/sample-anim.html", "sample-viz.html": "tests/sample-viz.html"}
rows = []
for name, s in src.items():
    rec = {"file": name, "source": s, "sha256": hashlib.sha256(Path("bench/fixed", name).read_bytes()).hexdigest()}
    if s.startswith("tests/"):
        rec["commit"] = "512d308"
    rows.append(rec)
Path("bench/fixed/SOURCES.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
EOF
```

`git show`의 출력이 바이트 그대로인지 `git show 512d308:tests/sample-anim.html | sha256sum`과 대조한다.

- [ ] **Step 2: 실패하는 시험 작성**

`tests/test_eval_commands.py`:

```python
"""C0 명령 시험: rebuild·shoot·고정 견본·체크리스트·프롬프트. 실행: python -B -m unittest discover -s tests"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")
CSS = "<style>\n/* BEGIN report-base (시험) */\n/* END report-base */\n</style>"


def run(*args):
    return subprocess.run([sys.executable, "-B", *map(str, args)], capture_output=True, text=True,
                          encoding="utf-8", env=ENV)


def digest(folder):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(folder).iterdir())}


class Bench(unittest.TestCase):
    def test_sources_match_files(self):
        rows = json.loads((ROOT / "bench/fixed/SOURCES.json").read_text(encoding="utf-8"))
        self.assertEqual({r["file"] for r in rows}, {"04-rules.html", "03-groups.html", "session-report.html",
                                                     "sample-anim.html", "sample-viz.html"})
        for r in rows:
            data = (ROOT / "bench/fixed" / r["file"]).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), r["sha256"], r["file"])


class Rebuild(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.bench = Path(self.tmp.name, "bench")
        self.out = Path(self.tmp.name, "out")
        self.bench.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_build_failure_code_passes_through_and_bench_unchanged(self):
        import rebuild
        (self.bench / "bad.html").write_text("<html><head></head><body></body></html>", encoding="utf-8")
        before = digest(self.bench)
        self.assertEqual(rebuild.main([str(self.out)], bench=self.bench), 1)  # build.py가 표시 없는 문서에서 1로 끝난다
        self.assertEqual(digest(self.bench), before)

    def test_success_fills_blocks_from_worktree(self):
        import rebuild
        (self.bench / "ok.html").write_text(f"<html><head>{CSS}</head><body></body></html>", encoding="utf-8")
        before = digest(self.bench)
        self.assertEqual(rebuild.main([str(self.out)], bench=self.bench), 0)
        built = (self.out / "ok.html").read_text(encoding="utf-8")
        self.assertIn((ROOT / "report-base.css").read_text(encoding="utf-8")[:200], built)
        self.assertEqual(digest(self.bench), before)

    def test_block_mismatch_fails(self):
        import rebuild
        p = Path(self.tmp.name, "x.html")
        p.write_text("<style>\n/* BEGIN report-base (시험) */\n낡은 내용\n/* END report-base */\n</style>", encoding="utf-8")
        self.assertEqual(rebuild.mismatches(p), ["report-base"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: 시험이 실패하는지 확인**

Run: `python -B -m unittest tests.test_eval_commands -v`
Expected: `Rebuild` 시험이 `eval/rebuild.py`가 없어 실패한다. `Bench`는 통과한다.

- [ ] **Step 4: `eval/rebuild.py` 구현**

```python
"""고정 견본 재빌드 명령.

사용법: python eval/rebuild.py <출력 폴더>
bench/fixed/의 HTML을 출력 폴더에 복사하고, 현재 워크트리의 build.py로 빌드한다. bench/는 바꾸지 않는다.
시험은 main(argv, bench=<견본 폴더>)로 다른 견본 폴더를 넘긴다.
build.py가 실패하면 그 종료 코드를 그대로 돌려준다. 빌드 뒤 관리 블록이 현재 워크트리의
report-base.css·report-demo.css·report-charts.js·report-peeps.js와 다르면 1을 돌려준다.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
BASE_BLOCK = re.compile(r"/\* BEGIN report-base[^*]*\*/\n(.*?)/\* END report-base \*/", re.S)
CHART_BLOCK = re.compile(r"/\* BEGIN report-charts[^*]*\*/\n(.*?)/\* END report-charts \*/", re.S)


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def mismatches(path):
    """관리 블록 가운데 현재 워크트리 파일과 다른 블록의 이름 목록."""
    html = Path(path).read_text(encoding="utf-8")
    bad = []
    base = BASE_BLOCK.findall(html)
    if not base or any(b != read("report-base.css") + read("report-demo.css") for b in base):
        bad.append("report-base")
    if any(c != read("report-charts.js") + "\n" + read("report-peeps.js") for c in CHART_BLOCK.findall(html)):
        bad.append("report-charts")
    return bad


def main(argv=None, bench=None):
    ap = argparse.ArgumentParser(description="고정 견본을 현재 워크트리의 CSS·JS로 다시 빌드한다")
    ap.add_argument("out")
    a = ap.parse_args(argv)
    bench = Path(bench) if bench else ROOT / "bench" / "fixed"
    files = sorted(bench.glob("*.html"))
    if not files:
        print(f"{bench}에 HTML 견본이 없다", file=sys.stderr)
        return 1
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    copies = []
    for f in files:
        shutil.copyfile(f, out / f.name)
        copies.append(out / f.name)
    r = subprocess.run([sys.executable, "-B", str(ROOT / "build.py"), *map(str, copies)],
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    if r.returncode:
        return r.returncode
    bad = {c.name: m for c in copies if (m := mismatches(c))}
    if bad:
        print(f"관리 블록이 현재 워크트리 파일과 다르다: {bad}", file=sys.stderr)
        return 1
    print(f"견본 {len(copies)}개를 {out}에 다시 빌드했다")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: 시험 통과 확인**

Run: `python -B -m unittest tests.test_eval_commands -v`
Expected: 모든 시험 PASS.

- [ ] **Step 6: 실제 견본 재빌드 확인**

Run: `python -B eval/rebuild.py <스크래치>/rebuilt && git status --short bench`
Expected: 종료 코드 0, `견본 5개를 … 다시 빌드했다`, `bench/` 변경 없음.

- [ ] **Step 7: 커밋**

```bash
git add bench eval/rebuild.py tests/test_eval_commands.py
git commit -m "C0: 고정 견본 사본과 재빌드 명령을 추가한다"
```

---

### Task 2: 브라우저 없는 측정 함수

**Files:**
- Create: `eval/measure.py`
- Test: `tests/test_eval_measure.py`

**Interfaces:**
- Consumes: 없음. 피평가 워크트리의 `checks/`를 가져오지 않는다.
- Produces (모두 `measure`에서 가져온다):
  - `chars(text) -> int`
  - `dwell_steps(samples: list[tuple[float, dict[str,str]]], ends: list[float]) -> list[dict]`. 단계마다 `{step, end, done, dwell, n, lo, hi, ok}`
  - `parse_color(s) -> tuple[r,g,b,a] | None`, `luminance(rgba)`, `blend(fg, bg)`, `contrast(c1, c2) -> float`, `text_threshold(px, weight) -> float`
  - `deutan(rgb) -> tuple`, `lab(rgb) -> tuple`, `delta_e76(a, b) -> float`, `cvd_pairs(colors: dict[str, rgb]) -> list[(a, b, de)]`
  - `gap(a, b)`, `overlap_area(a, b)`, `points_inside(points, box) -> int`, `inside_view(box, w, h) -> bool`, `escapes(box, width) -> bool`. 상자는 `(left, top, right, bottom)`
  - `note_steps(steps, view) -> list[dict]`. 입력 단계는 `{step, active: box|None, active_count, notes, boxes, points}`. 출력 단계마다 `{step, near, visible, why | distance, overlaps, edge_points}`
  - `page_number_count(texts, total) -> int`
  - `source_facts(html) -> {"demo_calls": int, "has_svg": bool, "pages": [str], "paged": bool}`
  - `item(id, target, status, value=None, detail=None) -> dict`, 상수 `ORDER`, `TARGET`, `THEMED`, `RULE_IDS`

- [ ] **Step 1: 실패하는 시험 작성**

`tests/test_eval_measure.py`:

```python
"""C0 순수 측정 함수 시험. 실행: python -B -m unittest discover -s tests"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
import measure as m  # noqa: E402

WHITE = (255, 255, 255, 1.0)


class Chars(unittest.TestCase):
    def test_spaces_removed_and_number_group_is_one(self):
        self.assertEqual(m.chars("고점 15 → -2bp"), len("고점#→-#bp"))
        self.assertEqual(m.chars("1,234.5원"), 2)


class Dwell(unittest.TestCase):
    def test_dwell_and_n(self):
        samples = [(0.0, {}), (0.5, {"a": "가나"}), (1.0, {"a": "가나다라"}), (4.0, {"a": "가나다라"})]
        s = m.dwell_steps(samples, [4.0])[0]
        self.assertEqual((s["done"], s["dwell"], s["n"]), (1.0, 3.0, 4))
        self.assertAlmostEqual(s["lo"], 1.5)
        self.assertTrue(s["ok"])

    def test_short_dwell_fails_and_unchanged_element_not_counted(self):
        samples = [(0.0, {"k": "같다"}), (1.0, {"k": "같다"}), (1.05, {"k": "같다", "c": "새 글"}), (1.32, {"k": "같다", "c": "새 글"})]
        s = m.dwell_steps(samples, [1.0, 1.32])[1]
        self.assertEqual(s["n"], 2)
        self.assertAlmostEqual(s["dwell"], 0.27, places=3)
        self.assertFalse(s["ok"])

    def test_changed_text_counts_whole_new_text_and_upper_bound(self):
        samples = [(0.0, {"k": "옛 글"}), (0.1, {"k": "새 글자"}), (9.0, {"k": "새 글자"})]
        s = m.dwell_steps(samples, [9.0])[0]
        self.assertEqual(s["n"], 3)
        self.assertFalse(s["ok"])  # 8.9초 > 1 + 3/8 + 3


class Color(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(m.parse_color("#8FA3BC"), (143, 163, 188, 1.0))
        self.assertEqual(m.parse_color("rgba(0, 0, 0, 0)"), (0.0, 0.0, 0.0, 0.0))
        self.assertEqual(m.parse_color("rgb(31, 58, 95)"), (31.0, 58.0, 95.0, 1.0))
        self.assertIsNone(m.parse_color("url(#g)"))

    def test_contrast_known_values(self):
        self.assertAlmostEqual(m.contrast(m.parse_color("#8FA3BC"), WHITE), 2.58, places=2)
        self.assertAlmostEqual(m.contrast((0, 0, 0, 1.0), WHITE), 21.0, places=2)

    def test_large_text_threshold(self):
        self.assertEqual(m.text_threshold(16, 400), 4.5)
        self.assertEqual(m.text_threshold(24, 400), 3.0)
        self.assertEqual(m.text_threshold(18.66, 700), 3.0)
        self.assertEqual(m.text_threshold(18.66, 600), 4.5)

    def test_blend(self):
        self.assertEqual(m.blend((0, 0, 0, 0.5), WHITE), (127.5, 127.5, 127.5, 1.0))


class Cvd(unittest.TestCase):
    def test_white_stays_white_and_lab(self):
        w = m.deutan((255, 255, 255))
        for c in w:
            self.assertAlmostEqual(c, 255, delta=0.5)
        L, a, b = m.lab((255, 255, 255))
        self.assertAlmostEqual(L, 100, places=1)

    def test_red_green_collapse_under_deutan(self):
        self.assertGreater(m.delta_e76((200, 60, 60), (60, 160, 60)), 15)
        de = m.delta_e76(m.deutan((200, 60, 60)), m.deutan((60, 160, 60)))
        self.assertLess(de, m.delta_e76((200, 60, 60), (60, 160, 60)))

    def test_pairs(self):
        p = m.cvd_pairs({"s1": (0, 0, 0), "s2": (255, 255, 255), "s3": (0, 0, 0)})
        self.assertEqual([(a, b) for a, b, _ in p], [("s1", "s2"), ("s1", "s3"), ("s2", "s3")])
        self.assertEqual(p[1][2], 0)


class Geometry(unittest.TestCase):
    def test_gap_and_overlap(self):
        self.assertEqual(m.gap((0, 0, 10, 10), (70, 0, 80, 10)), 60)
        self.assertEqual(m.gap((0, 0, 10, 10), (5, 5, 20, 20)), 0)
        self.assertEqual(m.overlap_area((0, 0, 10, 10), (5, 5, 20, 20)), 25)

    def test_points_and_view(self):
        self.assertEqual(m.points_inside([(1, 1), (50, 50), (5, 9)], (0, 0, 10, 10)), 2)
        self.assertTrue(m.inside_view((0, 0, 1280, 800), 1280, 800))
        self.assertFalse(m.inside_view((0, 700, 100, 900), 1280, 800))
        self.assertTrue(m.escapes((0, 0, 400, 10), 390))
        self.assertFalse(m.escapes((16, 0, 374, 10), 390))


class Notes(unittest.TestCase):
    VIEW = [1280, 800]

    def step(self, **kw):
        base = {"step": 1, "active": (100, 100, 200, 140), "notes": [(220, 100, 380, 140)], "boxes": [], "points": []}
        base.update(kw)
        return base

    def test_near_and_visible(self):
        r = m.note_steps([self.step()], self.VIEW)[0]
        self.assertTrue(r["near"] and r["visible"])

    def test_far_note_fails(self):
        r = m.note_steps([self.step(notes=[(260, 100, 420, 140)])], self.VIEW)[0]
        self.assertFalse(r["near"])
        self.assertEqual(r["distance"], 60)

    def test_missing_note_and_active(self):
        self.assertFalse(m.note_steps([self.step(notes=[])], self.VIEW)[0]["near"])
        self.assertFalse(m.note_steps([self.step(active=None)], self.VIEW)[0]["visible"])

    def test_two_active_nodes_fail(self):
        r = m.note_steps([self.step(active_count=2)], self.VIEW)[0]
        self.assertEqual((r["near"], r["why"]), (False, "현재 노드가 둘 이상"))

    def test_overlap_and_edge_points(self):
        r = m.note_steps([self.step(boxes=[(300, 120, 340, 160)])], self.VIEW)[0]
        self.assertFalse(r["near"])
        r = m.note_steps([self.step(points=[(300, 110)])], self.VIEW)[0]
        self.assertFalse(r["near"])
        self.assertEqual(r["edge_points"], 1)

    def test_offscreen_active(self):
        r = m.note_steps([self.step(active=(100, 900, 200, 940), notes=[(220, 900, 380, 940)])], self.VIEW)[0]
        self.assertTrue(r["near"])
        self.assertFalse(r["visible"])


class PageNumber(unittest.TestCase):
    def test_count(self):
        self.assertEqual(m.page_number_count(["2 / 3", "2 / 3", "1/28", "2/3"], 3), 3)
        self.assertEqual(m.page_number_count(["1/28"], 3), 0)


class Facts(unittest.TestCase):
    def test_demo_svg_pages(self):
        html = ('<nav class="pager"></nav><section class="page" id="p1"><svg></svg></section>'
                '<section class="page" id="p2"></section>'
                "<script>/* BEGIN report-charts x */RC.demo(a)/* END report-charts */</script>"
                "<script>RC.demo(document.getElementById('d'), [])</script>")
        f = m.source_facts(html)
        self.assertEqual(f, {"demo_calls": 1, "has_svg": True, "pages": ["p1", "p2"], "paged": True})

    def test_engine_block_only(self):
        html = '<script>/* BEGIN report-charts x */RC.demo(a);"<svg>"/* END report-charts */</script><p>글</p>'
        self.assertEqual(m.source_facts(html), {"demo_calls": 0, "has_svg": False, "pages": [], "paged": False})

    def test_mermaid_or_chart_counts_as_svg(self):
        self.assertTrue(m.source_facts('<pre class="mermaid">graph TD;A-->B</pre>')["has_svg"])
        self.assertTrue(m.source_facts("<script>RC.chart(box, {})</script>")["has_svg"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 실패 확인**

Run: `python -B -m unittest tests.test_eval_measure -v`
Expected: `ModuleNotFoundError: No module named 'measure'`.

- [ ] **Step 3: `eval/measure.py` 구현**

```python
"""C0 측정 함수. 브라우저가 모은 원시값으로 판정값을 계산한다. 이 모듈은 브라우저를 쓰지 않는다."""
import math
import re

# 원문 사실은 피평가 워크트리의 checks/에 기대지 않고 여기서 계산한다(checks/common.py와 같은 정규식).
CHARTS_BLOCK = re.compile(r"/\* BEGIN report-charts[^*]*\*/.*?/\* END report-charts \*/", re.S)
PAGE_ID = re.compile(r'<section class="(page[^"]*)" id="(p\d+)"[^>]*>(.*?)</section>', re.S)
MERMAID = re.compile(r'<pre\b[^>]*\bclass="[^"]*\bmermaid\b[^"]*"[^>]*>(.*?)</pre>', re.S)


def doc_scripts(html):
    """관리 블록(report-charts) 밖 <script>의 내용."""
    return "\n".join(re.findall(r"<script\b[^>]*>(.*?)</script>", CHARTS_BLOCK.sub("", html), re.S))


ORDER = ["dwell", "step-anim", "step1", "note-near", "active-visible", "svg-font-390", "figure-overflow-390",
         "contrast-text", "contrast-graphic", "cvd", "html-font-390", "overflow-390", "table-col-390",
         "page-number", "hash-nav", "rules-motion", "rules-layout", "rules-all"]
TARGET = {i: "motion" for i in ORDER[:7]}
TARGET.update({i: "layout" for i in ORDER[7:15]})
TARGET.update({"rules-motion": "motion", "rules-layout": "layout", "rules-all": "content"})
THEMED = {"contrast-text", "contrast-graphic", "cvd"}
RULE_IDS = {"rules-motion", "rules-layout", "rules-all"}
NEAR = 48


def item(id_, target, status, value=None, detail=None):
    return {"id": id_, "target": target, "status": status, "value": value, "detail": detail}


def chars(text):
    """글자 수: 공백을 빼고, 숫자 묶음(1,234.5 같은)은 1자로 센다."""
    return len(re.sub(r"\s", "", re.sub(r"\d[\d,.]*", "#", text)))


def _state_at(samples, t):
    best = samples[0][1]
    for ts, state in samples:
        if ts <= t + 1e-9:
            best = state
        else:
            break
    return best


def dwell_steps(samples, ends):
    """samples: 시간순 [(t, {요소 키: 보이는 글})], ends: 단계 끝 라벨 시각 [e0, e1, …].
    단계 i는 e(i-1)(첫 단계는 0)에서 e(i)까지다. 글 완료 시점은 단계 안에서 보이는 글이 마지막으로 바뀐 표본 시각이다."""
    out = []
    for i, end in enumerate(ends):
        start = 0.0 if i == 0 else ends[i - 1]
        inside = [s for s in samples if start - 1e-9 <= s[0] <= end + 1e-9]
        done = start
        for (_, a), (tb, b) in zip(inside, inside[1:]):
            if a != b:
                done = tb
        before, after = _state_at(samples, start), _state_at(samples, end)
        n = sum(chars(text) for key, text in after.items() if before.get(key) != text)
        lo, dwell = 1 + n / 8, end - done
        out.append({"step": i + 1, "end": round(end, 3), "done": round(done, 3), "dwell": round(dwell, 3), "n": n,
                    "lo": round(lo, 3), "hi": round(lo + 3, 3), "ok": lo - 1e-6 <= dwell <= lo + 3 + 1e-6})
    return out


def parse_color(s):
    """'rgb(…)'·'rgba(…)'·'#rgb'·'#rrggbb'·'transparent'를 (r, g, b, a)로 바꾼다. 읽을 수 없으면 None."""
    if s is None:
        return None
    s = s.strip().lower()
    if s in ("transparent", "none", ""):
        return (0.0, 0.0, 0.0, 0.0)
    h = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", s)
    if h:
        v = h.group(1)
        if len(v) == 3:
            v = "".join(c * 2 for c in v)
        return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16), 1.0)
    r = re.fullmatch(r"rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)(?:[\s,/]+([\d.]+%?))?\s*\)", s)
    if r:
        a = r.group(4)
        alpha = 1.0 if a is None else (float(a[:-1]) / 100 if a.endswith("%") else float(a))
        return (float(r.group(1)), float(r.group(2)), float(r.group(3)), alpha)
    return None


def _lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _unlin(c):
    c = min(1.0, max(0.0, c))
    v = 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return v * 255


def luminance(c):
    r, g, b = (_lin(v) for v in c[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def blend(fg, bg):
    a = fg[3]
    return tuple(fg[i] * a + bg[i] * (1 - a) for i in range(3)) + (1.0,)


def contrast(c1, c2):
    hi, lo = sorted((luminance(c1), luminance(c2)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def text_threshold(px, weight):
    """WCAG 1.4.3: 24px 이상이거나 굵은(700 이상) 18.66px 이상 글자는 3:1, 나머지는 4.5:1."""
    return 3.0 if px >= 24 - 1e-9 or (weight >= 700 and px >= 18.66 - 1e-9) else 4.5


DEUTAN = ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881))


def deutan(rgb):
    """제2색각(Machado 2009, 심각도 1.0) 모의 변환. 선형 RGB에서 행렬을 곱한다."""
    lin = [_lin(v) for v in rgb[:3]]
    return tuple(_unlin(sum(k * c for k, c in zip(row, lin))) for row in DEUTAN)


def lab(rgb):
    r, g, b = (_lin(v) for v in rgb[:3])
    x = (0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / 0.95047
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = (0.0193339 * r + 0.1191920 * g + 0.9503041 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116

    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def delta_e76(a, b):
    return math.dist(lab(a), lab(b))


def cvd_pairs(colors):
    names = list(colors)
    return [(a, b, round(delta_e76(deutan(colors[a]), deutan(colors[b])), 2))
            for i, a in enumerate(names) for b in names[i + 1:]]


def gap(a, b):
    """두 경계 상자 (left, top, right, bottom) 사이 거리. 겹치거나 닿으면 0."""
    dx = max(0.0, a[0] - b[2], b[0] - a[2])
    dy = max(0.0, a[1] - b[3], b[1] - a[3])
    return math.hypot(dx, dy)


def overlap_area(a, b):
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


def points_inside(points, box):
    return sum(1 for x, y in points if box[0] <= x <= box[2] and box[1] <= y <= box[3])


def inside_view(box, w, h):
    return box[0] >= -0.5 and box[1] >= -0.5 and box[2] <= w + 0.5 and box[3] <= h + 0.5


def escapes(box, width):
    return box[0] < -0.5 or box[2] > width + 0.5


def note_steps(steps, view):
    """단계 끝마다 현재 노드와 가장 가까운 보이는 설명 상자로 거리·겹침·화면 안을 판정한다."""
    out = []
    for s in steps:
        a, count = s.get("active"), s.get("active_count", 1 if s.get("active") else 0)
        if count != 1 or not a:
            why = "현재 노드 없음" if count == 0 else "현재 노드가 둘 이상"
            out.append({"step": s["step"], "near": False, "visible": False, "why": why})
            continue
        if not s["notes"]:
            out.append({"step": s["step"], "near": False, "visible": False, "why": "보이는 설명 상자 없음"})
            continue
        note = min(s["notes"], key=lambda b: gap(a, b))
        d = gap(a, note)
        hits = [b for b in s["boxes"] if overlap_area(b, note) > 1]
        pts = points_inside(s["points"], note)
        out.append({"step": s["step"], "distance": round(d, 1), "overlaps": len(hits), "edge_points": pts,
                    "near": d <= NEAR and not hits and not pts,
                    "visible": inside_view(a, *view) and inside_view(note, *view)})
    return out


PAGE_NO = re.compile(r"^\s*(\d+)\s*/\s*(\d+)\s*$")


def page_number_count(texts, total):
    """'n / m' 모양이고 m이 문서의 페이지 수인 글의 개수."""
    return sum(1 for t in texts if (p := PAGE_NO.match(t)) and int(p.group(2)) == total)


def source_facts(html):
    """원문만으로 정하는 사실: RC.demo 호출 수(관리 블록 밖), SVG 유무, 페이지 id, 페이지형 여부."""
    js = doc_scripts(html)
    markup = re.sub(r"<script\b.*?</script>", "", html, flags=re.S | re.I)
    pages = [pid for _, pid, _ in PAGE_ID.findall(html)]
    has_svg = bool(re.search(r"<svg\b", markup, re.I) or "".join(MERMAID.findall(html)).strip()
                   or re.search(r"\bRC\.chart\s*\(", js))
    return {"demo_calls": len(re.findall(r"\bRC\.demo\s*\(", js)), "has_svg": has_svg,
            "pages": pages, "paged": bool(pages) and 'class="pager"' in html}
```

- [ ] **Step 4: 통과 확인**

Run: `python -B -m unittest tests.test_eval_measure -v`
Expected: 모든 시험 PASS. 실패하면 함수를 고치고 시험의 기대값은 바꾸지 않는다(기대값은 손으로 계산한 값이다).

- [ ] **Step 5: 커밋**

```bash
git add eval/measure.py tests/test_eval_measure.py
git commit -m "C0: 체류 시간·대비·색각·거리 등 브라우저 없는 측정 함수를 추가한다"
```

---

### Task 3: 문서 열기와 원시값 수집 함수

**Files:**
- Create: `eval/harness.py`, `eval/probe.js`
- Test: `tests/test_eval_harness.py`

**Interfaces:**
- Consumes: 없음
- Produces:
  - `harness.EnvFail(Exception)`, `harness.VIEW = {1280: {...}, 390: {...}}`, `harness.TIMEOUT = 15.0`
  - `harness.Server(folder)`: 컨텍스트 관리자. `.port`, `.url(name, mode=None, page=None) -> str`
  - `harness.Session(folder)`: 컨텍스트 관리자. `.open(name, demo_calls, width=1280, theme="light", mode=None, page=None, verify=True) -> (page, demo_ok)`. 새 탭으로 열고 측정 시작 조건을 기다린 뒤 `probe.js`를 넣는다. 조건이 갖춰지지 않거나 요청한 페이지가 보이지 않으면 `EnvFail`. `.notes`는 `{"load_errors": set, "render_fail": set}`이고 세션 동안 모인다.
  - `probe.js`가 정의하는 `window.__c0`: `visible(e)`, `own(e)`, `textEls(root)`, `box(e)`, `fonts(root, inSvg)`, `layout()`, `demos()`, `ends(tl)`, `eachEnd(fig, fn)`, `svgFontSteps(id)`, `contrast()`, `graphics(root)`, `graphicSteps(id)`, `pageNumbers()`, `shown(id)`, `tokens(names)`, `figText(fig)`, `dwellSamples(id)`, `step1(id, mode)`, `stepAnim(id)`, `toStep(id, i)`, `noteStep(fig, i)`, `noteSteps(id)`

- [ ] **Step 1: 실패하는 시험 작성**

`tests/test_eval_harness.py`:

```python
"""C0 문서 열기 시험(합성 HTML, 외부 네트워크 없음). 실행: python -B -m unittest discover -s tests"""
import socket
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
import harness  # noqa: E402

ENGINE = (ROOT / "report-charts.js").read_text(encoding="utf-8")


def write(folder, name, body, script=""):
    p = Path(folder, name)
    p.write_text(f'<!doctype html><html lang="ko"><head><meta charset="utf-8"></head><body>{body}'
                 f"<script>{script}</script></body></html>", encoding="utf-8")
    return p


class Open(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def test_korean_file_name_opens_and_probe_loaded(self):
        write(self.tmp.name, "시험 문서.html", "<p>글</p>")
        with harness.Session(self.tmp.name) as s:
            page, ok = s.open("시험 문서.html", 0)
            self.assertTrue(ok)
            self.assertEqual(page.evaluate("() => typeof window.__c0.layout"), "function")
            page.close()

    def test_blocked_cdn_is_env_fail(self):
        write(self.tmp.name, "a.html", '<script src="http://127.0.0.1:9/gsap.min.js"></script><p>글</p>')
        with harness.Session(self.tmp.name) as s:
            with self.assertRaises(harness.EnvFail):
                s.open("a.html", 0)

    def test_static_fallback_is_not_demo_ok(self):
        body = '<figure id="d"><svg viewBox="0 0 10 10"></svg><p class="src">자료</p></figure>'
        write(self.tmp.name, "b.html", body, ENGINE + "\nRC.demo(document.getElementById('d'), "
              "[{name: '가', text: '나', play: function () {}}]);")
        with harness.Session(self.tmp.name) as s:
            page, ok = s.open("b.html", 1)
            self.assertFalse(ok)
            page.close()

    def test_server_closed_after_exception(self):
        try:
            with harness.Server(self.tmp.name) as srv:
                port = srv.port
                raise RuntimeError("측정 중 예외")
        except RuntimeError:
            pass
        with self.assertRaises(OSError):
            socket.create_connection(("127.0.0.1", port), timeout=1).close()

    def test_same_origin_404_is_recorded_not_env_fail(self):
        write(self.tmp.name, "c.html", '<img src="없는그림.png"><p>글</p>')
        with harness.Session(self.tmp.name) as s:
            page, ok = s.open("c.html", 0)
            page.close()
            self.assertEqual(len(s.notes["load_errors"]), 1)

    def test_requested_page_must_be_shown(self):
        write(self.tmp.name, "d.html", '<section class="page" id="p1">일</section>'
              '<section class="page" id="p2" style="display:none">이</section>')
        with harness.Session(self.tmp.name) as s:
            with self.assertRaises(harness.EnvFail):
                s.open("d.html", 0, page="p2")
            page, _ = s.open("d.html", 0, page="p2", verify=False)
            page.close()

    def test_url_has_mode_and_page(self):
        with harness.Server(self.tmp.name) as srv:
            self.assertTrue(srv.url("가 나.html", "step", "p2").endswith("/%EA%B0%80%20%EB%82%98.html?rc-mode=step#p2"))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 실패 확인**

Run: `python -B -m unittest tests.test_eval_harness -v`
Expected: `ModuleNotFoundError: No module named 'harness'`.

- [ ] **Step 3: `eval/harness.py` 구현**

```python
"""문서 열기: 로컬 서버, 헤드리스 Chromium 세션, 측정 시작 조건, 환경 실패."""
import functools
import http.server
import threading
import time
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

PROBE = (Path(__file__).resolve().parent / "probe.js").read_text(encoding="utf-8")
TIMEOUT = 15.0
VIEW = {1280: {"width": 1280, "height": 800}, 390: {"width": 390, "height": 844}}
WATCHED = {"document", "script", "stylesheet", "font", "fetch", "xhr", "image"}
BASE_READY = """() => document.fonts.status === 'loaded'
  && [...document.querySelectorAll('pre.mermaid')].every(p => p.querySelector('svg') || p.classList.contains('viz-fail'))"""
RENDER_FAIL = """() => [...document.querySelectorAll('.viz-fail')].map(e => (e.id || e.tagName.toLowerCase()) + ': ' + e.textContent.trim().slice(0, 40))"""
DEMO_READY = """n => document.querySelectorAll('figure[data-rc-ready="1"]').length >= n
  || !!document.querySelector('.demo-static')"""
DEMO_STATE = """() => ({ready: document.querySelectorAll('figure[data-rc-ready="1"]').length,
  fallback: document.querySelectorAll('.demo-static').length})"""


class EnvFail(Exception):
    """측정 시작 조건이 갖춰지지 않았다(외부 요청 실패, 15초 초과)."""


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class Server:
    """폴더 하나를 127.0.0.1의 빈 포트로 띄운다. with 블록을 나가면 반드시 끈다."""

    def __init__(self, folder):
        handler = functools.partial(_Quiet, directory=str(folder))
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.port = self.httpd.server_address[1]

    def __enter__(self):
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()

    def url(self, name, mode=None, page=None):
        q = f"?rc-mode={mode}" if mode else ""
        h = f"#{page}" if page else ""
        return f"http://127.0.0.1:{self.port}/{quote(name)}{q}{h}"


def _ignored(url):
    return url.endswith("favicon.ico")


def open_doc(context, url, demo_calls, page_id=None, notes=None):
    """새 탭으로 문서를 열고 측정 시작 조건을 기다린다. (page, demo_ok)를 돌려준다.
    글꼴·도식·네트워크가 15초 안에 준비되지 않거나 다른 출처(CDN) 요청이 실패하면 EnvFail.
    같은 출처(로컬 서버)의 요청 실패와 렌더 실패(.viz-fail)는 notes['load_errors']·notes['render_fail']에 모은다.
    page_id를 주면 그 페이지가 보이는지 확인하고, 보이지 않으면 EnvFail.
    RC.demo 호출이 있는데 data-rc-ready가 오지 않거나 정적 목록으로 물러나면 demo_ok가 False다."""
    page = context.new_page()
    origin = url.split("/", 3)[:3]
    local = "/".join(origin)
    external, same = [], []

    def failed(u, text):
        if _ignored(u):
            return
        (same if u.startswith(local) else external).append(text)

    page.on("requestfailed", lambda r: failed(r.url, r.url) if r.resource_type in WATCHED else None)
    page.on("response", lambda r: failed(r.url, f"{r.status} {r.url}")
            if r.status >= 400 and r.request.resource_type in WATCHED else None)
    deadline = time.monotonic() + TIMEOUT

    def left():
        return max(1.0, (deadline - time.monotonic()) * 1000)

    try:
        page.goto(url, wait_until="networkidle", timeout=TIMEOUT * 1000)
        if external:
            raise EnvFail("외부 요청 실패: " + ", ".join(external[:3]))
        page.wait_for_function(BASE_READY, timeout=left())
    except PWTimeout:
        page.close()
        raise EnvFail("15초 안에 글꼴·도식·네트워크가 준비되지 않았다") from None
    except EnvFail:
        page.close()
        raise
    page.add_script_tag(content=PROBE)
    if page_id and not page.evaluate("id => __c0.shown(id)", page_id):
        page.close()
        raise EnvFail(f"주소 끝 #{page_id}로 열었는데 그 페이지가 보이지 않는다")
    if notes is not None:
        notes.setdefault("load_errors", set()).update(same)
        notes.setdefault("render_fail", set()).update(page.evaluate(RENDER_FAIL))
    demo_ok = True
    if demo_calls:
        try:
            page.wait_for_function(DEMO_READY, arg=demo_calls, timeout=left())
        except PWTimeout:
            pass
        st = page.evaluate(DEMO_STATE)
        demo_ok = st["ready"] >= demo_calls and not st["fallback"]
    return page, demo_ok


class Session:
    """브라우저 하나와 (폭, 테마)별 컨텍스트, 문서 폴더를 띄운 서버. with 블록을 나가면 모두 닫는다."""

    def __init__(self, folder):
        self.server = Server(folder)
        self.notes = {"load_errors": set(), "render_fail": set()}

    def __enter__(self):
        self.server.__enter__()
        self.pw = self.browser = None
        try:
            self.pw = sync_playwright().start()
            self.browser = self.pw.chromium.launch()
        except Exception:
            self.__exit__(None, None, None)
            raise
        self.contexts = {}
        return self

    def __exit__(self, *exc):
        try:
            if self.browser:
                self.browser.close()
        finally:
            try:
                if self.pw:
                    self.pw.stop()
            finally:
                self.server.__exit__(*exc)

    def context(self, width, theme):
        key = (width, theme)
        if key not in self.contexts:
            self.contexts[key] = self.browser.new_context(viewport=VIEW[width], color_scheme=theme)
        return self.contexts[key]

    def open(self, name, demo_calls, width=1280, theme="light", mode=None, page=None, verify=True):
        """verify가 True이고 page를 주면 열린 문서에서 그 페이지가 보이는지 확인한다(hash-nav만 False)."""
        return open_doc(self.context(width, theme), self.server.url(name, mode, page), demo_calls,
                        page if verify else None, self.notes)
```

- [ ] **Step 4: `eval/probe.js` 구현**

```js
/* C0 측정기의 화면 수집 함수. eval/harness.py가 측정 시작 조건이 갖춰진 뒤 문서에 넣는다.
   원시값만 모으고, 통과·실패 판정은 eval/measure.py·motion.py·layout.py가 한다. */
(function () {
  var C = window.__c0 = {};
  var SKIP = /^(SCRIPT|STYLE|TITLE|NOSCRIPT)$/i;
  var SHAPE = /^(rect|path|polygon|circle|ellipse)$/i;
  var GEOM = 'text, rect, polygon, circle, ellipse, path, line, polyline, foreignObject';
  function cs(e) { return getComputedStyle(e); }
  function opac(e) { var o = 1; for (var n = e; n; n = n.parentElement) o *= +cs(n).opacity; return o; }
  function clipped(e) { for (var n = e; n; n = n.parentElement) { var c = cs(n).clipPath; if (c && c !== 'none') return true; } return false; }
  function rendered(e) {
    return e.checkVisibility ? e.checkVisibility({ visibilityProperty: true }) : e.getClientRects().length > 0;
  }
  function alpha(c) {
    var m = /rgba?\(([^)]+)\)/.exec(c || '');
    if (!m) return c === 'transparent' || c === 'none' ? 0 : 1;
    var p = m[1].split(/[\s,\/]+/).filter(Boolean);
    return p.length > 3 ? parseFloat(p[3]) : 1;
  }
  function own(e) {
    var s = '';
    for (var i = 0; i < e.childNodes.length; i++) if (e.childNodes[i].nodeType === 3) s += e.childNodes[i].nodeValue;
    return s.replace(/\s+/g, ' ').trim();
  }
  function box(e) { var r = e.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; }
  function area(e) { var r = e.getBoundingClientRect(); return r.width * r.height; }
  function ink(e) { var c = cs(e); return e instanceof SVGElement ? c.fill : c.color; }
  function scale(e) { // 화면 변환 배율: SVG 안이면 화면 변환 행렬, 밖이면 경계 상자 대비 비율
    var s = e instanceof SVGElement ? e : e.closest('foreignObject');
    if (s && s.getScreenCTM) { var m = s.getScreenCTM(); if (m) return Math.sqrt(Math.abs(m.a * m.d - m.b * m.c)); }
    var w = e.offsetWidth;
    return w ? e.getBoundingClientRect().width / w : 1;
  }
  function wait(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  // 보이는 요소: 그려지고, 조상 불투명도 곱이 0.05 초과, 면적 1px² 이상, clip-path 없음, 글자면 글자색 알파가 0이 아님
  C.visible = function (e) {
    return rendered(e) && opac(e) > 0.05 && area(e) >= 1 && !clipped(e) && (!own(e) || alpha(ink(e)) > 0);
  };
  C.own = own;
  C.box = box;
  C.textEls = function (root) {
    return [].filter.call(root.querySelectorAll('*'), function (e) {
      return !SKIP.test(e.tagName) && !e.closest('defs') && own(e);
    });
  };
  C.fonts = function (root, inSvg) { // inSvg: true면 SVG 안 글자(그려지는 모든 글자), false면 SVG 밖의 보이는 글자
    return C.textEls(root).filter(function (e) {
      return !!e.closest('svg') === inSvg && (inSvg ? rendered(e) : C.visible(e));
    }).map(function (e) { return { px: +(parseFloat(cs(e).fontSize) * scale(e)).toFixed(2), text: own(e).slice(0, 24) }; });
  };
  function scrollBox(e) { // overflow-x가 auto·scroll인 조상만 스크롤 상자로 본다
    for (var n = e.parentElement; n && n !== document.body && n !== document.documentElement; n = n.parentElement)
      if (/^(auto|scroll)$/.test(cs(n).overflowX)) return n;
    return null;
  }
  C.layout = function () {
    var figs = [];
    [].forEach.call(document.querySelectorAll('figure, figure svg, pre.mermaid svg'), function (e) {
      if (!rendered(e) || (e.tagName.toLowerCase() === 'svg' && e.parentElement.closest('svg'))) return;
      var sb = scrollBox(e);
      figs.push({ name: e.id || e.tagName.toLowerCase(), box: box(sb || e), scroll: !!sb });
    });
    var cells = [].filter.call(document.querySelectorAll('td, th'), C.visible).map(function (e) {
      return { w: +e.getBoundingClientRect().width.toFixed(1), text: e.textContent.trim().slice(0, 16) };
    });
    var rootClip = [document.documentElement, document.body].some(function (e) { return /^(hidden|clip)$/.test(cs(e).overflowX); });
    return { width: document.documentElement.clientWidth, scrollWidth: document.documentElement.scrollWidth, rootClip: rootClip,
      svgFonts: C.fonts(document.body, true), htmlFonts: C.fonts(document.body, false), figures: figs, cells: cells };
  };
  C.demos = function () {
    return [].map.call(document.querySelectorAll('figure[data-rc-ready="1"]'), function (f) {
      var p = f.closest('section.page');
      return { id: f.id, page: p ? p.id : null, mode: f.dataset.rcMode || 'auto' };
    });
  };
  C.ends = function (tl) { var out = []; for (var i = 0; ('e' + i) in tl.labels; i++) out.push(tl.labels['e' + i]); return out; };
  C.eachEnd = function (fig, fn) { // 타임라인을 단계 끝으로 직접 옮기며 fn을 부른다(화면 상태만 보는 측정에 쓴다)
    var tl = fig._rcTl;
    return C.ends(tl).map(function (e, i) { tl.seek('e' + i, false); return fn(i); });
  };
  function noteFonts(f) { // SVG 밖 HTML 설명 상자의 글자
    return [].concat.apply([], [].map.call(f.querySelectorAll('.rc-note'), function (n) {
      return n.closest('svg') || !C.visible(n) ? [] : C.fonts(n, false);
    }));
  }
  C.svgFontSteps = function (id) {
    var f = document.getElementById(id);
    return [].concat.apply([], C.eachEnd(f, function () { return C.fonts(f, true).concat(noteFonts(f)); }));
  };
  function bgOf(e) { // 조상으로 올라가며 처음 만나는 불투명 바탕색. 반투명이나 그림 바탕이면 null
    for (var n = e; n; n = n.parentElement) {
      var s = cs(n);
      if (s.backgroundImage && s.backgroundImage !== 'none') return null;
      var a = alpha(s.backgroundColor);
      if (a >= 0.999) return s.backgroundColor;
      if (a > 0.001) return null;
    }
    return 'rgb(255, 255, 255)';
  }
  function under(e, x, y) { // 글자 중심점 아래에 그려진 도형의 채움색. 없으면 undefined, 반투명이면 null
    if (x < 0 || y < 0 || x >= innerWidth || y >= innerHeight) return undefined;
    var st = document.elementsFromPoint(x, y), i = st.indexOf(e);
    for (var k = i + 1; k < st.length; k++) {
      var s = st[k];
      if (s.contains(e)) { if (s.tagName.toLowerCase() === 'svg') break; continue; }
      if (!(s instanceof SVGElement)) break;
      if (!SHAPE.test(s.tagName)) continue;
      var c = cs(s);
      if (c.fill === 'none' || alpha(c.fill) === 0) continue;
      return opac(s) * parseFloat(c.fillOpacity) >= 0.999 && alpha(c.fill) >= 0.999 ? c.fill : null;
    }
    return undefined;
  }
  function weight(c) { var w = parseInt(c.fontWeight, 10); return isNaN(w) ? (c.fontWeight === 'bold' ? 700 : 400) : w; }
  function textPair(e) { // op는 요소 불투명도다. 판정할 때 글자색 알파에 곱해 바탕과 합성한다
    var c = cs(e), inSvg = !!e.closest('svg'), r = e.getBoundingClientRect();
    var rec = { text: own(e).slice(0, 24), px: +(parseFloat(c.fontSize) * scale(e)).toFixed(2), weight: weight(c),
      svg: inSvg, fg: ink(e), op: +opac(e).toFixed(3), bg: null, why: null };
    if (inSvg) {
      var u = under(e, (r.left + r.right) / 2, (r.top + r.bottom) / 2);
      if (u === null) { rec.why = '반투명 도형 바탕'; return rec; }
      if (u) { rec.bg = u; return rec; }
    }
    rec.bg = bgOf(inSvg ? e.closest('svg') : e);
    if (!rec.bg) rec.why = '반투명이나 그림 바탕';
    return rec;
  }
  C.graphics = function (root) {
    var out = [];
    [].forEach.call(root.querySelectorAll('.fill'), function (e) {
      if (C.visible(e)) out.push({ kind: 'fill', name: e.parentElement.textContent.trim().slice(0, 16),
        fg: cs(e).backgroundColor, bg: bgOf(e.parentElement) });
    });
    if (window.echarts) [].forEach.call(root.querySelectorAll('[_echarts_instance_]'), function (b) {
      var inst = echarts.getInstanceByDom(b);
      if (!inst || !C.visible(b)) return;
      var bg = bgOf(b);
      try { // getModel은 ECharts 내부 API다. 읽지 못하면 측정 불가로 남긴다
        inst.getModel().getSeries().forEach(function (s) {
          var d = s.getData(), line = s.subType === 'line';
          var pick = function (st) { return st ? (line ? st.stroke : st.fill) : null; };
          if (s.subType === 'pie') {
            for (var i = 0; i < d.count(); i++) out.push({ kind: 'series', name: s.name + ':' + d.getName(i), fg: pick(d.getItemVisual(i, 'style')), bg: bg });
          } else out.push({ kind: 'series', name: String(s.name), fg: pick(d.getVisual('style')), bg: bg });
        });
      } catch (x) { out.push({ kind: 'series', name: 'echarts', fg: null, bg: bg, why: 'ECharts 계열 색을 읽지 못했다' }); }
    });
    [].forEach.call(root.querySelectorAll('svg g.node, svg [data-rc-active]'), function (n) {
      var shape = n.tagName.toLowerCase() === 'g' ? n.querySelector('rect, polygon, path, circle, ellipse') : n;
      if (!shape || !C.visible(shape)) return;
      var c = cs(shape);
      if (c.stroke === 'none' || alpha(c.stroke) === 0) return;
      out.push({ kind: 'node', name: (n.id || '').slice(-24), fg: c.stroke, bg: bgOf(shape.closest('svg')) });
    });
    return out;
  };
  C.contrast = function () { // 바탕 도형을 찾는 동안 pointer-events:none 요소도 적중 시험에 들게 한다
    var pe = document.createElement('style');
    pe.textContent = '*{pointer-events:auto !important}';
    document.head.appendChild(pe);
    var H = innerHeight, els = C.textEls(document.body).filter(C.visible), done = new Set(), text = [];
    for (var y = 0; y < document.documentElement.scrollHeight; y += H) {
      scrollTo(0, y);
      els.forEach(function (e) {
        if (done.has(e)) return;
        var r = e.getBoundingClientRect(), cy = (r.top + r.bottom) / 2;
        if (r.width === 0 || cy < 0 || cy >= H) return;
        done.add(e);
        text.push(textPair(e));
      });
    }
    els.forEach(function (e) { if (!done.has(e)) text.push(textPair(e)); });
    scrollTo(0, 0);
    pe.remove();
    return { text: text, graphic: C.graphics(document) };
  };
  C.graphicSteps = function (id) {
    var f = document.getElementById(id);
    return [].concat.apply([], C.eachEnd(f, function () { return C.graphics(f); }));
  };
  C.pageNumbers = function () {
    return C.textEls(document.body).filter(function (e) { return C.visible(e) && !e.closest('figure, table'); })
      .map(own).filter(function (t) { return /^\d+\s*\/\s*\d+$/.test(t); });
  };
  C.shown = function (id) { var e = document.getElementById(id); return !!e && rendered(e) && e.getBoundingClientRect().height > 0; };
  C.tokens = function (names) {
    var s = cs(document.documentElement), o = {};
    names.forEach(function (n) { o[n] = s.getPropertyValue('--' + n).trim(); });
    return o;
  };
  C.figText = function (fig) { // figure 안 보이는 글 요소 {키: 글}. 조작 줄과 단계 목록은 뺀다
    var m = {};
    C.textEls(fig).forEach(function (e) {
      if (e.closest('.demo-ctl, .demo-steps') || !C.visible(e)) return;
      var k = e.getAttribute('data-c0k');
      if (!k) { C.k = (C.k || 0) + 1; k = 'k' + C.k; e.setAttribute('data-c0k', k); }
      m[k] = own(e);
    });
    return m;
  };
  C.dwellSamples = function (id) { // '처음부터'를 누른 뒤 타임라인을 0부터 끝까지 0.05초 간격(단계 끝 라벨 포함)으로 옮기며 글을 기록한다
    var f = document.getElementById(id), tl = f._rcTl, b = f.querySelectorAll('.demo-ctl button');
    if (b[3]) b[3].click();
    var ends = C.ends(tl), D = tl.duration(), ts = [0];
    for (var t = 0.05; t < D + 1e-9; t += 0.05) ts.push(Math.round(t * 1000) / 1000);
    ts = ts.concat(ends).sort(function (a, c) { return a - c; })
      .filter(function (v, i, a) { return i === 0 || v - a[i - 1] > 1e-6; });
    var scale = typeof tl.timeScale === 'function' ? tl.timeScale() : 1;
    return { ends: ends, timeScale: scale, samples: ts.map(function (t) { tl.seek(t, false); return [t, C.figText(f)]; }) };
  };
  C.step1 = function (id, mode) { // 처음 연 상태의 시간과, 재생(자동)·다음(넘김)을 누른 뒤 e0에 닿기까지의 벽시계 시간
    var f = document.getElementById(id), tl = f._rcTl, b = f.querySelectorAll('.demo-ctl button'), t0 = tl.time(), e0 = tl.labels.e0;
    return new Promise(function (done) {
      var start = performance.now();
      (mode === 'step' ? b[2] : b[1]).click();
      (function poll() {
        var el = (performance.now() - start) / 1000, hit = tl.time() >= e0 - 1e-6;
        if (hit || el > 6) done({ initial: t0, e0: e0, reached: hit, seconds: +el.toFixed(3) });
        else requestAnimationFrame(poll);
      })();
    });
  };
  function settle(tl, start, cap) { // 타임라인 시간과 창 스크롤이 300ms 동안 멈출 때까지 기다린다. 마지막으로 바뀐 시각(초)을 돌려준다
    return new Promise(function (done) {
      var last = tl.time(), sy = scrollY, lc = start;
      (function poll() {
        var now = performance.now(), t = tl.time();
        if (t !== last || scrollY !== sy) { last = t; sy = scrollY; lc = now; }
        if (now - lc > 300 || now - start > cap) done((lc - start) / 1000); else requestAnimationFrame(poll);
      })();
    });
  }
  C.stepAnim = function (id) { // '다음'을 누를 때마다 연출 길이(벽시계)와 타임라인 변화량, 첫 단계 뒤 3초 동안 멈춰 있는지
    var f = document.getElementById(id), tl = f._rcTl, b = f.querySelectorAll('.demo-ctl button'), n = C.ends(tl).length, lens = [], deltas = [], held = null;
    function one(k) {
      if (k >= n || b[2].disabled) return Promise.resolve();
      var start = performance.now(), t0 = tl.time();
      b[2].click();
      return settle(tl, start, 8000).then(function (s) {
        lens.push(+s.toFixed(3));
        deltas.push(+(tl.time() - t0).toFixed(3));
        if (held !== null) return one(k + 1);
        var t = tl.time();
        return wait(3000).then(function () { held = Math.abs(tl.time() - t) < 1e-6; return one(k + 1); });
      });
    }
    return one(0).then(function () { return { lengths: lens, deltas: deltas, held: held }; });
  };
  C.toStep = function (id, i) { // 엔진 버튼으로 i번째 단계 끝까지 간다. i=0은 '처음부터' 뒤 필요하면 '다음'을 한 번 누른다
    var f = document.getElementById(id), tl = f._rcTl, b = f.querySelectorAll('.demo-ctl button'), e0 = tl.labels.e0;
    var start = performance.now();
    if (i === 0) {
      b[3].click();
      return settle(tl, start, 10000).then(function () {
        if (tl.time() >= e0 - 1e-6) return { time: tl.time() };
        var s2 = performance.now();
        b[2].click();
        return settle(tl, s2, 10000).then(function () { return { time: tl.time() }; });
      });
    }
    b[2].click();
    return settle(tl, start, 10000).then(function () { return { time: tl.time() }; });
  };
  function pointsOf(e) {
    var out = [];
    try {
      var L = e.getTotalLength(), m = e.getScreenCTM(), k = m ? Math.sqrt(Math.abs(m.a * m.d - m.b * m.c)) : 1, step = 2 / (k || 1);
      for (var s = 0; s <= L; s += step) { var p = e.getPointAtLength(s), q = new DOMPoint(p.x, p.y).matrixTransform(m); out.push([q.x, q.y]); }
    } catch (x) { /* 길이를 구할 수 없는 요소는 건너뛴다 */ }
    return out;
  }
  function stickman(e) { var g = e.closest('.rc-icon'); return !!g && !!g.querySelector('image'); }
  C.noteStep = function (f, i) { // 현재 노드(설명 상자·아이콘 밖의 보이는 data-rc-active), 보이는 설명 상자, 설명 상자 근처(4px)의 무대 요소 상자와 간선 점
    var acts = [].filter.call(f.querySelectorAll('[data-rc-active]'), function (e) { return !e.closest('.rc-note, .rc-icon') && C.visible(e); });
    var notes = [].filter.call(f.querySelectorAll('.rc-note'), C.visible).map(box);
    var a = acts.length === 1 ? box(acts[0]) : null, boxes = [], points = [];
    if (a && notes.length) {
      var z = notes.reduce(function (p, n) { return [Math.min(p[0], n[0]), Math.min(p[1], n[1]), Math.max(p[2], n[2]), Math.max(p[3], n[3])]; });
      var nearZ = function (x0, y0, x1, y1) { return x1 >= z[0] - 4 && x0 <= z[2] + 4 && y1 >= z[1] - 4 && y0 <= z[3] + 4; };
      [].forEach.call(f.querySelectorAll('svg'), function (svg) {
        [].forEach.call(svg.querySelectorAll(GEOM), function (e) {
          if (e.closest('.rc-note, defs, marker, clipPath, mask, pattern') || stickman(e) || !C.visible(e)) return;
          var c = cs(e), edge = /^(line|polyline)$/i.test(e.tagName) || (/^path$/i.test(e.tagName) && (c.fill === 'none' || alpha(c.fill) === 0));
          if (edge) pointsOf(e).forEach(function (p) { if (nearZ(p[0], p[1], p[0], p[1])) points.push(p); });
          else { var b = box(e); if (b[2] > b[0] && nearZ(b[0], b[1], b[2], b[3])) boxes.push(b); }
        });
      });
    }
    return { step: i + 1, active: a, active_count: acts.length, notes: notes, boxes: boxes, points: points };
  };
  C.noteSteps = function (id) { // figure 윗변을 창 윗변에 맞춰 한 번 스크롤한 뒤, 엔진 버튼으로 단계를 넘기며 단계 끝마다 측정한다
    var f = document.getElementById(id), n = C.ends(f._rcTl).length, out = [];
    scrollTo(0, f.getBoundingClientRect().top + scrollY);
    function one(i) {
      if (i >= n) return Promise.resolve();
      return C.toStep(id, i).then(function () { out.push(C.noteStep(f, i)); return one(i + 1); });
    }
    return one(0).then(function () { return { view: [innerWidth, innerHeight], steps: out }; });
  };
})();
```

- [ ] **Step 5: 통과 확인**

Run: `python -B -m unittest tests.test_eval_harness -v`
Expected: 모든 시험 PASS. 정적 목록 시험은 gsap이 없는 합성 문서에서 엔진이 `demo-static`을 붙이므로 `ok`가 False다.

- [ ] **Step 6: 커밋**

```bash
git add eval/harness.py eval/probe.js tests/test_eval_harness.py
git commit -m "C0: 문서 열기·측정 시작 조건·환경 실패와 화면 수집 함수를 추가한다"
```

---

### Task 4: layout 항목과 규칙 항목

**Files:**
- Create: `eval/layout.py`, `eval/rules.py`
- Test: `tests/test_eval_gates.py`

**Interfaces:**
- Consumes: `measure.*`, `harness.Session`, `__c0.layout/contrast/graphicSteps/svgFontSteps/pageNumbers/shown/tokens/demos`
- Produces:
  - `layout.light_items(sess, name, facts, wanted, mode, judge_hash=False) -> list[item]`: 390 폭 항목(`svg-font-390`·`figure-overflow-390`·`html-font-390`·`overflow-390`·`table-col-390`), 밝은 테마의 `contrast-text`·`contrast-graphic`·`cvd`, `page-number`, `hash-nav`(`judge_hash`가 False면 `value.recorded_only`가 true)
  - `layout.dark_items(sess, name, facts, wanted, mode) -> list[item]`: 어두운 테마의 `contrast-text`·`contrast-graphic`·`cvd`
  - 판정 함수(순수): `font_item(id, target, fonts)`, `contrast_text_item(records)`, `contrast_graphic_item(records)`, `cvd_item(tokens)`, `overflow_item(layouts)`, `figure_item(layouts)`, `table_item(layouts)`, `page_number_item(per_page, total)`
  - `rules.violations(checks_dir, modules, html_path) -> list[str]`, `rules.rule_items(html_path, wanted, base_checks=None) -> list[item]`

- [ ] **Step 1: 실패하는 시험 작성**

`tests/test_eval_gates.py`(이 Task에서는 아래 클래스만 쓰고, Task 5에서 motion 시험을 추가한다):

```python
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
```

- [ ] **Step 2: 실패 확인**

Run: `python -B -m unittest tests.test_eval_gates -v`
Expected: `ModuleNotFoundError: No module named 'layout'`.

- [ ] **Step 3: `eval/rules.py` 구현**

```python
"""규칙 항목: 현재 워크트리의 checks/와, 주면 기준 커밋의 checks/ 사본으로 각각 실행한다. 둘 다 위반 0건이어야 통과다."""
import json
import os
import subprocess
import sys
from pathlib import Path

from measure import TARGET, item

ROOT = Path(__file__).resolve().parent.parent
MODULES = {"rules-motion": ["anim"], "rules-layout": ["style"], "rules-all": ["style", "anim", "content", "common"]}
RUNNER = r'''
import contextlib, importlib, importlib.util, json, sys
d, mods, path = sys.argv[1], sys.argv[2].split(","), sys.argv[3]
spec = importlib.util.spec_from_file_location("checks", d + "/__init__.py", submodule_search_locations=[d])
pkg = importlib.util.module_from_spec(spec)
sys.modules["checks"] = pkg
spec.loader.exec_module(pkg)
html = open(path, encoding="utf-8").read()
out = []
with contextlib.redirect_stdout(sys.stderr):  # 규칙 함수의 '참고:' 출력이 JSON을 더럽히지 않게 한다
    for m in mods:
        for fn, mode in importlib.import_module("checks." + m).RULES:
            out += fn(html, None) if mode == "old" else fn(html)
print(json.dumps(out, ensure_ascii=False))
'''


def violations(checks_dir, modules, html_path):
    """checks_dir의 규칙 모듈(RULES)을 따로 띄운 파이썬에서 실행해 위반 문장 목록을 돌려준다.
    금지어 검사(common)는 checks_dir의 부모 폴더에 있는 금지어.md를 읽으므로, 그 파일이 없으면 멈춘다."""
    if "common" in modules and not (Path(checks_dir).parent / "금지어.md").exists():
        raise RuntimeError(f"{Path(checks_dir).parent}에 금지어.md가 없어 금지어 검사를 할 수 없다")
    r = subprocess.run([sys.executable, "-B", "-c", RUNNER, str(checks_dir), ",".join(modules), str(html_path)],
                       capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    if r.returncode:
        raise RuntimeError(f"규칙 실행 실패({checks_dir}): {r.stderr.strip()[-500:]}")
    return json.loads(r.stdout)


def rule_items(html_path, wanted, base_checks=None):
    out = []
    for id_, mods in MODULES.items():
        if id_ not in wanted:
            continue
        cand = violations(ROOT / "checks", mods, html_path)
        base = violations(Path(base_checks), mods, html_path) if base_checks else None
        out.append(item(id_, TARGET[id_], "fail" if cand or base else "pass",
                        {"candidate": len(cand), "base": None if base is None else len(base)},
                        (cand + (base or []))[:20] or None))
    return out
```

- [ ] **Step 4: `eval/layout.py` 구현**

```python
"""layout 항목과 390 폭 motion 항목(svg-font-390·figure-overflow-390)의 측정과 판정."""
from measure import TARGET, blend, contrast, cvd_pairs, escapes, item, page_number_count, parse_color, text_threshold

SERIES = ("s1", "s2", "s3", "s4")
W390 = {"svg-font-390", "figure-overflow-390", "html-font-390", "overflow-390", "table-col-390"}


def _uniq(rows, keys):
    seen, out = set(), []
    for r in rows:
        k = tuple(r.get(x) for x in keys)
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def font_item(id_, target, fonts):
    if not fonts:
        return item(id_, target, "pass", {"count": 0, "min_px": None, "small": 0})
    small = [f for f in fonts if f["px"] < 11 - 1e-6]
    return item(id_, target, "fail" if small else "pass",
                {"count": len(fonts), "min_px": min(f["px"] for f in fonts), "small": len(small)},
                _uniq(small, ("text", "px"))[:15] or None)


def _pairs(records, need_of):
    """요소 불투명도(op)는 글자색 알파에 곱해 바탕과 합성한다. 바탕이나 색을 정할 수 없으면 측정 불가로 센다."""
    bad, ratios, unm = [], [], 0
    for r in records:
        fg = parse_color(r.get("fg"))
        bg = parse_color(r["bg"]) if r.get("bg") else None
        if r.get("why") or not fg or not bg or bg[3] < 0.999:
            unm += 1
            continue
        a = fg[3] * r.get("op", 1.0)
        if a < 0.999:
            fg = blend(fg[:3] + (a,), bg)
        ratio, need = contrast(fg, bg), need_of(r)
        ratios.append(ratio)
        if ratio + 1e-9 < need:
            bad.append(dict(r, ratio=round(ratio, 2), need=need))
    return bad, ratios, unm


def contrast_text_item(records):
    bad, ratios, unm = _pairs(records, lambda r: text_threshold(r["px"], r["weight"]))
    return item("contrast-text", "layout", "fail" if bad else "pass",
                {"checked": len(ratios), "unmeasurable": unm, "fails": len(bad),
                 "min_ratio": round(min(ratios), 2) if ratios else None},
                _uniq(bad, ("text", "fg", "bg"))[:15] or None)


def contrast_graphic_item(records):
    bad, ratios, unm = _pairs(records, lambda r: 3.0)
    return item("contrast-graphic", "layout", "fail" if bad else "pass",
                {"checked": len(ratios), "unmeasurable": unm, "fails": len(bad),
                 "min_ratio": round(min(ratios), 2) if ratios else None},
                _uniq(bad, ("kind", "name", "fg", "bg"))[:15] or None)


def cvd_item(tokens):
    colors = {k: parse_color(v) for k, v in tokens.items() if parse_color(v)}
    pairs = cvd_pairs(colors)
    bad = [{"a": a, "b": b, "de": de} for a, b, de in pairs if de < 15]
    return item("cvd", "layout", "fail" if bad or len(colors) < 2 else "pass",
                {"tokens": tokens, "min_de": min((de for _, _, de in pairs), default=None)}, bad or None)


def overflow_item(layouts):
    """문서 스크롤 폭이 창 폭을 넘거나, html·body가 overflow-x hidden·clip으로 넘침을 감추면 실패다."""
    bad = {p: {"scroll_width": v["scrollWidth"], "width": v["width"], "root_clip": v.get("rootClip", False)}
           for p, v in layouts.items() if v["scrollWidth"] > v["width"] or v.get("rootClip")}
    return item("overflow-390", "layout", "fail" if bad else "pass",
                {"max_scroll_width": max((v["scrollWidth"] for v in layouts.values()), default=None)}, bad or None)


def figure_item(layouts):
    bad = [{"page": p, **f} for p, v in layouts.items() for f in v["figures"] if escapes(f["box"], v["width"])]
    return item("figure-overflow-390", "motion", "fail" if bad else "pass",
                {"figures": sum(len(v["figures"]) for v in layouts.values())}, bad[:10] or None)


def table_item(layouts):
    cells = [dict(c, page=p) for p, v in layouts.items() for c in v["cells"]]
    bad = [c for c in cells if c["w"] < 56 - 1e-6]
    return item("table-col-390", "layout", "fail" if bad else "pass",
                {"cells": len(cells), "min_w": min((c["w"] for c in cells), default=None)}, bad[:10] or None)


def page_number_item(per_page, total):
    counts = {p: page_number_count(t, total) for p, t in per_page.items()}
    return item("page-number", "layout", "pass" if all(c == 1 for c in counts.values()) else "fail", counts)


def _na(ids, why):
    return [item(i, TARGET[i], "n/a", detail=why) for i in ids]


def _pages(facts):
    return facts["pages"] or [None]


def _demos_on(page, pid):
    return [d for d in page.evaluate("() => __c0.demos()") if pid is None or d["page"] == pid]


def _measure_390(sess, name, facts, mode):
    lay, svg_steps = {}, []
    for pid in _pages(facts):
        page, demo_ok = sess.open(name, facts["demo_calls"], 390, "light", mode, pid)
        try:
            lay[pid] = page.evaluate("() => __c0.layout()")
            if demo_ok:
                for d in _demos_on(page, pid):
                    svg_steps += page.evaluate("id => __c0.svgFontSteps(id)", d["id"])
        finally:
            page.close()
    return lay, svg_steps


def _theme_pass(sess, name, facts, theme, mode, want_numbers):
    texts, graphics, numbers, tokens = [], [], {}, None
    for pid in _pages(facts):
        page, demo_ok = sess.open(name, facts["demo_calls"], 1280, theme, mode, pid)
        try:
            if tokens is None:
                tokens = page.evaluate("n => __c0.tokens(n)", list(SERIES))
            if want_numbers:
                numbers[pid] = page.evaluate("() => __c0.pageNumbers()")
            r = page.evaluate("() => __c0.contrast()")
            texts += r["text"]
            graphics += r["graphic"]
            if demo_ok:
                for d in _demos_on(page, pid):
                    graphics += page.evaluate("id => __c0.graphicSteps(id)", d["id"])
        finally:
            page.close()
    return texts, graphics, numbers, tokens


def _theme_items(texts, graphics, tokens, wanted):
    out = []
    if "contrast-text" in wanted:
        out.append(contrast_text_item(texts))
    if "contrast-graphic" in wanted:
        out.append(contrast_graphic_item(graphics))
    if "cvd" in wanted:
        out.append(cvd_item(tokens))
    return out


def hash_nav_item(sess, name, facts, mode, judged):
    """judged가 False면 기록만 한다(value.recorded_only). 고정 견본의 페이지 전환 코드는 관리 블록 밖이기 때문이다."""
    page, _ = sess.open(name, facts["demo_calls"], 1280, "light", mode, "p2", verify=False)
    try:
        first = page.evaluate("() => __c0.shown('p2')")
    finally:
        page.close()
    page, _ = sess.open(name, facts["demo_calls"], 1280, "light", mode, "p1", verify=False)
    try:
        page.evaluate("() => { location.hash = '#p2'; }")
        page.wait_for_timeout(500)
        second = page.evaluate("() => __c0.shown('p2')")
    finally:
        page.close()
    return item("hash-nav", "layout", "pass" if first and second else "fail",
                {"open_with_hash": first, "hash_change": second, "recorded_only": not judged})


def light_items(sess, name, facts, wanted, mode, judge_hash=False):
    out = []
    svg_ids = wanted & {"svg-font-390", "figure-overflow-390"}
    if svg_ids and not facts["has_svg"]:
        out += _na(sorted(svg_ids), "원문에 SVG가 없다")
    if (wanted & W390) - (svg_ids if not facts["has_svg"] else set()):
        lay, svg_steps = _measure_390(sess, name, facts, mode)
        if facts["has_svg"] and "svg-font-390" in wanted:
            out.append(font_item("svg-font-390", "motion", [f for v in lay.values() for f in v["svgFonts"]] + svg_steps))
        if facts["has_svg"] and "figure-overflow-390" in wanted:
            out.append(figure_item(lay))
        if "html-font-390" in wanted:
            out.append(font_item("html-font-390", "layout", [f for v in lay.values() for f in v["htmlFonts"]]))
        if "overflow-390" in wanted:
            out.append(overflow_item(lay))
        if "table-col-390" in wanted:
            out.append(table_item(lay))
    paged_ids = wanted & {"page-number", "hash-nav"}
    if paged_ids and not facts["paged"]:
        out += _na(sorted(paged_ids), "페이지형 문서가 아니다")
    want_numbers = facts["paged"] and "page-number" in wanted
    if wanted & {"contrast-text", "contrast-graphic", "cvd"} or want_numbers:
        texts, graphics, numbers, tokens = _theme_pass(sess, name, facts, "light", mode, want_numbers)
        out += _theme_items(texts, graphics, tokens, wanted)
        if want_numbers:
            out.append(page_number_item(numbers, len(facts["pages"])))
    if facts["paged"] and "hash-nav" in wanted:
        out.append(hash_nav_item(sess, name, facts, mode, judge_hash) if len(facts["pages"]) >= 2
                   else item("hash-nav", "layout", "n/a", detail="2페이지가 없다"))
    return out


def dark_items(sess, name, facts, wanted, mode):
    if not wanted & {"contrast-text", "contrast-graphic", "cvd"}:
        return []
    texts, graphics, _, tokens = _theme_pass(sess, name, facts, "dark", mode, False)
    return _theme_items(texts, graphics, tokens, wanted)
```

`light_items`의 390 측정 조건은 'SVG 항목만 원하고 SVG가 없으면 390 측정을 생략한다'는 뜻이다.

- [ ] **Step 5: 통과 확인**

Run: `python -B -m unittest tests.test_eval_gates -v`
Expected: `Pure`·`Browser`·`Rules`의 시험 모두 PASS. `test_svg_text_and_foreign_object_fonts_at_390`에서 viewBox 700을 358px 폭에 그리므로 14px 글자가 약 7.2px로 나온다.

- [ ] **Step 6: 커밋**

```bash
git add eval/layout.py eval/rules.py tests/test_eval_gates.py
git commit -m "C0: layout·규칙 판정 항목을 추가한다"
```

---

### Task 5: motion 항목과 기계 판정 명령

**Files:**
- Create: `eval/motion.py`, `eval/gates.py`
- Modify: `tests/test_eval_gates.py`(클래스 추가)

**Interfaces:**
- Consumes: `measure.dwell_steps`, `measure.note_steps`, `harness.Session`, `harness.EnvFail`, `layout.light_items/dark_items`, `rules.rule_items`, `__c0.demos/step1/dwellSamples/stepAnim/noteSteps`
- Produces:
  - `motion.motion_items(sess, name, facts, wanted, mode) -> list[item]`
  - `motion.judge_step1(r) -> bool`, `motion.judge_step_anim(r) -> (bool, list)`
  - `gates.measure_file(path, mode, only, base_checks, judge_hash=False) -> list[record]`, `gates.exit_code(records) -> int`, `gates.main(argv) -> int`
  - 명령: `python eval/gates.py <html>… [--mode auto|step] [--only motion|layout|content] [--base-checks <폴더>] [--judge-hash-nav] [--out <결과.json>]`. 기록 형태 `{file, mode, theme, env, items:[{id, target, status, value, detail}], load_errors, render_fail}`, `env`가 `env-fail`·`error`인 기록에는 `error`가 붙는다. 종료 코드 0·1·2·3.

- [ ] **Step 1: 실패하는 시험 추가**

`tests/test_eval_gates.py`의 `if __name__` 앞에 추가한다. 가짜 RC는 엔진 대신 계측 지점(`data-rc-ready`, `fig._rcTl`의 `labels`·`seek`·`time`·`duration`, `.demo-ctl button` 넷, `.rc-note`, `data-rc-active`)만 흉내 낸다.

```python
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

    def test_exit_code_rules(self):
        import gates
        ok = {"env": "ok", "items": [{"status": "pass", "value": {}}], "load_errors": [], "render_fail": []}
        hn = dict(ok, items=[{"status": "fail", "value": {"recorded_only": True}}])
        self.assertEqual(gates.exit_code([ok]), 0)
        self.assertEqual(gates.exit_code([hn]), 0)  # 기록만 하는 hash-nav 실패는 빼고 센다
        self.assertEqual(gates.exit_code([dict(ok, render_fail=["pre: 시각화를 불러오지 못했습니다"])]), 1)
        self.assertEqual(gates.exit_code([dict(ok, env="error", items=[]), dict(ok, env="env-fail", items=[])]), 2)
        self.assertEqual(gates.exit_code([dict(ok, env="error", items=[])]), 3)
```

`test_active_offscreen_fails`의 문자열 치환이 읽기 어려우면 구현자는 같은 뜻의 별도 무대 문자열(현재 노드 `n2`가 y=900에 있고 viewBox 높이 1000, svg 높이 1000)을 시험 안에 직접 써도 된다. 기대 결과는 `active-visible` 실패다.

- [ ] **Step 2: 실패 확인**

Run: `python -B -m unittest tests.test_eval_gates -v`
Expected: `Motion`·`Cli` 시험이 `motion`·`gates.py`가 없어 실패한다.

- [ ] **Step 3: `eval/motion.py` 구현**

```python
"""motion 애니메이션 항목: dwell·step-anim·step1·note-near·active-visible."""
from measure import dwell_steps, item, note_steps

ANIM = ("dwell", "step-anim", "step1", "note-near", "active-visible")
NOT_READY = "RC.demo 호출이 있는데 data-rc-ready가 오지 않았다(정적 목록으로 물러났거나 15초 초과)"


def judge_step1(r):
    return r["initial"] <= 0.05 + 1e-9 and r["reached"] and r["seconds"] >= 0.2 - 1e-9


def judge_step_anim(r):
    bad = [x for x in r["lengths"] if not 0.3 - 1e-9 <= x <= 2.6 + 1e-9]
    return not bad and r["held"] is not False, bad


def _combine(id_, rows):
    sts = [s for _, s, _, _ in rows]
    status = ("fail" if "fail" in sts else "unmeasurable" if "unmeasurable" in sts
              else "pass" if "pass" in sts else "n/a")
    detail = {f: d for f, _, _, d in rows if d is not None}
    return item(id_, "motion", status, {f: v for f, _, v, _ in rows}, detail or None)


def _run(sess, name, facts, mode, pid, script, arg):
    page, _ = sess.open(name, facts["demo_calls"], 1280, "light", mode, pid)
    try:
        return page.evaluate(script, arg)
    finally:
        page.close()


def motion_items(sess, name, facts, wanted, mode):
    want = [i for i in ANIM if i in wanted]
    if not want:
        return []
    if not facts["demo_calls"]:
        return [item(i, "motion", "n/a", detail="원문에 RC.demo 호출이 없다") for i in want]
    first = facts["pages"][0] if facts["pages"] else None
    page, ok = sess.open(name, facts["demo_calls"], 1280, "light", mode, first)
    try:
        demos = page.evaluate("() => __c0.demos()") if ok else []
    finally:
        page.close()
    if not ok:
        return [item(i, "motion", "unmeasurable", detail=NOT_READY) for i in want]
    rows = {i: [] for i in want}
    for d in demos:
        fid, pid, fmode = d["id"], d["page"], mode or d["mode"]
        if "step1" in rows:
            r = _run(sess, name, facts, mode, pid, "([id, m]) => __c0.step1(id, m)", [fid, fmode])
            rows["step1"].append((fid, "pass" if judge_step1(r) else "fail", r, None))
        if "dwell" in rows:
            if fmode != "auto":
                rows["dwell"].append((fid, "n/a", None, "단계 넘김 방식"))
            else:
                r = _run(sess, name, facts, mode, pid, "id => __c0.dwellSamples(id)", fid)
                steps = dwell_steps([(t, s) for t, s in r["samples"]], r["ends"])
                bad = [s for s in steps if not s["ok"]]
                status = "fail" if bad or r["timeScale"] != 1 else "pass"  # timeScale이 1이 아니면 타임라인 시간과 실제 재생 시간이 다르다
                rows["dwell"].append((fid, status,
                                      {"steps": len(steps), "fails": len(bad), "time_scale": r["timeScale"],
                                       "min_dwell": min((s["dwell"] for s in steps), default=None),
                                       "fails_after_step1": sum(not s["ok"] for s in steps[1:])}, steps))
        if "step-anim" in rows:
            if fmode != "step":
                rows["step-anim"].append((fid, "n/a", None, "자동 재생 방식"))
            else:
                r = _run(sess, name, facts, mode, pid, "id => __c0.stepAnim(id)", fid)
                good, bad = judge_step_anim(r)
                rows["step-anim"].append((fid, "pass" if good else "fail", r, bad or None))
        if "note-near" in rows or "active-visible" in rows:
            r = _run(sess, name, facts, mode, pid, "id => __c0.noteSteps(id)", fid)
            if not any(s["active_count"] for s in r["steps"]):
                for i in ("note-near", "active-visible"):
                    if i in rows:
                        rows[i].append((fid, "unmeasurable", None, "data-rc-active가 붙은 요소가 없다"))
            else:
                judged = note_steps(r["steps"], r["view"])
                if "note-near" in rows:
                    rows["note-near"].append((fid, "pass" if all(s["near"] for s in judged) else "fail",
                                              {"steps": len(judged), "fails": sum(not s["near"] for s in judged)}, judged))
                if "active-visible" in rows:
                    rows["active-visible"].append((fid, "pass" if all(s["visible"] for s in judged) else "fail",
                                                   {"steps": len(judged), "fails": sum(not s["visible"] for s in judged)}, judged))
    return [_combine(i, rows[i]) for i in want]
```

- [ ] **Step 4: `eval/gates.py` 구현**

```python
"""기계 판정 명령.

사용법: python eval/gates.py <html>… [--mode auto|step] [--only motion|layout|content] [--base-checks <폴더>] [--out <결과.json>]
문서마다 밝은 테마 기록(모든 항목)과 어두운 테마 기록(contrast-text·contrast-graphic·cvd)을 JSON 목록으로 출력한다.
기록 형태: {file, mode, theme, env, items: [{id, target, status, value, detail}], load_errors, render_fail}. status는 pass·fail·unmeasurable·n/a.
env는 ok·env-fail·error다. env-fail과 error 기록에는 error 메시지가 붙는다.
종료 코드: 환경 실패가 하나라도 있으면 2, 측정기 오류가 있으면 3, fail·unmeasurable·같은 출처 요청 실패·렌더 실패가 하나라도 있으면 1, 모두 통과하면 0.
hash-nav는 --judge-hash-nav가 없으면 기록만 하고(value.recorded_only) 종료 코드에서 뺀다. 고정 견본의 페이지 전환 코드는 관리 블록 밖이기 때문이다.
--base-checks는 기준 커밋 checkout의 checks/ 폴더다. spec 「기계 판정」대로 L1의 공식 측정이 쓴다. 그 부모 폴더에 금지어.md가 없으면 멈춘다.
"""
import argparse
import json
import sys
import traceback
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import EnvFail, Session  # noqa: E402
from layout import dark_items, light_items  # noqa: E402
from measure import ORDER, RULE_IDS, TARGET, THEMED, source_facts  # noqa: E402
from motion import motion_items  # noqa: E402
from rules import rule_items  # noqa: E402


def measure_file(path, mode, only, base_checks, judge_hash=False):
    path = Path(path).resolve()
    html = path.read_text(encoding="utf-8")
    facts = source_facts(html)
    wanted = {i for i in ORDER if only is None or TARGET[i] == only}
    records = []

    def record(theme):
        return {"file": str(path), "mode": mode or "default", "theme": theme, "env": "ok", "items": [],
                "load_errors": [], "render_fail": []}

    def guarded(rec, work):
        try:
            rec["items"] = sorted(work(), key=lambda x: ORDER.index(x["id"]))
        except EnvFail as e:
            rec.update(env="env-fail", error=str(e), items=[])
        except Exception as e:  # 측정기 오류는 판정 실패(1)와 섞이지 않게 따로 기록한다
            rec.update(env="error", error=f"{type(e).__name__}: {e}", trace=traceback.format_exc()[-1500:], items=[])

    if not wanted - RULE_IDS:  # 규칙 항목만 원하면 브라우저를 띄우지 않는다
        rec = record("light")
        guarded(rec, lambda: rule_items(path, wanted, base_checks))
        return [rec]
    with Session(path.parent) as sess:
        for theme in ("light", "dark"):
            w = wanted if theme == "light" else wanted & THEMED
            if not w:
                continue
            rec = record(theme)
            if theme == "light":
                guarded(rec, lambda: motion_items(sess, path.name, facts, w, mode)
                        + light_items(sess, path.name, facts, w, mode, judge_hash) + rule_items(path, w, base_checks))
            else:
                guarded(rec, lambda: dark_items(sess, path.name, facts, w, mode))
            rec["load_errors"] = sorted(sess.notes["load_errors"])
            rec["render_fail"] = sorted(sess.notes["render_fail"])
            records.append(rec)
    return records


def exit_code(records):
    if any(r["env"] == "env-fail" for r in records):
        return 2
    if any(r["env"] == "error" for r in records):
        return 3
    failed = any(i["status"] in ("fail", "unmeasurable") and not (i["value"] or {}).get("recorded_only")
                 for r in records for i in r["items"])
    return 1 if failed or any(r["load_errors"] or r["render_fail"] for r in records) else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="고정 견본의 판정 항목을 측정해 JSON으로 출력한다")
    ap.add_argument("html", nargs="+")
    ap.add_argument("--mode", choices=["auto", "step"])
    ap.add_argument("--only", choices=["motion", "layout", "content"])
    ap.add_argument("--base-checks")
    ap.add_argument("--judge-hash-nav", action="store_true", help="hash-nav를 종료 코드에 넣는다(template-paged.html·재생성본)")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    records = []
    for h in a.html:
        records += measure_file(h, a.mode, a.only, a.base_checks, a.judge_hash_nav)
        if a.out:  # 문서마다 써 두어 뒤 문서에서 멈춰도 앞 기록이 남는다
            Path(a.out).write_text(json.dumps(records, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(records, ensure_ascii=False, indent=1))
    return exit_code(records)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: 통과 확인**

Run: `python -B -m unittest tests.test_eval_gates -v`
Expected: 모든 시험 PASS. 실패하면 가짜 RC나 기대값을 느슨하게 바꾸지 말고 원인을 찾는다(superpowers:systematic-debugging).

- [ ] **Step 6: 실제 견본 연기 시험**

Run: `python -B eval/gates.py <스크래치>/rebuilt/04-rules.html --mode auto --only motion --out <스크래치>/smoke.json; echo $?`
Expected: 종료 코드 1, `dwell`·`step1` 실패, `note-near` 측정 불가, `svg-font-390` 실패(최소 글자 약 9.4px).

- [ ] **Step 7: 커밋**

```bash
git add eval/motion.py eval/gates.py tests/test_eval_gates.py
git commit -m "C0: 애니메이션 판정 항목과 기계 판정 명령을 추가한다"
```

---

### Task 6: 장면 명령

**Files:**
- Create: `eval/shoot.py`
- Modify: `tests/test_eval_commands.py`(클래스 추가)

**Interfaces:**
- Consumes: `harness.Session`, `harness.VIEW`, `harness.EnvFail`, `measure.source_facts`, `__c0.demos/ends/toStep`
- Produces: `python eval/shoot.py <html> <출력 폴더> [--mode auto|step]`, 함수 `shoot(path, out, mode=None) -> list[dict]`. 파일: `<페이지>-<폭>.png`, `<figure id>-s<단계>.png`, `<페이지>.txt`(단일 문서는 `doc.txt`), `index.json`(항목 `{file, kind: "page"|"step", page, width, figure?, step?, seconds?}`). 종료 코드 0, 환경 실패 2.

- [ ] **Step 1: 실패하는 시험 추가**

`tests/test_eval_commands.py`에 추가:

```python
class Shoot(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def test_named_files_and_index(self):
        from test_eval_gates import FAKE_RC, GOOD, PAGER, PAGE_JS, STAGE, doc
        body = (PAGER + '<section class="page" id="p1"><p class="pno">1 / 2</p><p>첫 페이지</p></section>'
                f'<section class="page" id="p2"><p class="pno">2 / 2</p>{STAGE}</section>')
        script = PAGE_JS + "window.FAKE = " + json.dumps(GOOD, ensure_ascii=False) + ";" + FAKE_RC + "RC.demo(document.getElementById('d'), []);"
        src = Path(self.tmp.name, "doc.html")
        src.write_text(doc(body, script), encoding="utf-8")
        out = Path(self.tmp.name, "shots")
        r = run(ROOT / "eval/shoot.py", src, out)
        self.assertEqual(r.returncode, 0, r.stderr)
        names = {p.name for p in out.iterdir()}
        for n in ("p1-1280.png", "p1-390.png", "p2-1280.png", "p2-390.png", "p1.txt", "p2.txt",
                  "d-s1.png", "d-s2.png", "index.json"):
            self.assertIn(n, names)
        idx = json.loads((out / "index.json").read_text(encoding="utf-8"))
        steps = [x for x in idx if x["kind"] == "step"]
        self.assertEqual([(x["figure"], x["step"], x["seconds"]) for x in steps], [("d", 1, 3.5), ("d", 2, 3.5)])
        self.assertIn("첫 페이지", (out / "p1.txt").read_text(encoding="utf-8"))
```

`test_eval_gates`를 가져오려면 `tests` 폴더가 `sys.path`에 있어야 한다. unittest discover가 `-s tests`로 실행하면 `tests`가 경로에 들어가 있다.

- [ ] **Step 2: 실패 확인**

Run: `python -B -m unittest discover -s tests -p "test_eval_commands.py" -v`
Expected: `Shoot` 시험이 `eval/shoot.py`가 없어 실패한다.

- [ ] **Step 3: `eval/shoot.py` 구현**

```python
"""검토용 장면 명령.

사용법: python eval/shoot.py <html> <출력 폴더> [--mode auto|step]
페이지형 문서는 페이지마다(전체 높이), 단일 문서는 화면 높이 단위(v1, v2 …)로 1280×800과 390×844 장면을 찍는다.
애니메이션은 figure마다 윗변을 창 윗변에 맞춘 뒤, 엔진의 '처음부터'·'다음' 버튼으로 단계를 넘기며 단계 끝 장면을 1280 폭에서 찍는다.
페이지별 보이는 글(<페이지>.txt, 단일 문서는 doc.txt)과 장면 목록(index.json)을 함께 남긴다. 환경 실패면 종료 코드 2.
"""
import argparse
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import VIEW, EnvFail, Session  # noqa: E402
from measure import source_facts  # noqa: E402

TEXT = "() => document.body.innerText"


def shoot(path, out, mode=None):
    path, out = Path(path).resolve(), Path(out)
    facts = source_facts(path.read_text(encoding="utf-8"))
    out.mkdir(parents=True, exist_ok=True)
    index = []
    with Session(path.parent) as sess:
        for w in (1280, 390):
            for pid in facts["pages"] or [None]:
                page, _ = sess.open(path.name, facts["demo_calls"], w, "light", mode, pid)
                try:
                    if pid:
                        name = f"{pid}-{w}.png"
                        page.screenshot(path=str(out / name), full_page=True)
                        index.append({"file": name, "kind": "page", "page": pid, "width": w})
                        if w == 1280:
                            (out / f"{pid}.txt").write_text(page.evaluate(TEXT), encoding="utf-8")
                    else:
                        h = VIEW[w]["height"]
                        total = page.evaluate("() => document.documentElement.scrollHeight")
                        for k in range(max(1, math.ceil(total / h))):
                            page.evaluate("y => scrollTo(0, y)", k * h)
                            name = f"v{k + 1}-{w}.png"
                            page.screenshot(path=str(out / name))
                            index.append({"file": name, "kind": "page", "page": f"v{k + 1}", "width": w})
                        if w == 1280:
                            (out / "doc.txt").write_text(page.evaluate(TEXT), encoding="utf-8")
                finally:
                    page.close()
        first = facts["pages"][0] if facts["pages"] else None
        demos = []
        if facts["demo_calls"]:
            page, ok = sess.open(path.name, facts["demo_calls"], 1280, "light", mode, first)
            try:
                demos = page.evaluate("() => __c0.demos()") if ok else []
            finally:
                page.close()
        for d in demos:
            page, _ = sess.open(path.name, facts["demo_calls"], 1280, "light", mode, d["page"])
            try:
                ends = page.evaluate("id => __c0.ends(document.getElementById(id)._rcTl)", d["id"])
                page.evaluate("id => { var f = document.getElementById(id); scrollTo(0, f.getBoundingClientRect().top + scrollY); }", d["id"])
                for i, e in enumerate(ends):  # 측정기와 같이 엔진 버튼으로 단계를 넘겨, 독자가 보는 장면을 찍는다
                    page.evaluate("([id, i]) => __c0.toStep(id, i)", [d["id"], i])
                    name = f"{d['id']}-s{i + 1}.png"
                    page.screenshot(path=str(out / name))
                    index.append({"file": name, "kind": "step", "page": d["page"], "width": 1280, "figure": d["id"],
                                  "step": i + 1, "seconds": round(e - (ends[i - 1] if i else 0), 2)})
            finally:
                page.close()
    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return index


def main(argv=None):
    ap = argparse.ArgumentParser(description="검토용 페이지·단계 장면과 보이는 글을 만든다")
    ap.add_argument("html")
    ap.add_argument("out")
    ap.add_argument("--mode", choices=["auto", "step"])
    a = ap.parse_args(argv)
    try:
        idx = shoot(a.html, a.out, a.mode)
    except EnvFail as e:
        print(f"환경 실패: {e}", file=sys.stderr)
        return 2
    print(f"장면 {len(idx)}개를 {a.out}에 남겼다")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: 통과 확인**

Run: `python -B -m unittest discover -s tests -p "test_eval_commands.py" -v`
Expected: 모든 시험 PASS.

- [ ] **Step 5: 커밋**

```bash
git add eval/shoot.py tests/test_eval_commands.py
git commit -m "C0: 검토용 장면 명령을 추가한다"
```

---

### Task 7: 체크리스트, 다수결, 프롬프트 틀

**Files:**
- Create: `eval/checklist.md`, `eval/checklist_vote.py`, `eval/prompts/checklist-review.md`, `eval/prompts/comprehension.md`, `eval/prompts/planted-error.md`, `eval/prompts/title-link.md`
- Modify: `tests/test_eval_commands.py`(클래스 추가)

**Interfaces:**
- Produces:
  - `checklist_vote.load_items(path) -> list[{id, category, target, question, defect}]`
  - `checklist_vote.majority(answers: list[str]) -> str`, `checklist_vote.stable(answers) -> bool`
  - `checklist_vote.answers(runs: dict[sample, list[list[{id, answer, evidence}]]]) -> dict[sample, dict[id, list[str]]]`, `checklist_vote.merge(base, *overrides)`
  - `checklist_vote.tally(per_sample: dict[sample, dict[id, list[str]]], items) -> {"samples": {sample: {id: {runs, majority, stable}}}, "coverage": {sample: {target: float|None}}}`
  - 명령: `python eval/checklist_vote.py <결과 폴더> <출력.json> [--override <보정 폴더>]…`. 결과 폴더의 `<견본>-run<k>.json`을 묶고, 보정 폴더의 같은 (견본, 항목)은 보정 결과로 바꾼다.
  - 프롬프트 빈칸: 모든 틀에 `{{INPUT_DIR}}`. `checklist-review.md`에 `{{CHECKLIST}}`, `comprehension.md`에 `{{QUESTIONS}}`, `planted-error.md`에 `{{ERROR_HINT_SCOPE}}`, `title-link.md`에 `{{STAGE}}`.

- [ ] **Step 1: 실패하는 시험 추가**

`tests/test_eval_commands.py`에 추가:

```python
DEFECTS = ["애니메이션 단계가 읽기 전에 넘어간다", "설명이 도형에서 떨어져 하단 자막으로만 나온다",
           "강조 노드와 설명을 한 화면에서 함께 볼 수 없다", "현재 노드와 지나온 노드가 구분되지 않는다",
           "390 폭에서 표를 읽기 어렵거나 가로 스크롤 단서가 없다", "페이지 번호가 두 번 보인다", "용어 풀이 배치가 깨진다",
           "제목만 읽으면 논지가 보이지 않는다", "같은 사실을 불릿·도식·표로 반복한다", "결정 요청에 권장안이 없다",
           "전후 비교의 기준선이 끝 장면에서 사라진다", "불릿과 표의 내용이 서로 다르다", "근거 없는 주장이 있다"]


class Checklist(unittest.TestCase):
    def test_items_cover_defects_and_labels(self):
        import checklist_vote as cv
        items = cv.load_items(ROOT / "eval/checklist.md")
        self.assertGreaterEqual(len(items), 13)
        self.assertEqual(len({i["id"] for i in items}), len(items))
        for i in items:
            self.assertIn(i["category"], {"사용자 만족도", "심미성", "구성", "이해 용이성", "논리 전개"})
            self.assertIn(i["target"], {"motion", "layout", "content"})
        for d in DEFECTS:
            self.assertTrue(any(d in i["defect"] for i in items), d)

    def test_majority_and_coverage(self):
        import checklist_vote as cv
        self.assertEqual(cv.majority(["예", "예", "아니오"]), "예")
        self.assertEqual(cv.majority(["예", "아니오", "해당 없음"]), "아니오")
        self.assertEqual(cv.majority(["해당 없음"] * 3), "해당 없음")
        self.assertFalse(cv.stable(["예", "예", "아니오"]))
        items = [{"id": "a", "target": "motion"}, {"id": "b", "target": "motion"}, {"id": "c", "target": "layout"}]
        run = lambda a, b, c: [{"id": "a", "answer": a, "evidence": ""}, {"id": "b", "answer": b, "evidence": ""}, {"id": "c", "answer": c, "evidence": ""}]
        per = cv.answers({"s": [run("예", "아니오", "해당 없음"), run("예", "아니오", "해당 없음"), run("예", "예", "해당 없음")]})
        t = cv.tally(per, items)
        self.assertEqual(t["coverage"]["s"], {"motion": 0.5, "layout": None, "content": None})
        self.assertEqual(t["samples"]["s"]["b"]["majority"], "아니오")
        self.assertFalse(t["samples"]["s"]["b"]["stable"])
        fixed = cv.merge(per, {"s": {"b": ["예", "예", "예"]}})
        self.assertEqual(cv.tally(fixed, items)["coverage"]["s"]["motion"], 1.0)
        self.assertNotIn("x", cv.tally({"s": {"x": ["예"] * 3}}, items)["samples"]["s"])  # 뺀 항목은 묶지 않는다


class Prompts(unittest.TestCase):
    SLOTS = {"checklist-review.md": "{{CHECKLIST}}", "comprehension.md": "{{QUESTIONS}}",
             "planted-error.md": "{{ERROR_HINT_SCOPE}}", "title-link.md": "{{STAGE}}"}

    def test_slots_only_no_answers(self):
        for name, slot in self.SLOTS.items():
            text = (ROOT / "eval/prompts" / name).read_text(encoding="utf-8")
            self.assertIn("{{INPUT_DIR}}", text, name)
            self.assertIn(slot, text, name)
            for banned in ("정답:", "정답은", "모범 답", "answer key", "심은 오류는"):
                self.assertNotIn(banned, text, name)
            self.assertNotIn("writing-html-reports", text, name)
            self.assertNotIn("whr-c0", text, name)
```

- [ ] **Step 2: 실패 확인**

Run: `python -B -m unittest discover -s tests -p "test_eval_commands.py" -v`
Expected: `Checklist`·`Prompts` 실패(파일 없음).

- [ ] **Step 3: `eval/checklist.md` 작성**

```markdown
# 보고서 화면 체크리스트

이 파일은 보고서 품질을 판정하는 이진 체크리스트다. 검토자는 `eval/shoot.py` 출력 폴더의 장면과 글만 보고 항목마다 '예'·'아니오'·'해당 없음'으로 답한다. '예'가 바람직한 상태다. 적용 대상은 그 항목을 고칠 수 있는 컴포넌트다. `motion`은 애니메이션·도식·차트, `layout`은 색·배치·페이지 틀, `content`는 문장·절 구성·근거·결정 요청이다. 질문의 '노드'는 도식 안의 도형(상자, 마름모, 막대)을 가리킨다. '설명 상자'는 애니메이션이 노드 옆에 보여 주는 글 상자이고, '자막'은 그림 아래에 나오는 단계 문장이다.

| id | 범주 | 적용 대상 | 질문 | 대응 결함 |
|---|---|---|---|---|
| `anim-readable` | 이해 용이성 | motion | 애니메이션 단계 장면마다, index.json의 `seconds`(그 단계의 연출과 머무는 시간을 합친 길이) 안에 그 장면에 새로 나온 자막과 설명 상자의 글을 끝까지 읽을 수 있는가(한국어 초당 8자 기준)? 애니메이션이 없으면 해당 없음이다. | 애니메이션 단계가 읽기 전에 넘어간다 |
| `note-beside` | 구성 | motion | 애니메이션 단계 장면마다, 그 단계의 설명이 강조된 노드 바로 옆의 설명 상자에 나오는가(그림 아래 자막에만 있지 않은가)? 애니메이션이 없으면 해당 없음이다. | 설명이 도형에서 떨어져 하단 자막으로만 나온다 |
| `focus-note-one-screen` | 이해 용이성 | motion | 애니메이션 단계 장면(1280×800 한 화면)마다, 강조된 노드와 그 단계의 설명(설명 상자나 자막)이 둘 다 화면 안에 보이는가? 애니메이션이 없으면 해당 없음이다. | 강조 노드와 설명을 한 화면에서 함께 볼 수 없다 |
| `current-vs-past` | 심미성 | motion | 여러 노드를 차례로 강조하는 애니메이션에서, 현재 강조된 노드와 이미 지나온 노드가 색이나 채움으로 서로 다르게 보이는가? 차례 강조가 없으면 해당 없음이다. | 현재 노드와 지나온 노드가 구분되지 않는다 |
| `baseline-kept` | 논리 전개 | motion | 전후 비교 애니메이션의 마지막 단계 장면에 비교 기준 막대나 바뀌기 전 값이 함께 남아 있는가? 전후 비교 애니메이션이 없으면 해당 없음이다. | 전후 비교의 기준선이 끝 장면에서 사라진다 |
| `svg-text-390` | 심미성 | motion | 390 폭 장면에서 도식·차트·애니메이션 안의 글자를 확대하지 않고 읽을 수 있는가? 도식·차트가 없으면 해당 없음이다. | 390 폭에서 도식 글자가 읽을 수 없게 작아진다 |
| `table-cols-390` | 이해 용이성 | layout | 390 폭 장면에서 모든 표의 열이 한두 글자 폭으로 잘리지 않고 단어 단위로 읽히는가? 표가 없으면 해당 없음이다. | 390 폭에서 표를 읽기 어렵거나 가로 스크롤 단서가 없다 |
| `table-scroll-cue-390` | 이해 용이성 | layout | 390 폭 장면에서 화면 오른쪽으로 잘려 이어지는 표마다, 가로로 밀어 볼 수 있다는 단서(그림자, 안내 문구, 잘린 열 표시)가 보이는가? 잘리는 표가 없으면 해당 없음이다. | 390 폭에서 표를 읽기 어렵거나 가로 스크롤 단서가 없다 |
| `single-page-number` | 심미성 | layout | 페이지 장면마다 '2 / 8' 같은 페이지 번호가 한 번만 보이는가? 페이지 번호가 없는 문서는 해당 없음이다. | 페이지 번호가 두 번 보인다 |
| `glossary-layout` | 심미성 | layout | 용어 풀이 목록이 있는 장면에서, 목록에 제목이 있고 각 용어와 풀이가 같은 줄에 가까이 붙어 짝이 바로 읽히는가? 용어 풀이 목록이 없으면 해당 없음이다. | 용어 풀이 배치가 깨진다 |
| `titles-tell-story` | 논리 전개 | content | 페이지(또는 절) 제목만 차례로 읽어도 문서의 결론과 논지가 이어져 보이는가(제목이 주제 이름에 그치지 않고 결론 문장인가)? 모든 문서에 적용한다. | 제목만 읽으면 논지가 보이지 않는다 |
| `no-triple-repeat` | 구성 | content | 각 페이지에서 불릿·도식·표가 같은 사실을 되풀이하지 않고 서로 다른 정보를 보태는가? 모든 문서에 적용한다. | 같은 사실을 불릿·도식·표로 반복한다 |
| `decision-recommend` | 사용자 만족도 | content | 독자에게 결정을 요청하는 항목마다 권장안과 그 이유가 적혀 있는가? 결정 요청이 없으면 해당 없음이다. | 결정 요청에 권장안이 없다 |
| `bullet-table-agree` | 논리 전개 | content | 같은 페이지의 불릿과 표·도식이 같은 대상에 대해 서로 다른 내용(빠진 항목, 다른 수치)을 말하지 않는가? 모든 문서에 적용한다. | 불릿과 표의 내용이 서로 다르다 |
| `claims-sourced` | 사용자 만족도 | content | 수치나 단정 주장마다 같은 페이지의 표·그림·출처 목록에서 근거를 찾을 수 있는가? 모든 문서에 적용한다. | 근거 없는 주장이 있다 |
```

- [ ] **Step 4: `eval/checklist_vote.py` 작성**

```python
"""체크리스트 3회 결과 묶기.

사용법: python eval/checklist_vote.py <결과 폴더> <출력.json> [--override <보정 폴더>]…
결과 폴더의 <견본>-run<k>.json(항목마다 {id, answer, evidence}의 목록)을 견본·항목별로 묶어
다수결, 흔들림(세 결과가 모두 같지 않음), 적용 대상별 충족률을 낸다.
보정 폴더는 문구를 고친 항목만 다시 측정한 결과다. 뒤에 준 폴더일수록 우선하며, 그 폴더에 있는 (견본, 항목)의 세 결과를 통째로 바꾼다.
현재 checklist.md에 없는 항목(뺀 항목)은 묶지 않는다.
다수결: 둘 이상 같은 답이 다수결이고, 셋이 모두 다르면 '아니오'다('해당 없음'이 끼어 있기 때문이다).
충족률: 다수결이 '예'인 항목 수 ÷ 다수결이 '해당 없음'이 아닌 항목 수. 분모가 0이면 null.
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
YES, NO, NA = "예", "아니오", "해당 없음"
TARGETS = ("motion", "layout", "content")


def load_items(path=ROOT / "eval" / "checklist.md"):
    items = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) == 5 and re.fullmatch(r"`[a-z0-9-]+`", cols[0]):
            items.append({"id": cols[0].strip("`"), "category": cols[1], "target": cols[2],
                          "question": cols[3], "defect": cols[4]})
    return items


def majority(answers):
    top, k = Counter(answers).most_common(1)[0]
    return top if k >= 2 else NO


def stable(answers):
    return len(set(answers)) == 1


def answers(runs):
    """{견본: [회차별 답 목록]}을 {견본: {항목: [답…]}}으로 바꾼다."""
    out = {}
    for sample, rs in runs.items():
        per = defaultdict(list)
        for r in rs:
            for a in r:
                per[a["id"]].append(a["answer"])
        out[sample] = dict(per)
    return out


def merge(base, *overrides):
    """보정 결과가 있는 (견본, 항목)은 보정 결과로 통째로 바꾼다."""
    out = {s: dict(v) for s, v in base.items()}
    for o in overrides:
        for s, per in o.items():
            out.setdefault(s, {}).update(per)
    return out


def tally(per_sample, items):
    """per_sample: {견본: {항목: [답…]}}."""
    target = {i["id"]: i["target"] for i in items}
    samples, coverage = {}, {}
    for sample, per in per_sample.items():
        per = {i: v for i, v in per.items() if i in target}
        samples[sample] = {i: {"runs": v, "majority": majority(v), "stable": stable(v)} for i, v in per.items()}
        cov = {}
        for t in TARGETS:
            got = [x["majority"] for i, x in samples[sample].items() if target.get(i) == t and x["majority"] != NA]
            cov[t] = round(got.count(YES) / len(got), 3) if got else None
        coverage[sample] = cov
    return {"samples": samples, "coverage": coverage}


def load_runs(folder):
    runs = defaultdict(list)
    for p in sorted(Path(folder).glob("*-run*.json")):
        runs[re.sub(r"-run\d+$", "", p.stem)].append(json.loads(p.read_text(encoding="utf-8")))
    return answers(dict(runs))


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="체크리스트 3회 결과를 다수결로 묶는다")
    ap.add_argument("folder")
    ap.add_argument("out")
    ap.add_argument("--override", action="append", default=[])
    a = ap.parse_args(argv)
    per = merge(load_runs(a.folder), *[load_runs(o) for o in a.override])
    res = tally(per, load_items())
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"견본 {len(per)}개의 결과를 {a.out}에 묶었다")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: 프롬프트 틀 작성**

틀 안에 JSON 코드 울타리가 있으므로, 이 plan에서는 바깥 울타리를 `~~~~`로 쓴다. 파일 내용은 울타리 사이의 글이다.

`eval/prompts/checklist-review.md`:

~~~~markdown
# 체크리스트 검토 프롬프트 틀

L1(이 하네스를 운용하는 메인 세션)은 이 틀의 빈칸을 채워 검토 서브에이전트에게 준다. `{{INPUT_DIR}}`에는 `eval/shoot.py` 출력 폴더 경로를 넣는다. `{{CHECKLIST}}`에는 `eval/checklist.md` 표의 id 열과 질문 열을 옮긴 목록과, 표 앞 문단의 용어 풀이를 넣는다. 대응 결함 열은 넣지 않는다.

---

당신은 보고서 화면을 처음 보는 검토자다. 이 보고서를 누가 왜 만들었는지 모른다고 가정한다. 아래 폴더의 파일만 보고 판정하고, 다른 파일이나 저장소는 찾지 않는다.

- **입력 폴더:** `{{INPUT_DIR}}`
- **장면 목록:** `index.json`이 장면 파일을 나열한다.
- **페이지 장면:** `kind`가 `page`인 장면이고, `width`는 1280 또는 390이다. 단일 문서는 화면 높이 단위로 나뉜다.
- **단계 장면:** `kind`가 `step`인 장면은 애니메이션 단계 끝 장면이다. `seconds`는 그 단계의 연출과 머무는 시간을 합친 길이(초)다.
- **글:** `<페이지>.txt`(단일 문서는 `doc.txt`)에 화면에 보이는 글이 있다.

항목마다 '예', '아니오', '해당 없음' 중 하나로 답한다. '예'는 항목이 묻는 바람직한 상태가 모든 해당 장면에서 성립한다는 뜻이고, 한 장면이라도 성립하지 않으면 '아니오'다. '해당 없음'은 항목이 묻는 대상(애니메이션, 표, 결정 요청 같은 대상)이 문서에 없을 때만 쓴다. 근거(`evidence`)에는 판정에 쓴 장면 파일 이름과 본 내용을 한두 문장으로 적는다.

항목은 다음과 같다.

{{CHECKLIST}}

출력은 JSON 배열 하나만 쓴다. 다른 글은 쓰지 않는다.

```json
[{"id": "항목 id", "answer": "예", "evidence": "p2-390.png: …"}]
```
~~~~

`eval/prompts/comprehension.md`:

~~~~markdown
# 이해도 시험 프롬프트 틀

L1(이 하네스를 운용하는 메인 세션)은 질문 목록을 따로 보관한다. `{{INPUT_DIR}}`에는 `eval/shoot.py` 출력 폴더 경로를 넣는다. `{{QUESTIONS}}`에는 번호와 질문 문장만 넣는다. 질문의 기대 답은 이 틀에 넣지 않고 L1이 따로 대조한다.

---

당신은 이 보고서를 받아 결정을 내려야 하는 독자다. 작성 과정과 저장소를 모른다고 가정한다. 아래 폴더의 파일만 보고 답하고, 다른 파일은 찾지 않는다.

- **입력 폴더:** `{{INPUT_DIR}}`(장면 목록 `index.json`, 장면 그림, 페이지별 글 `<페이지>.txt`)

질문은 다음과 같다.

{{QUESTIONS}}

답하는 규칙은 다음과 같다.

- **답:** 질문마다 보고서에 적힌 내용만으로 답한다. 보고서에서 답을 찾지 못하면 '보고서에 없음'이라고 쓴다.
- **근거:** 답마다 근거가 된 장면 파일 이름을 적는다.
- **추가 질문:** 결정하려면 보고서 작성자에게 더 물어야 할 질문을 모두 적는다.
- **찾은 오류:** 보고서 안에서 서로 맞지 않는 수치나 근거 없이 단정한 결론을 찾으면 적는다.

출력은 JSON 하나만 쓴다.

```json
{"answers": [{"no": 1, "answer": "…", "evidence": ["p3-1280.png"]}],
 "followups": ["작성자에게 더 물을 질문"],
 "errors": [{"where": "p2-1280.png", "what": "…"}]}
```
~~~~

`eval/prompts/planted-error.md`:

~~~~markdown
# 심어 둔 오류 시험 프롬프트 틀

L1(이 하네스를 운용하는 메인 세션)은 견본 사본에 오류를 넣고 `eval/shoot.py`로 장면을 만든다. `{{INPUT_DIR}}`에는 그 출력 폴더를 넣는다. `{{ERROR_HINT_SCOPE}}`에는 오류를 찾을 범위(예: '수치와 결론')만 넣는다. 넣은 오류의 내용과 위치는 이 틀에 넣지 않는다.

---

당신은 보고서를 승인하기 전에 검토하는 독자다. 작성 과정과 저장소를 모른다고 가정한다. 아래 폴더의 파일만 본다.

- **입력 폴더:** `{{INPUT_DIR}}`
- **검토 범위:** {{ERROR_HINT_SCOPE}}

보고서 안에서 틀렸거나 서로 맞지 않거나 근거 없이 단정한 내용을 모두 찾는다. 찾은 내용마다 위치(장면 파일 이름), 틀렸다고 본 이유, 확신 정도(높음·중간·낮음)를 적는다. 찾지 못하면 빈 배열을 쓴다.

출력은 JSON 하나만 쓴다.

```json
{"errors": [{"where": "p4-1280.png", "what": "…", "why": "…", "confidence": "높음"}]}
```
~~~~

`eval/prompts/title-link.md`:

~~~~markdown
# 제목 연결 프롬프트 틀

L1(이 하네스를 운용하는 메인 세션)은 같은 틀을 제목만, 전체, 판정의 차례로 쓴다. `{{STAGE}}`에는 그 단계 이름을 넣는다.

- **제목만:** L1은 절 이름과 결론 제목만 뽑아 글 파일로 둔다. `{{INPUT_DIR}}`에는 그 폴더를 넣고, 결과는 `titles.json`으로 저장한다.
- **전체:** `{{INPUT_DIR}}`에는 `eval/shoot.py` 출력 폴더를 넣고, 결과는 `full.json`으로 저장한다.
- **판정:** `{{INPUT_DIR}}`에는 `titles.json`과 `full.json`이 있는 폴더를 넣는다.

---

단계: {{STAGE}}
입력 폴더: `{{INPUT_DIR}}`

당신은 보고서 작성 과정과 저장소를 모르는 독자다. 입력 폴더의 파일만 본다.

제목만 단계와 전체 단계에서는 이 보고서의 결론을 세 문장 이하로 요약한다. 출력은 `{"summary": "…"}` 하나다.

판정 단계에서는 `titles.json`과 `full.json`의 요약이 같은 결정을 가리키는지 판정한다. 표현이 달라도 결론이 같으면 일치다. 출력은 `{"match": true, "why": "…"}` 하나다.
~~~~

- [ ] **Step 6: 통과 확인**

Run: `python -B -m unittest discover -s tests -p "test_eval_commands.py" -v`
Expected: 모든 시험 PASS.

- [ ] **Step 7: 커밋**

```bash
git add eval/checklist.md eval/checklist_vote.py eval/prompts tests/test_eval_commands.py
git commit -m "C0: 체크리스트·다수결 집계·검토 프롬프트 틀을 추가한다"
```

---

### Task 8: 최소 견본

**Files:**
- Create: `eval/validation/minimal-anim.html`

**Interfaces:**
- Consumes: 현재 엔진의 `RC.demo`, `RC.note`, `RC.icon`, `RC.fx`(`clear`·`pair`·`say`·`mark`), `RC.color`. build.py가 관리 블록을 채운다.
- Produces: `python eval/gates.py eval/validation/minimal-anim.html --mode auto --only motion`의 결과에서 실현 가능성 항목이 통과한다. 실현 가능성 항목은 `dwell`(2단계부터, `value.fails_after_step1`이 0), `note-near`, `active-visible`, `svg-font-390`, `figure-overflow-390`이다.

- [ ] **Step 1: 견본 작성**

무대는 `viewBox="0 0 340 300"`, `width="100%"`, `style="max-width:360px"`로 그린다. 1280 폭에서 360px, 390 폭에서 약 358px라 배율이 약 1.05이고, 노드 글자 13px와 설명 상자 글자 12.5px이 화면에서 11px을 넘는다.

노드는 세 사각형 `n1`·`n2`·`n3`(x=40, 폭 120, 높이 44, y=20·128·236)이고, 그 사이에 세로 간선 두 개(x=100)를 둔다. 설명 상자는 `RC.note(st, 160, 44)`이고, 단계마다 현재 노드 오른쪽 20px(x=180)에 노드와 같은 y로 둔다. 문서 코드는 `tl.call(act, [i])`로 단계 시작에 현재 노드에만 `data-rc-active`를 단다.

현재 노드는 `fx.mark(tl, node, 'accent')`로 강조하고, 지나온 노드는 `tl.to(prev, {stroke: RC.color('ink-3'), strokeWidth: 1, strokeDasharray: '4 3', duration: 0.2})`로 점선 회색이 된다. 머무는 시간은 단계 끝의 `tl.to({}, {duration: pad})` 빈 트윈으로 맞춘다. `pad = 1 + n/8 + 0.8`이고, n은 측정기와 같은 방식으로 센다. 첫 단계의 n은 설명 상자 글자 수이고, 나머지 단계의 n은 자막(단계 이름 + ': ' + 문장)과 설명 상자 글자 수의 합이다. 마지막 단계에는 `check` 아이콘을 노드 왼쪽(x=20)에 `fx.pair`로 함께 보인다.

본문과 id는 검토자에게 목적을 드러내지 않는 업무 내용으로 쓴다. 이 견본은 체크리스트 양성 대조에도 쓰이기 때문이다.

```html
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>요청 처리 흐름</title>
<style>
/* BEGIN report-base (build.py가 채운다. 손으로 고치지 않는다) */
/* END report-base */
</style>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
</head>
<body>
<main class="doc">
<h1>요청 처리 흐름</h1>
<p>요청서는 접수, 검토, 승인의 세 단계를 거쳐 처리된다. 아래 그림은 요청 한 건이 각 단계를 지나는 순서를 보인다.</p>
<figure id="d-req" data-anim="구조">
  <figcaption><span class="t">요청 처리 흐름 (애니메이션)</span></figcaption>
  <svg class="stage" id="st-req" viewBox="0 0 340 300" width="100%" style="max-width:360px" role="img" aria-label="요청 처리 흐름">
    <line x1="100" y1="64" x2="100" y2="128" style="stroke:var(--ink-2)"/>
    <line x1="100" y1="172" x2="100" y2="236" style="stroke:var(--ink-2)"/>
    <rect id="n1" x="40" y="20" width="120" height="44" style="fill:var(--paper);stroke:var(--ink)"/>
    <rect id="n2" x="40" y="128" width="120" height="44" style="fill:var(--paper);stroke:var(--ink)"/>
    <rect id="n3" x="40" y="236" width="120" height="44" style="fill:var(--paper);stroke:var(--ink)"/>
    <text x="100" y="47" font-size="13" text-anchor="middle">접수</text>
    <text x="100" y="155" font-size="13" text-anchor="middle">검토</text>
    <text x="100" y="263" font-size="13" text-anchor="middle">승인</text>
  </svg>
  <p class="src">자료: 요청 처리 절차(가상 예시)</p>
</figure>
</main>
<script>
/* BEGIN report-charts echarts@6.1.0 mermaid@11.17.2 gsap@3.15.0 (build.py가 채운다. 손으로 고치지 않는다) */
/* END report-charts */
</script>
<script>
(function () {
  var fx = RC.fx, st = document.getElementById('st-req'), nt = RC.note(st, 160, 44);
  var ok = RC.icon(st, 'check', 20, 258);
  var N = ['n1', 'n2', 'n3'].map(function (id) { return document.getElementById(id); });
  var Y = [20, 128, 236];
  function chars(s) { return String(s).replace(/\d[\d,.]*/g, '#').replace(/\s/g, '').length; }
  function act(i) { N.forEach(function (n, k) { if (k === i) n.setAttribute('data-rc-active', ''); else n.removeAttribute('data-rc-active'); }); }
  var S = [
    { name: '흐름 · 접수', text: '요청서를 접수 칸에 넣습니다.', note: '접수: 요청서 1건' },
    { name: '흐름 · 검토', text: '담당자가 요청 내용을 확인합니다.', note: '검토: 담당자 확인' },
    { name: '흐름 · 승인', text: '확인된 요청을 승인으로 넘깁니다.', note: '승인: 처리 완료' }
  ];
  RC.demo(document.getElementById('d-req'), S.map(function (s, i) {
    return { name: s.name, text: s.text, play: function (tl) {
      tl.call(act, [i]);
      fx.clear(tl, nt, [ok]);
      if (i > 0) tl.to(N[i - 1], { stroke: RC.color('ink-3'), strokeWidth: 1, strokeDasharray: '4 3', duration: 0.2 }, '<');
      fx.mark(tl, N[i], 'accent', '<');
      if (i === S.length - 1) fx.pair(tl, nt, ok, 180, Y[i], s.note, 0.4); else fx.say(tl, nt, 180, Y[i], s.note, 0.4);
      var n = chars(s.note) + (i ? chars(s.name + ': ' + s.text) : 0);
      tl.to({}, { duration: 1 + n / 8 + 0.8 });
    } };
  }));
})();
</script>
</body>
</html>
```

`check` 아이콘의 원은 반지름 11이므로 중심 (20, 258)에서 9~31 범위에 그려지고 노드(x=40)와 9px 떨어진다. 이 아이콘은 선으로 그린 상태 아이콘이라 겹침 판정의 무대 요소에 들지만, 설명 상자(x=180~340)와는 멀다.

- [ ] **Step 2: 관리 블록 채우기**

Run: `python -B build.py eval/validation/minimal-anim.html`
Expected: `기준 CSS 반영, 연결 코드 반영`.

- [ ] **Step 3: 실현 가능성 측정**

Run: `python -B eval/gates.py eval/validation/minimal-anim.html --mode auto --only motion --out <스크래치>/minimal.json; echo $?`
Expected: 실현 가능성 항목이 통과한다. `step1`은 현재 엔진이 처음 열 때 타임라인을 `e0`에 두므로 `fail`이고, 이 확인에서 뺀다(spec 「기준선과 검증」). 1단계 `dwell`은 판정에서 빼지만 결과는 기록한다.

통과하지 않으면 측정값으로 조정한다. 단계의 `dwell`이 `lo`보다 작으면 그 단계 pad에 `lo - dwell + 0.2`초를 보탠다. `dwell`이 `hi`보다 크면 `dwell - hi + 0.2`초를 뺀다. 설명 상자의 거리가 48px을 넘거나 겹치면 x를 노드 오른쪽 끝 + 20px로 둔다. 판정 기준값과 측정기는 바꾸지 않는다. 두 번 조정해도 통과하지 않으면 멈추고 BLOCKED로 돌려준다.

- [ ] **Step 4: 커밋**

```bash
git add eval/validation/minimal-anim.html
git commit -m "C0: 현재 엔진으로 애니메이션 기준값 일부를 지키는 최소 견본을 추가한다"
```

---

### Task 9: 기계 판정 기준선

**Files:**
- Create: `eval/baseline/meta.json`, `eval/baseline/gates-auto-1.json`~`-3.json`, `eval/baseline/gates-step-1.json`~`-3.json`, `eval/baseline/gates-template-extra.json`, `eval/baseline/feasibility-minimal-anim.json`

**Interfaces:**
- Consumes: `eval/rebuild.py`, `eval/gates.py`, `eval/validation/minimal-anim.html`, `template.html`(읽기만)
- Produces: `meta.json`의 키 `base_commit`·`worktree_head`·`measured_at`·`playwright`·`rebuilt_sha256`·`files`·`run_agreement`. `run_agreement`는 방식마다 세 번 측정한 (견본, 테마, 항목)의 상태가 모두 같은지를 `{"auto": {"same": 정수, "differ": [ … ]}, "step": …}`로 기록한다.

- [ ] **Step 1: 기준 커밋과 코드가 같은지 확인**

Run: `git diff --quiet 512d308 HEAD -- report-base.css report-demo.css report-charts.js report-peeps.js build.py checks check.py 금지어.md; echo $?`
Expected: `0`. 0이 아니면 기준 커밋의 코드로 다시 빌드해야 하는데, rebuild.py는 자기 워크트리의 build.py만 쓴다. 이때는 `git worktree add <스크래치>/base 512d308`로 기준 워크트리를 만들고, 이 브랜치의 `eval/`과 `bench/`를 그 워크트리에 복사해 그 안에서 `python -B eval/rebuild.py <스크래치>/rebuilt`를 실행한다. 측정이 끝나면 `git worktree remove <스크래치>/base`로 지운다.

- [ ] **Step 2: 재빌드와 두 방식 세 번 측정**

```bash
python -B eval/rebuild.py <스크래치>/rebuilt
for k in 1 2 3; do
  python -B eval/gates.py <스크래치>/rebuilt/*.html --mode auto --out eval/baseline/gates-auto-$k.json > /dev/null; echo "auto $k: $?"
  python -B eval/gates.py <스크래치>/rebuilt/*.html --mode step --out eval/baseline/gates-step-$k.json > /dev/null; echo "step $k: $?"
done
```

Expected: 모든 실행의 종료 코드가 1(실패 있음)이다. 2(환경 실패)가 나오면 네트워크를 확인하고 그 실행만 한 번 다시 측정한다. 다시 측정해도 2이면 멈추고 리포트에 적는다. 3(측정기 오류)이면 기록의 `error`와 `trace`로 원인을 고친다(superpowers:systematic-debugging).

- [ ] **Step 3: 결함 검출 표 대조**

`gates-auto-1.json`의 밝은 테마 기록에서 아래 항목의 상태와 측정값을 읽어 리포트에 옮긴다. 기대 열의 수치는 `visual-review-baseline.md`와 spec 「기준선과 검증」의 기록값이고, 이 plan이 실측한 값이 아니다.

| 견본 | 항목 | 기대 |
|---|---|---|
| 04-rules | `dwell` | `fail`, 단계 체류 약 0.32초 |
| 04-rules | `step1` | `fail`, 처음 시간이 `e0` |
| 04-rules | `note-near` | `unmeasurable`, `data-rc-active` 없음 |
| 04-rules | `svg-font-390` | `fail`, 노드 이름표 약 9.4px |
| sample-anim | `svg-font-390` | `fail`, 설명 상자 글 약 5~10px |
| sample-anim | `contrast-graphic` | `fail`, 막대 2.58:1(spec 기대) |
| session-report | `page-number` | `fail`, 페이지 번호 두 번 |

sample-anim에는 `.fill` 막대가 없다(`grep -c 'class="fill' bench/fixed/sample-anim.html`의 결과 0). 이 견본의 막대(`b-a` 등)는 테두리 없는 SVG `rect`이고, spec의 그래픽 대비 대상(`.fill`, ECharts 계열, 도식 노드 테두리)에 들지 않아 측정되지 않는다. 참고로 그 채움색 `--s4`(#8A8F98)의 흰 바탕 대비는 3.25:1이라 측정해도 3:1을 넘는다. 2.58:1 막대 `.fill`(`--accent-2`)은 `template.html`에만 있다. 그래서 sample-anim의 `contrast-graphic`이 통과로 나오면 측정기를 고치지 않고, spec의 전제가 실제와 다르다고 리포트에 적는다. 측정기가 막대 대비를 잡는지는 Step 4의 template.html 측정으로 보인다.

- [ ] **Step 4: 막대 대비 보조 측정과 실현 가능성**

```bash
python -B eval/gates.py template.html --only layout --out eval/baseline/gates-template-extra.json > /dev/null; echo $?
python -B eval/gates.py eval/validation/minimal-anim.html --mode auto --out eval/baseline/feasibility-minimal-anim.json > /dev/null; echo $?
```

Expected: template.html의 `contrast-graphic`이 `fail`이고 `value.min_ratio`가 2.58이다. minimal-anim은 Task 8 Produces의 실현 가능성 항목이 통과한다.

- [ ] **Step 5: 메타 기록**

`<스크래치>`를 절대 경로로 바꿔 실행한다.

```bash
python -B - <<'EOF'
import hashlib, json, subprocess, datetime
from pathlib import Path
import playwright
reb = Path(r"<스크래치>/rebuilt")
B = Path("eval/baseline")

def states(f):
    return {(Path(r["file"]).name, r["theme"], i["id"]): i["status"] for r in json.loads(f.read_text(encoding="utf-8")) for i in r["items"]}

agree = {}
for mode in ("auto", "step"):
    runs = [states(B / f"gates-{mode}-{k}.json") for k in (1, 2, 3)]
    keys = set().union(*runs)
    differ = sorted([list(k) + [[r.get(k) for r in runs]] for k in keys if len({r.get(k) for r in runs}) > 1])
    agree[mode] = {"same": len(keys) - len(differ), "differ": differ}
meta = {"base_commit": subprocess.check_output(["git", "rev-parse", "512d308"], text=True).strip(),
        "worktree_head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "measured_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "playwright": playwright.__version__,
        "rebuilt_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(reb.glob("*.html"))},
        "files": sorted(p.name for p in B.glob("*.json") if p.name != "meta.json"),
        "run_agreement": agree}
(B / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(json.dumps(agree, ensure_ascii=False)[:600])
EOF
python -B -c "import json,pathlib; m=json.load(open('eval/baseline/meta.json',encoding='utf-8')); missing=[f for f in m['files'] if not pathlib.Path('eval/baseline',f).exists()]; print('누락', missing); assert not missing and len(m['rebuilt_sha256'])==5"
```

Expected: 마지막 명령이 `누락 []`을 출력하고 예외 없이 끝난다. `run_agreement`의 `differ`가 비어 있지 않으면 흔들린 항목을 리포트에 적는다.

- [ ] **Step 6: 커밋**

```bash
git add eval/baseline
git commit -m "C0: 기준 커밋 512d308의 기계 판정 기준선을 세 번 측정해 남긴다"
```

---

### Task 10: 체크리스트 판별력 확인과 기준선

**Files:**
- Create: `eval/baseline/checklist/<견본>-run<k>.json`, `eval/baseline/checklist/recal-<회차>/`(보정할 때만), `eval/baseline/checklist-majority.json`, `eval/baseline/known-defects.json`, `eval/baseline/checklist-agreement.md`
- Modify (보정할 때만): `eval/checklist.md`

**Interfaces:**
- Consumes: `eval/shoot.py`, `eval/prompts/checklist-review.md`, `eval/checklist.md`, `eval/checklist_vote.py`, Task 9의 `<스크래치>/rebuilt`
- Produces: `known-defects.json`의 형태 `{"<견본>": {"<항목 id>": "근거 문장"}, "minimal-anim": {"positive": ["<항목 id>", …]}}`. `checklist-majority.json`은 `checklist_vote.tally`의 출력이다.

이 Task는 L2가 직접 진행하고, 검토는 서브에이전트가 한다.

- [ ] **Step 1: 장면 만들기**

검토 서브에이전트에게 저장소 이름이 드러나지 않게, 장면을 프로젝트 이름이 없는 임시 폴더 `C:/Users/ho381/AppData/Local/Temp/c0rv/`에 만든다. 견본 이름도 가린다.

```bash
R=C:/Users/ho381/AppData/Local/Temp/c0rv
python -B eval/shoot.py <스크래치>/rebuilt/04-rules.html $R/doc-a
python -B eval/shoot.py <스크래치>/rebuilt/03-groups.html $R/doc-b
python -B eval/shoot.py <스크래치>/rebuilt/session-report.html $R/doc-c
python -B eval/shoot.py <스크래치>/rebuilt/sample-anim.html $R/doc-d
python -B eval/shoot.py <스크래치>/rebuilt/sample-viz.html $R/doc-e
python -B eval/shoot.py eval/validation/minimal-anim.html $R/doc-f
ls $R/*/index.json
```

Expected: 명령마다 종료 코드 0이고, 마지막 줄이 `index.json` 여섯 개를 나열한다.

- [ ] **Step 2: 검토 3회 실행**

`eval/prompts/checklist-review.md`의 빈칸을 채운다. `{{INPUT_DIR}}`에는 장면 폴더를, `{{CHECKLIST}}`에는 id·질문 열과 용어 풀이를 넣는다. 견본마다 새 서브에이전트를 세 번 실행하고, 서브에이전트에게는 채운 프롬프트만 준다. 프롬프트에는 '입력 폴더 밖의 파일은 열지 않는다'를 넣는다. 결과 JSON을 `eval/baseline/checklist/<견본 이름>-run<k>.json`으로 저장한다(견본 이름은 `04-rules` 같은 실제 이름).

Run: `ls eval/baseline/checklist/*-run*.json | wc -l`
Expected: `18`(견본 여섯 × 3회). 결과마다 `python -B -c "import json,sys; d=json.load(open(sys.argv[1],encoding='utf-8')); assert all(a['answer'] in ('예','아니오','해당 없음') for a in d)" <파일>`이 예외 없이 끝난다.

- [ ] **Step 3: 알려진 결함 기록**

검토가 끝난 뒤에 `eval/baseline/known-defects.json`을 쓴다. 견본별로 대응 결함이 있는 체크리스트 항목을 `visual-review-baseline.md`에서 옮기고, 근거 문장을 함께 적는다. sample-viz는 시각 검토 기준선에 없으므로 음성 대조에 쓰지 않는다. minimal-anim의 `positive`에는 `anim-readable`·`note-beside`·`focus-note-one-screen`·`current-vs-past`·`svg-text-390`을 적는다.

Run: `python -B -c "import json; d=json.load(open('eval/baseline/known-defects.json',encoding='utf-8')); print(sorted(d))"`
Expected: `['03-groups', '04-rules', 'minimal-anim', 'sample-anim', 'session-report']`.

- [ ] **Step 4: 다수결과 표시**

Run: `python -B eval/checklist_vote.py eval/baseline/checklist eval/baseline/checklist-majority.json; echo $?`
Expected: `견본 6개의 결과를 … 묶었다`, 종료 코드 0.

표시 규칙은 spec을 따른다. 흔들림은 세 결과가 모두 같지 않은 (견본, 항목)이다. 음성 대조 실패는 `known-defects.json`의 대응 결함이 있는 견본에서 다수결이 '예'인 상황이다. 양성 대조 실패는 minimal-anim의 `positive` 항목에서 다수결이 '아니오'인 상황이다.

- [ ] **Step 5: 보정**

표시된 항목은 문구를 고친다(`eval/checklist.md`). 문구를 바꾼 항목은 견본에 맞추는 과적합을 피하려고 여섯 견본 모두에서 3회씩 다시 측정한다. 결과는 `eval/baseline/checklist/recal-<회차>/<견본>-run<k>.json`에 두고 고친 항목만 넣는다. 재측정은 두 번까지다. 그래도 표시가 남은 항목은 체크리스트에서 빼고, 뺀 항목이 덮던 결함을 `checklist-agreement.md`에 적는다.

Run: `python -B eval/checklist_vote.py eval/baseline/checklist eval/baseline/checklist-majority.json --override eval/baseline/checklist/recal-1 [--override eval/baseline/checklist/recal-2]`
Expected: 종료 코드 0. 결과의 견본별 항목에 뺀 항목이 없다.

- [ ] **Step 6: 일치율·판별력 보고**

`eval/baseline/checklist-agreement.md`에 다음 절을 둔다. 절 제목은 `일치율`, `음성 대조와 양성 대조`, `보정과 뺀 항목`이다.

- **일치율:** 견본·항목별 3회 결과의 일치 여부와, 항목별 일치율(세 결과가 모두 같은 견본의 비율)을 적는다.
- **음성 대조와 양성 대조:** 대조 실패 항목과 근거를 적는다.
- **보정과 뺀 항목:** 바꾼 문구, 뺀 항목과 이유, 뺀 항목이 덮던 결함을 적는다.

Run: `grep -c "^## " eval/baseline/checklist-agreement.md`
Expected: `3` 이상.

- [ ] **Step 7: 시험과 커밋**

Run: `python -B -m unittest discover -s tests`
Expected: 모든 시험 PASS. 체크리스트에서 항목을 빼면 `Checklist` 시험의 결함 대응이 깨질 수 있다. 그 결함에 대응하는 다른 항목이 남아 있는지 확인하고, 없으면 리포트에 적는다.

```bash
git add eval/baseline eval/checklist.md
git commit -m "C0: 체크리스트 3회 기준선과 판별력 보고를 남긴다"
```

---

### Task 11: 리포트

**Files:**
- Create: `C:/Users/ho381/AppData/Local/Temp/claude/D--projects-Structure-writing-html-reports/d5fb1593-166c-41a5-bca7-de1d08dffdcb/scratchpad/report-c0.md`(브랜치에 커밋하지 않는다)

**Interfaces:**
- Consumes: Task 1~10의 결과, `eval/baseline/*`, plan 리뷰 기록, 이 plan의 「이 plan이 정한 해석」
- Produces: spec 「산출 계약」과 L1 지시가 정한 항목으로 된 리포트

- [ ] **Step 1: 리포트 작성**

리포트에는 다음 절을 둔다.

- **변경 파일:** `git diff --stat 5badd33..HEAD`의 결과
- **시험 최종 결과:** `python -B -m unittest discover -s tests`의 마지막 줄
- **기준선 결과 요약:** Task 9의 견본별 실패 항목, `run_agreement`
- **결함 검출 표:** Task 9 Step 3 표의 항목별 상태와 측정값
- **실현 가능성과 판별력:** Task 8·9의 실현 가능성 결과, Task 10의 일치율·대조 결과·뺀 항목과 이유
- **plan 리뷰 반영:** 기능적 변화가 있었던 반영
- **spec·상위 설계와 다르게 정한 점:** 03-groups 추가, 큰 글자 예외, 「이 plan이 정한 해석」의 항목, sample-anim 막대 대비 전제
- **브랜치 이름:** `c0-eval-harness`

Run: `grep -c "^## " <리포트 경로>`
Expected: 위 절 수 이상.

---

## 자체 점검

- **spec 대조:** 산출물 표의 모든 경로가 Task 1~10에 있다. 문서 열기(Task 3), `measure.ORDER`의 모든 판정 항목(Task 4·5), 체류 시간 측정(Task 2·3·5), 설명 상자 판정(Task 2·3·5), 대비 판정(Task 3·4), 장면(Task 6), 체크리스트와 프롬프트(Task 7), 기준선과 검증(Task 8·9·10), 단위 시험 목록(Task 1~7), 산출 계약의 리포트(Task 11)가 대응한다.
- **이름 일치:** `source_facts`의 키(`demo_calls`·`has_svg`·`pages`·`paged`), `item`의 키, `__c0`의 함수 이름을 모든 Task가 같은 이름으로 쓴다.

<!-- spec-review: passed -->
