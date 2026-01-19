"""
VERICOM DLP 3D Printer GUI - Setting Page
LED Power 및 Blade 설정 페이지
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QFileDialog
)
from PySide6.QtCore import Signal, Qt

from pages.base_page import BasePage
from components.numeric_keypad import NumericKeypad
from controllers.settings_manager import get_settings
from styles.colors import Colors
from styles.fonts import Fonts
from styles.stylesheets import (
    get_axis_panel_style,
    Radius
)


class LEDPowerPanel(QFrame):
    """LED Power 설정 패널"""

    power_changed = Signal(int)  # 파워 값 변경
    led_on = Signal(int)         # LED ON (파워 값 전달)
    led_off = Signal()           # LED OFF
    full_black = Signal(int)     # Full Black (파워 값 전달) - Stray Light 측정용

    def __init__(self, parent=None):
        super().__init__(parent)

        self._power_value = 43   # 기본값 43% (440/1023 올림)
        self._is_on = False
        self._min_power = 9     # 최소 9% (91/1023 올림)
        self._max_power = 100   # 최대 100% (1023)

        self._setup_ui()

    def _setup_ui(self):
        """UI 구성"""
        self.setStyleSheet(get_axis_panel_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 타이틀 (border 없음)
        self.title_label = QLabel("LED POWER SET")
        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.NAVY};
                font-size: 18px;
                font-weight: 700;
                background-color: transparent;
                border: none;
            }}
        """)
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        layout.addStretch(1)

        # 파워 값 표시 (클릭 가능)
        self.power_btn = QPushButton(f"{self._power_value}%")
        self.power_btn.setFixedSize(200, 80)
        self.power_btn.setCursor(Qt.PointingHandCursor)
        self.power_btn.setFont(Fonts.mono_display())
        self._update_power_btn_style()
        self.power_btn.clicked.connect(self._on_power_click)

        power_container = QHBoxLayout()
        power_container.addStretch()
        power_container.addWidget(self.power_btn)
        power_container.addStretch()
        layout.addLayout(power_container)

        layout.addStretch(1)

        # ON/OFF 토글 버튼 + Full Black 버튼
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignCenter)
        btn_layout.setSpacing(10)

        self.btn_toggle = QPushButton("ON")
        self.btn_toggle.setFixedSize(100, 50)
        self.btn_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_toggle.setFont(Fonts.h3())
        self.btn_toggle.clicked.connect(self._on_toggle_click)
        self._update_toggle_style()

        # Full Black 버튼 (Stray Light 측정용)
        self.btn_full_black = QPushButton("BLACK")
        self.btn_full_black.setFixedSize(100, 50)
        self.btn_full_black.setCursor(Qt.PointingHandCursor)
        self.btn_full_black.setFont(Fonts.h3())
        self.btn_full_black.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.NAVY};
                border: none;
                border-radius: {Radius.MD}px;
                color: {Colors.WHITE};
                font-weight: 600;
            }}
            QPushButton:pressed {{
                background-color: #1E3A5F;
            }}
        """)
        self.btn_full_black.clicked.connect(self._on_full_black_click)

        btn_layout.addWidget(self.btn_toggle)
        btn_layout.addWidget(self.btn_full_black)
        layout.addLayout(btn_layout)

        layout.addStretch(1)

    def _update_power_btn_style(self):
        """파워 버튼 스타일 업데이트"""
        self.power_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_SECONDARY};
                border: 2px solid {Colors.CYAN};
                border-radius: {Radius.LG}px;
                color: {Colors.NAVY};
                font-size: 36px;
                font-weight: 700;
            }}
            QPushButton:pressed {{
                background-color: {Colors.BG_TERTIARY};
            }}
        """)

    def _update_toggle_style(self):
        """토글 버튼 스타일 업데이트"""
        if self._is_on:
            # LED가 켜진 상태 → OFF 버튼 (빨간색)
            self.btn_toggle.setText("OFF")
            self.btn_toggle.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.RED};
                    border: none;
                    border-radius: {Radius.MD}px;
                    color: {Colors.WHITE};
                    font-weight: 600;
                }}
                QPushButton:pressed {{
                    background-color: #B91C1C;
                }}
            """)
        else:
            # LED가 꺼진 상태 → ON 버튼 (흰 배경 + 테두리)
            self.btn_toggle.setText("ON")
            self.btn_toggle.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.BG_PRIMARY};
                    border: 2px solid {Colors.BORDER};
                    border-radius: {Radius.MD}px;
                    color: {Colors.TEXT_PRIMARY};
                    font-weight: 600;
                }}
                QPushButton:pressed {{
                    background-color: {Colors.BG_SECONDARY};
                }}
            """)

    def _on_power_click(self):
        """파워 값 클릭 - 키패드 열기"""
        keypad = NumericKeypad(
            title="LED Power",
            value=self._power_value,
            unit="%",
            min_val=self._min_power,
            max_val=self._max_power,
            allow_decimal=False,
            parent=self.window()
        )
        keypad.value_confirmed.connect(self._on_power_confirmed)
        keypad.exec()

    def _on_power_confirmed(self, value: float):
        """파워 값 확정"""
        self._power_value = int(value)
        self.power_btn.setText(f"{self._power_value}%")
        self.power_changed.emit(self._power_value)

    def _on_toggle_click(self):
        """ON/OFF 토글"""
        if self._is_on:
            # 현재 켜진 상태 → 끄기
            self._is_on = False
            self.led_off.emit()
        else:
            # 현재 꺼진 상태 → 켜기
            self._is_on = True
            self.led_on.emit(self._power_value)
        self._update_toggle_style()

    def _on_full_black_click(self):
        """Full Black 버튼 클릭 - Stray Light 측정용 전체 검정 화면"""
        self.full_black.emit(self._power_value)

    def get_power(self) -> int:
        """현재 파워 값 반환"""
        return self._power_value

    def set_power(self, value: int):
        """파워 값 설정"""
        self._power_value = max(self._min_power, min(self._max_power, value))
        self.power_btn.setText(f"{self._power_value}%")


