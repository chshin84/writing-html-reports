# C0 평가 하네스 spec 리뷰 기록

검토 대상은 `docs/superpowers/specs/2026-10-04-c0-eval-harness-design.md`이고, 렌즈별 원본은 같은 이름의 폴더에 있다.

## 실행 개요

렌즈는 lens-grounding, lens-consistency, lens-adversarial, lens-fit을 읽기 전용 에이전트로 따로 실행했다. 렌즈를 한 번씩만 실행했다. 선행연구 렌즈는 붙이지 않았다. 이 spec은 상위 아키텍처 설계가 정한 측정 도구를 구현하는 컴포넌트 설계라 발동 기준에 들지 않는다.

## 병합한 지적

- **실현 가능성 기준의 모순:** 현재 엔진은 1단계를 생략하고 재생 방식 인자를 무시하므로 최소 견본이 step1·step-anim을 통과할 수 없다. 공유 타임라인에서 dwell과 step-anim을 함께 맞추면 단계 글 12자 이하 제약이 생긴다. (consistency, adversarial, grounding 공동)
- **체류 시간 측정:** `.cnt` 간격은 연출과 머묾의 합이라 머문 시간 0도 통과한다. `.cnt`·`.demo-cap`은 계약 밖이고, 페이지형 견본에는 페이지 넘김의 `.cnt`가 앞선다. n의 정의(차집합 방식, 보이는 기준, 공백 제외)가 모호하다. 벽시계 측정은 병렬 부하에서 흔들린다. (adversarial, grounding, consistency 공동)
- **방식별 항목:** `--mode`마다 어떤 항목을 실행하는지 없다. (consistency, grounding 공동)
- **거짓 통과 경로:** 엔진이 깨져 정적 목록으로 물러난 문서를 '해당 없음'으로 통과시킨다. CDN·글꼴 실패와 측정 시작 조건이 없다. build.py 실패가 전달되지 않는다. 규칙 항목이 피평가 컴포넌트 소유 검사기를 쓴다. (adversarial)
- **글자 크기:** `foreignObject` 안 HTML 글자(Mermaid 노드 이름표, 설명 상자)가 두 글자 크기 항목 사이에 빠진다. (adversarial, grounding 공동)
- **대비:** SVG 글자 바탕 추정, 어두운 테마 전환 방법이 없다. 큰 글자 3:1 완화와 토큰 기반 그래픽 대비가 상위 설계와 다른데 표시하지 않았다. ECharts가 SVG로 그려 그래픽 대비를 DOM에서 잴 수 있다. (adversarial, consistency, grounding)
- **설명 상자 판정:** 간선 경계 상자 겹침 판정과 자기 자신 제외, 측정 전 스크롤 정책이 없다. data-rc-active가 있는데 설명 상자가 없는 실패 경로를 검증하지 않는다. (adversarial, consistency, grounding)
- **표와 페이지 틀:** session-report의 표는 모두 스크롤 상자 안이라 table-col-390으로 결함을 잡지 못한다. 페이지 전환 스크립트는 관리 블록 밖이라 고정 견본으로 C2의 hash-nav 개선을 잴 수 없다. page-number가 애니메이션 `.cnt`와 본문 분수를 오탐한다. (grounding, adversarial)
- **규칙 항목 대응:** C3의 check.py 전 규칙을 지목할 플래그가 없고, 금지어 검사의 귀속이 없다. '애니메이션 항목' 하위 집합이 정의되지 않았다. (consistency)
- **체크리스트:** 이진 3회에서 '2회 미만 일치'는 불가능한 조건이다. 보정이 한쪽 방향이고 상한이 없다. 출력 형식·다수결 집계·충족률 분모·기준선 저장 형태가 없다. 기준선 결함 일부는 고정 견본이 아닌 03-groups.html에만 있다. (adversarial, consistency, fit)
- **산출물과 범위:** 쌍대 판정 틀은 소비자가 없다. rebuild.py의 명령 형식과 bench 불변 조건이 빠졌다. rebuild·shoot·prompts의 검증 기준이 없다. (consistency, adversarial, fit)
- **문체와 용어:** 개수 예고, 내부 이름 미풀이, 표 셀 말끝, 여러 문장 불릿, 중간 관형절, 수식어 겹침. (fit)

## 걸러 낸 지적

없다. Mermaid 노드 이름표가 `foreignObject`라는 렌즈의 가정은 L1이 Playwright로 확인했다(04-rules의 d-flow에 foreignObject 20개, text 0개).

## 커버리지 공백

aggregating-lenses 기준으로 아무 렌즈도 보지 않은 차원은 없다.
