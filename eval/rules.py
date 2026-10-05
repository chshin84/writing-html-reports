"""규칙 항목: 현재 워크트리의 checks/와, 주면 기준 커밋의 checks/ 사본으로 각각 실행한다. 둘 다 위반 0건이어야 통과다."""
import json
import os
import subprocess
import sys
from pathlib import Path

from measure import TARGET, item

ROOT = Path(__file__).resolve().parent.parent
MODULES = {"rules-motion": ["anim"], "rules-layout": ["style"], "rules-all": ["style", "anim", "content", "common"]}
RUNNER = r'''
import contextlib, importlib, importlib.util, json, sys
d, mods, path = sys.argv[1], sys.argv[2].split(","), sys.argv[3]
spec = importlib.util.spec_from_file_location("checks", d + "/__init__.py", submodule_search_locations=[d])
pkg = importlib.util.module_from_spec(spec)
sys.modules["checks"] = pkg
spec.loader.exec_module(pkg)
html = open(path, encoding="utf-8").read()
out = []
with contextlib.redirect_stdout(sys.stderr):  # 규칙 함수의 '참고:' 출력이 JSON을 더럽히지 않게 한다
    for m in mods:
        for fn, mode in importlib.import_module("checks." + m).RULES:
            out += fn(html, None) if mode == "old" else fn(html)
print(json.dumps(out, ensure_ascii=False))
'''


def violations(checks_dir, modules, html_path):
    """checks_dir의 규칙 모듈(RULES)을 따로 띄운 파이썬에서 실행해 위반 문장 목록을 돌려준다.
    옛 checks의 금지어 검사(common)는 checks_dir의 부모 폴더에 있는 금지어.md 사본을 읽으므로, 그 사본이 없으면 멈춘다.
    지금 checks는 dc코더 원본을 읽는다(사본 삭제 2026-10-05)."""
    old_style = '"금지어.md"' in (Path(checks_dir) / "common.py").read_text(encoding="utf-8")
    if "common" in modules and old_style and not (Path(checks_dir).parent / "금지어.md").exists():
        raise RuntimeError(f"{Path(checks_dir).parent}에 금지어.md가 없어 금지어 검사를 할 수 없다")
    r = subprocess.run([sys.executable, "-B", "-c", RUNNER, str(checks_dir), ",".join(modules), str(html_path)],
                       capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    if r.returncode:
        raise RuntimeError(f"규칙 실행 실패({checks_dir}): {r.stderr.strip()[-500:]}")
    return json.loads(r.stdout)


def rule_items(html_path, wanted, base_checks=None):
    out = []
    for id_, mods in MODULES.items():
        if id_ not in wanted:
            continue
        cand = violations(ROOT / "checks", mods, html_path)
        base = violations(Path(base_checks), mods, html_path) if base_checks else None
        out.append(item(id_, TARGET[id_], "fail" if cand or base else "pass",
                        {"candidate": len(cand), "base": None if base is None else len(base)},
                        (cand + (base or []))[:20] or None))
    return out
