import os
import platform
import logging
import traceback
import signal
### 인트로 3순위 언어별 썸내일 선택
### 힐링
# pygame을 임포트하기 전에 환경 변수 설정
if platform.system() == "Darwin":
    # macOS에서는 coreaudio 드라이버를 기본으로 사용하고, 앱 번들에서도 작동하도록 설정
    os.environ["SDL_AUDIODRIVER"] = "coreaudio"
    # 오디오 디바이스 설정
    os.environ["AUDIODEV"] = "1"

# 환경 변수 설정이 완료된 후 pygame 임포트
import pygame
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
os.environ['SDL_VIDEODRIVER'] = 'dummy'

# 다른 오디오 라이브러리 미리 임포트
import threading
import sys
import json
import time
import platform  # platform 모듈을 먼저 임포트

# 시스템 정보 로깅 추가
system_info = f"운영체제: {platform.system()} {platform.release()}, Python: {sys.version.split()[0]}"
print(f"시스템 정보: {system_info}")

from pathlib import Path  # Path도 여기서 임포트

# 리소스 경로 처리 함수 추가
def resource_path(relative_path):
    """리소스 파일의 절대 경로를 반환합니다."""
    try:
        # 경로 객체로 변환 (문자열인 경우 Path로 변환)
        if isinstance(relative_path, str):
            relative_path = Path(relative_path)

        # 기본 리소스 경로
        base_path = SCRIPT_DIR / "resources"
        
        # 만약 relative_path가 'resources' + os.sep로 시작하면 직접 사용
        if str(relative_path).startswith('resources' + os.sep):
            final_path = SCRIPT_DIR / relative_path
        else:
            file_mappings = {
                '.xlsx': 'data',
                '.ico': 'images',
                '.png': 'images',
                '.jpg': 'images',
                '.jpeg': 'images',
                '.otf': 'font',
                '.wav': 'audio'
            }
            ext = relative_path.suffix.lower()
            if ext in file_mappings:
                final_path = base_path / file_mappings[ext] / relative_path.name
            else:
                final_path = base_path / relative_path
        
        final_path = final_path.resolve(strict=False)
        logging.debug(f"resource_path: {relative_path} -> {final_path}")
        if final_path.exists():
            return final_path.resolve(strict=False)
        
        # PyInstaller로 패키징된 경우
        if getattr(sys, 'frozen', False):
            try:
                base_path = Path(sys._MEIPASS) / "resources"
                full_path = base_path / relative_path
                if full_path.exists():
                    return full_path.resolve(strict=False)
            except Exception:
                pass
                
        # 리소스를 찾지 못한 경우 로깅
        logging.warning(f"리소스 파일을 찾을 수 없음: {relative_path}")
        return final_path.resolve(strict=False)
        
    except Exception as e:
        logging.error(f"리소스 경로 처리 중 오류 발생: {e}")
        traceback.print_exc()
        return (SCRIPT_DIR / relative_path).resolve(strict=False)

def get_words_from_excel(start_row, end_row):
    """엑셀에서 문장 가져오기"""
    try:
        start_row = int(start_row)
        end_row = int(end_row)
        import pandas as pd
        df = pd.read_excel(EXCEL_PATH, header=0)
        start_idx = start_row - 1
        end_idx = end_row - 1
        english = df.iloc[start_idx:end_idx+1, 0].tolist()
        korean = df.iloc[start_idx:end_idx+1, 1].tolist()
        chinese = df.iloc[start_idx:end_idx+1, 2].tolist()
        vietnamese = df.iloc[start_idx:end_idx+1, 3].tolist() if df.shape[1] > 3 else []
        japanese = df.iloc[start_idx:end_idx+1, 4].tolist() if df.shape[1] > 4 else []
        nepali = df.iloc[start_idx:end_idx+1, 5].tolist() if df.shape[1] > 5 else []
        english = [str(item).strip() if item is not None and not pd.isna(item) else "" for item in english]
        korean = [str(item).strip() if item is not None and not pd.isna(item) else "" for item in korean]
        chinese = [str(item).strip() if item is not None and not pd.isna(item) else "" for item in chinese]
        vietnamese = [str(item).strip() if item is not None and not pd.isna(item) else "" for item in vietnamese]
        japanese = [str(item).strip() if item is not None and not pd.isna(item) else "" for item in japanese]
        nepali = [str(item).strip() if item is not None and not pd.isna(item) else "" for item in nepali]
        max_len = max(len(english), len(korean), len(chinese), len(vietnamese), len(japanese), len(nepali))
        english += [""] * (max_len - len(english))
        korean += [""] * (max_len - len(korean))
        chinese += [""] * (max_len - len(chinese))
        vietnamese += [""] * (max_len - len(vietnamese))
        japanese += [""] * (max_len - len(japanese))
        nepali += [""] * (max_len - len(nepali))
        return english, korean, chinese, vietnamese, japanese, nepali
    except Exception as e:
        print("엑셀 파일 읽기 오류:", e)
        return [], [], [], [], [], []

# 전역 변수 선언 및 초기화
root = None
current_frame = None
subtitle_labels = []
SCRIPT_DIR = Path(__file__).parent.absolute()
print(f"스크립트 경로: {SCRIPT_DIR}")

# 언어 코드 매핑을 전역 상수로 정의
LANGUAGE_CODES = {
    'korean': 'ko', 
    'english': 'en', 
    'chinese': 'zh', 
    'japanese': 'jp', 
    'vietnamese': 'vn', 
    'nepali': 'ne'
}

import edge_tts
import asyncio
import threading
import tkinter as tk
from tkinter import ttk, filedialog
import pygame
import wave
import soundfile as sf
from PIL import Image, ImageFont, ImageTk
import subprocess
import pandas as pd
# import traceback  # 상단에서 이미 임포트함
import sounddevice as sd
import pyrubberband as pyrb
from tkinter import messagebox
import io
import numpy as np
import numpy  # 볼륨 처리를 위해 numpy 추가 임포트

# PyGame 초기화 (스크립트 상단에 추가)
try:
    pygame.mixer.quit()  # 기존 인스턴스가 있으면 정리
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
    pygame.init()
    print("PyGame 초기화 성공")
except Exception as e:
    print(f"PyGame 초기화 오류(무시됨): {e}")
    try:
        pygame.mixer.init(44100, -16, 2, 2048)
        pygame.init()
        print("PyGame 재초기화 성공")
    except:
        print("PyGame 초기화 실패 - 오디오 재생에 문제가 있을 수 있습니다")

# 로깅 설정
log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'edge600.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# 맥북 관련 설정 추가
if platform.system() == 'Darwin':  # macOS인 경우
    FONT_COUNTDOWN = ("AppleSDGothicNeo", 400, "bold")
    FONT_MESSAGE = ("AppleSDGothicNeo", 40, "bold") 
    FONT_SUBTITLE = ("AppleSDGothicNeo", 55, "bold")
    FONT_PROGRESS = ("AppleSDGothicNeo", 30, "bold")
    FONT_BREAK = ("AppleSDGothicNeo", 160, "bold")
    FONT_TITLE = ("AppleSDGothicNeo", 36, "bold")
else:  # 기존 Windows 폰트 유지
    FONT_COUNTDOWN = ("Helvetica", 400, "bold")
    FONT_MESSAGE = ("Helvetica", 40, "bold")
    FONT_SUBTITLE = ("AppleSDGothicNeo", 55, "bold")
    FONT_PROGRESS = ("AppleSDGothicNeo", 30, "bold") 
    FONT_BREAK = ("Helvetica", 160, "bold")
    FONT_TITLE = ("Helvetica", 36, "bold")

# 맥북 경로 처리
if platform.system() == 'Darwin':
    SCRIPT_DIR = Path(__file__).parent.resolve()
else:
    SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))

# 리소스 파일 경로 설정 (resource_path 함수 사용)
SETTINGS_PATH = Path(resource_path('settings.json'))
EXCEL_PATH = Path(resource_path('resources/data/en600new.xlsx'))
FONT_PATH = Path(resource_path("resources/fonts/Pretendard-Bold.otf"))

# 색상 설정
COLORS = {
    'background': 'gray3',  # 다크모드 배경
    'text': '#0CF615',     # 기본 텍스트 (초록색)
    'highlight': '#FFFFF0', # 음성 재생 시 (아이보리)
    'progress': '#C3EAFA', # 진행 표시
    'white': '#FFFFFF',    # 흰색 (카운트다운 숫자용)
    'pink': '#FF69B4'      # 핑크 (타이핑 메시지용)
}

# 음성 매핑 설정 수정
VOICE_MAPPING = {
    'english': {
        "Steffan": "en-US-SteffanNeural",
        "Ava": "en-US-AvaNeural",
        "Guy": "en-US-GuyNeural",
        "Emma": "en-US-EmmaNeural",
        "Jenny": "en-US-JennyNeural",
        # 유럽 영어 음성 추가
        "Sonia (UK)": "en-GB-SoniaNeural",
        "Ryan (UK)": "en-GB-RyanNeural",
        "Libby (UK)": "en-GB-LibbyNeural",
        "Thomas (UK)": "en-GB-ThomasNeural",
        "Alfie (UK)": "en-GB-AlfieNeural",
        "Clara (IE)": "en-IE-EmilyNeural",
        "Connor (IE)": "en-IE-ConnorNeural",
        # 인도 영어 음성 추가
        "Neerja (IN)": "en-IN-NeerjaNeural",
        "Prabhat (IN)": "en-IN-PrabhatNeural",
        # 싱가폴 영어 음성 추가
        "Wayne (SG)": "en-SG-WayneNeural",
        "Luna (SG)": "en-SG-LunaNeural",
        # 호주 영어 음성 추가
        "Natasha (AU)": "en-AU-NatashaNeural",
        "William (AU)": "en-AU-WilliamNeural",
        # 홍콩 영어 음성 추가
        "Sam (HK)": "en-HK-SamNeural",
        "Yan (HK)": "en-HK-YanNeural",
        # 캐나다 영어 음성 추가
        "Clara (CA)": "en-CA-ClaraNeural",
        "Liam (CA)": "en-CA-LiamNeural"
    },
    'korean': {
        'SunHi': 'ko-KR-SunHiNeural',      # TTS용 전체 이름으로 변경
        'InJoon': 'ko-KR-InJoonNeural',
        'Hyunsu': 'ko-KR-HyunsuMultilingualNeural'
    },
    'chinese': {
        'Xiaoxiao': 'zh-CN-XiaoxiaoNeural',
        'HsiaoChen': 'zh-TW-HsiaoChenNeural',
        'Yunjian': 'zh-CN-YunjianNeural',
        'Xiaoyi': 'zh-CN-XiaoyiNeural',  # 수정: Xisoyi → Xiaoyi
        'Yunxi': 'zh-CN-YunxiNeural',
        'Yunyang': 'zh-CN-YunyangNeural'
    },
    'japanese': {
        'Nanami': 'ja-JP-NanamiNeural',
        'Keita': 'ja-JP-KeitaNeural',
        'Naoki': 'ja-JP-NaokiNeural',
    },
    'vietnamese': {
        'HoaiMy': 'vi-VN-HoaiMyNeural',    # 여성 음성
        'NamMinh': 'vi-VN-NamMinhNeural',   # 남성 음성
        'Natural': 'vi-VN-HoaiMyNeural'     # 자연스러운 음성
    },
    'nepali': {
        'Sagar': 'ne-NP-SagarNeural',  # 네팔어 음성
        'Hemkala': 'ne-NP-HemkalaNeural'  # 네팔어 추가 음성
    }
}

# Add after VOICE_MAPPING = {...} section
voice_mapping = {
    'Steffan': 'en-US-SteffanNeural',
    'Jenny': 'en-US-JennyNeural',
    'Ava': 'en-US-AvaNeural',
    'Guy': 'en-US-GuyNeural',
    'Emma': 'en-US-EmmaNeural',
    # 유럽 영어 음성 추가
    'Sonia (UK)': 'en-GB-SoniaNeural',
    'Ryan (UK)': 'en-GB-RyanNeural',
    'Libby (UK)': 'en-GB-LibbyNeural',
    'Thomas (UK)': 'en-GB-ThomasNeural',
    'Alfie (UK)': 'en-GB-AlfieNeural',
    'Clara (IE)': 'en-IE-EmilyNeural',
    'Connor (IE)': 'en-IE-ConnorNeural',
    # 인도 영어 음성 추가
    'Neerja (IN)': 'en-IN-NeerjaNeural',
    'Prabhat (IN)': 'en-IN-PrabhatNeural',
    # 싱가폴 영어 음성 추가
    'Wayne (SG)': 'en-SG-WayneNeural',
    'Luna (SG)': 'en-SG-LunaNeural',
    # 호주 영어 음성 추가
    'Natasha (AU)': 'en-AU-NatashaNeural',
    'William (AU)': 'en-AU-WilliamNeural',
    # 홍콩 영어 음성 추가
    'Sam (HK)': 'en-HK-SamNeural',
    'Yan (HK)': 'en-HK-YanNeural',
    # 캐나다 영어 음성 추가
    'Clara (CA)': 'en-CA-ClaraNeural',
    'Liam (CA)': 'en-CA-LiamNeural',
    
    'SunHi': 'ko-KR-SunHiNeural',
    'InJoon': 'ko-KR-InJoonNeural',
    'Hyunsu': 'ko-KR-HyunsuMultilingualNeural',
    'Xiaoxiao': 'zh-CN-XiaoxiaoNeural',
    'Yunxi': 'zh-CN-YunxiNeural',
    'Yunyang': 'zh-CN-YunyangNeural',
    'HsiaoChen': 'zh-TW-HsiaoChenNeural',  # 대만 중국어 음성 추가
    'Yunjian': 'zh-CN-YunjianNeural',      # 추가 중국어 음성
    'Xiaoyi': 'zh-CN-XiaoyiNeural',        # 추가 중국어 음성 (맞춤법 수정)
    'Nanami': 'ja-JP-NanamiNeural',
    'Keita': 'ja-JP-KeitaNeural',
    'Naoki': 'ja-JP-NaokiNeural',
    'HoaiMy': 'vi-VN-HoaiMyNeural',    # 베트남어 여성
    'NamMinh': 'vi-VN-NamMinhNeural',   # 베트남어 남성
    'Natural': 'vi-VN-HoaiMyNeural',     # 베트남어 자연스러운 음성
    'Sagar': 'ne-NP-SagarNeural',  # 네팔어 음성
    'Hemkala': 'ne-NP-HemkalaNeural'  # 네팔어 추가 음성
}

# 기본 설정값
DEFAULT_SETTINGS = {
    'first_lang': 'english',
    'second_lang': 'korean',
    'third_lang': 'chinese',
    'first_repeat': '0',
    'second_repeat': '1',
    'third_repeat': '0',
    'kor_voice': 'SunHi',
    'eng_voice': 'Steffan',
    'zh_voice': 'Xiaoxiao',
    'jp_voice': 'Nanami',  # 추가
    'vn_voice': 'HoaiMy',  # 기본 여성 음성을 HoaiMy로 변경
    'ne_voice': 'Sagar',  # 네팔어 기본 음성
    'start_row': 1,
    'end_row': 10,
    'word_delay': '0.1',
    'spacing': '0.5',  # 0.1에서 0.5로 변경
    'english_speed': '2',  # 기본값 2.0으로 변경
    'korean_speed': '2',   # 기본값 2.0으로 변경 
    'chinese_speed': '2',  # 기본값 2.0으로 변경
    'japanese_speed': '2', # 기본값 2.0으로 변경
    'vietnamese_speed': '2', # 기본값 2.0으로 변경
    'nepali_speed': '2',   # 기본값 2.0으로 변경
    'keep_subtitles': 'true',
    'break_enabled': 'false',  # 기본값을 false로 변경
    'break_interval': '없음',   # 기본값을 '없음'으로 변경
    'break_duration': '5',
    'next_sentence_time': '0.5',
    'eng_voice_type': 'WAV',  # 기본 음성은 WAV
    'kor_voice_type': 'WAV',
    'zh_voice_type': 'WAV',
    'jp_voice_type': 'WAV',  # 추가
    'vn_voice_type': 'WAV',  # gTTS에서 WAV로 변경
    'ne_voice_type': 'TTS',  # 네팔어 기본 음성 타입
    'final_music': '없음',
    'auto_repeat': '0',      # 기본값을 0으로 변경
    'auto_repeat_enabled': 'false',  # 이 설정은 더 이상 사용하지 않음
    'save_tts': 'false',  # TTS 저장 옵션
    'tts_save_path': str(SCRIPT_DIR / 'tts_output'),  # 기본 저장 경로
}

# 힐링뮤직 시간 매핑 추가
FINAL_MUSIC_DURATION = {
    '없음': 0,
    '1분': 60,    # 60초
    '2분': 120,   # 120초 
    '3분': 180    # 180초
}

# 언어 설정
LANGUAGES = ['english', 'korean', 'chinese', 'japanese', 'vietnamese', 'nepali', 'none']
LANG_DISPLAY = {
    'english': '영어', 
    'korean': '한국어', 
    'chinese': '중국어',
    'japanese': '일본어',
    'vietnamese': '베트남어',
    'nepali': '네팔어',  # 새 항목 추가
    'none': '없음'
}

# 전역 변수 초기화
root = None
main_window = None
current_frame = None
countdown_logo_image = None  # FLAC 로고 이미지 (카운트다운 화면용)
learning_logo_image = None   # FLAC 로고 이미지 (학습화면용)
flac_logo_image = None       # FLAC 로고 이미지 (우측 상단용)
lesson_start_time = 0        # 학습 시작 시간 전역 변수 추가
lesson_running = False       # 학습 실행 상태 전역 변수

# UI 요소 전역 변수
start_entry = None
end_entry = None
first_lang_cb = None
second_lang_cb = None
third_lang_cb = None
first_repeat = None
second_repeat = None
third_repeat = None
eng_voice_cb = None
kor_voice_cb = None
zh_voice_cb = None
jp_voice_cb = None  # 추가
vn_voice_cb = None  # 베트남어 추가
ne_voice_cb = None  # 네팔어 추가
eng_speed = None
kor_speed = None
zh_speed = None
jp_speed = None  # 추가
vn_speed = None  # 베트남어 추가
ne_speed = None  # 네팔어 추가
spacing_entry = None
next_sentence_entry = None
break_var = None
break_interval = None
progress_label = None
subtitle_labels = []
countdown_label = None
message_label = None
keep_subtitles_var = None
eng_voice_type = None
kor_voice_type = None
zh_voice_type = None
jp_voice_type = None  # 추가
vn_voice_type = None  # 추가
ne_voice_type = None  # 네팔어 추가
auto_repeat_var = None  # 추가
auto_repeat_enabled_var = None  # 추가 (함수 외부로 이동)

# UI 스타일 설정
# STYLE 딕셔너리는 UI 컴포넌트들의 시각적 스타일을 정의합니다.
STYLE = {
    # 프레임 스타일 (모든 컨테이너의 기본 스타일)
    # 예시: tk.Frame(root, **STYLE['frame'])
    'frame': {
        'bg': COLORS['background'],  # 배경색: 다크 모드 (#1e1e1e)
        'padx': 10,  # 좌우 여백
        'pady': 5    # 상하 여백
    },
    
    # 일반 레이블 스타일 (기본 텍스트 표시용)
    # 예시: tk.Label(frame, text="설정", **STYLE['label'])
    'label': {
        'font': ("Helvetica", 24, "bold"),  # 폰트: Helvetica 24pt 굵게
        'bg': COLORS['background'],  # 배경색: 다크 모드
        'fg': COLORS['text']         # 텍스트 색상: 초록색 (#4CAF50)
    },
    
    # 통계 화면 레이블 스타일 (학습 완료 후 통계 표시용)
    # 예시: tk.Label(stats_frame, text="총 학습 시간", **STYLE['stats_label'])
    'stats_label': {
        'font': ("Helvetica", 36, "bold"),  # 폰트: Helvetica 36pt 굵게
        'bg': COLORS['background'],  # 배경색: 다크 모드
        'fg': COLORS['text']         # 텍스트 색상: 초록색
    },
    
    # 입력 필드 스타일 (숫자 입력용)
    # 예시: tk.Entry(frame, **STYLE['entry'])
    'entry': {
        'font': ("Helvetica", 24),   # 폰트: Helvetica 24pt
        'width': 5                   # 입력 필드 너비: 5문자
    },
    
    # 콤보박스 스타일 (드롭다운 선택용)
    # 예시: ttk.Combobox(frame, **STYLE['combobox'])
    'combobox': {
        'font': ("Helvetica", 20)    # 폰트: Helvetica 20pt
    },
    
    # 버튼 스타일 (클릭 가능한 모든 버튼용)
    # 예시: tk.Button(frame, text="시작", **STYLE['button'])
    'button': {
        'font': ("Helvetica", 24, "bold"),  # 폰트: Helvetica 24pt 굵게
        'bg': COLORS['text'],        # 배경색: 초록색
        'fg': COLORS['background'],  # 텍스트 색상: 다크 모드 색상
        'padx': 20,                  # 버튼 좌우 패딩
        'pady': 10,                  # 버튼 상하 패딩
        'cursor': 'hand2'            # 마우스 오버시 손가락 커서
    }
}

# 초기화면 버튼 스타일 설정
HOME_BUTTON_STYLE = {
    'font': ("AppleSDGothicNeo", 24, "bold"),  # 폰트 크기 조정
    'bg': COLORS['highlight'],                # 독립적인 배경색
    'fg': COLORS['background'],               # 텍스트 색상 반전
    'activebackground': COLORS['highlight'],  # 클릭 시 배경색 유지
    'activeforeground': COLORS['background'],
    'bd': 2,                                  # 테두리 두께 추가
    'relief': 'groove',                       # 입체감 있는 테두리
    'cursor': 'hand2',
    'padx': 15,                               # 좌우 패딩 추가
    'pady': 8,                                # 상하 패딩 추가
    'highlightthickness': 0
}

# Add to global variables section at the top
eng_voice_type = None
kor_voice_type = None
zh_voice_type = None
jp_voice_type = None
vn_voice_type = None
ne_voice_type = None

def save_settings(settings):
    """설정값을 파일에 저장"""
    try:
        # TTS 저장 경로가 없으면 기본값 설정
        if 'tts_save_path' not in settings:
            settings['tts_save_path'] = str(SCRIPT_DIR / 'tts_output')
            
        # 볼륨 설정이 누락된 경우 기본값 설정
        if 'first_priority_volume' not in settings:
            settings['first_priority_volume'] = '100'
        if 'second_priority_volume' not in settings:
            settings['second_priority_volume'] = '100'
        if 'third_priority_volume' not in settings:
            settings['third_priority_volume'] = '100'
            
        # 파이널 뮤직 설정 저장 - UI 요소가 존재할 때만 접근하도록 수정
        try:
            if 'final_music_cb' in globals() and final_music_cb.winfo_exists():
                settings['final_music'] = final_music_cb.get()
        except (NameError, tk.TclError) as e:
            # UI 요소가 존재하지 않을 경우 기존 설정 유지
            print(f"파이널 뮤직 설정 읽기 중 오류 (무시됨): {e}")
        
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        print("\n=== 학습 설정 저장됨 ===")
        for key, value in settings.items():
            if key.endswith('_volume'):
                print(f"{key}: {value}%")
            else:
                print(f"{key}: {value}")
        print("=====================\n")
    except Exception as e:
        print(f"설정 저장 오류: {e}")
        traceback.print_exc()

