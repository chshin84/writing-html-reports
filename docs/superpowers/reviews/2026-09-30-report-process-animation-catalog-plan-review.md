# 보고서 작성 과정과 애니메이션 목록 구현 계획 리뷰

검토 대상은 `docs/superpowers/plans/2026-09-30-report-process-animation-catalog.md`이고, 경로가 `docs/superpowers/plans` 아래라 plan으로 판정했다. 짝 spec은 `docs/superpowers/specs/2026-09-30-report-process-animation-catalog-design.md`다. 렌즈 네 개(`lens-grounding`, `lens-consistency`, `lens-adversarial`, `lens-fit`)를 따로 실행했고, 렌즈별 원본은 같은 이름의 폴더에 있다.

렌즈를 한 번씩만 실행했다.

선행연구 렌즈(`lens-prior-art`)는 plan에는 제안하지 않는다는 규칙에 따라 제안하지 않았다.

네 렌즈 모두 `principles_applied`와 `read`를 채웠다. `lens-fit`의 `doc_type`은 '설계(plan)' 행으로 채워졌다.

## 지적 목록

| 렌즈 | 위치 | 유형 | 지적 |
|---|---|---|---|
| lens-grounding | 작업 7 Step 4 | omission | SKILL.md의 '동작 예시' 표현 7곳(시각화 절, 기준표, 함수 표 제목, RC.check 설명 등)을 계획이 고치지 않는다 |
| lens-grounding | 작업 1 Step 4 | mismatch | 생성물 크기 기대값 95,000바이트 안팎이 실제 실행값 91,486바이트와 다르다 |
| lens-grounding | 작업 3 Step 3 | contradiction | 원본 비교 방식이 기존 `script_violations`(콜론 앞 규칙 이름 일치)와 다르게 문구 전체 일치다 |
| lens-consistency | 작업 2 Step 4 | drift | 새 주석이 '동작 예시 아이콘'이라는 옛 이름을 쓴다 |
| lens-consistency | 작업 7 Step 4 | drift | '동작 예시 함수는 다음과 같다' 표 제목이 남는다 |
| lens-consistency | 작업 7 Files | scope | 보고서-규격.md '움직임' 행이 사라지는 '동작 예시' 절을 가리킨다 |
| lens-adversarial | Review Focus·작업 5 Step 5 | risk | 어두운 화면 확인이 스틱맨 한 가지만 본다 |
| lens-adversarial | 작업 1 | risk | 생성한 스틱맨이 사람 모양인지 눈으로 확인하는 단계가 없다 |
| lens-adversarial | 작업 2 Step 5 | failure-mode | 작업 2와 작업 5 사이 세 커밋 동안 구조 견본 배치가 깨진 채 남는다 |
| lens-adversarial | 작업 5·6 겹침 판정 | risk | 스틱맨 경계가 80×80 사각형으로 판정되는 점과 조정 반복 상한이 계획에 없다 |
| lens-adversarial | 작업 8 Step 6 | failure-mode | 정리 대상 파일이 계획 안에서 만들어지지 않아 출처가 불명확하다 |
| lens-fit | Global Constraints '스틱맨 배치' | style | 등식이 문장을 대신한다(`FULL-SENTENCE`) |
| lens-fit | Review Focus 다섯 항목 | style | 화살표가 문장을 대신한다(`FULL-SENTENCE`) |
| lens-fit | 작업 7 Step 3 문단 끝 문장 | style | 한 문장에 지시 세 가지(`ONE-IDEA`) |
| lens-fit | 작업 7 Step 3 문단 | style | '본문 불변 원칙'에 풀이가 없다(`TERM-EXPLAIN`) |

## 겹침과 상충

'동작 예시' 옛 용어 문제를 세 렌즈가 함께 잡았다. `lens-grounding`(SKILL.md 7곳), `lens-consistency`(report-charts.js 주석, SKILL.md 함수 표 제목, 보고서-규격.md '움직임' 행)이다. 같은 위치를 두고 고치라는 쪽과 두라는 쪽이 부딪치는 상충은 없다.

## 커버리지 공백

이 plan의 위험(생성물의 시각 품질, 커밋 사이의 깨진 상태, 브라우저 판정)에 비추어 볼 렌즈는 모두 실행되었다. 더 호출할 렌즈는 없다.

## 합치기에서 거른 지적

거른 지적은 없다. `lens-grounding`의 원본 비교 방식 지적은 근거가 서 있다. spec 본문은 '같은 문구로 검출된 위반'이라 적었고 plan 코드도 문구 일치를 쓰지만, spec의 '기존 `script_violations`와 같은 방식' 표현과는 실제 코드가 다르다.
