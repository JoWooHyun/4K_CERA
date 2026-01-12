# 4K_CERA - VERICOM DF10 DLP 3D Printer GUI

VERICOM DLP 3D 프린터 (DF10 광원)를 위한 터치스크린 GUI 애플리케이션입니다.

> **Note**: 이 프로젝트는 [vgui](https://github.com/JoWooHyun/vgui) (NVR2+ 광원)를 기반으로 DF10 광원용으로 수정되었습니다.

---

## 중요: 해상도 설정

> **DF10 광원은 HDMI 입력으로 1920x1080 @ 60Hz를 사용합니다.**
>
> 4K DMD를 사용하지만, HDMI 입력은 반드시 1920x1080이어야 합니다.
> 제조사(안화광전) 확인: 4K 해상도로 직접 전송하면 안 됩니다.

| 항목 | 값 | 비고 |
|------|-----|------|
| **HDMI 입력 해상도** | 1920 x 1080 @ 60Hz | **필수** |
| DMD 출력 해상도 | 3840 x 2160 (4K) | 내부 스케일링 |
| 레이어 이미지 해상도 | 1920 x 1080 | HDMI 입력과 동일 |

---

## 주요 변경사항 (NVR2+ → DF10)

| 항목 | NVR2+ (vgui) | DF10 (4K_CERA) |
|------|--------------|----------------|
| 컨트롤러 | DLPC6421 | DLPC6540 |
| 통신 방식 | USB I2C (Cypress) | Serial UART (9600bps) |
| HDMI 입력 해상도 | 1920 x 1080 @ 60Hz | 1920 x 1080 @ 60Hz |
| DMD | 0.47" FHD | 0.47" 4K |
| LED | 내장 UV | Luminus CBM-25X-UV |
| 파장 | - | 385nm (DF10E) / 405nm (DF10Z) |

---

## DF10 광원 제어 방식

### Boot ON/OFF vs LED ON/OFF

```
프로그램 시작
    ↓
[Boot ON] ← 팬 시작, 프로젝터 초기화 (1회만 실행)
    ↓
┌─────────────────────────────────────┐
│  Exposure / Clean / Print 반복     │
│  → LED ON / OFF 만 제어            │
│  → Boot OFF 하지 않음!             │
└─────────────────────────────────────┘
    ↓
프로그램 종료
    ↓
[Boot OFF] ← 팬 정지 (종료 시에만 실행)
```

**중요**:
- `Boot ON`은 프로그램 시작 시 1회만 실행
- `Boot OFF`는 프로그램 종료 시에만 실행
- Exposure/Clean/Print 작업에서는 `LED ON/OFF`만 제어
- Boot OFF 후 바로 Boot ON 하면 응답 없음 문제 발생 가능

### HEX 명령어

| 기능 | 명령 (HEX) | 성공 응답 |
|------|-----------|----------|
| **Boot ON** (팬 시작) | `2A FA 0D` | `2A FA 00 0D` |
| **Boot OFF** (팬 정지) | `2A FB 0D` | `2A FB 00 0D` |
| **LED ON** | `2A 4B 0D` | `2A 4B 00 0D` |
| **LED OFF** | `2A 47 0D` | `2A 47 00 0D` |
| 상태 조회 | `2A 53 0D` | LED ON: `2A 4B 00 0D` / OFF: `2A 47 00 0D` |

### 시리얼 통신 설정

| 항목 | 값 |
|------|-----|
| Baud rate | 9600 |
| Data bits | 8 |
| Stop bit | 1 |
| Parity | None |
| Level | **3.3V TTL** |

**주의**: 5V 시스템 사용 시 레벨 시프터 필요

---

## 시스템 사양

| 항목 | 스펙 |
|------|------|
| 프레임워크 | PySide6 (Qt for Python) |
| GUI 해상도 | 1024 x 600 px |
| **프로젝터 출력 해상도** | **1920 x 1080 @ 60Hz** |
| 타겟 디바이스 | 7인치 HDMI Touch LCD |
| 보드 | CM4 + Manta M8P 2.0 |
| 프로젝터 | DF10 0.47 4K (DLPC6540) |
| 모터 제어 | Moonraker API (Klipper) |
| DLP 통신 | Serial UART (9600bps, 8N1, 3.3V TTL) |

---

## 설치 및 실행

### Raspberry Pi

```bash
# 저장소 클론
git clone https://github.com/JoWooHyun/4K_CERA.git
cd 4K_CERA

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 실행
python main.py --no-sim
```

### Windows (개발용)

```bash
git clone https://github.com/JoWooHyun/4K_CERA.git
cd 4K_CERA
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py --sim
```

### 실행 옵션

| 옵션 | 설명 |
|------|------|
| `--kiosk` | 키오스크 모드 (전체화면, 커서 숨김) |
| `--windowed` | 윈도우 모드 (개발용) |
| `--sim` | 시뮬레이션 모드 |
| `--no-sim` | 실제 하드웨어 모드 |

---

## 테스트 도구

### LED 제어 테스트 (CLI)

```bash
python test/test_led.py
```

### LED 제어 테스트 (GUI)

```bash
python test/test_led_gui.py
```

버튼으로 수동 제어:
- **Projector ON** → Boot ON (팬 시작)
- **LED ON** → LED 켜기
- **LED OFF** → LED 끄기
- **Projector OFF** → Boot OFF (팬 정지)

---

## 프로젝트 구조

```
4K_CERA/
├── main.py                     # 메인 진입점
├── test/                       # 테스트 도구
│   ├── test_led.py             # LED 테스트 (CLI)
│   └── test_led_gui.py         # LED 테스트 (GUI)
├── controllers/
│   ├── dlp_controller.py       # DF10 시리얼 통신
│   └── motor_controller.py     # Moonraker 모터 제어
├── windows/
│   └── projector_window.py     # 프로젝터 출력 (1920x1080)
├── workers/
│   └── print_worker.py         # 프린팅 시퀀스
└── pages/                      # GUI 페이지들
```

---

## ZIP 파일 형식

### 레이어 이미지 해상도

> **레이어 이미지는 1920 x 1080 해상도로 생성해야 합니다.**

```
print_file.zip
├── run.gcode             # 프린트 파라미터
├── preview.png           # 썸네일
├── preview_cropping.png  # 크롭된 썸네일
├── 1.png                 # 레이어 1 (1920x1080)
├── 2.png                 # 레이어 2 (1920x1080)
└── ...
```

### run.gcode 필수 설정

```gcode
;resolutionX:1920
;resolutionY:1080
;machineX:124.8
;machineY:70.2
;machineZ:80
```

---

## 알려진 문제

### Boot OFF 후 응답 없음

**현상**: Boot OFF 후 바로 다음 명령 시 응답 없음
**원인**: 광원 모듈 내부 상태 초기화 시간 필요
**해결**: 프로그램 종료 시에만 Boot OFF 호출 (현재 적용됨)

### Wayland 호환성

라즈베리파이 Wayland 환경에서 프로젝터 윈도우 관련 이슈가 있을 수 있습니다.
- `close()` 대신 `hide()` 사용
- 윈도우 재사용 패턴 적용됨

---

## 개발 가이드

### 다음 작업자를 위한 체크리스트

- [ ] HDMI 출력이 1920x1080 @ 60Hz인지 확인
- [ ] 시리얼 포트가 `/dev/ttyUSB0`로 잡히는지 확인
- [ ] Boot ON 후 팬이 돌아가는지 확인
- [ ] LED ON 시 실제로 불이 켜지는지 확인

### 디버깅

```bash
# 시리얼 포트 확인
ls /dev/ttyUSB*

# LED 테스트
python test/test_led.py

# 로그 확인
# [DLP] 프리픽스: 시리얼 통신
# [Projector] 프리픽스: 프로젝터 윈도우
# [System] 프리픽스: 시스템 초기화
```

---

## 참고 문서

- `DF10 Series Data Sheet D (EN).pdf` - 하드웨어 사양
- `WI-EL00069 (V07) 0.47 4K Control Interface Description.pdf` - 시리얼 명령어

---

## 관련 프로젝트

- [vgui](https://github.com/JoWooHyun/vgui) - NVR2+ 광원 버전 (원본)

## 라이선스

Private - VERICOM
