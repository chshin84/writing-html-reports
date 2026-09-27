"""개선본 HTML의 BEGIN/END report-base 표시 사이를 report-base.css로 다시 채운다.

사용법: python build.py <html>...  (여러 번 실행해도 결과가 같다)
"""
import re
import sys
from pathlib import Path

BASE = (Path(__file__).parent / "report-base.css").read_text(encoding="utf-8")
BLOCK = re.compile(r"(/\* BEGIN report-base[^*]*\*/\n).*?(/\* END report-base \*/)", re.S)

for name in sys.argv[1:]:
    p = Path(name)
    html = p.read_text(encoding="utf-8")
    if not BLOCK.search(html):
        sys.exit(f"{name}: BEGIN/END report-base 표시가 없다")
    p.write_text(BLOCK.sub(lambda m: m.group(1) + BASE + m.group(2), html), encoding="utf-8")
    print(f"{name}: 기준 CSS 반영")
