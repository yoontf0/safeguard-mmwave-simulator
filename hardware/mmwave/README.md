# hardware/mmwave — 블록 B3 (IWR6843ISK-ODS mmWave 레이더)

마지막 확인: 2026-10-23, IWR6843ISK-ODS **Rev C**, mmWave SDK 3.6.2 Out-of-Box 데모

## 파일

| 파일 | 용도 |
|---|---|
| `xwr68xx_ods_oob_20261023.cfg` | Visualizer에서 저장한 레이더 설정 (10fps, 거리 해상도 0.044 m, 최대 9 m) |
| `mmwave_reader.py` | cfg 전송 → 프레임 수신 → 1초마다 프레임/초·점 개수·가장 가까운 점 거리 출력 |

## 보드 준비 (같은 실수 반복 금지)

1. **S1 스위치** (TI SWRU546E 표 3-3, `ON` 글자 쪽 = ON)

   | 모드 | 1 | 2 | 3 | 4 | 5 | 6 |
   |---|---|---|---|---|---|---|
   | Flashing | ON | OFF | ON | ON | **OFF** | 상관없음 |
   | Functional | **OFF** | OFF | ON | ON | OFF | 상관없음 |

   5번을 ON으로 두면 UniFlash가 `Received unexpected data`로 실패한다.
2. 스위치를 바꾼 뒤에는 **USB를 다시 꽂는다** (모드는 전원이 들어갈 때 정해짐).
3. 보드 USB 칩이 **CP2105**라서 포트가 2개 생긴다 (가이드의 XDS110/ttyACM 아님).
   - Enhanced = CLI (115200): Windows `COM6`, Pi `/dev/ttyUSB0`
   - Standard = 데이터 (921600): Windows `COM7`, Pi `/dev/ttyUSB1`
4. 굽기는 **데스크톱 UniFlash**로 (웹 버전은 Console이 무반응이었음).
   이미지: `C:\ti\mmwave_sdk_03_06_02_00-LTS\packages\ti\demo\xwr68xx\mmw\xwr68xx_mmw_demo.bin`
5. Visualizer 목록에 ODS 항목이 없다 → Platform `xWR68xx`, SDK `3.6`, `4Rx,3Tx(30 Azim 38 Elev)`.
   ISK 안테나 기준이라 각도는 조금 어긋날 수 있지만 재실 확인에는 충분하다.

## 실행

Visualizer와 UniFlash는 **먼저 닫는다** (포트를 잡고 있음).

```bash
# Pi (포트 자동 탐색)
python -m pip install pyserial
python hardware/mmwave/mmwave_reader.py

# 노트북
python hardware/mmwave/mmwave_reader.py --cli COM6 --data COM7

# 60초 기록
python hardware/mmwave/mmwave_reader.py --duration 60 --csv mmwave_log.csv
```

출력 예:

```
[  3.0s] 10.0 프레임/초 | 프레임 #31 | 점 2개 | 가장 가까운 점 0.98 m | 누락 0
```

10/23 노트북 실측 (COM6/COM7, 12초): 31줄 설정 전송 성공, **약 10 프레임/초**, 118 프레임 중 2개 누락
(각각 1프레임씩 건너뜀), 평균 점 9.3개. 0.13 m 점은 계속 잡힌다 (보드 바로 앞 책상·케이블 반사로 추정).

- 종료 코드 `2` = 실행 중 USB가 빠짐 → 나중에 상태기계 FAIL_SAFE 입력으로 쓸 수 있다.
- cfg의 `clutterRemoval -1 0`(정적 클러터 제거 꺼짐) 때문에 벽·가구도 점으로 잡힌다.
  차 안 재실 판단에서는 `clutterRemoval -1 1`로 켜고 비교해 볼 것.

## 다음 할 일 (블록 B3)

- [x] 노트북에서 `mmwave_reader.py` 동작 확인 (10/23)
- [x] Pi에서 실행 (10/23): 포트 자동 탐색 성공(`/dev/serial/by-id/...CP2105...01E86213-if00/if01`),
      30초 동안 **300 프레임, 누락 0, 10 프레임/초**. Pi OS trixie, `python3-serial` 3.5는 기본 설치돼 있었음
- [x] 60초 CSV 기록 (10/23, Pi): 59.9초 동안 **600 프레임, 끊김 0**, 프레임당 점 평균 11.0개(최대 32개),
      가장 가까운 점이 0.3 m보다 먼 프레임 230개 (사람 움직임). 파일은 Pi `~/mmwave_log.csv`
- [x] USB 탈착 (10/23, Pi): 121.7초 실행 중 뽑음 → `mmWave 포트 끊김: device reports readiness to read but
      returned no data (device disconnected ...)` 출력 후 바로 종료 (종료 코드 2 경로). 다시 꽂으면 같은 by-id 이름으로 돌아옴
- **B3 완료**
- [ ] 호흡 검출용 랩(Vital Signs / People Counting) 결정은 그다음