def load_settings():
    """저장된 설정값 불러오기"""
    try:
        if SETTINGS_PATH.exists():
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                saved_settings = json.load(f)
                
                # 기본값 설정이 없는 항목이 있으면 DEFAULT_SETTINGS에서 가져옴
                for key, default_value in DEFAULT_SETTINGS.items():
                    if key not in saved_settings:
                        saved_settings[key] = default_value
                
                # TTS 저장 경로가 없으면 기본값 설정
                if 'tts_save_path' not in saved_settings:
                    saved_settings['tts_save_path'] = str(SCRIPT_DIR / 'tts_output')
                    
                # 볼륨 설정이 없으면 기본값 설정
                if 'first_priority_volume' not in saved_settings:
                    saved_settings['first_priority_volume'] = '100'
                if 'second_priority_volume' not in saved_settings:
                    saved_settings['second_priority_volume'] = '100'
                if 'third_priority_volume' not in saved_settings:
                    saved_settings['third_priority_volume'] = '100'

                # 언어 설정값 한글->영문 변환 추가
                lang_display_reverse = {v: k for k, v in LANG_DISPLAY.items()}
                for lang_key in ['first_lang', 'second_lang', 'third_lang']:
                    if lang_key in saved_settings:
                        display_name = saved_settings[lang_key]
                        if display_name in lang_display_reverse:
                            saved_settings[lang_key] = lang_display_reverse[display_name]
                
                # 로그 출력 삭제
                return saved_settings
        else:
            # 설정 파일이 없으면 기본값 사용
            print("설정 파일이 없어 기본값을 사용합니다.")
            return DEFAULT_SETTINGS.copy()
    except Exception as e:
        print(f"설정 로드 오류: {e}")
        # 오류 발생 시 기본값 사용
        return DEFAULT_SETTINGS.copy()

def select_save_path():
    """TTS 저장 경로 설정 대화상자 표시"""
    settings = load_settings()
    current_path = settings.get('tts_save_path', DEFAULT_SETTINGS['tts_save_path'])
    print(f"현재 TTS 저장 경로: {current_path}")  # 디버깅 메시지
    new_path = filedialog.askdirectory(initialdir=current_path)
    if new_path:
        settings['tts_save_path'] = new_path
        save_settings(settings)
        print(f"새로운 TTS 저장 경로: {new_path}")  # 디버깅 메시지
        messagebox.showinfo("저장 위치 변경", f"TTS 저장 위치가 변경되었습니다:\n{new_path}")

