"""
DF10 LED 제어 GUI
간단한 버튼 테스트용
"""

import sys
import serial
import serial.tools.list_ports
import time
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QTextEdit
)
from PySide6.QtCore import Qt

# HEX 명령어
CMD_BOOT_ON = bytes([0x2A, 0xFA, 0x0D])
CMD_BOOT_OFF = bytes([0x2A, 0xFB, 0x0D])
CMD_LED_ON = bytes([0x2A, 0x4B, 0x0D])
CMD_LED_OFF = bytes([0x2A, 0x47, 0x0D])
CMD_QUERY = bytes([0x2A, 0x53, 0x0D])


class LEDControlGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ser = None
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("DF10 LED Control")
        self.setFixedSize(400, 500)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # 포트 선택
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        self.refresh_ports()
        port_layout.addWidget(self.port_combo)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_ports)
        port_layout.addWidget(refresh_btn)
        layout.addLayout(port_layout)

        # 연결 버튼
        connect_layout = QHBoxLayout()
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self.toggle_connection)
        self.connect_btn.setStyleSheet("background-color: #4CAF50; color: white; font-size: 16px; padding: 10px;")
        connect_layout.addWidget(self.connect_btn)
        layout.addLayout(connect_layout)

        # 상태 표시
        self.status_label = QLabel("Disconnected")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; color: red;")
        layout.addWidget(self.status_label)

        layout.addSpacing(20)

        # 프로젝터 제어
        layout.addWidget(QLabel("--- Projector ---"))
        proj_layout = QHBoxLayout()

        self.proj_on_btn = QPushButton("Projector ON")
        self.proj_on_btn.clicked.connect(self.projector_on)
        self.proj_on_btn.setStyleSheet("background-color: #2196F3; color: white; font-size: 14px; padding: 15px;")
        self.proj_on_btn.setEnabled(False)
        proj_layout.addWidget(self.proj_on_btn)

        self.proj_off_btn = QPushButton("Projector OFF")
        self.proj_off_btn.clicked.connect(self.projector_off)
        self.proj_off_btn.setStyleSheet("background-color: #607D8B; color: white; font-size: 14px; padding: 15px;")
        self.proj_off_btn.setEnabled(False)
        proj_layout.addWidget(self.proj_off_btn)

        layout.addLayout(proj_layout)

        layout.addSpacing(20)

        # LED 제어
        layout.addWidget(QLabel("--- LED ---"))
        led_layout = QHBoxLayout()

        self.led_on_btn = QPushButton("LED ON")
        self.led_on_btn.clicked.connect(self.led_on)
        self.led_on_btn.setStyleSheet("background-color: #FF9800; color: white; font-size: 14px; padding: 15px;")
        self.led_on_btn.setEnabled(False)
        led_layout.addWidget(self.led_on_btn)

        self.led_off_btn = QPushButton("LED OFF")
        self.led_off_btn.clicked.connect(self.led_off)
        self.led_off_btn.setStyleSheet("background-color: #795548; color: white; font-size: 14px; padding: 15px;")
        self.led_off_btn.setEnabled(False)
        led_layout.addWidget(self.led_off_btn)

        layout.addLayout(led_layout)

        layout.addSpacing(20)

        # 상태 조회
        self.query_btn = QPushButton("Query Status")
        self.query_btn.clicked.connect(self.query_status)
        self.query_btn.setEnabled(False)
        layout.addWidget(self.query_btn)

        # 로그
        layout.addWidget(QLabel("Log:"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        layout.addWidget(self.log_text)

    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(f"{port.device} - {port.description}", port.device)

    def log(self, msg):
        self.log_text.append(msg)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def toggle_connection(self):
        if self.ser and self.ser.is_open:
            self.disconnect()
        else:
            self.connect()

    def connect(self):
        port = self.port_combo.currentData()
        if not port:
            self.log("No port selected")
            return

        try:
            self.ser = serial.Serial(
                port=port,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()

            self.log(f"Connected to {port}")
            self.status_label.setText(f"Connected: {port}")
            self.status_label.setStyleSheet("font-size: 14px; color: green;")
            self.connect_btn.setText("Disconnect")
            self.connect_btn.setStyleSheet("background-color: #f44336; color: white; font-size: 16px; padding: 10px;")

            # 버튼 활성화
            self.proj_on_btn.setEnabled(True)
            self.proj_off_btn.setEnabled(True)
            self.led_on_btn.setEnabled(True)
            self.led_off_btn.setEnabled(True)
            self.query_btn.setEnabled(True)

        except Exception as e:
            self.log(f"Connection error: {e}")

    def disconnect(self):
        if self.ser:
            self.ser.close()
            self.ser = None

        self.log("Disconnected")
        self.status_label.setText("Disconnected")
        self.status_label.setStyleSheet("font-size: 14px; color: red;")
        self.connect_btn.setText("Connect")
        self.connect_btn.setStyleSheet("background-color: #4CAF50; color: white; font-size: 16px; padding: 10px;")

        # 버튼 비활성화
        self.proj_on_btn.setEnabled(False)
        self.proj_off_btn.setEnabled(False)
        self.led_on_btn.setEnabled(False)
        self.led_off_btn.setEnabled(False)
        self.query_btn.setEnabled(False)

    def send_command(self, cmd, name):
        if not self.ser or not self.ser.is_open:
            self.log("Not connected")
            return None

        self.log(f"[TX] {name}: {cmd.hex(' ')}")

        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self.ser.write(cmd)
        self.ser.flush()

        # 응답 대기
        for _ in range(10):
            time.sleep(0.1)
            if self.ser.in_waiting > 0:
                response = self.ser.read(self.ser.in_waiting)
                self.log(f"[RX] {response.hex(' ')}")
                return response

        self.log("[RX] No response")
        return None

    def projector_on(self):
        self.send_command(CMD_BOOT_ON, "BOOT_ON")

    def projector_off(self):
        self.send_command(CMD_BOOT_OFF, "BOOT_OFF")

    def led_on(self):
        self.send_command(CMD_LED_ON, "LED_ON")

    def led_off(self):
        self.send_command(CMD_LED_OFF, "LED_OFF")

    def query_status(self):
        self.send_command(CMD_QUERY, "QUERY")

    def closeEvent(self, event):
        if self.ser and self.ser.is_open:
            self.ser.close()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = LEDControlGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
