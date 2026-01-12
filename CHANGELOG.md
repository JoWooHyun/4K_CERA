# 4K_CERA 변경 이력 및 현재 진행 상황

## 현재 상태 (2026-01-12)

### 최신 개선사항

1. **Boot ON 후 초기화 대기 시간 증가**
   - 변경: `projector_on()` 메서드에서 0.5초 → 3초 대기
   - 이유: 광원 모듈 내부 초기화 시간 필요

2. **LED ON 전 Boot ON 자동 체크**
   - 변경: Boot OFF 상태에서 LED ON 시 자동으로 Boot ON 실행
   - 이유: 안전한 LED 제어를 위한 전제조건 확인

3. **Boot OFF 전 LED OFF 자동 체크**
   - 변경: LED ON 상태에서 Boot OFF 시 먼저 LED OFF 실행 후 0.5초 대기
   - 이유: 안전한 종료 시퀀스

### 해결된 문제

1. **Boot ON/OFF 로직 수정**
   - 문제: Exposure/Clean 작업 후 매번 Boot OFF → 두 번째 실행 시 응답 없음
   - 해결: 프로그램 시작 시 Boot ON 1회, 종료 시에만 Boot OFF
   - 작업 중에는 LED ON/OFF만 제어

2. **해상도 설정 통일 (1920x1080)**
   - DF10 광원은 HDMI 입력으로 1920x1080 @ 60Hz 사용 (4K 아님!)
   - `projector_window.py`: 1920x1080
   - `gcode_parser.py`: 기본값 1920x1080
   - 레이어 이미지도 1920x1080으로 생성해야 함

3. **시리얼 통신 인코딩 오류**
   - 문제: DF10에서 0xFA 등 바이트 응답 시 ASCII 디코딩 실패
   - 해결: `dlp_controller.py`에서 `latin-1` 폴백 디코딩 추가

4. **Wayland 호환성**
   - `close()` 대신 `hide()` 사용 (윈도우 재사용)

### 미해결 문제

1. **Boot OFF 후 응답 없음**
   - 현상: Boot OFF 직후 Boot ON 시 응답 없음
   - 원인: 광원 모듈 내부 초기화 시간 필요 (추정)
   - 현재 대응: Boot OFF는 프로그램 종료 시에만 호출

---

## 최신 변경사항 (2026-01-12)

### main.py
```python
# 프로그램 시작 시 Boot ON (1회만)
def _init_hardware(self):
    ...
    if not self.simulation:
        print("[System] DLP Boot ON (팬 시작)...")
        self.dlp.projector_on()

# Exposure/Clean 정지 시 - LED OFF만, Boot OFF 하지 않음
def _stop_exposure(self):
    self.dlp.led_off()
    # projector_off() 제거

# 프로그램 종료 시에만 Boot OFF
def closeEvent(self, event):
    if not self.simulation:
        self.dlp.led_off()
        self.dlp.projector_off()
```

### workers/print_worker.py
```python
# 프린트 시작 시 - Boot ON 호출 불필요 (이미 ON 상태)
# 프린트 종료 시 - LED OFF만, Boot OFF 하지 않음
def _cleanup(self):
    self._dlp_led_off()
    # projector_off() 제거
```

---

## Boot ON/OFF 제어 흐름

```
프로그램 시작 (_init_hardware)
    ↓
Boot ON (팬 시작) ← 1회만 실행
    ↓
┌─────────────────────────────────────┐
│                                     │
│  Exposure 시작 → LED ON             │
│  Exposure 정지 → LED OFF            │
│                                     │
│  Clean 시작 → LED ON                │
│  Clean 정지 → LED OFF               │
│                                     │
│  Print 시작 → LED ON/OFF 반복       │
│  Print 완료 → LED OFF               │
│                                     │
│  ※ Boot OFF 하지 않음!              │
│                                     │
└─────────────────────────────────────┘
    ↓
프로그램 종료 (closeEvent)
    ↓
Boot OFF (팬 정지)
```

---

## 해상도 설정

> **중요: 4K DMD를 사용하지만 HDMI 입력은 1920x1080이어야 합니다!**

| 파일 | 설정값 |
|------|--------|
| `windows/projector_window.py` | `PROJECTOR_WIDTH = 1920`, `PROJECTOR_HEIGHT = 1080` |
| `controllers/gcode_parser.py` | `resolutionX = 1920`, `resolutionY = 1080` |
| 레이어 이미지 | 1920 x 1080 px |

---

## 테스트 도구

### LED 제어 테스트

```bash
# CLI 테스트
python test/test_led.py

# GUI 테스트 (수동 버튼 제어)
python test/test_led_gui.py
```

### 체크리스트

- [ ] 프로그램 시작 시 팬이 돌아가는지 확인
- [ ] LED ON 시 실제로 불이 켜지는지 확인
- [ ] Exposure 2회 연속 동작 확인
- [ ] Clean 2회 연속 동작 확인
- [ ] 프로그램 종료 시 팬이 멈추는지 확인

---

## HEX 명령어 요약

| 기능 | 명령 | 성공 응답 |
|------|------|----------|
| Boot ON (팬 시작) | `2A FA 0D` | `2A FA 00 0D` |
| Boot OFF (팬 정지) | `2A FB 0D` | `2A FB 00 0D` |
| LED ON | `2A 4B 0D` | `2A 4B 00 0D` |
| LED OFF | `2A 47 0D` | `2A 47 00 0D` |
| 상태 조회 | `2A 53 0D` | `2A 4B 00 0D` (ON) / `2A 47 00 0D` (OFF) |

---

## 다음 작업자를 위한 가이드

1. **프로그램 실행 전**
   - HDMI 출력이 1920x1080 @ 60Hz인지 확인
   - 시리얼 포트 확인: `ls /dev/ttyUSB*`

2. **문제 발생 시**
   - `test/test_led_gui.py`로 수동 테스트
   - 로그 프리픽스: `[DLP]`, `[System]`, `[Projector]`

3. **주의사항**
   - Boot OFF 후 바로 Boot ON 하면 응답 없음
   - 레이어 이미지는 반드시 1920x1080으로 생성