def create_settings_ui(return_to_learning=False):
    """설정 화면 UI 생성"""
    
    global current_frame, start_entry, end_entry, first_lang_cb, second_lang_cb, third_lang_cb
    global first_repeat, second_repeat, third_repeat, eng_voice_cb, kor_voice_cb, zh_voice_cb, jp_voice_cb
    global eng_speed, kor_speed, zh_speed, jp_speed, spacing_entry, break_var, break_interval
    global keep_subtitles_var, eng_voice_type, kor_voice_type, zh_voice_type, jp_voice_type, final_music_var
    global next_sentence_entry  # 다음 문장 엔트리 전역 변수 추가
    global auto_repeat_var, auto_repeat_enabled_var  # auto_repeat_enabled_var 추가
    global vn_speed, vn_voice_cb, vn_voice_type  # 베트남어 관련 변수 추가
    global ne_speed, ne_voice_cb, ne_voice_type  # 네팔어 관련 변수 추가
    # 통합 음성 설정용 전역 변수
    global first_voice_type, first_voice_cb, first_speed
    global second_voice_type, second_voice_cb, second_speed
    global third_voice_type, third_voice_cb, third_speed
    
    # 저장된 설정값 불러오기
    saved_settings = load_settings()
    
    # auto_repeat_var 및 auto_repeat_enabled_var 초기화
    auto_repeat_var = tk.StringVar(value=saved_settings.get('auto_repeat', '0'))
    auto_repeat_enabled_var = tk.StringVar(value=saved_settings.get('auto_repeat_enabled', 'false'))
    
    # 동시/순차 자막 설정 초기화 (keep_subtitles_var 변수 사용)
    keep_subtitles_var = tk.StringVar(value=saved_settings.get('keep_subtitles', 'true'))
    subtitle_mode_text = tk.StringVar(value="동시 자막" if keep_subtitles_var.get() == 'true' else "순차 자막")
    
    # break_var 초기화
    break_var = tk.BooleanVar(value=saved_settings.get('break_enabled', DEFAULT_SETTINGS['break_enabled']) == 'true')
    
    # final_music_var 초기화 (힐링타임용)
    final_music_var = tk.StringVar(value=saved_settings.get('final_music', DEFAULT_SETTINGS['final_music']))
    
    # 이전 프레임 제거
    if current_frame:
        current_frame.destroy()
    
    # 메인 프레임 생성
    current_frame = tk.Frame(root, **STYLE['frame'])
    current_frame.pack(expand=True, fill='both')
    
    # 엔터키 이벤트 핸들러
    def handle_enter(event):
        widget = event.widget
        if widget == start_entry:
            end_entry.focus()
        else:
            start_learning()
    
    # 전역 엔터키 이벤트 핸들러
    def handle_global_enter(event):
        if event.widget == start_entry:
            end_entry.focus()
        else:
            start_learning()
    
    # 전역 엔터키 바인딩
    root.bind('<Return>', handle_global_enter)
    root.bind('<KP_Enter>', handle_global_enter)  # 숫자패드 엔터키
    
    # 엔터키 바인딩 함수
    def bind_enter(widget):
        widget.bind('<Return>', handle_enter)
        widget.bind('<KP_Enter>', handle_enter)  # 숫자패드 엔터키
    
    # 제목과 컨테이너 프레임 사이의 여백 제거
    title_frame = tk.Frame(current_frame, bg=COLORS['text'], relief='raised', borderwidth=3)
    title_frame.pack(pady=(15, 20))  # 상단 여백 15픽셀, 하단 여백 20픽셀로 균등화
    
    title_label = tk.Label(title_frame, text="도파민 대충영어", 
                          font=("Helvetica", 36, "bold"),
                          bg=COLORS['text'], fg='#000000',
                          padx=40, pady=5)
    title_label.pack()
    
    # 컨테이너 프레임의 상단 여백 조정
    container_frame = tk.Frame(current_frame, **STYLE['frame'])
    container_frame.pack(fill='both', expand=True, pady=0)  # 여백 제거
    
    # 전체 UI 컨테이너 (너비 80%로 제한하고 중앙 배치)
    main_container_wrapper = tk.Frame(current_frame, **STYLE['frame'])
    main_container_wrapper.pack(fill='both', expand=True, pady=0)
    
    # 중앙 배치를 위한 좌우 여백 프레임 설정
    main_container_wrapper.columnconfigure(0, weight=1)  # 왼쪽 여백
    main_container_wrapper.columnconfigure(1, weight=8)  # 메인 컨텐츠 (80%)
    main_container_wrapper.columnconfigure(2, weight=1)  # 오른쪽 여백
    
    # 메인 컨텐츠 컨테이너
    main_container = tk.Frame(main_container_wrapper, **STYLE['frame'])
    main_container.grid(row=0, column=1, sticky='nsew')
    
    # 학습범위와 언어설정 섹션을 순차적으로 배치
    
    # 1. 학습 범위 설정
    range_frame = tk.LabelFrame(main_container, text="기본 설정", bg=COLORS['background'])
    range_frame.pack(fill='x', expand=True, pady=20)  # 상하 여백 균등하게 20픽셀 적용
    
    # 줄 1: 시작/종료 번호 + 브레이크 설정 + 동시/순차 자막 버튼 + TTS 폴더
    row1_frame = tk.Frame(range_frame, bg=COLORS['background'])
    row1_frame.pack(fill='x', pady=5)
    
    # 시작번호
    tk.Label(row1_frame, text="시작 번호:", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=(20, 5))
    start_entry = tk.Entry(row1_frame, **{**STYLE['entry'], 'width': 5, 'justify': 'center', 'font': ("Helvetica", 20)})
    start_entry.pack(side='left', padx=(0, 5))
    
    # 종료번호
    tk.Label(row1_frame, text="종료 번호:", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=5)
    end_entry = tk.Entry(row1_frame, **{**STYLE['entry'], 'width': 5, 'justify': 'center', 'font': ("Helvetica", 20)})
    end_entry.pack(side='left', padx=(0, 15))
    
    # 브레이크 설정 (원래 row2_frame에 있던 것을 row1_frame으로 이동)
    tk.Label(row1_frame, text="브레이크:", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=(15,5)) 
    break_interval = ttk.Combobox(row1_frame,
                                values=['없음', '5', '10', '15', '20'],
                                width=4,
                                justify='center',
                                **STYLE['combobox'])
    break_interval.pack(side='left', padx=(0, 15))
    break_interval.set(saved_settings.get('break_interval', '없음'))
    
    # 동시/순차 자막 설정 (버튼으로 변경)
    def toggle_subtitle_mode():
        # 자막 모드 토글
        current_mode = keep_subtitles_var.get()
        new_mode = 'false' if current_mode == 'true' else 'true'
        keep_subtitles_var.set(new_mode)
        
        # 버튼 텍스트 업데이트
        new_text = "동시 자막" if new_mode == 'true' else "순차 자막"
        subtitle_mode_text.set(new_text)
        subtitle_mode_btn.config(text=new_text)
    
    subtitle_mode_btn = tk.Button(
        row1_frame, 
        textvariable=subtitle_mode_text,
        command=toggle_subtitle_mode,
        font=("Helvetica", 16, "bold"),
        bg=COLORS['text'], 
        fg=COLORS['background'],
        width=8,
        relief='raised',
        borderwidth=2
    )
    subtitle_mode_btn.pack(side='left', padx=(5, 5))
    
    # TTS 저장 위치 버튼 - 자막유지 우측으로 이동
    path_button = tk.Button(row1_frame, text="TTS 폴더 위치 선택",
                           command=select_save_path,
                           font=("Helvetica", 14, "bold"),
                           bg=COLORS['text'],
                           fg=COLORS['background'])
    path_button.pack(side='left', padx=(20, 5))
    
    # 줄 2: 문장 간격, 다음 문장, 힐링뮤직, 자동반복 (브레이크 설정은 row1으로 이동됨)
    row2_frame = tk.Frame(range_frame, bg=COLORS['background'])
    row2_frame.pack(fill='x', pady=5)
    
    # 문장 간격 설정
    tk.Label(row2_frame, text="문장 간격:", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=(20, 5))
    spacing_frame = tk.Frame(row2_frame, bg=COLORS['background'])
    spacing_frame.pack(side='left', padx=(0, 15))
    spacing_entry = tk.Entry(spacing_frame, **{**STYLE['entry'], 'width': 5, 'justify': 'center', 'font': ("Helvetica", 20)})
    spacing_entry.pack(side='left')
    # placeholder 텍스트로 초 표시
    spacing_entry.insert(0, "0초")
    spacing_entry.bind("<FocusIn>", lambda event: spacing_entry.delete(0, tk.END) if spacing_entry.get() == "0초" else None)
    
    # 다음 문장 설정
    tk.Label(row2_frame, text="다음 문장:", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left')
    next_sentence_frame = tk.Frame(row2_frame, bg=COLORS['background'])
    next_sentence_frame.pack(side='left', padx=(0, 15))
    next_sentence_entry = tk.Entry(next_sentence_frame, **{**STYLE['entry'], 'width': 5, 'justify': 'center', 'font': ("Helvetica", 20)})
    next_sentence_entry.pack(side='left')
    # 기존 설정값 불러오기 후 초 추가
    next_time = saved_settings.get('next_sentence_time', DEFAULT_SETTINGS['next_sentence_time'])
    next_sentence_entry.insert(0, f"{next_time}초")
    next_sentence_entry.bind("<FocusIn>", lambda event: next_sentence_entry.delete(0, tk.END) if "초" in next_sentence_entry.get() else None)
    
    # 힐링타임 설정
    tk.Label(row2_frame, text="힐링뮤직:", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=(15,5)) # 왼쪽 여백 추가
    global final_music_cb
    final_music_cb = ttk.Combobox(row2_frame, 
                                values=['없음', '1분', '2분', '3분'],
                                state='readonly',
                                width=4,  # 5에서 4로 축소
                                font=("Helvetica", 18))
    final_music_cb.set(DEFAULT_SETTINGS['final_music'])
    final_music_cb.pack(side='left', padx=5)
    
    # 자동반복 설정 - 힐링뮤직 우측으로 이동
    tk.Label(row2_frame, text="자동 반복:", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=(20, 5))
    auto_repeat_entry = tk.Entry(row2_frame, textvariable=auto_repeat_var, 
                               **{**STYLE['entry'], 'width': 5, 'justify': 'center', 'font': ("Helvetica", 20)})
    auto_repeat_entry.pack(side='left')
    tk.Label(row2_frame, text="회", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=(2, 5))
    
    # 줄 3: (기타 옵션)
    row3_frame = tk.Frame(range_frame, bg=COLORS['background'])
    row3_frame.pack(fill='x', pady=5)
    
    # 2. 언어 설정 (음성설정과 동일한 높이)
    lang_frame = tk.LabelFrame(main_container, text="언어 설정", **STYLE['frame'])
    lang_frame.pack(fill='x', pady=20)  # 상하 여백 20픽셀로 균등화
    
    # 1순위 언어
    first_lang_frame = tk.Frame(lang_frame, **STYLE['frame'])
    first_lang_frame.pack(fill='x', pady=5)  # 2에서 5로 증가하여 더 균등한 간격 제공
    tk.Label(first_lang_frame, text="1순위:", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=5)
    first_lang_cb = ttk.Combobox(first_lang_frame, values=[LANG_DISPLAY[l] for l in LANGUAGES], width=5, **STYLE['combobox'])
    first_lang_cb.pack(side='left', padx=5)
    
    # 언어 변경 시 음성 목록 업데이트 함수
    def update_first_voice_options(event):
        display_to_lang = {v: k for k, v in LANG_DISPLAY.items()}
        selected_lang_display = first_lang_cb.get()
        selected_lang = display_to_lang.get(selected_lang_display, 'english')
        
        # 선택된 언어에 따른 음성 목록 업데이트
        if selected_lang in VOICE_MAPPING:
            first_voice_cb['values'] = list(VOICE_MAPPING[selected_lang].keys())
            if VOICE_MAPPING[selected_lang]:
                first_voice_cb.set(list(VOICE_MAPPING[selected_lang].keys())[0])
    
    # 콤보박스 변경 이벤트 바인딩
    first_lang_cb.bind("<<ComboboxSelected>>", update_first_voice_options)
    
    tk.Label(first_lang_frame, text="횟수:", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=5)
    first_repeat = tk.Entry(first_lang_frame, **{**STYLE['entry'], 'width': 3, 'justify': 'center', 'font': ("Helvetica", 20)})
    first_repeat.pack(side='left')
    tk.Label(first_lang_frame, text="회", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=(5,5))
    tk.Label(first_lang_frame, text="유형:", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=5)
    first_voice_type = ttk.Combobox(first_lang_frame, values=['WAV','TTS'], width=3, **STYLE['combobox'])  # 4에서 3으로 너비 축소
    first_voice_type.pack(side='left', padx=5)
    tk.Label(first_lang_frame, text="음성:", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=5)
    first_voice_cb = ttk.Combobox(first_lang_frame,
                                  values=list(VOICE_MAPPING[saved_settings.get('first_lang','english')].keys()),
                                  width=9, **STYLE['combobox'])
    first_voice_cb.pack(side='left', padx=5)
    first_speed = ttk.Combobox(first_lang_frame,
                               values=['1','1.5','2','3','4'],
                               width=3, justify='center', **STYLE['combobox'])
    first_speed.pack(side='left', padx=(5,0))
    tk.Label(first_lang_frame, text="배속", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=(5,5))
    
    # 볼륨 슬라이더 추가 (범위 확장: 0-500%)
    tk.Label(first_lang_frame, text="볼륨:", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=(10,5))
    global first_volume_var
    saved_volume = int(saved_settings.get('first_priority_volume', '100'))
    first_volume_var = tk.IntVar(value=saved_volume)  # 저장된 볼륨값 사용
    first_volume_slider = ttk.Scale(first_lang_frame, from_=0, to=200, variable=first_volume_var, orient='horizontal', length=150)
    first_volume_slider.pack(side='left', padx=(0,5))
    first_volume_label = tk.Label(first_lang_frame, text="100%", **{**STYLE['label'], 'font': ("Helvetica", 16)})
    first_volume_label.pack(side='left')
    
    # 볼륨 값 변경시 라벨 업데이트
    def update_first_volume_label(event):
        first_volume_label.config(text=f"{first_volume_var.get()}%")
        # 실시간 볼륨 변경사항 설정값에 저장
        settings = load_settings()
        settings['first_priority_volume'] = str(first_volume_var.get())
        save_settings(settings)
    
    first_volume_slider.bind("<Motion>", update_first_volume_label)
    first_volume_slider.bind("<ButtonRelease-1>", update_first_volume_label)
    
    # 2순위 언어
    second_lang_frame = tk.Frame(lang_frame, **STYLE['frame'])
    second_lang_frame.pack(fill='x', pady=5)  # 2에서 5로 증가하여 더 균등한 간격 제공
    tk.Label(second_lang_frame, text="2순위:", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=5)
    second_lang_cb = ttk.Combobox(second_lang_frame, values=[LANG_DISPLAY[l] for l in LANGUAGES], width=5, **STYLE['combobox'])
    second_lang_cb.pack(side='left', padx=5)
    
    # 2순위 언어 변경 시 음성 목록 업데이트 함수
    def update_second_voice_options(event):
        display_to_lang = {v: k for k, v in LANG_DISPLAY.items()}
        selected_lang_display = second_lang_cb.get()
        selected_lang = display_to_lang.get(selected_lang_display, 'korean')
        
        # 선택된 언어에 따른 음성 목록 업데이트
        if selected_lang in VOICE_MAPPING:
            second_voice_cb['values'] = list(VOICE_MAPPING[selected_lang].keys())
            if VOICE_MAPPING[selected_lang]:
                second_voice_cb.set(list(VOICE_MAPPING[selected_lang].keys())[0])
    
    # 콤보박스 변경 이벤트 바인딩
    second_lang_cb.bind("<<ComboboxSelected>>", update_second_voice_options)
    
    tk.Label(second_lang_frame, text="횟수:", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=5)
    second_repeat = tk.Entry(second_lang_frame, **{**STYLE['entry'], 'width': 3, 'justify': 'center', 'font': ("Helvetica", 20)})
    second_repeat.pack(side='left')
    tk.Label(second_lang_frame, text="회", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=(5,5))
    tk.Label(second_lang_frame, text="유형:", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=5)
    second_voice_type = ttk.Combobox(second_lang_frame, values=['WAV','TTS'], width=3, **STYLE['combobox'])  # 4에서 3으로 너비 축소
    second_voice_type.pack(side='left', padx=5)
    tk.Label(second_lang_frame, text="음성:", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=5)
    second_voice_cb = ttk.Combobox(second_lang_frame,
                                   values=list(VOICE_MAPPING[saved_settings.get('second_lang','korean')].keys()),
                                   width=9, **STYLE['combobox'])
    second_voice_cb.pack(side='left', padx=5)
    second_speed = ttk.Combobox(second_lang_frame,
                                values=['1','1.5','2','3','4'],
                                width=3, justify='center', **STYLE['combobox'])
    second_speed.pack(side='left', padx=(5,0))
    tk.Label(second_lang_frame, text="배속", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=(5,5))
    
    # 볼륨 슬라이더 추가 (범위 확장: 0-500%)
    tk.Label(second_lang_frame, text="볼륨:", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=(10,5))
    global second_volume_var
    saved_volume = int(saved_settings.get('second_priority_volume', '100'))
    second_volume_var = tk.IntVar(value=saved_volume)  # 저장된 볼륨값 사용
    second_volume_slider = ttk.Scale(second_lang_frame, from_=0, to=200, variable=second_volume_var, orient='horizontal', length=150)
    second_volume_slider.pack(side='left', padx=(0,5))
    second_volume_label = tk.Label(second_lang_frame, text="100%", **{**STYLE['label'], 'font': ("Helvetica", 16)})
    second_volume_label.pack(side='left')
    
    # 볼륨 값 변경시 라벨 업데이트
    def update_second_volume_label(event):
        second_volume_label.config(text=f"{second_volume_var.get()}%")
        # 실시간 볼륨 변경사항 설정값에 저장
        settings = load_settings()
        settings['second_priority_volume'] = str(second_volume_var.get())
        save_settings(settings)
    
    second_volume_slider.bind("<Motion>", update_second_volume_label)
    second_volume_slider.bind("<ButtonRelease-1>", update_second_volume_label)
    
    # 3순위 언어
    third_lang_frame = tk.Frame(lang_frame, **STYLE['frame'])
    third_lang_frame.pack(fill='x', pady=5)  # 2에서 5로 증가하여 더 균등한 간격 제공
    tk.Label(third_lang_frame, text="3순위:", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=5)
    third_lang_cb = ttk.Combobox(third_lang_frame, values=[LANG_DISPLAY[l] for l in LANGUAGES], width=5, **STYLE['combobox'])
    third_lang_cb.pack(side='left', padx=5)
    
    # 3순위 언어 변경 시 음성 목록 업데이트 함수
    def update_third_voice_options(event):
        display_to_lang = {v: k for k, v in LANG_DISPLAY.items()}
        selected_lang_display = third_lang_cb.get()
        selected_lang = display_to_lang.get(selected_lang_display, 'chinese')
        
        # 선택된 언어에 따른 음성 목록 업데이트
        if selected_lang in VOICE_MAPPING:
            third_voice_cb['values'] = list(VOICE_MAPPING[selected_lang].keys())
            if VOICE_MAPPING[selected_lang]:
                third_voice_cb.set(list(VOICE_MAPPING[selected_lang].keys())[0])
    
    # 콤보박스 변경 이벤트 바인딩
    third_lang_cb.bind("<<ComboboxSelected>>", update_third_voice_options)
    
    tk.Label(third_lang_frame, text="횟수:", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=5)
    third_repeat = tk.Entry(third_lang_frame, **{**STYLE['entry'], 'width': 3, 'justify': 'center', 'font': ("Helvetica", 20)})
    third_repeat.pack(side='left')
    tk.Label(third_lang_frame, text="회", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=(5,5))
    tk.Label(third_lang_frame, text="유형:", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=5)
    third_voice_type = ttk.Combobox(third_lang_frame, values=['WAV','TTS'], width=3, **STYLE['combobox'])  # 4에서 3으로 너비 축소
    third_voice_type.pack(side='left', padx=5)
    tk.Label(third_lang_frame, text="음성:", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=5)
    third_voice_cb = ttk.Combobox(third_lang_frame,
                                  values=list(VOICE_MAPPING[saved_settings.get('third_lang','chinese')].keys()),
                                  width=9, **STYLE['combobox'])
    third_voice_cb.pack(side='left', padx=5)
    third_speed = ttk.Combobox(third_lang_frame,
                               values=['1','1.5','2','3','4'],
                               width=3, justify='center', **STYLE['combobox'])
    third_speed.pack(side='left', padx=(5,0))
    tk.Label(third_lang_frame, text="배속", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=(5,5))
    
    # 볼륨 슬라이더 추가 (범위 확장: 0-500%)
    tk.Label(third_lang_frame, text="볼륨:", **{**STYLE['label'], 'font': ("Helvetica", 20, "bold")}).pack(side='left', padx=(10,5))
    global third_volume_var
    third_volume_var = tk.IntVar(value=100)  # 기본값 100%
    third_volume_slider = ttk.Scale(third_lang_frame, from_=0, to=200, variable=third_volume_var, orient='horizontal', length=150)
    third_volume_slider.pack(side='left', padx=(0,5))
    third_volume_label = tk.Label(third_lang_frame, text="100%", **{**STYLE['label'], 'font': ("Helvetica", 16)})
    third_volume_label.pack(side='left')
    
    # 볼륨 값 변경시 라벨 업데이트
    def update_third_volume_label(event):
        third_volume_label.config(text=f"{third_volume_var.get()}%")
        # 실시간 볼륨 변경사항 설정값에 저장
        settings = load_settings()
        settings['third_priority_volume'] = str(third_volume_var.get())
        save_settings(settings)
    
    third_volume_slider.bind("<Motion>", update_third_volume_label)
    third_volume_slider.bind("<ButtonRelease-1>", update_third_volume_label)
    
    # 버튼 프레임도 중앙 정렬하여 배치
    button_frame_wrapper = tk.Frame(current_frame, bg=COLORS['background'])
    button_frame_wrapper.pack(side='bottom', fill='x', pady=20)
    
    # 버튼 프레임 좌우 여백 설정
    button_frame_wrapper.columnconfigure(0, weight=1)  # 왼쪽 여백
    button_frame_wrapper.columnconfigure(1, weight=8)  # 중앙 컨텐츠 (80%)
    button_frame_wrapper.columnconfigure(2, weight=1)  # 오른쪽 여백
    
    # 실제 버튼을 포함할 프레임
    button_frame = tk.Frame(button_frame_wrapper, bg=COLORS['background'])
    button_frame.grid(row=0, column=1, sticky='ew')
    
    # 버튼 스타일 설정 - 높이 조정
    button_style = {
        'font': ("Helvetica", 24, "bold"),
        'width': 12,  # 너비 10에서 7로 축소 (30% 감소)
        'height': 1,  # 높이 2에서 1로 축소
        'relief': 'raised',
        'borderwidth': 4,  # 테두리 두께 유지
        'cursor': 'hand2',
        'fg': 'black',
        'compound': 'center',  # 텍스트를 중앙에 배치
        'anchor': 'center'     # 텍스트를 중앙에 표시
    }

    # 버튼들을 담을 프레임 생성
    buttons_container = tk.Frame(button_frame, bg=COLORS['background'])
    buttons_container.pack(expand=True, fill='x', pady=(0, 20))  # 하단 여백 20픽셀 추가
    
    # TTS 저장 버튼
    save_tts_button = tk.Button(
        buttons_container,
        text="TTS 저장",
        command=start_tts_save,
        **{**button_style, 'bg': '#0078D7'}
    )
    save_tts_button.pack(side='left', expand=True, padx=20)

    # 학습 시작 버튼
    start_button = tk.Button(
        buttons_container,
        text="학습 시작",
        command=start_learning,
        **{**button_style, 'bg': '#4CAF50'}
    )
    start_button.pack(side='left', expand=True, padx=20)

    # 종료 버튼
    stop_button = tk.Button(
        buttons_container,
        text="종료",
        command=root.destroy,
        **{**button_style, 'bg': '#FF5555'}
    )
    stop_button.pack(side='left', expand=True, padx=20)
    
    # 설정값 적용
    start_entry.insert(0, saved_settings.get('start_row', DEFAULT_SETTINGS['start_row']))
    end_entry.insert(0, saved_settings.get('end_row', DEFAULT_SETTINGS['end_row']))
    
    first_lang_cb.set(LANG_DISPLAY[saved_settings.get('first_lang', DEFAULT_SETTINGS['first_lang'])])
    second_lang_cb.set(LANG_DISPLAY[saved_settings.get('second_lang', DEFAULT_SETTINGS['second_lang'])])
    third_lang_cb.set(LANG_DISPLAY[saved_settings.get('third_lang', DEFAULT_SETTINGS['third_lang'])])
    
    first_repeat.insert(0, saved_settings.get('first_repeat', DEFAULT_SETTINGS['first_repeat']))
    second_repeat.insert(0, saved_settings.get('second_repeat', DEFAULT_SETTINGS['second_repeat']))
    third_repeat.insert(0, saved_settings.get('third_repeat', DEFAULT_SETTINGS['third_repeat']))
    
    # 유형, 음성, 배속 기본값 설정
    first_lang = saved_settings.get('first_lang', DEFAULT_SETTINGS['first_lang'])
    second_lang = saved_settings.get('second_lang', DEFAULT_SETTINGS['second_lang'])
    third_lang = saved_settings.get('third_lang', DEFAULT_SETTINGS['third_lang'])
    
    # 유형 설정 (기본값: WAV)
    first_voice_type.set(saved_settings.get('first_voice_type', 'WAV'))
    second_voice_type.set(saved_settings.get('second_voice_type', 'WAV'))
    third_voice_type.set(saved_settings.get('third_voice_type', 'WAV'))
    
    # 음성 설정
    try:
        # 우선순위별 음성 설정 불러오기 (기본값은 언어별 기본 음성)
        first_voice = saved_settings.get("first_priority_voice", 
                      saved_settings.get(f"{first_lang}_voice", 
                      DEFAULT_SETTINGS.get(f"{first_lang}_voice", "")))
        if first_voice and first_voice in VOICE_MAPPING[first_lang]:
            first_voice_cb.set(first_voice)
        else:
            first_voice_cb.set(list(VOICE_MAPPING[first_lang].keys())[0])
            
        second_voice = saved_settings.get("second_priority_voice", 
                       saved_settings.get(f"{second_lang}_voice", 
                       DEFAULT_SETTINGS.get(f"{second_lang}_voice", "")))
        if second_voice and second_voice in VOICE_MAPPING[second_lang]:
            second_voice_cb.set(second_voice)
        else:
            second_voice_cb.set(list(VOICE_MAPPING[second_lang].keys())[0])
            
        third_voice = saved_settings.get("third_priority_voice", 
                      saved_settings.get(f"{third_lang}_voice", 
                      DEFAULT_SETTINGS.get(f"{third_lang}_voice", "")))
        if third_voice and third_voice in VOICE_MAPPING[third_lang]:
            third_voice_cb.set(third_voice)
        else:
            third_voice_cb.set(list(VOICE_MAPPING[third_lang].keys())[0])
    except Exception as e:
        print(f"음성 설정 적용 중 오류: {e}")
        
    # 배속 설정
    try:
        # 우선순위별 배속 설정 로드 (없으면 언어별 속도 사용)
        first_speed.set(saved_settings.get("first_priority_speed", saved_settings.get(f"{first_lang}_speed", DEFAULT_SETTINGS.get(f"{first_lang}_speed", "1"))))
        second_speed.set(saved_settings.get("second_priority_speed", saved_settings.get(f"{second_lang}_speed", DEFAULT_SETTINGS.get(f"{second_lang}_speed", "1"))))
        third_speed.set(saved_settings.get("third_priority_speed", saved_settings.get(f"{third_lang}_speed", DEFAULT_SETTINGS.get(f"{third_lang}_speed", "1"))))
    except Exception as e:
        print(f"배속 설정 적용 중 오류: {e}")
    
    # 볼륨 설정
    try:
        # 우선순위별 볼륨 설정 로드
        first_volume_var.set(int(saved_settings.get("first_priority_volume", "300")))
        second_volume_var.set(int(saved_settings.get("second_priority_volume", "300")))
        third_volume_var.set(int(saved_settings.get("third_priority_volume", "300")))
        
        # 볼륨 라벨 업데이트
        first_volume_label.config(text=f"{first_volume_var.get()}%")
        second_volume_label.config(text=f"{second_volume_var.get()}%")
        third_volume_label.config(text=f"{third_volume_var.get()}%")
    except Exception as e:
        print(f"볼륨 설정 적용 중 오류: {e}")
    
    # 음성 배속 설정 불러오기
    
    try:
        # 문장 간격, 자막 먼저, 다음 문장 설정값에 '초' 추가
        spacing_entry.delete(0, tk.END)
        spacing_entry.insert(0, f"{saved_settings.get('spacing', DEFAULT_SETTINGS['spacing'])}초")
        
        # subtitle_entry.delete(0, tk.END) # 삭제됨
        # subtitle_entry.insert(0, f"{saved_settings.get('subtitle_delay', DEFAULT_SETTINGS['subtitle_delay'])}초") # 삭제됨
        
        # 포커스 아웃 시 '초' 추가
        def add_seconds_on_focusout(event, entry):
            text = entry.get().strip()
            if text and not text.endswith('초'):
                # 숫자만 추출하고 '초' 추가
                try:
                    num = ''.join(filter(lambda c: c.isdigit() or c == '.', text))
                    if num:
                        entry.delete(0, tk.END)
                        entry.insert(0, f"{num}초")
                except:
                    pass
        
        spacing_entry.bind("<FocusOut>", lambda event: add_seconds_on_focusout(event, spacing_entry))
        # subtitle_entry.bind("<FocusOut>", lambda event: add_seconds_on_focusout(event, subtitle_entry)) # 삭제됨
        next_sentence_entry.bind("<FocusOut>", lambda event: add_seconds_on_focusout(event, next_sentence_entry))
    except Exception as e:
        print(f"설정 값 적용 중 오류: {e}")
    
    # break_interval.set(saved_settings.get('break_interval', '없음')) # row1으로 이동 시 함께 처리됨
    
    # 설정값 적용
    # 재생 설정 섹션에 final music과 랜덤 재생 옵션을 같은 줄에 배치
    
    # 자동반복 설정 수정 (체크박스 제거)

def reset_to_default():
    """설정을 기본값으로 초기화"""
    # 학습 범위
    start_entry.delete(0, tk.END)
    start_entry.insert(0, DEFAULT_SETTINGS['start_row'])
    end_entry.delete(0, tk.END)
    end_entry.insert(0, DEFAULT_SETTINGS['end_row'])
    
    # 언어 설정
    first_lang_cb.set(LANG_DISPLAY[DEFAULT_SETTINGS['first_lang']])
    second_lang_cb.set(LANG_DISPLAY[DEFAULT_SETTINGS['second_lang']])
    third_lang_cb.set(LANG_DISPLAY[DEFAULT_SETTINGS['third_lang']])
    
    # 반복 횟수
    first_repeat.delete(0, tk.END)
    first_repeat.insert(0, DEFAULT_SETTINGS['first_repeat'])
    second_repeat.delete(0, tk.END)
    second_repeat.insert(0, DEFAULT_SETTINGS['second_repeat'])
    third_repeat.delete(0, tk.END)
    third_repeat.insert(0, DEFAULT_SETTINGS['third_repeat'])
    
    # 통합 음성 설정
    first_voice_type.set('WAV')
    second_voice_type.set('WAV')
    third_voice_type.set('WAV')
    
    first_voice_cb.set(DEFAULT_SETTINGS[f"{DEFAULT_SETTINGS['first_lang']}_voice"])
    second_voice_cb.set(DEFAULT_SETTINGS[f"{DEFAULT_SETTINGS['second_lang']}_voice"])
    third_voice_cb.set(DEFAULT_SETTINGS[f"{DEFAULT_SETTINGS['third_lang']}_voice"])
    
    first_speed.set(DEFAULT_SETTINGS[f"{DEFAULT_SETTINGS['first_lang']}_speed"])
    second_speed.set(DEFAULT_SETTINGS[f"{DEFAULT_SETTINGS['second_lang']}_speed"])
    third_speed.set(DEFAULT_SETTINGS[f"{DEFAULT_SETTINGS['third_lang']}_speed"])
    
    # 우선순위별 설정 초기화 (설정에서 삭제)
    settings = load_settings()
    if 'first_priority_voice' in settings: del settings['first_priority_voice']
    if 'second_priority_voice' in settings: del settings['second_priority_voice']
    if 'third_priority_voice' in settings: del settings['third_priority_voice']
    if 'first_priority_speed' in settings: del settings['first_priority_speed']
    if 'second_priority_speed' in settings: del settings['second_priority_speed']
    if 'third_priority_speed' in settings: del settings['third_priority_speed']
    
    # 볼륨 설정 초기화
    if 'first_priority_volume' in settings: del settings['first_priority_volume']
    if 'second_priority_volume' in settings: del settings['second_priority_volume']
    if 'third_priority_volume' in settings: del settings['third_priority_volume']
    
    # 볼륨 슬라이더 값 초기화
    first_volume_var.set(100)
    second_volume_var.set(100)
    third_volume_var.set(100)
    
    save_settings(settings)
    
    # 재생 설정
    spacing_entry.delete(0, tk.END)
    spacing_entry.insert(0, DEFAULT_SETTINGS['spacing'])
    # subtitle_entry.delete(0, tk.END) # 삭제됨
    # subtitle_entry.insert(0, DEFAULT_SETTINGS['subtitle_delay']) # 삭제됨
    next_sentence_entry.delete(0, tk.END)
    next_sentence_entry.insert(0, DEFAULT_SETTINGS['next_sentence_time'])
    break_interval.set(DEFAULT_SETTINGS['break_interval'])
    final_music_cb.set(DEFAULT_SETTINGS['final_music'])
    
    # 자동 반복
    auto_repeat_entry.delete(0, tk.END)
    auto_repeat_entry.insert(0, '0')  # 기본값은 0회

def create_learning_ui():
    """학습 화면 UI 생성"""
    settings = load_settings()  # 설정 로드 추가
    global current_frame, progress_label, subtitle_labels, total_time_label, avg_time_label, learning_logo_image, flac_logo_image
    
    # 이전 프레임 제거
    if current_frame:
        current_frame.destroy()
    
    # 메인 프레임 생성 (테두리 추가)
    current_frame = tk.Frame(root, **STYLE['frame'], highlightbackground=COLORS['text'],
                           highlightcolor=COLORS['text'], highlightthickness=9)
    current_frame.pack(expand=True, fill='both')
    
    # 상단 프레임 (진행 상황)
    top_frame = tk.Frame(current_frame, **STYLE['frame'])
    top_frame.pack(fill='x', pady=10)
    
    # 좌측 컨테이너 (로고와 문구)
    left_container = tk.Frame(top_frame, bg=COLORS['background'])
    left_container.pack(side='left', padx=20)
    
    # 로고 추가 (좌측 상단)
    try:
        logo_path = resource_path("images/logo.png")
        if logo_path.exists():
            logo_image = Image.open(logo_path)
            # 로고 크기 조정 (20% 증가)
            logo_height = 39  # 30 * 1.2 = 36 (20% 증가)
            aspect_ratio = logo_image.width / logo_image.height
            logo_width = int(logo_height * aspect_ratio)
            logo_image = logo_image.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            learning_logo_image = ImageTk.PhotoImage(logo_image)  # 전역 변수에 저장
            
            logo_label = tk.Label(left_container, image=learning_logo_image,
                                bg=COLORS['background'])
            logo_label.pack(side='left', padx=(0, 10))  # 오른쪽 여백 추가
    except Exception as e:
        print(f"학습화면 로고 로딩 오류: {e}")
        traceback.print_exc()
    
    # 좌상단 문구
    title_label = tk.Label(left_container, text="한글속청 30일 영어 귀가 뚫린다!",
                          font=("AppleSDGothicNeo", 30, "bold"),
                          bg=COLORS['background'], fg=COLORS['progress'])
    title_label.pack(side='left', padx=5)
    
    # 투명 초기화면 버튼을 상단 중앙에 배치
    home_button = tk.Label(top_frame, 
                          text="",  # 텍스트 없음
                          bg=COLORS['background'], 
                          cursor='hand2',
                          width=10,  # 너비 설정
                          height=2)  # 높이 설정
    home_button.pack(side='left', expand=True, padx=20)

    # 클릭 이벤트 핸들러 수정
    def stop_learning_and_return(event):
        """학습을 정지하고 초기화면으로 복귀"""
        try:
            global is_learning
            is_learning = False  # 학습 중단 플래그 설정
            
            # 재생 중인 모든 음성 정지
            pygame.mixer.stop()
            pygame.mixer.music.stop()
            
            # sounddevice 재생 정지
            sd.stop()
            
            print("학습 정지: 사용자가 초기화면으로 복귀를 요청했습니다.")
            
            # 초기화면으로 복귀
            create_settings_ui()
        except Exception as e:
            print(f"학습 정지 오류: {e}")
    
    # 레이블에 클릭 이벤트 바인딩
    home_button.bind("<Button-1>", stop_learning_and_return)
    
    # 우측 컨테이너 (진행 번호)
    right_container = tk.Frame(top_frame, bg=COLORS['background'])
    right_container.pack(side='right', padx=20)
    
    # 현재 문장 번호 (먼저 배치)
    progress_label = tk.Label(right_container, text="001", font=FONT_PROGRESS,
                            bg=COLORS['background'], fg=COLORS['progress'])
    progress_label.pack(side='left')
    
    # 플랙 로고 추가 (문장 번호 다음에 배치)
    try:
        flac_logo_path = resource_path("resources/images/flac_logo.jpg")
        
        # 여러 경로에서 로고 파일 찾기
        potential_paths = [
            resource_path("resources/images/flac_logo.jpg"),
            resource_path("images/flac_logo.jpg"),
            resource_path("flac_logo.jpg"),
            resource_path("dist/dopa710/images/flac_logo.jpg"),
            resource_path("logo/flac_logo.jpg")
        ]
        
        found = False
        for test_path in potential_paths:
            if os.path.exists(test_path):
                flac_logo_path = test_path
                found = True
                print(f"[우상단] 플랙 로고 파일 발견: {flac_logo_path}")
                break
        
        if found:
            flac_img = Image.open(flac_logo_path)
            # 로고 크기 조정
            logo_height = 30  
            aspect_ratio = flac_img.width / flac_img.height
            logo_width = int(logo_height * aspect_ratio)
            flac_img = flac_img.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
            flac_logo_photo = ImageTk.PhotoImage(flac_img)
            
            flac_logo_label = tk.Label(right_container, image=flac_logo_photo,
                                bg=COLORS['background'])
            flac_logo_label.image = flac_logo_photo  # 참조 유지
            flac_logo_label.pack(side='left', padx=(10, 0))  # 왼쪽 여백 추가
            print(f"플랙 로고 로딩 성공: {logo_width}x{logo_height}")
    except Exception as e:
        print(f"플랙 로고 로딩 오류: {e}")
        traceback.print_exc()
    
    # 중앙 프레임 (자막)
    subtitle_frame = tk.Frame(current_frame, **STYLE['frame'])
    subtitle_frame.pack(expand=True, fill='both', pady=20)
    
    # 음성 재생 언어 확인 (순서 보장되도록 수정)
    active_languages_with_audio = []
    langs_order = [
        settings['first_lang'], 
        settings['second_lang'], 
        settings['third_lang']
    ]
    
    for lang in langs_order:
        repeat_key = {
            settings['first_lang']: 'first_repeat',
            settings['second_lang']: 'second_repeat',
            settings['third_lang']: 'third_repeat'
        }[lang]
        
        if int(settings[repeat_key]) > 0 and lang != 'none':
            active_languages_with_audio.append(lang)

    # 자막 레이블 생성 (활성화된 언어 순서대로 색상 적용)
    subtitle_labels = []
    for i, lang in enumerate(langs_order):
        if lang == 'none':
            continue
            
        # 해당 언어가 음성 재생되는지 여부에 따라 초기 색상 설정
        fg_color = COLORS['highlight'] if lang in active_languages_with_audio else COLORS['text']
        
        label = tk.Label(subtitle_frame, text="", font=FONT_SUBTITLE,
                         bg=COLORS['background'], fg=fg_color,
                         wraplength=1000)
        label.pack(expand=True, pady=5)
        subtitle_labels.append(label)
    
    # 하단 프레임 (통계)
    bottom_frame = tk.Frame(current_frame, **STYLE['frame'])
    bottom_frame.pack(fill='x', side='bottom', pady=10)
    
    # 공통 폰트 설정
    info_font = ("AppleSDGothicNeo", 24, "bold")  # 모든 정보에 동일한 폰트 적용
    
    # 왼쪽 - 총 소요 시간 (형식 변경: 00분00초)
    total_time_label = tk.Label(bottom_frame, text="00분00초",
                               font=info_font, bg=COLORS['background'],
                               fg=COLORS['progress'])
    total_time_label.pack(side='left', expand=True)
    
    # 중앙 - 배속 정보 프레임
    speed_frame = tk.Frame(bottom_frame, bg=COLORS['background'])
    speed_frame.pack(side='left', expand=True)
    
    # 실제 재생될 음성 정보 수집
    settings = load_settings()
    active_voices = []
    # 우선순위별 정확한 음성 정보 표시
    if int(settings['first_repeat']) > 0:
        first_lang = settings['first_lang']
        first_speed = settings.get('first_priority_speed', "1.0")
        active_voices.append(f"{LANG_DISPLAY[first_lang]} {first_speed}배속")
    
    if int(settings['second_repeat']) > 0:
        second_lang = settings['second_lang']
        second_speed = settings.get('second_priority_speed', "1.0")
        active_voices.append(f"{LANG_DISPLAY[second_lang]} {second_speed}배속")
    
    if int(settings['third_repeat']) > 0:
        third_lang = settings['third_lang']
        third_speed = settings.get('third_priority_speed', "1.0")
        active_voices.append(f"{LANG_DISPLAY[third_lang]} {third_speed}배속")
    
    # 배속 정보 로딩 디버그 출력
    print("\n[배속 설정 확인]")
    print(f"1순위({settings['first_lang']}): {settings.get('first_priority_speed', '1.0')}배속")
    print(f"2순위({settings['second_lang']}): {settings.get('second_priority_speed', '1.0')}배속")
    print(f"3순위({settings['third_lang']}): {settings.get('third_priority_speed', '1.0')}배속")
    
    # 배속 정보 레이블 생성
    global speed_label
    speed_label = tk.Label(speed_frame, text=" • ".join(active_voices),
                          font=("AppleSDGothicNeo", 24, "bold"),
                          bg=COLORS['background'],
                          fg=COLORS['progress'])
    speed_label.pack()
    
    # 오른쪽 - 평균 시간
    avg_time_label = tk.Label(bottom_frame, text="time = 0.0초",
                             font=info_font, bg=COLORS['background'],
                             fg=COLORS['progress'])
    avg_time_label.pack(side='right', expand=True)
    
    root.update()
    
    # 시간 업데이트 시작 부분 제거
    # update_time_display.start_time = time.time()
    # update_time_display()

def start_learning():
    """학습 시작 함수"""
    try:
        settings = get_settings()
        if not settings:
            show_error_popup("설정 오류", "학습 설정을 가져올 수 없습니다.")
            return
            
        # 시작 및 종료 행 번호 유효성 검사
        start_value = settings.get('start_row', '1')
        end_value = settings.get('end_row', '10')
        
        if not validate_settings(start_value, end_value):
            return
            
        # 카운트다운 시작
        def run_async():
            asyncio.run(learning_sequence())
        
        async def learning_sequence():
            # 카운트다운 화면 표시
            await show_countdown()
            root.update()
            
            # 학습 화면으로 전환
            create_learning_ui()
            root.update()
            
            # 학습 시작
            await start_learning_async(settings)
        
        # 별도 스레드에서 비동기 시퀀스 실행
        threading.Thread(target=run_async, daemon=True).start()
    except Exception as e:
        print(f"학습 시작 중 오류 발생: {e}")
        traceback.print_exc()

async def show_countdown():
    """카운트다운 표시"""
    global current_frame, countdown_label, message_label, countdown_logo_image
    
    try:
        # 이전 프레임 제거
        if current_frame:
            current_frame.destroy()
        
        # 새 프레임 생성 (전체 화면)
        current_frame = tk.Frame(root, bg='black')
        current_frame.pack(fill='both', expand=True)
        
        # 설정 로드
        settings = load_settings()
        
        # 로고 이미지 로드 (한 번만 로드)
        if countdown_logo_image is None:
            logo_path = SCRIPT_DIR / "resources" / "images" / "flac_logo.jpg"
            
            # 여러 경로에서 로고 파일 찾기
            potential_paths = [
                SCRIPT_DIR / "resources" / "images" / "flac_logo.jpg",
                SCRIPT_DIR / "images" / "flac_logo.jpg",
                SCRIPT_DIR / "logo" / "flac_logo.jpg",
                SCRIPT_DIR / "flac_logo.jpg"
            ]
            
            found = False
            for test_path in potential_paths:
                if os.path.exists(test_path):
                    logo_path = test_path
                    found = True
                    print(f"[카운트다운] 로고 파일 발견: {logo_path}")
                    break
            
            if found:
                # 로고 이미지 로드
                try:
                    logo_img = Image.open(logo_path)
                    # 로고 크기 조정 (원본의 40%)
                    logo_width, logo_height = logo_img.size
                    logo_img = logo_img.resize((int(logo_width * 0.4), int(logo_height * 0.4)))
                    countdown_logo_image = ImageTk.PhotoImage(logo_img)
                    print(f"[카운트다운] 로고 이미지 로드 성공: {logo_path}")
                except Exception as e:
                    print(f"[카운트다운] 로고 이미지 로드 실패: {e}")
                    countdown_logo_image = None
            else:
                print(f"[카운트다운] 로고 이미지 파일이 없습니다: {logo_path}")
                countdown_logo_image = None
        
        # 썸네일 표시 (3초)
        try:
            # 설정 확인
            settings = load_settings()
            
            # 2순위와 3순위 언어 확인 (3순위 우선, 없으면 2순위)
            third_lang = settings.get('third_lang', 'korean')
            second_lang = settings.get('second_lang', 'english')
            
            # 첫 번째로 3순위 언어 사용
            start_row = int(settings.get('start_row', '1'))
            
            # 이미지 번호 계산 (1-100 -> 1번, 101-200 -> 2번, ...)
            image_number = ((start_row - 1) // 100) + 1
            if image_number < 1:
                image_number = 1
            if image_number > 6:  # 이미지는 최대 6번까지만 있는 것으로 보임
                image_number = 6
                
            print(f"[썸네일] 시작 행: {start_row}, 3순위 언어: {third_lang}, 2순위 언어: {second_lang}")
            print(f"[썸네일] 계산된 이미지 번호: {image_number} (시작 행: {start_row})")
            
            # 이미지 선택 로직
            lang_map = {
                'vietnamese': 'vi600',
                'japanese': ['ja600', 'jp600'],  # 두 가지 접두어 모두 시도
                'chinese': ['zh600', 'ch600'],   # 두 가지 접두어 모두 시도
                'korean': 'ko600',
                'english': 'en600',
                'nepali': 'ne600'  # 네팔어 추가
            }
            
            # 각 언어별 접두어 추출
            third_prefix = lang_map.get(third_lang, '')
            second_prefix = lang_map.get(second_lang, '')
            first_prefix = lang_map.get(settings.get('first_lang', 'english'), '')
            
            print(f"[썸네일] 이미지 접두어 후보: 3순위={third_prefix}, 2순위={second_prefix}, 1순위={first_prefix}")
            
            # 이미지 파일 탐색 (3순위, 2순위, 1순위, 기본 순서로)
            found_image = False
            img_path = None
            
            # 시도할 접두어 순서 설정
            prefix_candidates = []
            
            # 3순위 언어가 있는 경우에만 해당 언어의 접두어 추가
            if third_lang != 'none':
                if isinstance(third_prefix, list):
                    prefix_candidates.extend(third_prefix)
                else:
                    prefix_candidates.append(third_prefix)
            
            # 2순위 언어가 있는 경우에만 해당 언어의 접두어 추가
            if second_lang != 'none':
                if isinstance(second_prefix, list):
                    prefix_candidates.extend(second_prefix)
                else:
                    prefix_candidates.append(second_prefix)
            
            # 1순위 언어가 있는 경우에만 해당 언어의 접두어 추가
            if settings.get('first_lang') != 'none':
                if isinstance(first_prefix, list):
                    prefix_candidates.extend(first_prefix)
                else:
                    prefix_candidates.append(first_prefix)
            
            # 기본 접두어 추가
            prefix_candidates.extend(['ko600', 'en600'])
            
            print(f"[썸네일] 시도할 접두어 순서: {prefix_candidates}")
            
            # 각 접두어별로 이미지 파일 탐색
            for prefix in prefix_candidates:
                print(f"[썸네일] {prefix} 접두어로 이미지 검색 시작")
                # 특정 접두어에 대한 경로 시도
                potential_paths = [
                    # 계산된 이미지 번호로 시도 (우선 순위 최상위)
                    SCRIPT_DIR / 'images' / f'{prefix}-{image_number}.jpg',
                    SCRIPT_DIR / 'images' / f'{prefix}-{image_number}.png',
                    # 그 다음 start_row로 직접 시도
                    SCRIPT_DIR / 'images' / f'{prefix}-{start_row}.jpg',
                    SCRIPT_DIR / 'images' / f'{prefix}-{start_row}.png',
                    # 기타 번호들 시도
                    SCRIPT_DIR / 'images' / f'{prefix}-1.jpg',
                    SCRIPT_DIR / 'images' / f'{prefix}-2.jpg',
                    SCRIPT_DIR / 'images' / f'{prefix}-3.jpg',
                    SCRIPT_DIR / 'images' / f'{prefix}-4.jpg',
                    SCRIPT_DIR / 'images' / f'{prefix}-5.jpg',
                    SCRIPT_DIR / 'images' / f'{prefix}-6.jpg',
                    # 기타 패턴 시도
                    SCRIPT_DIR / 'images' / f'{prefix}-intro.jpg',
                    SCRIPT_DIR / 'images' / f'{prefix}-intro.png',
                    SCRIPT_DIR / 'base' / f'{prefix}-{image_number}.jpg',
                    SCRIPT_DIR / 'base' / f'{prefix}-{image_number}.png',
                    SCRIPT_DIR / 'base' / f'{prefix}-{start_row}.jpg',
                    SCRIPT_DIR / 'base' / f'{prefix}-{start_row}.png',
                    SCRIPT_DIR / 'base' / f'{prefix}-intro.jpg',
                    SCRIPT_DIR / 'base' / f'{prefix}-intro.png'
                ]
                
                for path in potential_paths:
                    if path.exists():
                        img_path = path
                        found_image = True
                        print(f"[썸네일] 이미지 파일 발견: {img_path} ({prefix} 접두어)")
                        break
                
                if found_image:
                    break  # 이미지를 찾았으면 다음 접두어는 시도하지 않음
            
            # 위 접두어별 탐색으로도 찾지 못한 경우 기본 이미지 시도
            if not found_image:
                print("[썸네일] 언어별 접두어로 이미지를 찾지 못해 기본 이미지 시도")
                default_paths = [
                    SCRIPT_DIR / 'images' / 'intro.jpg',
                    SCRIPT_DIR / 'images' / 'intro.png',
                    SCRIPT_DIR / 'intro.jpg',
                    SCRIPT_DIR / 'intro.png'
                ]
                
                for path in default_paths:
                    if path.exists():
                        img_path = path
                        found_image = True
                        print(f"[썸네일] 기본 이미지 파일 발견: {img_path}")
                        break
            
            # 최종적으로 이미지 파일을 찾은 경우
            if found_image and img_path:
                print(f"[썸네일] 이미지 경로: {img_path}")
                print(f"[썸네일] 파일 존재 여부: {img_path.exists()}")
                print(f"[썸네일] 절대 경로: {img_path.absolute()}")
                
                # 썸네일 이미지 존재할 경우 표시
                img = Image.open(img_path)
                print(f"[썸네일] 원본 크기: {img.width}x{img.height}")
                
                # 화면 크기에 맞게 이미지 크기 조정
                screen_width = root.winfo_width()
                screen_height = root.winfo_height()
                print(f"[썸네일] 화면 크기: {screen_width}x{screen_height}")
                
                # 화면 크기가 0일 경우 기본값 사용
                if screen_width < 100 or screen_height < 100:
                    screen_width = 1280
                    screen_height = 800

                # 화면 크기의 90%를 목표로 설정
                target_w = int(screen_width * 0.99)
                target_h = int(screen_height * 0.99)
                print(f"[썸네일] 목표 크기: {target_w}x{target_h}")
                
                # 비율 계산
                img_ratio = img.width / img.height
                target_ratio = target_w / target_h
                
                if img_ratio > target_ratio:
                    new_w = target_w
                    new_h = int(target_w / img_ratio)
                else:
                    new_h = target_h
                    new_w = int(target_h * img_ratio)
                
                print(f"[썸네일] 조정된 크기: {new_w}x{new_h}")
                
                # 이미지 리사이즈
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                # 썸네일 레이블 생성 및 배치
                thumbnail = tk.Label(current_frame, image=photo, bg='black')
                thumbnail.image = photo  # 참조 유지
                thumbnail.place(relx=0.5, rely=0.5, anchor='center')
                
                print("[썸네일] 3초 표시 시작")
                root.update()
                
                # 3초 대기 (0.1초 단위로 업데이트)
                for _ in range(30):
                    await asyncio.sleep(0.1)
                    root.update()
                
                print("[썸네일] 3초 표시 완료")
                thumbnail.destroy()
                img.close()
            else:
                print("[썸네일] 적합한 이미지 파일을 찾을 수 없습니다.")
                await asyncio.sleep(0.1)
        except Exception as e:
            print(f"[썸네일 오류] {str(e)}")
            traceback.print_exc()
            await asyncio.sleep(0.1)
    
    except Exception as e:
        print(f"[썸네일 오류] {str(e)}")
        traceback.print_exc()
    
    # 배경색을 다시 원래대로 변경
    current_frame.configure(bg=COLORS['background'])
    
    # 카운트다운 요소 준비 ------------------------------------------------------
    countdown_frame = tk.Frame(current_frame, bg=COLORS['background'])
    countdown_frame.place(relx=0.5, rely=0.5, anchor='center')
    
    # 로고 이미지와 카운트다운 숫자를 담을 단일 컨테이너
    # 명시적으로 단일 프레임으로 생성하여 화면 분할 방지
    container = tk.Canvas(
        countdown_frame, 
        bg=COLORS['background'],
        highlightthickness=0,  # 테두리 제거
        borderwidth=0
    )
    container.pack(padx=0, pady=0)
    
    # FLAC 로고 추가
    logo_label = None
    try:
        logo_path = SCRIPT_DIR / 'resources/images/flac_logo.jpg'
        if logo_path.exists():
            # 직접 이미지 로드하여 PhotoImage 생성
            logo_img = Image.open(logo_path)
            print(f"[로고] 원본 크기: {logo_img.size}")
            
            # 이미지 크기 조정
            scale_factor = 0.8
            new_width = int(logo_img.width * scale_factor)
            new_height = int(logo_img.height * scale_factor)
            
            # 캔버스 크기를 이미지 크기에 맞게 설정
            container.config(width=new_width, height=new_height)
            
            # 이미지 리사이징
            logo_img = logo_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # PhotoImage 생성
            logo_photo = ImageTk.PhotoImage(logo_img)
            
            # 캔버스에 이미지 직접 추가 (레이블 대신 캔버스에 이미지 표시)
            logo_image_id = container.create_image(
                new_width//2,  # x 위치 (중앙)
                new_height//2, # y 위치 (중앙)
                image=logo_photo,
                anchor='center'
            )
            # 참조 유지
            container.logo_image = logo_photo
            print(f"[로고] 로딩 성공: {new_width}x{new_height} 크기로 표시")
            
            # 카운트다운 숫자 (캔버스 위에 텍스트로 직접 표시)
            text_id = container.create_text(
                new_width//2,   # x 위치 (중앙)
                new_height//2,  # y 위치 (중앙)
                text="3",
                font=FONT_COUNTDOWN,
                fill='#FF69B4',  # 색상을 핫핑크로 변경
                anchor='center'
            )
            # 향후 업데이트를 위해 text_id 저장
            container.countdown_text_id = text_id
            
            # 카운트다운 레이블 참조를 Canvas 객체로 변경
            countdown_label = container
    except Exception as e:
        print(f"[로고 오류] {str(e)}")
        traceback.print_exc()
        
        # 로고 로드에 실패했을 경우 기본 카운트다운 레이블만 생성 (캔버스 활용)
        # 기본 크기 설정
        container.config(width=200, height=200)
        
        # 카운트다운 숫자만 캔버스에 표시
        text_id = container.create_text(
            100,  # x 위치 (중앙)
            100,  # y 위치 (중앙)
            text="3",
            font=FONT_COUNTDOWN,
            fill='#FF69B4',  # 색상을 핫핑크로 변경
            anchor='center'
        )
        container.countdown_text_id = text_id
        
        # 카운트다운 레이블 참조를 Canvas 객체로 설정
        countdown_label = container
    
    # 메시지 레이블 -----------------------------------------------------------
    message = "대충영어는 몸에 좋은 웨이브 파일을 사용합니다."  # WAV를 웨이브로 변경
    message_label = tk.Label(current_frame, font=FONT_MESSAGE,
                           fg=COLORS['pink'], bg=COLORS['background'])
    message_label.place(relx=0.5, rely=0.85, anchor='center')
    message_label.config(text="")  # 초기에는 빈 텍스트로 시작
    
    # 인트로 TTS 음성 생성 (카운트다운과 함께 재생할 준비) ----------------------
    current_repeat = int(settings.get('current_repeat', '0'))
    intro_tts_file = None
    
    # intro.wav 및 백업 파일 경로 설정
    intro_wav_file = str(SCRIPT_DIR / 'audio' / 'intro.wav')
    backup_wav_file = str(SCRIPT_DIR / 'audio' / 'intro_sunhi.wav')
    
    # intro.wav 파일이 없고 백업 파일이 있으면 복사해서 생성
    if not os.path.exists(intro_wav_file) and os.path.exists(backup_wav_file):
        try:
            import shutil
            shutil.copy2(backup_wav_file, intro_wav_file)
            print(f"[인트로] intro.wav 파일이 없어서 백업 파일에서 복사했습니다: {backup_wav_file} -> {intro_wav_file}")
        except Exception as e:
            print(f"[인트로] 백업 파일 복사 실패: {e}")
    
    if os.path.exists(intro_wav_file):
        print(f"[인트로] intro.wav 파일 발견: {intro_wav_file}")
        intro_tts_file = intro_wav_file
    elif current_repeat == 0:
        try:
            # 인트로 메시지 준비
            intro_message = "대충영어는 몸에 좋은 웨이브 파일을 사용합니다."
            
            # Edge TTS로 음성 생성 준비
            voice = 'ko-KR-SunHiNeural'  # 순희 음성
            
            # 기본 대체 파일이 있는지 확인
            if os.path.exists(backup_wav_file):
                print(f"[인트로] 대체 WAV 파일 준비됨: {backup_wav_file}")
            else:
                print("[인트로] 경고: 대체 WAV 파일이 없습니다.")
            
            # TTS 생성 시도
            temp_tts_file = "temp_intro_tts.wav"
            intro_tts_file = "temp_intro_converted.wav"
            
            # Edge TTS로 음성 생성
            communicate = edge_tts.Communicate(
                intro_message, 
                voice,
                rate='+0%'  # 기본 속도
            )
            
            # 음성 파일 생성
            await communicate.save(temp_tts_file)
            print("[인트로] TTS 파일 생성 완료")
            
            # ffmpeg로 WAV 형식 변환
            subprocess.run([
                'ffmpeg', '-y',
                '-i', temp_tts_file,
                '-acodec', 'pcm_s16le',  # 16-bit PCM
                '-ar', '44100',          # 44.1kHz
                '-ac', '2',              # stereo
                intro_tts_file
            ], check=True, capture_output=True)
            
            # 원본 TTS 파일 삭제
            if os.path.exists(temp_tts_file):
                os.remove(temp_tts_file)
            
            print("[인트로] TTS 파일 변환 완료")
            
        except Exception as e:
            print(f"[인트로] TTS 생성 및 변환 오류: {e}")
            traceback.print_exc()
            
            # 오류 발생 시 기본 WAV 파일 사용
            if os.path.exists(backup_wav_file):
                print(f"[인트로] 대체 WAV 파일 사용: {backup_wav_file}")
                intro_tts_file = backup_wav_file
            else:
                print("[인트로] 오류: 대체 WAV 파일도 없습니다.")
                intro_tts_file = None
    else:
        print(f"[인트로] 반복 학습 중 ({current_repeat}회차) - 인트로 음성 생성 생략")
    
    # 카운트다운과 타이핑 효과 실행 --------------------------------------------
    print("[카운트다운] 시작")
    
    # 음성 재생 시작 (카운트다운과 동시에)
    if intro_tts_file and os.path.exists(intro_tts_file):
        try:
            print(f"[인트로] 음성 파일 재생 시작: {intro_tts_file}")
            pygame.mixer.music.load(intro_tts_file)
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"[인트로] 음성 재생 오류: {e}")
            traceback.print_exc()
            
            # pygame 실패 시 대체 방법 시도
            try:
                print("[인트로] 대체 재생 방법 시도")
                subprocess.run([
                    'ffplay', '-autoexit', '-nodisp', '-loglevel', 'quiet',
                    intro_tts_file
                ], check=True, capture_output=True)
            except Exception as sub_e:
                print(f"[인트로] 대체 재생 방법도 실패: {sub_e}")
    else:
        print("[인트로] 재생할 음성 파일이 없습니다.")
    
    # 타이핑 효과와 카운트다운 실행
    typing_speed = len(message) / 3  # 3초 동안 전체 메시지를 표시
    message_label.config(text=message)  # 메시지를 바로 표시
    root.update()
    
    for i in range(3, 0, -1):
        # 숫자 표시
        if hasattr(countdown_label, 'countdown_text_id'):
            # 캔버스에 텍스트 업데이트
            countdown_label.itemconfig(countdown_label.countdown_text_id, text=str(i))
        else:
            # 기존 레이블 방식 (오류 시 대체)
            countdown_label.config(text=str(i))
        root.update()
        
        # 0.3초 동안만 숫자 표시
        await precise_sleep(0.6)
        
        # 숫자 숨기기
        if hasattr(countdown_label, 'countdown_text_id'):
            # 캔버스에 텍스트 숨김
            countdown_label.itemconfig(countdown_label.countdown_text_id, text="")
        else:
            # 기존 레이블 방식
            countdown_label.config(text="")
        root.update()
        
        # 남은 시간 대기 (1초 간격 유지)
        await precise_sleep(0.4)
        print(f"[카운트다운] {i}초 남음")
    
    # 최종 메시지
    message_label.config(text=message)
    root.update()
    
    # 음성 재생이 끝날 때까지 대기
    while pygame.mixer.music.get_busy():
        await precise_sleep(0.1)
    
    # 임시 파일 삭제
    try:
        if intro_tts_file and os.path.exists(intro_tts_file):
            # 기본 파일 경로 확인
            base_wav_file = str(SCRIPT_DIR / 'audio' / 'intro.wav')
            backup_wav_file = str(SCRIPT_DIR / 'audio' / 'intro_sunhi.wav')
            
            # intro_tts_file이 기본 파일이 아닌 경우에만 삭제
            if intro_tts_file != base_wav_file and intro_tts_file != backup_wav_file:
                os.remove(intro_tts_file)
                print("[인트로] 임시 파일 삭제 완료")
            else:
                print("[인트로] 기본 음원 파일 보존 (삭제하지 않음)")
    except Exception as e:
        print(f"[임시 파일 삭제 오류] {str(e)}")

async def create_audio(text, voice, speed=1.0, language=None):
    """Edge TTS를 사용하여 오디오 파일 생성"""
    try:
        # 빈 텍스트 확인
        if not text or text.strip() == "":
            print("오류: 텍스트가 비어 있습니다.")
            return None
        
        # 언어별 특수 처리
        if language == 'nepali':
            # 네팔어 처리
            print(f"네팔어 TTS 생성 시작: {text} (음성: {voice}, 속도: {speed})")
            return await create_nepali_tts(text, voice, speed)
            
        # 음성 이름 매핑
        full_voice_name = voice_mapping.get(voice, voice)
        if not full_voice_name.endswith('Neural'):
            print(f"알 수 없는 음성: {voice}")
            return None
        print(f"Edge TTS 생성 시작: {text} (음성: {full_voice_name}, 속도: {speed})")
        
        # 오디오 디렉토리 경로 설정
        audio_dir = Path(resource_path('audio'))
        if not audio_dir.exists():
            audio_dir = SCRIPT_DIR / 'audio'
            audio_dir.mkdir(parents=True, exist_ok=True)
            
        # 임시 파일명 생성
        timestamp = int(time.time()*1000)
        edge_file = audio_dir / f"edge_{timestamp}.wav"
        temp_file = audio_dir / f"temp_{timestamp}.wav"
        
        try:
            # 재시도 로직 추가
            max_retries = 3
            retry_count = 0
            success = False
            
            while retry_count < max_retries and not success:
                try:
                    if retry_count > 0:
                        print(f"Edge TTS 생성 재시도 중... ({retry_count}/{max_retries})")
                        await precise_sleep(0.5)
                    
                    # Edge TTS 생성 및 저장
                    communicate = edge_tts.Communicate(text, full_voice_name)
                    await communicate.save(str(edge_file))
                    
                    # 생성된 파일 확인
                    if edge_file.exists() and edge_file.stat().st_size > 0:
                        print(f"Edge TTS 파일 생성 완료: {edge_file}")
                        success = True
                    else:
                        print(f"Edge TTS 파일이 정상적으로 생성되지 않음: {edge_file}")
                        retry_count += 1
                        
                except edge_tts.exceptions.NoAudioReceived:
                    print(f"오류: 오디오가 수신되지 않았습니다. 재시도 {retry_count+1}/{max_retries}")
                    retry_count += 1
                    
                except Exception as e:
                    print(f"Edge TTS 생성 중 예외 발생: {e}")
                    retry_count += 1
            
            if not success:
                print(f"최대 재시도 횟수({max_retries})를 초과했습니다.")
                # 백업 음성 파일 사용
                backup_file = Path(resource_path("audio/backup_audio.wav"))
                if backup_file.exists():
                    print(f"백업 오디오 파일을 사용합니다: {backup_file}")
                    return str(backup_file)
                else:
                    print(f"백업 오디오 파일도 찾을 수 없습니다: {backup_file}")
                return None
                
            # FFmpeg로 WAV 형식 변환
            try:
                subprocess.run([
                    'ffmpeg', '-y',
                    '-i', str(edge_file),
                    '-acodec', 'pcm_s16le',
                    '-ar', '22050',  # 샘플링 레이트 낮춤
                    '-ac', '1',      # 모노 채널로 변경
                    str(temp_file)
                ], check=True, capture_output=True)
                print(f"WAV 변환 완료: {temp_file}")
            except subprocess.CalledProcessError as e:
                print(f"FFmpeg 변환 오류: {e.stderr.decode() if e.stderr else str(e)}")
                if edge_file.exists():
                    edge_file.unlink()
                return None
            
            # 원본 파일 삭제
            if edge_file.exists():
                edge_file.unlink()
            
            # 속도 조절
            if speed != 1.0:
                speed_file = audio_dir / f"speed_{timestamp}.wav"
                atempo_filters = []
                remaining_speed = speed
                
                # 배속 적용 방법 개선
                print(f"배속 처리: 요청 속도={speed}x")
                
                # 4배속 이상인 경우도 처리할 수 있도록 수정
                while remaining_speed > 2.0:
                    atempo_filters.append("atempo=2.0")
                    remaining_speed /= 2.0
                    print(f"배속 단계 적용: atempo=2.0, 남은 배속={remaining_speed}x")
                
                if remaining_speed > 1.0:
                    atempo_filters.append(f"atempo={remaining_speed:.4f}")
                    print(f"배속 단계 적용: atempo={remaining_speed:.4f}x")
                
                # 필터가 비어있으면 기본 배속 설정
                if not atempo_filters:
                    atempo_filters.append(f"atempo={speed:.4f}")
                    print(f"기본 배속 적용: atempo={speed:.4f}x")
                
                # 볼륨 조절 추가
                volume = 1.3 if not voice.startswith('ko-') else 1.0
                filter_str = ','.join(atempo_filters + [f"volume={volume}"])
                
                print(f"최종 FFmpeg 필터: {filter_str}")
                
                try:
                    subprocess.run([
                        'ffmpeg', '-y',
                        '-i', str(temp_file),
                        '-filter:a', filter_str,
                        '-acodec', 'pcm_s16le',
                        '-ar', '22050',
                        '-ac', '1',
                        str(speed_file)
                    ], check=True, capture_output=True)
                    print(f"속도 조절 완료: {speed_file} (요청 배속: {speed}x)")
                except subprocess.CalledProcessError as e:
                    print(f"FFmpeg 속도 조절 오류: {e.stderr.decode() if e.stderr else str(e)}")
                    if temp_file.exists():
                        temp_file.unlink()
                    return None
                
                # 임시 파일 삭제
                if temp_file.exists():
                    temp_file.unlink()
                
                # 속도 조절된 파일 경로 반환
                return str(speed_file)
            else:
                # 속도 조절 없이 임시 파일 경로 반환
                return str(temp_file)
            
        except Exception as e:
            print(f"오디오 처리 중 오류: {e}")
            traceback.print_exc()
            # 임시 파일들 정리
            for file in [edge_file, temp_file]:
                if isinstance(file, Path) and file.exists():
                    try:
                        file.unlink()
                    except Exception as e:
                        print(f"임시 파일 삭제 실패: {e}")
            return None
            
    except Exception as e:
        print(f"Edge TTS 생성 오류: {str(e)}")
        traceback.print_exc()
        return None

# subtitle_labels 업데이트 함수 추가
def update_subtitle_label(label, text, is_playing_audio=False):
    """자막 레이블을 안전하게 업데이트합니다."""
    try:
        # 위젯이 존재하는지 확인
        if label is None or not root or not root.winfo_exists():
            return
            
        # 이중 확인을 위한 후속 시도
        try:
            if not label.winfo_exists():
                return
        except Exception:
            # 위젯이 이미 파괴되었거나 다른 오류 발생
            return
            
        # 안전하게 위젯 업데이트
        label.config(text=text)
        
        # 자막 색상 설정
        if is_playing_audio:
            # 음성 재생 중일 때는 아이보리색으로 표시
            label.config(fg=COLORS['highlight'])  # 아이보리색
        else:
            # 음성 재생 중이 아닐 때는 초록색으로 표시
            label.config(fg=COLORS['text'])  # 초록색
    except Exception as e:
        print(f"자막 업데이트 중 오류 발생: {e}")
        # 추가 디버깅 정보
        logging.error(f"자막 업데이트 오류: {e}")

def create_break_ui(duration):
    """브레이크 화면 UI 생성"""
    global current_frame
    
    if current_frame:
        current_frame.destroy()
    
    # 브레이크 프레임 생성
    current_frame = tk.Frame(root, **STYLE['frame'])
    current_frame.pack(expand=True, fill='both')
    
    # 중앙 정렬을 위한 컨테이너 프레임
    center_frame = tk.Frame(current_frame, bg=COLORS['background'])
    center_frame.place(relx=0.5, rely=0.5, anchor='center')
    
    # 브레이크 메시지
    break_label = tk.Label(center_frame, text="Break Time", font=FONT_BREAK,
                          bg=COLORS['background'], fg=COLORS['white'])
    break_label.pack(pady=20)
    
    # 남은 시간 표시
    time_label = tk.Label(center_frame, text="", font=FONT_MESSAGE,
                         bg=COLORS['background'], fg=COLORS['white'])
    time_label.pack(pady=10)
    
    # 카운트다운 실행 (root.update() 직접 호출 대신 after 사용)
    def update_countdown(remaining):
        if remaining <= 0:
            return
            
        # 위젯이 여전히 존재하는지 확인
        try:
            if time_label.winfo_exists() and root.winfo_exists():
                time_label.config(text=f"{remaining}초")
                # 1초 후 다음 카운트다운 호출 예약
                root.after(1000, update_countdown, remaining - 1)
        except Exception as e:
            logging.error(f"카운트다운 업데이트 오류: {e}")
            
    # 카운트다운 시작
    update_countdown(duration)

async def play_vietnamese_tts(text, speed=2.0):
    try:
        start_time = time.time()
        logging.info(f"베트남어 TTS 시작: {text}")
        
        # TTS 생성 및 파일 저장 로직
        audio_path = await create_audio(text, "HoaiMy", speed, "vi-VN")
        if not audio_path:
            raise Exception("TTS 파일 생성 실패")
        
        # WAV 파일 존재 여부 확인
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"오디오 파일을 찾을 수 없음: {audio_path}")
            
        await play_sound(audio_path)
        
        current_time = time.time() - start_time
        logging.info(f"베트남어 TTS 완료. 소요 시간: {current_time:.2f}초")
        return audio_path
        
    except Exception as e:
        logging.error(f"베트남어 TTS 처리 중 오류: {str(e)}")
        logging.error(traceback.format_exc())
        show_error_popup("TTS 오류", "베트남어 TTS 처리 중 오류가 발생했습니다.")
        return None


