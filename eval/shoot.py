"""검토용 장면 명령.

사용법: python eval/shoot.py <html> <출력 폴더> [--mode auto|step]
페이지형 문서는 페이지마다(전체 높이), 단일 문서는 화면 높이 단위(v1, v2 …)로 1280×800과 390×844 장면을 찍는다.
애니메이션은 figure마다 윗변을 창 윗변에 맞춘 뒤, 엔진의 '처음부터'·'다음' 버튼으로 단계를 넘기며 단계 끝 장면을 1280 폭에서 찍는다.
페이지별 보이는 글(<페이지>.txt, 단일 문서는 doc.txt)과 장면 목록(index.json)을 함께 남긴다. 환경 실패면 종료 코드 2.
다시 연 탭에서 data-rc-ready가 오지 않은 figure는 단계 장면을 생략하고 index.json에 {"kind": "skipped", "figure", "reason"}을 남긴다.
출력 폴더가 있고 비어 있지 않으면 이전 장면이 섞이지 않게 아무것도 지우지 않고 종료 코드 1로 멈춘다.
"""
import argparse
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import VIEW, EnvFail, Session  # noqa: E402
from measure import source_facts  # noqa: E402

TEXT = "() => document.body.innerText"
REOPEN = "다시 연 탭에서 data-rc-ready가 오지 않았다"


def shoot(path, out, mode=None):
    path, out = Path(path).resolve(), Path(out)
    facts = source_facts(path.read_text(encoding="utf-8"))
    out.mkdir(parents=True, exist_ok=True)
    index = []
    with Session(path.parent) as sess:
        for w in (1280, 390):
            for pid in facts["pages"] or [None]:
                page, _ = sess.open(path.name, facts["demo_calls"], w, "light", mode, pid)
                try:
                    if pid:
                        name = f"{pid}-{w}.png"
                        page.screenshot(path=str(out / name), full_page=True)
                        index.append({"file": name, "kind": "page", "page": pid, "width": w})
                        if w == 1280:
                            (out / f"{pid}.txt").write_text(page.evaluate(TEXT), encoding="utf-8")
                    else:
                        h = VIEW[w]["height"]
                        total = page.evaluate("() => document.documentElement.scrollHeight")
                        for k in range(max(1, math.ceil(total / h))):
                            page.evaluate("y => scrollTo(0, y)", k * h)
                            name = f"v{k + 1}-{w}.png"
                            page.screenshot(path=str(out / name))
                            index.append({"file": name, "kind": "page", "page": f"v{k + 1}", "width": w})
                        if w == 1280:
                            (out / "doc.txt").write_text(page.evaluate(TEXT), encoding="utf-8")
                finally:
                    page.close()
        first = facts["pages"][0] if facts["pages"] else None
        demos = []
        if facts["demo_calls"]:
            page, ok = sess.open(path.name, facts["demo_calls"], 1280, "light", mode, first)
            try:
                demos = page.evaluate("() => __c0.demos()") if ok else []
            finally:
                page.close()
        for d in demos:
            page, ok = sess.open(path.name, facts["demo_calls"], 1280, "light", mode, d["page"])
            try:
                if not ok:
                    index.append({"kind": "skipped", "figure": d["id"], "reason": REOPEN})
                    continue
                ends = page.evaluate("id => __c0.ends(document.getElementById(id)._rcTl)", d["id"])
                page.evaluate("id => { var f = document.getElementById(id); scrollTo(0, f.getBoundingClientRect().top + scrollY); }", d["id"])
                for i, e in enumerate(ends):  # 측정기와 같이 엔진 버튼으로 단계를 넘겨, 독자가 보는 장면을 찍는다
                    page.evaluate("([id, i]) => __c0.toStep(id, i)", [d["id"], i])
                    name = f"{d['id']}-s{i + 1}.png"
                    page.screenshot(path=str(out / name))
                    index.append({"file": name, "kind": "step", "page": d["page"], "width": 1280, "figure": d["id"],
                                  "step": i + 1, "seconds": round(e - (ends[i - 1] if i else 0), 2),
                                  "mode": page.evaluate("id => document.getElementById(id).dataset.rcMode || null", d["id"])})
            finally:
                page.close()
    (out / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return index


def main(argv=None):
    ap = argparse.ArgumentParser(description="검토용 페이지·단계 장면과 보이는 글을 만든다")
    ap.add_argument("html")
    ap.add_argument("out")
    ap.add_argument("--mode", choices=["auto", "step"])
    a = ap.parse_args(argv)
    out = Path(a.out)
    if out.exists() and any(out.iterdir()):
        print(f"출력 폴더가 비어 있지 않다: {out}. 이전 장면이 섞이지 않게 빈 폴더나 새 경로를 준다", file=sys.stderr)
        return 1
    try:
        idx = shoot(a.html, a.out, a.mode)
    except EnvFail as e:
        print(f"환경 실패: {e}", file=sys.stderr)
        return 2
    print(f"장면 {len(idx)}개를 {a.out}에 남겼다")
    return 0


if __name__ == "__main__":
    sys.exit(main())
