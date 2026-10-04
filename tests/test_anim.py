"""애니메이션·차트 스크립트 규칙 시험(checks/anim.py). C1 소유."""
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from checks import anim  # noqa: E402
from helpers import ROOT, anim_page, has, page  # noqa: E402


class ScriptMotion(unittest.TestCase):
    def test_chart_animation_true(self):
        self.assertTrue(has(anim.script_motion_violations(page(script="RC.chart(b,{animation: true})")), "차트 애니메이션"))

    def test_chart_animation_false_ok(self):
        self.assertEqual(anim.script_motion_violations(page(script="RC.chart(b,{animation: false})")), [])

    def test_gsap_direct_call(self):
        self.assertTrue(has(anim.script_motion_violations(page(script="gsap.to(a,{x:1})")), "GSAP 직접 호출"))

    def test_repeat_with_spaces(self):
        self.assertTrue(has(anim.script_motion_violations(page(script="tl.to(a,{repeat : -1})")), "GSAP 직접 호출"))

    def test_timeline_calls_ok(self):
        self.assertEqual(anim.script_motion_violations(page(script="tl.to(a,{x:1}).set(b,{y:0})")), [])

    def test_chart_decoration(self):
        for js in ("{shadowBlur:4}", "{borderRadius:4}", "{borderRadius:[0,4,4,0]}"):
            self.assertTrue(has(anim.script_motion_violations(page(script=js)), "차트 장식"), js)
        self.assertEqual(anim.script_motion_violations(page(script="{borderRadius:2}")), [])
        self.assertEqual(anim.script_motion_violations(page(script="{shadowBlur: 0}")), [])



class Anim(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(anim.anim_violations(anim_page([("page core", "p2", ["d1"])])), [])

    def test_missing_type(self):
        html = page(body='<figure id="d1"><svg></svg></figure>', script="RC.demo(document.getElementById('d1'),[]);")
        self.assertTrue(any("유형 누락" in f for f in anim.anim_violations(html)))

    def test_waiting_type(self):
        fails = anim.anim_violations(anim_page([("page core", "p2", ["d1"])], typ="선별"))
        self.assertTrue(any("견본 대기" in f for f in fails))

    def test_unknown_type(self):
        fails = anim.anim_violations(anim_page([("page core", "p2", ["d1"])], typ="회전"))
        self.assertTrue(any("목록에 없다" in f for f in fails))

    def test_two_on_one_page(self):
        fails = anim.anim_violations(anim_page([("page core", "p2", ["d1", "d2"])]))
        self.assertTrue(any("페이지당 1개" in f for f in fails))

    def test_unstarred_page(self):
        fails = anim.anim_violations(anim_page([("page", "p2", ["d1"])]))
        self.assertTrue(any("별 표시 없는 페이지" in f for f in fails))

    def test_demo_without_figure_id(self):
        fails = anim.anim_violations(page(body="<p>가</p>", script="RC.demo(a,[]);"))
        self.assertTrue(any("getElementById" in f for f in fails))

class ListSync(unittest.TestCase):
    def test_skill_table_matches_check(self):
        text = (ROOT / "시각화.md").read_text(encoding="utf-8")
        sec = text.split("\n## 애니메이션\n", 1)[1].split("\n## ", 1)[0]
        rows = {}
        for line in sec.splitlines():
            cols = [c.strip() for c in line.strip().strip("|").split("|")]
            if line.startswith("|") and len(cols) >= 2 and cols[-1] in ("사용 가능", "견본 대기"):
                rows[cols[0]] = cols[-1]
        self.assertEqual(rows, anim.ANIM_TYPES)



if __name__ == "__main__":
    unittest.main()
