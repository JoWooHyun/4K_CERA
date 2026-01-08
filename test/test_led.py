"""
DF10 LED 제어 테스트
PDF 문서 기반 (WI-EL00069 V07)

시리얼 설정: 9600, 8N1, 3.3V TTL
"""

import serial
import serial.tools.list_ports
import time
import sys

# HEX 명령어 (PDF 섹션 4)
CMD_BOOT_ON = bytes([0x2A, 0xFA, 0x0D])   # 팬 ON, LED OFF
CMD_BOOT_OFF = bytes([0x2A, 0xFB, 0x0D])  # 팬 OFF, LED OFF
CMD_LED_ON = bytes([0x2A, 0x4B, 0x0D])    # LED ON
CMD_LED_OFF = bytes([0x2A, 0x47, 0x0D])   # LED OFF
CMD_QUERY = bytes([0x2A, 0x53, 0x0D])     # 상태 조회


def find_serial_port():
    """시리얼 포트 자동 검색"""
    ports = serial.tools.list_ports.comports()
    print("사용 가능한 포트:")
    for port in ports:
        print(f"  - {port.device}: {port.description}")

    # USB-TTL 어댑터 찾기
    for port in ports:
        desc = port.description.lower()
        if any(x in desc for x in ['ch340', 'ch341', 'cp210', 'ft232', 'usb', 'serial']):
            return port.device

    if ports:
        return ports[0].device
    return None


def send_command(ser, cmd, name=""):
    """명령 전송 및 응답 수신"""
    print(f"\n[TX] {name}: {cmd.hex(' ')}")

    # 버퍼 클리어
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    # 명령 전송
    ser.write(cmd)
    ser.flush()

    # 응답 대기 (500ms)
    time.sleep(0.5)

    # 응답 읽기
    if ser.in_waiting > 0:
        response = ser.read(ser.in_waiting)
        print(f"[RX] {response.hex(' ')}")
        return response
    else:
        print("[RX] 응답 없음")
        return None


def main():
    # 포트 지정 또는 자동 검색
    if len(sys.argv) > 1:
        port = sys.argv[1]
    else:
        port = find_serial_port()

    if not port:
        print("시리얼 포트를 찾을 수 없습니다.")
        print("사용법: python test_led.py [COM포트]")
        return

    print(f"\n포트: {port}")
    print("설정: 9600, 8N1")

    try:
        # 시리얼 연결
        ser = serial.Serial(
            port=port,
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1
        )
        print("연결 성공!")

        print("\n" + "="*50)
        print("LED 제어 테스트")
        print("="*50)

        # 1. Boot ON (팬 켜기)
        print("\n[1] Boot ON (팬 시작)")
        send_command(ser, CMD_BOOT_ON, "BOOT_ON")
        time.sleep(1)

        # 2. LED ON
        print("\n[2] LED ON")
        send_command(ser, CMD_LED_ON, "LED_ON")

        # 3초 대기
        print("\n[*] 3초 대기...")
        time.sleep(3)

        # 3. LED OFF
        print("\n[3] LED OFF")
        send_command(ser, CMD_LED_OFF, "LED_OFF")
        time.sleep(1)

        # 4. Boot OFF (팬 끄기)
        print("\n[4] Boot OFF (팬 종료)")
        send_command(ser, CMD_BOOT_OFF, "BOOT_OFF")

        print("\n" + "="*50)
        print("테스트 완료!")
        print("="*50)

        ser.close()

    except serial.SerialException as e:
        print(f"시리얼 오류: {e}")
    except KeyboardInterrupt:
        print("\n중단됨")
        if 'ser' in locals():
            # 안전하게 종료
            ser.write(CMD_LED_OFF)
            ser.write(CMD_BOOT_OFF)
            ser.close()


if __name__ == "__main__":
    main()
