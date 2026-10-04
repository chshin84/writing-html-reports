"""C0 측정 함수. 브라우저가 모은 원시값으로 판정값을 계산한다. 이 모듈은 브라우저를 쓰지 않는다."""
import math
import re

# 원문 사실은 피평가 워크트리의 checks/에 기대지 않고 여기서 계산한다(checks/common.py와 같은 정규식).
CHARTS_BLOCK = re.compile(r"/\* BEGIN report-charts[^*]*\*/.*?/\* END report-charts \*/", re.S)
PAGE_ID = re.compile(r'<section class="(page[^"]*)" id="(p\d+)"[^>]*>(.*?)</section>', re.S)
MERMAID = re.compile(r'<pre\b[^>]*\bclass="[^"]*\bmermaid\b[^"]*"[^>]*>(.*?)</pre>', re.S)


def doc_scripts(html):
    """관리 블록(report-charts) 밖 <script>의 내용."""
    return "\n".join(re.findall(r"<script\b[^>]*>(.*?)</script>", CHARTS_BLOCK.sub("", html), re.S))


ORDER = ["dwell", "step-anim", "step1", "note-near", "active-visible", "svg-font-390", "figure-overflow-390",
         "contrast-text", "contrast-graphic", "cvd", "html-font-390", "overflow-390", "table-col-390",
         "page-number", "hash-nav", "rules-motion", "rules-layout", "rules-all"]
TARGET = {i: "motion" for i in ORDER[:7]}
TARGET.update({i: "layout" for i in ORDER[7:15]})
TARGET.update({"rules-motion": "motion", "rules-layout": "layout", "rules-all": "content"})
THEMED = {"contrast-text", "contrast-graphic", "cvd"}
RULE_IDS = {"rules-motion", "rules-layout", "rules-all"}
NEAR = 48


def item(id_, target, status, value=None, detail=None):
    return {"id": id_, "target": target, "status": status, "value": value, "detail": detail}


def chars(text):
    """글자 수: 공백을 빼고, 숫자 묶음(1,234.5 같은)은 1자로 센다."""
    return len(re.sub(r"\s", "", re.sub(r"\d[\d,.]*", "#", text)))


def _state_at(samples, t):
    best = samples[0][1]
    for ts, state in samples:
        if ts <= t + 1e-9:
            best = state
        else:
            break
    return best


def dwell_steps(samples, ends):
    """samples: 시간순 [(t, {요소 키: 보이는 글})], ends: 단계 끝 라벨 시각 [e0, e1, …].
    단계 i는 e(i-1)(첫 단계는 0)에서 e(i)까지다. 글 완료 시점은 단계 안에서 보이는 글이 마지막으로 바뀐 표본 시각이다."""
    out = []
    for i, end in enumerate(ends):
        start = 0.0 if i == 0 else ends[i - 1]
        inside = [s for s in samples if start - 1e-9 <= s[0] <= end + 1e-9]
        done = start
        for (_, a), (tb, b) in zip(inside, inside[1:]):
            if a != b:
                done = tb
        before, after = _state_at(samples, start), _state_at(samples, end)
        n = sum(chars(text) for key, text in after.items() if before.get(key) != text)
        lo, dwell = 1 + n / 8, end - done
        out.append({"step": i + 1, "end": round(end, 3), "done": round(done, 3), "dwell": round(dwell, 3), "n": n,
                    "lo": round(lo, 3), "hi": round(lo + 3, 3), "ok": lo - 1e-6 <= dwell <= lo + 3 + 1e-6})
    return out


def parse_color(s):
    """'rgb(…)'·'rgba(…)'·'#rgb'·'#rrggbb'·'transparent'를 (r, g, b, a)로 바꾼다. 읽을 수 없으면 None."""
    if s is None:
        return None
    s = s.strip().lower()
    if s in ("transparent", "none", ""):
        return (0.0, 0.0, 0.0, 0.0)
    h = re.fullmatch(r"#([0-9a-f]{3}|[0-9a-f]{6})", s)
    if h:
        v = h.group(1)
        if len(v) == 3:
            v = "".join(c * 2 for c in v)
        return (int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16), 1.0)
    r = re.fullmatch(r"rgba?\(\s*([\d.]+)[\s,]+([\d.]+)[\s,]+([\d.]+)(?:[\s,/]+([\d.]+%?))?\s*\)", s)
    if r:
        a = r.group(4)
        alpha = 1.0 if a is None else (float(a[:-1]) / 100 if a.endswith("%") else float(a))
        return (float(r.group(1)), float(r.group(2)), float(r.group(3)), alpha)
    return None


def _lin(c):
    c /= 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _unlin(c):
    c = min(1.0, max(0.0, c))
    v = 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return v * 255


