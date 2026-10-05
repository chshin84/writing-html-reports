"""기계 판정 명령.

사용법: python eval/gates.py <html>… [--mode auto|step] [--only motion|layout|content] [--base-checks <폴더>] [--judge-hash-nav] [--out <결과.json>]
문서마다 밝은 테마 기록(모든 항목)과 어두운 테마 기록(contrast-text·contrast-graphic·cvd)을 JSON 목록으로 출력한다.
기록 형태: {file, mode, theme, env, items: [{id, target, status, value, detail}], load_errors, render_fail}. status는 pass·fail·unmeasurable·n/a.
env는 ok·env-fail·error다. env-fail과 error 기록에는 error 메시지가 붙는다.
종료 코드: 환경 실패가 하나라도 있으면 2, 측정기 오류가 있으면 3, fail·unmeasurable·같은 출처 요청 실패·렌더 실패가 하나라도 있으면 1, 모두 통과하면 0.
hash-nav는 --judge-hash-nav가 없으면 기록만 하고(value.recorded_only) 종료 코드에서 뺀다. 고정 견본의 페이지 전환 코드는 관리 블록 밖이기 때문이다.
--base-checks는 기준 커밋 checkout의 checks/ 폴더다. spec 「기계 판정」대로 L1의 공식 측정이 쓴다. 옛 checks가 읽는 금지어.md 사본이 그 부모 폴더에 없으면 멈춘다.
규칙 항목은 gates.py가 놓인 워크트리의 checks/로 실행한다. 후보를 판정할 때는 후보 워크트리의 eval/gates.py를 실행하고,
기준 커밋 규칙은 --base-checks로 함께 실행한다.
문서를 열기 전의 예외(파일 없음, Chromium 실행 실패 등)도 그 문서의 밝은 테마 error 기록으로 남긴다.
"""
import argparse
import json
import sys
import traceback
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from harness import EnvFail, Session  # noqa: E402
from layout import dark_items, light_items  # noqa: E402
from measure import ORDER, RULE_IDS, TARGET, THEMED, source_facts  # noqa: E402
from motion import motion_items  # noqa: E402
from rules import rule_items  # noqa: E402


def measure_file(path, mode, only, base_checks, judge_hash=False):
    path = Path(path).resolve()
    html = path.read_text(encoding="utf-8")
    facts = source_facts(html)
    wanted = {i for i in ORDER if only is None or TARGET[i] == only}
    records = []

    def record(theme):
        return {"file": str(path), "mode": mode or "default", "theme": theme, "env": "ok", "items": [],
                "load_errors": [], "render_fail": []}

    def guarded(rec, work):
        try:
            rec["items"] = sorted(work(), key=lambda x: ORDER.index(x["id"]))
        except EnvFail as e:
            rec.update(env="env-fail", error=str(e), items=[])
        except Exception as e:  # 측정기 오류는 판정 실패(1)와 섞이지 않게 따로 기록한다
            rec.update(env="error", error=f"{type(e).__name__}: {e}", trace=traceback.format_exc()[-1500:], items=[])

    if not wanted - RULE_IDS:  # 규칙 항목만 원하면 브라우저를 띄우지 않는다
        rec = record("light")
        guarded(rec, lambda: rule_items(path, wanted, base_checks))
        return [rec]
    with Session(path.parent) as sess:
        for theme in ("light", "dark"):
            w = wanted if theme == "light" else wanted & THEMED
            if not w:
                continue
            rec = record(theme)
            if theme == "light":
                guarded(rec, lambda: motion_items(sess, path.name, facts, w, mode)
                        + light_items(sess, path.name, facts, w, mode, judge_hash) + rule_items(path, w, base_checks))
            else:
                guarded(rec, lambda: dark_items(sess, path.name, facts, w, mode))
            rec["load_errors"] = sorted(sess.notes["load_errors"])
            rec["render_fail"] = sorted(sess.notes["render_fail"])
            records.append(rec)
    return records


def exit_code(records):
    if any(r["env"] == "env-fail" for r in records):
        return 2
    if any(r["env"] == "error" for r in records):
        return 3
    failed = any(i["status"] in ("fail", "unmeasurable") and not (i["value"] or {}).get("recorded_only")
                 for r in records for i in r["items"])
    return 1 if failed or any(r["load_errors"] or r["render_fail"] for r in records) else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="고정 견본의 판정 항목을 측정해 JSON으로 출력한다")
    ap.add_argument("html", nargs="+")
    ap.add_argument("--mode", choices=["auto", "step"])
    ap.add_argument("--only", choices=["motion", "layout", "content"])
    ap.add_argument("--base-checks")
    ap.add_argument("--judge-hash-nav", action="store_true", help="hash-nav를 종료 코드에 넣는다(template-paged.html·재생성본)")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    records = []
    for h in a.html:
        try:
            records += measure_file(h, a.mode, a.only, a.base_checks, a.judge_hash_nav)
        except Exception as e:  # guarded 밖의 예외(파일 없음, 세션 진입 실패)도 판정 실패(1)와 섞이지 않게 기록한다
            records.append({"file": str(Path(h).resolve()), "mode": a.mode or "default", "theme": "light", "env": "error",
                            "error": f"{type(e).__name__}: {e}", "items": [], "load_errors": [], "render_fail": []})
        if a.out:  # 문서마다 써 두어 뒤 문서에서 멈춰도 앞 기록이 남는다
            Path(a.out).write_text(json.dumps(records, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(records, ensure_ascii=False, indent=1))
    return exit_code(records)


if __name__ == "__main__":
    sys.exit(main())
