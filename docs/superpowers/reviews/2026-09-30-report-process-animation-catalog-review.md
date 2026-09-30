# 보고서 작성 과정과 애니메이션 목록 설계 리뷰

검토 대상은 `docs/superpowers/specs/2026-09-30-report-process-animation-catalog-design.md`이고, 경로가 `docs/superpowers/specs` 아래라 spec으로 판정했다. 렌즈 네 개(`lens-grounding`, `lens-consistency`, `lens-adversarial`, `lens-fit`)를 대상 하나에 하나씩 따로 실행했고, 렌즈별 원본은 같은 이름의 폴더에 있다.

렌즈를 한 번씩만 실행했다.

선행연구 렌즈(`lens-prior-art`)는 제안하지 않았다. 이 spec은 이미 하던 보고서 작성과 동작 예시 작업을 과정과 목록으로 정리하는 일이라, 발동 기준인 '되는지 자체가 미지수'에 해당하지 않는다.

네 렌즈 모두 `principles_applied`를 채웠고 `read`도 비어 있지 않다. `lens-fit`의 `doc_type`은 '설계(spec·plan)' 행으로 채워졌다.

## 지적 목록

| 렌즈 | 위치 | 유형 | 지적 |
|---|---|---|---|
| lens-grounding | — | — | 지적 없음. 검증 대상 사실 일곱 가지(시험 41개, 높이 40, 조각 이름 아홉 개, p9 11점 산수, 파일당 3개 상한, 95KB 가정 표시, CC0 표기)가 모두 일치했다 |
| lens-consistency | 인물 그림 · 이름 호환 | drift | `RC.fx.think(tl, person, question)` 인용에 네 번째 인자 `at`이 빠졌다 |
| lens-consistency | 인물 그림 · 아이콘 표 | gap | `person-guide`(안내)를 언제 어떤 효과로 쓰는지가 없다 |
| lens-consistency | 작업 과정 표 6단계 | gap | '선택 이유 보고'의 형식과 확인 절차가 시험·완료 기준에 없다 |
| lens-consistency | 검사기 변경 · 원본 대조 예외 | contradiction | 새 규칙 네 가지가 원본 대조 예외를 어느 방식으로 받는지와 `main()` 연결이 정해지지 않았다 |
| lens-consistency | 인물 그림 · 크기와 범위 | gap | 상반신으로 자르는 단계가 `tools/build-peeps.py` 작업 목록에 없다 |
| lens-consistency | 설계 범위 | scope | 인물 그림 파이프라인과 목록·검사기 작업이 한 plan으로 묶여 있다 |
| lens-adversarial | 검사기 변경 · B 제외 | failure-mode | 페이지 본문 전체에서 `<polygon>`을 세는 정규식으로는 figure 경계를 구분하지 못한다. 혼합 페이지 시험이 없다 |
| lens-adversarial | 견본과 문서 · sample-viz 행 | failure-mode | 새 견본의 막대·선을 `<g>`로 묶으면 `RC.check`가 겹침을 놓친다. 새 견본에 배치 제약이 다시 적혀 있지 않다 |
| lens-adversarial | 인물 그림 · 문서 삽입과 오프라인 | failure-mode | 오프라인 문서에는 연결 코드 블록이 없어 인물 그림 삽입 지점이 없다 |
| lens-adversarial | 검사기 변경 · 목록 이중 유지 | over-engineering | 두 목록을 손으로 유지하고 시험으로 불일치를 잡는 대신 한쪽을 생성할 수 있다 |
| lens-adversarial | 인물 그림 · 원본 보관 | irreversible | 원본을 다시 구할 주소·파일 이름·체크섬이 저장소에 없다 |
| lens-fit | 가정과 위험, 인물 그림 절의 불릿 | style | 불릿 한 항목이 여러 문장이다(`BULLET-SCOPE`) |
| lens-fit | 인물 그림 · 데이터 생성 | style | 연결어미 뒤 쉼표가 한 문장에 둘이다(`COMMA-CUT`) |
| lens-fit | 애니메이션 목록 표 · 내용 신호 열 | style | '분해 합산' 행만 서술형으로 끝난다(`ONE-ENDING`) |

## 겹침과 상충

둘 이상의 렌즈가 같은 곳을 함께 잡은 지적은 없다. 같은 위치를 두고 한쪽은 고치라 하고 다른 쪽은 그대로 두라는 상충도 없다. `lens-grounding`이 지적 없음을 돌려준 절(인물 그림, 검사기 변경)에 다른 렌즈의 지적이 있으나, 사실 일치와 설계 공백은 보는 대상이 달라 상충이 아니다.

## 커버리지 공백

이 spec의 위험(외부 자산, 정규식 검사기, 겹침 판정)에 비추어 볼 렌즈는 모두 실행되었다. 더 호출할 렌즈는 없다.

## 합치기에서 거른 지적

`lens-consistency`의 drift 지적(`think` 호출 인자) 하나를 근거 부족으로 걸렀다. `report-charts.js`의 선언은 `think: function (tl, person, question, at)`이고 `at`은 생략할 수 있는 위치 인자다. 기존 견본 `tests/sample-viz.html`도 `fx.think(tl, ic.who, ic.ask)`로 세 인자만 넘겨 동작한다. 그래서 '인자 개수가 다른 호출을 만든다'는 결과가 따라 나오지 않는다.

`lens-grounding`이 notes에 적은 '원본 `02-과정과-결론.html`이 폴더에 없다'는 지적 대상 문서의 문제가 아니다. 확인해 보니 그 파일은 2026-09-29 17:29에 휴지통으로 옮겨져 있었고, 이 사실은 사용자에게 따로 알렸다.
