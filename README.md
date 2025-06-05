# Edge600 - 도파민 대충영어

## 소개
Edge600은 언어 학습을 위한 도파민 기반 학습 프로그램입니다.

## 시스템 요구사항
- Python 3.8 이상
- Windows 10/11, macOS 10.15 이상, 또는 Linux

## 설치 방법

### 1. 소스코드에서 실행
1. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

2. 프로그램 실행:
```bash
python Edge600-715.py
```

### 2. 실행 파일 빌드

#### 빌드 전 준비
1. PyInstaller 설치:
```bash
pip install pyinstaller
```

2. 필요한 패키지 설치:
```bash
pip install -r requirements.txt
```

#### 빌드 실행
빌드 스크립트를 사용하여 실행 파일을 생성합니다:

```bash
# 기본 빌드 (디렉토리 모드)
python build.py

# 이전 빌드 정리 후 빌드
python build.py --clean

# 단일 파일로 빌드
python build.py --onefile
```

#### 빌드 결과
- Windows: `dist/Edge600.exe` 또는 `dist/Edge600` 디렉토리
- macOS: `dist/Edge600.app`
- Linux: `dist/Edge600` 또는 `dist/Edge600` 디렉토리

## 프로그램 구조
- `Edge600-715.py`: 메인 프로그램 파일
- `Edge600.spec`: PyInstaller 스펙 파일
- `build.py`: 빌드 스크립트
- `assets/`: 이미지 및 아이콘 파일
- `audio/`: 오디오 파일
- `data/`: 데이터 파일

## 주요 기능
- 다국어 학습 지원
- TTS(Text-to-Speech) 기능
- 학습 통계 및 분석
- 사용자 설정 저장 및 불러오기

## 문제 해결

### 오디오 재생 문제
- Windows: DirectSound 드라이버 문제가 있을 경우 기본 드라이버로 전환됩니다.
- macOS: coreaudio 드라이버를 사용합니다.

### 리소스 파일 문제
- 리소스 파일을 찾을 수 없는 경우 로그 파일을 확인하세요.
- 로그 파일은 `logs` 디렉토리에 저장됩니다.

## 라이센스
이 프로그램은 개인 및 교육용으로만 사용할 수 있습니다. 