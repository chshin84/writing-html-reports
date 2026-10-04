"""페이지 근거·핵심 페이지(별) 표시·점수표·새 규약 문서(약어 풀이·마무리 보고서) 규칙. C3(보고서 내용 규격) 소유."""
import re
from collections import Counter
from html.parser import HTMLParser

from checks.common import PAGE_ID, TOC, TextOnly, visible_text

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


BREAK = "¶"  # 블록 경계 표지
WRAPUP = re.compile(r'<main\b[^>]*\bdata-kind="wrapup"')  # 마무리 보고서 표시
TOKEN = re.compile(r"[A-Za-z0-9_](?:[A-Za-z0-9_./\\-]*[A-Za-z0-9_])?")
ABBR = re.compile(r"[A-Z]{2,6}")
GLOSS = re.compile(r'<dl\b[^>]*\bclass="(?:[^"]*\s)?gloss(?:\s[^"]*)?"[^>]*>(.*?)</dl>', re.S)
PAREN_AFTER = re.compile(r"\s?[(（]")  # 약어(풀이)
PAREN_BEFORE = re.compile(r"[^\s()（）¶]\s?[(（]\s?$")  # 풀이(약어)의 여는 괄호까지
PAREN_CLOSE = re.compile(r"\s?[)）]")


def is_new_doc(html):
    """새 규약 문서: 절 이름(p.sec)을 쓰거나 마무리 보고서 표시가 있다. 새 검사는 이 문서에만 적용한다."""
    return bool(SEC.search(html) or WRAPUP.search(html))


class ProseText(TextOnly):
    """code·pre·script·svg·style·title 밖의 글. 약어 검사용이다."""
    SKIP = ("code", "pre", "script", "svg", "style", "title")
    BLOCK = ("p", "div", "li", "dt", "dd", "td", "th", "tr", "section", "h1", "h2", "h3", "h4", "figcaption", "br")

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self.skip += 1
        elif tag in self.BLOCK:
            self.chunks.append(BREAK)  # 블록이 바뀌면 앞 글의 괄호가 뒤 약어로 이어지지 않게 한다

    def handle_endtag(self, tag):
        if tag in self.SKIP and self.skip:
            self.skip -= 1


def abbrs(text):
    """(약어, 시작, 끝) 목록. 숫자·점·하이픈이 섞인 토큰 전체는 약어가 아니다.
    점이 없고 빗금이 든 토큰(ETF/ETN)은 빗금으로 나눠 조각마다 본다. 점이 든 토큰(파일 경로·URL)은 통째로 본다."""
    out = []
    for m in TOKEN.finditer(text):
        tok = m.group()
        pieces = [(tok, m.start())]
        if "." not in tok and re.search(r"[/\\]", tok):
            pieces = [(p.group(), m.start() + p.start()) for p in re.finditer(r"[^/\\]+", tok)]
        out += [(t, st, st + len(t)) for t, st in pieces if ABBR.fullmatch(t)]
    return out


def unglossed(html):
    """풀이 없는 약어를 처음 나온 순서로 한 번씩 돌려준다. 새 규약 판별은 하지 않는다."""
    text = visible_text(html, ProseText)
    glossed = {a for block in GLOSS.findall(html) for dt in re.findall(r"<dt\b[^>]*>(.*?)</dt>", block, re.S)
               for a, _, _ in abbrs(strip_tags(dt))}
    seen, out = set(), []
    for a, start, end in abbrs(text):
        if a in seen:
            continue
        seen.add(a)
        around = PAREN_BEFORE.search(text[max(0, start - 4):start]) and PAREN_CLOSE.match(text, end)
        if a not in glossed and not PAREN_AFTER.match(text, end) and not around:
            out.append(a)
    return out


def abbr_violations(html, old_html=None):
    """새 규약 문서에서 풀이 없는 영문 약어(대문자 2~6자)를 검출한다. 수정 전 문서에도 풀이 없던 약어는 뺀다."""
    if not is_new_doc(html):
        return []
    old = set(unglossed(old_html)) if old_html is not None else set()
    return [f"약어 풀이 없음: {a}(.gloss 용어나 처음 나온 곳의 괄호 풀이를 둔다)" for a in unglossed(html) if a not in old]


PARTS = {"changed": "바뀐 것", "achieved": "처음 요청 대비 달성", "remaining": "남은 일",
         "decisions": "결정 요청", "verification": "검증 범위"}
