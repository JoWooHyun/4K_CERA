"""
MASK 적용 도구
==============

슬라이서에서 생성한 ZIP 파일의 레이어 이미지에 MASK를 적용합니다.

사용법:
    python mask_applier.py <input.zip> <mask.bmp> [output.zip]
    python mask_applier.py --gui  # GUI 모드

예시:
    python mask_applier.py print_file.zip read.bmp
    python mask_applier.py print_file.zip read.bmp print_file_masked.zip
"""

import sys
import os
import zipfile
import tempfile
import shutil
import argparse
from pathlib import Path
from io import BytesIO

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QFileDialog, QProgressBar, QMessageBox,
        QGroupBox
    )
    from PySide6.QtCore import Qt, QThread, Signal
    from PySide6.QtGui import QPixmap
    PYSIDE6_AVAILABLE = True
except ImportError:
    PYSIDE6_AVAILABLE = False


class MaskApplier:
    """MASK 적용 클래스"""

    def __init__(self, mask_path: str):
        """
        Args:
            mask_path: MASK BMP 파일 경로
        """
        if not PIL_AVAILABLE:
            raise ImportError("Pillow 라이브러리가 필요합니다: pip install Pillow")

        self.mask_path = mask_path
        self.mask_image = None
        self._load_mask()

    def _load_mask(self):
        """MASK 이미지 로드"""
        if not os.path.exists(self.mask_path):
            raise FileNotFoundError(f"MASK 파일을 찾을 수 없습니다: {self.mask_path}")

        self.mask_image = Image.open(self.mask_path)

        # 그레이스케일이면 RGB로 변환
        if self.mask_image.mode == 'L':
            self.mask_image = self.mask_image.convert('RGB')
        elif self.mask_image.mode == 'P':
            self.mask_image = self.mask_image.convert('RGB')
        elif self.mask_image.mode == 'RGBA':
            self.mask_image = self.mask_image.convert('RGB')

        print(f"MASK 로드 완료: {self.mask_image.size[0]}x{self.mask_image.size[1]}")

    def apply_mask(self, layer_image: Image.Image) -> Image.Image:
        """
        레이어 이미지에 MASK 적용

        Args:
            layer_image: 원본 레이어 이미지

        Returns:
            MASK가 적용된 이미지
        """
        # 해상도 확인
        if layer_image.size != self.mask_image.size:
            print(f"  경고: 해상도 불일치 - 레이어({layer_image.size}) != MASK({self.mask_image.size})")
            # MASK를 레이어 크기로 리사이즈
            mask_resized = self.mask_image.resize(layer_image.size, Image.Resampling.NEAREST)
        else:
            mask_resized = self.mask_image

        # 레이어 이미지 모드 변환
        if layer_image.mode == 'L':
            layer_rgb = layer_image.convert('RGB')
        elif layer_image.mode == 'P':
            layer_rgb = layer_image.convert('RGB')
        elif layer_image.mode == 'RGBA':
            layer_rgb = layer_image.convert('RGB')
        else:
            layer_rgb = layer_image

        # MASK를 그레이스케일로 변환하여 알파 채널로 사용
        mask_gray = mask_resized.convert('L')

        # 검정 배경 생성
        result = Image.new('RGB', layer_image.size, (0, 0, 0))

        # MASK를 알파로 사용하여 합성
        # MASK의 흰색 부분 = 레이어 표시, 검정 부분 = 표시 안함
        result = Image.composite(layer_rgb, result, mask_gray)

        return result

    def process_zip(self, input_zip: str, output_zip: str = None,
                    progress_callback=None) -> str:
        """
        ZIP 파일의 모든 레이어에 MASK 적용

        Args:
            input_zip: 입력 ZIP 파일 경로
            output_zip: 출력 ZIP 파일 경로 (None이면 자동 생성)
            progress_callback: 진행률 콜백 함수 (current, total)

        Returns:
            출력 ZIP 파일 경로
        """
        if not os.path.exists(input_zip):
            raise FileNotFoundError(f"입력 파일을 찾을 수 없습니다: {input_zip}")

        # 출력 파일 경로 결정
        if output_zip is None:
            base_name = os.path.splitext(input_zip)[0]
            output_zip = f"{base_name}_masked.zip"

        # 임시 디렉토리에서 작업
        with tempfile.TemporaryDirectory() as temp_dir:
            # ZIP 압축 해제
            print(f"압축 해제 중: {input_zip}")
            with zipfile.ZipFile(input_zip, 'r') as zf:
                zf.extractall(temp_dir)

            # 레이어 이미지 찾기 (숫자.png 형식)
            layer_files = []
            for f in os.listdir(temp_dir):
                if f.endswith('.png'):
                    name = os.path.splitext(f)[0]
                    if name.isdigit():
                        layer_files.append((int(name), f))

            layer_files.sort(key=lambda x: x[0])
            total_layers = len(layer_files)
            print(f"레이어 수: {total_layers}")

            # 각 레이어에 MASK 적용
            for i, (layer_num, filename) in enumerate(layer_files):
                layer_path = os.path.join(temp_dir, filename)

                # 레이어 이미지 로드
                layer_img = Image.open(layer_path)

                # MASK 적용
                masked_img = self.apply_mask(layer_img)

                # 저장 (원본 덮어쓰기)
                masked_img.save(layer_path, 'PNG')

                # 진행률 콜백
                if progress_callback:
                    progress_callback(i + 1, total_layers)

                if (i + 1) % 100 == 0 or (i + 1) == total_layers:
                    print(f"  처리 중: {i + 1}/{total_layers}")

            # 새 ZIP 파일 생성
            print(f"압축 중: {output_zip}")
            with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zf.write(file_path, arcname)

        print(f"완료: {output_zip}")
        return output_zip


