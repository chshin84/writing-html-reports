# 04-rules.html 애니메이션 실측 기록

2026-10-04 세션에서 L1이 `lens-groups-report/04-rules.html#p2`를 로컬 서버(`python -B -m http.server`)로 열고, Playwright MCP의 `browser_evaluate`로 아래 코드를 실행했다.

```js
async () => {
  await new Promise(r => setTimeout(r, 1500));
  const f = document.getElementById('d-flow');
  const tl = f._rcTl;
  const r = await RC.check('d-flow');
  return {
    timelineSeconds: tl && +tl.duration().toFixed(2),
    steps: f.querySelectorAll('.demo-steps li').length,
    icons: f.querySelectorAll('.rc-icon').length,
    notes: f.querySelectorAll('.rc-note').length,
    capBelowSvg: !!f.querySelector('.demo-cap'),
    check: r
  };
}
```

결과는 다음과 같다.

```json
{"timelineSeconds": 8.96, "steps": 28, "icons": 0, "notes": 0, "capBelowSvg": true,
 "check": {"pass": true, "frames": 1293, "overlapFrames": 0, "overlapSamples": [], "issues": [], "seconds": 9}}
```

같은 문서를 시각 검토 서브에이전트가 따로 측정한 재생 시간은 8.7초다(`visual-review-baseline.md`). 단계 이름과 문장 길이는 파일의 `RC.demo` 호출을 정규식으로 세어 얻었다. 시나리오 A~E가 4·4·5·7·8단계이고, 단계 문장은 공백을 빼고 10~19자다.
