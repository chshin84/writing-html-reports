"""고정 견본 재빌드 명령.

사용법: python eval/rebuild.py <출력 폴더>
bench/fixed/의 HTML을 출력 폴더에 복사하고, 현재 워크트리의 build.py로 빌드한다. bench/는 바꾸지 않는다.
시험은 main(argv, bench=<견본 폴더>)로 다른 견본 폴더를 넘긴다.
build.py가 실패하면 그 종료 코드를 그대로 돌려준다. 빌드 뒤 관리 블록이 현재 워크트리의
report-base.css·report-demo.css·report-charts.js·report-peeps.js와 다르면 1을 돌려준다.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
BASE_BLOCK = re.compile(r"/\* BEGIN report-base[^*]*\*/\n(.*?)/\* END report-base \*/", re.S)
CHART_BLOCK = re.compile(r"/\* BEGIN report-charts[^*]*\*/\n(.*?)/\* END report-charts \*/", re.S)


def read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def mismatches(path):
    """관리 블록 가운데 현재 워크트리 파일과 다른 블록의 이름 목록."""
    html = Path(path).read_text(encoding="utf-8")
    bad = []
    base = BASE_BLOCK.findall(html)
    if not base or any(b != read("report-base.css") + read("report-demo.css") for b in base):
        bad.append("report-base")
    if any(c != read("report-charts.js") + "\n" + read("report-peeps.js") for c in CHART_BLOCK.findall(html)):
        bad.append("report-charts")
    return bad


def main(argv=None, bench=None):
    ap = argparse.ArgumentParser(description="고정 견본을 현재 워크트리의 CSS·JS로 다시 빌드한다")
    ap.add_argument("out")
    a = ap.parse_args(argv)
    bench = Path(bench) if bench else ROOT / "bench" / "fixed"
    files = sorted(bench.glob("*.html"))
    if not files:
        print(f"{bench}에 HTML 견본이 없다", file=sys.stderr)
        return 1
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    copies = []
    for f in files:
        shutil.copyfile(f, out / f.name)
        copies.append(out / f.name)
    r = subprocess.run([sys.executable, "-B", str(ROOT / "build.py"), *map(str, copies)],
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    if r.returncode:
        return r.returncode
    bad = {c.name: m for c in copies if (m := mismatches(c))}
    if bad:
        print(f"관리 블록이 현재 워크트리 파일과 다르다: {bad}", file=sys.stderr)
        return 1
    print(f"견본 {len(copies)}개를 {out}에 다시 빌드했다")
    return 0


if __name__ == "__main__":
    sys.exit(main())
