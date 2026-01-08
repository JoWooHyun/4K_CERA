# 4K_CERA - VERICOM 4K DLP 3D Printer GUI

VERICOM 4K DLP 3D 프린터 (DF10 광원)를 위한 터치스크린 GUI 애플리케이션입니다.

> **Note**: 이 프로젝트는 [vgui](https://github.com/JoWooHyun/vgui) (NVR2+ 광원)를 기반으로 DF10 광원용으로 수정되었습니다.

## 주요 변경사항 (NVR2+ → DF10)

| 항목 | NVR2+ (vgui) | DF10 (4K_CERA) |
|------|--------------|----------------|
| 컨트롤러 | DLPC6421 | DLPC6540 |
| 통신 방식 | USB I2C (Cypress) | Serial UART (9600bps) |
| HDMI 입력 해상도 | 1920 x 1080 @ 60Hz | 1920 x 1080 @ 60Hz |
| DMD 출력 해상도 | 1920 x 1080 (FHD) | 3840 x 2160 (4K) |
| DMD | 0.47" FHD | 0.47" 4K |
| LED | 내장 UV | Luminus CBM-25X-UV |
| 파장 | - | 385nm (DF10E) / 405nm (DF10Z) |

## 시스템 사양

| 항목 | 스펙 |
|------|------|
| 프레임워크 | PySide6 (Qt for Python) |
| GUI 해상도 | 1024 x 600 px |
| HDMI 입력 해상도 | 1920 x 1080 @ 60Hz |
| DMD 출력 해상도 | 3840 x 2160 px (4K) |
| 타겟 디바이스 | 7인치 HDMI Touch LCD |
| 보드 | CM4 + Manta M8P 2.0 |
| 프로젝터 | DF10 0.47 4K (DLPC6540) |
| 모터 제어 | Moonraker API (Klipper) |
| DLP 통신 | Serial UART (9600bps, 8N1, 3.3V TTL) |
| 디자인 테마 | Navy (#1E3A5F) + Cyan (#06B6D4) |

## 프린터 특징

- **Top-Down 방식** DLP 프린터
- **Z축**: 빌드 플레이트 상하 이동
- **X축**: 블레이드 수평 이동 (레진 평탄화)
- **LED 노출**: DF10 모듈을 통한 UV LED 제어 (시리얼 통신)

## DF10 하드웨어 연결

### 시리얼 통신 핀아웃

| 핀 | 설명 |
|----|------|
| TX | DF10 → Host (3.3V TTL) |
| RX | Host → DF10 (3.3V TTL) |
| GND | 공통 그라운드 |

**주의**: 3.3V TTL 레벨입니다. 5V 시스템 사용 시 레벨 시프터 필요.

### 권장 USB-TTL 어댑터

- CH340 / CH341
- CP2102 / CP2104
- FT232RL / FT232RQ
- PL2303

## 프로젝트 구조

```
4K_CERA/
├── main.py                     # 메인 진입점, 윈도우 관리
├── test_df10.py                # DF10 시리얼 통신 테스트
├── components/                 # 재사용 UI 컴포넌트
│   ├── header.py               # 페이지 헤더
│   ├── icon_button.py          # 아이콘 버튼
│   ├── number_dial.py          # ±버튼 숫자 다이얼
│   └── numeric_keypad.py       # 터치 숫자 키패드
├── controllers/                # 하드웨어 컨트롤러
│   ├── motor_controller.py     # Moonraker 모터 제어
│   ├── dlp_controller.py       # DF10 DLP/LED 제어 (시리얼)
│   ├── gcode_parser.py         # ZIP/G-code 파싱
│   ├── settings_manager.py     # 설정 저장/로드
│   └── theme_manager.py        # 테마 관리
├── workers/                    # 백그라운드 워커
│   └── print_worker.py         # 프린팅 시퀀스 실행 (QThread)
├── windows/                    # 추가 윈도우
│   └── projector_window.py     # 프로젝터 출력 윈도우
├── pages/                      # GUI 페이지 (14개)
│   ├── main_page.py            # 메인 홈
│   ├── tool_page.py            # 도구 메뉴
│   ├── manual_page.py          # Z축/X축 수동 제어
│   ├── print_page.py           # 파일 목록
│   ├── file_preview_page.py    # 파일 미리보기 + 설정
│   ├── print_progress_page.py  # 프린트 진행 상황
│   ├── exposure_page.py        # LED 노출 테스트
│   ├── clean_page.py           # 트레이 클리닝
│   ├── system_page.py          # 시스템 설정
│   ├── setting_page.py         # LED/블레이드 설정
│   ├── theme_page.py           # 테마 선택
│   ├── device_info_page.py     # 장치 정보
│   ├── language_page.py        # 언어 설정
│   └── service_page.py         # 서비스 정보
├── styles/                     # 스타일 정의
│   ├── colors.py               # 컬러 팔레트 (동적 테마)
│   ├── fonts.py                # 폰트 설정
│   ├── icons.py                # SVG 아이콘
│   └── stylesheets.py          # Qt 스타일시트
└── utils/                      # 유틸리티
    ├── usb_monitor.py          # USB 모니터링
    ├── zip_handler.py          # ZIP 파일 처리
    └── time_formatter.py       # 시간 포맷팅
```

## 설치

### Raspberry Pi (실제 환경)

```bash
# 저장소 클론
git clone https://github.com/JoWooHyun/4K_CERA.git
cd 4K_CERA

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### Windows (개발 환경)

```bash
git clone https://github.com/JoWooHyun/4K_CERA.git
cd 4K_CERA
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 실행

### 실제 하드웨어 모드

```bash
python main.py
```

### 시뮬레이션 모드 (하드웨어 없이 테스트)

```bash
python main.py --sim
```

### DF10 시리얼 통신 테스트

```bash
# 자동 포트 검색
python test_df10.py

# 특정 포트 지정
python test_df10.py COM3

# 시뮬레이션 모드
python test_df10.py --sim

# 대화형 모드
python test_df10.py -i

# 사용 가능한 포트 목록
python test_df10.py --list
```

### 실행 옵션

| 옵션 | 설명 |
|------|------|
| `--kiosk` | 키오스크 모드 (전체화면, 커서 숨김) |
| `--windowed` | 윈도우 모드 (개발용) |
| `--sim` | 시뮬레이션 모드 |
| `--no-sim` | 실제 하드웨어 모드 |

## DF10 시리얼 명령어

### 문자열 명령어

| 명령어 | 설명 |
|--------|------|
| `CM+LEDE=1` | LED ON |
| `CM+LEDE=0` | LED OFF |
| `CM+LEDS=XXX` | 밝기 설정 (91-1023) |
| `CM+GTMP` | LED 온도 조회 |
| `CM+SPJF=X` | 화면 플립 (0-3) |

### HEX 명령어

| 명령어 | 설명 |
|--------|------|
| `0x2A 0xFA 0x0D` | 프로젝터 ON |
| `0x2A 0xFB 0x0D` | 프로젝터 OFF |
| `0x2A 0x47 0x0D` | LED OFF |
| `0x2A 0x4B 0x0D` | LED ON |

## 프린팅 워크플로우

1. **파일 선택**: USB에서 ZIP 파일 선택
2. **미리보기**: 썸네일, 레이어 수, 노출 시간 확인
3. **파라미터 설정**: 블레이드 속도, LED 파워 조절
4. **프린트 시작**: 자동 시퀀스 실행
   - Z축/X축 홈 이동
   - 레진 평탄화
   - 레이어별 노출 및 이동
5. **완료 또는 에러**: 자동 정리 (X축 홈 복귀)

## 에러 처리

### 이미지 로드 실패
- 3회 재시도 후 실패 시 프린트 자동 중지
- 에러 다이얼로그로 사용자 알림

### 모터 에러
- Z축/X축 이동 실패 시 프린트 자동 중지
- 안전을 위해 Z축은 현재 위치 유지

### DF10 시리얼 에러
- 연결 실패 시 자동 포트 재검색
- 타임아웃 발생 시 재시도

### 정지/에러 시 동작
1. LED OFF
2. 프로젝터 OFF
3. X축만 홈 복귀 (Z축 위치 유지)
4. 에러 다이얼로그 표시 (에러 시)
5. 메인 페이지로 이동

## ZIP 파일 형식

프린트 파일은 다음 구조의 ZIP 파일이어야 합니다:

```
print_file.zip
├── run.gcode             # 프린트 파라미터 (필수)
├── preview.png           # 썸네일 이미지 (필수)
├── preview_cropping.png  # 크롭된 썸네일 (필수)
├── 1.png                 # 레이어 1
├── 2.png                 # 레이어 2
├── ...
└── N.png                 # 레이어 N (연속된 숫자)
```

### ZIP 파일 검증 조건

| 조건 | 설명 | 실패 시 메시지 |
|------|------|----------------|
| run.gcode 존재 | 필수 파일 | "run.gcode 파일이 없습니다" |
| 머신 설정 일치 | 아래 5개 값 필수 | "지원하지 않는 프린터 파일입니다" |
| preview.png 존재 | 필수 파일 | "미리보기 이미지가 없습니다" |
| preview_cropping.png 존재 | 필수 파일 | "미리보기 이미지가 없습니다" |
| 레이어 이미지 연속 | 1.png, 2.png... 중간 빠짐 없이 | "레이어 이미지가 손상되었습니다" |

### 필수 머신 설정 (run.gcode 내)

```gcode
;resolutionX:3840
;resolutionY:2160
;machineX:124.8
;machineY:70.2
;machineZ:80
```

### run.gcode 파라미터 예시

```gcode
;totalLayer:100
;layerHeight:0.05
;normalExposureTime:3.0
;bottomLayerExposureTime:30.0
;bottomLayerCount:8
;normalLayerLiftHeight:5.0
;normalLayerLiftSpeed:65
;estimatedPrintTime:3600
;resolutionX:3840
;resolutionY:2160
;machineX:124.8
;machineY:70.2
;machineZ:80
```

## 온도 관리

DF10은 적절한 온도 관리가 필요합니다:

| 부품 | 권장 온도 | 경고 온도 |
|------|----------|----------|
| LED MCPCB | < 45°C | > 45°C |
| DMD 히트싱크 | < 30°C | > 30°C |

온도가 높을 경우:
- 팬 속도 증가 (`set_fan_speed()`)
- LED 밝기 감소
- 주변 환기 확인

## 개발 가이드

### 블레이드 속도 단위

- **UI 표시**: mm/s (10-100)
- **내부 저장**: mm/s × 50 = Gcode F-value
- **예시**: 30 mm/s → F1500

### 테마 시스템

- `ThemeManager` 싱글톤으로 테마 관리
- `Colors` 메타클래스로 동적 색상 변경
- `get_*_style()` 함수로 동적 스타일 적용
- `main.py`에서 다른 모듈 임포트 전 ThemeManager 초기화 (저장된 테마 적용)
- 테마 변경 시 `_rebuild_pages()`로 모든 페이지 새로 생성

### 새 개발자를 위한 테마 가이드

**중요**: 새로운 다이얼로그나 컴포넌트 추가 시:

1. 배경색은 `Colors.WHITE` 대신 `Colors.BG_PRIMARY` 사용
2. 정적 스타일시트 상수 대신 `get_*_style()` 동적 함수 사용
3. 인라인 스타일이 많은 경우 `_update_*_style()` 헬퍼 메서드 작성

```python
# 올바른 예:
self.setStyleSheet(f"""
    QDialog {{
        background-color: {Colors.BG_PRIMARY};  # 테마에 따라 변경됨
        ...
    }}
""")

# 잘못된 예:
self.setStyleSheet(f"""
    QDialog {{
        background-color: {Colors.WHITE};  # 항상 흰색 고정
        ...
    }}
""")
```

## 관련 프로젝트

- [vgui](https://github.com/JoWooHyun/vgui) - NVR2+ 광원 버전 (원본)

## 라이선스

Private - VERICOM
