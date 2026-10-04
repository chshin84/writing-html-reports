"""공통 부품 시험(checks/common.py): 관리 블록 제외와 금지어 검사. L1 소유."""
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from checks import anim, common, style  # noqa: E402
from helpers import page  # noqa: E402


class ManagedBlock(unittest.TestCase):
    def test_managed_block_is_excluded(self):
        block = ("<script>/* BEGIN report-charts echarts@6.1.0 mermaid@11.17.2 gsap@3.15.0 */\n"
                 "gsap.to(x,{repeat:-1}); var c='#123456';\n/* END report-charts */</script>")
        self.assertEqual(style.script_style_violations(page(head=block)), [])
        self.assertEqual(anim.script_motion_violations(page(head=block)), [])


class Banned(unittest.TestCase):
    def test_banned_word_in_script_string(self):
        fails = common.banned_violations(page(script="var s={name:'부분 합계'};"))
        self.assertTrue(any("'부분'" in f for f in fails))

    def test_banned_word_in_managed_block_is_ignored(self):
        block = "<script>/* BEGIN report-charts x */\nvar s='부분';\n/* END report-charts */</script>"
        self.assertEqual(common.banned_violations(page(head=block)), [])



if __name__ == "__main__":
    unittest.main()
