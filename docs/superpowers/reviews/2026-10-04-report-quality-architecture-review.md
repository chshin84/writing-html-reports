# 보고서 품질 개선 아키텍처 리뷰 기록

검토 대상은 `docs/superpowers/specs/2026-10-04-report-quality-architecture-design.md`이고, 렌즈별 원본은 같은 이름의 폴더에 있다.

## 실행 개요

렌즈는 lens-grounding, lens-consistency, lens-adversarial, lens-fit을 읽기 전용 에이전트로 따로 실행했다. 렌즈를 한 번씩만 실행했다.

선행연구 렌즈는 붙이지 않았다. 대상은 `docs/superpowers/specs` 아래 파일이라 spec으로 판정했다. 이 spec은 기존 스킬의 결함을 고치고 정리하는 설계라 발동 기준에 들지 않는다. 같은 날 사용자의 직접 요청으로 선행연구 렌즈 4개를 이미 실행했고, 그 결과가 이 spec의 근거다.

## 병합한 지적

지적 끝 괄호는 그 지적을 잡은 렌즈다. 둘 이상의 렌즈가 함께 잡은 지적은 '공동'으로 표시했다.

- **C1 대안 경쟁의 성격:** 두 대안의 차이는 엔진 품질이 아니라 기본 재생 방식이라는 사용자 경험 선택이다. 시나리오 분할을 선택 인자로만 구현하면 고정 견본에 나타나지 않는다. 단계 넘김 기본에서는 체류 시간 판정의 뜻이 사라진다. (adversarial, consistency 공동)
- **피평가자에게 시험지 노출:** 고정 질문·정답·심을 오류가 main에 들어간 뒤 워크트리를 만들므로 L2가 읽을 수 있다. (adversarial)
- **자기 측정:** 2·3층 점수를 L2가 측정해 리포트에 적으므로 원하는 결과까지 재측정할 수 있다. (adversarial)
- **컴포넌트별 적용 기준 부재:** C1·C2는 내용을 고칠 수 없는데 내용이 정하는 항목(약어 풀이, 고정 질문 100%, 심어 둔 오류, 논리·구성 체크리스트)이 그대로 걸린다. (consistency, adversarial 공동)
- **기계 판정 문턱값 부재:** 체류 시간, 설명 상자 거리, 대비, 390px 최소 글자의 수치가 없고 근거끼리 값이 다르다. (consistency, adversarial 공동)
- **재생성 절차 부재:** 고정 원자료의 경로·형태, 생성자, 생성 횟수, 개선 전 재생성 기준선의 생산자가 없다. 생성 편차를 통제하지 않는다. (consistency, adversarial 공동)
- **기준선 시점과 흔들림:** 기준선 측정 커밋이 두 절에서 다르게 읽힌다. 기준선을 한 번만 재면 항목별 우연한 하락으로 병합이 막힌다. C0 확인이 2·3층 도구의 흔들림을 재지 않는다. (consistency, adversarial)
- **check.py 분할의 공백:** 시험이 `check.*`를 직접 46회 부르므로 집계기만 남기면 깨진다. `banned_violations`·`preservation`·원본 대조 분기가 배정과 계약 밖이다. 애니메이션 개수 상한이 별 상한과 한 함수(`star_violations`)에 있다. '같은 개수로 통과'는 동작 보존을 증명하지 못한다. (grounding, adversarial)
- **소유권 공백과 겹침:**
  - `tests/test_check.py`·`tests/test_build.py`의 소유자가 없다. (grounding, consistency, adversarial 공동)
  - 관리 블록(css·js 사본)이 컴포넌트 경계를 넘는다. (grounding, consistency 공동)
  - 애니메이션 조작 UI CSS(`report-base.css` 110~117행)는 C2 소유인데 C1이 필요로 한다. (consistency)
  - SVG 글자 축소는 엔진(C1)에서 생기는데 C2에 배정되었다. (consistency)
  - '구조' 견본이 C2 소유 `tests/sample-viz.html`에 있다. (adversarial)
  - 사전 정리 행의 소유 파일이 실제 작업과 다르다. (consistency)
  - `examples/**`의 내용이 정해지지 않았다. (grounding)
  - `RC.focus`가 호환 목록에서 빠졌다. (grounding)
- **L1의 구현 겸직:** 차트 직접 이름표와 템플릿 견본 블록을 L1이 통합 때 구현해 평가를 거치지 않는다. (adversarial, consistency 공동)
- **견본 과적합:** 엔진이 견본 세 개에만 맞춰져도 기준을 넘는다. (adversarial)
- **미배정 개선안:** 결정 먼저, 원격 게시 전 공개 범위·민감 정보 점검, 삼중 반복 규칙, 긴 흐름도 높이·현재/지나온 노드 강조, 약어 추출 대조가 미배정이다. 본문 제목 결론 문장 기본값도 지적되었다. (consistency)
- **통합 기준이 느슨함:** 통합 확인이 '개선 전보다 높다' 하나이고 점수 정의가 없다. 제목 연결 문턱값이 없다. (consistency)
- **spec 작성 주체 모순:** 목적 절은 컴포넌트가 spec을 쓴다고 하고 실행 순서는 L1이 잠근다고 한다. (consistency)
- **비용 상한 부재:** L2마다 평가 재실행 횟수 상한이 없다. (adversarial)
- **근거 휘발:** 근거가 세션 스크래치에만 있다. (adversarial, fit 공동)
- **설치본 갱신 방법 부재:** 설치본은 사본이고 갱신 단위·되돌리는 방법이 없다. (adversarial)
- **근거 표기:** 8.96초는 실측 기준선 파일의 8.7초와 다르고, `RC.check` 통과와 40k 토큰의 출처가 없다. (grounding)
- **문체와 용어:** 개수 예고와 개수로 가리키기, L1·L2·L3·BLOCKED·RC·superseded·팬아웃 미풀이, 실행 순서 4·6단계 확인 방법 부재, 화살표 문장, 중간 관형절, 수식어 겹침, 쉼표 과다, 여러 문장 불릿, 캐릭터 이름 드리프트. (fit, consistency)

## 걸러 낸 지적

- **근거 표기 중 두 건:** 8.96초와 `RC.check` 통과는 세션에서 Playwright MCP로 직접 측정한 값이다(타임라인 8.96초, `pass: true`). 40k 토큰은 `nested-orchestration` 스킬 「가드레일」의 비용 항목에 실측값으로 적혀 있다. 근거는 있으나 문서에 출처를 밝히지 않은 점은 맞아, 출처 표기 지적으로 남긴다.
- **본문 제목을 결론 문장으로:** 절 제목은 명사구, 결론은 절 첫 문장이라는 사용자 원칙 `TITLE-LAYERS`를 따른 결과이므로 결함이 아니다.

## 커버리지 공백

aggregating-lenses 기준으로 아무 렌즈도 보지 않은 차원은 없다. lens-consistency는 개선안 이름(P1~P5)의 정의를 찾지 못해 초안의 A1~A4·B1~B3과 렌즈 지적으로 대신 대조했다고 밝혔다.
