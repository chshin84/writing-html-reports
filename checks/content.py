"""페이지 근거·핵심 페이지(별) 표시·점수표 규칙. C3(보고서 내용 규격) 소유."""
import re

from checks.common import PAGE_ID, TOC

PAGE = re.compile(r'<section class="(page[^"]*)"[^>]*>(.*?)</section>', re.S)
EVIDENCE = re.compile(r'<table|<figure|<svg|class="keyfig"|class="bars"')
SEC = re.compile(r'<p\b[^>]*\bclass="(?:[^"]*\s)?sec(?:\s[^"]*)?"[^>]*>(.*?)</p>', re.S)  # 절 이름(C2 계약)
HEAD = re.compile(r"<h[12][^>]*>(.*?)</h[12]>", re.S)


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


def page_name(body):
    """페이지 이름: 절 이름(p.sec)이 있으면 그 글, 없으면 첫 h1·h2의 글이다."""
    m = SEC.search(body) or HEAD.search(body)
    return strip_tags(m.group(1)) if m else ""


def page_violations(html):
    """페이지형 문서에서 근거(표·도표·핵심 수치)가 없는 페이지를 검출한다.
    절차·목록·부록처럼 증명할 결론이 없는 페이지는 class="page list"로 뺀다."""
    out = []
    for cls, body in PAGE.findall(html):
        if "list" in cls.split() or EVIDENCE.search(body):
            continue
        name = page_name(body) or body[:40]
        out.append(f"근거 없는 페이지(표·도표·핵심 수치 없음): {name[:40]}")
    return out


def star_violations(html):
    """핵심 페이지 표시의 상한. ★(core)은 1개, ☆(key)는 2개 이하, 별 합계는 3개 이하다."""
    toc = " ".join(TOC.findall(html))
    classes = [c.split() for c in re.findall(r'<a\b[^>]*\bclass="([^"]*)"', toc)]
    core, key = sum("core" in c for c in classes), sum("key" in c for c in classes)
    out = []
    if core > 1:
        out.append(f"★ 핵심 페이지 {core}개(1개만 둔다)")
    if key > 2:
        out.append(f"☆ 중요 페이지 {key}개(2개 이하로 둔다)")
    if core + key > 3:
        out.append(f"별 표시 페이지 {core + key}개(3개 이하로 둔다)")
    if key and not core:
        out.append("☆만 있고 ★이 없다(가장 중요한 페이지 1개에 ★을 둔다)")
    return out


SRC = re.compile(r'<(?:li|p)\b[^>]*\bdata-src="([^"]+)"')  # 결론 문장의 근거 페이지
KEY_SRC = re.compile(r'<div\b[^>]*\bdata-src="([^"]+)"')  # 핵심 수치의 출처 페이지
WEIGHT = {"N": 4, "R": 3, "B": 2, "C": 2, "D": 1}
ANIM_FIG = re.compile(r'<figure\b[^>]*\bdata-anim="[^"]*"[^>]*>.*?</figure>', re.S)


