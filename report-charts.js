/* report-charts for echarts@6.1.0 mermaid@11.17.2 gsap@3.15.0
   보고서 시각화 연결 코드. build.py가 문서의 BEGIN/END report-charts 사이에 채운다. 원본은 이 파일이고, 문서 안에서 고치지 않는다.
   함수: RC.chart(상자, 옵션), RC.color(토큰 이름), RC.ma(값 배열, n), RC.demo(figure, 단계 배열),
   RC.icon(무대 svg, 아이콘 이름, x, y), RC.note(무대 svg, 폭, 높이), RC.focus(무대 svg), RC.fx(애니메이션 효과 묶음), RC.check(figure id: 완료 전 판정 도구).
   규칙은 시각화.md '시각화' 절과 '애니메이션' 절에 있다. */
(function () {
  var root = document.documentElement;
  var FAIL = '시각화를 불러오지 못했습니다';
  var PRINT_W = 688; // A4 본문 폭(210mm - 좌우 여백 28mm)의 px 값
  var RC = window.RC = {};

  function tok(name) { return getComputedStyle(root).getPropertyValue('--' + name).trim(); }
  function fail(box) { box.textContent = FAIL; box.classList.add('viz-fail'); }
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  var SKIP_TXT = /^(SCRIPT|STYLE|TITLE|NOSCRIPT)$/;
  function ownText(e) {
    var s = '';
    for (var i = 0; i < e.childNodes.length; i++) if (e.childNodes[i].nodeType === 3) s += e.childNodes[i].nodeValue;
    return s.replace(/\s+/g, ' ').trim();
  }
  function seen(e, fig) { // C0 하네스의 보임 판정을 계산된 스타일로 옮긴 것이다. 숨은 페이지에서도 쓰도록 면적 조건은 뺀다
    var o = 1, c0 = getComputedStyle(e);
    if (c0.visibility === 'hidden' || c0.visibility === 'collapse') return false;
    for (var n = e; n && n !== fig.parentElement; n = n.parentElement) {
      var c = n === e ? c0 : getComputedStyle(n);
      if (c.display === 'none' || (c.clipPath && c.clipPath !== 'none')) return false;
      o *= +c.opacity;
    }
    if (o <= 0.05) return false;
    var col = c0[e instanceof SVGElement ? 'fill' : 'color'];
    return !/^(transparent|none)$|,\s*0\)$/.test(col);
  }
  function textPool(fig) { // 표본마다 다시 찾지 않도록 글을 가질 수 있는 요소를 단계마다 한 번 모은다. 조작 줄·단계 목록·자막·시나리오 줄은 뺀다
    return [].filter.call(fig.querySelectorAll('*'), function (e) {
      return !SKIP_TXT.test(e.tagName) && !e.closest('.demo-ctl, .demo-steps, .demo-cap, .demo-scen, defs');
    });
  }
  function texts(fig, pool) { // figure 안 보이는 글 요소와 그 글
    var m = new Map();
    pool.forEach(function (e) { var t = ownText(e); if (t && seen(e, fig)) m.set(e, t); });
    return m;
  }
  function sameTexts(a, b) {
    if (a.size !== b.size) return false;
    var ok = true;
    a.forEach(function (v, k) { if (b.get(k) !== v) ok = false; });
    return ok;
  }
  function sampleStep(tl, fig, from, to, before, pool) { // from~to를 0.05초 간격으로 옮기며 글이 마지막으로 바뀐 시각(done)과 새 글자 수(n)를 구한다
    var prev = before, done = from, ts = [];
    for (var t = from; t < to - 1e-9; t += 0.05) ts.push(t);
    ts.push(to);
    ts.forEach(function (t) { tl.seek(t, false); var cur = texts(fig, pool); if (!sameTexts(prev, cur)) done = t; prev = cur; });
    var n = 0;
    prev.forEach(function (v, e) { if (before.get(e) !== v) n += chars(v); });
    return { done: done, n: n };
  }

  RC.color = function (name) {
    var v = tok(name);
    if (!v) console.error('RC.color: 없는 토큰 이름 ' + name);
    return v;
  };

  RC.ma = function (values, n) {
    var out = [], sum = 0;
    for (var i = 0; i < values.length; i++) {
      sum += values[i];
      if (i >= n) sum -= values[i - n];
      out.push(i >= n - 1 ? Math.round(sum / n * 1e8) / 1e8 : null);
    }
    return out;
  };

  /* 차트 */
  var themed = false, charts = [];
  function registerTheme() {
    if (themed) return;
    themed = true;
    var ink = tok('ink'), ink3 = tok('ink-3'), hair = tok('hair'), rule = tok('rule');
    var axis = { axisLine: { lineStyle: { color: rule } }, axisTick: { lineStyle: { color: rule } },
      axisLabel: { color: ink3 }, splitLine: { show: false } };
    echarts.registerTheme('report', {
      color: [tok('s1'), tok('s2'), tok('s3'), tok('s4'), tok('accent-2')],
      backgroundColor: 'transparent',
      textStyle: { fontFamily: tok('sans'), color: ink },
      categoryAxis: axis, timeAxis: axis,
      valueAxis: { axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: ink3 },
        splitLine: { lineStyle: { color: hair } } },
      legend: { textStyle: { color: ink3 }, icon: 'rect', itemWidth: 12, itemHeight: 8 },
      tooltip: { backgroundColor: tok('paper'), borderColor: hair, borderWidth: 1, textStyle: { color: ink },
        extraCssText: 'box-shadow:none;border-radius:0' },
      line: { symbol: 'none', lineStyle: { width: 1.5 } },
      bar: { itemStyle: { borderRadius: 0 } },
      pie: { itemStyle: { borderColor: tok('paper'), borderWidth: 1 } },
      candlestick: { itemStyle: { color: tok('neg'), color0: tok('s1'), borderColor: tok('neg'), borderColor0: tok('s1') } }
    });
  }
  RC.chart = function (box, option) {
    if (!box) { console.error('RC.chart: 차트 상자가 없다'); return null; }
    if (typeof echarts === 'undefined') { fail(box); return null; }
    try {
      registerTheme();
      var w = box.clientWidth || document.querySelector('main.doc').clientWidth; // 숨은 페이지는 폭이 0이다
      var h = box.clientHeight || parseFloat(getComputedStyle(box).height) || 320;
      var chart = echarts.init(box, 'report', { renderer: 'svg', width: w, height: h });
      option.animation = false;
      if (!option.tooltip) {
        var pie = (option.series || []).some(function (s) { return s.type === 'pie'; });
        option.tooltip = { trigger: pie ? 'item' : 'axis' };
      }
      chart.setOption(option);
    } catch (e) { // 차트 하나의 오류가 뒤의 시각화를 막지 않게 한다
      console.error('RC.chart', e);
      if (chart) chart.dispose();
      fail(box);
      return null;
    }
    charts.push({ chart: chart, box: box, h: h });
    new ResizeObserver(function () {
      if (box.clientWidth > 0 && box.clientWidth !== chart.getWidth()) chart.resize({ width: box.clientWidth, height: h });
    }).observe(box);
    return chart;
  };
  addEventListener('beforeprint', function () {
    charts.forEach(function (it) { it.chart.resize({ width: PRINT_W, height: it.h }); });
  });
  addEventListener('afterprint', function () {
    charts.forEach(function (it) {
      if (it.box.clientWidth > 0) it.chart.resize({ width: it.box.clientWidth, height: it.h });
    });
  });

  /* 도식. mermaid는 스크립트가 실행되자마자(DOMContentLoaded 전에) startOnLoad를 꺼야 한다.
     그러지 않으면 mermaid.min.js 자신의 기본 자동 실행이 .mermaid 요소를 먼저 렌더링해
     pre.textContent를 SVG로 바꿔버리고, 이어지는 renderMermaid()가 그 SVG 텍스트를 다시
     mermaid에 넣어 파싱에 실패한다. */
  if (typeof mermaid !== 'undefined') {
    mermaid.initialize({
      startOnLoad: false, theme: 'base', securityLevel: 'strict', fontFamily: tok('sans'),
      flowchart: { curve: 'linear' },
      themeVariables: {
        fontFamily: tok('sans'), fontSize: '14px', background: tok('paper'), textColor: tok('ink'),
        primaryColor: tok('paper'), primaryTextColor: tok('ink'), primaryBorderColor: tok('ink'),
        secondaryColor: tok('tint'), tertiaryColor: tok('paper'), lineColor: tok('ink-2'),
        clusterBkg: tok('paper'), clusterBorder: tok('hair'), edgeLabelBackground: tok('paper'),
        actorBkg: tok('paper'), actorBorder: tok('ink'), actorTextColor: tok('ink'), actorLineColor: tok('hair'),
        signalColor: tok('ink'), signalTextColor: tok('ink'),
        noteBkgColor: tok('tint'), noteBorderColor: tok('hair'), noteTextColor: tok('ink')
      }
    });
  }
  function renderMermaid() {
    var pres = [].slice.call(document.querySelectorAll('pre.mermaid'));
    if (!pres.length) return null;
    if (typeof mermaid === 'undefined') { pres.forEach(fail); return null; }
    return pres.reduce(function (p, pre, i) {
      var src = pre.textContent;
      return p.then(function () { return mermaid.render('rc-mermaid-' + i, src); })
        .then(function (r) { pre.innerHTML = r.svg; pre.classList.add('rendered'); }, function () { fail(pre); });
    }, Promise.resolve());
  }
  RC.ready = new Promise(function (res) {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', res); else res();
  }).then(function () { return document.fonts ? document.fonts.ready : null; }).then(renderMermaid);

  /* 애니메이션 아이콘: 스틱맨(Open Peeps 상반신 80×80, report-peeps.js)과 1px 선으로 그린 상태 표시. (x, y)는 아이콘 중심이고, 처음에는 투명하다 */
  var SVGNS = 'http://www.w3.org/2000/svg';
  function sv(tag, attrs, parent) {
    var e = document.createElementNS(SVGNS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    if (parent) parent.appendChild(e);
    return e;
  }
  function glyph(g, x, y, ch, size) {
    var t = sv('text', { x: x, y: y + size * 0.35, 'text-anchor': 'middle', 'font-size': size, 'font-weight': 600, stroke: 'none' }, g);
    t.textContent = ch;
  }
  var ICONS = {
    question: function (g, x, y) { glyph(g, x, y, '?', 20); },
    check: function (g, x, y) {
      sv('circle', { cx: x, cy: y, r: 11 }, g);
      sv('path', { d: 'M' + (x - 5) + ' ' + y + 'L' + (x - 1) + ' ' + (y + 4) + 'L' + (x + 6) + ' ' + (y - 4) }, g);
    },
    cross: function (g, x, y) {
      sv('circle', { cx: x, cy: y, r: 11 }, g);
      sv('path', { d: 'M' + (x - 4) + ' ' + (y - 4) + 'L' + (x + 4) + ' ' + (y + 4) + 'M' + (x + 4) + ' ' + (y - 4) + 'L' + (x - 4) + ' ' + (y + 4) }, g);
    },
    doc: function (g, x, y) {
      sv('rect', { x: x - 8, y: y - 11, width: 16, height: 22 }, g);
      sv('path', { d: 'M' + (x - 4) + ' ' + (y - 5) + 'H' + (x + 4) + 'M' + (x - 4) + ' ' + y + 'H' + (x + 4) + 'M' + (x - 4) + ' ' + (y + 5) + 'H' + (x + 1) }, g);
    },
    coin: function (g, x, y) { sv('circle', { cx: x, cy: y, r: 10 }, g); glyph(g, x, y, '₩', 11); }
  };
  var ICON_COLOR = { question: 'accent', check: 'accent', cross: 'neg' };
  RC.icon = function (svg, name, x, y) {
    var P = window.RC_PEEPS;
    if (svg && P && P.figures[name]) { // 스틱맨: 80×80 image(SVG data URI)로 넣어 경계와 변형 원점이 그림 칸과 같게 한다. 선은 ink, 바탕은 paper 토큰 값을 만들 때 넣는다
      var body = P.figures[name].replace(/class="pk"/g, 'fill="' + tok('ink') + '"').replace(/class="pw"/g, 'fill="' + tok('paper') + '"');
      var src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="' + P.viewBox + '">' + body + '</svg>');
      var pg = sv('g', { 'class': 'rc-icon', opacity: 0 }, svg);
      sv('image', { x: x - 40, y: y - 40, width: 80, height: 80, href: src }, pg);
      return pg;
    }
    if (!svg || !ICONS[name]) { console.error('RC.icon: 무대가 없거나 없는 아이콘 이름 ' + name); return null; }
    var c = tok(ICON_COLOR[name] || 'ink');
    var g = sv('g', { 'class': 'rc-icon', fill: 'none', stroke: c, 'stroke-width': 1, opacity: 0 }, svg);
    ICONS[name](g, x, y);
    [].forEach.call(g.querySelectorAll('text'), function (t) { t.style.fill = c; }); // svg text의 기본 글자색 규칙보다 앞서게 한다
    return g;
  };

  /* 애니메이션 설명 상자: 발췌 문장을 연출 중인 도형 옆에 두어 시선이 무대 안에 머물게 한다.
     돌려주는 값 { g: 상자, t: 문장 칸, n: 숫자 칸 }. 위치는 RC.fx.say가 단계마다 옮긴다 */
  RC.note = function (svg, w, h) {
    if (!svg) { console.error('RC.note: 무대가 없다'); return null; }
    var g = sv('g', { 'class': 'rc-note', opacity: 0 }, svg);
    sv('rect', { x: 0, y: 0, width: w, height: h, fill: tok('paper'), stroke: tok('hair') }, g);
    var fo = sv('foreignObject', { x: 0, y: 0, width: w, height: h }, g);
    var div = document.createElement('div');
    div.style.cssText = 'padding:6px 8px;font:12.5px/1.45 var(--sans);color:var(--ink);word-break:keep-all';
    var t = document.createElement('span'), n = document.createElement('b');
    n.style.cssText = 'color:var(--accent);font-weight:600';
    div.appendChild(t); div.appendChild(document.createTextNode(' ')); div.appendChild(n);
    fo.appendChild(div);
    return { g: g, t: t, n: n };
  };

  function geom(e) { // 숨은 페이지에서는 getBBox가 0이므로 도형 속성에서 위치를 읽는다
    var a = function (k) { return parseFloat(e.getAttribute(k)) || 0; };
    if (e.tagName === 'rect') return { x: a('x'), y: a('y'), width: a('width'), height: a('height') };
    if (e.tagName === 'polygon' || e.tagName === 'polyline') {
      var v = e.getAttribute('points').trim().split(/[\s,]+/).map(Number), xs = [], ys = [];
      for (var i = 0; i + 1 < v.length; i += 2) { xs.push(v[i]); ys.push(v[i + 1]); }
      var x0 = Math.min.apply(null, xs), y0 = Math.min.apply(null, ys);
      return { x: x0, y: y0, width: Math.max.apply(null, xs) - x0, height: Math.max.apply(null, ys) - y0 };
    }
    if (e.tagName === 'circle') return { x: a('cx') - a('r'), y: a('cy') - a('r'), width: 2 * a('r'), height: 2 * a('r') };
    return e.getBBox();
  }
  /* 애니메이션 초점 틀: 현재 도형의 네 모서리에 붙는 괄호. RC.fx.spot이 도형에서 도형으로 미끄러지듯 옮긴다 */
  RC.focus = function (svg) {
    if (!svg) { console.error('RC.focus: 무대가 없다'); return null; }
    var A = 9, g = sv('g', { 'class': 'rc-focus', fill: 'none', stroke: tok('accent'), 'stroke-width': 1.5, opacity: 0 }, svg);
    var d = ['M0 ' + A + 'V0H' + A, 'M-' + A + ' 0H0V' + A, 'M0 -' + A + 'V0H-' + A, 'M' + A + ' 0H0V-' + A]; // 왼위, 오른위, 오른아래, 왼아래
    return { g: g, c: d.map(function (p) { return sv('path', { d: p }, g); }), cur: null };
  };

  /* 애니메이션 효과: play(tl, $) 안에서 RC.fx.이름(tl, …)으로 부른다. 단계 하나의 연출은 2초 안팎으로 맞춘다.
     at은 GSAP 위치 인자(생략하면 앞 효과 뒤, '<'이면 앞 효과와 함께)다.
     글 규칙(RC.demo가 강제한다): 글이 한 번 나타날 때(타이핑과 카운트업이 이어진 한 덩어리)마다 1초 안에 끝나고,
     자동 재생에서는 단계의 글이 다 나온 뒤 1초 + 글자 수 ÷ 8초 이상 머문다. 글자 수에는 자막과 설명 상자와 숫자 칸이 모두 든다.
     설명 상자 하나의 글은 30자 이하다. 글자 수는 공백을 빼고 세며 숫자 하나는 1자다 */
  var TEXT_MAX = 1, CHAR_MAX = 30;
  function chars(s) { return String(s).replace(/\d[\d,.]*/g, '#').replace(/\s/g, '').length; }
  function holdFor(n) { return 1 + n / 8; } // 글이 다 나온 뒤 머무는 시간의 하한(초). 상한은 이 값 + 3초다
  var HOLD_PAD = 0.3; // 측정 간격(0.05초)과 반올림을 흡수하는 여유
  var DEFAULT_MODE = 'step'; // 주소에 ?rc-mode가 없을 때의 재생 방식. L1이 실측 뒤 바꿀 수 있다
  var STEP_MIN = 0.43, STEP_MAX = 2.43; // 단계 넘김의 단계 연출 길이. 사이 띄움 0.02초를 더하면 0.45~2.45초다
  function playMode() { var m = /[?&]rc-mode=(auto|step)(?:&|$)/.exec(location.search); return m ? m[1] : DEFAULT_MODE; }
  var demoStep = null; // RC.demo가 단계를 만드는 동안 $로 마지막에 조회한 요소(last)와 mark·spot이 받은 요소(mark)를 적는다
  var stepLog = null; // RC.demo가 단계마다 글 등장 구간과 글자 수를 모은다
  RC.issues = []; // 글 규칙 위반. 겹침 판정 도구가 함께 읽는다
  function issue(msg) { RC.issues.push(msg); console.error('RC.demo: ' + msg); }
  function textRules(L, s, fig) { // 글 등장 1초 규칙과 설명 상자 30자 규칙(작성자 글만 센다)
    if (!L.beats.length) return;
    L.beats.sort(function (a, b) { return a[0] - b[0]; });
    var merged = [L.beats[0].slice()];
    L.beats.slice(1).forEach(function (b) { // 이어지거나 겹치는 글 등장은 한 덩어리로 본다
      var m = merged[merged.length - 1];
      if (b[0] <= m[1] + 0.05) m[1] = Math.max(m[1], b[1]); else merged.push(b.slice());
    });
    merged.forEach(function (m) {
      if (m[1] - m[0] > TEXT_MAX + 0.001) issue('[' + fig.id + '] "' + s.name + '" 단계의 글 등장이 1초를 넘는다(' + (m[1] - m[0]).toFixed(2) + '초)');
    });
    var n = 0; L.fin.forEach(function (v) { n += chars(v); });
    if (n > CHAR_MAX) issue('[' + fig.id + '] "' + s.name + '" 단계의 설명이 30자를 넘는다(' + n + '자)');
  }
  function len(e) { return e && e.getTotalLength ? e.getTotalLength() : 0; }
  var shown = typeof WeakMap === 'function' ? new WeakMap() : null; // 글자 요소마다 직전 단계에서 보인 문장
  function textTween(tl, e, from, render, dur, at) { // 되감을 때 직전 단계의 문장으로 돌아가게 한다
    var prev = shown && shown.has(e) ? shown.get(e) : e.textContent, p = { v: 0 }, full = render(1);
    if (shown) shown.set(e, full);
    var tw = gsap.to(p, { v: 1, duration: Math.min(dur, TEXT_MAX), ease: 'none',
      onUpdate: function () { e.textContent = p.v === 0 ? prev : render(p.v); } });
    tl.add(tw, at);
    if (stepLog) {
      if (full) stepLog.beats.push([tw.startTime(), tw.startTime() + tw.duration()]);
      stepLog.fin.set(e, full); // 같은 칸을 다시 쓰면 마지막 글만 센다
    }
    return tl;
  }
  RC.fx = {
    mark: function (tl, e, color, at) {
      return tl.to(e, { stroke: tok(color || 'accent'), strokeWidth: 2, duration: 0.3 }, at);
    },
    unmark: function (tl, els, at) { return tl.set(els, { stroke: tok('ink'), strokeWidth: 1 }, at); },
    spot: function (tl, frame, e, color, at) { // 초점 틀을 도형 e로 옮기고, e는 현재 도형, 직전 도형은 지나온 도형으로 바꾼다
      var c = tok(color || 'accent'), b = geom(e), P = 6;
      var pts = [[b.x - P, b.y - P], [b.x + b.width + P, b.y - P], [b.x + b.width + P, b.y + b.height + P], [b.x - P, b.y + b.height + P]];
      if (frame.cur && frame.cur !== e) tl.to(frame.cur, { stroke: tok('accent-2'), strokeWidth: 1.5, fillOpacity: 0, duration: 0.3 }, at);
      else tl.to({}, { duration: 0 }, at);
      if (!frame.cur) { // 처음에는 크게 나타났다가 조여진다
        pts.forEach(function (p, i) { var o = [[-1, -1], [1, -1], [1, 1], [-1, 1]][i]; tl.set(frame.c[i], { x: p[0] + o[0] * 14, y: p[1] + o[1] * 14 }, '<'); });
        tl.set(frame.g, { opacity: 0 }, '<');
      }
      tl.to(frame.g, { opacity: 1, stroke: c, duration: 0.3 }, '<');
      pts.forEach(function (p, i) { tl.to(frame.c[i], { x: p[0], y: p[1], duration: 0.45, ease: 'power3.inOut' }, '<'); });
      tl.set(e, { fill: c, fillOpacity: 0 }, '<');
      tl.to(e, { stroke: c, strokeWidth: 2, fillOpacity: 0.08, duration: 0.35 }, '<0.1');
      frame.cur = e;
      return tl;
    },
    unspot: function (tl, frame, els, at) { // 시나리오를 다시 시작할 때 도형과 초점 틀을 처음 상태로 돌린다
      els = [].concat(els || []);
      if (els.length) { tl.set(els, { stroke: tok('ink'), strokeWidth: 1, fillOpacity: 0 }, at); at = '<'; }
      tl.set(frame.g, { opacity: 0 }, at); // 도형 없이 부르면 초점 틀만 숨겨, 다음 spot이 틀을 끌고 가지 않고 새로 나타난다
      frame.cur = null;
      return tl;
    },
    draw: function (tl, line, dur, at) { // 선이 그려지며 나타난다
      var L = len(line);
      gsap.set(line, { strokeDasharray: L, strokeDashoffset: L });
      return tl.to(line, { strokeDashoffset: 0, duration: dur || 0.5, ease: 'none' }, at);
    },
    undraw: function (tl, lines, at) {
      [].concat(lines).forEach(function (l) { tl.set(l, { strokeDashoffset: len(l) }, at); });
      return tl;
    },
    follow: function (tl, dot, path, dur, at) { // 표식이 선을 따라 이동한다
      var L = len(path), n = 12, frames = [];
      for (var i = 1; i <= n; i++) {
        var pt = path.getPointAtLength(L * i / n);
        frames.push({ attr: { cx: pt.x, cy: pt.y } });
      }
      return tl.to(dot, { keyframes: frames, duration: dur || 0.6, ease: 'power1.inOut' }, at);
    },
    pop: function (tl, e, at) { // 살짝 튀어나오며 등장한다
      gsap.set(e, { opacity: 0, scale: 0.3, transformOrigin: '50% 50%' });
      return tl.to(e, { opacity: 1, scale: 1, duration: 0.35, ease: 'back.out(2.2)' }, at);
    },
    hide: function (tl, els, at) { return tl.set(els, { opacity: 0, scale: 0.3, transformOrigin: '50% 50%' }, at); },
    think: function (tl, person, question, at) { // 고개를 갸웃하고 물음표가 깜빡인다(약 0.8초)
      tl.to(person, { rotation: -8, transformOrigin: '50% 100%', duration: 0.2, yoyo: true, repeat: 3 }, at);
      return tl.to(question, { y: -4, duration: 0.2, yoyo: true, repeat: 3 }, '<');
    },
    swap: function (tl, from, to, at) { // 한 아이콘을 다른 아이콘으로 바꾼다(물음표 → 판정)
      tl.to(from, { opacity: 0, scale: 0.6, transformOrigin: '50% 50%', duration: 0.15 }, at);
      return RC.fx.pop(tl, to); // 앞 아이콘이 사라진 뒤 나타나 두 아이콘이 겹치지 않는다
    },
    shake: function (tl, e, at) { return tl.to(e, { x: 5, duration: 0.06, yoyo: true, repeat: 5 }, at); },
    type: function (tl, e, text, dur, at) { // 문장이 타이핑되듯 나타난다. dur 0이면 바로 바뀐다
      return textTween(tl, e, '', function (v) { return text.slice(0, Math.ceil(text.length * v)); },
        dur == null ? Math.min(0.6, text.length * 0.03) : dur, at);
    },
    clear: function (tl, note, icons, at) { // 직전 단계의 쌍(설명 상자와 아이콘)을 함께 지운다. 단계의 맨 처음에 둔다
      var els = [note.g].concat(icons || []);
      tl.to(els, { opacity: 0, duration: 0.15 }, at);
      return tl.set(icons || [], { scale: 0.3, transformOrigin: '50% 50%' });
    },
    pair: function (tl, note, icons, x, y, text, dur, at) { // 아이콘과 설명 상자를 같은 순간에 함께 띄우고 문장을 타이핑한다
      icons = [].concat(icons || []);
      tl.set(note.g, { x: x, y: y }, at); // 보이지 않는 동안 자리를 옮긴다
      RC.fx.type(tl, note.n, '', 0, '<');
      tl.to(note.g, { opacity: 1, duration: 0.25 }, '<');
      icons.forEach(function (e) { RC.fx.pop(tl, e, '<'); });
      return RC.fx.type(tl, note.t, text, dur, '<');
    },
    say: function (tl, note, x, y, text, dur, at) { return RC.fx.pair(tl, note, [], x, y, text, dur, at); },
    count: function (tl, e, from, to, suffix, dur, at) { // 숫자가 올라가며 표시된다
      return textTween(tl, e, '', function (v) { return Math.round(from + (to - from) * v).toLocaleString('ko-KR') + (suffix || ''); },
        dur == null ? 0.4 : dur, at);
    }
  };

  /* 애니메이션 */
  var SCEN = /^(시나리오 [^·]+?) · (.+)$/;
  function scenarioGroups(steps) { // '시나리오 X · Y' 단계를 이어진 구간끼리 X로 묶는다. 다른 이름은 묶지 않는다
    var of = [], list = [];
    steps.forEach(function (s, i) {
      var m = SCEN.exec(s.name || ''), g = list[list.length - 1];
      if (!m) { of.push(null); return; }
      if (!g || g.name !== m[1] || g.to !== i - 1) { g = { name: m[1], from: i, to: i }; list.push(g); } else g.to = i;
      of.push(g);
    });
    return { of: of, list: list };
  }
  RC.demo = function (fig, steps) {
    if (!fig) { console.error('RC.demo: figure가 없다'); return null; }
    if (!Array.isArray(steps) || !steps.length) { console.error('RC.demo: 단계 배열이 없다'); return null; }
    fig.classList.add('demo');
    var ctl = el('div', 'demo-ctl'), cap = el('p', 'demo-cap'), list = el('ol', 'demo-steps');
    var bPrev = el('button', null, '이전'), bPlay = el('button', null, '재생'),
        bNext = el('button', null, '다음'), bReset = el('button', null, '처음부터'), cnt = el('span', 'cnt');
    [bPrev, bPlay, bNext, bReset].forEach(function (b) { b.type = 'button'; ctl.appendChild(b); });
    ctl.appendChild(cnt);
    steps.forEach(function (s) {
      var li = el('li');
      li.appendChild(el('b', null, s.name));
      li.appendChild(document.createTextNode(' ' + s.text));
      list.appendChild(li);
    });
    var groups = scenarioGroups(steps), scen = null;
    if (groups.list.length >= 2 && steps.length > 12) { // 조작 줄 아래 별도 줄. 조작 버튼 순서를 바꾸지 않는다
      scen = el('div', 'demo-scen');
      [null].concat(groups.list).forEach(function (g) {
        var b = el('button', g ? null : 'on', g ? g.name : '전체');
        b.type = 'button'; b._rcGroup = g; scen.appendChild(b);
      });
    }
    var src = fig.querySelector('.src');
    [ctl, scen, cap, list].forEach(function (n) { if (n) fig.insertBefore(n, src); });
    var mode = playMode(); fig.dataset.rcMode = mode;
    if (typeof gsap === 'undefined') { fig.classList.add('demo-static'); return null; }

    RC.ready.then(function () {
      var find = function (name) {
        var hit = fig.querySelector('[id="' + name + '"]');
        if (hit) return hit;
        var re = new RegExp('-flowchart-' + name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '-\\d+$');
        var nodes = fig.querySelectorAll('g.node');
        for (var i = 0; i < nodes.length; i++) {
          if (re.test(nodes[i].id)) return nodes[i].querySelector('rect, polygon, path') || nodes[i];
        }
        return null;
      };
      var rec = { last: null, mark: null };
      var $ = function (name) { var e = find(name); if (e && demoStep === rec) rec.last = e; return e; };
      var tl = gsap.timeline({ paused: true }), ends = [], info = [], auto = mode === 'auto';
      function rewindTo(t) { tl.seek(0, false); tl.seek(t, false); } // 처음부터 다시 옮겨 빌드 중 gsap.set이 끼어도 화면 상태를 맞춘다
      var capPrev = null;
      /* Task 4: memo, prevActive */
      /* Task 5: stage, restore, box, vb */
      /* Task 6: usePeep, hideNext, prevIt, NEG */
      try {
        steps.forEach(function (s, i) {
          var start = tl.duration(), pre = Math.max(0, start - 0.01), sub = gsap.timeline();
          stepLog = { beats: [], fin: new Map() };
          rec.last = rec.mark = null; demoStep = rec;
          try { s.play(sub, $); } finally { demoStep = null; }
          var L = stepLog; stepLog = null;
          textRules(L, s, fig);
          tl.add(sub, start);
          if (!auto && sub.duration() > STEP_MAX) sub.timeScale(sub.duration() / STEP_MAX);
          var it = { start: start, active: rec.mark || rec.last, noteOn: false, n: 0, done: start, pause: 0.3,
                     color: undefined, diamond: false, note: null, think: null };
          /* Task 4: it.color, it.diamond, styleNodes */
          /* Task 6: 앞 단계 스틱맨 숨김과 판정 스틱맨 */
          var animEnd = Math.max(sub.endTime(), tl.duration());
          rewindTo(pre);
          /* Task 5: 자동 상자 위치와 it.noteOn */
          /* Task 6: 고민 스틱맨 */
          var pool = textPool(fig);
          rewindTo(pre);
          var before = texts(fig, pool), smp = sampleStep(tl, fig, start, animEnd, before, pool), capText = s.name + ': ' + s.text;
          it.n = smp.n; it.done = smp.done;
          if (!it.noteOn && capPrev !== capText) { it.n += chars(capText); it.done = Math.max(it.done, start + 0.05); } // 자막은 타임라인 밖 글이라 따로 센다
          capPrev = it.noteOn ? null : capText;
          if (auto && animEnd - it.done > holdFor(it.n) + 3) console.warn('RC.demo: [' + fig.id + '] "' + s.name + '" 단계는 글이 끝난 뒤 연출이 길어 체류 상한을 넘는다');
          var end = auto ? Math.max(animEnd, it.done + holdFor(it.n) + HOLD_PAD) : Math.max(animEnd, start + STEP_MIN);
          if (end > tl.duration()) tl.to({}, { duration: end - tl.duration() });
          tl.addLabel('e' + i, end); ends.push(end);
          it.pause = Math.max(0.3, it.done + holdFor(it.n) + HOLD_PAD - end);
          info.push(it);
          tl.to({}, { duration: 0.02 }); // 다음 단계의 즉시 설정이 이 단계의 끝 시각과 겹쳐 미리 실행되지 않게 띄운다
        });
      } catch (e) { // 단계 코드가 틀리면 동작하지 않는 버튼 대신 단계 설명 목록을 보인다
        console.error('RC.demo', e);
        tl.kill();
        fig.classList.add('demo-static');
        /* Task 5: restore() */
        return;
      }
      /* Task 5: restore() */
      rewindTo(0); // 빌드를 끝낸 화면을 처음 상태로 맞춘다
      var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches, last = steps.length - 1;
      var at = null, tw = null, timer = null, quiet = true, pend = null, from = 0, to = last, saved = -1, activeEl = null;
      function stepAt(t) { if (t <= 1e-6) return -1; var i = 0; while (i < last && ends[i] < t - 1e-6) i++; return i; }
      function startOf(i) { return i > 0 ? ends[i - 1] : 0; }
      function label(i) {
        if (i < 0) return '0/' + steps.length;
        var g = groups.of[i];
        return g ? g.name + ' ' + (i - g.from + 1) + '/' + (g.to - g.from + 1) : (i + 1) + '/' + steps.length;
      }
      function show(i) {
        at = i;
        cnt.textContent = label(i);
        cap.textContent = i < 0 ? '' : steps[i].name + ': ' + steps[i].text;
        cap.classList.toggle('rc-off', i >= 0 && info[i].noteOn);
        bPrev.disabled = i < 0;
        bNext.disabled = i === last;
        pend = quiet || i < 0 ? null : i;
      }
      function sync() {
        var t = tl.time(), i = stepAt(t);
        if (i !== at) show(i);
        /* Task 4: data-rc-active 옮기기 */
        /* Task 7: pend 처리(keepInView) */
      }
      function stop() {
        tl.pause();
        if (tw) { tw.kill(); tw = null; }
        if (timer) { timer.kill(); timer = null; }
        bPlay.textContent = '재생';
      }
      function seekTo(t) { tl.seek(t, false); sync(); } // seek의 두 번째 인자 false: 바로 옮겨도 글자 효과(onUpdate)가 끝 상태를 그린다
      function go(i, animate) {
        stop();
        if (i < 0) { seekTo(0); return; }
        if (animate && !reduce) { seekTo(startOf(i)); tw = tl.tweenTo(ends[i], { onComplete: function () { tw = null; } }); }
        else seekTo(ends[i]);
      }
      function play() {
        if (at >= to || at < from - 1) seekTo(startOf(from));
        bPlay.textContent = '일시정지';
        if (auto && !reduce) { tw = tl.tweenTo(ends[to], { onComplete: stop }); return; }
        (function next() { // 단계 넘김: 한 단계를 재생하고 체류 시간 규칙만큼 쉰 뒤 다음 단계로 간다
          var i = at + 1;
          var rest = function () {
            if (i >= to) { stop(); return; }
            timer = gsap.delayedCall(reduce ? holdFor(info[i].n) + HOLD_PAD : info[i].pause, next);
          };
          if (reduce) { seekTo(ends[i]); rest(); }
          else tw = tl.tweenTo(ends[i], { onComplete: function () { tw = null; rest(); } });
        })();
      }
      tl.eventCallback('onUpdate', sync);
      bPrev.onclick = function () { go(at - 1, false); };
      bNext.onclick = function () { go(Math.min(last, at + 1), true); };
      bReset.onclick = function () { whole(); go(-1); };
      bPlay.onclick = function () { if (tw || timer || tl.isActive()) stop(); else play(); };
      function whole() { // 시나리오 범위를 '전체'로 되돌린다
        from = 0; to = last;
        if (scen) [].forEach.call(scen.children, function (x) { x.classList.toggle('on', !x._rcGroup); });
      }
      if (scen) [].forEach.call(scen.children, function (b) {
        b.onclick = function () { // 시나리오를 고르면 첫 단계부터 재생해 그 시나리오 끝에서 멈춘다. '전체'는 처음 상태로 돌아간다
          var g = b._rcGroup;
          if (!g) { whole(); go(-1); return; }
          [].forEach.call(scen.children, function (x) { x.classList.toggle('on', x === b); });
          from = g.from; to = g.to;
          stop(); seekTo(startOf(from)); play();
        };
      });
      new ResizeObserver(function () { if (fig.clientWidth === 0) stop(); }).observe(fig); // 다른 페이지로 넘기면 멈춘다
      addEventListener('beforeprint', function () { saved = at; stop(); quiet = true; seekTo(ends[last]); });
      addEventListener('afterprint', function () { go(saved, false); quiet = false; });
      seekTo(0); quiet = false;
      fig._rcTl = tl; fig.dataset.rcReady = '1'; // C0 하네스와 RC.check가 쓴다
      /* Task 8: watchFit(fig) */
    });
    return null;
  };

  /* 완료 전 판정 도구: 애니메이션을 처음부터 연속 재생하며 매 프레임 겹침을 판정하고 글 규칙 위반(RC.issues)을 함께 돌려준다.
     브라우저에서 RC.check('figure id')를 실행한다. 판정 대상: 아이콘·설명 상자와 무대의 모든 요소(글자·도형·연결선·초점 틀),
     초점 틀과 무대 글자, 무대 글자끼리. class="rc-token"인 이동 표식은 뺀다 */
  RC.check = function (id) {
    var fig = document.getElementById(id), st = fig && fig.querySelector('svg');
    if (!st) return Promise.resolve({ error: '애니메이션 figure가 없다: ' + id });
    var b = fig.querySelectorAll('.demo-ctl button');
    if (b.length < 4) return Promise.resolve({ error: '조작 버튼이 없다(RC.demo를 부르지 않았다)' });
    var op = function (e) { return +getComputedStyle(e).opacity; };
    var box = function (e) {
      var r = e.getBoundingClientRect(), k = /^(path|line)$/.test(e.tagName) ? 1.5 : 0; // 선은 두께만큼 넓혀 본다
      return { l: r.left - k, r: r.right + k, t: r.top - k, b: r.bottom + k };
    };
    var hit = function (a, c) { return Math.max(0, Math.min(a.r, c.r) - Math.max(a.l, c.l)) * Math.max(0, Math.min(a.b, c.b) - Math.max(a.t, c.t)) > 1; };
    var nm = function (e) {
      var g = e.closest('.rc-icon, .rc-note, .rc-focus');
      return g ? g.getAttribute('class') : (e.id || e.tagName + (e.textContent ? ':' + e.textContent.trim().slice(0, 8) : ''));
    };
    var fixed = [].filter.call(st.children, function (e) {
      return /^(text|rect|polygon|circle|path|line)$/.test(e.tagName) && !/\brc-/.test(e.getAttribute('class') || '');
    });
    var texts = fixed.filter(function (e) { return e.tagName === 'text'; });
    function frame() {
      var dyn = [].filter.call(st.querySelectorAll('.rc-icon, .rc-note'), function (e) { return op(e) > 0.05; });
      var f = st.querySelector('.rc-focus'), fc = f && op(f) > 0.05 ? [].slice.call(f.children) : [];
      var bad = [], pair = function (a, c) { if (hit(box(a), box(c))) bad.push(nm(a) + ' × ' + nm(c)); };
      dyn.forEach(function (a, i) { dyn.slice(i + 1).concat(fixed, fc).forEach(function (c) { pair(a, c); }); });
      fc.forEach(function (a) { texts.forEach(function (c) { pair(a, c); }); }); // 초점 틀은 이동 중 가는 선을 스칠 수 있어 글자만 본다
      texts.forEach(function (a, i) { texts.slice(i + 1).forEach(function (c) { pair(a, c); }); });
      return bad;
    }
    return RC.ready.then(function () {
      if (fig.dataset.rcReady !== '1' || fig.classList.contains('demo-static'))
        return { pass: false, error: '애니메이션이 만들어지지 않았다(GSAP이 없거나 단계 코드 오류). 콘솔의 RC.demo 오류를 확인한다' };
      if (!st.getBoundingClientRect().width)
        return { pass: false, error: '애니메이션이 화면에 보이지 않는다. 페이지형 문서는 그 페이지로 이동한 뒤 실행한다' };
      var mine = function () { return RC.issues.filter(function (m) { return m.indexOf('[' + id + ']') === 0; }); };
      return new Promise(function (done) {
        var frames = 0, overlapFrames = 0, samples = [], t0 = performance.now();
        b[3].click(); fig._rcTl.seek(0, false); b[1].click(); // 1단계 연출부터 판정한다
        (function loop() {
          var bad = frame(); frames++;
          if (bad.length) { overlapFrames++; if (samples.length < 5) samples.push(fig.querySelector('.cnt').textContent + ' ' + bad.join('; ')); }
          if (performance.now() - t0 > 500 && b[1].textContent === '재생') {
            b[3].click();
            done({ pass: overlapFrames === 0 && !mine().length, frames: frames, overlapFrames: overlapFrames, overlapSamples: samples,
              issues: mine(), seconds: +((performance.now() - t0) / 1000).toFixed(1) });
          } else requestAnimationFrame(loop);
        })();
      });
    });
  };
})();
