"""보고서 규격 검사기.

사용법: python check.py <개선본.html> [원본.html]
규격 위반(만듦새)과 페이지형 문서의 근거 없는 페이지와 라벨(제목·표 머리·도표 제목)의 명사구 여부와 한국어 금지어와 시각화 스크립트·Mermaid 원문의 규격 위반을 검사하고, 원본이 있으면 내용 보존(본문 문장·숫자)도 검사한다.
원본이 있으면 원본에 이미 있던 금지어는 위반으로 세지 않고 참고로만 출력한다(본문은 고치지 않으므로).
위반이 하나라도 있으면 종료 코드 1을 돌려준다.
"""
import difflib
import re
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from checks import anim, common, content, style  # noqa: E402
from checks.common import SvgText, visible_text  # noqa: E402

# 규칙 모듈마다 RULES = [(규칙 함수, 원본 대조 방식)]. 새 규칙은 모듈의 RULES에 더하고 이 파일은 고치지 않는다.
# 대조 방식: plain 원본과 무관, prefix 원본에 같은 규칙 이름이 있으면 참고로만 출력,
# exact 원본에 같은 문장이 있으면 참고로만 출력, drop 원본이 있으면 결과를 참고로만 출력하고 비움(점수표 출력),
# old 원본을 함수에 넘김.
RULES = style.RULES + anim.RULES + content.RULES + common.RULES
NOTES = {"prefix": "참고: 원본에 있던 스크립트 위반(원본 스크립트는 고치지 않는다) — {}",
         "exact": "참고: 원본에 있던 애니메이션 위반(수정 작업이라 위반으로 세지 않는다) — {}",
         "drop": "참고: 핵심 페이지 표시가 평가와 다르다(수정 작업이라 위반으로 세지 않는다) — {}"}


def run_rule(fn, mode, new, old):
    if mode == "old":
        return fn(new, old)
    if mode == "drop":
        res = fn(new, show=True)
        if old is not None and res:  # 기존 문서 수정은 구조를 바꾸지 않으므로 점수표만 참고로 둔다
            print(NOTES[mode].format(res))
            return []
        return res
    res = fn(new)
    if old is None or mode == "plain":
        return res
    if mode == "prefix":
        old_rules = {f.split(":")[0] for f in fn(old)}
        kept = [f for f in res if f.split(":")[0] in old_rules]
    else:
        old_set = set(fn(old))
        kept = [f for f in res if f in old_set]
    if kept:
        print(NOTES[mode].format(kept))
    return [f for f in res if f not in kept]


def numbers(text):
    return Counter(re.findall(r"\d+(?:[.,]\d+)?", text))


def preservation(new_html, old_html):
    out = []
    a, b = visible_text(old_html), visible_text(new_html)
    ratio = difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()
    if ratio < 0.93:
        out.append(f"본문 글자 유사도 {ratio:.3f} (기준 0.93 이상)")
    old_n = numbers(a) + numbers(visible_text(old_html, SvgText))
    new_n = numbers(b) + numbers(visible_text(new_html, SvgText))
    lost = old_n - new_n
    if lost:
        out.append(f"사라진 숫자 {sum(lost.values())}개 — 예: {list(lost)[:8]}")
    return ratio, out


def main():
    new = Path(sys.argv[1]).read_text(encoding="utf-8")
    old = Path(sys.argv[2]).read_text(encoding="utf-8") if len(sys.argv) > 2 else None
    fails = []
    for fn, mode in RULES:
        fails += run_rule(fn, mode, new, old)
    if old is not None:
        ratio, lost = preservation(new, old)
        fails += lost
        print(f"본문 글자 유사도: {ratio:.3f}")
    print(f"[{Path(sys.argv[1]).name}] 위반 {len(fails)}건")
    for f in fails:
        print("  -", f)
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