class BladePanel(QFrame):
    """Blade 설정 패널"""

    speed_changed = Signal(int)    # 속도 변경
    blade_move = Signal()          # MOVE 버튼 클릭
    home_axis = Signal()           # 홈 이동

    def __init__(self, parent=None):
        super().__init__(parent)

        self._speed_value = 30  # 기본값 30 mm/s
        self._min_speed = 10    # 최소 10 mm/s
        self._max_speed = 100   # 최대 100 mm/s

        self._setup_ui()

    def _setup_ui(self):
        """UI 구성"""
        self.setStyleSheet(get_axis_panel_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 타이틀 (border 없음)
        self.title_label = QLabel("BLADE SET")
        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.NAVY};
                font-size: 18px;
                font-weight: 700;
                background-color: transparent;
                border: none;
            }}
        """)
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        layout.addStretch(1)

        # Speed 라벨 (border 없음)
        speed_label = QLabel("Speed")
        speed_label.setAlignment(Qt.AlignCenter)
        speed_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-size: 14px;
                background-color: transparent;
                border: none;
            }}
        """)
        layout.addWidget(speed_label)

        # 속도 값 표시 (클릭 가능)
        self.speed_btn = QPushButton(f"{self._speed_value} mm/s")
        self.speed_btn.setFixedSize(200, 80)
        self.speed_btn.setCursor(Qt.PointingHandCursor)
        self.speed_btn.setFont(Fonts.mono_display())
        self._update_speed_btn_style()
        self.speed_btn.clicked.connect(self._on_speed_click)

        speed_container = QHBoxLayout()
        speed_container.addStretch()
        speed_container.addWidget(self.speed_btn)
        speed_container.addStretch()
        layout.addLayout(speed_container)

        layout.addStretch(1)

        # 제어 버튼들 (HOME, MOVE)
        control_layout = QHBoxLayout()
        control_layout.setSpacing(12)
        control_layout.setAlignment(Qt.AlignCenter)

        # 홈 버튼
        self.btn_home = QPushButton("HOME")
        self.btn_home.setFixedSize(100, 50)
        self.btn_home.setCursor(Qt.PointingHandCursor)
        self.btn_home.setFont(Fonts.h3())
        self.btn_home.setStyleSheet(self._get_action_btn_style())
        self.btn_home.clicked.connect(self.home_axis.emit)

        # MOVE 버튼
        self.btn_move = QPushButton("MOVE")
        self.btn_move.setFixedSize(100, 50)
        self.btn_move.setCursor(Qt.PointingHandCursor)
        self.btn_move.setFont(Fonts.h3())
        self.btn_move.setStyleSheet(self._get_action_btn_style())
        self.btn_move.clicked.connect(self.blade_move.emit)

        control_layout.addWidget(self.btn_home)
        control_layout.addWidget(self.btn_move)

        layout.addLayout(control_layout)

        layout.addStretch(1)

    def _update_speed_btn_style(self):
        """속도 버튼 스타일 업데이트"""
        self.speed_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_SECONDARY};
                border: 2px solid {Colors.CYAN};
                border-radius: {Radius.LG}px;
                color: {Colors.NAVY};
                font-size: 28px;
                font-weight: 700;
            }}
            QPushButton:pressed {{
                background-color: {Colors.BG_TERTIARY};
            }}
        """)

    def _get_action_btn_style(self):
        """액션 버튼 스타일 반환"""
        return f"""
            QPushButton {{
                background-color: {Colors.BG_SECONDARY};
                border: 2px solid {Colors.BORDER};
                border-radius: {Radius.MD}px;
                color: {Colors.TEXT_PRIMARY};
                font-weight: 600;
            }}
            QPushButton:pressed {{
                background-color: {Colors.BG_TERTIARY};
            }}
        """

    def _on_speed_click(self):
        """속도 값 클릭 - 키패드 열기"""
        keypad = NumericKeypad(
            title="Blade Speed",
            value=self._speed_value,
            unit="mm/s",
            min_val=self._min_speed,
            max_val=self._max_speed,
            allow_decimal=False,
            parent=self.window()
        )
        keypad.value_confirmed.connect(self._on_speed_confirmed)
        keypad.exec()

    def _on_speed_confirmed(self, value: float):
        """속도 값 확정"""
        self._speed_value = int(value)
        self.speed_btn.setText(f"{self._speed_value} mm/s")
        self.speed_changed.emit(self._speed_value)

    def get_speed(self) -> int:
        """현재 속도 값 반환"""
        return self._speed_value

    def set_speed(self, value: int):
        """속도 값 설정"""
        self._speed_value = max(self._min_speed, min(self._max_speed, value))
        self.speed_btn.setText(f"{self._speed_value} mm/s")


class MaskPanel(QFrame):
    """MASK 설정 패널"""

    mask_changed = Signal(bool, str)  # (enabled, file_path)
    mask_led_on = Signal(bool, str)  # (mask_enabled, mask_path) - LED ON with mask option
    mask_led_off = Signal()  # LED OFF

    def __init__(self, parent=None):
        super().__init__(parent)

        self._settings = get_settings()
        self._mask_enabled = self._settings.get_mask_enabled()
        self._mask_path = self._settings.get_mask_file_path()
        self._led_on = False  # LED 상태 추적

        self._setup_ui()

    def _setup_ui(self):
        """UI 구성"""
        self.setStyleSheet(get_axis_panel_style())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 타이틀
        self.title_label = QLabel("MASK SET")
        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.NAVY};
                font-size: 18px;
                font-weight: 700;
                background-color: transparent;
                border: none;
            }}
        """)
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        layout.addStretch(1)

        # 파일 경로 표시
        path_label = QLabel("File")
        path_label.setAlignment(Qt.AlignCenter)
        path_label.setStyleSheet(f"""
            QLabel {{
                color: {Colors.TEXT_SECONDARY};
                font-size: 14px;
                background-color: transparent;
                border: none;
            }}
        """)
        layout.addWidget(path_label)

        # 파일 선택 버튼
        self.file_btn = QPushButton(self._get_filename_display())
        self.file_btn.setFixedSize(200, 50)
        self.file_btn.setCursor(Qt.PointingHandCursor)
        self._update_file_btn_style()
        self.file_btn.clicked.connect(self._on_file_click)

        file_container = QHBoxLayout()
        file_container.addStretch()
        file_container.addWidget(self.file_btn)
        file_container.addStretch()
        layout.addLayout(file_container)

        layout.addStretch(1)

        # ON/OFF 토글 버튼
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignCenter)

        self.btn_toggle = QPushButton("ON" if self._mask_enabled else "OFF")
        self.btn_toggle.setFixedSize(120, 50)
        self.btn_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_toggle.setFont(Fonts.h3())
        self.btn_toggle.clicked.connect(self._on_toggle_click)
        self._update_toggle_style()

        btn_layout.addWidget(self.btn_toggle)
        layout.addLayout(btn_layout)

        layout.addStretch(1)

        # LED ON/OFF 버튼 (흰색 전체 화면 + MASK 적용 테스트용)
        led_btn_layout = QHBoxLayout()
        led_btn_layout.setAlignment(Qt.AlignCenter)
        led_btn_layout.setSpacing(10)

        self.btn_led_on = QPushButton("LED ON")
        self.btn_led_on.setFixedSize(90, 45)
        self.btn_led_on.setCursor(Qt.PointingHandCursor)
        self.btn_led_on.setFont(Fonts.body())
        self.btn_led_on.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.NAVY};
                border: none;
                border-radius: {Radius.MD}px;
                color: {Colors.WHITE};
                font-weight: 600;
            }}
            QPushButton:pressed {{
                background-color: {Colors.NAVY_LIGHT};
            }}
        """)
        self.btn_led_on.clicked.connect(self._on_led_on_click)

        self.btn_led_off = QPushButton("LED OFF")
        self.btn_led_off.setFixedSize(90, 45)
        self.btn_led_off.setCursor(Qt.PointingHandCursor)
        self.btn_led_off.setFont(Fonts.body())
        self.btn_led_off.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.RED};
                border: none;
                border-radius: {Radius.MD}px;
                color: {Colors.WHITE};
                font-weight: 600;
            }}
            QPushButton:pressed {{
                background-color: {Colors.RED_LIGHT};
            }}
        """)
        self.btn_led_off.clicked.connect(self._on_led_off_click)
        self.btn_led_off.hide()  # 초기에는 숨김

        led_btn_layout.addWidget(self.btn_led_on)
        led_btn_layout.addWidget(self.btn_led_off)
        layout.addLayout(led_btn_layout)

        layout.addStretch(1)

    def _on_led_on_click(self):
        """LED ON 클릭"""
        self._led_on = True
        self.btn_led_on.hide()
        self.btn_led_off.show()
        self.mask_led_on.emit(self._mask_enabled, self._mask_path)

    def _on_led_off_click(self):
        """LED OFF 클릭"""
        self._led_on = False
        self.btn_led_off.hide()
        self.btn_led_on.show()
        self.mask_led_off.emit()

    def _get_filename_display(self) -> str:
        """파일명 표시용 문자열"""
        if self._mask_path and os.path.exists(self._mask_path):
            filename = os.path.basename(self._mask_path)
            if len(filename) > 15:
                return filename[:12] + "..."
            return filename
        return "Select File..."

    def _update_file_btn_style(self):
        """파일 버튼 스타일 업데이트"""
        has_file = self._mask_path and os.path.exists(self._mask_path)
        border_color = Colors.CYAN if has_file else Colors.BORDER
        text_color = Colors.NAVY if has_file else Colors.TEXT_SECONDARY

        self.file_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.BG_SECONDARY};
                border: 2px solid {border_color};
                border-radius: {Radius.MD}px;
                color: {text_color};
                font-size: 14px;
                font-weight: 600;
            }}
            QPushButton:pressed {{
                background-color: {Colors.BG_TERTIARY};
            }}
        """)

    def _update_toggle_style(self):
        """토글 버튼 스타일 업데이트"""
        if self._mask_enabled:
            self.btn_toggle.setText("ON")
            self.btn_toggle.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.CYAN};
                    border: none;
                    border-radius: {Radius.MD}px;
                    color: {Colors.WHITE};
                    font-weight: 600;
                }}
                QPushButton:pressed {{
                    background-color: #0891B2;
                }}
            """)
        else:
            self.btn_toggle.setText("OFF")
            self.btn_toggle.setStyleSheet(f"""
                QPushButton {{
                    background-color: {Colors.BG_PRIMARY};
                    border: 2px solid {Colors.BORDER};
                    border-radius: {Radius.MD}px;
                    color: {Colors.TEXT_PRIMARY};
                    font-weight: 600;
                }}
                QPushButton:pressed {{
                    background-color: {Colors.BG_SECONDARY};
                }}
            """)

    def _on_file_click(self):
        """파일 선택 클릭"""
        file_path, _ = QFileDialog.getOpenFileName(
            self.window(),
            "MASK 파일 선택",
            "",
            "BMP Files (*.bmp);;All Files (*)"
        )

        if file_path:
            self._mask_path = file_path
            self._settings.set_mask_file_path(file_path)
            self.file_btn.setText(self._get_filename_display())
            self._update_file_btn_style()
            self.mask_changed.emit(self._mask_enabled, self._mask_path)

    def _on_toggle_click(self):
        """ON/OFF 토글"""
        if not self._mask_path or not os.path.exists(self._mask_path):
            # 파일이 없으면 파일 선택 먼저
            self._on_file_click()
            if not self._mask_path:
                return

        self._mask_enabled = not self._mask_enabled
        self._settings.set_mask_enabled(self._mask_enabled)
        self._update_toggle_style()
        self.mask_changed.emit(self._mask_enabled, self._mask_path)

    def get_mask_enabled(self) -> bool:
        """MASK 활성화 여부 반환"""
        return self._mask_enabled

    def get_mask_path(self) -> str:
        """MASK 파일 경로 반환"""
        return self._mask_path


