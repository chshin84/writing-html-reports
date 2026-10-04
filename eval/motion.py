"""motion 애니메이션 항목: dwell·step-anim·step1·note-near·active-visible."""
from measure import dwell_steps, item, note_steps

ANIM = ("dwell", "step-anim", "step1", "note-near", "active-visible")
NOT_READY = "RC.demo 호출이 있는데 data-rc-ready가 오지 않았다(정적 목록으로 물러났거나 15초 초과)"
REOPEN = "다시 연 탭에서 data-rc-ready가 오지 않았다"
STUCK = "'다음'을 누를 수 없었다"


def judge_step1(r):
    """처음 연 상태가 0.05초 이하이고 e0에 닿아야 한다. 첫 단계 끝까지 걸린 시간은 벽시계와
    타임라인 기준((e0 - initial) ÷ timeScale) 모두 0.2초 이상이어야 한다. 프레임이 늦어 벽시계만 늘어난 거짓 통과를 막는다."""
    return (r["initial"] <= 0.05 + 1e-9 and r["reached"] and r["seconds"] >= 0.2 - 1e-9
            and (r["e0"] - r["initial"]) / r["timeScale"] >= 0.2 - 1e-9)


def judge_step_anim(r):
    """단계마다 타임라인 기준 연출 길이(deltas ÷ timeScale)가 0.3초 이상 2.6초 이하여야 한다. 벽시계 lengths는 기록만 한다.
    단계가 둘 이상인데 '다음'을 한 번도 누르지 못했거나 멈춤 확인(held)을 하지 못했으면 실패다. (통과 여부, 실패 내용)을 돌려준다."""
    if r["steps"] >= 2 and (not r["lengths"] or r["held"] is None):
        return False, STUCK
    ts = r["timeScale"]
    bad = [{"step": k + 1, "timeline": round(d / ts, 3)} for k, d in enumerate(r["deltas"])
           if not 0.3 - 1e-9 <= d / ts <= 2.6 + 1e-9]
    return not bad and r["held"] is not False, bad


def _combine(id_, rows):
    sts = [s for _, s, _, _ in rows]
    status = ("fail" if "fail" in sts else "unmeasurable" if "unmeasurable" in sts
              else "pass" if "pass" in sts else "n/a")
    detail = {f: d for f, _, _, d in rows if d is not None}
    return item(id_, "motion", status, {f: v for f, _, v, _ in rows}, detail or None)


def _run(sess, name, facts, mode, pid, script, arg):
    """figure마다 문서를 새 탭으로 열어 script를 실행한다. 다시 연 탭이 준비되지 않으면(demo_ok False) None을 돌려준다."""
    page, demo_ok = sess.open(name, facts["demo_calls"], 1280, "light", mode, pid)
    try:
        return page.evaluate(script, arg) if demo_ok else None
    finally:
        page.close()


def figure_rows(fid, fmode, want, run):
    """figure 하나의 항목별 행 {항목: (figure, status, value, detail)}을 만든다.
    run(script, arg)는 새 탭에서 script를 실행한 결과를 돌려주고, 그 탭이 준비되지 않았으면 None을 돌려준다.
    None이면 그 항목은 측정 불가다."""
    out = {}

    def missed(i):
        out[i] = (fid, "unmeasurable", None, REOPEN)

    if "step1" in want:
        r = run("([id, m]) => __c0.step1(id, m)", [fid, fmode])
        if r is None:
            missed("step1")
        else:
            out["step1"] = (fid, "pass" if judge_step1(r) else "fail", r, None)
    if "dwell" in want and fmode != "auto":
        out["dwell"] = (fid, "n/a", None, "단계 넘김 방식")
    elif "dwell" in want:
        r = run("id => __c0.dwellSamples(id)", fid)
        if r is None:
            missed("dwell")
        else:
            steps = dwell_steps([(t, s) for t, s in r["samples"]], r["ends"])
            bad = [s for s in steps if not s["ok"]]
            status = "fail" if bad or r["timeScale"] != 1 else "pass"  # timeScale이 1이 아니면 타임라인 시간과 실제 재생 시간이 다르다
            out["dwell"] = (fid, status,
                            {"steps": len(steps), "fails": len(bad), "time_scale": r["timeScale"],
                             "min_dwell": min((s["dwell"] for s in steps), default=None),
                             "fails_after_step1": sum(not s["ok"] for s in steps[1:])}, steps)
    if "step-anim" in want and fmode != "step":
        out["step-anim"] = (fid, "n/a", None, "자동 재생 방식")
    elif "step-anim" in want:
        r = run("id => __c0.stepAnim(id)", fid)
        if r is None:
            missed("step-anim")
        else:
            good, bad = judge_step_anim(r)
            out["step-anim"] = (fid, "pass" if good else "fail", r, bad or None)
    note_ids = [i for i in ("note-near", "active-visible") if i in want]
    if note_ids:
        r = run("id => __c0.noteSteps(id)", fid)
        if r is None:
            for i in note_ids:
                missed(i)
        elif not any(s["active_count"] for s in r["steps"]):
            for i in note_ids:
                out[i] = (fid, "unmeasurable", None, "data-rc-active가 붙은 요소가 없다")
        else:
            judged = note_steps(r["steps"], r["view"])
            if "note-near" in want:
                out["note-near"] = (fid, "pass" if all(s["near"] for s in judged) else "fail",
                                    {"steps": len(judged), "fails": sum(not s["near"] for s in judged)}, judged)
            if "active-visible" in want:
                out["active-visible"] = (fid, "pass" if all(s["visible"] for s in judged) else "fail",
                                         {"steps": len(judged), "fails": sum(not s["visible"] for s in judged)}, judged)
    return out


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
        fid, pid = d["id"], d["page"]
        got = figure_rows(fid, mode or d["mode"], want,
                          lambda script, arg: _run(sess, name, facts, mode, pid, script, arg))
        for i in want:
            rows[i].append(got[i])
    return [_combine(i, rows[i]) for i in want]