def get_settings():
    """현재 설정값 가져오기"""
    # 기본 설정 로드
    current_settings = load_settings()
    
    # 각 순위별 볼륨 설정 로드
    try:
        first_volume = max(0, min(500, int(first_volume_var.get())))
        second_volume = max(0, min(500, int(second_volume_var.get())))
        third_volume = max(0, min(500, int(third_volume_var.get())))
    except (ValueError, NameError, AttributeError):
        # 볼륨 슬라이더가 초기화되지 않았거나 값이 없는 경우
        first_volume = int(current_settings.get('first_priority_volume', 100))
        second_volume = int(current_settings.get('second_priority_volume', 100))
        third_volume = int(current_settings.get('third_priority_volume', 100))
    
    # 자동반복 값 처리 (숫자만 허용)
    auto_repeat_val = auto_repeat_var.get()
    try:
        repeat_count = int(auto_repeat_val)
        if repeat_count < 0:
            repeat_count = 0
    except ValueError:
        repeat_count = 0
    
    # 언어 표시명을 실제 언어 코드로 변환
    display_to_lang = {v: k for k, v in LANG_DISPLAY.items()}
    
    # 1-2-3순위 언어 가져오기
    first_lang = display_to_lang.get(first_lang_cb.get(), DEFAULT_SETTINGS['first_lang'])
    second_lang = display_to_lang.get(second_lang_cb.get(), DEFAULT_SETTINGS['second_lang'])
    third_lang = display_to_lang.get(third_lang_cb.get(), DEFAULT_SETTINGS['third_lang'])
    
    # 설정값 수집
    settings = {
        'start_row': start_entry.get() or DEFAULT_SETTINGS['start_row'],
        'end_row': end_entry.get() or DEFAULT_SETTINGS['end_row'],
        'first_lang': first_lang,
        'second_lang': second_lang,
        'third_lang': third_lang,
        'first_repeat': first_repeat.get() or DEFAULT_SETTINGS['first_repeat'],
        'second_repeat': second_repeat.get() or DEFAULT_SETTINGS['second_repeat'],
        'third_repeat': third_repeat.get() or DEFAULT_SETTINGS['third_repeat'],
        
        # 각 언어별 음성 설정은 우선순위에 따라 설정
        f"{first_lang}_voice": first_voice_cb.get() or DEFAULT_SETTINGS.get(f"{first_lang}_voice", ""),
        f"{second_lang}_voice": second_voice_cb.get() or DEFAULT_SETTINGS.get(f"{second_lang}_voice", ""),
        f"{third_lang}_voice": third_voice_cb.get() or DEFAULT_SETTINGS.get(f"{third_lang}_voice", ""),
        
        # 각 언어별 음성 유형 설정
        'first_voice_type': first_voice_type.get() or 'WAV',
        'second_voice_type': second_voice_type.get() or 'WAV',
        'third_voice_type': third_voice_type.get() or 'WAV',
        
        # 각 언어별 음성 속도 설정 - 문자열 값이 수치형으로 정확히 변환되도록 처리
        f"{first_lang}_speed": first_speed.get() or DEFAULT_SETTINGS.get(f"{first_lang}_speed", "1"),
        f"{second_lang}_speed": second_speed.get() or DEFAULT_SETTINGS.get(f"{second_lang}_speed", "1"),
        f"{third_lang}_speed": third_speed.get() or DEFAULT_SETTINGS.get(f"{third_lang}_speed", "1"),
        
        # 기존 호환성을 위한 개별 언어 속도 설정
        'english_speed': first_speed.get() if first_lang == 'english' else (second_speed.get() if second_lang == 'english' else (third_speed.get() if third_lang == 'english' else DEFAULT_SETTINGS['english_speed'])),
        'korean_speed': first_speed.get() if first_lang == 'korean' else (second_speed.get() if second_lang == 'korean' else (third_speed.get() if third_lang == 'korean' else DEFAULT_SETTINGS['korean_speed'])),
        'chinese_speed': first_speed.get() if first_lang == 'chinese' else (second_speed.get() if second_lang == 'chinese' else (third_speed.get() if third_lang == 'chinese' else DEFAULT_SETTINGS['chinese_speed'])),
        'japanese_speed': first_speed.get() if first_lang == 'japanese' else (second_speed.get() if second_lang == 'japanese' else (third_speed.get() if third_lang == 'japanese' else DEFAULT_SETTINGS['japanese_speed'])),
        'vietnamese_speed': first_speed.get() if first_lang == 'vietnamese' else (second_speed.get() if second_lang == 'vietnamese' else (third_speed.get() if third_lang == 'vietnamese' else DEFAULT_SETTINGS['vietnamese_speed'])),
        'nepali_speed': first_speed.get() if first_lang == 'nepali' else (second_speed.get() if second_lang == 'nepali' else (third_speed.get() if third_lang == 'nepali' else DEFAULT_SETTINGS['nepali_speed'])),
        
        # 기존 호환성을 위한 개별 언어 음성 설정
        'eng_voice': first_voice_cb.get() if first_lang == 'english' else (second_voice_cb.get() if second_lang == 'english' else (third_voice_cb.get() if third_lang == 'english' else DEFAULT_SETTINGS['eng_voice'])),
        'kor_voice': first_voice_cb.get() if first_lang == 'korean' else (second_voice_cb.get() if second_lang == 'korean' else (third_voice_cb.get() if third_lang == 'korean' else DEFAULT_SETTINGS['kor_voice'])),
        'zh_voice': first_voice_cb.get() if first_lang == 'chinese' else (second_voice_cb.get() if second_lang == 'chinese' else (third_voice_cb.get() if third_lang == 'chinese' else DEFAULT_SETTINGS['zh_voice'])),
        'jp_voice': first_voice_cb.get() if first_lang == 'japanese' else (second_voice_cb.get() if second_lang == 'japanese' else (third_voice_cb.get() if third_lang == 'japanese' else DEFAULT_SETTINGS['jp_voice'])),
        'vn_voice': first_voice_cb.get() if first_lang == 'vietnamese' else (second_voice_cb.get() if second_lang == 'vietnamese' else (third_voice_cb.get() if third_lang == 'vietnamese' else DEFAULT_SETTINGS['vn_voice'])),
        'ne_voice': first_voice_cb.get() if first_lang == 'nepali' else (second_voice_cb.get() if second_lang == 'nepali' else (third_voice_cb.get() if third_lang == 'nepali' else DEFAULT_SETTINGS['ne_voice'])),
        
        # 기존 호환성을 위한 음성 유형
        'eng_voice_type': first_voice_type.get() if first_lang == 'english' else (second_voice_type.get() if second_lang == 'english' else (third_voice_type.get() if third_lang == 'english' else DEFAULT_SETTINGS['eng_voice_type'])),
        'kor_voice_type': first_voice_type.get() if first_lang == 'korean' else (second_voice_type.get() if second_lang == 'korean' else (third_voice_type.get() if third_lang == 'korean' else DEFAULT_SETTINGS['kor_voice_type'])),
        'zh_voice_type': first_voice_type.get() if first_lang == 'chinese' else (second_voice_type.get() if second_lang == 'chinese' else (third_voice_type.get() if third_lang == 'chinese' else DEFAULT_SETTINGS['zh_voice_type'])),
        'jp_voice_type': first_voice_type.get() if first_lang == 'japanese' else (second_voice_type.get() if second_lang == 'japanese' else (third_voice_type.get() if third_lang == 'japanese' else DEFAULT_SETTINGS['jp_voice_type'])),
        'vn_voice_type': first_voice_type.get() if first_lang == 'vietnamese' else (second_voice_type.get() if second_lang == 'vietnamese' else (third_voice_type.get() if third_lang == 'vietnamese' else DEFAULT_SETTINGS['vn_voice_type'])),
        'ne_voice_type': first_voice_type.get() if first_lang == 'nepali' else (second_voice_type.get() if second_lang == 'nepali' else (third_voice_type.get() if third_lang == 'nepali' else DEFAULT_SETTINGS['ne_voice_type'])),
        
        'spacing': spacing_entry.get().replace('초', '') or DEFAULT_SETTINGS['spacing'],
        'next_sentence_time': next_sentence_entry.get().replace('초', '') or DEFAULT_SETTINGS['next_sentence_time'],
        'keep_subtitles': keep_subtitles_var.get() or DEFAULT_SETTINGS['keep_subtitles'],
        'break_enabled': 'true' if break_interval.get() != '없음' else 'false',
        'break_interval': break_interval.get() or DEFAULT_SETTINGS['break_interval'],
        'final_music': final_music_cb.get() or DEFAULT_SETTINGS['final_music'],
        'auto_repeat': str(repeat_count),
        'auto_repeat_enabled': 'true' if repeat_count > 0 else 'false',
    }
    
    # 우선순위별 음성 및 배속 설정 값 저장 (동일 언어라도 독립 적용)
    settings['first_priority_voice'] = first_voice_cb.get()
    settings['second_priority_voice'] = second_voice_cb.get()
    settings['third_priority_voice'] = third_voice_cb.get()
    settings['first_priority_speed'] = first_speed.get()
    settings['second_priority_speed'] = second_speed.get()
    settings['third_priority_speed'] = third_speed.get()
    
    # 볼륨 설정 저장 (위에서 계산한 값 사용)
    settings['first_priority_volume'] = str(first_volume)
    settings['second_priority_volume'] = str(second_volume)
    settings['third_priority_volume'] = str(third_volume)
    
    # 볼륨 설정 로그
    print(f"볼륨 설정 - 1순위: {first_volume}%, 2순위: {second_volume}%, 3순위: {third_volume}%")
    
    # 기존 설정의 다른 값들 유지 (TTS 저장 경로 등)
    for key, value in current_settings.items():
        if key not in settings and value:
            settings[key] = value
    
    # 설정 저장
    save_settings(settings)
    
    return settings

