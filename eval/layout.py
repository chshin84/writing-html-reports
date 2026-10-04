"""layout 항목과 390 폭 motion 항목(svg-font-390·figure-overflow-390)의 측정과 판정."""
from measure import TARGET, blend, contrast, cvd_pairs, escapes, item, page_number_count, parse_color, text_threshold

SERIES = ("s1", "s2", "s3", "s4")
W390 = {"svg-font-390", "figure-overflow-390", "html-font-390", "overflow-390", "table-col-390"}


def _uniq(rows, keys):
    seen, out = set(), []
    for r in rows:
        k = tuple(r.get(x) for x in keys)
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def font_item(id_, target, fonts):
    if not fonts:
        return item(id_, target, "pass", {"count": 0, "min_px": None, "small": 0})
    small = [f for f in fonts if f["px"] < 11 - 1e-6]
    return item(id_, target, "fail" if small else "pass",
                {"count": len(fonts), "min_px": min(f["px"] for f in fonts), "small": len(small)},
                _uniq(small, ("text", "px"))[:15] or None)


def _pairs(records, need_of):
    """요소 불투명도(op)는 글자색 알파에 곱해 바탕과 합성한다. 바탕이나 색을 정할 수 없으면 측정 불가로 센다."""
    bad, ratios, unm = [], [], 0
    for r in records:
        fg = parse_color(r.get("fg"))
        bg = parse_color(r["bg"]) if r.get("bg") else None
        if r.get("why") or not fg or not bg or bg[3] < 0.999:
            unm += 1
            continue
        a = fg[3] * r.get("op", 1.0)
        if a < 0.999:
            fg = blend(fg[:3] + (a,), bg)
        ratio, need = contrast(fg, bg), need_of(r)
        ratios.append(ratio)
        if ratio + 1e-9 < need:
            bad.append(dict(r, ratio=round(ratio, 2), need=need))
    return bad, ratios, unm


def contrast_text_item(records):
    bad, ratios, unm = _pairs(records, lambda r: text_threshold(r["px"], r["weight"]))
    return item("contrast-text", "layout", "fail" if bad else "pass",
                {"checked": len(ratios), "unmeasurable": unm, "fails": len(bad),
                 "min_ratio": round(min(ratios), 2) if ratios else None},
                _uniq(bad, ("text", "fg", "bg"))[:15] or None)


def contrast_graphic_item(records):
    bad, ratios, unm = _pairs(records, lambda r: 3.0)
    return item("contrast-graphic", "layout", "fail" if bad else "pass",
                {"checked": len(ratios), "unmeasurable": unm, "fails": len(bad),
                 "min_ratio": round(min(ratios), 2) if ratios else None},
                _uniq(bad, ("kind", "name", "fg", "bg"))[:15] or None)


def cvd_item(tokens):
    """정의하지 않은 토큰(빈 값)은 빼고, 값이 있는데 읽지 못한 토큰이 하나라도 있으면 실패로 하고 detail에 그 토큰을 적는다."""
    given = {k: v for k, v in tokens.items() if v.strip()}
    colors = {k: parse_color(v) for k, v in given.items() if parse_color(v)}
    unreadable = {k: v for k, v in given.items() if k not in colors}
    pairs = cvd_pairs(colors)
    bad = [{"a": a, "b": b, "de": de} for a, b, de in pairs if de < 15]
    detail = dict({"unreadable": unreadable}, **({"pairs": bad} if bad else {})) if unreadable else bad or None
    return item("cvd", "layout", "fail" if bad or unreadable or len(colors) < 2 else "pass",
                {"tokens": tokens, "min_de": min((de for _, _, de in pairs), default=None)}, detail)


def overflow_item(layouts):
    """문서 스크롤 폭이 창 폭을 넘거나, html·body가 overflow-x hidden·clip으로 넘침을 감추면 실패다."""
    bad = {p: {"scroll_width": v["scrollWidth"], "width": v["width"], "root_clip": v.get("rootClip", False)}
           for p, v in layouts.items() if v["scrollWidth"] > v["width"] or v.get("rootClip")}
    return item("overflow-390", "layout", "fail" if bad else "pass",
                {"max_scroll_width": max((v["scrollWidth"] for v in layouts.values()), default=None)}, bad or None)


def figure_item(layouts):
    bad = [{"page": p, **f} for p, v in layouts.items() for f in v["figures"] if escapes(f["box"], v["width"])]
    return item("figure-overflow-390", "motion", "fail" if bad else "pass",
                {"figures": sum(len(v["figures"]) for v in layouts.values())}, bad[:10] or None)


def table_item(layouts):
    cells = [dict(c, page=p) for p, v in layouts.items() for c in v["cells"]]
    bad = [c for c in cells if c["w"] < 56 - 1e-6]
    return item("table-col-390", "layout", "fail" if bad else "pass",
                {"cells": len(cells), "min_w": min((c["w"] for c in cells), default=None)}, bad[:10] or None)


def page_number_item(per_page, total):
    counts = {p: page_number_count(t, total) for p, t in per_page.items()}
    return item("page-number", "layout", "pass" if all(c == 1 for c in counts.values()) else "fail", counts)


