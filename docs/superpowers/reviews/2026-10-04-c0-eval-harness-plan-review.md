# C0 평가 하네스 plan 리뷰 기록

검토 대상은 `docs/superpowers/plans/2026-10-04-c0-eval-harness.md`이고, 렌즈별 원본은 같은 이름의 폴더에 있다. 경로가 `docs/superpowers/plans` 아래이므로 plan으로 판정했다.

## 실행 개요

렌즈는 lens-grounding, lens-consistency, lens-adversarial, lens-fit을 읽기 전용 Plan 에이전트로 따로 실행했다. 렌즈를 한 번씩만 실행했다. 선행연구 렌즈는 붙이지 않았다. 대상이 plan이라 제안 대상이 아니기 때문이다.

## 병합한 지적

- **실현 가능성의 1단계 제외:** spec은 최소 견본의 `dwell`을 1단계 제외로 판정하라는데, `motion.py`는 모든 단계를 판정하고 plan은 1단계 패딩을 고치라고 한다. (grounding, consistency 공동)
- **sample-anim 막대 대비의 설명:** `C.graphics`는 SVG `rect` 막대를 모으지 않으므로 통과는 측정 대상이 없어서다. '약 3.24:1'은 3.249를 버린 값이다. (grounding, consistency 공동)
- **고정 견본의 hash-nav:** spec은 기록만 하라는데 gates.py는 종료 코드에 넣고 구분 표시가 없다. (grounding, consistency notes)
- **기계 판정 기준선 횟수:** 상위 설계는 C0이 고정 견본 기준선을 3회 측정한다고 적는데 plan은 방식마다 1회다. (grounding)
- **반투명 글자의 측정 불가:** 불투명도 0.999 미만 글자를 측정 불가로 처리해 spec보다 넓고, 모든 글자를 측정 불가로 만들어 통과하는 경로가 생긴다. (consistency, adversarial 공동)
- **아이콘 제외 범위:** spec은 스틱맨만 빼는데 plan은 `.rc-icon` 전체를 뺀다. (consistency)
- **`--base-checks`의 금지어.md:** 부모 폴더에 금지어.md가 없으면 `banned_violations`의 출력이 RUNNER의 JSON을 오염시켜 실패하거나, 검사가 조용히 빠진다. (consistency, adversarial 공동)
- **`seconds`의 이름:** 단계 타임라인 길이를 체크리스트와 프롬프트는 '머무는 시간'이라 부른다. (consistency)
- **방식 때문에 재지 않는 항목:** n/a로 기록하는 선택이 해석 절에 없다. (consistency)
- **리포트 단계 공백:** 산출 계약의 리포트를 만드는 단계와 경로가 없다. (consistency, fit 공동)
- **보정 뒤 다수결:** recal 폴더를 묶는 명령과 병합 규칙이 없고, 표시된 견본만 다시 측정하면 견본마다 문구가 달라진다. (consistency, adversarial 공동)
- **스크롤 상자 시험:** 스크롤 상자 판정의 브라우저 시험이 없고 표 시험은 아무것도 판정하지 않는다. (consistency)
- **기준 커밋 대체 경로:** 코드가 다를 때 실행할 수단이 없고 워크트리를 지우는 단계가 없다. (consistency, adversarial 공동)
- **peeps 대조와 괄호 주의:** rebuild의 peeps 대조가 해석 절에 없다. 괄호 주의 문단과 코드가 다르다. (consistency)
- **단계 이동 방식:** `seek`만 쓰면 버튼 핸들러의 스크롤이 반영되지 않고 고정 300ms가 부드러운 스크롤에 짧다. (adversarial)
- **보임 판정:** clip-path, scale 0, 면적 0, 투명 글자색을 보이는 것으로 센다. (adversarial)
- **현재 노드 여럿:** `data-rc-active`가 여럿이거나 설명 상자 안에 있으면 거짓 판정이 난다. (adversarial)
- **SVG 밖 설명 상자 글자:** 단계마다 재는 글자 크기에서 빠진다. (adversarial)
- **렌더 실패와 같은 출처 404:** Mermaid 렌더 실패를 환경 실패로, 로컬 404도 환경 실패로 분류한다. (adversarial)
- **처리되지 않은 예외:** EnvFail 밖의 예외가 종료 코드 1과 겹치고 앞 기록이 사라진다. (adversarial)
- **피평가 checks.common 의존:** 해당 없음 판정이 피평가 워크트리의 `checks/common.py`에 기댄다. (adversarial)
- **측정기 위조 경로:** `_rcTl`·realm 위조, 측정 불가 유도, 벽시계 부하는 완화만 가능하다. (adversarial)
- **스크롤 상자의 hidden:** `overflow-x:hidden`도 스크롤 상자로 본다. (adversarial)
- **ECharts 내부 API, pointer-events, 세션 정리:** 내부 API 실패의 조용한 통과, `elementsFromPoint`의 pointer-events 누락, `pw.stop()` 누락. (adversarial)
- **검토자 독립성:** 스크래치 경로가 저장소 이름을 드러내고, known-defects.json을 검토 전에 쓰며, 최소 견본 본문이 목적을 드러낸다. (adversarial)
- **명령과 시험 세부:** PowerShell 리디렉션, `--bench`의 명령줄 노출, 도형 바탕 시험의 글자색, 숨은 페이지 SVG 시험 누락, 열린 페이지 검사 누락. (adversarial, grounding, consistency)
- **소유 범위 문장:** Global Constraints가 spec보다 소유 범위를 넓게 적는다. (consistency)
- **문서 형식:** 확인 방법 없는 단계, `<스크래치>` 미정의, 조정 규칙 없음, Task 9·10 Interfaces 누락, '잰다', `A가 아니라 B` 두 번, 여러 문장 불릿, 개수 예고, 용어 혼용(도형·노드, 설명 글, 기준선, 상태값, 장면·스크린샷), 용어 미풀이, 관형절, 체크리스트 해당 없음 문장 불일치, 표 열 형식, 기호 문장, 출처 없는 기대값, `--base-checks` 사용처. (fit)

## 걸러 낸 지적

- **`--base-checks`의 YAGNI(fit):** spec 「기계 판정」이 이 인자를 요구하고 L1 공식 측정이 쓴다. 근거가 서지 않아 걸렀다. 사용처는 plan 본문에 spec 조항으로 연결한다.

## 커버리지 공백

aggregating-lenses 기준으로 아무 렌즈도 보지 않은 차원은 없다.