async def start_learning_async(settings):
    """학습 과정을 비동기적으로 시작합니다."""
    global learning_started, repeat_count, current_repeat, current_frame, learning_in_progress
    
    try:
        global is_learning, lesson_start_time
        is_learning = True  # 학습 시작 시 플래그 설정
        lesson_start_time = time.time()  # 학습 시작 시간 기록
        
        # 현재 반복 횟수 초기화
        settings['current_repeat'] = '0'
        save_settings(settings)
        
        # 자동반복 설정 확인 (음수 값 방지)
        repeat_count = max(int(settings.get('auto_repeat', '0')), 0)
        
        current_repeat = 0
        # 수정: 조건문 변경 - repeat_count가 0이어도 최소 1회는 실행
        while (current_repeat == 0 or current_repeat < repeat_count) and is_learning:
            if not is_learning:  # 학습 중단 체크
                print("학습이 사용자에 의해 중단되었습니다.")
                return
                
            if current_repeat > 0:
                # 자동반복 회차 표시 수정 - 0이 아닌 실제 설정값 사용
                if repeat_count > 0:
                    print(f"\n=== 자동반복 {current_repeat}/{repeat_count} 시작 ===")
                else:
                    print(f"\n=== 자동반복 {current_repeat}회차 시작 ===")
                
                # 5초부터 1초까지 카운트다운 표시
                await show_repeat_countdown()
                
                # 학습 UI 생성
                create_learning_ui()
                root.update()
            
            # 현재 반복 횟수를 설정에 저장
            settings['current_repeat'] = str(current_repeat)
            save_settings(settings)
            
            # 문자열을 정수로 변환
            start_row = int(settings['start_row'])
            end_row = int(settings['end_row'])
            
            # 엑셀에서 문장 가져오기
            english, korean, chinese, vietnamese, japanese, nepali = get_words_from_excel(start_row, end_row)
            if not english:
                messagebox.showerror("오류", "엑셀 파일을 읽을 수 없습니다.")
                create_settings_ui()
                return
                
            # 언어별 데이터 매핑
            lang_data = {
                'english': {
                    'voice': settings.get('eng_voice', 'Jenny'),
                    'speed': float(settings.get('english_speed', '1.0')) if settings.get('english_speed') else 1.0
                },
                'korean': {
                    'voice': settings.get('kor_voice', 'SunHi'),
                    'speed': float(settings.get('korean_speed', '1.0')) if settings.get('korean_speed') else 1.0
                },
                'chinese': {
                    'voice': settings.get('zh_voice', 'Xiaoxiao'),
                    'speed': float(settings.get('chinese_speed', '1.0')) if settings.get('chinese_speed') else 1.0
                },
                'japanese': {
                    'voice': settings.get('jp_voice', 'Nanami'),
                    'speed': float(settings.get('japanese_speed', '1.0')) if settings.get('japanese_speed') else 1.0
                },
                'vietnamese': {
                    'voice': settings.get('vn_voice', 'HoaiMy'),
                    'speed': float(settings.get('vietnamese_speed', '2.0')) if settings.get('vietnamese_speed') else 2.0
                },
                'nepali': {
                    'voice': settings.get('ne_voice', 'DefaultNepaliVoice'),
                    'speed': float(settings.get('nepali_speed', '1.0')) if settings.get('nepali_speed') else 1.0
                }
            }
            
            # 1-2-3순위별 언어 속성 설정 (순위별로 독립적으로 저장)
            rank_lang_data = {
                'first': {
                    'lang': settings['first_lang'],
                    'voice': settings.get('first_priority_voice', DEFAULT_SETTINGS.get(f"{settings['first_lang']}_voice", "")),
                    'speed': float(settings.get('first_priority_speed', DEFAULT_SETTINGS.get(f"{settings['first_lang']}_speed", "1"))),
                    'volume': int(settings.get('first_priority_volume', "100"))
                },
                'second': {
                    'lang': settings['second_lang'],
                    'voice': settings.get('second_priority_voice', DEFAULT_SETTINGS.get(f"{settings['second_lang']}_voice", "")),
                    'speed': float(settings.get('second_priority_speed', DEFAULT_SETTINGS.get(f"{settings['second_lang']}_speed", "1"))),
                    'volume': int(settings.get('second_priority_volume', "100"))
                },
                'third': {
                    'lang': settings['third_lang'],
                    'voice': settings.get('third_priority_voice', DEFAULT_SETTINGS.get(f"{settings['third_lang']}_voice", "")),
                    'speed': float(settings.get('third_priority_speed', DEFAULT_SETTINGS.get(f"{settings['third_lang']}_speed", "1"))),
                    'volume': int(settings.get('third_priority_volume', "100"))
                }
            }

            # 배속 및 볼륨 디버깅 로그 추가
            print("\n[배속 및 볼륨 설정 확인]")
            print(f"1순위({settings['first_lang']}): {rank_lang_data['first']['speed']}배속, {rank_lang_data['first']['volume']}% 볼륨")
            print(f"2순위({settings['second_lang']}): {rank_lang_data['second']['speed']}배속, {rank_lang_data['second']['volume']}% 볼륨")
            print(f"3순위({settings['third_lang']}): {rank_lang_data['third']['speed']}배속, {rank_lang_data['third']['volume']}% 볼륨")
            
            total_sentences = len(english)
            start_time = time.time()
            sentence_times = []
            break_interval_value = settings.get('break_interval', '없음')
            break_interval = 0 if break_interval_value == '없음' else int(break_interval_value)
            break_enabled = settings.get('break_enabled', 'true') == 'true'
            
            # 학습 설정 로깅 순서 정의
            setting_order = [
                # 기본 설정
                'start_row', 'end_row',
                
                # 언어 설정
                'first_lang', 'second_lang', 'third_lang',
                'first_repeat', 'second_repeat', 'third_repeat',
                
                # 음성 설정
                'eng_voice', 'kor_voice', 'zh_voice', 'jp_voice', 'vn_voice',
                
                # 음성 타입 설정
                'eng_voice_type', 'kor_voice_type', 'zh_voice_type', 'jp_voice_type', 'vn_voice_type',
                
                # 속도 설정
                'english_speed', 'korean_speed', 'chinese_speed', 
                'japanese_speed', 'vietnamese_speed',  # 일본어, 베트남어 속도 추가
                
                # 기타 설정
                'spacing', 'next_sentence_time',
                'keep_subtitles', 'break_enabled', 'break_interval',
                'final_music', 'auto_repeat', 'auto_repeat_enabled'
            ]
            
            print("\n=== 학습 설정 저장됨 ===")
            
            # 설정값 그룹화하여 출력
            print("\n[ 기본 설정 ]")
            print(f"시작 번호: {settings.get('start_row')}")
            print(f"종료 번호: {settings.get('end_row')}")
            
            print("\n[ 언어 설정 ]")
            print(f"1순위: {settings.get('first_lang')} ({settings.get('first_repeat')}회)")
            print(f"2순위: {settings.get('second_lang')} ({settings.get('second_repeat')}회)")
            print(f"3순위: {settings.get('third_lang')} ({settings.get('third_repeat')}회)")
            
            print("\n[ 음성 설정 ]")
            print(f"영어: {settings.get('eng_voice')} ({settings.get('eng_voice_type')}, {settings.get('english_speed')}배속)")
            print(f"한국어: {settings.get('kor_voice')} ({settings.get('kor_voice_type')}, {settings.get('korean_speed')}배속)")
            print(f"중국어: {settings.get('zh_voice')} ({settings.get('zh_voice_type')}, {settings.get('chinese_speed')}배속)")
            print(f"일본어: {settings.get('jp_voice')} ({settings.get('jp_voice_type')}, {settings.get('japanese_speed')}배속)")
            print(f"베트남어: {settings.get('vn_voice')} ({settings.get('vn_voice_type')}, {settings.get('vietnamese_speed')}배속)")
            print(f"네팔어: {settings.get('ne_voice')} ({settings.get('ne_voice_type')}, {settings.get('nepali_speed')}배속)")
            
            print("\n[ 기타 설정 ]")
            print(f"문장 간격: {settings.get('spacing')}초")
            print(f"다음 문장: {settings.get('next_sentence_time')}초")
            print(f"동시 자막: {settings.get('keep_subtitles')}")
            print(f"브레이크: {settings.get('break_enabled')} ({settings.get('break_interval')}문장)")
            print(f"힐링뮤직: {settings.get('final_music')}")
            print(f"자동반복: {settings.get('auto_repeat_enabled')} ({settings.get('auto_repeat')}회)")
            
            # 실제 재생될 음성 정보 수집
            active_voices = []
            if int(settings['first_repeat']) > 0:
                first_lang = settings['first_lang']
                active_voices.append(f"{LANG_DISPLAY[first_lang]} {settings.get(first_lang + '_speed', '2.0')}배속")
            if int(settings['second_repeat']) > 0:
                second_lang = settings['second_lang']
                active_voices.append(f"{LANG_DISPLAY[second_lang]} {settings.get(second_lang + '_speed', '2.0')}배속")
            if int(settings['third_repeat']) > 0:
                third_lang = settings['third_lang']
                if third_lang == 'vietnamese':
                    active_voices.append(f"{LANG_DISPLAY[third_lang]} {settings.get('vietnamese_speed', '2.0')}배속")
                else:
                    active_voices.append(f"{LANG_DISPLAY[third_lang]} {settings.get(third_lang + '_speed', '2.0')}배속")

            # 실제 재생될 음성 정보만 로깅
            print("\n[ 실제 재생될 음성 ]")
            print(" • ".join(active_voices))
            print("\n=====================\n")
            
            # speed_label을 전역 변수로 선언
            global speed_label
            if 'speed_label' not in globals():
                speed_label = None
                
            # 하단 중앙에 배속 정보 표시
            if speed_label and speed_label.winfo_exists():
                speed_label.config(text=" • ".join(active_voices))
            
            # 각 문장별 학습
            for i, (eng, kor, chn, vie, jpn, nep) in enumerate(zip(english, korean, chinese, vietnamese, japanese, nepali)):
                if not is_learning:  # 학습 중단 체크
                    return
                    
                # 브레이크 체크 (인덱스 1부터 시작, break_interval 간격으로)
                if break_enabled and i > 0 and (i) % break_interval == 0:
                    current_total_time = time.time() - start_time
                    await show_break_screen(5)
                    start_time += 5  # 브레이크 시간 보정
                    create_learning_ui()
                    root.update()
                
                excel_row = start_row + i
                sentence_start_time = time.time()
                
                # 진행 상황 업데이트
                try:
                    if progress_label and progress_label.winfo_exists():
                        progress_label.config(text=f"{excel_row:03d}")
                    
                    # 시간 업데이트 - 문장당 1회만
                    elapsed_time = time.time() - start_time
                    if total_time_label and total_time_label.winfo_exists():
                        minutes = int(elapsed_time // 60)
                        seconds = int(elapsed_time % 60)
                        total_time_label.config(text=f"{minutes:02d}분{seconds:02d}초")
                    if avg_time_label and avg_time_label.winfo_exists() and sentence_times:
                        avg = sum(sentence_times) / len(sentence_times)
                        avg_time_label.config(text=f"time = {avg:.1f}초")
                except Exception as e:
                    print(f"위젯 업데이트 중 오류 발생: {e}")
                    pass
                root.update()
                
                # 언어 순서대로 자막 표시 및 음성 재생
                texts = {
                    'english': eng, 
                    'korean': kor, 
                    'chinese': chn,
                    'japanese': jpn,
                    'vietnamese': vie,
                    'nepali': nep
                }
                langs_in_settings = [settings['first_lang'], settings['second_lang'], settings['third_lang']]
                
                # 자막 표시를 위한 고유 언어 및 해당 레이블 위치 결정
                unique_lang_positions = {}
                # subtitle_labels의 수만큼만 레이블 위치를 할당하기 위함
                available_label_indices = list(range(len(subtitle_labels))) 
                
                temp_seen_langs_for_pos = set()
                for lang_in_order in langs_in_settings:
                    if lang_in_order != 'none' and lang_in_order not in temp_seen_langs_for_pos:
                        if available_label_indices: # 할당할 레이블이 남아있는 경우
                            label_idx_to_assign = available_label_indices.pop(0) # 가장 앞 순서의 레이블부터 사용
                            unique_lang_positions[lang_in_order] = label_idx_to_assign
                            temp_seen_langs_for_pos.add(lang_in_order)

                # 모든 자막 라벨 초기화 (텍스트 지우고 초록색으로)
                for label_widget in subtitle_labels: # 모든 레이블 위젯에 대해
                    update_subtitle_label(label_widget, "", is_playing_audio=False)
                root.update()
                
                # 동시 자막 모드
                if settings.get('keep_subtitles', 'true') == 'true':
                    current_time = time.time() - start_time
                    for lang, position in unique_lang_positions.items():
                        if lang in texts and position < len(subtitle_labels):
                            print(format_log(current_time, '자막', lang, '', texts[lang]))
                            update_subtitle_label(subtitle_labels[position], texts[lang], is_playing_audio=False)
                    root.update()
                    # await precise_sleep(float(settings['subtitle_delay'])) # 삭제됨 - subtitle_delay 설정 자체가 없어짐
                
                # 각 순위별 언어 처리 (순차 자막 모드 포함)
                for rank_idx, current_processing_lang_key in enumerate(['first', 'second', 'third']):
                    current_processing_lang = settings[f'{current_processing_lang_key}_lang']
                    if current_processing_lang == 'none':
                        # 'none'인 경우에도 다음 언어가 있다면 문장 간격을 적용해야 할 수 있음
                        if rank_idx < 2: # 마지막 순위가 아니라면
                             await precise_sleep(float(settings['spacing']))
                        continue

                    current_text_to_process = texts.get(current_processing_lang, "")
                    current_repeat_count = int(settings[f'{current_processing_lang_key}_repeat'])
                    # 베트남어, 네팔어는 TTS 함수 내부에서 재생하므로 is_audio_for_current에서 직접 WAV/TTS 구분 불필요
                    is_audio_for_current = current_repeat_count > 0

                    target_label_idx = -1
                    if current_processing_lang in unique_lang_positions:
                        target_label_idx = unique_lang_positions[current_processing_lang]

                    # 순차 자막 모드에서 자막 표시/강조
                    if settings.get('keep_subtitles', 'true') != 'true':
                        if target_label_idx != -1 and target_label_idx < len(subtitle_labels):
                            # 현재 처리 중인 언어의 자막만 업데이트, 나머지는 그대로 둠
                            update_subtitle_label(subtitle_labels[target_label_idx], current_text_to_process, is_playing_audio=is_audio_for_current)
                        root.update()
                        if is_audio_for_current: # 음성 재생이 있다면 자막 표시 후 딜레이
                            # await precise_sleep(float(settings['subtitle_delay'])) # 삭제됨
                            pass # subtitle_delay가 삭제되었으므로 추가 지연 없음
                    
                    # 음성 재생 로직
                    if is_audio_for_current:
                        # 동시 자막 모드이거나, 순차 자막 모드에서 이미 강조된 경우라도, 재생 직전 확실히 강조
                        if target_label_idx != -1 and target_label_idx < len(subtitle_labels):
                            update_subtitle_label(subtitle_labels[target_label_idx], current_text_to_process, is_playing_audio=True)
                        root.update()

                        voice_type = settings.get(f'{current_processing_lang_key}_voice_type', 'WAV') # 기본 WAV
                        # rank_lang_data에서 해당 순위의 음성, 속도, 볼륨 가져오기
                        current_rank_data = rank_lang_data[current_processing_lang_key]
                        lang_voice = current_rank_data['voice']
                        lang_speed = float(current_rank_data['speed'])
                        lang_volume = int(current_rank_data['volume'])

                        for _ in range(current_repeat_count):
                            if current_processing_lang == 'vietnamese':
                                # play_vietnamese_tts는 내부적으로 create_audio -> play_sound(play_audio)를 호출함
                                # play_audio에 볼륨 전달 필요
                                audio_file_vn = await create_audio(current_text_to_process, lang_voice, lang_speed, language='vietnamese')
                                if audio_file_vn:
                                    play_audio(audio_file_vn, volume=lang_volume)
                                    if os.path.exists(audio_file_vn): os.remove(audio_file_vn)
                            elif current_processing_lang == 'nepali':
                                audio_file_ne = await create_nepali_tts(current_text_to_process, lang_voice, lang_speed)
                                if audio_file_ne:
                                    play_audio(audio_file_ne, volume=lang_volume)
                                    if os.path.exists(audio_file_ne): os.remove(audio_file_ne)
                            elif voice_type == 'WAV':
                                success = play_wav_file(current_processing_lang, lang_voice, excel_row, settings, start_time, current_text_to_process)
                                if not success: # WAV 실패 시 TTS
                                    audio_file = await create_audio(current_text_to_process, lang_voice, lang_speed)
                                    if audio_file:
                                        play_audio(audio_file, volume=lang_volume)
                                        if os.path.exists(audio_file): os.remove(audio_file)
                            else:  # TTS
                                audio_file = await create_audio(current_text_to_process, lang_voice, lang_speed)
                                if audio_file:
                                    play_audio(audio_file, volume=lang_volume)
                                    if os.path.exists(audio_file): os.remove(audio_file)
                        
                        # 음성 재생 후 자막 색상 복원 (초록색)
                        if target_label_idx != -1 and target_label_idx < len(subtitle_labels):
                            update_subtitle_label(subtitle_labels[target_label_idx], current_text_to_process, is_playing_audio=False)
                        root.update()

                    # 현재 순위 처리 후 다음 순위 언어가 있다면 문장 간격 적용
                    if rank_idx < 2: # 0 (1순위), 1 (2순위) 처리 후. 2 (3순위) 후에는 간격 없음.
                         await precise_sleep(float(settings['spacing']))
                
                # 문장 소요 시간 기록
                sentence_time = time.time() - sentence_start_time
                sentence_times.append(sentence_time)
                
                # 다음 문장 처리
                if i < total_sentences - 1:
                    # 다음 문장 대기 (중복 적용 제거)
                    # 다음 문장 시간만 적용하고, 문장 간격은 아래에서 적용
                    # await asyncio.sleep(float(settings['next_sentence_time']))
                    # await asyncio.sleep(float(settings['spacing']))
                    pass
                else:
                    # 마지막 문장 처리
                    # 마지막 문장에만 다음 문장 시간 적용
                    await precise_sleep(float(settings['next_sentence_time']))
                    
                    # 자막 초기화
                    for label in subtitle_labels:
                        update_subtitle_label(label, "", is_playing_audio=False)  # 음성 비재생 언어:false
                    root.update()
                    
                    # 통계 표시 전 상태 저장
                    final_total_time = time.time() - start_time
                    final_avg_time = sum(sentence_times) / len(sentence_times) if sentence_times else 0
                    
                    # 현재 반복 횟수 증가
                    current_repeat += 1
                    # 반복 횟수를 설정에 저장
                    settings['current_repeat'] = str(current_repeat)
                    save_settings(settings)
                    
                    # 다음 반복이 아직 남아있다면 계속 진행
                    if current_repeat < repeat_count:
                        print(f"\n--- 다음 반복 {current_repeat}/{repeat_count} 준비 중... ---")
                        await precise_sleep(3)
                        # 다음 반복을 위해 UI 초기화
                        if current_frame:
                            current_frame.destroy()
                        current_frame = tk.Frame(root, bg=COLORS['background'])
                        current_frame.pack(fill='both', expand=True)
                        
                        # 로딩 메시지 표시
                        loading_label = tk.Label(current_frame, text="다음 반복 준비 중...", 
                                                font=("Helvetica", 24, "bold"),
                                                bg=COLORS['background'], fg=COLORS['text'])
                        loading_label.pack(expand=True)
                        root.update()
                        
                        await asyncio.sleep(1)
                        create_learning_ui()
                        root.update()
                        continue
                    else:
                        # 마지막 반복이 끝났을 때 통계 표시
                        # 결과 데이터프레임 생성 (학습 결과를 통계용 데이터프레임으로 변환)
                        result_df = pd.DataFrame({
                            'index': list(range(1, len(sentence_times) + 1)),
                            'sentence': english[:len(sentence_times)],
                            'time': sentence_times,
                            'correct': [1] * len(sentence_times)  # 기본적으로 모든 문장을 정답으로 처리
                        })
                        
                        # 업그레이드된 통계 화면 표시
                        show_statistics(result_df)
            
            # 문장 간격 적용
            if excel_row < end_row:  # 마지막 문장이 아닐 경우에만 간격 적용
                # 정확한 시간 적용을 위해 실수형으로 변환하고 정확성 확보
                spacing_time = float(settings['spacing'])
                current_time = time.time() - start_time
                print(f"[{format_time_with_ms(current_time)}] 문장 간격: {spacing_time}초")
                
                # 정확한 딜레이를 위한 시간 측정 시작
                delay_start = time.time()
                await precise_sleep(spacing_time)
                actual_delay = time.time() - delay_start
                print(f"실제 적용된 문장 간격: {actual_delay:.3f}초")
                
                # 다음 문장 시간 적용
                next_sentence_time = float(settings['next_sentence_time'])
                current_time = time.time() - start_time
                print(f"[{format_time_with_ms(current_time)}] 다음 문장 대기: {next_sentence_time}초")
                
                # 정확한 딜레이를 위한 시간 측정 시작
                delay_start = time.time()
                await precise_sleep(next_sentence_time)
                actual_delay = time.time() - delay_start
                print(f"실제 적용된 다음 문장 대기: {actual_delay:.3f}초")
            
            # 다음 문장으로 넘어가기 전 자막 초기화 (자막 유지 옵션이 false일 경우)
            if settings['keep_subtitles'] != 'true':
                for label in subtitle_labels:
                    update_subtitle_label(label, "", is_playing_audio=False)  # 음성 비재생 언어:false
                root.update()
            
    except Exception as e:
        logging.error(f"학습 진행 중 오류 발생: {str(e)}")
        logging.error(traceback.format_exc())
        show_error_popup("학습 오류", "학습 진행 중 예상치 못한 오류가 발생했습니다.")
    finally:
        is_learning = False  # 학습 종료 시 플래그 해제
        # 재생 중인 오디오 정지
        try:
            pygame.mixer.music.stop()
        except:
            pass

def play_wav_file(lang, voice, index, settings, start_time=None, text=""):
    """WAV 파일 직접 재생"""
    try:
        # 언어 코드 가져오기 (전역 LANGUAGE_CODES 사용)
        lang_code = LANGUAGE_CODES.get(lang.lower(), lang.lower())
        
        # 배속 설정 가져오기 - 언어가 어떤 순위인지 확인하여 해당 순위의 배속 사용
        speed = 1.0
        volume = 100  # 기본 볼륨 값
        first_lang = settings.get('first_lang')
        second_lang = settings.get('second_lang')
        third_lang = settings.get('third_lang')

        # 순위별 언어와 일치하는지 확인하여 해당 순위의 배속 및 볼륨 적용
        if lang == first_lang:
            speed = float(settings.get("first_priority_speed", settings.get(f"{lang}_speed", 1.0)))
            volume = int(settings.get("first_priority_volume", 100))
            print(f"1순위 언어 배속 적용: {speed}x, 볼륨: {volume}% ({lang})")
        elif lang == second_lang:
            speed = float(settings.get("second_priority_speed", settings.get(f"{lang}_speed", 1.0)))
            volume = int(settings.get("second_priority_volume", 100))
            print(f"2순위 언어 배속 적용: {speed}x, 볼륨: {volume}% ({lang})")
        elif lang == third_lang:
            speed = float(settings.get("third_priority_speed", settings.get(f"{lang}_speed", 1.0)))
            volume = int(settings.get("third_priority_volume", 100))
            print(f"3순위 언어 배속 적용: {speed}x, 볼륨: {volume}% ({lang})")
        else:
            # 기존 방식 (fallback)
            speed_key = f"{lang}_speed"
            speed = float(settings.get(speed_key, 1.0))
            print(f"기본 배속 적용: {speed}x, 볼륨: {volume}% ({lang})")
        
        # 음성 이름 포맷팅 (첫 글자 대문자, 나머지 소문자)
        voice_proper = voice[0].upper() + voice[1:].lower() if voice else ""
        voice_lower = voice.lower() if voice else ""
        
        # 언어 코드 변환 - 전체 이름은 첫 글자 대문자로
        lang_proper = lang[0].upper() + lang[1:].lower() if lang else ""
        
        # 로그 출력 (디버깅용)
        print(f"WAV 파일 검색 - 언어: {lang_proper} ({lang_code}), 음성: {voice_proper}, 인덱스: {index}, 배속: {speed}x")
        
        # 파일 경로 후보 목록 (우선순위 순)
        file_paths = [
            # 1. 사용자가 요청한 경로 구조: audio/en/Steffan/en1.wav
            resource_path(f"audio/{lang_code}/{voice_proper}/{lang_code}{index}.wav"),
            
            # 2. 대체 경로: 소문자 음성명 사용
            resource_path(f"audio/{lang_code}/{voice_lower}/{lang_code}{index}.wav"),
            
            # 3. 대체 경로: 파일명 형식만 다른 경우
            resource_path(f"audio/{lang_code}/{voice_proper}/{index}.wav"),
            resource_path(f"audio/{lang_code}/{voice_lower}/{index}.wav"),
            
            # 4. 대체 경로: 언어가 소문자가 아닌 첫 글자 대문자로 된 경우
            resource_path(f"audio/{lang_proper}/{voice_proper}/{lang_code}{index}.wav"),
            resource_path(f"audio/{lang_proper}/{voice_lower}/{lang_code}{index}.wav"),
            resource_path(f"audio/{lang_proper}/{voice_proper}/{index}.wav"),
            resource_path(f"audio/{lang_proper}/{voice_lower}/{index}.wav"),
            
            # 5. 대체 경로: 언어 폴더 없이 직접 음성 폴더에 있는 경우
            resource_path(f"audio/{voice_proper}/{lang_code}{index}.wav"),
            resource_path(f"audio/{voice_lower}/{lang_code}{index}.wav"),
            resource_path(f"audio/{voice_proper}/{index}.wav"),
            resource_path(f"audio/{voice_lower}/{index}.wav"),
            
            # 6. 대체 경로: 음성 폴더 없이 언어 폴더에 직접 있는 경우 
            resource_path(f"audio/{lang_code}/{lang_code}{index}.wav"),
            resource_path(f"audio/{lang_proper}/{lang_code}{index}.wav"),
            resource_path(f"audio/{lang_code}/{index}.wav"),
            resource_path(f"audio/{lang_proper}/{index}.wav"),
            
            # 7. 대체 경로: audio 폴더 바로 아래 있는 경우
            resource_path(f"audio/{lang_code}{index}.wav"),
            resource_path(f"audio/{lang_proper}_{index}.wav"),
            resource_path(f"audio/{voice_proper}_{index}.wav"),
            resource_path(f"audio/{voice_lower}_{index}.wav"),
            resource_path(f"audio/{index}.wav"),
            
            # 8. 대체 경로: 조합 형식
            resource_path(f"audio/{lang_code}_{voice_proper}/{lang_code}{index}.wav"),
            resource_path(f"audio/{lang_code}_{voice_lower}/{lang_code}{index}.wav"),
            resource_path(f"audio/{lang_proper}_{voice_proper}/{lang_code}{index}.wav"),
            resource_path(f"audio/{lang_proper}_{voice_lower}/{lang_code}{index}.wav"),
            
            # 9. 기존 경로(하위 호환성 유지)
            resource_path(f"resources/audio/{lang_code}/{voice_proper}/{lang_code}{index}.wav"),
            resource_path(f"resources/audio/{lang_code}/{voice_lower}/{lang_code}{index}.wav")
        ]
        
        # WAV 파일이 존재하는지 확인
        wav_exists = False
        found_path = None
        
        # 모든 경로 시도
        for i, path in enumerate(file_paths):
            if os.path.exists(path):
                wav_exists = True
                found_path = path
                print(f"WAV 파일 발견: {path}")
                break
        
        # WAV 파일이 없으면 False 반환
        if not wav_exists:
            print(f"파일이 존재하지 않음: {file_paths[0]}")
            print("백업 오디오 파일도 찾을 수 없습니다.")
            return False
                
        # 배속 처리
        if speed != 1.0:
            try:
                print(f"배속 적용: {speed}x")
                # 파일 읽기
                data, sample_rate = sf.read(found_path)
                
                # 배속 적용
                output_path = resource_path(f"temp/temp_speed_{int(time.time())}.wav")
                y_stretched = pyrb.time_stretch(data, sample_rate, speed)
                sf.write(output_path, y_stretched, sample_rate)
                
                # 배속 정보 표시 업데이트
                update_speed_info(lang, speed)
                
                # 배속된 파일 재생 (볼륨 적용)
                result = play_audio(output_path, volume=volume)
                
                # 임시 파일 삭제
                try:
                    os.remove(output_path)
                except:
                    pass
                    
                if result:
                    print(f"배속된 WAV 파일: {found_path} ({speed}x)")
                    return True
                else:
                    print(f"배속된 WAV 파일 재생 실패: {found_path}")
                    return False
            except Exception as e:
                print(f"배속 처리 오류: {e}")
                # 배속 실패 시 원본 파일 재생 시도
                print("원본 파일로 재생 시도")
        
        # 배속이 필요없는 경우 원본 파일 바로 재생
        # 배속 정보 표시 업데이트
        update_speed_info(lang, speed)
        
        # 재생 시도 (볼륨 적용)
        result = play_audio(found_path, volume=volume)
        if result:
            print(f"WAV 파일 재생 성공: {found_path}")
            return True
        else:
            print(f"WAV 파일 재생 실패: {found_path}")
            return False
    except Exception as e:
        print(f"오디오 재생 오류: {e}")
        traceback.print_exc()
        return False
    
async def show_break_screen(duration):
    """비동기 방식으로 브레이크 화면을 표시합니다."""
    create_break_ui(duration)
    await precise_sleep(duration)

async def create_nepali_tts(text, voice="Sagar", speed=1.0):
    """네팔어 TTS 생성 (Edge TTS 사용)"""
    try:
        # 빈 텍스트 확인
        if not text or text.strip() == "":
            print("오류: 네팔어 텍스트가 비어 있습니다.")
            return None
        
        # 음성 선택 (VOICE_MAPPING에서 네팔어 음성 가져오기)
        full_voice_name = VOICE_MAPPING['nepali'].get(voice, 'ne-NP-SagarNeural')
        print(f"네팔어 TTS 생성 중: {text} (음성: {full_voice_name}, 속도: {speed})")
        
        # 오디오 디렉토리 경로 설정
        audio_dir = Path(resource_path('temp'))
        if not audio_dir.exists():
            audio_dir = SCRIPT_DIR / 'temp'
            audio_dir.mkdir(parents=True, exist_ok=True)
            
        # 임시 파일명 생성
        timestamp = int(time.time()*1000)
        edge_file = audio_dir / f"ne_edge_{timestamp}.wav"
        temp_file = audio_dir / f"ne_temp_{timestamp}.wav"
        
        # Edge TTS 생성 및 저장
        try:
            communicate = edge_tts.Communicate(text, full_voice_name)
            await communicate.save(str(edge_file))
            
            # 생성된 파일 확인
            if not edge_file.exists() or edge_file.stat().st_size <= 0:
                print(f"네팔어 TTS 파일이 정상적으로 생성되지 않음: {edge_file}")
                return None
                
            print(f"네팔어 TTS 파일 생성 완료: {edge_file}")
            
            # FFmpeg로 WAV 형식 변환
            try:
                subprocess.run([
                    'ffmpeg', '-y',
                    '-i', str(edge_file),
                    '-acodec', 'pcm_s16le',
                    '-ar', '22050',  # 샘플링 레이트
                    '-ac', '1',      # 모노 채널로 변경
                    str(temp_file)
                ], check=True, capture_output=True)
                print(f"네팔어 WAV 변환 완료: {temp_file}")
            except subprocess.CalledProcessError as e:
                print(f"네팔어 FFmpeg 변환 오류: {e.stderr.decode() if e.stderr else str(e)}")
                if edge_file.exists():
                    edge_file.unlink()
                return None
            
            # 원본 파일 삭제
            if edge_file.exists():
                edge_file.unlink()
            
            # 속도 조절
            if speed != 1.0:
                speed_file = audio_dir / f"ne_speed_{timestamp}.wav"
                atempo_filters = []
                remaining_speed = speed
                
                while remaining_speed > 2.0:
                    atempo_filters.append("atempo=2.0")
                    remaining_speed /= 2.0
                
                if remaining_speed != 1.0:
                    atempo_filters.append(f"atempo={remaining_speed}")
                
                filter_str = ','.join(atempo_filters)
                
                try:
                    subprocess.run([
                        'ffmpeg', '-y',
                        '-i', str(temp_file),
                        '-filter:a', filter_str,
                        '-acodec', 'pcm_s16le',
                        '-ar', '22050',
                        '-ac', '1',
                        str(speed_file)
                    ], check=True, capture_output=True)
                    print(f"네팔어 속도 조절 완료: {speed_file}")
                except subprocess.CalledProcessError as e:
                    print(f"네팔어 FFmpeg 속도 조절 오류: {e.stderr.decode() if e.stderr else str(e)}")
                    if temp_file.exists():
                        temp_file.unlink()
                    return None
                
                # 임시 파일 삭제
                if temp_file.exists():
                    temp_file.unlink()
                
                # 속도 조절된 파일 경로 반환
                return str(speed_file)
            else:
                # 속도 조절 없이 임시 파일 경로 반환
                return str(temp_file)
            
        except Exception as e:
            print(f"네팔어 오디오 처리 중 오류: {e}")
            traceback.print_exc()
            # 임시 파일들 정리
            for file in [edge_file, temp_file]:
                if isinstance(file, Path) and file.exists():
                    try:
                        file.unlink()
                    except Exception as e:
                        print(f"네팔어 임시 파일 삭제 실패: {e}")
            return None
            
    except Exception as e:
        print(f"네팔어 TTS 생성 오류: {str(e)}")
        traceback.print_exc()
        return None

def play_audio(file_path, volume=100):
    """음성 파일 재생 (볼륨 조절 기능 추가)"""
    try:
        print(f"오디오 재생 요청: {file_path}, 볼륨: {volume}%")
        if isinstance(file_path, bool):
            print("파일 경로가 bool 타입으로 전달됨")
            return False
            
        # 파일 경로 정규화 (상대 경로 -> 절대 경로)
        if file_path and not os.path.isabs(file_path):
            # resource_path 함수를 통해 절대 경로 변환 시도
            try:
                abs_path = resource_path(file_path)
                if os.path.exists(abs_path):
                    file_path = abs_path
            except:
                pass
            
        # 파일 존재 여부 확인
        if not file_path or not os.path.exists(file_path):
            print(f"파일이 존재하지 않음: {file_path}")
            
            # 파일 확장자 변경 시도 (.wav -> .mp3 또는 그 반대)
            if file_path:
                base_path, ext = os.path.splitext(file_path)
                alt_exts = ['.wav', '.mp3', '.ogg']
                for alt_ext in alt_exts:
                    if alt_ext != ext:
                        alt_path = base_path + alt_ext
                        if os.path.exists(alt_path):
                            print(f"대체 파일 발견: {alt_path}")
                            file_path = alt_path
                            break
            
            # 여전히 파일이 없으면 백업 오디오 사용
            if not os.path.exists(file_path):
                # 백업 오디오 파일 사용 시도
                backup_paths = [
                    Path(resource_path("resources/backup_audio.wav")),
                    Path(resource_path("resources/audio/backup_audio.wav")),
                    Path(resource_path("resources/sounds/backup_audio.wav")),
                    Path(resource_path("resources/backup_audio.wav"))
                ]
                
                for backup_file in backup_paths:
                    if backup_file.exists():
                        print(f"백업 오디오 파일을 사용합니다: {backup_file}")
                        file_path = str(backup_file)
                        break
                else:
                    print("백업 오디오 파일도 찾을 수 없습니다.")
                    return False
            
        # pygame 초기화 확인
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=44100)
                print("Pygame 믹서 초기화됨")
            except Exception as e:
                print(f"Pygame 믹서 초기화 실패: {e}")
                try:
                    pygame.mixer.init(44100, -16, 2, 2048)
                    print("대체 설정으로 pygame.mixer 초기화 성공")
                except Exception as e:
                    print(f"모든 pygame.mixer 초기화 방법 실패: {e}")
                    return False
            
        print(f"오디오 재생 시도: {file_path}")
        
        # 재생 시도 방법 1: pygame.mixer.Sound
        try:
            sound = pygame.mixer.Sound(file_path)
            # 볼륨 설정 적용 (0-500% -> 0.0-5.0) - 두 가지 방법으로 보강
            volume_normalized = max(0, min(volume, 500)) / 100.0
            
            # 방법 1: 기본 볼륨 설정
            sound.set_volume(volume_normalized)
            
            # 방법 2: 오디오 데이터 직접 증폭 시도 (pygame 2.0 이상에서만 가능)
            try:
                # 버퍼 복사본 추출 및 증폭 후 sound 객체에 적용 시도
                if volume > 100 and hasattr(sound, 'get_raw'):
                    array_sample = pygame.sndarray.array(sound)
                    # 100% 초과분에 대해 추가 증폭 (1.0 이상 부분만)
                    extra_boost = (volume_normalized - 1.0) * 0.5 + 1.0 if volume_normalized > 1.0 else 1.0
                    # 클리핑을 방지하면서 증폭
                    array_sample = array_sample * extra_boost
                    new_sound = pygame.sndarray.make_sound(array_sample)
                    sound = new_sound
            except Exception as e:
                print(f"고급 볼륨 증폭 적용 실패 (무시해도 됨): {e}")
                
            print(f"볼륨 적용(강화): {volume}% ({volume_normalized:.2f})")
            sound.play()
            while pygame.mixer.get_busy():
                pygame.time.Clock().tick(10)
            return True
            
        except Exception as e:
            print(f"Pygame Sound 재생 실패: {e}")
            
            # 재생 시도 방법 2: pygame.mixer.music
            try:
                pygame.mixer.music.load(file_path)
                # ubcfcub968 uc124uc815 uc801uc6a9 (0-500% -> 0.0-5.0)
                volume_normalized = max(0, min(volume, 500)) / 100.0
                
                # 볼륨 증폭 시 추가 방법 시도
                if volume > 100:
                    try:
                        # 볼륨이 높을 때는 파일을 직접 읽어서 증폭 후 다시 저장하는 방식 시도
                        temp_file_path = None
                        data, samplerate = sf.read(file_path)
                        
                        # 제곱 방식 증폭 공식 적용 (100% 이상에서 더 강력한 효과)
                        boost_factor = max(0, (volume / 100.0) ** 1.5)
                        print(f"  - 볼륨 증폭 계수: {boost_factor:.2f}x (제곱 증폭 공식)")
                        data = data * boost_factor
                        
                        # 클리핑 방지
                        max_value = numpy.max(numpy.abs(data))
                        if max_value > 0.95:
                            scaling_factor = 0.95 / max_value
                            data = data * scaling_factor
                            print(f"  - 오디오 클리핑 방지 적용: {scaling_factor:.2f}x")
                        
                        # 임시 파일로 저장
                        temp_dir = os.path.join(SCRIPT_DIR, "resources", "audio", "temp")
                        os.makedirs(temp_dir, exist_ok=True)
                        temp_file_path = os.path.join(temp_dir, f"vol_boost_{int(time.time())}.wav")
                        sf.write(temp_file_path, data, samplerate)
                        
                        # 임시 파일 로드
                        pygame.mixer.music.load(temp_file_path)
                        # 기본 볼륨은 최대로 설정 (이미 데이터에서 증폭됨)
                        pygame.mixer.music.set_volume(1.0)
                        print(f"  - 증폭된 임시 파일 사용: {temp_file_path}")
                        
                        # 이전에 생성된 임시 파일 정리 (10개 이상 시)
                        try:
                            temp_files = [os.path.join(temp_dir, f) for f in os.listdir(temp_dir) if f.startswith("vol_boost_")]
                            if len(temp_files) > 10:
                                # 가장 오래된 파일 삭제
                                temp_files.sort(key=os.path.getmtime)
                                for old_file in temp_files[:-10]:  # 최신 10개만 남기고 삭제
                                    try:
                                        os.remove(old_file)
                                        print(f"  - 오래된 임시 파일 삭제: {old_file}")
                                    except:
                                        pass
                        except Exception as e:
                            print(f"  - 임시 파일 정리 중 오류 (무시됨): {e}")
                    except Exception as e:
                        print(f"  - 고급 볼륨 증폭 실패 (기본 방식으로 대체): {e}")
                        # 실패 시 원래 파일 사용
                        pygame.mixer.music.load(file_path)
                        pygame.mixer.music.set_volume(volume_normalized)
                else:
                    # 볼륨이 100% 이하면 기본 방식 사용
                    pygame.mixer.music.set_volume(volume_normalized)
                
                print(f"볼륨 적용(music 강화): {volume}% ({volume_normalized:.2f})")
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                return True
            except Exception as e:
                print(f"Pygame Music 재생 실패: {e}")
                
                # 재생 시도 방법 3: sounddevice
                try:
                    data, samplerate = sf.read(file_path)
                    # 볼륨 설정 적용 (0-500% -> 0.0-5.0)
                    volume_normalized = max(0, min(volume, 500)) / 100.0
                    
                    # sounddevice 볼륨 조절 강화
                    if volume > 100:
                        # 100% 이상인 경우 추가 증폭 공식 적용
                        # 개선된 볼륨 계산 공식: 1.0-5.0 범위의 방사 증폭 적용
                        boost_factor = max(0, (volume / 100.0) ** 1.5)  # 제곱 방식 증폭
                        print(f"  - 볼륨 증폭 계수: {boost_factor:.2f}x (제곱 증폭 공식)")
                        data = data * boost_factor
                    else:
                        # 기본 선형 적용
                        data = data * volume_normalized
                        
                    # 오디오 잡음을 방지하기 위한 클리핑
                    if volume > 200:
                        # 볼륨이 높을 경우, 클리핑을 방지하기 위한 하드 교정
                        max_value = numpy.max(numpy.abs(data))
                        if max_value > 0.95:  # 전차 발생을 방지하기 위한 값
                            scaling_factor = 0.95 / max_value
                            data = data * scaling_factor
                            print(f"  - 오디오 클리핑 방지 적용: {scaling_factor:.2f}x")
                        
                    print(f"볼륨 적용(sounddevice 강화): {volume}% ({volume_normalized:.2f})")
                    sd.play(data, samplerate)
                    sd.wait()
                    return True
                except Exception as e:
                    print(f"Sounddevice 재생 실패: {e}")
     
    except Exception as e:
        print(f"오디오 재생 중 예외 발생: {e}")
        return False