def luminance(c):
    r, g, b = (_lin(v) for v in c[:3])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def blend(fg, bg):
    a = fg[3]
    return tuple(fg[i] * a + bg[i] * (1 - a) for i in range(3)) + (1.0,)


def contrast(c1, c2):
    hi, lo = sorted((luminance(c1), luminance(c2)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def text_threshold(px, weight):
    """WCAG 1.4.3: 24px 이상이거나 굵은(700 이상) 18.66px 이상 글자는 3:1, 나머지는 4.5:1."""
    return 3.0 if px >= 24 - 1e-9 or (weight >= 700 and px >= 18.66 - 1e-9) else 4.5


DEUTAN = ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881))


def deutan(rgb):
    """제2색각(Machado 2009, 심각도 1.0) 모의 변환. 선형 RGB에서 행렬을 곱한다."""
    lin = [_lin(v) for v in rgb[:3]]
    return tuple(_unlin(sum(k * c for k, c in zip(row, lin))) for row in DEUTAN)


def lab(rgb):
    r, g, b = (_lin(v) for v in rgb[:3])
    x = (0.4124564 * r + 0.3575761 * g + 0.1804375 * b) / 0.95047
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = (0.0193339 * r + 0.1191920 * g + 0.9503041 * b) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116

    fx, fy, fz = f(x), f(y), f(z)
    return (116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz))


def delta_e76(a, b):
    return math.dist(lab(a), lab(b))


def cvd_pairs(colors):
    names = list(colors)
    return [(a, b, round(delta_e76(deutan(colors[a]), deutan(colors[b])), 2))
            for i, a in enumerate(names) for b in names[i + 1:]]


def gap(a, b):
    """두 경계 상자 (left, top, right, bottom) 사이 거리. 겹치거나 닿으면 0."""
    dx = max(0.0, a[0] - b[2], b[0] - a[2])
    dy = max(0.0, a[1] - b[3], b[1] - a[3])
    return math.hypot(dx, dy)


def overlap_area(a, b):
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0])) * max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


def points_inside(points, box):
    return sum(1 for x, y in points if box[0] <= x <= box[2] and box[1] <= y <= box[3])


def inside_view(box, w, h):
    return box[0] >= -0.5 and box[1] >= -0.5 and box[2] <= w + 0.5 and box[3] <= h + 0.5


def escapes(box, width):
    return box[0] < -0.5 or box[2] > width + 0.5


def note_steps(steps, view):
    """단계 끝마다 현재 노드와 가장 가까운 보이는 설명 상자로 거리·겹침·화면 안을 판정한다."""
    out = []
    for s in steps:
        a, count = s.get("active"), s.get("active_count", 1 if s.get("active") else 0)
        if count != 1 or not a:
            why = "현재 노드 없음" if count == 0 else "현재 노드가 둘 이상"
            out.append({"step": s["step"], "near": False, "visible": False, "why": why})
            continue
        if not s["notes"]:
            out.append({"step": s["step"], "near": False, "visible": False, "why": "보이는 설명 상자 없음"})
            continue
        note = min(s["notes"], key=lambda b: gap(a, b))
        d = gap(a, note)
        hits = [b for b in s["boxes"] if overlap_area(b, note) > 1]
        pts = points_inside(s["points"], note)
        out.append({"step": s["step"], "distance": round(d, 1), "overlaps": len(hits), "edge_points": pts,
                    "near": d <= NEAR and not hits and not pts,
                    "visible": inside_view(a, *view) and inside_view(note, *view)})
    return out


PAGE_NO = re.compile(r"^\s*(\d+)\s*/\s*(\d+)\s*$")


def page_number_count(texts, total):
    """'n / m' 모양이고 m이 문서의 페이지 수인 글의 개수."""
    return sum(1 for t in texts if (p := PAGE_NO.match(t)) and int(p.group(2)) == total)


def source_facts(html):
    """원문만으로 정하는 사실: RC.demo 호출 수(관리 블록 밖), SVG 유무, 페이지 id, 페이지형 여부."""
    js = doc_scripts(html)
    markup = re.sub(r"<script\b.*?</script>", "", html, flags=re.S | re.I)
    pages = [pid for _, pid, _ in PAGE_ID.findall(html)]
    has_svg = bool(re.search(r"<svg\b", markup, re.I) or "".join(MERMAID.findall(html)).strip()
                   or re.search(r"\bRC\.chart\s*\(", js))
    return {"demo_calls": len(re.findall(r"\bRC\.demo\s*\(", js)), "has_svg": has_svg,
            "pages": pages, "paged": bool(pages) and 'class="pager"' in html}
