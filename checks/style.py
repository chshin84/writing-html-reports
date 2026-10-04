"""서식·라벨·스크립트 주소 규칙. C2(페이지 틀·CSS) 소유."""
import re

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


# (규칙 함수, 원본 대조 방식). 방식은 check.py의 집계기가 해석한다.
RULES = [
    (style_violations, "plain"),
    (script_style_violations, "prefix"),
    (label_violations, "plain"),
]
