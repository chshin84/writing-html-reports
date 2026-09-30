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
from html.parser import HTMLParser
from pathlib import Path

ALLOWED_FONT_HOSTS = ("cdn.jsdelivr.net/gh/orioncactus/pretendard",)
BANNED_FILE = Path(__file__).parent / "금지어.md"  # disciplined-coder 금지어 표의 사본
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
CHARTS_BLOCK = re.compile(r"/\* BEGIN report-charts[^*]*\*/.*?/\* END report-charts \*/", re.S)
LIB_URL = re.compile(r"^https://cdn\.jsdelivr\.net/npm/(?:echarts|mermaid|gsap)@([^/]+)/")


class TextOnly(HTMLParser):
    """style·script·svg 밖의 보이는 글자만 모은다."""

    def __init__(self):
        super().__init__()
        self.skip = 0
        self.chunks = []

    def handle_starttag(self, tag, attrs):
        if tag in ("style", "script", "svg", "title"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("style", "script", "svg", "title") and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.chunks.append(data)


class SvgText(HTMLParser):
    """svg 안의 text 요소 글자를 모은다."""

    def __init__(self):
        super().__init__()
        self.in_svg = 0
        self.chunks = []

    def handle_starttag(self, tag, attrs):
        if tag == "svg":
            self.in_svg += 1

    def handle_endtag(self, tag):
        if tag == "svg" and self.in_svg:
            self.in_svg -= 1

    def handle_data(self, data):
        if self.in_svg and data.strip():
            self.chunks.append(data)


def visible_text(html, parser_cls=TextOnly):
    p = parser_cls()
    p.feed(html)
    return re.sub(r"\s+", " ", " ".join(p.chunks)).strip()


def css_of(html):
    return "\n".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S)) + "\n" + " ".join(
        re.findall(r'style="([^"]*)"', html)
    )


def style_violations(html):
    css = css_of(html)
    out = []

    def rule(name, hits):
        if hits:
            out.append(f"{name}: {len(hits)}건 — 예: {hits[0][:80]}")

    rule("둥근 모서리(3px 이상)", [m for m in re.findall(r"border-radius\s*:\s*([^;}\"]+)", css)
                              if any(float(n) >= 3 for n in re.findall(r"([\d.]+)px", m)) or "%" in m])
    rule("svg 둥근 모서리(rx 3 이상)", [m for m in re.findall(r'\brx="([\d.]+)"', html) if float(m) >= 3])
    rule("그림자", [m for m in re.findall(r"box-shadow\s*:\s*([^;}\"]+)", css) if m.strip() != "none"])
    rule("그라데이션", re.findall(r"(?:linear|radial|conic)-gradient\([^)]*", css))
    rule("움직임", re.findall(r"(?:@keyframes\s+\w+|transition\s*:[^;}]+|animation\s*:[^;}]+)", css)
         + re.findall(r"IntersectionObserver", html))
    rule("왼쪽 색 띠(3px 이상)", re.findall(r"border-left\s*:\s*(?:[3-9]|\d\d)px[^;}\"]*", css))
    rule("대문자 변환·자간 확대", re.findall(r"(?:text-transform\s*:\s*uppercase|letter-spacing\s*:\s*\.?0?\.[1-9]\d*em)", css))
    rule("허용 밖 웹폰트", [u for u in re.findall(r'<link[^>]+href="([^"]+)"', html)
                       if ("font" in u) and not any(h in u for h in ALLOWED_FONT_HOSTS)])
    rule("모노 글꼴 직접 지정", re.findall(r'font-family\s*:\s*"?(?:IBM Plex Mono|JetBrains Mono|Space Mono)[^;}]*', css))
    rule("알약 배지(99px·999px)", re.findall(r"border-radius\s*:\s*99+px", css))
    rule("이모지", EMOJI.findall(visible_text(html)))
    # 색 리터럴은 :root 토큰 정의 밖에서 쓰지 않는다(흰색·검정 예외 없음).
    body_css = re.sub(r":root[^{]*\{[^}]*\}", "", css)
    rule("토큰 밖 색 리터럴", re.findall(r"#[0-9a-fA-F]{3,8}\b", body_css)
         + re.findall(r'(?:fill|stroke)="(#[0-9a-fA-F]{3,8})"', html))
    return out


