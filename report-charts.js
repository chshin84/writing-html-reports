/* report-charts for echarts@6.1.0 mermaid@11.17.2 gsap@3.15.0
   보고서 시각화 연결 코드. build.py가 문서의 BEGIN/END report-charts 사이에 채운다. 원본은 이 파일이고, 문서 안에서 고치지 않는다.
   함수: RC.chart(상자, 옵션), RC.color(토큰 이름), RC.ma(값 배열, n), RC.demo(figure, 단계 배열). 규칙은 SKILL.md '시각화' 절에 있다. */
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

  /* 도식 */
  function renderMermaid() {
    var pres = [].slice.call(document.querySelectorAll('pre.mermaid'));
    if (!pres.length) return null;
    if (typeof mermaid === 'undefined') { pres.forEach(fail); return null; }
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
    return pres.reduce(function (p, pre, i) {
      var src = pre.textContent;
      return p.then(function () { return mermaid.render('rc-mermaid-' + i, src); })
        .then(function (r) { pre.innerHTML = r.svg; pre.classList.add('rendered'); }, function () { fail(pre); });
    }, Promise.resolve());
  }
  RC.ready = new Promise(function (res) {
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', res); else res();
  }).then(function () { return document.fonts ? document.fonts.ready : null; }).then(renderMermaid);

  /* 동작 예시 */
  RC.demo = function (fig, steps) {
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
        return fig.querySelector('[id="' + name + '"]') || fig.querySelector('g.node[id*="-' + name + '-"]');
      };
      var tl = gsap.timeline({ paused: true }), ends = [];
      try {
        steps.forEach(function (s, i) { s.play(tl, $); tl.addLabel('e' + i); ends.push(tl.duration()); });
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
        if (animate && !reduce) tw = tl.tweenTo('e' + i, { onComplete: function () { tw = null; } });
        else tl.seek('e' + i);
        show(i);
      }
      function tick() {
        if (cur < last) { tl.seek('e' + (cur + 1)); show(cur + 1); timer = gsap.delayedCall(1.2, tick); } else stop();
      }
      function play() {
        if (cur === last) go(0, false);
        bPlay.textContent = '일시정지';
        if (reduce) timer = gsap.delayedCall(1.2, tick); else tl.play();
      }
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
      addEventListener('beforeprint', function () { saved = cur; stop(); tl.seek('e' + last); });
      addEventListener('afterprint', function () { go(saved, false); });
      go(0, false);
    });
    return null;
  };
})();