def initial_setup():
    """프로그램 초기 설정"""
    global root
    
    try:
        import sys
        
        # 시작 타이머 설정
        start_time = time.time()
        
        # 환경 감지 및 로깅
        is_frozen = getattr(sys, 'frozen', False)
        env_type = "PyInstaller 패키지" if is_frozen else "개발 환경"
        print(f"실행 환경: {env_type}")
        
        if is_frozen:
            print(f"실행 파일 경로: {sys.executable}")
            print(f"임시 경로: {sys._MEIPASS if hasattr(sys, '_MEIPASS') else '없음'}")
        
        # macOS 환경설정 - 필요할 때만 적용
        if sys.platform == "darwin":
            os.environ["SDL_AUDIODRIVER"] = "coreaudio"
            print("SDL_AUDIODRIVER를 coreaudio로 설정함 (macOS)")
            
            # macOS에서 PyInstaller로 패키징된 경우 추가 설정
            if is_frozen:
                # 앱 번들 내에서 리소스 경로 설정
                os.environ["RESOURCEPATH"] = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
                print(f"리소스 경로 설정: {os.environ['RESOURCEPATH']}")
        
        # pygame 초기화 - 비동기 방식으로 최적화
        def init_pygame():
            try:
                # 이미 초기화되었는지 확인
                if pygame.get_init():
                    print("Pygame이 이미 초기화되어 있습니다.")
                    return True
                    
                pygame.init()
                # 최소한의 믹서 설정으로 초기화
                pygame.mixer.init(44100, -16, 2, 1024)
                print("Pygame 초기화 완료")
                return True
            except Exception as e:
                print(f"Pygame 초기화 오류: {e}")
                traceback.print_exc()
                return False
        
        # 별도 스레드에서 pygame 초기화
        pygame_thread = threading.Thread(target=init_pygame)
        pygame_thread.daemon = True
        pygame_thread.start()
        
        print("Pygame 초기화 시작 (백그라운드)")
         
        # tkinter 루트 생성 및 설정 (빠른 UI 표시를 위해 먼저 실행)
        root = tk.Tk()
        root.title("도파민 대충영어")
        
        # 로고 로딩 및 아이콘 설정
        try:
            # 아이콘 설정 (플랫폼별 처리)
            icon_path = resource_path("images/logo.png")
            if os.path.exists(icon_path):
                if platform.system() == "Windows":
                    root.iconbitmap(default=icon_path)
                else:
                    logo_img = ImageTk.PhotoImage(file=icon_path)
                    root.iconphoto(True, logo_img)
                print(f"앱 아이콘 설정 완료: {icon_path}")
        except Exception as e:
            print(f"아이콘 설정 오류: {e}")
            # 오류가 발생해도 계속 진행
        
        # 나머지 초기화 코드는 그대로 유지
        # 화면 크기 설정 (고정 크기)
        width = 1080
        height = 608
         
        # 화면 좌상단에 위치
        x = 0
        y = 0
         
        # 윈도우 설정
        root.geometry(f"{width}x{height}+{x}+{y}")
        root.configure(bg=COLORS['background'])
        root.resizable(False, False)
        
        # 초기 화면 생성 (UI 먼저 표시)ㅈ
        create_settings_ui()
        
        # 필수 로고 파일 미리 로드 (병렬 처리)
        def preload_logos():
            try:
                logo_path = SCRIPT_DIR / 'resources/images/logo.png'
                flac_logo_path = SCRIPT_DIR / 'resources/images/flac_logo.jpg'
                if logo_path.exists():
                    Image.open(logo_path)
                if flac_logo_path.exists():
                    Image.open(flac_logo_path)
            except Exception as e:
                print(f"로고 프리로드 오류: {e}")
        
        logo_thread = threading.Thread(target=preload_logos)
        logo_thread.daemon = True
        logo_thread.start()
        
        # 비필수 초기화 작업을 UI 표시 후로 지연
        def delayed_init():
            # pygame 스레드가 끝날 때까지 기다림
            pygame_thread.join(timeout=2.0)
            
            # 마지막 초기화
            try:
                print(f"초기화 완료: {time.time() - start_time:.2f}초 소요")
            except Exception as e:
                print(f"지연된 초기화 오류: {e}")
        
        # UI 표시 후 0.5초 후 나머지 초기화 실행
        root.after(500, delayed_init)
         
        return root
         
    except Exception as e:
        print(f"초기 설정 중 오류 발생: {e}")
        traceback.print_exc()
        return None

