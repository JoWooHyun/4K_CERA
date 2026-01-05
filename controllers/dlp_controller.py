"""
4K_CERA DLP 3D Printer - DLP Controller
DF10 시리즈 프로젝터 및 LED 제어 (시리얼 UART)

안화광전(Anhua Optoelectronics) DF10 시리즈 0.47 4K DLP 광원 제어

통신 방식: USB to TTL 시리얼 (3.3V)
- 보레이트: 9600
- 데이터 비트: 8
- 스톱 비트: 1
- 패리티: None

참조 문서:
- DF10 Series Data Sheet D (EN).pdf
- WI-EL00069 (V07) 0.47 4K Control Interface Description.pdf
"""

import serial
import serial.tools.list_ports
import time
from typing import Optional, List
from dataclasses import dataclass
from enum import IntEnum


class DF10Command:
    """DF10 시리얼 명령어 상수 (문자열 명령)"""
    # LED 제어
    LED_ON = "CM+LEDE=1"           # LED ON (팬 + LED 동시 켜기)
    LED_OFF = "CM+LEDE=0"          # LED OFF (팬 + LED 동시 끄기)
    LED_BRIGHTNESS = "CM+LEDS="    # 밝기 설정 (0-1023)
    LED_READ_PWM = "CM+LEDR"       # PWM 값 읽기
    LED_READ_TIME = "CM+LEDT"      # LED 사용 시간 읽기

    # 전원 제어 (LED 없이 팬만)
    POWER_ON = "CM+SLED=1"         # 전원 ON (팬 ON, LED 밝기 유지)
    POWER_OFF = "CM+SLED=0"        # 전원 OFF (팬 OFF)

    # 설정
    SET_DEFAULT_BRIGHTNESS = "CM+SBTN="  # 기본 밝기 설정 (91-1023)
    SET_FLIP = "CM+SPJF="          # 화면 플립 (0-3)
    STORE_SETTINGS = "CM+SAVE"     # 현재 설정 저장

    # 조회
    GET_TEMPERATURE = "CM+GTMP"    # LED 온도 조회 (0-100°C)
    GET_VERSION = "CM+VERS"        # 펌웨어 버전 조회
    GET_DMD_TIME = "CM+DMDT"       # DMD 사용 시간 조회

    # 팬 제어
    FAN1_SPEED = "CM+FAN1="        # 팬1 속도 (0-100%)
    FAN2_SPEED = "CM+FAN2="        # 팬2 속도 (0-100%)


class DF10HexCommand:
    """DF10 HEX 명령어 (바이너리 명령)"""
    # 전원 제어
    BOOT_ON = bytes([0x2A, 0xFA, 0x0D])      # 전원 ON (팬 ON, LED OFF)
    BOOT_OFF = bytes([0x2A, 0xFB, 0x0D])     # 전원 OFF
    LED_ON = bytes([0x2A, 0x4B, 0x0D])       # LED ON
    LED_OFF = bytes([0x2A, 0x47, 0x0D])      # LED OFF
    QUERY_STATUS = bytes([0x2A, 0x53, 0x0D]) # 상태 조회
    STORE = bytes([0x2A, 0xFC, 0x0D])        # 설정 저장
    GET_TEMP = bytes([0x2A, 0x4E, 0x0D])     # 온도 조회
    GET_LED_TIME = bytes([0x2A, 0x4F, 0x0D]) # LED 시간 조회
    RESET_LED_TIME = bytes([0x2A, 0xFE, 0x0D])  # LED 시간 리셋
    GET_VERSION = bytes([0x2A, 0xF5, 0x0D])  # 버전 조회
    READ_PWM = bytes([0x2A, 0x54, 0x0D])     # PWM 읽기


class FlipMode(IntEnum):
    """이미지 반전 모드"""
    NONE = 0x00
    HORIZONTAL = 0x01
    VERTICAL = 0x02
    BOTH = 0x03


@dataclass
class DLPConfig:
    """DLP 설정"""
    # 시리얼 포트 설정
    port: str = ""                      # 자동 검색 또는 수동 지정
    baudrate: int = 9600
    timeout: float = 1.0                # 읽기 타임아웃 (초)

    # 밝기 설정 (vgui 호환)
    default_brightness: int = 440       # 기본 밝기
    min_brightness: int = 91            # 최소 밝기
    max_brightness: int = 1023          # 최대 밝기

    # 온도 제한
    max_led_temperature: int = 45       # LED 최대 온도 (°C)

    # 팬 설정
    default_fan_speed: int = 100        # 기본 팬 속도 (%)


