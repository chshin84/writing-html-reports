# C1 애니메이션 엔진 plan 리뷰 기록

검토 대상은 `docs/superpowers/plans/2026-10-04-c1-animation-engine.md`이고, 렌즈별 원본은 같은 이름의 폴더에 있다. 대상이 `docs/superpowers/plans` 아래이므로 plan으로 판정했다.

## 실행 개요

렌즈는 lens-grounding, lens-consistency, lens-adversarial, lens-fit을 읽기 전용 Plan 에이전트로 따로 실행했다. 렌즈를 한 번씩만 실행했다. 선행연구 렌즈는 붙이지 않았다. plan에는 제안하지 않는다는 규칙에 따랐다.

## 병합한 지적

- **빌드 중 seek의 부작용:** 단계마다 주 타임라인을 옮겨 표본을 모으면, 다음 단계의 빌드 시점 `gsap.set`(`RC.fx.pop`·`RC.fx.draw`)이 렌더 사이에 끼어 같은 요소를 여러 단계에서 다루는 문서에서 되감기 상태가 틀어질 수 있다. (adversarial, consistency 공동)
- **viewBox 넓히기의 spec 이탈:** spec은 표시 범위 안의 쪽만 고르고 자리가 없으면 자막을 보이라고 정한다. plan은 범위를 넓힌다. 근거로 든 '04-rules 위쪽 노드에 자리가 없다'는 실측이 아니고, 노드 S는 아래쪽에 자리가 있을 수 있다. 넓히면 1280 폭에서도 글자가 줄 수 있다. (consistency, grounding, adversarial 공동)
- **spec 문구와 다르게 정한 결정:** 판정 스틱맨 색을 두 단계로 본 것, 현재 노드 표시를 Mermaid 노드로 한정한 것, 지나온 노드에서 작성자 강조색을 보조 강조색으로 바꾼 것, `data-rc-active`를 단계 시작에 단 것, 자동 스틱맨을 자동 설명 상자에 묶은 것, 시나리오 선택 시 곧바로 재생하는 것이 spec 문구와 다르거나 해석인데 리포트 기재 표시가 없다. (grounding, consistency 공동)
- **보임 판정의 정의 차이:** 엔진 `seen()`은 C0의 보임 판정과 달리 visibility·clip-path·면적·문서 루트까지의 불투명도를 보지 않는다. 엔진 n이 C0 n보다 커질 수 있다. (grounding, adversarial 공동)
- **자동 상자 계산의 예외 전파:** 배치 계산 예외가 작성자 play와 같은 try에 있어 figure 전체가 정적 목록으로 물러난다. (adversarial)
- **RC.check와 배치 판정의 차이:** 장애물을 단계 끝에만 모으고, 직접 그린 무대의 path를 점으로 본다. RC.check는 매 프레임과 경계 상자로 본다. (adversarial)
- **화면 안 스크롤:** 부드러운 스크롤이 측정 중에도 일어나고, figure가 조금만 겹쳐도 발동한다. 조건은 spec이 정했다. (adversarial)
- **at 인자의 의미 변화:** '<' 차이는 0.02초뿐이고, 숫자 절대 위치와 단계 사이 라벨의 의미가 바뀐다. 시각화.md를 고치지 않는다. (adversarial)
- **멈출 조건 없는 실패 처리:** Task 10·12의 실패 처리에 상한이 없어 고정 견본 맞춤으로 흐를 수 있다. (adversarial)
- **시험 코드의 호출 수:** `SampleSelfCheck`가 관리 블록 주석의 `RC.demo(`까지 세어 harness 준비 조건이 충족되지 않는다. (grounding)
- **산출물 공백:** 리포트를 쓰는 단계, 리뷰 마커, 엔진을 고친 뒤의 견본 재빌드가 빠졌다. 리포트 항목 이름이 spec의 '상위 설계와 다르게 정한 점'과 다르다. (consistency)
- **골격과 Task의 이름 불일치:** 골격에 루프 앞 변수 자리가 없고, `usePeep` 정의 순서가 정해지지 않았으며, Task 8 주석과 넣는 함수 이름이 다르고, `info` 필드 목록에 `note`·`think`가 없다. (consistency)
- **시험 공백:** 되감기 시험이 설명 상자 글만 보고, Task 11의 문장과 금지어 검사가 충돌한다('자리'). (consistency, fit 공동)
- **plan 형식:** Task 12의 자리표시 경로, Task 3의 코드 없는 CSS 지시, Task 11의 내용 없는 지시, Task 10 Step 2의 기대 결과, Task 12의 Interfaces·커밋 누락, Goal 범위. (fit)
- **문체:** 여러 문장 불릿, 목록 말끝 불일치, 문장 중간 관형절, 수식어 겹침, 용어 첫 풀이 누락, 개수로 가리키기. (fit)

## 걸러 낸 지적

없다. 모든 지적의 근거 줄을 열어 확인했다.

## 커버리지 공백

aggregating-lenses 기준으로 아무 렌즈도 보지 않은 차원은 없다. lens-consistency는 상위 설계와 `eval/motion.py`를 열지 않았으나, lens-grounding과 lens-adversarial이 두 파일을 읽었다.
