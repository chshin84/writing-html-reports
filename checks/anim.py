"""애니메이션·차트 스크립트 규칙. C1(애니메이션 엔진) 소유."""
import re

from checks.common import PAGE_ID, doc_scripts


def script_motion_violations(html):
    """차트 애니메이션, GSAP 직접 호출, 차트 장식."""
    js, out = doc_scripts(html), []

    def rule(name, hits):
        if hits:
            out.append(f"{name}: {len(hits)}건 — 예: {hits[0][:80]}")

    rule("차트 애니메이션", re.findall(r"animation\s*:\s*true", js))
    rule("GSAP 직접 호출(play(tl, $) 안에서는 tl.to·tl.set을 쓴다)",
         re.findall(r"\bgsap\.\w+", js) + re.findall(r"\b(?:repeat\s*:\s*-?\s*[1-9]|yoyo\s*:\s*true)", js))
    rule("차트 장식", re.findall(r"shadowBlur\s*:\s*(?!0+(?:\.0+)?(?![\d.]))[^,}\s]+", js)
         + [m for m in re.findall(r"borderRadius\s*:\s*(\[[^\]]*\]|[\d.]+)", js)
            if any(float(n) >= 3 for n in re.findall(r"\d+(?:\.\d+)?", m))])
    return out


def anim_count_violations(html):
    """파일당 애니메이션 상한. 3개 이하다."""
    demos = len(re.findall(r"\bRC\.demo\s*\(", doc_scripts(html)))
    return [f"애니메이션 {demos}개(3개 이하로 둔다)"] if demos > 3 else []


ANIM_TYPES = {  # 애니메이션 목록. 시각화.md '애니메이션' 절의 표와 같아야 한다(tests의 ListSync가 확인한다)
    "구조": "사용 가능", "전후 전환": "사용 가능", "규칙 적용 재생": "사용 가능",
    "선별": "견본 대기", "표본 누적": "견본 대기", "충격 적용": "견본 대기", "분해 합산": "견본 대기",
}
DEMO_ID = re.compile(r"\bRC\.demo\s*\(\s*document\.getElementById\(\s*['\"]([^'\"]+)['\"]\s*\)")


def anim_violations(html):
    """애니메이션 figure의 유형(data-anim)과 배치를 본다. 페이지 규칙은 페이지형 문서에만 적용한다."""
    scripts = doc_scripts(html)
    calls = len(re.findall(r"\bRC\.demo\s*\(", scripts))
    ids = DEMO_ID.findall(scripts)
    out = []
    if calls > len(ids):
        out.append(f"RC.demo 호출 {calls - len(ids)}개가 figure를 document.getElementById('figure id')로 넘기지 않는다(유형을 확인할 수 없다)")
    figs = {}
    for attrs in re.findall(r"<figure\b([^>]*)>", html):
        m = re.search(r'\bid="([^"]+)"', attrs)
        if m:
            figs[m.group(1)] = attrs
    for fid in ids:
        attrs = figs.get(fid)
        if attrs is None:
            out.append(f"애니메이션 figure가 없다: {fid}")
            continue
        t = re.search(r'\bdata-anim="([^"]*)"', attrs)
        if not t:
            out.append(f"애니메이션 유형 누락: {fid}에 data-anim이 없다")
        elif t.group(1) not in ANIM_TYPES:
            out.append(f"허용 밖 애니메이션 유형: {fid}의 '{t.group(1)}'은 목록에 없다")
        elif ANIM_TYPES[t.group(1)] != "사용 가능":
            out.append(f"허용 밖 애니메이션 유형: {fid}의 '{t.group(1)}'은 {ANIM_TYPES[t.group(1)]} 상태다(견본을 먼저 만든다)")
    for cls, pid, body in PAGE_ID.findall(html):
        n = sum(f'id="{fid}"' in body for fid in ids)
        if n > 1:
            out.append(f"{pid} 애니메이션 {n}개(페이지당 1개)")
        if n and not ({"core", "key"} & set(cls.split())):
            out.append(f"{pid} 별 표시 없는 페이지의 애니메이션(★·☆ 페이지에만 둔다)")
    return out


NUM = r"(-?\d+(?:\.\d+)?)"
NOTE_AT = re.compile(r"\bfx\.pair\s*\(\s*[^,()]+,\s*[^,()]+,\s*(?:\[[^\]]*\]|[^,()]+),\s*" + NUM + r"\s*,\s*" + NUM + r"\s*,"
                     r"|\bfx\.say\s*\(\s*[^,()]+,\s*[^,()]+,\s*" + NUM + r"\s*,\s*" + NUM + r"\s*,")


def note_fixed_violations(html):
    """설명 상자 위치: 한 애니메이션의 모든 단계(play 수)에서 RC.fx.pair·say가 같은 숫자 좌표를 쓰면 상자를 한 위치에 고정한 것이다.
    호출은 그 앞의 가장 가까운 RC.demo 호출에 속한다고 본다. 좌표가 변수인 호출은 판정하지 않는다."""
    js, out = doc_scripts(html), []
    starts = [m.start() for m in re.finditer(r"\bRC\.demo\s*\(", js)]
    for k, s in enumerate(starts):
        seg = js[s:starts[k + 1] if k + 1 < len(starts) else len(js)]
        at = [(m.group(1) or m.group(3), m.group(2) or m.group(4)) for m in NOTE_AT.finditer(seg)]
        steps = len(re.findall(r"\bplay\s*:", seg))
        if len(at) >= max(2, steps) and len(set(at)) == 1:
            m = DEMO_ID.match(seg)
            fid = m.group(1) if m else f"RC.demo {k + 1}번째 호출"
            out.append(f"설명 상자 고정 위치: {fid}의 설명 상자가 모든 단계에서 ({at[0][0]}, {at[0][1]})에 있다"
                       "(현재 노드 48px 안으로 옮기거나 RC.note를 지우고 엔진 자동 상자에 맡긴다)")
    return out


def baseline_mark_violations(html):
    """전후 비교의 기준선: 전후 전환 figure는 기준선 도형에 data-rc-base를 달아 RC.check가 마지막 단계까지 남는지 보게 한다."""
    out = []
    for attrs, body in re.findall(r"<figure\b([^>]*)>(.*?)</figure>", html, re.S):
        if re.search(r'\bdata-anim="전후 전환"', attrs) and not re.search(r"\bdata-rc-base\b", body):
            m = re.search(r'\bid="([^"]+)"', attrs)
            out.append(f"전후 전환 기준선 표시 누락: {m.group(1) if m else '이름 없는 figure'}에 data-rc-base를 단 기준선 도형이 없다"
                       "(기준선은 바뀐 값과 별도 도형으로 두고 마지막 단계까지 남긴다)")
    return out


RULES = [
    (script_motion_violations, "prefix"),
    (anim_count_violations, "plain"),
    (anim_violations, "exact"),
    (note_fixed_violations, "exact"),
    (baseline_mark_violations, "exact"),
]