def apply_mask_to_single_image(layer_path: str, mask_path: str, output_path: str = None):
    """단일 이미지에 MASK 적용 (테스트용)"""
    applier = MaskApplier(mask_path)

    layer_img = Image.open(layer_path)
    masked_img = applier.apply_mask(layer_img)

    if output_path is None:
        base, ext = os.path.splitext(layer_path)
        output_path = f"{base}_masked{ext}"

    masked_img.save(output_path)
    print(f"저장됨: {output_path}")
    return output_path


# ============================================================
# GUI 모드
# ============================================================

if PYSIDE6_AVAILABLE:

    class MaskWorker(QThread):
        """MASK 적용 워커 스레드"""
        progress = Signal(int, int)  # current, total
        finished = Signal(str)  # output path
        error = Signal(str)  # error message

        def __init__(self, input_zip: str, mask_path: str, output_zip: str = None):
            super().__init__()
            self.input_zip = input_zip
            self.mask_path = mask_path
            self.output_zip = output_zip

        def run(self):
            try:
                applier = MaskApplier(self.mask_path)
                output = applier.process_zip(
                    self.input_zip,
                    self.output_zip,
                    progress_callback=lambda c, t: self.progress.emit(c, t)
                )
                self.finished.emit(output)
            except Exception as e:
                self.error.emit(str(e))


    class MaskApplierGUI(QMainWindow):
        """MASK 적용 도구 GUI"""

        def __init__(self):
            super().__init__()
            self.setWindowTitle("MASK 적용 도구")
            self.setFixedSize(500, 350)

            self.input_zip = ""
            self.mask_file = ""
            self.worker = None

            self._setup_ui()

        def _setup_ui(self):
            central = QWidget()
            self.setCentralWidget(central)
            layout = QVBoxLayout(central)
            layout.setSpacing(15)
            layout.setContentsMargins(20, 20, 20, 20)

            # 입력 파일 선택
            input_group = QGroupBox("1. 입력 ZIP 파일")
            input_layout = QHBoxLayout(input_group)
            self.input_label = QLabel("선택되지 않음")
            self.input_label.setStyleSheet("color: gray;")
            input_btn = QPushButton("파일 선택...")
            input_btn.clicked.connect(self._select_input)
            input_layout.addWidget(self.input_label, 1)
            input_layout.addWidget(input_btn)
            layout.addWidget(input_group)

            # MASK 파일 선택
            mask_group = QGroupBox("2. MASK 파일 (BMP)")
            mask_layout = QHBoxLayout(mask_group)
            self.mask_label = QLabel("선택되지 않음")
            self.mask_label.setStyleSheet("color: gray;")
            mask_btn = QPushButton("파일 선택...")
            mask_btn.clicked.connect(self._select_mask)
            mask_layout.addWidget(self.mask_label, 1)
            mask_layout.addWidget(mask_btn)
            layout.addWidget(mask_group)

            # 진행 상황
            progress_group = QGroupBox("3. 진행 상황")
            progress_layout = QVBoxLayout(progress_group)
            self.progress_bar = QProgressBar()
            self.progress_bar.setValue(0)
            self.progress_label = QLabel("대기 중...")
            progress_layout.addWidget(self.progress_bar)
            progress_layout.addWidget(self.progress_label)
            layout.addWidget(progress_group)

            # 실행 버튼
            self.run_btn = QPushButton("MASK 적용 시작")
            self.run_btn.setFixedHeight(50)
            self.run_btn.setStyleSheet("""
                QPushButton {
                    background-color: #06B6D4;
                    color: white;
                    font-size: 16px;
                    font-weight: bold;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #0891B2;
                }
                QPushButton:disabled {
                    background-color: #9CA3AF;
                }
            """)
            self.run_btn.clicked.connect(self._start_processing)
            layout.addWidget(self.run_btn)

        def _select_input(self):
            path, _ = QFileDialog.getOpenFileName(
                self, "입력 ZIP 파일 선택", "", "ZIP Files (*.zip)"
            )
            if path:
                self.input_zip = path
                self.input_label.setText(os.path.basename(path))
                self.input_label.setStyleSheet("color: black;")

        def _select_mask(self):
            path, _ = QFileDialog.getOpenFileName(
                self, "MASK 파일 선택", "", "BMP Files (*.bmp)"
            )
            if path:
                self.mask_file = path
                self.mask_label.setText(os.path.basename(path))
                self.mask_label.setStyleSheet("color: black;")

        def _start_processing(self):
            if not self.input_zip:
                QMessageBox.warning(self, "경고", "입력 ZIP 파일을 선택하세요.")
                return
            if not self.mask_file:
                QMessageBox.warning(self, "경고", "MASK 파일을 선택하세요.")
                return

            self.run_btn.setEnabled(False)
            self.progress_bar.setValue(0)
            self.progress_label.setText("처리 중...")

            self.worker = MaskWorker(self.input_zip, self.mask_file)
            self.worker.progress.connect(self._on_progress)
            self.worker.finished.connect(self._on_finished)
            self.worker.error.connect(self._on_error)
            self.worker.start()

        def _on_progress(self, current, total):
            percent = int(current / total * 100)
            self.progress_bar.setValue(percent)
            self.progress_label.setText(f"처리 중: {current}/{total} 레이어")

        def _on_finished(self, output_path):
            self.run_btn.setEnabled(True)
            self.progress_label.setText("완료!")
            QMessageBox.information(
                self, "완료",
                f"MASK 적용이 완료되었습니다.\n\n출력 파일:\n{output_path}"
            )

        def _on_error(self, error_msg):
            self.run_btn.setEnabled(True)
            self.progress_label.setText("오류 발생")
            QMessageBox.critical(self, "오류", f"처리 중 오류가 발생했습니다:\n{error_msg}")