class SettingPage(BasePage):
    """설정 페이지 (LED Power + Blade + MASK)"""

    # LED 시그널
    led_power_changed = Signal(int)
    led_on = Signal(int)  # 파워 값 전달
    led_off = Signal()
    full_black = Signal(int)  # Full Black (파워 값 전달) - Stray Light 측정용

    # Blade 시그널
    blade_speed_changed = Signal(int)
    blade_move = Signal()  # MOVE 버튼 클릭
    blade_home = Signal()

    # MASK 시그널
    mask_changed = Signal(bool, str)  # (enabled, file_path)
    mask_led_on = Signal(bool, str)  # (mask_enabled, mask_path) - MASK 테스트용 LED ON
    mask_led_off = Signal()  # MASK 테스트용 LED OFF

    def __init__(self, parent=None):
        super().__init__("Setting", show_back=True, parent=parent)
        self._setup_content()

    def _setup_content(self):
        """콘텐츠 구성"""
        # 3열 레이아웃
        panels_layout = QHBoxLayout()
        panels_layout.setSpacing(15)

        # LED Power 패널
        self.led_panel = LEDPowerPanel()
        self.led_panel.power_changed.connect(self.led_power_changed.emit)
        self.led_panel.led_on.connect(self.led_on.emit)
        self.led_panel.led_off.connect(self.led_off.emit)
        self.led_panel.full_black.connect(self.full_black.emit)

        # Blade 패널
        self.blade_panel = BladePanel()
        self.blade_panel.speed_changed.connect(self.blade_speed_changed.emit)
        self.blade_panel.blade_move.connect(self.blade_move.emit)
        self.blade_panel.home_axis.connect(self.blade_home.emit)

        # MASK 패널
        self.mask_panel = MaskPanel()
        self.mask_panel.mask_changed.connect(self.mask_changed.emit)
        self.mask_panel.mask_led_on.connect(self.mask_led_on.emit)
        self.mask_panel.mask_led_off.connect(self.mask_led_off.emit)

        panels_layout.addWidget(self.led_panel)
        panels_layout.addWidget(self.blade_panel)
        panels_layout.addWidget(self.mask_panel)

        self.content_layout.addLayout(panels_layout)

    def get_led_power(self) -> int:
        """LED 파워 값 반환"""
        return self.led_panel.get_power()

    def set_led_power(self, value: int):
        """LED 파워 값 설정"""
        self.led_panel.set_power(value)

    def get_blade_speed(self) -> int:
        """Blade 속도 값 반환"""
        return self.blade_panel.get_speed()

    def set_blade_speed(self, value: int):
        """Blade 속도 값 설정"""
        self.blade_panel.set_speed(value)

    def get_mask_enabled(self) -> bool:
        """MASK 활성화 여부 반환"""
        return self.mask_panel.get_mask_enabled()

    def get_mask_path(self) -> str:
        """MASK 파일 경로 반환"""
        return self.mask_panel.get_mask_path()
