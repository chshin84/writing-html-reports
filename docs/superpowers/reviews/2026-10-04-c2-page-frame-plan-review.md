# C2 페이지 틀 plan 리뷰 기록

대상은 `docs/superpowers/plans/2026-10-04-c2-page-frame.md`(plan)이다. 경로가 `plans` 아래이므로 plan으로 판정했다. 렌즈는 lens-grounding, lens-consistency, lens-adversarial, lens-fit이고 렌즈마다 읽기 전용 Plan 에이전트로 따로 실행했다. 렌즈를 한 번씩만 실행했다. 원본은 같은 이름 폴더에 있다.

선행연구 렌즈는 붙이지 않았다. plan에는 제안하지 않는다는 규칙에 해당한다.

## 합친 지적

| 지적 | 렌즈 | 함께 잡은 렌즈 |
|---|---|---|
| 견본 결론 제목이 '결론'으로 시작해 checks/content.py가 p2를 핵심 후보에서 빼고 ★ 표시와 평가가 달라진다(위반 0건 예상과 모순) | grounding | 없음 |
| 밝은 `--s4` 변경이 기준선 회색과 `--s1`의 대비를 3.53에서 1.65로 떨어뜨린다 | adversarial | 없음 |
| 어두운 새 `--s4`와 `--accent-2`의 제2색각 색차가 14.1이다 | adversarial | 없음 |
| 인쇄 규칙의 명시도가 낮아 단서가 인쇄에 남을 수 있다 | consistency | 없음 |
| 390 폭 용어 목록 배치가 체크리스트 `glossary-layout`의 '같은 줄' 문언과 다르다 | consistency | 없음 |
| Task 2 Step 2의 실패 예상(ERROR·FAIL 구분)이 시험 코드와 다르다 | consistency, grounding, fit | 셋 |
| Task 1 Step 2의 실패 이유는 8.39가 아니라 2.95 대비에서 먼저 난다 | grounding | consistency(덧붙임) |
| 리포트 작성 단계가 없다 | consistency, fit | 둘 |
| probe.js가 `light-dark()`를 못 읽는다는 단정의 근거가 없다 | grounding | 없음 |
| 56px로 하이픈 줄바꿈을 막지 못한다 | adversarial | 없음 |
| 4열 판정이 넘침과 다르다(넘치는 3열 표, 들어가는 4열 표) | adversarial | 없음 |
| `th,td` 최소 폭이 `.tbl` 밖 표에도 걸린다 | adversarial | 없음 |
| CSS 글자('용어', 단서)는 글 추출에 없다 | adversarial | 없음 |
| `--base-checks` 실행을 재현하지 않는다 | adversarial | 없음 |
| 원본 h2 추출이 새 문서와 다른 경로다 | adversarial | 없음 |
| `.sec`·`.state` 전역 선택자 | adversarial | 없음 |
| 직접 나열 용어 목록의 괘선이 열 간격에서 끊긴다 | adversarial | 없음 |
| '기존 docstring 유지'·'이하 기존 본문 그대로' 자리표시 | fit | 없음 |
| `<스크래치>`·`<임시>` 자리표시와 이름 불일치 | fit | 없음 |
| 커밋 명령에 trailer 두 줄이 없다 | fit | 없음 |
| 용어 목록·`#top` 앵커 확인에 코드가 없다 | fit | 없음 |
| Task 6에 체크박스가 없다 | fit | 없음 |
| 변경 전 위반 건수를 기록하는 단계가 없다 | fit | 없음 |
| Architecture가 네 문장이다, 개수 예고, 화살표 서술, 한 문장 여러 기준 | fit | 없음 |

## 커버리지 공백

Chromium 표 칸 `min-width` 반영, `fit-content(14em)`과 `subgrid`의 배치, WebKit 동작은 어느 렌즈도 측정하지 않았다(브라우저를 띄우지 않았다). 렌즈 원본에 `principles_applied`는 모두 채워져 있다.
