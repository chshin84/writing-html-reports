/* report-charts for echarts@6.1.0 mermaid@11.17.2 gsap@3.15.0
   보고서 시각화 연결 코드. build.py가 문서의 BEGIN/END report-charts 사이에 채운다. 원본은 이 파일이고, 문서 안에서 고치지 않는다.
   함수: RC.chart(상자, 옵션), RC.color(토큰 이름), RC.ma(값 배열, n), RC.demo(figure, 단계 배열),
   RC.icon(무대 svg, 아이콘 이름, x, y), RC.note(무대 svg, 폭, 높이), RC.fx(동작 예시 효과 묶음). 규칙은 SKILL.md '시각화' 절에 있다. */
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

  /* 동작 예시 아이콘: 1px 선으로 그린 상태 표시. (x, y)는 아이콘 중심이고, 처음에는 투명하다 */
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
    person: function (g, x, y) { // 졸라맨: 높이 40, 폭 18
      sv('circle', { cx: x, cy: y - 14, r: 6 }, g);
      sv('path', { d: 'M' + x + ' ' + (y - 8) + 'V' + (y + 8) + 'M' + (x - 9) + ' ' + (y - 2) + 'H' + (x + 9) +
        'M' + (x - 7) + ' ' + (y + 20) + 'L' + x + ' ' + (y + 8) + 'L' + (x + 7) + ' ' + (y + 20) }, g);
    },
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
    if (!svg || !ICONS[name]) { console.error('RC.icon: 무대가 없거나 없는 아이콘 이름 ' + name); return null; }
    var c = tok(ICON_COLOR[name] || 'ink');
    var g = sv('g', { 'class': 'rc-icon', fill: 'none', stroke: c, 'stroke-width': 1, opacity: 0 }, svg);
    ICONS[name](g, x, y);
    [].forEach.call(g.querySelectorAll('text'), function (t) { t.style.fill = c; }); // svg text의 기본 글자색 규칙보다 앞서게 한다
    return g;
  };

  /* 동작 예시 설명 상자: 발췌 문장을 연출 중인 도형 옆에 두어 시선이 무대 안에 머물게 한다.
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

  /* 동작 예시 효과: play(tl, $) 안에서 RC.fx.이름(tl, …)으로 부른다. 단계 하나의 연출은 2초 안팎으로 맞춘다.
     at은 GSAP 위치 인자(생략하면 앞 효과 뒤, '<'이면 앞 효과와 함께)다 */
  function len(e) { return e && e.getTotalLength ? e.getTotalLength() : 0; }
  var shown = typeof WeakMap === 'function' ? new WeakMap() : null; // 글자 요소마다 직전 단계에서 보인 문장
  function textTween(tl, e, from, render, dur, at) { // 되감을 때 직전 단계의 문장으로 돌아가게 한다
    var prev = shown && shown.has(e) ? shown.get(e) : e.textContent, p = { v: 0 };
    if (shown) shown.set(e, render(1));
    return tl.to(p, { v: 1, duration: dur, ease: 'none',
      onUpdate: function () { e.textContent = p.v === 0 ? prev : render(p.v); } }, at);
  }
  RC.fx = {
    mark: function (tl, e, color, at) {
      return tl.to(e, { stroke: tok(color || 'accent'), strokeWidth: 2, duration: 0.3 }, at);
    },
    unmark: function (tl, els, at) { return tl.set(els, { stroke: tok('ink'), strokeWidth: 1 }, at); },
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
    shake: function (tl, e, at) { return tl.to(e, { x: 5, duration: 0.06, yoyo: true, repeat: 5 }, at); },
    type: function (tl, e, text, dur, at) { // 문장이 타이핑되듯 나타난다. dur 0이면 바로 바뀐다
      return textTween(tl, e, '', function (v) { return text.slice(0, Math.ceil(text.length * v)); },
        dur == null ? Math.min(1, text.length * 0.03) : dur, at);
    },
    say: function (tl, note, x, y, text, dur, at) { // 설명 상자를 (x, y)로 옮기고 문장을 타이핑한다. 숫자 칸은 비운다
      tl.set(note.g, { x: x, y: y, opacity: 1 }, at);
      RC.fx.type(tl, note.n, '', 0, '<');
      return RC.fx.type(tl, note.t, text, dur, '<');
    },
    count: function (tl, e, from, to, suffix, dur, at) { // 숫자가 올라가며 표시된다
      return textTween(tl, e, '', function (v) { return Math.round(from + (to - from) * v).toLocaleString('ko-KR') + (suffix || ''); },
        dur == null ? 0.7 : dur, at);
    }
  };

  /* 동작 예시 */
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
    var src = fig.querySelector('.src');
    [ctl, cap, list].forEach(function (n) { fig.insertBefore(n, src); });
    if (typeof gsap === 'undefined') { fig.classList.add('demo-static'); return null; }

    RC.ready.then(function () {
      var $ = function (name) {
        var hit = fig.querySelector('[id="' + name + '"]');
        if (hit) return hit;
        var re = new RegExp('-flowchart-' + name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '-\\d+$');
        var nodes = fig.querySelectorAll('g.node');
        for (var i = 0; i < nodes.length; i++) {
          if (re.test(nodes[i].id)) return nodes[i].querySelector('rect, polygon, path') || nodes[i];
        }
        return null;
      };
      var tl = gsap.timeline({ paused: true }), ends = [];
      try {
        steps.forEach(function (s, i) {
          s.play(tl, $); tl.addLabel('e' + i); ends.push(tl.duration());
          tl.to({}, { duration: 0.02 }); // 다음 단계의 즉시 설정이 이 단계의 끝 시각과 겹쳐 미리 실행되지 않게 띄운다
        });
      } catch (e) { // 단계 코드가 틀리면 동작하지 않는 버튼 대신 단계 설명 목록을 보인다
        console.error('RC.demo', e);
        tl.kill();
        fig.classList.add('demo-static');
        return;
      }
      var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
      var cur = 0, tw = null, timer = null, saved = 0, last = steps.length - 1;

      function show(i) {
        cur = i;
        cnt.textContent = (i + 1) + '/' + steps.length;
        cap.textContent = steps[i].name + ': ' + steps[i].text;
        bPrev.disabled = i === 0;
        bNext.disabled = i === last;
      }
      function stop() {
        tl.pause();
        if (tw) { tw.kill(); tw = null; }
        if (timer) { timer.kill(); timer = null; }
        bPlay.textContent = '재생';
      }
      function go(i, animate) {
        stop();
        if (animate && !reduce) { // 직전 단계로 바로 옮긴 뒤 한 단계만 연출한다(빠르게 여러 번 눌러도 2초 안팎)
          if (i > 0) tl.seek('e' + (i - 1), false);
          tw = tl.tweenTo('e' + i, { onComplete: function () { tw = null; } });
        }
        else tl.seek('e' + i, false);
        show(i);
      }
      function tick() {
        if (cur < last) { tl.seek('e' + (cur + 1), false); show(cur + 1); timer = gsap.delayedCall(1.2, tick); } else stop();
      }
      function play() {
        if (cur === last) go(0, false);
        bPlay.textContent = '일시정지';
        if (reduce) timer = gsap.delayedCall(1.2, tick); else tl.play();
      }
      // seek의 두 번째 인자 false: 바로 이동할 때도 글자 효과(onUpdate)가 끝 상태를 그리게 한다
      tl.eventCallback('onUpdate', function () { // 연속 재생 중에만 단계 표시를 따라가게 한다
        if (tw) return;
        var t = tl.time(), i = 0;
        while (i < last && ends[i] < t - 1e-6) i++;
        if (i !== cur) show(i);
      });
      tl.eventCallback('onComplete', function () { bPlay.textContent = '재생'; });
      bPrev.onclick = function () { go(Math.max(0, cur - 1), false); };
      bNext.onclick = function () { go(Math.min(last, cur + 1), true); };
      bReset.onclick = function () { go(0, false); };
      bPlay.onclick = function () { if (tl.isActive() || tw || timer) stop(); else play(); };
      new ResizeObserver(function () { if (fig.clientWidth === 0) stop(); }).observe(fig); // 다른 페이지로 넘기면 멈춘다
      addEventListener('beforeprint', function () { saved = cur; stop(); tl.seek('e' + last, false); });
      addEventListener('afterprint', function () { go(saved, false); });
      go(0, false);
    });
    return null;
  };
})();