def doc_scripts(html):
    """문서 스크립트: report-charts 표시 밖 <script>의 내용. 연결 코드는 build.py가 관리하므로 보지 않는다."""
    return "\n".join(re.findall(r"<script\b[^>]*>(.*?)</script>", CHARTS_BLOCK.sub("", html), re.S))


def mermaid_sources(html):
    return "\n".join(re.findall(r'<pre\b[^>]*\bclass="[^"]*\bmermaid\b[^"]*"[^>]*>(.*?)</pre>', html, re.S))


def script_urls(html):
    """<script src>와 문서 스크립트의 import 주소."""
    js = doc_scripts(html)
    return (re.findall(r'<script\b[^>]*\bsrc="([^"]+)"', html)
            + re.findall(r"""\bimport\b[^'"()]*?\bfrom\s*['"]([^'"]+)['"]""", js)
            + re.findall(r"""\bimport\s*\(\s*['"]([^'"]+)['"]""", js)
            + re.findall(r"""\bimport\s+['"]([^'"]+)['"]""", js))


def script_strings(html):
    """문서 스크립트의 따옴표 문자열. 금지어 검사에 넣는다."""
    found = re.findall(r"""'((?:[^'\\\n]|\\.)*)'|"((?:[^"\\\n]|\\.)*)"|`([^`]*)`""", doc_scripts(html))
    return " ".join(a or b or c for a, b, c in found)


def script_violations(html):
    """시각화 스크립트와 Mermaid 원문의 규격 위반."""
    js, mmd, out = doc_scripts(html), mermaid_sources(html), []

    def rule(name, hits):
        if hits:
            out.append(f"{name}: {len(hits)}건 — 예: {hits[0][:80]}")

    urls = script_urls(html)
    rule("차트 애니메이션", re.findall(r"animation\s*:\s*true", js))
    rule("허용 밖 스크립트", [u for u in urls if not LIB_URL.match(u)])
    rule("버전 미고정", [u for u in urls if LIB_URL.match(u) and not re.fullmatch(r"\d+\.\d+\.\d+", LIB_URL.match(u).group(1))])
    rule("GSAP 직접 호출(play(tl, $) 안에서는 tl.to·tl.set을 쓴다)",
         re.findall(r"\bgsap\.\w+", js) + re.findall(r"\b(?:repeat\s*:\s*-?\s*[1-9]|yoyo\s*:\s*true)", js))
    rule("차트 장식", re.findall(r"shadowBlur\s*:\s*(?!0+(?:\.0+)?(?![\d.]))[^,}\s]+", js)
         + [m for m in re.findall(r"borderRadius\s*:\s*(\[[^\]]*\]|[\d.]+)", js)
            if any(float(n) >= 3 for n in re.findall(r"\d+(?:\.\d+)?", m))])
    js_no_ids = re.sub(r"""(?:querySelector(?:All)?|getElementById)\(\s*['"`][^'"`]*['"`]""", "", js)
    rule("스크립트·도식 색 리터럴",
         re.findall(r"""['"`][^'"`\n]*?(#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3}))\b""", js_no_ids)
         + re.findall(r"#[0-9a-fA-F]{3,8}\b", mmd)
         + re.findall(r"(?m)^\s*(?:style|classDef)\b.*$", mmd))
    return out


def banned_rules():
    """korean-banned-words.md의 표에서 (금지어, 대신 쓰는 말, 제외 목록)을 읽는다. 파일이 없으면 None."""
    if not BANNED_FILE.exists():
        return None
    rules = []
    for line in BANNED_FILE.read_text(encoding="utf-8").splitlines():
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) < 5 or not cols[0].startswith("`"):
            continue
        excl = re.findall(r"`([^`]+)`", cols[4])
        for term in re.findall(r"`([^`]+)`", cols[0]):
            rules.append((term, cols[1], [e for e in excl if term in e]))
    return rules


