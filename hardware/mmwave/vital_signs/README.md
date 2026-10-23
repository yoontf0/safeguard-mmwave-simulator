# hardware/mmwave/vital_signs — Vital Signs With People Tracking (실험)

상태: 펌웨어 동작 확인, 호흡수 비교는 아직 (2026-10-24)

## 10/24 결과 (노트북, `mmwave_reader.py`로 cfg 한 줄씩 전송)

| cfg | 결과 |
|---|---|
| `vital_signs_ODS_2m_experimental.cfg` (이 폴더) | 36줄은 통과, **`sensorStart`에서 실패**: `Init Calibration Status = 0xffe Error -1` |
| TI 원본 `vital_signs_ISK_2m.cfg` | **정상 시작**, 약 11 프레임/초 (프레임 주기 90 ms와 일치), 보드 앞 0.6~0.9 m에 점 |

- 결론: Vital Signs ISK 펌웨어는 **ODS 보드에서도 돈다.** 그러나 ODS 송신 안테나 조합(`chirpCfg` 3/3/4 + `bpmCfg -1 1 0 1`)은 이 펌웨어가 받지 않는다.
  People Tracking 펌웨어와 달리 ISK 송신 방식만 지원하는 것으로 보인다. → **실험 cfg는 쓰지 말고 TI 원본 ISK cfg로 시험한다.**
- ISK cfg의 안테나 배치는 ODS와 달라 **좌우 각도는 어긋날 수 있다.** 호흡은 거리 방향의 미세 변위로 계산하므로 동작 가능성은 있다 (시험으로 확인할 것).
- Vital Signs 패킷은 32바이트 채우기 규칙이 달라 TI Visualizer(`parseFrame.py`)도 이 데모에서는 길이 검사를 건너뛴다.
  `mmwave_reader.py`도 이제 TLV 1040이 있는 프레임은 이 검사를 건너뛰고, 대신 **모르는 TLV 번호**가 나오면 깨진 프레임으로 센다.

### 노트북 Industrial Visualizer 시험 (원본 ISK cfg)

- 사람 추적 1명, Range Bin 14, **심박 70.3 표시**, 그러나 **호흡수 N/A ("Holding Breath")** → 이후 Undefined.
- 콘솔에 `Invalid TLV type: 262144 ... Dropping frame`이 반복됐다 = **노트북 수신에서 프레임이 깨져 버려짐**
  (People Tracking 때 노트북 7~8% 손실과 같은 현상). 호흡 파형이 중간에 튀고 0으로 끊긴 원인으로 본다.
- → **Pi에서 `mmwave_reader.py`로 받기** (Pi는 People Tracking 손실 0). 리더가 TLV 1040을 읽어 호흡·심박을 출력·기록한다.
  표시 규칙은 TI Visualizer와 같다: 호흡 흔들림 0 = 값 없음, 0.02 미만 = 숨 참음.

### Pi 1차 측정 (`vital1.csv`, 3분, 혼자, 중간중간 일부러 숨 참음, 직접 센 호흡수 없음)

| 항목 | 결과 |
|---|---|
| 프레임 | 2,000개, 11.1 프레임/초, **누락 0** (노트북에서 보던 깨짐 없음) |
| 호흡·심박 값 | 125번 (약 15프레임마다 한 번, TI 설명과 일치) |
| 호흡 상태 | 정상 값 70%, **숨 참음 30%** (실제로 숨을 참은 것이 반영됨) |
| 거리 칸 | 계속 15 (같은 위치를 봄) |
| 호흡수 (10초 단위 중앙값) | **6.7~15.1회/분**로 들쭉날쭉, 값이 1.7회/분 단위로 끊김 |
| 심박수 (10초 단위 중앙값) | 50~77 |

- 이 측정에서 리더가 프레임 88%를 "깨짐"으로 셌고 그 프레임의 추적 정보를 버렸다 (그래서 추적 0명).
  원인은 리더의 길이 검사: Vital Signs 펌웨어는 호흡 값이 없는 프레임도 32바이트 채우기를 하지 않는다.
  → "딱 맞음 또는 32바이트 채움" 둘 다 정상으로 고쳤다 (실제 누락은 0).
- 정답(직접 센 호흡수)이 없어 정확도는 판단하지 않는다.

### Pi 2차 측정 (`vital2.csv`, 3분, 평소 호흡, 친구가 1분씩 직접 셈)

프레임 2,000개, 11.1 프레임/초, **누락 0, 깨짐 0**, 거리 칸 15 일정.

| 구간 | 친구가 센 값 | 레이더 호흡수 중앙값 (구간 안 범위) | 차이 | 숨 참음 판정 |
|---|---|---|---|---|
| 30~90초 | 22회/분 | 11.7회/분 (6.7~21.8) | -47% | 9번 |
| 120~180초 | 25회/분 | 15.1회/분 (5.0~21.8) | -40% | 6번 |

- 레이더 값이 직접 센 값의 **약 절반**이다. 두 가능성을 아직 구별하지 못했다:
  (1) 들숨과 날숨을 따로 세어 2배가 됐다 (쉬는 성인 보통 분당 12~20회라 22~25회는 높은 편),
  (2) ODS 보드에 ISK cfg를 쓴 탓에 레이더가 절반 빈도로 잡았다 (구간 안에서도 값이 크게 흔들림).
  → 세는 방법을 확인하거나, 배를 동영상으로 찍어 다시 세서 정답을 확정할 것.
