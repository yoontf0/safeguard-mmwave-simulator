"""
SafeGuard 블록 B3 - IWR6843ISK-ODS mmWave 수신 확인 스크립트.

보드에 mmWave SDK 3.6 Out-of-Box 데모(xwr68xx_mmw_demo.bin)가 구워져 있고
S1이 Functional 모드(1 OFF, 2 OFF, 3 ON, 4 ON, 5 OFF)일 때 사용한다.

1. CLI 포트(115200)로 .cfg 명령을 한 줄씩 보낸다 (sensorStop ... sensorStart).
2. 데이터 포트(921600)에서 TLV 프레임을 받아 매직워드로 자르고 파싱한다.
3. 1초마다 프레임/초, 마지막 프레임 점 개수, 가장 가까운 점 거리를 출력한다.

src/ 시뮬레이터와 무관한 하드웨어 전용 스크립트다 (pyserial만 필요).
보드 USB 칩이 CP2105라서 포트가 2개 생긴다:
    - Enhanced 포트 = CLI  (Pi: /dev/ttyUSB0 또는 by-id ...-if00, Windows: COM6)
    - Standard 포트 = 데이터 (Pi: /dev/ttyUSB1 또는 by-id ...-if01, Windows: COM7)

사용법:
    python hardware/mmwave/mmwave_reader.py                       # Pi: 포트 자동 탐색
    python hardware/mmwave/mmwave_reader.py --cli COM6 --data COM7 # 노트북
    python hardware/mmwave/mmwave_reader.py --duration 60 --csv mmwave_log.csv

mmWave Demo Visualizer가 열려 있으면 포트를 잡고 있어서 실패한다. 먼저 닫을 것.
"""

from __future__ import annotations

import argparse
import csv
import glob
import math
import struct
import sys
import time
from pathlib import Path

try:
    import serial  # type: ignore
except ImportError as exc:  # pragma: no cover
    raise ImportError("pyserial이 필요합니다: python -m pip install pyserial") from exc

DEFAULT_CFG = Path(__file__).resolve().parent / "xwr68xx_ods_oob_20261023.cfg"

CLI_BAUD = 115200
DATA_BAUD = 921600

# 프레임 헤더: 매직워드 8바이트 + uint32 8개 (SDK 3.x)
MAGIC = bytes([0x02, 0x01, 0x04, 0x03, 0x06, 0x05, 0x08, 0x07])
HEADER_FMT = "<8I"  # version, totalPacketLen, platform, frameNumber,
                    # timeCpuCycles, numDetectedObj, numTLVs, subFrameNumber
HEADER_LEN = len(MAGIC) + struct.calcsize(HEADER_FMT)  # 40
TLV_HEADER_FMT = "<2I"  # type, length(payload 바이트, TLV 헤더 제외)
TLV_DETECTED_POINTS = 1  # float32 x, y, z, doppler (16바이트/점)
MAX_PACKET_LEN = 64 * 1024  # 이보다 크면 깨진 헤더로 보고 버린다


def find_ports() -> tuple[str | None, str | None]:
    """Pi(리눅스)에서 CP2105 by-id 경로로 CLI/데이터 포트를 찾는다."""
    cli = sorted(glob.glob("/dev/serial/by-id/*CP2105*if00*"))
    data = sorted(glob.glob("/dev/serial/by-id/*CP2105*if01*"))
    if cli and data:
        return cli[0], data[0]
    if Path("/dev/ttyUSB0").exists() and Path("/dev/ttyUSB1").exists():
        return "/dev/ttyUSB0", "/dev/ttyUSB1"
    return None, None


def read_cfg_lines(path: Path) -> list[str]:
    lines = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("%"):
            lines.append(line)
    return lines


