"""C0 순수 측정 함수 시험. 실행: python -B -m unittest discover -s tests"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
import measure as m  # noqa: E402

WHITE = (255, 255, 255, 1.0)


class Chars(unittest.TestCase):
    def test_spaces_removed_and_number_group_is_one(self):
        self.assertEqual(m.chars("고점 15 → -2bp"), len("고점#→-#bp"))
        self.assertEqual(m.chars("1,234.5원"), 2)


class Dwell(unittest.TestCase):
    def test_dwell_and_n(self):
        samples = [(0.0, {}), (0.5, {"a": "가나"}), (1.0, {"a": "가나다라"}), (4.0, {"a": "가나다라"})]
        s = m.dwell_steps(samples, [4.0])[0]
        self.assertEqual((s["done"], s["dwell"], s["n"]), (1.0, 3.0, 4))
        self.assertAlmostEqual(s["lo"], 1.5)
        self.assertTrue(s["ok"])

    def test_short_dwell_fails_and_unchanged_element_not_counted(self):
        samples = [(0.0, {"k": "같다"}), (1.0, {"k": "같다"}), (1.05, {"k": "같다", "c": "새 글"}), (1.32, {"k": "같다", "c": "새 글"})]
        s = m.dwell_steps(samples, [1.0, 1.32])[1]
        self.assertEqual(s["n"], 2)
        self.assertAlmostEqual(s["dwell"], 0.27, places=3)
        self.assertFalse(s["ok"])

    def test_changed_text_counts_whole_new_text_and_upper_bound(self):
        samples = [(0.0, {"k": "옛 글"}), (0.1, {"k": "새 글자"}), (9.0, {"k": "새 글자"})]
        s = m.dwell_steps(samples, [9.0])[0]
        self.assertEqual(s["n"], 3)
        self.assertFalse(s["ok"])  # 8.9초 > 1 + 3/8 + 3


class Color(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(m.parse_color("#8FA3BC"), (143, 163, 188, 1.0))
        self.assertEqual(m.parse_color("rgba(0, 0, 0, 0)"), (0.0, 0.0, 0.0, 0.0))
        self.assertEqual(m.parse_color("rgb(31, 58, 95)"), (31.0, 58.0, 95.0, 1.0))
        self.assertIsNone(m.parse_color("url(#g)"))

    def test_contrast_known_values(self):
        self.assertAlmostEqual(m.contrast(m.parse_color("#8FA3BC"), WHITE), 2.58, places=2)
        self.assertAlmostEqual(m.contrast((0, 0, 0, 1.0), WHITE), 21.0, places=2)

    def test_large_text_threshold(self):
        self.assertEqual(m.text_threshold(16, 400), 4.5)
        self.assertEqual(m.text_threshold(24, 400), 3.0)
        self.assertEqual(m.text_threshold(18.66, 700), 3.0)
        self.assertEqual(m.text_threshold(18.66, 600), 4.5)

    def test_blend(self):
        self.assertEqual(m.blend((0, 0, 0, 0.5), WHITE), (127.5, 127.5, 127.5, 1.0))


class Cvd(unittest.TestCase):
    def test_white_stays_white_and_lab(self):
        w = m.deutan((255, 255, 255))
        for c in w:
            self.assertAlmostEqual(c, 255, delta=0.5)
        L, a, b = m.lab((255, 255, 255))
        self.assertAlmostEqual(L, 100, places=1)

    def test_red_green_collapse_under_deutan(self):
        self.assertGreater(m.delta_e76((200, 60, 60), (60, 160, 60)), 15)
        de = m.delta_e76(m.deutan((200, 60, 60)), m.deutan((60, 160, 60)))
        self.assertLess(de, m.delta_e76((200, 60, 60), (60, 160, 60)))

    def test_pairs(self):
        p = m.cvd_pairs({"s1": (0, 0, 0), "s2": (255, 255, 255), "s3": (0, 0, 0)})
        self.assertEqual([(a, b) for a, b, _ in p], [("s1", "s2"), ("s1", "s3"), ("s2", "s3")])
        self.assertEqual(p[1][2], 0)


class Geometry(unittest.TestCase):
    def test_gap_and_overlap(self):
        self.assertEqual(m.gap((0, 0, 10, 10), (70, 0, 80, 10)), 60)
        self.assertEqual(m.gap((0, 0, 10, 10), (5, 5, 20, 20)), 0)
        self.assertEqual(m.overlap_area((0, 0, 10, 10), (5, 5, 20, 20)), 25)

    def test_points_and_view(self):
        self.assertEqual(m.points_inside([(1, 1), (50, 50), (5, 9)], (0, 0, 10, 10)), 2)
        self.assertTrue(m.inside_view((0, 0, 1280, 800), 1280, 800))
        self.assertFalse(m.inside_view((0, 700, 100, 900), 1280, 800))
        self.assertTrue(m.escapes((0, 0, 400, 10), 390))
        self.assertFalse(m.escapes((16, 0, 374, 10), 390))


class Notes(unittest.TestCase):
    VIEW = [1280, 800]

    def step(self, **kw):
        base = {"step": 1, "active": (100, 100, 200, 140), "notes": [(220, 100, 380, 140)], "boxes": [], "points": []}
        base.update(kw)
        return base

    def test_near_and_visible(self):
        r = m.note_steps([self.step()], self.VIEW)[0]
        self.assertTrue(r["near"] and r["visible"])

    def test_far_note_fails(self):
        r = m.note_steps([self.step(notes=[(260, 100, 420, 140)])], self.VIEW)[0]
        self.assertFalse(r["near"])
        self.assertEqual(r["distance"], 60)

    def test_missing_note_and_active(self):
        self.assertFalse(m.note_steps([self.step(notes=[])], self.VIEW)[0]["near"])
        self.assertFalse(m.note_steps([self.step(active=None)], self.VIEW)[0]["visible"])

    def test_two_active_nodes_fail(self):
        r = m.note_steps([self.step(active_count=2)], self.VIEW)[0]
        self.assertEqual((r["near"], r["why"]), (False, "현재 노드가 둘 이상"))

    def test_overlap_and_edge_points(self):
        r = m.note_steps([self.step(boxes=[(300, 120, 340, 160)])], self.VIEW)[0]
        self.assertFalse(r["near"])
        r = m.note_steps([self.step(points=[(300, 110)])], self.VIEW)[0]
        self.assertFalse(r["near"])
        self.assertEqual(r["edge_points"], 1)

    def test_offscreen_active(self):
        r = m.note_steps([self.step(active=(100, 900, 200, 940), notes=[(220, 900, 380, 940)])], self.VIEW)[0]
        self.assertTrue(r["near"])
        self.assertFalse(r["visible"])


class PageNumber(unittest.TestCase):
    def test_count(self):
        self.assertEqual(m.page_number_count(["2 / 3", "2 / 3", "1/28", "2/3"], 3), 3)
        self.assertEqual(m.page_number_count(["1/28"], 3), 0)


class Facts(unittest.TestCase):
    def test_demo_svg_pages(self):
        html = ('<nav class="pager"></nav><section class="page" id="p1"><svg></svg></section>'
                '<section class="page" id="p2"></section>'
                "<script>/* BEGIN report-charts x */RC.demo(a)/* END report-charts */</script>"
                "<script>RC.demo(document.getElementById('d'), [])</script>")
        f = m.source_facts(html)
        self.assertEqual(f, {"demo_calls": 1, "has_svg": True, "pages": ["p1", "p2"], "paged": True})

    def test_engine_block_only(self):
        html = '<script>/* BEGIN report-charts x */RC.demo(a);"<svg>"/* END report-charts */</script><p>글</p>'
        self.assertEqual(m.source_facts(html), {"demo_calls": 0, "has_svg": False, "pages": [], "paged": False})

    def test_mermaid_or_chart_counts_as_svg(self):
        self.assertTrue(m.source_facts('<pre class="mermaid">graph TD;A-->B</pre>')["has_svg"])
        self.assertTrue(m.source_facts("<script>RC.chart(box, {})</script>")["has_svg"])


if __name__ == "__main__":
    unittest.main()
