# 보고서 시각화 확장 plan 리뷰 기록

대상: `docs/superpowers/plans/2026-09-29-report-visualization.md`(커밋 662f4b9). 이 파일이 `docs/superpowers/plans` 아래에 있어 plan으로 구분했다. 렌즈 원본은 같은 이름의 폴더에 있다.

## 실행 조건

렌즈 네 개(`lens-grounding`, `lens-consistency`, `lens-adversarial`, `lens-fit`)를 읽기 전용 에이전트로 따로 실행했다. 렌즈를 한 번씩만 실행했다. 금지어는 렌즈 전에 plan 산문과 코드 블록 안 한국어 문안을 `check.py`의 금지어 검출로 기계 검사했고 0건이었다.

`lens-prior-art`는 붙이지 않았다. plan에는 선행연구 렌즈를 제안하지 않는다는 규칙에 따랐다.

네 렌즈 모두 `principles_applied`를 채웠다.

## 합친 지적 목록

아래 목록은 렌즈 지적을 합친 결과다. 괄호 안은 지적한 렌즈다.

- **견본 라벨 위반 (grounding):** p1 핵심 수치 이름 '시험 페이지'가 라벨 규칙의 문장 어미 정규식(끝 글자 '지')에 걸려 Task 5 Step 6의 '위반 0건' 기대가 틀린다.
- **견본 금지어 (grounding, adversarial):** p2 문장의 '밑돌았습니다'가 금지어 '돌았'에 걸린다.
- **인쇄 폭 가정 (grounding):** zrender SVG 렌더러가 svg를 고정 px 폭 div로 감싸므로 `.viz svg{max-width:100%}`만으로는 인쇄 폭에 맞춰 줄지 않는다. zrender가 viewBox를 이미 두므로 `fit()`은 효과가 없다.
- **check.py 줄 위치 (grounding):** 모듈 설명의 바꿀 문장은 2행이 아니라 4행이다.
- **Task 2 실패 예상 목록 (grounding notes):** 수정 전에는 `test_banned_word_in_script_string`도 실패한다.
- **spec과 다른 선언 없는 설계 (consistency):** BEGIN 표시 버전의 출처, 마름모 노드 허용, GSAP 부재 시 단계 목록 표시, `play`의 두 번째 인자 `$`, 색 리터럴 검출 범위 축소, `tests/test_build.py`와 `.gitignore` 추가, SKILL.md description 변경, 스킬 동작 시험 프롬프트의 추가 지시가 spec과 다르지만 선언이 없다.
- **장식 금지 문안 누락 (consistency):** SKILL.md 문안에 3D·계열마다 채도 높은 색 금지와 `LABEL-NOUN` 언급이 빠졌다.
- **대체 방식 인용 오류 (consistency):** Task 1이 spec에 없는 '페이지가 보일 때 그리기'를 spec의 결정으로 인용한다.
- **수정 지점 오기 (consistency, fit):** Task 1이 `$` 함수를 Task 4 Step 3에서 고치라고 가리키지만 코드는 Step 1에 있다.
- **셸 변수 `E` (consistency, adversarial):** Task 5 Step 9가 Step 7에서만 정의한 `$E`를 쓴다.
- **단계 표시 되돌림 (consistency, adversarial notes):** tweenTo 도중 onUpdate가 단계 표시를 앞 번호로 잠깐 되돌리고, 동작 시험 4번은 전환이 끝난 뒤 값을 보지 않는다.
- **인쇄 목록 줄 수 (consistency):** p5 동작 예시가 두 개라 단계 목록은 여섯 줄이다.
- **차트 애니메이션 정상 견본 (consistency):** `script_violations`로 `animation:false`를 판정하는 정상 견본 시험이 없다.
- **재생 버튼 무시 (adversarial):** '다음' 뒤 `tw`가 남아 첫 '재생' 클릭이 `stop()`만 실행한다.
- **RC.demo 예외 격리 (adversarial):** `play()` 예외가 RC.ready 안에서 조용히 삼켜져 동작하지 않는 버튼만 남는다.
- **RC.chart 예외 격리 (adversarial):** 상자가 없거나 옵션이 잘못되면 문서 스크립트 전체가 멈춘다.
- **RC.color 빈 값 (adversarial):** 없는 토큰 이름에 빈 문자열을 오류 없이 돌려주고, SKILL.md 이름 목록이 '등'으로 열려 있다.
- **가정 확인 파일 (adversarial, grounding notes):** 숨은 요소와 보이는 요소의 글자가 같아 글꼴 조각 로드 조건을 재현하지 못하고, `[ ]` 노드의 rect 존재를 측정하지 않는다.
- **서버 수명 (adversarial):** 서버를 Task 1에서 켜고 Task 7에서 꺼, 과제를 따로 실행하면 Task 5에 서버가 없을 수 있다.
- **시험 시간 의존 (adversarial):** 동작 시험 식이 RC.ready를 기다리지 않는다.
- **shadowBlur 0 (adversarial):** 그림자를 끄는 `shadowBlur: 0`도 위반으로 검출된다.
- **원본 스크립트 위반 (adversarial):** 기존 HTML 수정 작업에서 원본에 있던 스크립트 위반을 새 위반과 구분하지 않는다.
- **연결 코드 없는 RC 호출 (adversarial):** 시각화가 없는 문서의 문서 스크립트 삭제 지시가 없고, build.py가 연결 코드 없이 RC를 호출하는 문서를 통과시킨다.
- **설치 스킬 직접 수정 (adversarial):** Task 5와 Task 6 커밋 사이에 템플릿과 SKILL.md가 서로 다른 규격을 가리키는 상태가 생긴다.
- **SKILL.md 문안 문체 (fit):** 기존 칸에 붙일 문장의 마침표 누락, '플로우 차트'와 '도식' 혼용, '도표'·'차트 제목'·'시각화' 관계 미정의, 세 문장 불릿, '기준표' 미정의가 있다.
- **확인 단계 부족 (fit):** Task 6의 문서 치환 단계에 확인 명령이 없고, 로드 실패 시험의 차트 확인과 Task 7 캡처에 식과 명령이 없다. Task 5 Step 7·9의 기대 결과 단락이 네 문장을 넘는다.

## 상충과 커버리지 공백

상충은 없다. 같은 지점을 두 렌즈가 다룬 곳(인쇄 폭, 셸 변수, 수정 지점, 단계 표시 되돌림)은 방향이 같다.

커버리지 공백은 하나다. Chromium에서 CSS `rx`·`ry`가 Mermaid 노드 rect에 적용되는지와 GSAP `tweenTo`의 `onComplete` 인자 동작은 grounding 렌즈가 알려진 API와 모순이 없다고만 적었고, 소스로 대조한 렌즈는 없다.
