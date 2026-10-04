"""체크리스트 3회 결과 묶기.

사용법: python eval/checklist_vote.py <결과 폴더> <출력.json> [--override <보정 폴더>]…
결과 폴더의 <견본>-run<k>.json(항목마다 {id, answer, evidence}의 목록)을 견본·항목별로 묶어
다수결, 흔들림(세 결과가 모두 같지 않음), 적용 대상별 충족률을 낸다.
보정 폴더는 문구를 고친 항목만 다시 측정한 결과다. 뒤에 준 폴더일수록 우선하며, 그 폴더에 있는 (견본, 항목)의 세 결과를 통째로 바꾼다.
현재 checklist.md에 없는 항목(뺀 항목)은 묶지 않는다.
입력 검사: 결과 폴더는 견본마다 실행 결과가 정확히 3개여야 하고, 보정 폴더는 항목마다 답이 3개여야 한다.
답은 '예'·'아니오'·'해당 없음' 중 하나여야 한다. 어기면 견본·항목·값을 적은 ValueError로 멈춘다.
다수결: 둘 이상 같은 답이 다수결이고, 셋이 모두 다르면 '아니오'다('해당 없음'이 끼어 있기 때문이다).
충족률: 다수결이 '예'인 항목 수 ÷ 다수결이 '해당 없음'이 아닌 항목 수. 분모가 0이면 null.
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
YES, NO, NA = "예", "아니오", "해당 없음"
TARGETS = ("motion", "layout", "content")


def load_items(path=ROOT / "eval" / "checklist.md"):
    items = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        cols = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cols) == 5 and re.fullmatch(r"`[a-z0-9-]+`", cols[0]):
            items.append({"id": cols[0].strip("`"), "category": cols[1], "target": cols[2],
                          "question": cols[3], "defect": cols[4]})
    return items


def majority(answers):
    top, k = Counter(answers).most_common(1)[0]
    return top if k >= 2 else NO


def stable(answers):
    return len(set(answers)) == 1


def answers(runs):
    """{견본: [회차별 답 목록]}을 {견본: {항목: [답…]}}으로 바꾼다."""
    out = {}
    for sample, rs in runs.items():
        per = defaultdict(list)
        for r in rs:
            for a in r:
                per[a["id"]].append(a["answer"])
        out[sample] = dict(per)
    return out


def merge(base, *overrides):
    """보정 결과가 있는 (견본, 항목)은 보정 결과로 통째로 바꾼다."""
    out = {s: dict(v) for s, v in base.items()}
    for o in overrides:
        for s, per in o.items():
            out.setdefault(s, {}).update(per)
    return out


def tally(per_sample, items):
    """per_sample: {견본: {항목: [답…]}}."""
    target = {i["id"]: i["target"] for i in items}
    samples, coverage = {}, {}
    for sample, per in per_sample.items():
        per = {i: v for i, v in per.items() if i in target}
        samples[sample] = {i: {"runs": v, "majority": majority(v), "stable": stable(v)} for i, v in per.items()}
        cov = {}
        for t in TARGETS:
            got = [x["majority"] for i, x in samples[sample].items() if target.get(i) == t and x["majority"] != NA]
            cov[t] = round(got.count(YES) / len(got), 3) if got else None
        coverage[sample] = cov
    return {"samples": samples, "coverage": coverage}


def load_runs(folder, partial=False):
    """partial이 True면 보정 폴더로 보고, 견본별 실행 결과 수 대신 항목별 답 수가 3인지 검사한다."""
    runs = defaultdict(list)
    for p in sorted(Path(folder).glob("*-run*.json")):
        runs[re.sub(r"-run\d+$", "", p.stem)].append(json.loads(p.read_text(encoding="utf-8")))
    for sample, rs in runs.items():
        if not partial and len(rs) != 3:
            raise ValueError(f"{folder}: 견본 {sample}의 실행 결과가 {len(rs)}개다(3개여야 한다)")
        for r in rs:
            for a in r:
                if a["answer"] not in (YES, NO, NA):
                    raise ValueError(f"{folder}: 견본 {sample} 항목 {a['id']}의 답 {a['answer']!r}는 '예'·'아니오'·'해당 없음'이 아니다")
    out = answers(dict(runs))
    if partial:
        for sample, per in out.items():
            for i, v in per.items():
                if len(v) != 3:
                    raise ValueError(f"{folder}: 견본 {sample} 항목 {i}의 답이 {len(v)}개다(3개여야 한다)")
    return out


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="체크리스트 3회 결과를 다수결로 묶는다")
    ap.add_argument("folder")
    ap.add_argument("out")
    ap.add_argument("--override", action="append", default=[])
    a = ap.parse_args(argv)
    per = merge(load_runs(a.folder), *[load_runs(o, partial=True) for o in a.override])
    res = tally(per, load_items())
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"견본 {len(per)}개의 결과를 {a.out}에 묶었다")
    return 0


if __name__ == "__main__":
    sys.exit(main())
