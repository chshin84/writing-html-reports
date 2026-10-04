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
    if (!ownText(e)) return true; // C0처럼 글자색은 글을 가진 요소에만 본다. 채움이 없는 도형도 보이는 무대 요소다
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
  var authored = { note: new WeakSet(), icon: new WeakSet() }; // 작성자가 RC.note·RC.icon을 만든 figure. 자동 상자·스틱맨을 두지 않는다
  function own(kind, svg) { var f = svg && svg.closest && svg.closest('figure'); if (f) authored[kind].add(f); }
  function peepEl(svg, name, x, y, size) { // 스틱맨 그림. (x, y)는 중심, size는 한 변이다. 처음에는 투명하다
    var P = window.RC_PEEPS, body = P.figures[name].replace(/class="pk"/g, 'fill="' + tok('ink') + '"').replace(/class="pw"/g, 'fill="' + tok('paper') + '"');
    var src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" viewBox="' + P.viewBox + '">' + body + '</svg>');
    var pg = sv('g', { 'class': 'rc-icon', opacity: 0, 'data-rc-peep': name }, svg);
    sv('image', { x: x - size / 2, y: y - size / 2, width: size, height: size, href: src }, pg);
    return pg;
  }
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
    own('icon', svg); var P = window.RC_PEEPS;
    if (svg && P && P.figures[name]) { // 스틱맨: 80×80 image(SVG data URI)로 넣어 경계와 변형 원점이 그림 칸과 같게 한다. 선은 ink, 바탕은 paper 토큰 값을 만들 때 넣는다
      return peepEl(svg, name, x, y, 80);
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
    own('note', svg);
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
  var FX = 'rc-fx'; // spot·unspot가 도형에 주는 트윈의 표시. 현재 노드 표시는 이 트윈을 작성자 색으로 보지 않는다
  RC.fx = {
    mark: function (tl, e, color, at) {
      if (demoStep) demoStep.mark = e && typeof e !== 'string' && e.length != null && !e.tagName ? e[e.length - 1] : e;
      return tl.to(e, { stroke: tok(color || 'accent'), strokeWidth: 2, duration: 0.3 }, at);
    },
    unmark: function (tl, els, at) { return tl.set(els, { stroke: tok('ink'), strokeWidth: 1 }, at); },
    spot: function (tl, frame, e, color, at) { // 초점 틀을 도형 e로 옮기고, e는 현재 도형, 직전 도형은 지나온 도형으로 바꾼다
      if (demoStep) demoStep.mark = e;
      var c = tok(color || 'accent'), b = geom(e), P = 6;
      var pts = [[b.x - P, b.y - P], [b.x + b.width + P, b.y - P], [b.x + b.width + P, b.y + b.height + P], [b.x - P, b.y + b.height + P]];
      if (frame.cur && frame.cur !== e) tl.to(frame.cur, { stroke: tok('accent-2'), strokeWidth: 1.5, fillOpacity: 0, duration: 0.3, data: FX }, at);
      else tl.to({}, { duration: 0 }, at);
      if (!frame.cur) { // 처음에는 크게 나타났다가 조여진다
        pts.forEach(function (p, i) { var o = [[-1, -1], [1, -1], [1, 1], [-1, 1]][i]; tl.set(frame.c[i], { x: p[0] + o[0] * 14, y: p[1] + o[1] * 14 }, '<'); });
        tl.set(frame.g, { opacity: 0 }, '<');
      }
      tl.to(frame.g, { opacity: 1, stroke: c, duration: 0.3 }, '<');
      pts.forEach(function (p, i) { tl.to(frame.c[i], { x: p[0], y: p[1], duration: 0.45, ease: 'power3.inOut' }, '<'); });
      tl.set(e, { fill: c, fillOpacity: 0, data: FX }, '<');
      tl.to(e, { stroke: c, strokeWidth: 2, fillOpacity: 0.08, duration: 0.35, data: FX }, '<0.1');
      frame.cur = e;
      return tl;
    },
    unspot: function (tl, frame, els, at) { // 시나리오를 다시 시작할 때 도형과 초점 틀을 처음 상태로 돌린다
      els = [].concat(els || []);
      if (els.length) { tl.set(els, { stroke: tok('ink'), strokeWidth: 1, fillOpacity: 0, data: FX }, at); at = '<'; }
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
  function authorSet(sub, e, keys) { // 이번 단계에서 작성자가 요소 e에 준 속성 값. 없으면 null
    if (!e) return null;
    var hit = null;
    sub.getChildren(true, true, false).forEach(function (t) {
      if (t.vars.data === FX || t.targets().indexOf(e) < 0) return;
      keys.forEach(function (k) {
        var v = t.vars[k] != null ? t.vars[k] : t.vars.attr && t.vars.attr[k];
        if (v != null) { hit = hit || {}; hit[k] = v; }
      });
    });
    return hit;
  }
  function closedShape(e) { return !!(e && /^(rect|polygon|circle|ellipse)$/i.test(e.tagName) && !e.closest('.rc-note, .rc-icon, .rc-focus')); }
  function mmdShape(e) { return !!(e && e.closest && e.closest('pre.mermaid svg g.node')); }
  function ownFill(e) { var f = e.style.fill || e.getAttribute('fill'); return !!f && f !== 'none'; } // 작성자가 인라인 스타일·속성으로 준 채움
  function styleNodes(tl, sub, cur, prev, at, memo) { // 닫힌 도형에 현재·지나온 노드 표시를 한다. 작성자가 준 색은 덮어쓰지 않는다
    var A = tok('accent'), K = ['stroke', 'strokeWidth', 'fill', 'fillOpacity'];
    if (closedShape(prev) && prev !== cur) {
      var s = authorSet(sub, prev, K) || {}, v = { duration: 0.3, autoRound: false }; // autoRound를 끄지 않으면 GSAP가 1.5px을 2px로 반올림한다
      if (s.stroke == null && !memo.author.has(prev)) v.stroke = tok('accent-2'); // 작성자가 tl.to로 색을 준 적이 있으면 그 색을 둔다
      if (s.strokeWidth == null) v.strokeWidth = 1.5;
      if (s.fill == null && s.fillOpacity == null && memo.fill.has(prev)) { v.fill = memo.fill.get(prev).fill; v.fillOpacity = memo.fill.get(prev).op; }
      tl.to(prev, v, at);
    }
    if (closedShape(cur)) {
      var c = authorSet(sub, cur, K) || {}, w = { duration: 0.3, autoRound: false };
      if (c.stroke == null && !memo.author.has(cur)) w.stroke = A;
      if (c.strokeWidth == null) w.strokeWidth = 2;
      if (c.fill == null && c.fillOpacity == null && !ownFill(cur)) {
        if (!memo.fill.has(cur)) { var cs = getComputedStyle(cur); memo.fill.set(cur, { fill: cs.fill, op: +cs.fillOpacity }); }
        w.fill = A; w.fillOpacity = 0.08;
      }
      tl.to(cur, w, at);
    }
    sub.getChildren(true, true, false).forEach(function (t) { // 작성자가 tl.to·tl.set으로 테두리 색을 준 요소를 기억한다
      if (t.vars.data === FX) return;
      var v = t.vars.stroke != null ? t.vars.stroke : t.vars.attr && t.vars.attr.stroke;
      if (v != null) t.targets().forEach(function (e) { memo.author.add(e); });
    });
  }
  var NOTE_W = 220, GAP = 8, PEEP = 56;
  function reveal(fig) { // 숨은 페이지의 figure를 계산하는 동안만 화면 밖에 펼친다. 되돌리는 함수를 돌려준다
    var undo = [];
    for (var k = 0; k < 6 && !fig.getClientRects().length; k++) {
      var n = fig;
      while (n && n !== document.body && getComputedStyle(n).display !== 'none') n = n.parentElement;
      if (!n || n === document.body) break;
      undo.push([n, n.getAttribute('style')]);
      var w = (n.parentElement && n.parentElement.clientWidth) || document.documentElement.clientWidth;
      n.style.cssText += ';display:block !important;position:absolute !important;left:-99999px !important;top:0 !important;width:' + w + 'px !important';
    }
    return function () { undo.reverse().forEach(function (u) { if (u[1] == null) u[0].removeAttribute('style'); else u[0].setAttribute('style', u[1]); }); };
  }
  function autoNote(svg) { // 자동 설명 상자 하나를 만들어 단계마다 글과 위치만 바꾼다
    var g = sv('g', { 'class': 'rc-note', opacity: 0 }, svg);
    var rect = sv('rect', { x: 0, y: 0, width: NOTE_W, height: 30, style: 'fill:' + tok('paper') + ';stroke:' + tok('hair') }, g);
    var fo = sv('foreignObject', { x: 0, y: 0, width: NOTE_W, height: 30 }, g);
    var div = document.createElement('div'), t = document.createElement('span');
    div.style.cssText = 'padding:6px 8px;font:12.5px/1.45 var(--sans);color:var(--ink);word-break:keep-all';
    div.appendChild(t); fo.appendChild(div);
    return { g: g, rect: rect, fo: fo, div: div, t: t, text: '' };
  }
  function noteHeight(box, text) {
    box.t.textContent = text;
    var h = box.div.offsetHeight;
    box.t.textContent = box.text;
    return h ? Math.ceil(h) + 1 : 18 * Math.ceil(chars(text) * 13 / 204) + 13;
  }
  function userBox(inv, e) { // 화면 경계 상자를 무대 좌표로 바꾼다
    var r = e.getBoundingClientRect(), a = new DOMPoint(r.left, r.top).matrixTransform(inv), b = new DOMPoint(r.right, r.bottom).matrixTransform(inv);
    return { l: Math.min(a.x, b.x), t: Math.min(a.y, b.y), r: Math.max(a.x, b.x), b: Math.max(a.y, b.y) };
  }
  var STAGE_GEOM = 'text, rect, polygon, circle, ellipse, path, line, polyline, foreignObject, image';
  function obstacles(svg, fig, into) { // 무대 요소(도형·글자·간선·간선 이름표·보이는 아이콘)의 상자와 간선 점을 무대 좌표로 into에 더한다
    var inv = svg.getScreenCTM().inverse(), dots = !!svg.closest('pre.mermaid'); // Mermaid 선은 점으로(C0 하네스), 직접 그린 무대의 선은 경계 상자로(RC.check) 본다
    [].forEach.call(svg.querySelectorAll(STAGE_GEOM), function (e) {
      if (e.closest('.rc-note, defs, marker, clipPath, mask, pattern') || !seen(e, fig)) return;
      var c = getComputedStyle(e), tag = e.tagName.toLowerCase();
      var line = tag === 'line' || tag === 'polyline' || (tag === 'path' && (c.fill === 'none' || /,\s*0\)$/.test(c.fill)));
      if (line && dots && e.getTotalLength) {
        var m = e.getScreenCTM(), L = e.getTotalLength();
        for (var s = 0; s <= L; s += 3) { var p = e.getPointAtLength(s); into.pts.push(new DOMPoint(p.x, p.y).matrixTransform(m).matrixTransform(inv)); }
        return;
      }
      var b = userBox(inv, e), k = line ? 1.5 : 0;
      if ((b.r - b.l) * (b.b - b.t) >= 1 || line) into.boxes.push({ l: b.l - k, t: b.t - k, r: b.r + k, b: b.b + k });
    });
    return into;
  }
  function freeAt(u, obs) {
    var l = u.l - 3, t = u.t - 3, r = u.r + 3, b = u.b + 3;
    for (var i = 0; i < obs.boxes.length; i++) { var o = obs.boxes[i]; if (Math.min(r, o.r) - Math.max(l, o.l) > 0.5 && Math.min(b, o.b) - Math.max(t, o.t) > 0.5) return false; }
    for (var k = 0; k < obs.pts.length; k++) { var p = obs.pts[k]; if (p.x >= l && p.x <= r && p.y >= t && p.y <= b) return false; }
    return true;
  }
  function placeUnit(a, nh, peepW, obs, vb, lim) { // 자동 상자(폭 220, 높이 nh)와 스틱맨 칸(peepW가 0이 아니면 56×56)의 위치를 찾는다
    // 쪽은 오른쪽·왼쪽·아래·위 순서로 보고, 한 쪽 안에서는 노드와의 상자 간 거리, 그다음 옆으로 비킨 정도가 작은 위치를 먼저 본다.
    // 상자는 표시 범위 vb 안, 노드 경계에서 lim(무대 단위) 안에만 둔다. 대각선 위치도 상자 간 거리로 잰다
    lim = lim || 40;
    var h = nh, P = peepW ? PEEP : 0, R = lim + NOTE_W + P + h + 8, seenPt = {};
    var near = { // 탐색 범위 밖 장애물과 겹친 간선 점을 미리 덜어 낸다
      boxes: obs.boxes.filter(function (o) { return o.r >= a.l - R && o.l <= a.r + R && o.b >= a.t - R && o.t <= a.b + R; }),
      pts: obs.pts.filter(function (q) {
        if (q.x < a.l - R || q.x > a.r + R || q.y < a.t - R || q.y > a.b + R) return false;
        var key = Math.round(q.x * 2) + ',' + Math.round(q.y * 2);
        if (seenPt[key]) return false;
        seenPt[key] = 1; return true;
      })
    };
    function rect(x, y, w, hh) { return { l: x, t: y, r: x + w, b: y + hh }; }
    function inVb(u) { return u.l >= vb.l && u.t >= vb.t && u.r <= vb.r && u.b <= vb.b; }
    function ok(u) { return inVb(u) && freeAt(u, near); }
    function dist(n) { var dx = Math.max(0, n.l - a.r, a.l - n.r), dy = Math.max(0, n.t - a.b, a.t - n.b); return Math.sqrt(dx * dx + dy * dy); }
    function sweep(lo, hi, mid) { var v = [mid]; for (var d = 4; mid - d >= lo || mid + d <= hi; d += 4) { if (mid + d <= hi) v.push(mid + d); if (mid - d >= lo) v.push(mid - d); } return v; }
    function peeps(side, n) { // 스틱맨 칸 후보: 노드에서 먼 쪽 옆, 또는 노드에서 먼 쪽 위·아래
      var far = side === 1 ? n.l - 4 - P : n.r + 4, end = side === 1 ? n.l : n.r - P, out = [rect(far, n.t, P, P)];
      if (side !== 3) out.push(rect(end, n.b + 4, P, P));
      if (side !== 2) out.push(rect(end, n.t - 4 - P, P, P));
      return out;
    }
    var cy = (a.t + a.b - h) / 2, cx = (a.l + a.r - NOTE_W) / 2;
    for (var side = 0; side < 4; side++) {
      var cands = [];
      for (var g = GAP; g <= lim + 1e-9; g += 4) {
        var room = Math.sqrt(Math.max(0, lim * lim - g * g)); // 이 간격에서 옆으로 비킬 수 있는 거리
        if (side < 2) {
          var x = side === 0 ? a.r + g : a.l - g - NOTE_W;
          sweep(a.t - h - room, a.b + room, cy).forEach(function (y) { cands.push({ n: rect(x, y, NOTE_W, h), off: Math.abs(y - cy) }); });
        } else {
          var y0 = side === 2 ? a.b + g : a.t - g - h;
          sweep(a.l - NOTE_W - room, a.r + room, cx).forEach(function (x2) { cands.push({ n: rect(x2, y0, NOTE_W, h), off: Math.abs(x2 - cx) }); });
        }
      }
      cands.forEach(function (c) { c.d = dist(c.n); });
      cands = cands.filter(function (c) { return c.d <= lim + 1e-9; }).sort(function (p, q) { return p.d - q.d || p.off - q.off; });
      for (var i = 0; i < cands.length; i++) {
        var n = cands[i].n;
        if (!ok(n)) continue;
        var pk = P ? peeps(side, n).filter(ok)[0] : rect(n.r + 4, n.t, 0, 0);
        if (!pk) continue;
        return { side: side, u: { l: Math.min(n.l, pk.l), t: Math.min(n.t, pk.t), r: Math.max(n.r, pk.r), b: Math.max(n.b, pk.b) },
                 note: { x: n.l, y: n.t }, peep: { x: pk.l, y: pk.t } };
      }
    }
    return null;
  }
  function showNote(tl, box, at, p, text, h) { // 단계 시작에 자동 상자의 글과 위치를 바꾼다. p가 null이면 숨긴다
    if (!p) { tl.set(box.g, { opacity: 0 }, at); return; }
    var prev = box.text, o = { v: 0 };
    tl.set(box.g, { x: p.x, y: p.y, opacity: 1 }, at);
    tl.set([box.rect, box.fo], { attr: { height: h } }, at);
    tl.to(o, { v: 1, duration: 0.01, onUpdate: function () { box.t.textContent = o.v > 0 ? text : prev; } }, at); // 되감으면 앞 단계 글로 돌아간다
    box.text = text;
  }
  function keepInView(fig, it, reduce) { // 현재 노드와 설명 상자가 창 밖이면 가장 가까운 위치로 옮긴다. figure가 화면과 겹칠 때만 한다
    var f = fig.getBoundingClientRect(), H = innerHeight, M = 16;
    if (!f.width || f.bottom <= 0 || f.top >= H) return;
    var els = [it.active].concat(it.noteOn ? [].slice.call(fig.querySelectorAll('.rc-note')) : []).filter(Boolean);
    var rs = els.map(function (e) { return e.getBoundingClientRect(); }).filter(function (r) { return r.width || r.height; });
    if (!rs.length) return;
    var how = reduce ? 'auto' : 'smooth', sb = it.active && it.active.closest && it.active.closest('.rc-scroll');
    var top = Math.min.apply(null, rs.map(function (r) { return r.top; })), bot = Math.max.apply(null, rs.map(function (r) { return r.bottom; }));
    var dy = bot - top > H - 2 * M || top < M ? top - M : bot > H - M ? bot - H + M : 0;
    if (sb) { // 390 폭 스크롤 상자 안에서는 가로로도 옮긴다
      var s = sb.getBoundingClientRect(), lf = Math.min.apply(null, rs.map(function (r) { return r.left; })), rt = Math.max.apply(null, rs.map(function (r) { return r.right; }));
      var dx = rt - lf > s.width || lf < s.left ? lf - s.left - M : rt > s.right ? rt - s.right + M : 0;
      if (dx) sb.scrollBy({ left: dx, behavior: how });
    }
    if (dy) scrollBy({ top: dy, behavior: how });
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
      var memo = { author: new Set(), fill: new Map() }, prevActive = null;
      var stage = fig.querySelector('svg'), restore = null;
      try { // 펼친 figure는 빌드가 어떻게 끝나도 되돌린다
      restore = reveal(fig);
      var box = stage && !authored.note.has(fig) && !stage.querySelector('.rc-note') ? autoNote(stage) : null;
      var vbv = stage && stage.viewBox && stage.viewBox.baseVal && stage.viewBox.baseVal.width ? stage.viewBox.baseVal : null;
      var vb = vbv ? { l: vbv.x, t: vbv.y, r: vbv.x + vbv.width, b: vbv.y + vbv.height } : null;
      var usePeep = !!(box && window.RC_PEEPS && !authored.icon.has(fig) && !stage.querySelector('.rc-icon')); // 작성자 아이콘이 없을 때만 자동 스틱맨을 둔다
      var hideNext = [], prevIt = null, NEG = tok('neg');
      if (box) tl.to({}, { duration: 0.01 }); // 시각 0의 즉시 설정은 seek(0)으로 되돌릴 수 없어, 1단계의 자동 상자·스틱맨 설정을 시각 0 뒤에 둔다
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
          var set = authorSet(sub, it.active, ['stroke']);
          it.color = set ? set.stroke : undefined;
          it.diamond = mmdShape(it.active) && it.active.tagName.toLowerCase() === 'polygon';
          styleNodes(tl, sub, it.active, prevActive, start, memo);
          prevActive = it.active;
          if (hideNext.length) tl.set(hideNext, { opacity: 0 }, start);
          hideNext = [];
          if (prevIt && prevIt.think) { // 바로 앞 단계의 마름모 옆 스틱맨을 판정으로 바꾼다. 색은 이번 단계의 강조 색으로 정한다
            var vd = peepEl(stage, it.color === NEG ? 'person-fail' : 'person-done', prevIt.think.x + PEEP / 2, prevIt.think.y + PEEP / 2, PEEP);
            tl.set(vd, { opacity: 1 }, start); hideNext.push(vd);
          }
          var animEnd = Math.max(sub.endTime(), tl.duration());
          rewindTo(pre);
          if (box && vb && it.active && stage.contains(it.active) && stage.getScreenCTM()) {
            try { // 위치 계산이 실패해도 그 단계에 상자를 두지 않을 뿐 애니메이션은 만든다
              var obs = { boxes: [], pts: [] }, ots = [];
              for (var ot = start; ot < animEnd - 1e-9; ot += 0.25) ots.push(ot);
              ots.push(animEnd);
              ots.forEach(function (t) { tl.seek(t, false); obstacles(stage, fig, obs); });
              var cm = stage.getScreenCTM(), a = userBox(cm.inverse(), it.active), nh = noteHeight(box, s.text);
              var lim = Math.min(40, 44 / (Math.sqrt(Math.abs(cm.a * cm.d - cm.b * cm.c)) || 1)); // 화면 거리 44px(판정 48px) 안에 들도록 무대 단위로 바꾼다
              var peepW = usePeep && it.diamond ? PEEP + 4 : 0;
              it.note = peepW && placeUnit(a, nh, peepW, obs, vb, lim); // 스틱맨 칸까지 들어갈 위치가 없으면 상자만 둔다
              if (it.note) it.note.think = true;
              else it.note = placeUnit(a, nh, 0, obs, vb, lim);
              showNote(tl, box, start, it.note && it.note.note, s.text, nh);
            } catch (err) { console.error('RC.demo: 자동 설명 상자 위치 계산', err); it.note = null; tl.set(box.g, { opacity: 0 }, start); }
            rewindTo(pre);
          } else if (box) tl.set(box.g, { opacity: 0 }, start);
          var authorNotes = [].filter.call(fig.querySelectorAll('.rc-note'), function (n) { return !box || n !== box.g; });
          if (authorNotes.length) { tl.seek(animEnd, false); it.noteOn = authorNotes.some(function (n) { return seen(n, fig); }); rewindTo(pre); } // 작성자 상자가 단계 끝에 보이는지
          if (it.note) it.noteOn = true;
          it.think = usePeep && it.diamond && it.note && it.note.think ? it.note.peep : null;
          if (it.think) {
            var th = peepEl(stage, 'person', it.think.x + PEEP / 2, it.think.y + PEEP / 2, PEEP);
            tl.set(th, { opacity: 1 }, start); hideNext.push(th);
          }
          prevIt = it;
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
        return;
      }
      } finally { if (restore) restore(); }
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
        var a = i < 0 ? null : t >= ends[i] - 1e-6 ? info[i].active : i > 0 ? info[i - 1].active : null;
        if (a !== activeEl) {
          if (activeEl) activeEl.removeAttribute('data-rc-active');
          activeEl = a;
          if (a) a.setAttribute('data-rc-active', '');
        }
        if (pend !== null && t >= info[pend].start + 1e-3) { var k = pend; pend = null; keepInView(fig, info[k], reduce); }
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