async def save_all_tts():
    """선택된 언어의 모든 TTS 파일 저장"""
    try:
        saved_settings = load_settings()
        settings = get_settings()
        save_path = Path(saved_settings.get('tts_save_path', DEFAULT_SETTINGS['tts_save_path']))
        
        # 음성 회수가 1 이상인 언어들 모두 찾기
        active_langs = []
        lang_voice_map = {
            'english': settings['eng_voice'],
            'korean': settings['kor_voice'],
            'chinese': settings['zh_voice'],
            'japanese': settings['jp_voice'],
            'vietnamese': settings['vn_voice'],  # 베트남어 추가
            'nepali': settings['ne_voice']  # 네팔어 추가
        }

        for lang, repeat in [
            (settings['first_lang'], settings['first_repeat']),
            (settings['second_lang'], settings['second_repeat']),
            (settings['third_lang'], settings['third_repeat'])
        ]:
            if int(repeat) > 0:
                active_langs.append((lang, lang_voice_map[lang]))

        if not active_langs:
            messagebox.showerror("오류", "음성 회수가 1 이상인 언어가 없습니다.")
            return

        # 사용자에게 저장할 언어 선택하게 하기
        if len(active_langs) > 1:
            lang_names = {
                'english': '영어',
                'korean': '한국어',
                'chinese': '중국어',
                'japanese': '일본어',
                'vietnamese': '베트남어',
                'nepali': '네팔어'  # 네팔어 추가
            }
            choices = [f"{lang_names[lang]} ({voice})" for lang, voice in active_langs]
            choice = messagebox.askquestion("언어 선택", 
                                          "여러 언어가 선택되었습니다.\n첫 번째 언어로 저장하시겠습니까?")
            if choice != 'yes':
                return
        
        selected_lang, selected_voice = active_langs[0]
        start_row = int(settings['start_row'])
        end_row = int(settings['end_row'])

        # 엑셀에서 문장 가져오기
        texts = get_words_from_excel(start_row, end_row)
        selected_texts = texts[0] if selected_lang == 'english' else \
                        texts[1] if selected_lang == 'korean' else \
                        texts[2] if selected_lang == 'chinese' else \
                        texts[3] if selected_lang == 'vietnamese' else \
                        texts[4] if selected_lang == 'japanese' else \
                        texts[5] if selected_lang == 'nepali' else []

        print(f"\n=== TTS 일괄 저장 시작 ===")
        print(f"저장 경로: {save_path}")
        print(f"문장 범위: {start_row} ~ {end_row}")
        print(f"선택 언어: {LANG_DISPLAY[selected_lang]}")
        print(f"선택 음성: {selected_voice}")
        print("=====================\n")

        # 저장 경로 생성
        save_path.mkdir(parents=True, exist_ok=True)

        # 각 문장별로 TTS 생성 및 저장
        for i, text in enumerate(selected_texts, start=start_row):
            if not text:  # 빈 문장 건너뛰기
                continue

            # 베트남어 처리
            if selected_lang == 'vietnamese':
                temp_file = f"temp_vn_{int(time.time()*1000)}.wav"
                final_file = save_path / f"vn{i}.wav"
                
                try:
                    # Edge TTS로 음성 생성
                    communicate = edge_tts.Communicate(text, VOICE_MAPPING['vietnamese'][selected_voice])
                    await communicate.save(str(temp_file))
                    
                    # WAV 파일 변환 및 저장 - 기본 음질 설정으로 변경
                    subprocess.run([
                        'ffmpeg', '-y',
                        '-i', temp_file,
                        '-acodec', 'pcm_s16le',
                        '-ar', '22050',  # 샘플링 레이트 낮춤 (44100 → 22050)
                        '-ac', '1',      # 모노 채널로 변경 (2 → 1)
                        str(final_file)
                    ], check=True, capture_output=True)
                    
                    print(f"TTS 파일 생성: vn{i}.wav")
                    
                finally:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                continue

            # 다른 언어 처리 (기존 코드)
            full_voice_name = voice_mapping.get(selected_voice, selected_voice)
            temp_file = f"temp_{int(time.time()*1000)}.wav"
            communicate = edge_tts.Communicate(text, full_voice_name)
            await communicate.save(temp_file)
            
            # WAV 형식으로 변환 - 기본 음질 설정으로 변경
            converted_file = f"converted_{int(time.time()*1000)}.wav"
            subprocess.run([
                'ffmpeg', '-y',
                '-i', temp_file,
                '-acodec', 'pcm_s16le',
                '-ar', '22050',  # 샘플링 레이트 낮춤 (44100 → 22050)
                '-ac', '1',      # 모노 채널로 변경 (2 → 1)
                converted_file
            ], check=True, capture_output=True)
            
            os.remove(temp_file)
            
            # 저장 경로에 복사
            lang_code = full_voice_name.split('-')[0].lower()
            final_filename = f"{lang_code}{i}.wav"
            final_path = save_path / final_filename
            
            import shutil
            shutil.copy2(converted_file, final_path)
            print(f"TTS 파일 생성: {final_filename}")
            
            os.remove(converted_file)

        print("\n=== TTS 일괄 저장 완료 ===")
        messagebox.showinfo("완료", "TTS 파일 저장이 완료되었습니다.")

    except Exception as e:
        print(f"TTS 저장 중 오류: {e}")
        messagebox.showerror("오류", f"TTS 저장 중 오류가 발생했습니다.\n{str(e)}")

def start_tts_save():
    """TTS 저장 시작"""
    threading.Thread(target=lambda: asyncio.run(save_all_tts()), daemon=True).start()

async def play_sound(file_path):
    """음성 파일을 재생합니다"""
    try:
        # 파일 존재 확인
        if not os.path.exists(file_path):
            print(f"오류: 음성 파일이 존재하지 않습니다: {file_path}")
            
            # 백업 오디오 파일 사용
            backup_file = Path(resource_path("resources/backup_audio.wav"))
            if backup_file.exists():
                print(f"백업 오디오 파일을 사용합니다: {backup_file}")
                file_path = str(backup_file)
            else:
                print("백업 오디오 파일도 찾을 수 없습니다.")
                return False
        
        # 별도 스레드에서 오디오 재생
        thread = threading.Thread(target=lambda: _play_audio_internal(file_path))
        thread.start()
        
        # 파일 크기 기반으로 예상 재생 시간 계산
        file_size = os.path.getsize(file_path)
        estimated_duration = file_size / 48000  # 대략적인 계산
        
        # 비동기 대기
        await precise_sleep(min(estimated_duration, 10))  # 최대 10초 대기
        
        return True
    except Exception as e:
        print(f"음성 재생 오류: {e}")
        return False

def _play_audio_internal(file_path):
    """내부 오디오 재생 함수 (스레드에서 실행됨)"""
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init(44100, -16, 2, 2048)
        sound = pygame.mixer.Sound(file_path)
        sound.play()
        while pygame.mixer.get_busy():
            time.sleep(0.1)
        return True
    except Exception as e:
        print(f"pygame 재생 실패: {e}")
        return False

def format_time_with_ms(seconds):
    """시간을 분:초.밀리초 형식으로 포맷팅"""
    minutes = int(seconds // 60)
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:06.3f}"

def format_log(time_ms, type_str, lang, voice, text):
    """로그 메시지를 통일된 형식으로 포맷팅
    
    Args:
        time_ms (float): 시간 (초)
        type_str (str): 로그 유형 ('자막' 또는 'TTS' 또는 'WAV')
        lang (str): 언어 ('korean', 'english', 등)
        voice (str): 음성 이름 (SunHi, Steffan 등) - TTS/WAV 경우에만 사용
        text (str): 표시할 텍스트
        
    Returns:
        str: 포맷팅된 로그 메시지
    """
    # 언어 코드 매핑에서 언어 코드 가져오기
    lang_code = LANGUAGE_CODES.get(lang, lang)
    
    formatted_time = format_time_with_ms(time_ms)
    
    if type_str == '자막':
        return f"[{formatted_time}] - 자막({lang_code}) - {text}"
    else:  # TTS 또는 WAV
        return f"[{formatted_time}] - {type_str}({voice}) - {text}"

