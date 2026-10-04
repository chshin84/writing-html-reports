"""서식·라벨·스크립트 주소 규칙. C2(페이지 틀·CSS) 소유."""
import re
from html.parser import HTMLParser

from checks.common import css_of, doc_scripts, mermaid_sources, script_urls, visible_text

ALLOWED_FONT_HOSTS = ("cdn.jsdelivr.net/gh/orioncactus/pretendard",)
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")
LIB_URL = re.compile(r"^https://cdn\.jsdelivr\.net/npm/(?:echarts|mermaid|gsap)@([^/]+)/")


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


def script_style_violations(html):
    """문서 스크립트의 주소·버전 고정과, 스크립트·Mermaid 원문의 색 리터럴."""
    js, mmd, out = doc_scripts(html), mermaid_sources(html), []

    def rule(name, hits):
        if hits:
            out.append(f"{name}: {len(hits)}건 — 예: {hits[0][:80]}")

    urls = script_urls(html)
    rule("허용 밖 스크립트", [u for u in urls if not LIB_URL.match(u)])
    rule("버전 미고정", [u for u in urls if LIB_URL.match(u) and not re.fullmatch(r"\d+\.\d+\.\d+", LIB_URL.match(u).group(1))])
    js_no_ids = re.sub(r"""(?:querySelector(?:All)?|getElementById)\(\s*['"`][^'"`]*['"`]""", "", js)
    rule("스크립트·도식 색 리터럴",
         re.findall(r"""['"`][^'"`\n]*?(#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3}))\b""", js_no_ids)
         + re.findall(r"#[0-9a-fA-F]{3,8}\b", mmd)
         + re.findall(r"(?m)^\s*(?:style|classDef)\b.*$", mmd))
    return out


VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
TITLE_MAX = 40  # 결론 제목은 공백 포함 40자 이하
SENTENCE_END = re.compile(r"[가-힣]다\.?$")


BLOCK = {"address", "article", "aside", "blockquote", "div", "dl", "fieldset", "figure", "footer", "form",
         "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr", "main", "nav", "ol", "p", "pre", "section",
         "table", "ul"}


class _Heads(HTMLParser):
    """모든 h2의 (시작 위치, 글자)와, section.page마다 직계 <p class="sec"> 유무와 직계 h2를 모은다."""

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.starts = [0] + [m.end() for m in re.finditer("\n", html)]
        self.stack, self.pages, self.h2, self.cur = [], [], [], None
        self.feed(html)
        self.close()

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            return
        cls = (dict(attrs).get("class") or "").split()
        if tag in BLOCK and self.stack and self.stack[-1][0] == "p":
            self.stack.pop()  # 블록 요소가 시작되면 닫는 태그 없는 p는 HTML 규칙대로 먼저 닫힌다
        top = self.stack[-1] if self.stack else None
        if tag == "h2":
            line, col = self.getpos()
            self.cur = {"start": self.starts[line - 1] + col, "text": ""}
            self.h2.append(self.cur)
        if top and top[1] is not None:  # 바로 위가 section.page면 직계 자식이다
            pg = self.pages[top[1]]
            if tag == "p" and "sec" in cls:
                pg["sec"] = True
            elif tag == "h2":
                pg["h2"].append(self.cur)
        if tag == "section" and "page" in cls:
            self.pages.append({"sec": False, "h2": []})
            self.stack.append((tag, len(self.pages) - 1))
        else:
            self.stack.append((tag, None))

    def handle_endtag(self, tag):
        if tag == "h2":
            self.cur = None
        for i in range(len(self.stack) - 1, -1, -1):  # 닫는 태그가 빠진 요소는 함께 닫는다
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if self.cur is not None:
            self.cur["text"] += data


def _squash(text):
    return re.sub(r"\s+", " ", text).strip()


def conclusion_titles(html):
    """<p class="sec">가 있는 section.page의 직계 h2: [(문서 안 시작 위치, 공백을 하나로 줄인 글자)]."""
    return [(h["start"], _squash(h["text"])) for p in _Heads(html).pages if p["sec"] for h in p["h2"]]


def conclusion_violations(new_html, old_html=None):
    """결론 제목(.sec 페이지의 직계 h2)은 공백 포함 40자 이하이고 문장 어미 '다'로 끝나야 한다.
    원본을 주면 원본의 h2와 같은 글자인 제목은 위반으로 세지 않는다(기존 문서의 본문 문장은 고치지 않는다).
    원본 h2도 같은 파서로 읽어 두 글자의 정규화가 같다."""
    old = {_squash(h["text"]) for h in _Heads(old_html).h2} if old_html is not None else set()
    out = []
    for _, t in conclusion_titles(new_html):
        if t in old:
            continue
        why = []
        if len(t) > TITLE_MAX:
            why.append(f"{len(t)}자(기준 {TITLE_MAX}자)")
        if not SENTENCE_END.search(t):
            why.append("문장 어미 없음")
        if why:
            out.append(f"결론 제목이 규격에 맞지 않음({', '.join(why)}): {t[:60]}")
    return out


HANGUL = re.compile("[가-힣]")
LABEL_TAGS = re.compile(r'<(title|h1|h2|h3|caption|th)\b[^>]*>(.*?)</\1>|<span class="(?:t|k)">(.*?)</span>'
                        r'|<p\b[^>]*\bclass="[^"]*\bsec\b[^"]*"[^>]*>(.*?)(?:</p>|(?=<(?:h[1-6]|ul|ol|div|p|table|dl|figure|section)\b))', re.S)
LABEL_MAX = {"title": 24, "h1": 24}  # 나머지 라벨(절 이름 .sec 포함)은 18자


def label_violations(html):
    """제목·소제목·표 머리·도표 제목·절 이름(.sec)이 명사구인지 본다. 문장 어미, 질문형 어미,
    목적격 조사(을·를), 콜론 뒤 문장, 세 어절 이상 앞의 관형절, 길이 초과를 검출한다.
    결론 제목(.sec 페이지의 직계 h2)은 conclusion_violations가 보므로 여기서 뺀다."""
    out = []
    skip = {start for start, _ in conclusion_titles(html)}
    for m in LABEL_TAGS.finditer(html):
        if m.start() in skip:
            continue
        tag, inner, span, sec = m.groups()
        t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", inner or span or sec or "")).strip()
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


# (규칙 함수, 원본 대조 방식). 방식은 check.py의 집계기가 해석한다.
RULES = [
    (style_violations, "plain"),
    (script_style_violations, "prefix"),
    (label_violations, "plain"),
    (conclusion_violations, "old"),
]