PAGE_OPEN = re.compile(r'<section class="page[^"]*" id="p\d+"([^>]*)>')  # PAGE_ID와 같은 모양의 여는 태그
PART = re.compile(r'\bdata-part="([^"]+)"')
BASIS = re.compile(r'<p\b[^>]*\bclass="(?:[^"]*\s)?basis(?:\s[^"]*)?"[^>]*>(.*?)</p>', re.S)
HASH = r"(?<![0-9A-Za-z])(?=[0-9a-f]*[0-9])(?=[0-9a-f]*[a-f])[0-9a-f]{7,40}(?![0-9A-Za-z])"  # 커밋 해시
REF = re.compile(
    HASH +
    r"|[\w.-]*[/\\][\w./\\-]*\w\.[A-Za-z]\w{0,5}(?![0-9A-Za-z])"  # 확장자가 붙은 경로
    r"|[\w-]+\.(?:md|html|csv|json|py|txt|xlsx|pdf|yaml|yml)(?![0-9A-Za-z])")  # 알려진 확장자가 붙은 이름


def _missing_parts(html):
    """페이지형 문서는 PAGE_ID 모양의 페이지 section에 있는 data-part만 센다(그 밖의 페이지는 장면·점수에서 빠진다)."""
    opens = PAGE_OPEN.findall(html)
    attrs = opens if opens else re.findall(r"<section\b([^>]*)>", html)
    found = {m for a in attrs for m in PART.findall(a)}
    return [p for p in PARTS if p not in found]


def parts_violations(html, old_html=None):
    """마무리 보고서(data-kind="wrapup")에 다섯 필수 절(data-part)이 모두 있는지 본다. 수정 전 문서에도 없던 절은 뺀다."""
    if not WRAPUP.search(html):
        return []
    old = set(_missing_parts(old_html)) if old_html is not None else set()
    return [f"마무리 보고서 필수 절 없음: {p}({PARTS[p]})" for p in _missing_parts(html) if p not in old]


def _basis_problems(html):
    m = BASIS.search(html)
    end = html.find("</section>")
    if not m or (end != -1 and m.start() > end):
        return ["원본 기준 없음: 문서 머리(첫 section 끝 앞)에 p.basis가 없다"]
    text = strip_tags(m.group(1))
    if not REF.search(text):
        return [f"원본 기준에 커밋 해시·.md 경로·파일 경로가 없다: {text[:40]}"]
    return []


def basis_violations(html, old_html=None):
    """마무리 보고서 머리의 원본 기준(p.basis)에 커밋 해시·.md 경로·파일 경로가 있는지 본다. 수정 전 문서에도 있던 결함은 뺀다."""
    if not WRAPUP.search(html):
        return []
    old = {f.split(":")[0] for f in _basis_problems(old_html)} if old_html is not None else set()
    return [f for f in _basis_problems(html) if f.split(":")[0] not in old]


FILE_LINE = re.compile(r"[\w./\-]*\w\.[A-Za-z]\w{0,5}:\d+")  # 파일:줄
RUN_SRC = re.compile(HASH + "|" + FILE_LINE.pattern)
DOC_PATH = re.compile(r"\S+\.(?:md|html|pdf|docx|pptx|hwp)")  # 읽는 문서. 줄 번호 없이는 실행 원자료가 아니다
LINE_TAGS = ("li", "p", "tr", "dd")  # 한 줄로 보는 요소. 겹치면 바깥 요소가 한 줄이다
NEST = ("ul", "ol", "dl", "table")  # 이 요소가 열려 있으면 같은 이름의 줄 요소는 중첩이다
VOID = ("br", "img", "hr", "meta", "link", "input", "wbr", "source", "col", "area", "base", "embed", "track")


class Lines(HTMLParser):
    """줄(li·p·tr·dd)마다 글, code 요소 안의 글, 링크, 확인 상태, 요약(.gist) 안인지, 첫 data-part 절 앞인지를 모은다.
    닫지 않은 li·p·tr·dd는 같은 이름의 형제 요소가 열릴 때 닫는다."""

    def __init__(self):
        super().__init__()
        self.stack, self.lines, self.cur, self.cur_depth, self.part_seen, self.skip = [], [], None, 0, False, 0
        self.ids, self.in_code = set(), 0

    def _finish(self):
        self.cur["text"] = re.sub(r"\s+", " ", "".join(self.cur["text"])).strip()
        self.lines.append(self.cur)
        self.cur = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "section" and "data-part" in a:
            self.part_seen = True
        if tag in ("script", "style"):
            self.skip += 1
        if (self.cur is not None and tag == self.cur["tag"]
                and not any(t in NEST for t, _ in self.stack[self.cur_depth:])):
            del self.stack[self.cur_depth - 1:]  # 닫지 않은 형제 줄
            self._finish()
        if tag not in VOID:
            self.stack.append((tag, (a.get("class") or "").split()))
        if tag in LINE_TAGS and self.cur is None:
            gist = tag == "li" and any("gist" in c for _, c in self.stack)
            self.cur = dict(tag=tag, text=[], codes=[], links=[], state=None, gist=gist, head=not self.part_seen)
            self.cur_depth = len(self.stack)
        if self.cur is not None:
            if tag == "code":
                self.in_code += 1
                self.cur["codes"].append("")
            if tag == "a" and a.get("href"):
                self.cur["links"].append(a["href"])
            if a.get("data-state") and self.cur["state"] != "run":
                self.cur["state"] = a["data-state"]

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip:
            self.skip -= 1
        if tag == "code" and self.in_code:
            self.in_code -= 1
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break
        if self.cur is not None and len(self.stack) < self.cur_depth:
            self._finish()

    def handle_data(self, data):
        if self.cur is not None and not self.skip:
            self.cur["text"].append(data)
            if self.in_code and self.cur["codes"]:
                self.cur["codes"][-1] += data