def send_cfg(cli: serial.Serial, lines: list[str]) -> bool:
    """명령을 한 줄씩 보내고 'Done'/'Error' 응답을 확인한다."""
    cli.reset_input_buffer()
    ok = True
    for line in lines:
        cli.write((line + "\n").encode("ascii"))
        timeout_s = 3.0 if line.startswith("sensorStart") else 1.0
        deadline = time.monotonic() + timeout_s
        reply = b""
        while time.monotonic() < deadline:
            reply += cli.read(cli.in_waiting or 1)
            if b"Done" in reply or b"Error" in reply or b"Ignored" in reply:
                break
        text = reply.decode("ascii", errors="replace")
        if "Done" in text or "Ignored" in text:
            continue
        # 센서가 이미 멈춰 있을 때 sensorStop이 에러를 내는 건 무시해도 된다
        if line == "sensorStop":
            continue
        ok = False
        detail = " ".join(text.split()) or "(응답 없음)"
        print(f"  [CFG 실패] {line}\n    -> {detail}")
    return ok


def parse_frame(packet: bytes) -> dict:
    """매직워드로 시작하는 완전한 패킷 하나를 파싱한다."""
    (_version, total_len, platform, frame_number, _cycles,
     num_obj, num_tlvs, _subframe) = struct.unpack_from(HEADER_FMT, packet, len(MAGIC))
    points = []
    offset = HEADER_LEN
    for _ in range(num_tlvs):
        if offset + 8 > total_len:
            break
        tlv_type, tlv_len = struct.unpack_from(TLV_HEADER_FMT, packet, offset)
        offset += 8
        if tlv_type == TLV_DETECTED_POINTS:
            for i in range(min(num_obj, tlv_len // 16)):
                x, y, z, v = struct.unpack_from("<4f", packet, offset + i * 16)
                points.append((x, y, z, v))
        offset += tlv_len
    return {"frame_number": frame_number, "platform": platform,
            "num_obj": num_obj, "points": points}


class FrameReader:
    """데이터 포트 바이트 흐름을 쌓아 두고 완전한 프레임만 꺼낸다."""

    def __init__(self) -> None:
        self.buf = bytearray()

    def feed(self, data: bytes) -> list[dict]:
        self.buf += data
        frames = []
        while True:
            start = self.buf.find(MAGIC)
            if start < 0:
                # 매직워드가 경계에 걸쳐 있을 수 있으니 끝 7바이트는 남긴다
                del self.buf[:-(len(MAGIC) - 1)]
                return frames
            if start > 0:
                del self.buf[:start]
            if len(self.buf) < HEADER_LEN:
                return frames
            total_len = struct.unpack_from("<I", self.buf, len(MAGIC) + 4)[0]
            if total_len < HEADER_LEN or total_len > MAX_PACKET_LEN:
                del self.buf[:len(MAGIC)]  # 깨진 헤더: 다음 매직워드를 찾는다
                continue
            if len(self.buf) < total_len:
                return frames
            frames.append(parse_frame(bytes(self.buf[:total_len])))
            del self.buf[:total_len]


def nearest_range_m(points: list[tuple[float, float, float, float]]) -> float | None:
    if not points:
        return None
    return min(math.sqrt(x * x + y * y + z * z) for x, y, z, _v in points)


def run(args: argparse.Namespace) -> int:
    cli_port, data_port = args.cli, args.data
    if not (cli_port and data_port):
        cli_port, data_port = find_ports()
    if not (cli_port and data_port):
        print("mmWave 포트를 못 찾았습니다. 보드 USB 연결을 확인하거나 --cli/--data로 지정하세요.")
        return 1
    print(f"CLI  포트: {cli_port} ({CLI_BAUD})")
    print(f"데이터 포트: {data_port} ({DATA_BAUD})")

    try:
        cli = serial.Serial(cli_port, CLI_BAUD, timeout=0.1)
        data = serial.Serial(data_port, DATA_BAUD, timeout=0.1)
    except serial.SerialException as exc:
        print(f"포트를 열 수 없습니다: {exc}")
        print("mmWave Demo Visualizer나 UniFlash가 켜져 있으면 닫고 다시 실행하세요.")
        return 1

    csv_file = None
    writer = None
    try:
        if not args.no_cfg:
            lines = read_cfg_lines(args.cfg)
            print(f"설정 전송: {args.cfg.name} ({len(lines)}줄)")
            if not send_cfg(cli, lines):
                print("설정 전송 실패. S1이 Functional 모드인지, 보드를 다시 꽂았는지 확인하세요.")
                return 1
            print("설정 완료 -> sensorStart\n")
        data.reset_input_buffer()

        if args.csv:
            csv_file = open(args.csv, "w", newline="", encoding="utf-8")
            writer = csv.writer(csv_file)
            writer.writerow(["wall_time", "frame_number", "num_points", "nearest_range_m"])

        reader = FrameReader()
        t_start = time.monotonic()
        t_report = t_start
        frames_in_window = 0
        total_frames = 0
        dropped = 0
        last_frame_no = None
        last = None

        while args.duration <= 0 or time.monotonic() - t_start < args.duration:
            chunk = data.read(data.in_waiting or 1)
            for frame in reader.feed(chunk):
                total_frames += 1
                frames_in_window += 1
                if last_frame_no is not None and frame["frame_number"] > last_frame_no + 1:
                    dropped += frame["frame_number"] - last_frame_no - 1
                last_frame_no = frame["frame_number"]
                last = frame
                if writer:
                    near = nearest_range_m(frame["points"])
                    writer.writerow([f"{time.time():.3f}", frame["frame_number"],
                                     len(frame["points"]), "" if near is None else f"{near:.3f}"])
                if args.show_points:
                    for x, y, z, v in frame["points"]:
                        print(f"    x={x:+.2f} y={y:+.2f} z={z:+.2f} m  v={v:+.2f} m/s")

            now = time.monotonic()
            if now - t_report >= 1.0:
                fps = frames_in_window / (now - t_report)
                if last is None:
                    print(f"[{now - t_start:5.1f}s] 프레임 없음 - 데이터 포트/설정 확인")
                else:
                    near = nearest_range_m(last["points"])
                    near_txt = "-" if near is None else f"{near:.2f} m"
                    print(f"[{now - t_start:5.1f}s] {fps:4.1f} 프레임/초 | "
                          f"프레임 #{last['frame_number']} | 점 {len(last['points'])}개 | "
                          f"가장 가까운 점 {near_txt} | 누락 {dropped}")
                frames_in_window = 0
                t_report = now
    except serial.SerialException as exc:
        # USB가 빠지면 여기로 온다 (상태기계의 FAIL_SAFE 입력 후보)
        print(f"\nmmWave 포트 끊김: {exc}")
        return 2
    except KeyboardInterrupt:
        print("\n중단 (Ctrl+C)")
    finally:
        try:
            cli.write(b"sensorStop\n")
        except serial.SerialException:
            pass
        cli.close()
        data.close()
        if csv_file:
            csv_file.close()

    print(f"총 {total_frames} 프레임, 누락 {dropped}")
    return 0


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="IWR6843ISK-ODS mmWave 수신 확인")
    p.add_argument("--cli", help="CLI 포트 (예: /dev/ttyUSB0, COM6). 생략하면 자동 탐색")
    p.add_argument("--data", help="데이터 포트 (예: /dev/ttyUSB1, COM7). 생략하면 자동 탐색")
    p.add_argument("--cfg", type=Path, default=DEFAULT_CFG, help="보낼 .cfg 파일")
    p.add_argument("--no-cfg", action="store_true", help="설정을 보내지 않고 수신만 (이미 동작 중일 때)")
    p.add_argument("--duration", type=float, default=0, help="실행 시간(초), 0이면 Ctrl+C까지")
    p.add_argument("--csv", type=Path, help="프레임별 기록 CSV 경로")
    p.add_argument("--show-points", action="store_true", help="점 좌표를 모두 출력")
    return p.parse_args()


if __name__ == "__main__":
    sys.exit(run(_parse_args()))
