"""C0 문서 열기 시험(합성 HTML, 외부 네트워크 없음). 실행: python -B -m unittest discover -s tests"""
import socket
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
import harness  # noqa: E402

ENGINE = (ROOT / "report-charts.js").read_text(encoding="utf-8")


def write(folder, name, body, script=""):
    p = Path(folder, name)
    p.write_text(f'<!doctype html><html lang="ko"><head><meta charset="utf-8"></head><body>{body}'
                 f"<script>{script}</script></body></html>", encoding="utf-8")
    return p


class Open(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def test_korean_file_name_opens_and_probe_loaded(self):
        write(self.tmp.name, "시험 문서.html", "<p>글</p>")
        with harness.Session(self.tmp.name) as s:
            page, ok = s.open("시험 문서.html", 0)
            self.assertTrue(ok)
            self.assertEqual(page.evaluate("() => typeof window.__c0.layout"), "function")
            page.close()

    def test_blocked_cdn_is_env_fail(self):
        write(self.tmp.name, "a.html", '<script src="http://127.0.0.1:9/gsap.min.js"></script><p>글</p>')
        with harness.Session(self.tmp.name) as s:
            with self.assertRaises(harness.EnvFail):
                s.open("a.html", 0)

    def test_static_fallback_is_not_demo_ok(self):
        body = '<figure id="d"><svg viewBox="0 0 10 10"></svg><p class="src">자료</p></figure>'
        write(self.tmp.name, "b.html", body, ENGINE + "\nRC.demo(document.getElementById('d'), "
              "[{name: '가', text: '나', play: function () {}}]);")
        with harness.Session(self.tmp.name) as s:
            page, ok = s.open("b.html", 1)
            self.assertFalse(ok)
            page.close()

    def test_server_closed_after_exception(self):
        try:
            with harness.Server(self.tmp.name) as srv:
                port = srv.port
                raise RuntimeError("측정 중 예외")
        except RuntimeError:
            pass
        with self.assertRaises(OSError):
            socket.create_connection(("127.0.0.1", port), timeout=1).close()

    def test_same_origin_404_is_recorded_not_env_fail(self):
        write(self.tmp.name, "c.html", '<img src="없는그림.png"><p>글</p>')
        with harness.Session(self.tmp.name) as s:
            page, ok = s.open("c.html", 0)
            page.close()
            self.assertEqual(len(s.notes["load_errors"]), 1)

    def test_requested_page_must_be_shown(self):
        write(self.tmp.name, "d.html", '<section class="page" id="p1">일</section>'
              '<section class="page" id="p2" style="display:none">이</section>')
        with harness.Session(self.tmp.name) as s:
            with self.assertRaises(harness.EnvFail):
                s.open("d.html", 0, page="p2")
            page, _ = s.open("d.html", 0, page="p2", verify=False)
            page.close()

    def test_url_has_mode_and_page(self):
        with harness.Server(self.tmp.name) as srv:
            self.assertTrue(srv.url("가 나.html", "step", "p2").endswith("/%EA%B0%80%20%EB%82%98.html?rc-mode=step#p2"))


if __name__ == "__main__":
    unittest.main()
