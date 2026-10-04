# C3 보고서 내용 규격 plan 리뷰 기록

검토 대상은 `docs/superpowers/plans/2026-10-04-c3-content-rules.md`이고, 렌즈별 원본은 같은 이름의 폴더에 있다. 경로가 `docs/superpowers/plans` 아래이므로 plan으로 판정했다.

## 실행 개요

렌즈는 lens-grounding, lens-consistency, lens-adversarial, lens-fit을 읽기 전용 Plan 에이전트로 따로 실행했다. 렌즈를 한 번씩만 실행했다. 선행연구 렌즈는 붙이지 않았다. 대상이 plan이라 제안 대상이 아니기 때문이다. 이 세션의 권한 판정이 `template-paged.html`, `eval/prompts/checklist-review.md`, `eval/checklist_vote.py` 읽기를 거부해 렌즈에게도 읽지 말라고 지시했다.

## 병합한 지적

- **C2 병합 뒤의 템플릿:** C2가 `template-paged.html`에 `p.sec`를 넣으면 그 템플릿은 새 규약 문서가 된다. '두 템플릿은 새 규약 문서가 아님' 전제와 `FixedNoFalsePositive`가 병합 뒤 깨질 수 있다. (consistency, adversarial 공동)
- **거부된 파일을 읽는 시험:** `FixedNoFalsePositive`와 Task 7 Step 3 스크립트가 `template-paged.html`을 읽어 Global Constraints의 '읽지 않는 파일'과 부딪친다. (fit, adversarial 공동)
- **옛 규칙 grep 패턴:** `TITLE-CLAIM보다`는 SKILL.md 실제 문장과 글자가 달라 개정 전에도 출력이 없다. (grounding, consistency 공동)
- **목차 별 표시 방법:** Task 6 Step 1은 ★·☆ 기호로, Step 3은 `class="core"`·`"key"`로 지시한다. 별 문자를 직접 쓰면 이모지 위반이다. (grounding, fit 공동)
- **SKILL.md의 일반 불릿:** 원본 기준·대체됨 배너·원격 게시·질문과 용어 먼저를 SKILL.md 일반 불릿으로 넣으면 spec의 '마무리 보고서를 새로 만들 때만'과 규칙 문서 배치 원칙에 어긋나고 두 문서에 중복된다. (consistency)
- **해시 조건의 설명 불일치:** 마무리-보고서.md 문장은 '7자 이상 16진수', 구현은 7~40자 소문자다. (consistency)
- **페이지 이름 설명:** SKILL.md에 'h2에서 읽는다'고 쓰게 하지만 `page_name`은 첫 h1·h2를 읽는다. (consistency)
- **새 규약이 아닌 문서 시험:** 필수 절·원본 기준 시험의 `test_not_wrapup`은 `.sec`이 있는 문서를 쓰고, `.sec`도 표시도 없는 문서 입력은 없다. (consistency)
- **리포트 단계와 세 번째 차례 처분:** 리포트 항목을 모으는 단계, 리뷰 마커, 세 번째 자가 점검 미달의 처분이 없다. Task 7에 Interfaces와 커밋이 없다. (consistency, fit 공동)
- **Task 1 기대 결과와 남는 줄:** PageName 시험의 실패 양상이 Step 2 기대와 다르고, `page_violations`의 `h` 대입 줄이 쓰이지 않은 채 남는다. (grounding)
- **'풀이(약어)' 형식:** '상장지수펀드(ETF)'처럼 풀이 뒤 괄호 속 약어가 위반으로 잡힌다. (adversarial)
- **실제 글의 약어 오탐률:** 판별이 켜진 실제 글에서 약어 규칙이 몇 건을 내는지 재는 단계가 없다. (adversarial)
- **견본 스크립트 측정:** 손으로 쓴 페이지 전환 스크립트를 어느 단계도 측정하지 않는다. (adversarial, fit 공동)
- **자가 점검의 수정 대상:** '아니오' 이유로 규칙 문서까지 고치게 해 견본 하나에 맞춘 규칙이 생길 수 있다. (adversarial)
- **검토자 지시문:** 목적을 드러내지 않는 고정 지시문이 없고, 공식 프롬프트와 다르다는 기록도 없다. (adversarial)
- **`data-part` 속성 순서:** 필수 절 검사는 어느 `section`의 `data-part`든 세지만 `PAGE_ID`는 `class`·`id` 순서만 페이지로 본다. 순서가 틀린 페이지가 소리 없이 빠진다. (adversarial, fit 공동)
- **원본 기준 판정의 느슨함:** 숫자만 된 7자 이상 수와 'e.g'·'Node.js'도 통과한다. (adversarial)
- **글 추출 사본:** `ProseText`의 합치기는 `common.visible_text`가 이미 한다. (adversarial)
- **확인 방법 없는 단계:** Task 4 절 제목, Task 5 새 문구, Task 6 C2 클래스와 스크립트 동작을 확인하는 명령이 없다. Task 5 Step 2의 개정 전 값을 얻는 방법이 없다. 기대 출력 문자열이 세 곳에서 다르다. '후보' 불릿과 「독자 구분」 구절의 글이 정해지지 않았다. (fit)
- **문체:** '원본' 한 낱말이 두 개념을 가리킨다. 금지어 '경우'·'더해'. 개수로 가리키기, 관형절, 수식어 중첩, 여러 문장 불릿. (fit)

## 걸러 낸 지적

없다.

## 커버리지 공백

aggregating-lenses 기준으로 아무 렌즈도 보지 않은 차원은 없다. 다만 `template-paged.html`의 실제 내용은 모든 렌즈가 읽지 않았다.