def _na(ids, why):
    return [item(i, TARGET[i], "n/a", detail=why) for i in ids]


def _pages(facts):
    return facts["pages"] or [None]


def _demos_on(page, pid):
    return [d for d in page.evaluate("() => __c0.demos()") if pid is None or d["page"] == pid]


def _measure_390(sess, name, facts, mode):
    lay, svg_steps = {}, []
    for pid in _pages(facts):
        page, demo_ok = sess.open(name, facts["demo_calls"], 390, "light", mode, pid)
        try:
            lay[pid] = page.evaluate("() => __c0.layout()")
            if demo_ok:
                for d in _demos_on(page, pid):
                    svg_steps += page.evaluate("id => __c0.svgFontSteps(id)", d["id"])
        finally:
            page.close()
    return lay, svg_steps


def _theme_pass(sess, name, facts, theme, mode, want_numbers):
    texts, graphics, numbers, tokens = [], [], {}, None
    for pid in _pages(facts):
        page, demo_ok = sess.open(name, facts["demo_calls"], 1280, theme, mode, pid)
        try:
            if tokens is None:
                tokens = page.evaluate("n => __c0.tokens(n)", list(SERIES))
            if want_numbers:
                numbers[pid] = page.evaluate("() => __c0.pageNumbers()")
            r = page.evaluate("() => __c0.contrast()")
            texts += r["text"]
            graphics += r["graphic"]
            if demo_ok:
                for d in _demos_on(page, pid):
                    graphics += page.evaluate("id => __c0.graphicSteps(id)", d["id"])
        finally:
            page.close()
    return texts, graphics, numbers, tokens


def _theme_items(texts, graphics, tokens, wanted):
    out = []
    if "contrast-text" in wanted:
        out.append(contrast_text_item(texts))
    if "contrast-graphic" in wanted:
        out.append(contrast_graphic_item(graphics))
    if "cvd" in wanted:
        out.append(cvd_item(tokens))
    return out


def hash_nav_item(sess, name, facts, mode, judged):
    """judged가 False면 기록만 한다(value.recorded_only). 고정 견본의 페이지 전환 코드는 관리 블록 밖이기 때문이다."""
    page, _ = sess.open(name, facts["demo_calls"], 1280, "light", mode, "p2", verify=False)
    try:
        first = page.evaluate("() => __c0.shown('p2')")
    finally:
        page.close()
    page, _ = sess.open(name, facts["demo_calls"], 1280, "light", mode, "p1", verify=False)
    try:
        page.evaluate("() => { location.hash = '#p2'; }")
        page.wait_for_timeout(500)
        second = page.evaluate("() => __c0.shown('p2')")
    finally:
        page.close()
    return item("hash-nav", "layout", "pass" if first and second else "fail",
                {"open_with_hash": first, "hash_change": second, "recorded_only": not judged})


def light_items(sess, name, facts, wanted, mode, judge_hash=False):
    out = []
    svg_ids = wanted & {"svg-font-390", "figure-overflow-390"}
    if svg_ids and not facts["has_svg"]:
        out += _na(sorted(svg_ids), "원문에 SVG가 없다")
    if (wanted & W390) - (svg_ids if not facts["has_svg"] else set()):
        lay, svg_steps = _measure_390(sess, name, facts, mode)
        if facts["has_svg"] and "svg-font-390" in wanted:
            out.append(font_item("svg-font-390", "motion", [f for v in lay.values() for f in v["svgFonts"]] + svg_steps))
        if facts["has_svg"] and "figure-overflow-390" in wanted:
            out.append(figure_item(lay))
        if "html-font-390" in wanted:
            out.append(font_item("html-font-390", "layout", [f for v in lay.values() for f in v["htmlFonts"]]))
        if "overflow-390" in wanted:
            out.append(overflow_item(lay))
        if "table-col-390" in wanted:
            out.append(table_item(lay))
    paged_ids = wanted & {"page-number", "hash-nav"}
    if paged_ids and not facts["paged"]:
        out += _na(sorted(paged_ids), "페이지형 문서가 아니다")
    want_numbers = facts["paged"] and "page-number" in wanted
    if wanted & {"contrast-text", "contrast-graphic", "cvd"} or want_numbers:
        texts, graphics, numbers, tokens = _theme_pass(sess, name, facts, "light", mode, want_numbers)
        out += _theme_items(texts, graphics, tokens, wanted)
        if want_numbers:
            out.append(page_number_item(numbers, len(facts["pages"])))
    if facts["paged"] and "hash-nav" in wanted:
        out.append(hash_nav_item(sess, name, facts, mode, judge_hash) if len(facts["pages"]) >= 2
                   else item("hash-nav", "layout", "n/a", detail="2페이지가 없다"))
    return out


def dark_items(sess, name, facts, wanted, mode):
    if not wanted & {"contrast-text", "contrast-graphic", "cvd"}:
        return []
    texts, graphics, _, tokens = _theme_pass(sess, name, facts, "dark", mode, False)
    return _theme_items(texts, graphics, tokens, wanted)