- 이 측정에서 추적 수가 계속 0이었다 (Visualizer에서는 같은 펌웨어로 Targets 1). 이 펌웨어는 추적 정보를 TLV 1010이 아닌
  다른 형식으로 보내는 것으로 보인다. 호흡·심박(TLV 1040)은 정상으로 읽혔다. 원인은 따로 확인할 것.
- 친구는 **내쉴 때만** 셌다 → 22, 25회/분이 정답. 레이더가 약 40~47% 낮게 잡았다.
- 유력한 원인: 레이더가 잰 거리 칸 15(15 × 8.4 cm ≈ 1.26 m)가 실제 가슴 거리(약 0.95 m, 칸 11)보다 **약 30 cm 뒤**였다.
  추적 위치로 거리를 정하는 기본 모드(`VSRangeIdxCfg 0`)가 ODS 보드에서 어긋났을 수 있다.
  → 거리를 칸 11로 고정한 `vital_signs_ISK_2m_fixed_bin11.cfg`를 만들어 두었다 (TI 원본에서 `VSRangeIdxCfg` 한 줄만 바꿈, **아직 시험 안 함**).

### 결정 (10/24): 호흡·심박은 여기서 마무리

멘토 의견: mmWave로 호흡수·심박수 검출은 어렵다 → **미세 움직임(재실 확인)만으로 충분**.
재실 확인은 People Tracking 정지 유지 시험 B(정지 구간 95.7% 추적 유지, 최대 공백 1.3초, fineMotion 모드)로 실측 근거가 있다.
Vital Signs는 "ODS 보드에서 동작 확인, 비공식 조합이라 정확도는 주장하지 않음"으로 정리하고, 시간이 남으면 고정 거리 cfg만 시도한다.

- 보고서에는 **호흡수 정확도를 아직 주장하지 않는다.** 현재 말할 수 있는 것: ODS 보드에서 Vital Signs 펌웨어가 동작하고,
  Pi에서 손실 없이 호흡·심박 값을 받으며, 숨 참음이 반영된다.

## 왜 "실험"인가

Radar Toolbox 4.00의 Vital Signs With People Tracking은 **IWR6843ISK와 IWR6843AOPEVM만 공식 지원**한다. 우리 보드(IWR6843ISK-ODS)는 목록에 없다. 소스 코드는 공개되지 않고 바이너리만 있다.

그래도 시도해 볼 근거가 있다. 같은 툴박스의 3D People Tracking은 **ISK와 ODS가 같은 펌웨어를 쓰고 cfg의 안테나 관련 9줄만 다르다** (두 TI cfg를 diff로 확인). 그래서 ISK용 Vital Signs cfg의 그 9줄만 ODS 값으로 바꿨다.

## 파일

| 파일 | 내용 |
|---|---|
| `vital_signs_ODS_2m_experimental.cfg` | TI `vital_signs_ISK_2m.cfg` + 안테나 9줄을 TI `ODS_6m_staticRetention.cfg` 값으로 교체 (`[ODS]` 표시, 원래 값은 주석으로 남김) |

바뀐 줄: `bpmCfg`, `chirpCfg` 3줄(송신 안테나 조합), `antGeometry0/1`, `antPhaseRot`, `fovCfg`, `dynamic2DAngleCfg` 첫 값.
나머지는 TI 원본 그대로다: 추적 영역 센서 앞 0.3~1.75 m, 정지 영역 0.3~1.75 m, `vitalsign 15 300`, `VSRangeIdxCfg 0 21`, 프레임 90 ms.

## TI 파일 (`C:\ti\radar_toolbox_4_00_00_05\source\ti\examples\Industrial_and_Personal_Electronics\Vital_Signs\Vital_Signs_With_People_Tracking`)

- 펌웨어: `prebuilt_binaries\vital_signs_tracking_6843ISK_demo.bin`
- 원본 cfg: `chirp_configs\vital_signs_ISK_2m.cfg`, `vital_signs_ISK_6m.cfg`
- 화면: Industrial Visualizer, Demo는 **Vital Signs with People Tracking**

## 시험 방법

1. 노트북 UniFlash로 `vital_signs_tracking_6843ISK_demo.bin` 굽기 (S1 Flashing: 위·아래·위·위·아래 → 끝나면 1번만 아래)
2. Industrial Visualizer → Device xWR6843, Demo **Vital Signs with People Tracking** → Connect
3. cfg로 **`vital_signs_ODS_2m_experimental.cfg`**를 보내기. 비교용으로 TI 원본 `vital_signs_ISK_2m.cfg`도 한 번
4. 사람 1명이 센서 앞 **0.5~1.5 m**에 앉아서 센서가 **가슴을 향하게**, **20초 이상 가만히** (TI 설명서 조건)
5. 그동안 다른 사람이 **1분 동안 호흡 수를 직접 세기** → 화면의 호흡수와 비교

| 기록할 것 | 실험 cfg (ODS) | 원본 cfg (ISK) |
|---|---|---|
| 사람 추적 박스가 생기는가 | | |
| 호흡수 표시 / 직접 센 값 | | |
| 심박수 표시 (참고용, 정확도 주장 안 함) | | |

**보고서 원칙**: 호흡수는 직접 센 값과의 차이를 숫자로 적는다. 심박수는 "표시됨" 정도로만 쓰고 정확도는 주장하지 않는다.
다시 People Tracking으로 돌아가려면 `3D_people_track_6843_demo.bin`을 다시 굽는다.
