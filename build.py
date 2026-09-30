"""개선본 HTML의 BEGIN/END 표시 사이를 기준 파일로 다시 채운다.

사용법: python build.py <html>...  (여러 번 실행해도 결과가 같다)
- report-base: <style> 안의 표시를 report-base.css로 채운다. 이 표시는 필수다.
- report-charts: <script> 안의 표시를 report-charts.js로 채운다. 표시가 있는 문서만 채운다.
  문서의 CDN 주소 버전이 report-charts.js 첫 줄의 대상 버전과 다르면 채우지 않고 멈춘다.
  문서가 RC 함수를 호출하는데 이 표시가 없어도 멈춘다.
  같은 블록에 report-peeps.js(스틱맨 그림 데이터)를 이어 넣는다.
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
BASE = (HERE / "report-base.css").read_text(encoding="utf-8")
CHARTS = (HERE / "report-charts.js").read_text(encoding="utf-8")
PEEPS = (HERE / "report-peeps.js").read_text(encoding="utf-8")
LIBS = dict(re.findall(r"(echarts|mermaid|gsap)@([\d.]+)", CHARTS.splitlines()[0]))
MARK = ("/* BEGIN report-charts " + " ".join(f"{k}@{v}" for k, v in LIBS.items())
        + " (build.py가 채운다. 손으로 고치지 않는다) */\n")
BLOCK = re.compile(r"(/\* BEGIN report-base[^*]*\*/\n).*?(/\* END report-base \*/)", re.S)
CHART_BLOCK = re.compile(r"/\* BEGIN report-charts[^*]*\*/\n.*?(/\* END report-charts \*/)", re.S)
CDN_VER = re.compile(r"cdn\.jsdelivr\.net/npm/(echarts|mermaid|gsap)@([^/\"']+)/")
RC_CALL = re.compile(r"\bRC\.(?:chart|demo|ma|color)\s*\(")

for name in sys.argv[1:]:
    p = Path(name)
    html = p.read_text(encoding="utf-8")
    if not BLOCK.search(html):
        sys.exit(f"{name}: BEGIN/END report-base 표시가 없다")
    out = BLOCK.sub(lambda m: m.group(1) + BASE + m.group(2), html)
    charts = bool(CHART_BLOCK.search(out))
    if not charts and RC_CALL.search(out):
        sys.exit(f"{name}: RC 함수를 호출하는데 BEGIN/END report-charts 표시가 없다. 템플릿의 연결 코드 <script>를 넣는다")
    if charts:
        wrong = {k: v for k, v in CDN_VER.findall(out) if LIBS.get(k) != v}
        if wrong:
            sys.exit(f"{name}: CDN 버전 {wrong}이 연결 코드의 대상 버전 {LIBS}과 다르다. 채우지 않았다")
        out = CHART_BLOCK.sub(lambda m: MARK + CHARTS + "\n" + PEEPS + m.group(1), out)
    p.write_text(out, encoding="utf-8")
    print(f"{name}: 기준 CSS 반영" + (", 연결 코드 반영" if charts else ""))
