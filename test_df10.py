"""
DF10 시리얼 통신 테스트 스크립트
================================

DF10 드라이버 보드와의 시리얼 통신을 테스트합니다.

사용법:
    python test_df10.py                    # 자동 포트 검색
    python test_df10.py COM3               # 특정 포트 지정
    python test_df10.py --sim              # 시뮬레이션 모드
    python test_df10.py --list             # 사용 가능한 포트 목록

테스트 항목:
    1. 시리얼 포트 연결
    2. 버전 조회
    3. 온도 조회
    4. LED ON/OFF 테스트
    5. 밝기 조절 테스트
"""

import sys
import time
import argparse
import serial.tools.list_ports
from controllers.dlp_controller import DLPController, DLPConfig, FlipMode


def list_ports():
    """사용 가능한 시리얼 포트 목록 출력"""
    print("\n사용 가능한 시리얼 포트:")
    print("-" * 60)

    ports = serial.tools.list_ports.comports()
    if not ports:
        print("  (발견된 포트 없음)")
        return

    for port in ports:
        print(f"  {port.device}")
        print(f"    설명: {port.description}")
        print(f"    HWID: {port.hwid}")
        print()


def test_basic_connection(dlp: DLPController) -> bool:
    """기본 연결 테스트"""
    print("\n[테스트 1] 기본 연결 및 버전 조회")
    print("-" * 40)

    version = dlp.get_version()
    if version:
        print(f"  ✓ 버전: {version}")
        return True
    else:
        print("  ✗ 버전 조회 실패")
        return False


def test_temperature(dlp: DLPController) -> bool:
    """온도 조회 테스트"""
    print("\n[테스트 2] 온도 조회")
    print("-" * 40)

    temp = dlp.get_led_temperature()
    if temp >= 0:
        print(f"  ✓ LED 온도: {temp}°C")

        if temp > 45:
            print(f"    ⚠ 경고: 온도가 높습니다! (권장: <45°C)")
        return True
    else:
        print("  ✗ 온도 조회 실패")
        return False


def test_usage_time(dlp: DLPController) -> bool:
    """사용 시간 조회 테스트"""
    print("\n[테스트 3] 사용 시간 조회")
    print("-" * 40)

    led_time = dlp.get_led_hours()
    dmd_time = dlp.get_dmd_hours()

    if led_time >= 0:
        hours = led_time // 60
        mins = led_time % 60
        print(f"  ✓ LED 사용 시간: {hours}시간 {mins}분")
    else:
        print("  ✗ LED 시간 조회 실패")

    if dmd_time >= 0:
        hours = dmd_time // 60
        mins = dmd_time % 60
        print(f"  ✓ DMD 사용 시간: {hours}시간 {mins}분")
    else:
        print("  ✗ DMD 시간 조회 실패")

    return led_time >= 0


def test_led_control(dlp: DLPController) -> bool:
    """LED ON/OFF 테스트"""
    print("\n[테스트 4] LED ON/OFF 테스트")
    print("-" * 40)

    # 프로젝터 먼저 켜기
    print("  프로젝터 ON...", end=" ")
    if dlp.projector_on():
        print("✓")
    else:
        print("✗")
        return False

    time.sleep(0.5)

    # LED ON
    print("  LED ON (밝기 300)...", end=" ")
    if dlp.led_on(brightness=300):
        print("✓")
    else:
        print("✗")
        dlp.projector_off()
        return False

    # 1초 대기
    print("  1초 대기...")
    time.sleep(1)

    # LED OFF
    print("  LED OFF...", end=" ")
    if dlp.led_off():
        print("✓")
    else:
        print("✗")

    # 프로젝터 끄기
    print("  프로젝터 OFF...", end=" ")
    if dlp.projector_off():
        print("✓")
    else:
        print("✗")

    return True


def test_brightness_control(dlp: DLPController) -> bool:
    """밝기 조절 테스트"""
    print("\n[테스트 5] 밝기 조절 테스트")
    print("-" * 40)

    test_values = [100, 300, 500, 700, 1023]

    dlp.projector_on()
    time.sleep(0.5)

    for brightness in test_values:
        print(f"  밝기 {brightness} 설정...", end=" ")
        if dlp.set_brightness(brightness):
            print("✓")
        else:
            print("✗")
            dlp.projector_off()
            return False
        time.sleep(0.2)

    # 현재 밝기 읽기
    current = dlp.get_brightness()
    print(f"  현재 밝기 읽기: {current}")

    dlp.projector_off()
    return True


def test_flip_modes(dlp: DLPController) -> bool:
    """화면 플립 테스트"""
    print("\n[테스트 6] 화면 플립 모드 테스트")
    print("-" * 40)

    modes = [
        (FlipMode.NONE, "플립 없음"),
        (FlipMode.HORIZONTAL, "좌우 반전"),
        (FlipMode.VERTICAL, "상하 반전"),
        (FlipMode.BOTH, "좌우+상하 반전"),
    ]

    for mode, name in modes:
        print(f"  {name} (모드 {mode.value})...", end=" ")
        if dlp.set_flip(mode):
            print("✓")
        else:
            print("✗")
            return False
        time.sleep(0.2)

    # 원래대로 복원
    dlp.set_flip(FlipMode.NONE)
    return True


