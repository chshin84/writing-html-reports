# Open Peeps 출처와 라이선스

`report-peeps.js`의 스틱맨 네 가지는 Pablo Stanley의 Open Peeps 조각을 조합해 만든 생성물이다. Open Peeps는 CC0 1.0(퍼블릭 도메인 헌정)으로 공개되어 출처 표시 없이 수정과 재배포를 할 수 있다.

- 공식 사이트: https://www.openpeeps.com/
- 다시 받는 주소: https://gum.co/openpeeps (가격 칸에 0을 넣는다)
- 원본 보관 위치: `assets/open-peeps-src/` (git에서 제외, 이 PC에만 있다)

| 원본 파일 | SHA-256 |
|---|---|
| `Flat Assets.zip` | `2e0a4e79c868ae71f7d1b010ecd111c5015103e097d712955964636cad89ceb5` |
| `open-peeps-mono.fig` | `7b1109c62470d8f421c38fc6c7db3a0268091cf035fa412037d8170dd123b307` |
| `open-peeps-mono.sketch` | `4d90a431934e70e5c7be4576c00cc4b1c1e0a68ae3b94e9ff743992551a7c39b` |
| `open-peeps-mono.studio` | `d9e7541b796297955e1242d94e8e1e4e521f941c66700c8370c7d69df17538b4` |

| 아이콘 이름 | 자세 | 표정 | 머리 |
|---|---|---|---|
| `person` | pose/standing/crossed_arms-1 | face/Suspicious | head/Short 2 |
| `person-guide` | pose/standing/pointing_finger-1 | face/Explaining | head/Short 2 |
| `person-done` | pose/standing/robot_dance-1 | face/Smile Big | head/Short 2 |
| `person-fail` | pose/standing/resting-2 | face/Tired | head/Short 2 |

원본이 사라지면 위 주소에서 다시 받아 SHA-256이 같은지 확인한 뒤 `assets/open-peeps-src/`에 두고 `python tools/build-peeps.py`를 실행한다.