def lines(html):
    """(줄 목록, 문서의 id 집합)."""
    parser = Lines()
    parser.feed(html)
    parser.close()
    if parser.cur is not None:
        parser._finish()
    return parser.lines, parser.ids


def _subtract(found, old_html, fn):
    """원본(old_html)에도 같은 줄의 위반이 있으면 그 개수만큼 뺀다. found는 (줄 글, 위반 문장) 목록이다."""
    old = Counter(t for t, _ in fn(old_html)) if old_html is not None else Counter()
    out = []
    for text, msg in found:
        if old[text]:
            old[text] -= 1
        else:
            out.append(msg)
    return out


def _run_source(x):
    """실행 원자료: 문서 경로만 든 것이 아닌 code 요소, 파일:줄, 커밋 해시."""
    real_code = any(c.strip() and not DOC_PATH.fullmatch(c.strip()) for c in x["codes"])
    return real_code or RUN_SRC.search(x["text"])


def _run_problems(html):
    return [(x["text"], f"실행 확인 줄에 원자료 없음: {x['text'][:40]}") for x in lines(html)[0]
            if x["state"] == "run" and not _run_source(x)]


def run_source_violations(html, old_html=None):
    """마무리 보고서에서 실행 확인(data-state="run") 줄에 원자료(code 요소·파일:줄·커밋 해시)가 없으면 검출한다.
    code 안의 글이 문서 경로(.md·.html 등)뿐이면 읽은 내용이므로 원자료로 세지 않는다. 수정 전 문서에도 있던 줄은 뺀다."""
    if not WRAPUP.search(html):
        return []
    return _subtract(_run_problems(html), old_html, _run_problems)


def section_names(html):
    """「절 이름」으로 가리킬 수 있는 이름: 절 이름(p.sec), 요약 상자 밖의 h2·h3 제목, 다섯 필수 절 이름."""
    body = re.sub(r'<div\b[^>]*\bclass="(?:[^"]*\s)?gist(?:\s[^"]*)?"[^>]*>.*?</div>', "", html, flags=re.S)
    names = {strip_tags(t) for t in SEC.findall(body) + re.findall(r"<h[23]\b[^>]*>(.*?)</h[23]>", body, re.S)}
    return names | set(PARTS.values())


def _summary_problems(html):
    names = section_names(html)
    found, ids = lines(html)
    out = []
    for x in found:
        if not (x["gist"] or (x["head"] and x["state"])):
            continue
        linked = any(h[1:] in ids if h.startswith("#") else True for h in x["links"])
        named = any(n in names for n in re.findall(r"「([^」]+)」", x["text"]))
        if not (linked or any(c.strip() for c in x["codes"]) or named
                or REF.search(x["text"]) or FILE_LINE.search(x["text"])):
            out.append((x["text"], f"요약 줄에 근거 위치 없음: {x['text'][:40]}"))
    return out


def summary_source_violations(html, old_html=None):
    """마무리 보고서의 요약 줄(.gist의 li)과 첫 data-part 절 앞의 확인 상태 줄에 보이는 근거 위치가 없으면 검출한다.
    근거 위치: 문서에 있는 id로 가는 링크나 외부 링크, 「절 이름」, code 요소, 커밋 해시, 파일 경로, 파일:줄.
    data-src는 독자에게 보이지 않아 세지 않는다."""
    if not WRAPUP.search(html):
        return []
    return _subtract(_summary_problems(html), old_html, _summary_problems)


RULES = [
    (star_violations, "plain"),
    (score_violations, "drop"),
    (page_violations, "plain"),
    (abbr_violations, "old"),
    (parts_violations, "old"),
    (basis_violations, "old"),
    (run_source_violations, "old"),
    (summary_source_violations, "old"),
]