def banned_hits(text, rules):
    """금지어별 출현 횟수. 제외어의 일부로 나온 출현은 세지 않는다."""
    hits = Counter()
    for term, _, excl in rules:
        for m in re.finditer(re.escape(term), text):
            i = m.start()
            covered = any(text[i - k:i - k + len(e)] == e
                          for e in excl for k in [x.start() for x in re.finditer(re.escape(term), e)])
            if not covered:
                hits[term] += 1
    return hits


def all_text(html):
    return visible_text(html) + " " + visible_text(html, SvgText) + " " + script_strings(html)


def banned_violations(new_html, old_html=None):
    rules = banned_rules()
    if rules is None:
        print(f"참고: {BANNED_FILE}가 없어 금지어 검사를 생략했다")
        return []
    advice = {t: a for t, a, _ in rules}
    new = banned_hits(all_text(new_html), rules)
    if old_html is not None:
        old = banned_hits(all_text(old_html), rules)
        kept = new & old
        if kept:
            print(f"참고: 원본에 있던 금지어 {sum(kept.values())}건(본문 불변이라 두었다) — {dict(kept)}")
        new = new - old
    return [f"금지어 '{t}' {n}건 — 대신: {advice[t]}" for t, n in new.items()]


HANGUL = re.compile("[가-힣]")
LABEL_TAGS = re.compile(r'<(title|h1|h2|h3|caption|th)\b[^>]*>(.*?)</\1>|<span class="(?:t|k)">(.*?)</span>', re.S)
LABEL_MAX = {"title": 24, "h1": 24}  # 나머지 라벨은 18자


def label_violations(html):
    """제목·소제목·표 머리·도표 제목이 명사구인지 본다. 문장 어미, 질문형 어미,
    목적격 조사(을·를), 콜론 뒤 문장, 세 어절 이상 앞의 관형절, 길이 초과를 검출한다."""
    out = []
    for tag, inner, span in LABEL_TAGS.findall(html):
        t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", inner or span)).strip()
        letters = re.findall(r"[A-Za-z가-힣]", t)
        if not HANGUL.search(t) or "${" in t or len(HANGUL.findall(t)) * 2 < len(letters):
            continue  # 코드·자료 형태 이름이 주가 되는 라벨은 보지 않는다
        words = t.split(" ")
        why = []
        if re.search(r"(?:다|요|까|나|지|죠)[.?!]?$", t):
            why.append("문장·질문형 어미")
        if any(re.search(r"[가-힣](?:을|를)$", w) for w in words[:-1]):
            why.append("목적어가 있는 절")
        if re.search(r":\s*\S+\s+\S+\s+\S+", t):
            why.append("콜론 뒤 문장")
        adn = [len(w) > 1 and bool(re.search(r"[가-힣](?:한|된|는|던|린|운|난|날|할|든|은|른|만든)$", w))
               for w in words]
        # 논항(조사 붙은 어절)을 거느린 관형형이나, '결과·과정' 같은 넓은 말을 꾸미는 관형형은 절이다
        if any(adn[i] and re.search(r"[가-힣](?:이|가|을|를|에|에서|으로|로)$", words[i - 1])
               for i in range(1, len(words) - 1)) or (
                len(words) >= 2 and adn[-2] and words[-1] in ("결과", "과정", "것", "점", "방법", "내용")):
            why.append("명사 앞 관형절")
        limit = LABEL_MAX.get(tag, 18)
        core = re.sub(r"\s*\([^)]*\)", "", t)  # 괄호 속 기간·단위는 길이에서 뺀다
        if len(core) > limit:
            why.append(f"{len(core)}자(기준 {limit}자)")
        if why:
            out.append(f"라벨이 명사구가 아님({', '.join(why)}): {t[:60]}")
    return out


PAGE = re.compile(r'<section class="(page[^"]*)"[^>]*>(.*?)</section>', re.S)
EVIDENCE = re.compile(r'<table|<figure|<svg|class="keyfig"|class="bars"')


