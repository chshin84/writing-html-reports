"""여러 시험 파일이 함께 쓰는 도우미. L1 소유."""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PINNED = {"echarts": "6.1.0", "mermaid": "11.17.2", "gsap": "3.15.0"}


def cdn(lib, ver=None):
    return f'<script src="https://cdn.jsdelivr.net/npm/{lib}@{ver or PINNED[lib]}/dist/{lib}.min.js"></script>'


def page(style="", head="", body="", script=""):
    return ('<!doctype html><html lang="ko"><head><title>시험 문서</title>'
            f"<style>{style}</style>{head}</head><body><main class=\"doc\">{body}</main>"
            f"<script>{script}</script></body></html>")


def has(fails, name):
    return any(f.startswith(name) for f in fails)


ENV = dict(os.environ, PYTHONIOENCODING="utf-8")


def run_check(*paths):
    return subprocess.run([sys.executable, "-B", str(ROOT / "check.py"), *map(str, paths)],
                          capture_output=True, text=True, encoding="utf-8", env=ENV)



def toc(*classes):
    links = " · ".join(f'<a href="#p{i}" class="{c}">{i}. 절</a>' for i, c in enumerate(classes, 1))
    return page(body=f'<p class="toc">{links}</p>')


def paged(gist, marks, titles=("요약", "구조 A", "구조 B", "구조 C")):
    toc = " · ".join(f'<a href="#p{i}" class="{marks.get(i, "")}">{i}. {t}</a>' for i, t in enumerate(titles, 1))
    secs = [f'<section class="page" id="p1"><h2>{titles[0]}</h2><div class="gist"><ul>{gist}</ul></div></section>']
    secs += [f'<section class="page" id="p{i}"><h2>{t}</h2><table><tr><td>가</td></tr></table></section>'
             for i, t in enumerate(titles[1:], 2)]
    return page(body=f'<p class="toc">{toc}</p>' + "".join(secs))


def anim_page(sections, typ="구조"):
    """sections: [(section 클래스, 페이지 id, figure id 목록)]"""
    body = "".join(
        f'<section class="{c}" id="{p}"><h2>절 {p}</h2>'
        + "".join(f'<figure id="{f}" data-anim="{typ}"><svg></svg></figure>' for f in figs)
        + "</section>" for c, p, figs in sections)
    script = "".join(f"RC.demo(document.getElementById('{f}'),[]);" for _, _, figs in sections for f in figs)
    return page(body=body, script=script)

