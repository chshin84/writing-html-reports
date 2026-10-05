"""검사 모듈의 공통 부품: HTML 글자 추출, 문서 스크립트·Mermaid 원문 추출, 공용 상수, 금지어 검사.
L1 소유. 규칙 모듈(style·content·anim)이 이 모듈을 가져다 쓴다."""
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

# 금지어 원본. dc코더가 있으면 dc코더가, 없으면 KW 플러그인이 같은 표를 세션에 싣는다(KW 설치를 전제로 사본을 두지 않는다)
BANNED_SOURCES = [Path.home() / ".claude" / "disciplined-coder" / "korean-banned-words.md",
                  Path.home() / ".claude" / "kw-ax" / "korean-banned-words.md"]
BANNED_FILE = next((p for p in BANNED_SOURCES if p.exists()), BANNED_SOURCES[0])
CHARTS_BLOCK = re.compile(r"/\* BEGIN report-charts[^*]*\*/.*?/\* END report-charts \*/", re.S)
PAGE_ID = re.compile(r'<section class="(page[^"]*)" id="(p\d+)"[^>]*>(.*?)</section>', re.S)
TOC = re.compile(r'<p class="toc">(.*?)</p>', re.S)


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


def banned_rules():
    """korean-banned-words.md의 표에서 (금지어, 대신 쓰는 말, 제외 목록)을 읽는다. 원본이 없으면 멈춘다."""
    if not BANNED_FILE.exists():
        raise SystemExit("금지어 원본이 없다: " + " · ".join(map(str, BANNED_SOURCES)) + ". dc코더나 KW 플러그인을 설치한다")
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
    advice = {t: a for t, a, _ in rules}
    new = banned_hits(all_text(new_html), rules)
    if old_html is not None:
        old = banned_hits(all_text(old_html), rules)
        kept = new & old
        if kept:
            print(f"참고: 원본에 있던 금지어 {sum(kept.values())}건(본문 불변이라 두었다) — {dict(kept)}")
        new = new - old
    return [f"금지어 '{t}' {n}건 — 대신: {advice[t]}" for t, n in new.items()]


RULES = [
    (banned_violations, "old"),
]
