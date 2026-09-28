# 보고서 시각화 확장 설계 리뷰 기록

대상: `docs/superpowers/specs/2026-09-28-report-visualization-design.md`(커밋 e1299b7). 이 파일이 `docs/superpowers/specs` 아래에 있어 spec으로 구분했다. 렌즈 원본은 같은 이름의 폴더에 있다.

## 실행 조건

렌즈 네 개(`lens-grounding`, `lens-consistency`, `lens-adversarial`, `lens-fit`)를 읽기 전용 에이전트로 따로 실행했다. 렌즈를 한 번씩만 실행했다. 금지어는 렌즈 전에 `check.py`의 금지어 검출로 기계 검사했고 0건이었다.

`lens-prior-art`는 붙이지 않았다. 이 spec은 널리 쓰이는 라이브러리(ECharts·Mermaid·GSAP)를 기존 규격에 연결하는 작업이고, 되는지 자체가 미지수인 일이 아니라서 발동 기준에 해당하지 않는다고 판정했다.

네 렌즈 모두 `principles_applied`를 채웠다.

## 합친 지적 목록

아래 목록은 렌즈 지적을 합친 결과다. 괄호 안은 지적한 렌즈다.

- **움직임 규칙의 검사 범위 (grounding, consistency, adversarial):** 현재 `check.py`의 움직임 정규식은 CSS가 아니라 HTML 전체를 검사하므로 문서 스크립트의 `animation:false`도 위반으로 검출된다. spec의 '표시 밖 CSS의 움직임 금지'와 '차트 장식'의 `animation:true` 행이 이 동작과 맞지 않는다. 합치기에서 `check.py`의 해당 줄을 열어 사실로 확인했다.
- **근거 인정 행의 효과 (grounding, adversarial):** 기존 근거 정규식이 이미 `<figure`를 인정하므로 `class="mermaid"`·`class="viz"` 추가는 figure 없이 둔 도표만 통과시킨다.
- **CDN 버전 미측정 (grounding):** 채택한 echarts 6.1.0과 gsap 3.15.0의 jsDelivr 주소를 측정하지 않았고, 새 주 버전 회피 기준이 ECharts 6에는 적용되지 않았다.
- **`RC.color` 누락 (consistency, fit):** 구성 요소 표의 함수 목록에 `RC.color`가 빠져 있다.
- **시각화 점검의 적용 범위 (consistency):** 완료 기준의 '도표로 바꾸거나'가 기존 HTML 수정 작업에도 적용되어 새 문서 한정 결정과 상충한다.
- **`보고서-규격.md` 검출 목록 (consistency):** 새 검사 규칙이 '검사기가 검출하는 위반' 절에 반영되지 않는다.
- **`SKILL.md` 흔한 실수와 완료 기준 (consistency):** 두 번째 관리 구간의 원본 안내와 build.py 출력 문구가 갱신되지 않는다.
- **스크립트 위치와 실행 순서 (consistency, adversarial):** CDN 태그, report-charts 구간, 문서 스크립트의 위치와 순서가 정해져 있지 않다.
- **인쇄용 단계 설명 목록 (consistency):** `RC.demo` 인터페이스에 단계 설명 목록 요소가 없다.
- **인쇄의 `beforeprint` 의존 (adversarial, grounding notes):** 헤드리스 PDF 출력에서 `beforeprint`가 발생하는지 확인되지 않았고 `afterprint` 복원이 없다.
- **검증 공백 (consistency):** `RC.ma`, 움직임 줄이기 설정, 일시정지, 조작 버튼, 숨은 페이지의 ECharts, 수정한 검사 규칙에 검증 층이 없다.
- **JS 문자열의 금지어·라벨 (consistency, adversarial):** ECharts 제목·축·범례와 `RC.demo` 설명 문장이 금지어·라벨 검사 밖에 있고 검증 표에도 없다.
- **Mermaid 원문의 색과 모양 (consistency, adversarial):** `pre.mermaid`의 `style`·`classDef` 색과 둥근 노드가 어느 규칙에도 검출되지 않는다.
- **모듈 import 우회 (adversarial):** `<script type="module">`의 import 주소가 허용 스크립트·버전 고정 규칙을 통과한다.
- **Mermaid 자동 렌더와 글꼴 시점 (adversarial):** `startOnLoad:false`와 글꼴 로드 뒤 렌더가 정해져 있지 않다.
- **숨은 페이지의 동작 예시 (adversarial):** 페이지 복귀 시 재생 재개인지 정지 유지인지 정해져 있지 않다.
- **`data-h` (fit, adversarial):** 요청에 없는 높이 설정 경로다.
- **`borderRadius` 임계값 (consistency):** 차트는 1 이상, CSS와 SVG는 3 이상으로 임계값이 다르다.
- **`gsap.` 규칙의 이름과 범위 (consistency, adversarial):** `play(tl)` 콜백 안의 `gsap.set`도 '동작 예시 밖'으로 검출되고, `repeat: -1`처럼 공백이 있으면 검출되지 않는다.
- **다크 모드 전환 (adversarial, grounding notes):** 테마 색을 초기화 때 한 번 읽으므로 열람 중 테마 전환을 따라가지 않는다.
- **CDN 로드 실패 (adversarial):** 라이브러리 하나가 없으면 연결 코드 전체가 멈추고 도표가 빈 상자로 남는다.
- **과시각화 (adversarial, fit):** 기준표의 '해당 없음' 칸과 완료 기준의 설명 부담이 변환 쪽으로 기울게 한다.
- **옛 문서 재삽입 (adversarial):** build.py가 옛 문서에 새 연결 코드를 넣으면 옛 CDN 버전과 섞인다.
- **기준표 범위 (consistency, fit):** 캔들·산점도·상태 다이어그램 행은 사용자가 든 대상 목록에 없다.
- **스킬 동작 시험 (adversarial):** 재시도 상한이 없고 과시각화를 실패로 판정하지 않는다.
- **가정 확인의 판정 기준 (fit):** '도식 배치가 정상이다'가 약한 기준이다.
- **문체 (fit):** 표 열 네 곳의 말끝 불일치, 연결어미 쉼표 둘, 여러 문장 불릿, 문장 중간 관형절, 수식어 겹침, '요소'의 넓은 지칭, '근거 조건'·'문서 스크립트'·`.bars` 미풀이, '동작 예시'와 '단계 재생'과 '도표'의 용어 혼용이 있다.

## 상충과 커버리지 공백

상충은 하나다. `lens-adversarial`은 근거 인정 행을 삭제하자고 했고, `lens-consistency`는 같은 행에 단위 시험이 없다고 지적했다. 두 지적은 같은 행을 두고 삭제와 보강으로 방향이 다르다.

커버리지 공백은 둘이다. GSAP 무료 사용 조건 같은 라이선스 사실은 spec에 적혀 있지 않아 어느 렌즈도 보지 않았다. 헤드리스 Edge의 `beforeprint` 발생 여부는 두 렌즈가 가정으로만 언급했고 측정한 렌즈는 없다.
