# hardware/mmwave/vital_signs — Vital Signs With People Tracking (실험)

상태: **cfg만 준비, 아직 시험 안 함** (2026-10-24)

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
