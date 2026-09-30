"""Open Peeps 원본 묶음에서 스틱맨 네 가지를 조합해 report-peeps.js로 쓴다.

사용법: python tools/build-peeps.py [출력 경로]   (원본: assets/open-peeps-src/Flat Assets.zip)
원본의 채움 색은 검은색·흰색 두 가지라고 가정하고, 다른 색이나 그라데이션이 나오면 멈춘다.
"""
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "open-peeps-src" / "Flat Assets.zip"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "report-peeps.js"
ATOMS = "Flat Assets/Separate Atoms/"
HEAD = "Short 2"
CROP = "0 150 1500 1500"  # 머리 위부터 허리까지(상반신)
PEEPS = {  # 아이콘 이름: (자세, 표정)
    "person": ("crossed_arms-1", "Suspicious"),
    "person-guide": ("pointing_finger-1", "Explaining"),
    "person-done": ("robot_dance-1", "Smile Big"),
    "person-fail": ("resting-2", "Tired"),
}
FILL = {"#000000": "pk", "#FFFFFF": "pw"}  # pk: 선 색 토큰(ink), pw: 바탕 토큰(paper)
NUM = re.compile(r"-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?")


def rounded(m):
    v = f"{float(m.group(0)):.1f}".rstrip("0").rstrip(".")
    v = "0" if v in ("-0", "") else v
    nxt = m.string[m.end():m.end() + 1]
    return v + (" " if nxt and nxt in ".0123456789" else "")  # 반올림으로 경계가 붙지 않게 띄운다


def inner(z, name):
    s = z.read(ATOMS + name).decode("utf-8")
    s = re.sub(r"^.*?<svg[^>]*>", "", s, flags=re.S).rsplit("</svg>", 1)[0]
    s = re.sub(r"<title>.*?</title>|<desc>.*?</desc>|<!--.*?-->", "", s, flags=re.S)
    if re.search(r"Gradient|<image|style=", s):
        sys.exit(f"{name}: 그라데이션·이미지·style 속성이 있다. 처리하지 않는다")
    s = re.sub(r'\sid="[^"]*"', "", s)

    def color(m):
        v = m.group(1).upper()
        if v == "NONE":
            return m.group(0)
        if v not in FILL:
            sys.exit(f"{name}: 처리하지 않는 채움 색 {v}")
        return f' class="{FILL[v]}"'
    s = re.sub(r'\sfill="([^"]*)"', color, s)
    s = re.sub(r'\b(d|points|transform)="([^"]*)"', lambda a: f'{a.group(1)}="{NUM.sub(rounded, a.group(2))}"', s)
    return re.sub(r"\s+", " ", s).strip()


def peep(z, pose, face):
    return (f'<g transform="translate(-121,634)">{inner(z, f"pose/standing/{pose}.svg")}</g>'
            f'<g transform="translate(404,180)">{inner(z, f"head/{HEAD}.svg")}'
            f'<g transform="translate(159,186)">{inner(z, f"face/{face}.svg")}</g></g>')


if not SRC.exists():
    sys.exit(f"원본 묶음이 없다: {SRC} (assets/LICENSE-open-peeps.md의 주소에서 다시 받는다)")
with zipfile.ZipFile(SRC) as z:
    data = {"figures": {k: peep(z, *v) for k, v in PEEPS.items()}, "viewBox": CROP}
js = ("/* report-peeps: Open Peeps(Pablo Stanley, CC0 1.0) 조각을 조합한 스틱맨 그림이다. 생성물이므로 손으로 고치지 않고 "
      "tools/build-peeps.py를 실행한다 */\n"
      "window.RC_PEEPS = " + json.dumps(data, ensure_ascii=False, sort_keys=True) + ";\n")
with open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write(js)
print(f"{OUT}: 스틱맨 {len(data['figures'])}개, {len(js.encode('utf-8')):,}바이트")
