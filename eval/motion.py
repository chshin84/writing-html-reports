"""motion 애니메이션 항목: dwell·step-anim·step1·note-near·active-visible."""
from measure import dwell_steps, item, note_steps

ANIM = ("dwell", "step-anim", "step1", "note-near", "active-visible")
NOT_READY = "RC.demo 호출이 있는데 data-rc-ready가 오지 않았다(정적 목록으로 물러났거나 15초 초과)"


def judge_step1(r):
    return r["initial"] <= 0.05 + 1e-9 and r["reached"] and r["seconds"] >= 0.2 - 1e-9


def judge_step_anim(r):
    bad = [x for x in r["lengths"] if not 0.3 - 1e-9 <= x <= 2.6 + 1e-9]
    return not bad and r["held"] is not False, bad


def _combine(id_, rows):
    sts = [s for _, s, _, _ in rows]
    status = ("fail" if "fail" in sts else "unmeasurable" if "unmeasurable" in sts
              else "pass" if "pass" in sts else "n/a")
    detail = {f: d for f, _, _, d in rows if d is not None}
    return item(id_, "motion", status, {f: v for f, _, v, _ in rows}, detail or None)


def _run(sess, name, facts, mode, pid, script, arg):
    page, _ = sess.open(name, facts["demo_calls"], 1280, "light", mode, pid)
    try:
        return page.evaluate(script, arg)
    finally:
        page.close()


def motion_items(sess, name, facts, wanted, mode):
    want = [i for i in ANIM if i in wanted]
    if not want:
        return []
    if not facts["demo_calls"]:
        return [item(i, "motion", "n/a", detail="원문에 RC.demo 호출이 없다") for i in want]
    first = facts["pages"][0] if facts["pages"] else None
    page, ok = sess.open(name, facts["demo_calls"], 1280, "light", mode, first)
    try:
        demos = page.evaluate("() => __c0.demos()") if ok else []
    finally:
        page.close()
    if not ok:
        return [item(i, "motion", "unmeasurable", detail=NOT_READY) for i in want]
    rows = {i: [] for i in want}
    for d in demos:
        fid, pid, fmode = d["id"], d["page"], mode or d["mode"]
        if "step1" in rows:
            r = _run(sess, name, facts, mode, pid, "([id, m]) => __c0.step1(id, m)", [fid, fmode])
            rows["step1"].append((fid, "pass" if judge_step1(r) else "fail", r, None))
        if "dwell" in rows:
            if fmode != "auto":
                rows["dwell"].append((fid, "n/a", None, "단계 넘김 방식"))
            else:
                r = _run(sess, name, facts, mode, pid, "id => __c0.dwellSamples(id)", fid)
                steps = dwell_steps([(t, s) for t, s in r["samples"]], r["ends"])
                bad = [s for s in steps if not s["ok"]]
                status = "fail" if bad or r["timeScale"] != 1 else "pass"  # timeScale이 1이 아니면 타임라인 시간과 실제 재생 시간이 다르다
                rows["dwell"].append((fid, status,
                                      {"steps": len(steps), "fails": len(bad), "time_scale": r["timeScale"],
                                       "min_dwell": min((s["dwell"] for s in steps), default=None),
                                       "fails_after_step1": sum(not s["ok"] for s in steps[1:])}, steps))
        if "step-anim" in rows:
            if fmode != "step":
                rows["step-anim"].append((fid, "n/a", None, "자동 재생 방식"))
            else:
                r = _run(sess, name, facts, mode, pid, "id => __c0.stepAnim(id)", fid)
                good, bad = judge_step_anim(r)
                rows["step-anim"].append((fid, "pass" if good else "fail", r, bad or None))
        if "note-near" in rows or "active-visible" in rows:
            r = _run(sess, name, facts, mode, pid, "id => __c0.noteSteps(id)", fid)
            if not any(s["active_count"] for s in r["steps"]):
                for i in ("note-near", "active-visible"):
                    if i in rows:
                        rows[i].append((fid, "unmeasurable", None, "data-rc-active가 붙은 요소가 없다"))
            else:
                judged = note_steps(r["steps"], r["view"])
                if "note-near" in rows:
                    rows["note-near"].append((fid, "pass" if all(s["near"] for s in judged) else "fail",
                                              {"steps": len(judged), "fails": sum(not s["near"] for s in judged)}, judged))
                if "active-visible" in rows:
                    rows["active-visible"].append((fid, "pass" if all(s["visible"] for s in judged) else "fail",
                                                   {"steps": len(judged), "fails": sum(not s["visible"] for s in judged)}, judged))
    return [_combine(i, rows[i]) for i in want]
