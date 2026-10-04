/* C0 측정기의 화면 수집 함수. eval/harness.py가 측정 시작 조건이 갖춰진 뒤 문서에 넣는다.
   원시값만 모으고, 통과·실패 판정은 eval/measure.py·motion.py·layout.py가 한다. */
(function () {
  var C = window.__c0 = {};
  var SKIP = /^(SCRIPT|STYLE|TITLE|NOSCRIPT)$/i;
  var SHAPE = /^(rect|path|polygon|circle|ellipse)$/i;
  var GEOM = 'text, rect, polygon, circle, ellipse, path, line, polyline, foreignObject';
  function cs(e) { return getComputedStyle(e); }
  function opac(e) { var o = 1; for (var n = e; n; n = n.parentElement) o *= +cs(n).opacity; return o; }
  function clipped(e) { for (var n = e; n; n = n.parentElement) { var c = cs(n).clipPath; if (c && c !== 'none') return true; } return false; }
  function rendered(e) {
    return e.checkVisibility ? e.checkVisibility({ visibilityProperty: true }) : e.getClientRects().length > 0;
  }
  function alpha(c) {
    var m = /rgba?\(([^)]+)\)/.exec(c || '');
    if (!m) return c === 'transparent' || c === 'none' ? 0 : 1;
    var p = m[1].split(/[\s,\/]+/).filter(Boolean);
    return p.length > 3 ? parseFloat(p[3]) : 1;
  }
  function own(e) {
    var s = '';
    for (var i = 0; i < e.childNodes.length; i++) if (e.childNodes[i].nodeType === 3) s += e.childNodes[i].nodeValue;
    return s.replace(/\s+/g, ' ').trim();
  }
  function box(e) { var r = e.getBoundingClientRect(); return [r.left, r.top, r.right, r.bottom]; }
  function area(e) { var r = e.getBoundingClientRect(); return r.width * r.height; }
  function ink(e) { var c = cs(e); return e instanceof SVGElement ? c.fill : c.color; }
  function scale(e) { // 화면 변환 배율: SVG 안이면 화면 변환 행렬, 밖이면 경계 상자 대비 비율
    var s = e instanceof SVGElement ? e : e.closest('foreignObject');
    if (s && s.getScreenCTM) { var m = s.getScreenCTM(); if (m) return Math.sqrt(Math.abs(m.a * m.d - m.b * m.c)); }
    var w = e.offsetWidth;
    return w ? e.getBoundingClientRect().width / w : 1;
  }
  function wait(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  // 보이는 요소: 그려지고, 조상 불투명도 곱이 0.05 초과, 면적 1px² 이상, clip-path 없음, 글자면 글자색 알파가 0이 아님
  C.visible = function (e) {
    return rendered(e) && opac(e) > 0.05 && area(e) >= 1 && !clipped(e) && (!own(e) || alpha(ink(e)) > 0);
  };
  C.own = own;
  C.box = box;
  C.textEls = function (root) {
    return [].filter.call(root.querySelectorAll('*'), function (e) {
      return !SKIP.test(e.tagName) && !e.closest('defs') && own(e);
    });
  };
  C.fonts = function (root, inSvg) { // inSvg: true면 SVG 안 글자(그려지는 모든 글자), false면 SVG 밖의 보이는 글자
    return C.textEls(root).filter(function (e) {
      return !!e.closest('svg') === inSvg && (inSvg ? rendered(e) : C.visible(e));
    }).map(function (e) { return { px: +(parseFloat(cs(e).fontSize) * scale(e)).toFixed(2), text: own(e).slice(0, 24) }; });
  };
  function scrollBox(e) { // overflow-x가 auto·scroll인 조상만 스크롤 상자로 본다
    for (var n = e.parentElement; n && n !== document.body && n !== document.documentElement; n = n.parentElement)
      if (/^(auto|scroll)$/.test(cs(n).overflowX)) return n;
    return null;
  }
  C.layout = function () {
    var figs = [];
    [].forEach.call(document.querySelectorAll('figure, figure svg, pre.mermaid svg'), function (e) {
      if (!rendered(e) || (e.tagName.toLowerCase() === 'svg' && e.parentElement.closest('svg'))) return;
      var sb = scrollBox(e);
      figs.push({ name: e.id || e.tagName.toLowerCase(), box: box(sb || e), scroll: !!sb });
    });
    var cells = [].filter.call(document.querySelectorAll('td, th'), C.visible).map(function (e) {
      return { w: +e.getBoundingClientRect().width.toFixed(1), text: e.textContent.trim().slice(0, 16) };
    });
    var rootClip = [document.documentElement, document.body].some(function (e) { return /^(hidden|clip)$/.test(cs(e).overflowX); });
    return { width: document.documentElement.clientWidth, scrollWidth: document.documentElement.scrollWidth, rootClip: rootClip,
      svgFonts: C.fonts(document.body, true), htmlFonts: C.fonts(document.body, false), figures: figs, cells: cells };
  };
  C.demos = function () {
    return [].map.call(document.querySelectorAll('figure[data-rc-ready="1"]'), function (f) {
      var p = f.closest('section.page');
      return { id: f.id, page: p ? p.id : null, mode: f.dataset.rcMode || 'auto' };
    });
  };
  C.ends = function (tl) { var out = []; for (var i = 0; ('e' + i) in tl.labels; i++) out.push(tl.labels['e' + i]); return out; };
  C.eachEnd = function (fig, fn) { // 타임라인을 단계 끝으로 직접 옮기며 fn을 부른다(화면 상태만 보는 측정에 쓴다)
    var tl = fig._rcTl;
    return C.ends(tl).map(function (e, i) { tl.seek('e' + i, false); return fn(i); });
  };
  function noteFonts(f) { // SVG 밖 HTML 설명 상자의 글자
    return [].concat.apply([], [].map.call(f.querySelectorAll('.rc-note'), function (n) {
      return n.closest('svg') || !C.visible(n) ? [] : C.fonts(n, false);
    }));
  }
  C.svgFontSteps = function (id) {
    var f = document.getElementById(id);
    return [].concat.apply([], C.eachEnd(f, function () { return C.fonts(f, true).concat(noteFonts(f)); }));
  };
  function bgOf(e) { // 조상으로 올라가며 처음 만나는 불투명 바탕색. 반투명이나 그림 바탕이면 null
    for (var n = e; n; n = n.parentElement) {
      var s = cs(n);
      if (s.backgroundImage && s.backgroundImage !== 'none') return null;
      var a = alpha(s.backgroundColor);
      if (a >= 0.999) return s.backgroundColor;
      if (a > 0.001) return null;
    }
    return 'rgb(255, 255, 255)';
  }
  function under(e, x, y) { // 글자 중심점 아래에 그려진 도형의 채움색. 없으면 undefined, 반투명이면 null
    if (x < 0 || y < 0 || x >= innerWidth || y >= innerHeight) return undefined;
    var st = document.elementsFromPoint(x, y), i = st.indexOf(e);
    for (var k = i + 1; k < st.length; k++) {
      var s = st[k];
      if (s.contains(e)) { if (s.tagName.toLowerCase() === 'svg') break; continue; }
      if (!(s instanceof SVGElement)) break;
      if (!SHAPE.test(s.tagName)) continue;
      var c = cs(s);
      if (c.fill === 'none' || alpha(c.fill) === 0) continue;
      return opac(s) * parseFloat(c.fillOpacity) >= 0.999 && alpha(c.fill) >= 0.999 ? c.fill : null;
    }
    return undefined;
  }
  function weight(c) { var w = parseInt(c.fontWeight, 10); return isNaN(w) ? (c.fontWeight === 'bold' ? 700 : 400) : w; }
  function textPair(e) { // op는 요소 불투명도다. 판정할 때 글자색 알파에 곱해 바탕과 합성한다
    var c = cs(e), inSvg = !!e.closest('svg'), r = e.getBoundingClientRect();
    var rec = { text: own(e).slice(0, 24), px: +(parseFloat(c.fontSize) * scale(e)).toFixed(2), weight: weight(c),
      svg: inSvg, fg: ink(e), op: +opac(e).toFixed(3), bg: null, why: null };
    if (inSvg) {
      var u = under(e, (r.left + r.right) / 2, (r.top + r.bottom) / 2);
      if (u === null) { rec.why = '반투명 도형 바탕'; return rec; }
      if (u) { rec.bg = u; return rec; }
    }
    rec.bg = bgOf(inSvg ? e.closest('svg') : e);
    if (!rec.bg) rec.why = '반투명이나 그림 바탕';
    return rec;
  }
  C.graphics = function (root) {
    var out = [];
    [].forEach.call(root.querySelectorAll('.fill'), function (e) {
      if (C.visible(e)) out.push({ kind: 'fill', name: e.parentElement.textContent.trim().slice(0, 16),
        fg: cs(e).backgroundColor, bg: bgOf(e.parentElement) });
    });
    if (window.echarts) [].forEach.call(root.querySelectorAll('[_echarts_instance_]'), function (b) {
      var inst = echarts.getInstanceByDom(b);
      if (!inst || !C.visible(b)) return;
      var bg = bgOf(b);
      try { // getModel은 ECharts 내부 API다. 읽지 못하면 측정 불가로 남긴다
        inst.getModel().getSeries().forEach(function (s) {
          var d = s.getData(), line = s.subType === 'line';
          var pick = function (st) { return st ? (line ? st.stroke : st.fill) : null; };
          if (s.subType === 'pie') {
            for (var i = 0; i < d.count(); i++) out.push({ kind: 'series', name: s.name + ':' + d.getName(i), fg: pick(d.getItemVisual(i, 'style')), bg: bg });
          } else out.push({ kind: 'series', name: String(s.name), fg: pick(d.getVisual('style')), bg: bg });
        });
      } catch (x) { out.push({ kind: 'series', name: 'echarts', fg: null, bg: bg, why: 'ECharts 계열 색을 읽지 못했다' }); }
    });
    [].forEach.call(root.querySelectorAll('svg g.node, svg [data-rc-active]'), function (n) {
      var shape = n.tagName.toLowerCase() === 'g' ? n.querySelector('rect, polygon, path, circle, ellipse') : n;
      if (!shape || !C.visible(shape)) return;
      var c = cs(shape);
      if (c.stroke === 'none' || alpha(c.stroke) === 0) return;
      out.push({ kind: 'node', name: (n.id || '').slice(-24), fg: c.stroke, bg: bgOf(shape.closest('svg')) });
    });
    return out;
  };
  C.contrast = function () { // 바탕 도형을 찾는 동안 pointer-events:none 요소도 적중 시험에 들게 한다
    var pe = document.createElement('style');
    pe.textContent = '*{pointer-events:auto !important}';
    document.head.appendChild(pe);
    var H = innerHeight, els = C.textEls(document.body).filter(C.visible), done = new Set(), text = [];
    for (var y = 0; y < document.documentElement.scrollHeight; y += H) {
      scrollTo(0, y);
      els.forEach(function (e) {
        if (done.has(e)) return;
        var r = e.getBoundingClientRect(), cy = (r.top + r.bottom) / 2;
        if (r.width === 0 || cy < 0 || cy >= H) return;
        done.add(e);
        text.push(textPair(e));
      });
    }
    els.forEach(function (e) { if (!done.has(e)) text.push(textPair(e)); });
    scrollTo(0, 0);
    pe.remove();
    return { text: text, graphic: C.graphics(document) };
  };
  C.graphicSteps = function (id) {
    var f = document.getElementById(id);
    return [].concat.apply([], C.eachEnd(f, function () { return C.graphics(f); }));
  };
  C.pageNumbers = function () {
    return C.textEls(document.body).filter(function (e) { return C.visible(e) && !e.closest('figure, table'); })
      .map(own).filter(function (t) { return /^\d+\s*\/\s*\d+$/.test(t); });
  };
  C.shown = function (id) { var e = document.getElementById(id); return !!e && rendered(e) && e.getBoundingClientRect().height > 0; };
  C.tokens = function (names) {
    var s = cs(document.documentElement), o = {};
    names.forEach(function (n) { o[n] = s.getPropertyValue('--' + n).trim(); });
    return o;
  };
  C.figText = function (fig) { // figure 안 보이는 글 요소 {키: 글}. 조작 줄과 단계 목록은 뺀다
    var m = {};
    C.textEls(fig).forEach(function (e) {
      if (e.closest('.demo-ctl, .demo-steps') || !C.visible(e)) return;
      var k = e.getAttribute('data-c0k');
      if (!k) { C.k = (C.k || 0) + 1; k = 'k' + C.k; e.setAttribute('data-c0k', k); }
      m[k] = own(e);
    });
    return m;
  };
  C.dwellSamples = function (id) { // '처음부터'를 누른 뒤 타임라인을 0부터 끝까지 0.05초 간격(단계 끝 라벨 포함)으로 옮기며 글을 기록한다
    var f = document.getElementById(id), tl = f._rcTl, b = f.querySelectorAll('.demo-ctl button');
    if (b[3]) b[3].click();
    var ends = C.ends(tl), D = tl.duration(), ts = [0];
    for (var t = 0.05; t < D + 1e-9; t += 0.05) ts.push(Math.round(t * 1000) / 1000);
    ts = ts.concat(ends).sort(function (a, c) { return a - c; })
      .filter(function (v, i, a) { return i === 0 || v - a[i - 1] > 1e-6; });
    var scale = typeof tl.timeScale === 'function' ? tl.timeScale() : 1;
    return { ends: ends, timeScale: scale, samples: ts.map(function (t) { tl.seek(t, false); return [t, C.figText(f)]; }) };
  };
  C.step1 = function (id, mode) { // 처음 연 상태의 시간과, 재생(자동)·다음(넘김)을 누른 뒤 e0에 닿기까지의 벽시계 시간
    var f = document.getElementById(id), tl = f._rcTl, b = f.querySelectorAll('.demo-ctl button'), t0 = tl.time(), e0 = tl.labels.e0;
    return new Promise(function (done) {
      var start = performance.now();
      (mode === 'step' ? b[2] : b[1]).click();
      (function poll() {
        var el = (performance.now() - start) / 1000, hit = tl.time() >= e0 - 1e-6;
        if (hit || el > 6) done({ initial: t0, e0: e0, reached: hit, seconds: +el.toFixed(3) });
        else requestAnimationFrame(poll);
      })();
    });
  };
  function settle(tl, start, cap) { // 타임라인 시간과 창 스크롤이 300ms 동안 멈출 때까지 기다린다. 마지막으로 바뀐 시각(초)을 돌려준다
    return new Promise(function (done) {
      var last = tl.time(), sy = scrollY, lc = start;
      (function poll() {
        var now = performance.now(), t = tl.time();
        if (t !== last || scrollY !== sy) { last = t; sy = scrollY; lc = now; }
        if (now - lc > 300 || now - start > cap) done((lc - start) / 1000); else requestAnimationFrame(poll);
      })();
    });
  }
  C.stepAnim = function (id) { // '다음'을 누를 때마다 연출 길이(벽시계)와 타임라인 변화량, 첫 단계 뒤 3초 동안 멈춰 있는지
    var f = document.getElementById(id), tl = f._rcTl, b = f.querySelectorAll('.demo-ctl button'), n = C.ends(tl).length, lens = [], deltas = [], held = null;
    function one(k) {
      if (k >= n || b[2].disabled) return Promise.resolve();
      var start = performance.now(), t0 = tl.time();
      b[2].click();
      return settle(tl, start, 8000).then(function (s) {
        lens.push(+s.toFixed(3));
        deltas.push(+(tl.time() - t0).toFixed(3));
        if (held !== null) return one(k + 1);
        var t = tl.time();
        return wait(3000).then(function () { held = Math.abs(tl.time() - t) < 1e-6; return one(k + 1); });
      });
    }
    return one(0).then(function () { return { lengths: lens, deltas: deltas, held: held }; });
  };
  C.toStep = function (id, i) { // 엔진 버튼으로 i번째 단계 끝까지 간다. i=0은 '처음부터' 뒤 필요하면 '다음'을 한 번 누른다
    var f = document.getElementById(id), tl = f._rcTl, b = f.querySelectorAll('.demo-ctl button'), e0 = tl.labels.e0;
    var start = performance.now();
    if (i === 0) {
      b[3].click();
      return settle(tl, start, 10000).then(function () {
        if (tl.time() >= e0 - 1e-6) return { time: tl.time() };
        var s2 = performance.now();
        b[2].click();
        return settle(tl, s2, 10000).then(function () { return { time: tl.time() }; });
      });
    }
    b[2].click();
    return settle(tl, start, 10000).then(function () { return { time: tl.time() }; });
  };
  function pointsOf(e) {
    var out = [];
    try {
      var L = e.getTotalLength(), m = e.getScreenCTM(), k = m ? Math.sqrt(Math.abs(m.a * m.d - m.b * m.c)) : 1, step = 2 / (k || 1);
      for (var s = 0; s <= L; s += step) { var p = e.getPointAtLength(s), q = new DOMPoint(p.x, p.y).matrixTransform(m); out.push([q.x, q.y]); }
    } catch (x) { /* 길이를 구할 수 없는 요소는 건너뛴다 */ }
    return out;
  }
  function stickman(e) { var g = e.closest('.rc-icon'); return !!g && !!g.querySelector('image'); }
  C.noteStep = function (f, i) { // 현재 노드(설명 상자·아이콘 밖의 보이는 data-rc-active), 보이는 설명 상자, 설명 상자 근처(4px)의 무대 요소 상자와 간선 점
    var acts = [].filter.call(f.querySelectorAll('[data-rc-active]'), function (e) { return !e.closest('.rc-note, .rc-icon') && C.visible(e); });
    var notes = [].filter.call(f.querySelectorAll('.rc-note'), C.visible).map(box);
    var a = acts.length === 1 ? box(acts[0]) : null, boxes = [], points = [];
    if (a && notes.length) {
      var z = notes.reduce(function (p, n) { return [Math.min(p[0], n[0]), Math.min(p[1], n[1]), Math.max(p[2], n[2]), Math.max(p[3], n[3])]; });
      var nearZ = function (x0, y0, x1, y1) { return x1 >= z[0] - 4 && x0 <= z[2] + 4 && y1 >= z[1] - 4 && y0 <= z[3] + 4; };
      [].forEach.call(f.querySelectorAll('svg'), function (svg) {
        [].forEach.call(svg.querySelectorAll(GEOM), function (e) {
          if (e.closest('.rc-note, defs, marker, clipPath, mask, pattern') || stickman(e) || !C.visible(e)) return;
          var c = cs(e), edge = /^(line|polyline)$/i.test(e.tagName) || (/^path$/i.test(e.tagName) && (c.fill === 'none' || alpha(c.fill) === 0));
          if (edge) pointsOf(e).forEach(function (p) { if (nearZ(p[0], p[1], p[0], p[1])) points.push(p); });
          else { var b = box(e); if (b[2] > b[0] && nearZ(b[0], b[1], b[2], b[3])) boxes.push(b); }
        });
      });
    }
    return { step: i + 1, active: a, active_count: acts.length, notes: notes, boxes: boxes, points: points };
  };
  C.noteSteps = function (id) { // figure 윗변을 창 윗변에 맞춰 한 번 스크롤한 뒤, 엔진 버튼으로 단계를 넘기며 단계 끝마다 측정한다
    var f = document.getElementById(id), n = C.ends(f._rcTl).length, out = [];
    scrollTo(0, f.getBoundingClientRect().top + scrollY);
    function one(i) {
      if (i >= n) return Promise.resolve();
      return C.toStep(id, i).then(function () { out.push(C.noteStep(f, i)); return one(i + 1); });
    }
    return one(0).then(function () { return { view: [innerWidth, innerHeight], steps: out }; });
  };
})();