async def precise_sleep(delay_time):
    """
    정밀한 시간 지연을 위한 함수
    asyncio.sleep보다 더 정확한 지연을 구현
    
    Args:
        delay_time (float): 지연할 시간 (초)
    """
    if delay_time <= 0:
        return
        
    # 매우 작은 지연(0.1초 이하)은 더 정밀한 방법으로 처리
    if delay_time < 0.1:
        start_time = time.time()
        while time.time() - start_time < delay_time:
            # CPU를 과도하게 사용하지 않도록 매우 짧은 sleep 추가
            await asyncio.sleep(0.001)
        return
    
    # 0.1초 이상의 지연은 일반 asyncio.sleep 사용
    await asyncio.sleep(delay_time)

def validate_settings(start_value, end_value):
    """입력된 설정값 검증"""
    try:
        start_row = int(start_value)
        end_row = int(end_value)
        
        if start_row < 1 or start_row > end_row:
            print(f"잘못된 범위: {start_row} ~ {end_row}")
            return False
            
        return True
    except ValueError:
        print(f"숫자 형식 오류: {start_value}, {end_value}")
        return False

async def create_backup_audio():
    """백업 오디오 파일 생성 (시스템 메시지용)"""
    try:
        print("백업 오디오 파일 생성 시작...")
        
        # base 디렉토리 확인 및 생성
        base_dir = SCRIPT_DIR / 'resources'
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # 백업 오디오 파일 경로
        backup_file = base_dir / 'backup_audio.wav'
        
        # 백업 파일이 이미 존재하면 재생성하지 않음
        if backup_file.exists() and backup_file.stat().st_size > 0:
            print(f"백업 오디오 파일이 이미 존재합니다: {backup_file}")
            return
        
        # 임시 파일 경로
        temp_file = SCRIPT_DIR / f"temp_backup_{int(time.time())}.wav"
        
        # 다양한 텍스트와 음성으로 시도 (여러 옵션 제공)
        options = [
            ("시스템 메시지입니다.", "ko-KR-SunHiNeural"),
            ("System message.", "en-US-AriaNeural"),
            ("안녕하세요.", "ko-KR-SunHiNeural")
        ]
        
        success = False
        
        for text, voice in options:
            try:
                print(f"백업 오디오 생성 시도: '{text}' (음성: {voice})")
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(str(temp_file))
                
                if temp_file.exists() and temp_file.stat().st_size > 0:
                    print(f"백업 오디오 생성 성공: {temp_file}")
                    # 백업 파일로 복사
                    import shutil
                    shutil.copy2(str(temp_file), str(backup_file))
                    print(f"백업 파일 생성 완료: {backup_file}")
                    success = True
                    break
            except Exception as e:
                print(f"옵션 '{text}'로 시도 중 오류 발생: {e}")
        
        # 모든 시도 실패 시 카운트다운 파일 복사
        if not success:
            print("모든 Edge TTS 시도 실패, 카운트다운 파일 사용")
            countdown_file = SCRIPT_DIR / 'audio' / 'countdown.wav'
            if countdown_file.exists():
                import shutil
                shutil.copy2(str(countdown_file), str(backup_file))
                print(f"카운트다운 파일을 백업 파일로 복사했습니다: {backup_file}")
            else:
                print("카운트다운 파일이 없어 빈 오디오 파일 생성")
                # 빈 오디오 파일 생성 코드 추가
        
        # 임시 파일 삭제
        if temp_file.exists():
            try:
                temp_file.unlink()
                print(f"임시 파일 삭제 완료: {temp_file}")
            except Exception as e:
                print(f"임시 파일 삭제 오류: {e}")
                
    except Exception as e:
        print(f"백업 오디오 파일 생성 오류: {e}")
        traceback.print_exc()

def show_error_popup(title: str, message: str):
    """오류 팝업을 표시합니다."""
    try:
        # root 존재 확인
        if not root or not root.winfo_exists():
            # root가 없으면 messagebox 사용
            messagebox.showerror(title, message)
            return
        
        # 팝업 생성
        popup = tk.Toplevel(root)
        popup.title(title)
        popup.transient(root)  # 부모 창에 종속되도록 설정
        popup.grab_set()       # 모달 동작 설정
        
        # 화면 중앙에 위치
        popup_width = 400
        popup_height = 200
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - popup_width) // 2
        y = (screen_height - popup_height) // 2
        popup.geometry(f"{popup_width}x{popup_height}+{x}+{y}")
        
        # 아이콘 설정
        try:
            icon_path = resource_path(os.path.join("resources", "error_icon.ico"))
            popup.iconbitmap(icon_path)
        except Exception as e:
            logging.warning(f"[아이콘] 오류: {str(e)}")
        
        # 메시지 표시
        msg_frame = tk.Frame(popup, bg=COLORS['background'])
        msg_frame.pack(expand=True, fill='both')
        
        msg_label = tk.Label(msg_frame, text=message, padx=20, pady=20,
                             bg=COLORS['background'], fg=COLORS['white'],
                             wraplength=popup_width-50)  # 텍스트 자동 줄바꿈
        msg_label.pack(expand=True)
        
        # 확인 버튼
        btn_frame = tk.Frame(popup, bg=COLORS['background'])
        btn_frame.pack(pady=10, fill='x')
        
        ok_btn = tk.Button(btn_frame, text="확인", command=popup.destroy, 
                          width=10, bg=COLORS['background'], fg=COLORS['white'])
        ok_btn.pack(pady=10)
        
        # 키보드 이벤트 바인딩
        popup.bind("<Return>", lambda e: popup.destroy())
        popup.bind("<Escape>", lambda e: popup.destroy())
        
        # 항상 최상위에 표시
        popup.attributes('-topmost', True)
        
    except tk.TclError as e:
        # Tkinter 오류 시 기본 messagebox 사용
        logging.error(f"팝업 생성 실패, messagebox 사용: {e}")
        messagebox.showerror(title, message)
    except Exception as e:
        logging.error(f"오류 팝업 표시 실패: {e}")
        logging.error(traceback.format_exc())
        print(f"오류: {title} - {message}")

# 비동기 함수를 이벤트 루프에서 실행하기 위한 도우미 함수
def run_async_in_thread(coroutine, callback=None):
    """별도 스레드에서 비동기 함수를 실행합니다."""
    def run_async():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = None
        try:
            # 신호 핸들러 설치 (특히 macOS에서 중요)
            for sig in (signal.SIGINT, signal.SIGTERM):
                try:
                    loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(shutdown(loop, s)))
                except NotImplementedError:
                    # Windows에서는 add_signal_handler가 지원되지 않음
                    pass
                    
            # 코루틴 실행
            result = loop.run_until_complete(coroutine)
        except asyncio.CancelledError:
            logging.info("비동기 작업이 취소되었습니다.")
        except Exception as e:
            logging.error(f"비동기 실행 오류: {e}")
            traceback.print_exc()  # 항상 스택 트레이스 출력하도록 수정
        finally:
            # 정리 작업
            try:
                # 모든 pending 태스크 확인 및 취소
                pending_tasks = asyncio.all_tasks(loop)
                if pending_tasks:
                    # 자기 자신을 제외한 태스크만 취소
                    pending_tasks = [t for t in pending_tasks if not t.done()]
                    if pending_tasks:
                        logging.warning(f"{len(pending_tasks)}개의 미완료 태스크가 있습니다. 정리 중...")
                        for task in pending_tasks:
                            task.cancel()
                            
                        # 모든 태스크가 취소될 때까지 짧게 대기
                        loop.run_until_complete(asyncio.gather(*pending_tasks, return_exceptions=True))
                        logging.info("모든 pending 태스크가 취소되었습니다.")
                
                # 루프 닫기
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.run_until_complete(loop.shutdown_default_executor())
                loop.close()
                logging.debug("이벤트 루프가 정상적으로 닫혔습니다.")
            except Exception as cleanup_error:
                logging.error(f"이벤트 루프 정리 오류: {cleanup_error}")
                traceback.print_exc()
        
        # 콜백 처리 (UI 스레드에서 실행)
        if callback and result is not None:
            try:
                if root and root.winfo_exists():
                    root.after(0, lambda: callback(result))
                else:
                    logging.warning("콜백을 실행할 수 없습니다: UI가 이미 종료되었습니다.")
            except Exception as cb_error:
                logging.error(f"비동기 콜백 실행 오류: {cb_error}")
                traceback.print_exc()
    
    # 비동기 종료 핸들러
    async def shutdown(loop, signal=None):
        """이벤트 루프를 안전하게 종료합니다."""
        if signal:
            logging.info(f"시그널 {signal.name}을 받았습니다. 안전하게 종료합니다.")
        
        # 모든 태스크 취소
        tasks = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task(loop)]
        for task in tasks:
            task.cancel()
            
        # 태스크들이 완료될 때까지 대기
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # 루프 정지 (안전한 종료를 위해)
        loop.stop()
    
    # 데몬 스레드로 실행하여 메인 프로그램 종료 시 함께 종료되도록 함
    thread = threading.Thread(target=run_async, daemon=True)
    thread.start()
    return thread  # 스레드 객체 반환 (필요 시 조인 등의 작업을 위해)

def play_final_music_sync(duration):
    """파이널 뮤직을 동기적으로 재생 - play_final_music의 래퍼 함수"""
    try:
        # 기본 WAV 파일 경로
        music_file = resource_path(os.path.join("audio", "final.wav"))
        
        # WAV 파일이 없는 경우 MP3 파일을 찾아서 WAV로 변환
        if not os.path.exists(music_file):
            print("WAV 파일을 찾을 수 없어 MP3 확인 중...")
            mp3_file = resource_path(os.path.join("resources", "final.mp3"))
            
            if os.path.exists(mp3_file):
                print(f"MP3 파일 발견: {mp3_file} - WAV로 변환 시도")
                try:
                    # ffmpeg로 MP3를 WAV로 변환
                    wav_output = os.path.join(os.path.dirname(mp3_file), "final.wav")
                    subprocess.run([
                        'ffmpeg', '-y', '-i', mp3_file, 
                        '-acodec', 'pcm_s16le', 
                        '-ar', '44100', 
                        '-ac', '2', 
                        wav_output
                    ], check=True, capture_output=True)
                    
                    music_file = wav_output
                    print(f"MP3 파일을 WAV로 변환 완료: {wav_output}")
                except Exception as e:
                    print(f"MP3 변환 오류: {e}")
                    music_file = mp3_file  # 변환 실패 시 MP3 파일 직접 사용
            else:
                print("MP3 파일도 찾을 수 없습니다.")
    except Exception as e:
        print(f"파이널 뮤직 준비 중 오류: {e}")
        traceback.print_exc()
        
    # play_final_music을 동기 모드(is_async=False)로 호출하는 비동기 함수를 실행
    run_async_in_thread(play_final_music_sync(duration, is_async=False))

def show_final_image():
    """최종 이미지를 표시하는 함수 (필요에 따라 구현 내용을 추가하세요)"""
    try:
        final_image_path = resource_path("resources/images/final_image.jpg")
        if os.path.exists(final_image_path):
            from PIL import Image, ImageTk
            img = Image.open(final_image_path)
            photo = ImageTk.PhotoImage(img)
            final_label = tk.Label(root, image=photo)
            final_label.image = photo  # 참조 유지
            final_label.pack()
        else:
            print("최종 이미지 파일을 찾을 수 없습니다.")
    except Exception as e:
        print("최종 이미지 표시 중 오류:", e)

def show_statistics(df):
    """학습 종료 후 통계 화면 표시 - 업그레이드된 디자인"""
    global current_frame, lesson_running
    
    # 설정 로드
    settings = load_settings()
    
    # 자동반복 관련 설정 확인
    current_repeat = int(settings.get('current_repeat', '0'))
    auto_repeat = int(settings.get('auto_repeat', '0'))
    
    # 학습 종료 시간 기록
    lesson_end_time = time.time()
    lesson_running = False
    
    if current_frame:
        current_frame.destroy()
    
    # 메인 프레임 - 그라데이션 배경 효과를 위해 캔버스 사용
    current_frame = tk.Frame(root, bg=COLORS['background'])
    current_frame.pack(fill='both', expand=True)
    
    # 배경 캔버스 추가 - 상단에서 하단으로 그라데이션 효과
    canvas_width = root.winfo_width() if root.winfo_width() > 100 else 1200
    canvas_height = root.winfo_height() if root.winfo_height() > 100 else 800
    
    background = tk.Canvas(current_frame, width=canvas_width, height=canvas_height, 
                         bg=COLORS['background'], highlightthickness=0)
    background.place(x=0, y=0, relwidth=1, relheight=1)
    
    # 그라데이션 배경 효과 (상단에서 하단으로)
    for i in range(100):
        # 상단 색상에서 하단 색상으로 점진적 변화
        r1, g1, b1 = 40, 42, 58  # 상단 색상 (더 어두운 톤)
        r2, g2, b2 = 30, 32, 48  # 하단 색상 (더 어두운 톤)
        r = int(r1 + (r2-r1) * i/100)
        g = int(g1 + (g2-g1) * i/100)
        b = int(b1 + (b2-b1) * i/100)
        color = f'#{r:02x}{g:02x}{b:02x}'
        y0 = int(i * canvas_height / 100)
        y1 = int((i + 1) * canvas_height / 100)
        background.create_rectangle(0, y0, canvas_width, y1, fill=color, outline=color)
    
    # 타이틀 카드 - 둥근 모서리와 그림자 효과
    title_frame = tk.Frame(current_frame, bg="#3c3f57", padx=30, pady=15)
    title_frame.place(relx=0.5, rely=0.1, anchor='center')
    
    # 학습 결과 통계 제목
    title_label = tk.Label(title_frame, text="학습 결과 통계", 
                          font=("AppleSDGothicNeo", 36, "bold"),
                          bg="#3c3f57", fg="#ffffff")
    title_label.pack()
    
    # 통계 카드 컨테이너
    stats_container = tk.Frame(current_frame, bg=COLORS['background'])
    stats_container.place(relx=0.5, rely=0.5, anchor='center')
    
    # 통계 데이터 계산
    total_questions = len(df)
    correct_answers = df['correct'].sum()
    accuracy = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
    
    total_study_time = lesson_end_time - lesson_start_time
    hours, remainder = divmod(total_study_time, 3600)
    minutes, seconds = divmod(remainder, 60)
    time_str = f"{int(hours)}시간 {int(minutes)}분 {int(seconds)}초"
    
    # 통계 카드 디자인 - 4개의 모던한 카드로 표시
    cards = [
        {
            "icon": "⏱️", 
            "title": "학습 시간",
            "value": time_str,
            "color": "#4e85eb"  # 파란색 계열
        },
        {
            "icon": "📚", 
            "title": "학습 문장",
            "value": f"{total_questions}문장",
            "color": "#50b086"  # 녹색 계열
        },
        {
            "icon": "✅", 
            "title": "정답 개수",
            "value": f"{int(correct_answers)}문장",
            "color": "#e6a440"  # 주황색 계열
        },
        {
            "icon": "🎯", 
            "title": "정확도",
            "value": f"{accuracy:.1f}%",
            "color": "#e07b67"  # 빨간색 계열
        }
    ]
    
    # 2x2 그리드 레이아웃으로 카드 배치
    card_frame = tk.Frame(stats_container, bg=COLORS['background'])
    card_frame.pack(pady=20)
    
    row, col = 0, 0
    for idx, card in enumerate(cards):
        # 카드 프레임 - 둥근 모서리 효과를 위한 디자인
        card_container = tk.Frame(card_frame, bg=card["color"], padx=20, pady=15, 
                                 relief="flat", borderwidth=0)
        card_container.grid(row=row, column=col, padx=15, pady=15)
        
        # 아이콘 표시
        icon_label = tk.Label(card_container, text=card["icon"], 
                             font=("AppleSDGothicNeo", 42),
                             bg=card["color"], fg="#ffffff")
        icon_label.pack(pady=(0, 5))
        
        # 타이틀
        title_label = tk.Label(card_container, text=card["title"], 
                              font=("AppleSDGothicNeo", 18),
                              bg=card["color"], fg="#ffffff")
        title_label.pack()
        
        # 값 (더 큰 글꼴)
        value_label = tk.Label(card_container, text=card["value"], 
                              font=("AppleSDGothicNeo", 28, "bold"),
                              bg=card["color"], fg="#ffffff")
        value_label.pack(pady=(5, 0))
        
        # 그리드 위치 계산
        col += 1
        if col > 1:
            col = 0
            row += 1
    
    # 결과 데이터 저장
    df.to_csv(f'학습결과_{time.strftime("%Y%m%d_%H%M%S")}.csv', index=False, encoding='utf-8-sig')
    print(f"통계: 총 {total_questions}문장, 정답 {correct_answers}문장, 정확도 {accuracy:.1f}%")
    
    # 자동반복 중인 경우 파이널 뮤직 재생 안함
    # 수정: auto_repeat >= 0을 auto_repeat > 0으로 변경하여 0일 때는 반복하지 않도록 함
    is_auto_repeating = (current_repeat < auto_repeat) and (auto_repeat > 0)
    
    # Final music 재생 설정
    final_music_setting = settings.get('final_music', '1분')
    
    # 통계 화면 표시 후 5초 뒤에 이미지 표시 (이전: 1초)
    # 힐링뮤직이 활성화된 경우에만 이미지 표시
    if final_music_setting != '없음' and not is_auto_repeating:
        root.after(5000, show_final_image)
    
    if final_music_setting != '없음' and not is_auto_repeating:
        # Final music 재생 시작 (수정: sounddevice 대신 pygame 사용)
        music_file = resource_path(os.path.join("resources", "audio", "final.wav"))
        if os.path.exists(music_file):
            pygame.mixer.music.load(music_file)
            pygame.mixer.music.set_volume(0.3)
            pygame.mixer.music.play()
            print(f"Final music 재생 시작 ({final_music_setting})")
        
        # 재생 시간 설정 (수정: asyncio.run 대신 스레드 사용)
        selected_duration = FINAL_MUSIC_DURATION[final_music_setting]
        # 통계 화면 5초 표시 후 뮤직 재생 시작 (이전: 3초)
        root.after(5000, lambda: play_final_music_sync(selected_duration))
    else:
        if is_auto_repeating:
            print(f"자동반복 중 ({current_repeat+1}/{auto_repeat}) - 파이널 뮤직 재생 건너뜀")
        # 통계 화면 5초 표시 후 설정 화면으로 이동 (이전: 5초)
        root.after(5000, create_settings_ui)
    
def update_speed_info(lang, speed):
    """배속 정보를 화면에 표시"""
    global speed_label
    if speed_label and speed_label.winfo_exists():
        # lang에서 언어명 가져오기
        lang_name = LANG_DISPLAY.get(lang, lang)
        speed_label.config(text=f"{lang_name} {speed}배속 재생 중")

# 시스템 정보 로깅
system_info = f"{platform.system()} {platform.release()}, Python {sys.version.split()[0]}"
logging.info(f"프로그램 시작 - 시스템 정보: {system_info}")

def show_error_message(title, message):
    """에러 메시지 표시"""
    try:
        # root 위젯이 존재하는지 확인
        if root and root.winfo_exists():
            messagebox.showerror(title, message, parent=root)
        else:
            # root 위젯이 없는 경우, 독립적인 에러 메시지 표시
            messagebox.showerror(title, message)
            
    except tk.TclError as e:
        # Tkinter 관련 오류 처리
        logging.error(f"Tkinter 오류 메시지 표시 실패: {e}")
        print(f"Tkinter 오류: {title} - {message} (원인: {e})")
    except Exception as e:
        # 기타 예외 처리
        logging.error(f"오류 메시지 표시 실패: {e}")
        logging.error(f"오류 상세: {traceback.format_exc()}")
        print(f"오류: {title} - {message}")

def cleanup():
    """프로그램 종료 시 정리 작업"""
    logging.info("프로그램 종료")
    try:
        # Pygame 종료
        pygame.quit()
        
        # 임시 파일 정리
        temp_dir = SCRIPT_DIR / "audio"
        if temp_dir.exists():
            for file in temp_dir.glob("temp_*"):
                try:
                    file.unlink()
                    logging.info(f"임시 파일 삭제: {file}")
                except Exception as e:
                    logging.warning(f"임시 파일 삭제 실패: {file} - {e}")
                    
            for file in temp_dir.glob("speed_*"):
                try:
                    file.unlink()
                    logging.info(f"임시 파일 삭제: {file}")
                except Exception as e:
                    logging.warning(f"임시 파일 삭제 실패: {file} - {e}")
    except Exception as e:
        logging.error(f"정리 작업 중 오류 발생: {e}")

def main():
    """메인 프로그램 실행 함수"""
    try:
        logging.info("초기 설정 시작...")
        root = initial_setup()

        if root:
            logging.info("메인 루프 시작")
            create_settings_ui()
            root.mainloop()
        else:
            logging.error("초기화 실패로 프로그램을 실행할 수 없습니다.")
            show_error_message("초기화 오류", 
                             "프로그램 초기화에 실패했습니다.\n로그 파일을 확인해주세요.")

    except Exception as e:
        logging.error(f"프로그램 실행 중 오류 발생: {e}")
        logging.error(f"오류 발생 위치: {traceback.format_exc()}")
        show_error_message("오류 발생", 
                         f"프로그램 실행 중 오류가 발생했습니다.\n{str(e)}\n\n자세한 내용은 로그 파일을 확인해주세요.")

    finally:
        cleanup()

# 프로그램 시작점
if __name__ == "__main__":
    main()

async def show_repeat_countdown():
    """자동 반복용 카운트다운 표시"""
    global current_frame, countdown_label
    
    # 이전 프레임 제거
    if current_frame:
        current_frame.destroy()
    
    # 카운트다운 프레임 생성
    current_frame = tk.Frame(root, bg=COLORS['background'])
    current_frame.pack(expand=True, fill='both')
    
    # 전체 화면을 차지하는 메인 컨테이너
    main_container = tk.Frame(current_frame, bg=COLORS['background'])
    main_container.place(relx=0.5, rely=0.5, anchor='center')
    
    # 카운트다운 컨테이너
    container = tk.Canvas(main_container, width=200, height=200,
                         bg=COLORS['background'], highlightthickness=0)
    container.pack(pady=20)
    
    # 카운트다운 숫자만 캔버스에 표시
    text_id = container.create_text(
        100,  # x 위치 (중앙)
        100,  # y 위치 (중앙)
        text="5",
        font=FONT_COUNTDOWN,
        fill='#FF69B4',  # 색상을 핫핑크로 변경
        anchor='center'
    )
    container.countdown_text_id = text_id
    countdown_label = container
    
    # 카운트다운 실행
    for i in range(5, 0, -1):
        # 숫자 표시
        countdown_label.itemconfig(countdown_label.countdown_text_id, text=str(i))
        root.update()
        
        # 0.6초 동안 숫자 표시
        await precise_sleep(0.6)
        
        # 숫자 숨기기
        countdown_label.itemconfig(countdown_label.countdown_text_id, text="")
        root.update()
        
        # 남은 시간 대기 (1초 간격 유지)
        await precise_sleep(0.4)
        print(f"[카운트다운] {i}초 남음")
    
    print("[카운트다운] 완료")