def page_scores(html):
    """핵심 페이지 평가. 요약·결론·부록 페이지는 후보에서 뺀다. 페이지 이름은 p.sec, 없으면 첫 h1·h2에서 읽는다.
    N 필수도: 이 페이지만을 근거로 하는 결론 문장 수(이 페이지가 없으면 그 결론을 이해할 수 없다).
    R 관련도: 이 페이지를 근거에 포함하는 결론 문장 수.
    B 구조 복잡도: 이 페이지 정지 도식의 판단 분기 수(polygon 마름모, Mermaid {…} 노드). 애니메이션 figure는 세지 않는다.
    C 핵심 수치: 머리말 핵심 수치 중 이 페이지에서 나온 수.
    D 참조: 다른 페이지가 이 페이지를 가리키는 링크 수.
    점수 = 4N + 3R + 2B + 2C + D. 별은 N ≥ 1인 후보만 받는다.
    ★ = 점수가 가장 높은 후보(동점이면 N, 그다음 앞 페이지).
    ☆ = 나머지 후보 중 ★ 점수의 50% 이상이고, ★과 자기를 뺀 후보 점수 중앙값의 2배 이상인 페이지, 높은 순 2개.
    페이지형 문서가 아니면 None을 돌려준다."""
    pages = PAGE_ID.findall(html)
    if not pages:
        return None
    srcs = [s.split() for s in SRC.findall(html)]
    keyfig = " ".join(re.findall(r'class="keyfig"(.*?)</div>\s*</div>', html, re.S))
    ksrcs = [s.split() for s in KEY_SRC.findall(keyfig)]
    rows = []
    for order, (cls, pid, body) in enumerate(pages):
        title = page_name(body)
        excluded = (bool({"summary", "conclusion", "list"} & set(cls.split()))
                    or 'class="doc-head"' in body or 'class="gist"' in body
                    or re.match(r"(요약|결론|부록)", title) is not None)
        static = ANIM_FIG.sub("", body)  # 애니메이션이 자기 페이지 점수를 올리지 않게 뺀다
        mermaid = " ".join(re.findall(r'<pre\b[^>]*\bclass="[^"]*\bmermaid\b[^"]*"[^>]*>(.*?)</pre>', static, re.S))
        m = {"N": sum(s == [pid] for s in srcs), "R": sum(pid in s for s in srcs),
             "B": len(re.findall(r"<polygon\b", static)) + len(re.findall(r"\w\{[^}\n]*\}", mermaid)),
             "C": sum(pid in s for s in ksrcs),
             "D": sum(o[2].count(f'href="#{pid}"') for o in pages if o[1] != pid)}
        rows.append(dict(m, id=pid, title=title, excluded=excluded, order=order, expect="",
                         score=sum(WEIGHT[k] * m[k] for k in WEIGHT)))
    cands = sorted((x for x in rows if not x["excluded"] and x["N"] >= 1),
                   key=lambda x: (-x["score"], -x["N"], x["order"]))
    if cands:
        top = cands[0]
        top["expect"] = "core"
        others = [x for x in rows if not x["excluded"] and x is not top]
        for x in cands[1:]:
            rest = sorted(o["score"] for o in others if o is not x)
            med = (rest[len(rest) // 2] + rest[(len(rest) - 1) // 2]) / 2 if rest else 0
            if x["score"] * 2 >= top["score"] and x["score"] >= 2 * med and sum(r["expect"] == "key" for r in rows) < 2:
                x["expect"] = "key"
    return rows


def score_violations(html, show=False):
    """목차의 ★·☆ 표시가 평가와 다르거나 요약 결론에 근거 표시가 없으면 위반으로 돌려준다. show이면 점수표를 출력한다."""
    rows = page_scores(html)
    if rows is None:
        return []
    toc = " ".join(TOC.findall(html))
    mark = {}
    for href, cls in re.findall(r'<a\b[^>]*href="#(p\d+)"[^>]*\bclass="([^"]*)"', toc):
        mark[href] = "core" if "core" in cls.split() else "key" if "key" in cls.split() else ""
    sym = {"core": "★", "key": "☆", "": "-"}
    if show:
        print("핵심 페이지 평가: 점수 = 4N(필수도) + 3R(관련도) + 2B(분기) + 2C(핵심 수치) + D(참조), 별은 N ≥ 1만")
        for x in rows:
            state = "제외(요약·결론·부록)" if x["excluded"] else (
                f"N{x['N']} R{x['R']} B{x['B']} C{x['C']} D{x['D']} = {x['score']}")
            print(f"  {x['id']:<4} {x['title'][:12]:<12} {state:<26} 평가 {sym[x['expect']]}  표시 {sym[mark.get(x['id'], '')]}")
    out = []
    gist = " ".join(re.findall(r'class="gist"(.*?)</div>', html, re.S))
    missing = len(re.findall(r"<li(?![^>]*data-src)[^>]*>", gist))
    if missing:
        out.append(f"요약 결론 {missing}개에 근거 페이지(data-src)가 없다")
    for x in rows:
        if mark.get(x["id"], "") != x["expect"]:
            out.append(f"{x['id']} 표시 {sym[mark.get(x['id'], '')]}가 평가 {sym[x['expect']]}와 다르다(점수 {x['score']}, N={x['N']})")
    return out


RULES = [
    (star_violations, "plain"),
    (score_violations, "drop"),
    (page_violations, "plain"),
]
