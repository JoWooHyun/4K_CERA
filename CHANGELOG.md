# 4K_CERA 변경 이력 및 현재 진행 상황

## 현재 상태 (2026-01-08)

### 해결된 문제

1. **시리얼 통신 인코딩 오류**
   - 문제: DF10에서 0xFA 등 바이트 응답 시 ASCII 디코딩 실패
   - 해결: `dlp_controller.py`에서 `latin-1` 폴백 디코딩 추가

2. **해상도 불일치**
   - 문제: 코드가 3840x2160(4K)으로 설정되어 있었으나, DF10 광원은 1920x1080 입력 필요
   - 해결: `projector_window.py` 해상도를 1920x1080으로 변경 (PDF 사양에 맞춤)

3. **Wayland 호환성 (부분 해결)**
   - 문제: 라즈베리파이에서 두 번째 clean/exposure 동작 시 Wayland fatal error 발생
   - 적용된 수정:
     - `close()` 대신 `hide()` 사용 (윈도우 재사용)
     - 프로젝터 상태 체크로 중복 명령 방지
     - xcb 플랫폼 강제 설정 제거 (vgui와 동일하게)

### 미해결 문제

1. **두 번째 동작 실패**
   - 현상: 첫 번째 clean/exposure는 정상 동작, 두 번째 시도 시 실패
   - 가능한 원인: Wayland 디스플레이 연결 문제 또는 시리얼 통신 상태
   - 테스트 필요: 해상도 수정 후 재테스트 필요

---

## 커밋 이력

### 2026-01-08
- `fix: DF10 광원 사양에 맞춰 해상도 1920x1080으로 변경`
  - PDF 문서 사양: HDMI input resolution 1920x1080 @ 60Hz
  - vgui와 동일한 구조로 단순화

### 이전 커밋
- `fix: 프로젝터 상태 체크 및 흰색 화면 크기 수정`
- `fix: vgui와 동일한 단순 프로젝터 윈도우로 변경`
- `fix: Wayland 호환성 및 시리얼 통신 안정성 개선`
- `fix: xcb 플랫폼 강제 설정 제거`
- `fix: 라즈베리파이 호환성 수정`

---

## 주요 변경 파일

### 1. `windows/projector_window.py`
```python
# 변경 전
PROJECTOR_WIDTH = 3840
PROJECTOR_HEIGHT = 2160

# 변경 후 (DF10 사양에 맞춤)
PROJECTOR_WIDTH = 1920
PROJECTOR_HEIGHT = 1080
```
- `apply_mask` 파라미터 제거 (vgui와 동일)
- `show_white_screen()` 단순화

### 2. `controllers/dlp_controller.py`
- 시리얼 응답 디코딩에 `latin-1` 폴백 추가
- 버퍼 클리어 추가 (`reset_input_buffer`, `reset_output_buffer`, `flush`)
- 프로젝터 ON/OFF 상태 체크로 중복 명령 방지

### 3. `main.py`
- 모든 `projector_window.close()` → `projector_window.hide()` 변경
- Wayland 호환성을 위한 윈도우 재사용 패턴 적용

---

## vgui와의 차이점

| 항목 | vgui (NVR2+) | 4K_CERA (DF10) |
|------|--------------|----------------|
| 해상도 | 1920x1080 | 1920x1080 (수정됨) |
| 통신 | USB I2C | Serial UART 9600bps |
| MASK 기능 | 없음 | 제거됨 |
| 프로젝터 윈도우 | 단순 | vgui와 동일하게 단순화됨 |

---

## 테스트 체크리스트

라즈베리파이에서 테스트 필요:

- [ ] Clean 1회 동작
- [ ] Clean 2회 연속 동작
- [ ] Exposure 1회 동작
- [ ] Exposure 2회 연속 동작
- [ ] LED ON/OFF Setting 페이지
- [ ] 전체 프린트 워크플로우

---

## 참고 문서

- `DF10 Series Data Sheet D (EN).pdf` - DF10 하드웨어 사양
- `WI-EL00069 (V07) 0.47 4K Control Interface Description.pdf` - 시리얼 명령어 프로토콜

### 중요 사양 (PDF에서 확인)

| 항목 | 값 |
|------|-----|
| HDMI 입력 해상도 | 1920x1080 @ 60Hz |
| 시리얼 통신 | 9600bps, 8N1 |
| LED 밝기 범위 | 91-1023 (PWM) |
| 프로젝터 ON 명령 | 0x2A 0xFA 0x0D |
| 프로젝터 OFF 명령 | 0x2A 0xFB 0x0D |
| LED ON 명령 | 0x2A 0x4B 0x0D |
| LED OFF 명령 | 0x2A 0x47 0x0D |

---

## 다음 작업자를 위한 가이드

1. **해상도 수정 후 테스트**
   - 출력 범위가 정상적으로 나오는지 확인
   - 두 번째 동작이 정상 작동하는지 확인

2. **문제 발생 시 확인사항**
   - 시리얼 포트 연결 상태: `ls /dev/ttyUSB*`
   - DLP 응답 확인: `python test_df10.py -i`
   - Wayland 환경 변수: `echo $XDG_SESSION_TYPE`

3. **디버깅**
   - 시리얼 통신 로그는 `[DLP]` 프리픽스로 출력됨
   - 프로젝터 윈도우 로그는 `[Projector]` 프리픽스로 출력됨
