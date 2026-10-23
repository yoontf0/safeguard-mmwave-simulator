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