class DLPController:
    """
    DF10 시리즈 DLP 프로젝터 및 LED 제어 클래스

    시리얼 통신을 통해 DLPC6540 드라이버 보드 제어
    vgui (NVR2+) 프로젝트와 호환되는 인터페이스 제공
    """

    def __init__(self, simulation: bool = False):
        """
        Args:
            simulation: True면 실제 하드웨어 없이 시뮬레이션
        """
        self.config = DLPConfig()
        self.simulation = simulation
        self._is_initialized = False
        self._projector_on = False
        self._led_on = False
        self._current_brightness = self.config.default_brightness
        self._flip_mode = FlipMode.NONE

        # 시리얼 포트 핸들
        self._serial: Optional[serial.Serial] = None

    # ==================== 초기화 ====================

    def initialize(self) -> bool:
        """DLP 컨트롤러 초기화"""
        if self.simulation:
            print("[DLP] 시뮬레이션 모드로 초기화")
            self._is_initialized = True
            return True

        try:
            # 시리얼 포트 검색 및 연결
            port = self._find_serial_port()
            if not port:
                print("[DLP] DF10 시리얼 포트를 찾을 수 없습니다")
                return False

            self._serial = serial.Serial(
                port=port,
                baudrate=self.config.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.config.timeout
            )

            # 연결 확인 (버전 조회)
            time.sleep(0.5)  # 포트 안정화 대기
            version = self._get_version()
            if version:
                print(f"[DLP] DF10 연결 성공: {port}, 버전: {version}")
            else:
                print(f"[DLP] DF10 연결됨: {port} (버전 조회 실패)")

            self._is_initialized = True
            print("[DLP] DF10 초기화 성공")
            return True

        except serial.SerialException as e:
            print(f"[DLP] 시리얼 포트 연결 실패: {e}")
            return False
        except Exception as e:
            print(f"[DLP] 초기화 실패: {e}")
            return False

    def _find_serial_port(self) -> Optional[str]:
        """DF10 드라이버 보드에 연결된 시리얼 포트 자동 검색"""
        # 수동 지정된 포트가 있으면 사용
        if self.config.port:
            return self.config.port

        # 자동 검색
        ports = serial.tools.list_ports.comports()

        for port in ports:
            desc_lower = port.description.lower()
            # USB-TTL 변환기 일반적인 식별자
            if any(keyword in desc_lower for keyword in
                   ['ch340', 'ch341', 'cp210', 'ft232', 'usb serial', 'usb-serial', 'pl2303']):
                print(f"[DLP] USB-TTL 포트 발견: {port.device} ({port.description})")
                return port.device

        # 못 찾으면 첫 번째 시리얼 포트 시도
        for port in ports:
            if 'COM' in port.device or 'ttyUSB' in port.device or 'ttyACM' in port.device:
                print(f"[DLP] 시리얼 포트 시도: {port.device}")
                return port.device

        return None

    def close(self):
        """리소스 정리"""
        if self._led_on:
            self.led_off()
        if self._projector_on:
            self.projector_off()

        if self._serial and self._serial.is_open:
            self._serial.close()
            print("[DLP] 시리얼 포트 닫힘")

        self._is_initialized = False
        print("[DLP] 컨트롤러 종료")

    @property
    def is_initialized(self) -> bool:
        return self._is_initialized

    # ==================== 시리얼 통신 ====================

    def _send_command(self, command: str, expect_response: bool = True) -> Optional[str]:
        """문자열 명령 전송"""
        if self.simulation:
            print(f"[DLP-SIM] 명령 전송: {command}")
            return "OK"

        if not self._serial or not self._serial.is_open:
            print("[DLP] 시리얼 포트가 열려있지 않습니다")
            return None

        try:
            # 버퍼 클리어
            self._serial.reset_input_buffer()

            # 명령 전송 (CR+LF 추가)
            full_command = f"{command}\r\n"
            self._serial.write(full_command.encode('ascii'))

            if not expect_response:
                return None

            # 응답 읽기
            time.sleep(0.1)
            response = self._serial.readline().decode('ascii').strip()

            return response

        except Exception as e:
            print(f"[DLP] 명령 전송 실패: {e}")
            return None

    def _send_hex_command(self, command: bytes, expect_response: bool = True) -> Optional[bytes]:
        """HEX 명령 전송"""
        if self.simulation:
            print(f"[DLP-SIM] HEX 명령 전송: {command.hex()}")
            return bytes([0x2A, 0x00, 0x00, 0x0D])

        if not self._serial or not self._serial.is_open:
            print("[DLP] 시리얼 포트가 열려있지 않습니다")
            return None

        try:
            self._serial.reset_input_buffer()
            self._serial.write(command)

            if not expect_response:
                return None

            time.sleep(0.1)
            response = self._serial.read(10)

            return response

        except Exception as e:
            print(f"[DLP] HEX 명령 전송 실패: {e}")
            return None

    # ==================== 프로젝터 제어 ====================

    def projector_on(self) -> bool:
        """프로젝터 켜기 (팬 가동 시작)"""
        print("[DLP] 프로젝터 켜기 시도...")

        if self.simulation:
            self._projector_on = True
            print("[DLP] ✅ 프로젝터 ON 성공 (시뮬레이션)")
            return True

        # HEX 명령 사용 (팬 ON, LED OFF 상태)
        response = self._send_hex_command(DF10HexCommand.BOOT_ON)

        if response and len(response) >= 4 and response[2] == 0x00:
            self._projector_on = True
            print("[DLP] ✅ 프로젝터 ON 성공")
            time.sleep(0.5)  # 안정화 대기
            return True

        # 문자열 명령으로 재시도
        response = self._send_command(DF10Command.POWER_ON)
        if response == "OK":
            self._projector_on = True
            print("[DLP] ✅ 프로젝터 ON 성공 (문자열 명령)")
            time.sleep(0.5)
            return True

        print("[DLP] ❌ 프로젝터 ON 실패")
        return False

    def projector_off(self) -> bool:
        """프로젝터 끄기"""
        print("[DLP] 프로젝터 끄기 시도...")

        if self.simulation:
            self._projector_on = False
            print("[DLP] ✅ 프로젝터 OFF 성공 (시뮬레이션)")
            return True

        # 먼저 LED OFF
        if self._led_on:
            self.led_off()

        response = self._send_hex_command(DF10HexCommand.BOOT_OFF)

        if response and len(response) >= 4 and response[2] == 0x00:
            self._projector_on = False
            print("[DLP] ✅ 프로젝터 OFF 성공")
            return True

        # 문자열 명령으로 재시도
        response = self._send_command(DF10Command.POWER_OFF)
        if response == "OK":
            self._projector_on = False
            print("[DLP] ✅ 프로젝터 OFF 성공 (문자열 명령)")
            return True

        print("[DLP] ❌ 프로젝터 OFF 실패")
        return False

    @property
    def is_projector_on(self) -> bool:
        return self._projector_on

    # ==================== LED 제어 ====================

    def led_on(self, brightness: Optional[int] = None) -> bool:
        """
        LED 켜기 (UV 조사 시작)

        Args:
            brightness: 밝기 (91~1023), None이면 현재 설정값 사용
        """
        print("[DLP] UV LED 켜기 시도...")

        # 밝기 설정
        if brightness is not None:
            self.set_brightness(brightness)

        if self.simulation:
            self._led_on = True
            print(f"[DLP] ✅ UV LED ON 성공 (brightness={self._current_brightness}) (시뮬레이션)")
            return True

        # LED ON 명령
        response = self._send_command(DF10Command.LED_ON)

        if response == "OK":
            self._led_on = True
            print(f"[DLP] ✅ UV LED ON 성공 (brightness={self._current_brightness})")
            return True

        # HEX 명령으로 재시도
        response = self._send_hex_command(DF10HexCommand.LED_ON)
        if response and len(response) >= 4 and response[2] == 0x00:
            self._led_on = True
            print(f"[DLP] ✅ UV LED ON 성공 (HEX 명령)")
            return True

        print("[DLP] ❌ UV LED ON 실패")
        return False

    def led_off(self) -> bool:
        """LED 끄기 (UV 조사 중지)"""
        print("[DLP] UV LED 끄기 시도...")

        if self.simulation:
            self._led_on = False
            print("[DLP] ✅ UV LED OFF 성공 (시뮬레이션)")
            return True

        response = self._send_command(DF10Command.LED_OFF)

        if response == "OK":
            self._led_on = False
            print("[DLP] ✅ UV LED OFF 성공")
            return True

        # HEX 명령으로 재시도
        response = self._send_hex_command(DF10HexCommand.LED_OFF)
        if response and len(response) >= 4 and response[2] == 0x00:
            self._led_on = False
            print("[DLP] ✅ UV LED OFF 성공 (HEX 명령)")
            return True

        print("[DLP] ❌ UV LED OFF 실패")
        return False

    @property
    def is_led_on(self) -> bool:
        return self._led_on

    def set_brightness(self, brightness: int) -> bool:
        """
        LED 밝기 설정

        Args:
            brightness: 91~1023
        """
        brightness = max(self.config.min_brightness,
                        min(brightness, self.config.max_brightness))

        print(f"[DLP] LED 밝기를 {brightness}(으)로 설정 중...")

        if self.simulation:
            self._current_brightness = brightness
            print(f"[DLP] ✅ LED 밝기 {brightness} 설정 성공 (시뮬레이션)")
            return True

        command = f"{DF10Command.LED_BRIGHTNESS}{brightness}"
        response = self._send_command(command)

        if response == "OK":
            self._current_brightness = brightness
            print(f"[DLP] ✅ LED 밝기 {brightness} 설정 성공")
            return True

        print(f"[DLP] ❌ LED 밝기 설정 실패")
        return False

    @property
    def current_brightness(self) -> int:
        return self._current_brightness

    # ==================== 이미지 반전 ====================

    def set_flip(self, horizontal: bool = False, vertical: bool = False) -> bool:
        """
        이미지 반전 설정

        Args:
            horizontal: 좌우 반전
            vertical: 상하 반전
        """
        # DF10 플립 모드 계산
        mode = 0
        if horizontal and vertical:
            mode = 3  # BOTH
        elif horizontal:
            mode = 1  # HORIZONTAL
        elif vertical:
            mode = 2  # VERTICAL
        else:
            mode = 0  # NONE

        if self.simulation:
            self._flip_mode = FlipMode(mode)
            print(f"[DLP] 반전 설정: H={horizontal}, V={vertical} (모드 {mode}) (시뮬레이션)")
            return True

        command = f"{DF10Command.SET_FLIP}{mode}"
        response = self._send_command(command)

        if response == "OK":
            self._flip_mode = FlipMode(mode)
            print(f"[DLP] 반전 설정: H={horizontal}, V={vertical} (모드 {mode})")
            return True

        return False

    def get_flip_value(self) -> int:
        """현재 반전 모드 값 반환"""
        return self._flip_mode

    # ==================== 테스트 패턴 ====================

    def set_test_pattern(self, pattern: int) -> bool:
        """
        테스트 패턴 설정

        DF10은 HDMI 입력을 사용하므로 테스트 패턴은 호스트에서 생성해야 함
        이 메서드는 vgui 호환성을 위해 유지
        """
        print(f"[DLP] 테스트 패턴 설정: 0x{pattern:02X} (DF10은 HDMI 입력 사용)")
        return True

    def clear_test_pattern(self) -> bool:
        """테스트 패턴 해제"""
        print("[DLP] 테스트 패턴 해제 (DF10은 HDMI 입력 사용)")
        return True

    # ==================== 상태 조회 ====================

    def _get_version(self) -> Optional[str]:
        """펌웨어 버전 조회"""
        if self.simulation:
            return "DF10-SIM-V1.0"

        response = self._send_command(DF10Command.GET_VERSION)
        if response and response != "ERROR":
            return response
        return None

    def get_led_temperature(self) -> float:
        """LED 온도 조회 (°C)"""
        if self.simulation:
            return 35.0

        response = self._send_command(DF10Command.GET_TEMPERATURE)
        if response and response.isdigit():
            return float(response)
        return -1

    # ==================== 복합 동작 ====================

    def expose(self, duration: float, brightness: Optional[int] = None) -> bool:
        """
        노광 실행

        Args:
            duration: 노광 시간 (초)
            brightness: LED 밝기
        """
        if not self.led_on(brightness):
            return False

        time.sleep(duration)

        return self.led_off()

    def start_exposure_test(self, pattern: int, h_flip: bool, v_flip: bool,
                           brightness: int = 440) -> bool:
        """
        노출 테스트 시작

        Args:
            pattern: 테스트 패턴 (DF10에서는 무시)
            h_flip: 좌우 반전
            v_flip: 상하 반전
            brightness: LED 밝기
        """
        # 프로젝터 켜기
        if not self.projector_on():
            return False

        # 반전 설정
        self.set_flip(h_flip, v_flip)

        # 패턴 설정 (DF10에서는 HDMI 입력)
        self.set_test_pattern(pattern)

        # LED 켜기
        return self.led_on(brightness)

    def stop_exposure_test(self) -> bool:
        """노출 테스트 정지"""
        self.led_off()
        self.clear_test_pattern()
        self.projector_off()
        return True


# 테스트용
if __name__ == "__main__":
    import sys

    # 시뮬레이션 모드로 테스트
    simulation = "--sim" in sys.argv

    dlp = DLPController(simulation=simulation)

    if dlp.initialize():
        print("초기화 성공!")

        # 테스트
        dlp.projector_on()
        dlp.set_brightness(500)
        dlp.led_on()
        time.sleep(1)
        dlp.led_off()
        dlp.projector_off()

        dlp.close()
    else:
        print("초기화 실패")