def run_interactive_mode(dlp: DLPController):
    """대화형 모드"""
    print("\n" + "=" * 60)
    print("대화형 모드")
    print("=" * 60)
    print("""
명령어:
  on [밝기]     - LED ON (밝기 선택적, 기본 500)
  off           - LED OFF
  b <값>        - 밝기 설정 (91-1023)
  t             - 온도 조회
  v             - 버전 조회
  p on/off      - 프로젝터 ON/OFF
  f <0-3>       - 화면 플립 모드
  fan <1|2> <속도> - 팬 속도 설정
  save          - 설정 저장
  q             - 종료
""")

    while True:
        try:
            cmd = input("\n> ").strip().lower()

            if not cmd:
                continue

            parts = cmd.split()
            action = parts[0]

            if action == 'q' or action == 'quit':
                break

            elif action == 'on':
                brightness = int(parts[1]) if len(parts) > 1 else 500
                print(f"LED ON (밝기: {brightness})")
                dlp.led_on(brightness)

            elif action == 'off':
                print("LED OFF")
                dlp.led_off()

            elif action == 'b' and len(parts) > 1:
                brightness = int(parts[1])
                print(f"밝기 설정: {brightness}")
                dlp.set_brightness(brightness)

            elif action == 't':
                temp = dlp.get_led_temperature()
                print(f"LED 온도: {temp}°C")

            elif action == 'v':
                version = dlp.get_version()
                print(f"버전: {version}")

            elif action == 'p' and len(parts) > 1:
                if parts[1] == 'on':
                    print("프로젝터 ON")
                    dlp.projector_on()
                else:
                    print("프로젝터 OFF")
                    dlp.projector_off()

            elif action == 'f' and len(parts) > 1:
                mode = int(parts[1])
                print(f"플립 모드 설정: {mode}")
                dlp.set_flip(FlipMode(mode))

            elif action == 'fan' and len(parts) > 2:
                fan_id = int(parts[1])
                speed = int(parts[2])
                print(f"팬{fan_id} 속도: {speed}%")
                dlp.set_fan_speed(fan_id, speed)

            elif action == 'save':
                print("설정 저장")
                dlp.save_settings()

            else:
                print("알 수 없는 명령입니다.")

        except ValueError as e:
            print(f"잘못된 입력: {e}")
        except KeyboardInterrupt:
            break

    print("\n종료합니다.")


def main():
    parser = argparse.ArgumentParser(description='DF10 시리얼 통신 테스트')
    parser.add_argument('port', nargs='?', help='시리얼 포트 (예: COM3)')
    parser.add_argument('--sim', action='store_true', help='시뮬레이션 모드')
    parser.add_argument('--list', action='store_true', help='포트 목록 출력')
    parser.add_argument('--interactive', '-i', action='store_true', help='대화형 모드')

    args = parser.parse_args()

    # 포트 목록 출력
    if args.list:
        list_ports()
        return

    print("=" * 60)
    print("DF10 시리얼 통신 테스트")
    print("=" * 60)

    # DLP 컨트롤러 생성
    config = DLPConfig(port=args.port or "")
    dlp = DLPController(simulation=args.sim, config=config)

    # 초기화
    print("\n초기화 중...")
    if not dlp.initialize():
        print("✗ DF10 초기화 실패!")
        print("\n다음을 확인해주세요:")
        print("  1. USB-TTL 케이블이 연결되어 있는지")
        print("  2. DF10 드라이버 보드에 전원이 들어왔는지")
        print("  3. 올바른 시리얼 포트인지 (--list로 확인)")
        return

    print(f"✓ DF10 초기화 성공!")

    if args.interactive:
        # 대화형 모드
        run_interactive_mode(dlp)
    else:
        # 자동 테스트
        results = []

        results.append(("기본 연결", test_basic_connection(dlp)))
        results.append(("온도 조회", test_temperature(dlp)))
        results.append(("사용 시간", test_usage_time(dlp)))

        # LED/밝기 테스트는 사용자 확인 필요
        print("\n" + "=" * 60)
        response = input("LED ON/OFF 테스트를 진행하시겠습니까? (y/n): ").strip().lower()
        if response == 'y':
            results.append(("LED 제어", test_led_control(dlp)))
            results.append(("밝기 조절", test_brightness_control(dlp)))

        response = input("화면 플립 테스트를 진행하시겠습니까? (y/n): ").strip().lower()
        if response == 'y':
            results.append(("화면 플립", test_flip_modes(dlp)))

        # 결과 요약
        print("\n" + "=" * 60)
        print("테스트 결과 요약")
        print("=" * 60)
        for name, passed in results:
            status = "✓ 성공" if passed else "✗ 실패"
            print(f"  {name}: {status}")

        passed_count = sum(1 for _, p in results if p)
        print(f"\n총 {len(results)}개 중 {passed_count}개 성공")

    # 정리
    dlp.close()


if __name__ == "__main__":
    main()
