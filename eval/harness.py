"""문서 열기: 로컬 서버, 헤드리스 Chromium 세션, 측정 시작 조건, 환경 실패."""
import functools
import http.server
import threading
import time
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import TimeoutError as PWTimeout
from playwright.sync_api import sync_playwright

PROBE = (Path(__file__).resolve().parent / "probe.js").read_text(encoding="utf-8")
TIMEOUT = 15.0
VIEW = {1280: {"width": 1280, "height": 800}, 390: {"width": 390, "height": 844}}
WATCHED = {"document", "script", "stylesheet", "font", "fetch", "xhr", "image"}
BASE_READY = """() => document.fonts.status === 'loaded'
  && [...document.querySelectorAll('pre.mermaid')].every(p => p.querySelector('svg') || p.classList.contains('viz-fail'))"""
RENDER_FAIL = """() => [...document.querySelectorAll('.viz-fail')].map(e => (e.id || e.tagName.toLowerCase()) + ': ' + e.textContent.trim().slice(0, 40))"""
DEMO_READY = """n => document.querySelectorAll('figure[data-rc-ready="1"]').length >= n
  || !!document.querySelector('.demo-static')"""
DEMO_STATE = """() => ({ready: document.querySelectorAll('figure[data-rc-ready="1"]').length,
  fallback: document.querySelectorAll('.demo-static').length})"""


class EnvFail(Exception):
    """측정 시작 조건이 갖춰지지 않았다(외부 요청 실패, 15초 초과)."""


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


class Server:
    """폴더 하나를 127.0.0.1의 빈 포트로 띄운다. with 블록을 나가면 반드시 끈다."""

    def __init__(self, folder):
        handler = functools.partial(_Quiet, directory=str(folder))
        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.port = self.httpd.server_address[1]

    def __enter__(self):
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()

    def url(self, name, mode=None, page=None):
        q = f"?rc-mode={mode}" if mode else ""
        h = f"#{page}" if page else ""
        return f"http://127.0.0.1:{self.port}/{quote(name)}{q}{h}"


def _ignored(url):
    return url.endswith("favicon.ico")


def open_doc(context, url, demo_calls, page_id=None, notes=None):
    """새 탭으로 문서를 열고 측정 시작 조건을 기다린다. (page, demo_ok)를 돌려준다.
    글꼴·도식·네트워크가 15초 안에 준비되지 않거나 다른 출처(CDN) 요청이 실패하면 EnvFail.
    같은 출처(로컬 서버)의 요청 실패와 렌더 실패(.viz-fail)는 notes['load_errors']·notes['render_fail']에 모은다.
    page_id를 주면 그 페이지가 보이는지 확인하고, 보이지 않으면 EnvFail.
    RC.demo 호출이 있는데 data-rc-ready가 오지 않거나 정적 목록으로 물러나면 demo_ok가 False다."""
    page = context.new_page()
    origin = url.split("/", 3)[:3]
    local = "/".join(origin)
    external, same = [], []

    def failed(u, text):
        if _ignored(u):
            return
        (same if u.startswith(local) else external).append(text)

    page.on("requestfailed", lambda r: failed(r.url, r.url) if r.resource_type in WATCHED else None)
    page.on("response", lambda r: failed(r.url, f"{r.status} {r.url}")
            if r.status >= 400 and r.request.resource_type in WATCHED else None)
    deadline = time.monotonic() + TIMEOUT

    def left():
        return max(1.0, (deadline - time.monotonic()) * 1000)

    try:
        page.goto(url, wait_until="networkidle", timeout=TIMEOUT * 1000)
        if external:
            raise EnvFail("외부 요청 실패: " + ", ".join(external[:3]))
        page.wait_for_function(BASE_READY, timeout=left())
    except PWTimeout:
        page.close()
        raise EnvFail("15초 안에 글꼴·도식·네트워크가 준비되지 않았다") from None
    except EnvFail:
        page.close()
        raise
    page.add_script_tag(content=PROBE)
    if page_id and not page.evaluate("id => __c0.shown(id)", page_id):
        page.close()
        raise EnvFail(f"주소 끝 #{page_id}로 열었는데 그 페이지가 보이지 않는다")
    if notes is not None:
        notes.setdefault("load_errors", set()).update(same)
        notes.setdefault("render_fail", set()).update(page.evaluate(RENDER_FAIL))
    demo_ok = True
    if demo_calls:
        try:
            page.wait_for_function(DEMO_READY, arg=demo_calls, timeout=left())
        except PWTimeout:
            pass
        st = page.evaluate(DEMO_STATE)
        demo_ok = st["ready"] >= demo_calls and not st["fallback"]
    return page, demo_ok


class Session:
    """브라우저 하나와 (폭, 테마)별 컨텍스트, 문서 폴더를 띄운 서버. with 블록을 나가면 모두 닫는다."""

    def __init__(self, folder):
        self.server = Server(folder)
        self.notes = {"load_errors": set(), "render_fail": set()}

    def __enter__(self):
        self.server.__enter__()
        self.pw = self.browser = None
        try:
            self.pw = sync_playwright().start()
            self.browser = self.pw.chromium.launch()
        except Exception:
            self.__exit__(None, None, None)
            raise
        self.contexts = {}
        return self

    def __exit__(self, *exc):
        try:
            if self.browser:
                self.browser.close()
        finally:
            try:
                if self.pw:
                    self.pw.stop()
            finally:
                self.server.__exit__(*exc)

    def context(self, width, theme):
        key = (width, theme)
        if key not in self.contexts:
            self.contexts[key] = self.browser.new_context(viewport=VIEW[width], color_scheme=theme)
        return self.contexts[key]

    def open(self, name, demo_calls, width=1280, theme="light", mode=None, page=None, verify=True):
        """verify가 True이고 page를 주면 열린 문서에서 그 페이지가 보이는지 확인한다(hash-nav만 False)."""
        return open_doc(self.context(width, theme), self.server.url(name, mode, page), demo_calls,
                        page if verify else None, self.notes)