def run_gui():
    """GUI 모드 실행"""
    if not PYSIDE6_AVAILABLE:
        print("오류: PySide6가 설치되어 있지 않습니다.")
        print("설치: pip install PySide6")
        sys.exit(1)

    app = QApplication(sys.argv)
    window = MaskApplierGUI()
    window.show()
    sys.exit(app.exec())


def main():
    parser = argparse.ArgumentParser(
        description='MASK 적용 도구 - ZIP 파일의 레이어 이미지에 MASK를 적용합니다.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  %(prog)s print_file.zip read.bmp
  %(prog)s print_file.zip read.bmp output.zip
  %(prog)s --gui
  %(prog)s --single layer.png read.bmp
        """
    )
    parser.add_argument('input_zip', nargs='?', help='입력 ZIP 파일')
    parser.add_argument('mask_bmp', nargs='?', help='MASK BMP 파일')
    parser.add_argument('output_zip', nargs='?', help='출력 ZIP 파일 (선택사항)')
    parser.add_argument('--gui', action='store_true', help='GUI 모드로 실행')
    parser.add_argument('--single', metavar='IMAGE', help='단일 이미지에 MASK 적용')

    args = parser.parse_args()

    # PIL 확인
    if not PIL_AVAILABLE:
        print("오류: Pillow 라이브러리가 필요합니다.")
        print("설치: pip install Pillow")
        sys.exit(1)

    # GUI 모드
    if args.gui:
        run_gui()
        return

    # 단일 이미지 모드
    if args.single:
        if not args.mask_bmp:
            print("오류: MASK 파일을 지정하세요.")
            sys.exit(1)
        apply_mask_to_single_image(args.single, args.mask_bmp)
        return

    # ZIP 처리 모드
    if not args.input_zip or not args.mask_bmp:
        parser.print_help()
        sys.exit(1)

    applier = MaskApplier(args.mask_bmp)
    applier.process_zip(args.input_zip, args.output_zip)


if __name__ == "__main__":
    main()