def page_violations(html):
    """페이지형 문서에서 근거(표·도표·핵심 수치)가 없는 페이지를 검출한다.
    절차·목록·부록처럼 증명할 결론이 없는 페이지는 class="page list"로 뺀다."""
    out = []
    for cls, body in PAGE.findall(html):
        if "list" in cls.split() or EVIDENCE.search(body):
            continue
        h = re.search(r"<h[12][^>]*>(.*?)</h[12]>", body, re.S)
        name = re.sub(r"<[^>]+>", "", h.group(1)).strip() if h else body[:40]
        out.append(f"근거 없는 페이지(표·도표·핵심 수치 없음): {name[:40]}")
    return out


TOC = re.compile(r'<p class="toc">(.*?)</p>', re.S)


def star_violations(html):
    """핵심 페이지 표시와 애니메이션의 상한. ★(core)은 1개, ☆(key)는 2개 이하, 별 합계와 애니메이션은 3개 이하다."""
    toc = " ".join(TOC.findall(html))
    classes = [c.split() for c in re.findall(r'<a\b[^>]*\bclass="([^"]*)"', toc)]
    core, key = sum("core" in c for c in classes), sum("key" in c for c in classes)
    demos = len(re.findall(r"\bRC\.demo\s*\(", doc_scripts(html)))
    out = []
    if core > 1:
        out.append(f"★ 핵심 페이지 {core}개(1개만 둔다)")
    if key > 2:
        out.append(f"☆ 중요 페이지 {key}개(2개 이하로 둔다)")
    if core + key > 3:
        out.append(f"별 표시 페이지 {core + key}개(3개 이하로 둔다)")
    if key and not core:
        out.append("☆만 있고 ★이 없다(가장 중요한 페이지 1개에 ★을 둔다)")
    if demos > 3:
        out.append(f"애니메이션 {demos}개(3개 이하로 둔다)")
    return out


ANIM_TYPES = {  # 애니메이션 목록. SKILL.md '애니메이션' 절의 표와 같아야 한다(tests의 ListSync가 확인한다)
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


PAGE_ID = re.compile(r'<section class="(page[^"]*)" id="(p\d+)"[^>]*>(.*?)</section>', re.S)
SRC = re.compile(r'<(?:li|p)\b[^>]*\bdata-src="([^"]+)"')  # 결론 문장의 근거 페이지
KEY_SRC = re.compile(r'<div\b[^>]*\bdata-src="([^"]+)"')  # 핵심 수치의 출처 페이지
WEIGHT = {"N": 4, "R": 3, "B": 2, "C": 2, "D": 1}
ANIM_FIG = re.compile(r'<figure\b[^>]*\bdata-anim="[^"]*"[^>]*>.*?</figure>', re.S)


def page_scores(html):
    """핵심 페이지 평가. 요약·결론·부록 페이지는 후보에서 뺀다.
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
        h = re.search(r"<h[12][^>]*>(.*?)</h[12]>", body, re.S)
        title = re.sub(r"<[^>]+>", "", h.group(1)).strip() if h else ""
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
    scripts = script_violations(new)
    if old is not None:
        old_rules = {f.split(":")[0] for f in script_violations(old)}
        kept = [f for f in scripts if f.split(":")[0] in old_rules]
        if kept:
            print(f"참고: 원본에 있던 스크립트 위반(원본 스크립트는 고치지 않는다) — {kept}")
        scripts = [f for f in scripts if f not in kept]
    anims = anim_violations(new)
    if old is not None:
        old_anims = set(anim_violations(old))
        kept = [f for f in anims if f in old_anims]
        if kept:
            print(f"참고: 원본에 있던 애니메이션 위반(수정 작업이라 위반으로 세지 않는다) — {kept}")
        anims = [f for f in anims if f not in old_anims]
    scores = score_violations(new, show=True)
    if old is not None and scores:  # 기존 문서 수정은 구조를 바꾸지 않으므로 점수표만 참고로 둔다
        print(f"참고: 핵심 페이지 표시가 평가와 다르다(수정 작업이라 위반으로 세지 않는다) — {scores}")
        scores = []
    fails = (style_violations(new) + scripts + star_violations(new) + anims + scores + label_violations(new)
             + page_violations(new) + banned_violations(new, old))
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
