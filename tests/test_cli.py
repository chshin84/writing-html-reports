"""check.py 명령줄 시험: 템플릿 통과, 파일당 애니메이션 상한, 원본 대조. L1 소유."""
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import ROOT, anim_page, page, run_check  # noqa: E402


class Templates(unittest.TestCase):
    def test_templates_pass(self):
        for name in ("template.html", "template-paged.html"):
            r = run_check(ROOT / name)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class DemoCount(unittest.TestCase):
    def run_page(self, n):
        body = "".join(f'<figure id="d{i}" data-anim="구조"><svg></svg></figure>' for i in range(n))
        script = "".join(f"RC.demo(document.getElementById('d{i}'),[]);" for i in range(n))
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "doc.html"
            f.write_text(page(body=body, script=script), encoding="utf-8")
            return run_check(f)

    def test_four_demos_violation(self):
        r = self.run_page(4)
        self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
        self.assertIn("애니메이션 4개", r.stdout)

    def test_three_demos_ok(self):
        self.assertEqual(self.run_page(3).returncode, 0)


class Original(unittest.TestCase):
    def test_script_violation_already_in_original_is_note_only(self):
        with tempfile.TemporaryDirectory() as d:
            html = page(body="<p>가</p>", script="gsap.to(a,{x:1})")
            new, old = Path(d) / "new.html", Path(d) / "old.html"
            new.write_text(html, encoding="utf-8")
            old.write_text(html, encoding="utf-8")
            r = run_check(new, old)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("참고: 원본에 있던 스크립트 위반", r.stdout)

    def test_anim_violation_already_in_original_is_note_only(self):
        with tempfile.TemporaryDirectory() as d:
            html = anim_page([("page", "p2", ["d1"])])
            new, old = Path(d) / "new.html", Path(d) / "old.html"
            new.write_text(html, encoding="utf-8")
            old.write_text(html, encoding="utf-8")
            r = run_check(new, old)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("참고: 원본에 있던 애니메이션 위반", r.stdout)

    def test_new_anim_violation_counts_even_with_original(self):
        with tempfile.TemporaryDirectory() as d:
            new, old = Path(d) / "new.html", Path(d) / "old.html"
            new.write_text(anim_page([("page", "p2", ["d1"]), ("page", "p3", ["d2"])]), encoding="utf-8")
            old.write_text(anim_page([("page", "p2", ["d1"])]), encoding="utf-8")
            r = run_check(new, old)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn("p3 별 표시 없는 페이지", r.stdout)


if __name__ == "__main__":
    unittest.main()
