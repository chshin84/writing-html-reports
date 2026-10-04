# C3 보고서 내용 규격 spec 리뷰 기록

검토 대상은 `docs/superpowers/specs/2026-10-04-c3-content-rules-design.md`이고, 렌즈별 원본은 같은 이름의 폴더에 있다.

## 실행 개요

렌즈는 lens-grounding, lens-consistency, lens-adversarial, lens-fit을 읽기 전용 에이전트로 따로 실행했다. 렌즈를 한 번씩만 실행했다. 선행연구 렌즈는 붙이지 않았다. 상위 설계가 정한 내용 규칙을 구현하는 컴포넌트 설계이고, 근거가 된 선행연구 대조(결정 메모·ADR·확인 상태 표시)는 같은 날 마쳤다.

## 병합한 지적

- **약어 검사의 오탐:** 고정 견본에는 풀이 없는 대문자 토큰이 견본마다 9~14종 있다(Mermaid의 LR·TD, 노드 id, 파일 이름 조각, 원칙 식별자, HTML·JSON 같은 원어). 측정 도구는 원본 없이 규칙을 실행하므로 원본 대조 보호가 없고, 최종 통합의 `rules-all`이 고정 견본에서 실패한다. 본문 범위와 제외 규칙이 없다. '`.note`의 용어:'는 근거 없는 관행이다. (grounding, consistency, adversarial 공동)
- **C2 미병합 상태의 검증:** C3 워크트리에는 결론 제목 규칙이 없어, 새 페이지 구성 견본이 현재 라벨 검사에서 위반된다. (consistency)
- **old 방식의 오해:** check.py의 `old`는 원본을 넘기기만 하고 제외는 함수 몫이다. 원본이 없을 때 None 처리도 필요하다. (grounding, consistency, adversarial 공동)
- **필수 절과 마무리 보고서 판별:** 필수 절과 보고서 머리의 식별 마크업이 없다. 자가 표시(`data-kind`)에만 맡겨 빠뜨리면 검사가 꺼지고 붙이면 짧은 보고서가 비대해진다. 절 이름이 상위 설계('처음 요청 대비 달성')와 다르다. 결정 요청 절이 정할 사항인지 정한 사항 기록인지 섞인다. 권장안의 이유가 빠졌다(체크리스트 decision-recommend). (consistency, adversarial, grounding)
- **결정 먼저:** 사용자에게 물을 수 없는 생성자의 예외가 없다. (adversarial)
- **원본 기준과 대체됨 배너:** 커밋·spec으로만 한정해 데이터 파일 작업을 덮지 못한다. 배너를 누가 언제 다는지 없다. (adversarial)
- **확인 상태와 원자료:** 둘이 묶이지 않아 상태가 꼬리표가 된다. `infer`·`assume` 값은 C2 spec에 없다. (adversarial, consistency, grounding)
- **SKILL.md 개정 범위:** 다른 절의 `h2` 명사구 규정이 남는다. 시각화·스타일 규칙 포인터 조건이 없다. 마무리 보고서 전용 규칙이 모두 SKILL.md에 들어가 비대해진다. 새 작업 과정 규칙이 기존 HTML 수정 작업에 적용되는지 없다. (grounding, consistency, adversarial)
- **원격 게시 순서:** 확인 후 점검이라 점검 결과를 보기 전에 승인한다. (adversarial)
- **검증:** 자기가 쓴 견본 하나로만 검증한다. 바꾸는 기존 규칙의 시험, 이해도 기준값·하락 금지·판정 차례·3회째 미달 처리, 기준 규칙 제외 대상, 체크리스트 대응이 없다. (adversarial, consistency, fit, grounding)
- **근거 표현:** 사후 질문에 '결정할 것'은 근거 파일에 없다. (grounding)
- **문서 틀:** 산출 계약의 마커 값·리포트 비커밋·plan 리뷰 반영 항목, 원자료 이름 혼용, 절 첫 문장, 용어 미풀이, 여러 문장 불릿. (consistency, fit)

## 걸러 낸 지적

없다.

## 커버리지 공백

aggregating-lenses 기준으로 아무 렌즈도 보지 않은 차원은 없다.
