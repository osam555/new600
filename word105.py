import os
import sys
import json
import time
import edge_tts
import asyncio
import threading
import traceback
import tkinter as tk
from datetime import datetime
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
os.environ['SDL_VIDEODRIVER'] = 'dummy'

import openpyxl
import tkinter as tk
from tkinter import ttk, messagebox
import os
import json
from pathlib import Path
import time
import subprocess
import asyncio
import edge_tts
import torch
import threading
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, concatenate_videoclips, AudioClip, CompositeAudioClip
import cv2 ## 무비파이 1.0.3 버전 사용
import tempfile
import pygame
import glob
import wave
import shutil
import traceback
from moviepy.audio.AudioClip import AudioArrayClip
from pydub import AudioSegment
import soundfile as sf
from playsound import playsound
import io

# pygame 초기화
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
pygame.init()

# 영어 음성 표시명과 실제 ID 매핑
english_voice_mapping = {
    "en-US-Steffan": "en-US-SteffanNeural",
    "en-US-Roger": "en-US-RogerNeural",
    "en-GB-Sonia": "en-GB-SoniaNeural",
    "en-US-Brian": "en-US-BrianNeural",
    "en-US-Emma": "en-US-EmmaNeural",
    "en-US-Jenny": "en-US-JennyNeural",
    "en-US-Guy": "en-US-GuyNeural",
    "en-US-Aria": "en-US-AriaNeural",
    "en-GB-Ryan": "en-GB-RyanNeural"
}

# 한글 이름과 실제 음성 ID 매핑
korean_voice_mapping = {
    "선희": "ko-KR-SunHiNeural",
    "인준": "ko-KR-InJoonNeural",
}

# 중국어 음성 표시명과 실제 ID 매핑
chinese_voice_mapping = {
    "XiaoXiao": "zh-CN-XiaoxiaoNeural",  # 자연스러운 여성 음성
    "YunXi": "zh-CN-YunxiNeural",        # 차분한 남성 음성
}

# 설정 파일 경로
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_PATH = SCRIPT_DIR / 'settings.json'
EXCEL_PATH = SCRIPT_DIR / 'voca1000.xlsx'

# 기본 설정값
DEFAULT_SETTINGS = {
    'direction': '영한',
    'zh_voice': 'XiaoXiao',
    'kor_voice': '선희',
    'eng_voice': 'en-US-Steffan',
    'start_row': '1',
    'end_row': '10',
    'chinese_repeat': '1',
    'korean_repeat': '1',
    'english_repeat': '1',
    'word_delay': '0.5',
    'spacing': '0.2',
    'speed': '1.5'
}

# 사용 가능한 음성 리스트를 전역 변수로 정의
english_voices = [
    "en-US-Steffan",      # 자연스러운 남성 음성
    "en-US-Jenny",        # 밝은 여성 음성
    "en-US-Roger",        # 차분한 남성 음성
    "en-GB-Sonia",        # 영국 억양 여성 음성
    "en-US-Brian",        # 전문적인 남성 음성
    "en-US-Emma",         # 자연스러운 여성 음성
    "en-US-Guy",          # 활기찬 남성 음성
    "en-US-Aria",         # 전문적인 여성 음성
    "en-GB-Ryan"          # 영국 억양 남성 음성
]

korean_voices = [
    "선희",  # SunHiNeural - 자연스러운 여성 음성
    "인준",  # InJoonNeural - 차분한 남성 음성
]

# 사용 가능한 음성 리스트를 전역 변수로 정의
chinese_voices = [
    "XiaoXiao",      # 자연스러운 여성 음성
    "YunXi",         # 차분한 남성 음성
]

# 전역 변수 추기화
root = None
direction_var = None
zh_voice_var = None
kor_voice_var = None
eng_voice_var = None
start_var = None
end_var = None
zh_repeat_var = None
kor_repeat_var = None
eng_repeat_var = None
delay_var = None
spacing_var = None
speed_var = None

def create_tooltip(widget, text):
    """위젯에 툴팁 추가"""
    def enter(event):
        tooltip = tk.Toplevel(widget)
        tooltip.wm_overrideredirect(True)  # 창 테두리 제거
        tooltip.wm_geometry(f"+{event.x_root+15}+{event.y_root+10}")
        
        label = tk.Label(tooltip, text=text, justify='left',
                       background="#ffffe0", relief="solid", borderwidth=1,
                       font=("Helvetica", "12", "normal"))
        label.pack(padx=3, pady=3)
        
        widget.tooltip = tooltip
        
    def leave(event):
        if hasattr(widget, "tooltip"):
            widget.tooltip.destroy()
            
    widget.bind("<Enter>", enter)
    widget.bind("<Leave>", leave)

def initial_setup():
    """초기화면 설정"""
    global root, direction_var, zh_voice_var, kor_voice_var, eng_voice_var
    global start_var, end_var, zh_repeat_var, kor_repeat_var, eng_repeat_var
    global delay_var, spacing_var, speed_var
    
    # 기존 설정 로드
    settings = load_settings()
    
    root = tk.Tk()
    root.title("단어 학습 프로그램")
    root.geometry("1244x700+0+0")  # 16:9 비율로 변경 (가로 확장)
    root.configure(bg='#2e2e2e')
    
    # 변수 초기화 (저장된 설정값 적용)
    direction_var = tk.StringVar(value=settings['direction'])
    zh_voice_var = tk.StringVar(value=settings['zh_voice'])
    kor_voice_var = tk.StringVar(value=settings['kor_voice'])
    eng_voice_var = tk.StringVar(value=settings['eng_voice'])
    start_var = tk.StringVar(value=settings['start_row'])
    end_var = tk.StringVar(value=settings['end_row'])
    zh_repeat_var = tk.StringVar(value=settings['chinese_repeat'])
    kor_repeat_var = tk.StringVar(value=settings['korean_repeat'])
    eng_repeat_var = tk.StringVar(value=settings['english_repeat'])
    delay_var = tk.StringVar(value=settings['word_delay'])
    spacing_var = tk.StringVar(value=settings['spacing'])
    speed_var = tk.StringVar(value=settings['speed'])
    
    # 제목 프레임 (3D 효과를 위한 중첩된 프레임)
    title_frame_outer = tk.Frame(root, bg='#1e1e1e', padx=2, pady=2)  # 그림자 효과
    title_frame_outer.pack(pady=40)  # pady 20 -> 40으로 증가
    title_frame = tk.Frame(title_frame_outer, bg='#3e3e3e', padx=20, pady=10)  # 메인 프레임
    title_frame.pack()
    
    # 제목 레이블
    title_label = tk.Label(title_frame, 
                          text="영어 중국어 단어장",
                          font=("Helvetica", 42, "bold"),  # 폰트 크기 증가
                          fg='white',
                          bg='#3e3e3e')
    title_label.pack()
    
    # 설정 프레임
    settings_frame = tk.Frame(root, bg='#2e2e2e')
    settings_frame.pack(pady=20)
    
    # 설정 항목의 폰트 크기와 스타일
    label_font = ("Helvetica", 24)  # 폰트 크기 조정
    entry_font = ("Helvetica", 24)  # 폰트 크기 조정
    
    # 1. 언어 선택 섹션
    section_frame1 = tk.Frame(settings_frame, bg='#2e2e2e')
    section_frame1.pack(pady=10, fill='x')
    
    # 섹션 제목과 내용을 같은 줄에 배치
    section_header1 = tk.Frame(section_frame1, bg='#2e2e2e')
    section_header1.pack(fill='x', padx=20)
    tk.Label(section_header1, text="1. 언어 선택", font=("Helvetica", 26, "bold"), fg='#4CAF50', bg='#2e2e2e', anchor='w').pack(side='left', padx=(0, 20))
    
    # 방향 설정 (같은 줄에 추가)
    direction_frame = tk.Frame(section_header1, bg='#2e2e2e')
    direction_frame.pack(side='left', fill='x')
    
    # 영한 순서 라디오 버튼과 텍스트 박스
    en_kor_container = tk.Frame(direction_frame, bg='#2e2e2e')
    en_kor_container.pack(side='left', padx=5)
    radio_en = tk.Radiobutton(en_kor_container, text="", variable=direction_var, value="영한", 
                  font=label_font, bg='#2e2e2e', fg='white', selectcolor='black',
                  relief='flat', borderwidth=0, highlightthickness=0, indicatoron=1)
    radio_en.pack(side='left')
    en_kor_frame = tk.Frame(en_kor_container, bg='#2e2e2e', relief='solid', borderwidth=1, highlightthickness=1, highlightcolor='#ffffff', highlightbackground='#666666')
    en_kor_frame.pack(side='left')
    en_kor_label = tk.Label(en_kor_frame, text="영한", font=label_font, bg='#2e2e2e', fg='white')
    en_kor_label.pack(padx=5, pady=2)
    
    # 한영 순서 라디오 버튼과 텍스트 박스
    kor_en_container = tk.Frame(direction_frame, bg='#2e2e2e')
    kor_en_container.pack(side='left', padx=5)
    radio_kor_en = tk.Radiobutton(kor_en_container, text="", variable=direction_var, value="한영", 
                  font=label_font, bg='#2e2e2e', fg='white', selectcolor='black',
                  relief='flat', borderwidth=0, highlightthickness=0, indicatoron=1)
    radio_kor_en.pack(side='left')
    kor_en_frame = tk.Frame(kor_en_container, bg='#2e2e2e', relief='solid', borderwidth=1, highlightthickness=1, highlightcolor='#ffffff', highlightbackground='#666666')
    kor_en_frame.pack(side='left')
    kor_en_label = tk.Label(kor_en_frame, text="한영", font=label_font, bg='#2e2e2e', fg='white')
    kor_en_label.pack(padx=5, pady=2)
    
    # 영중 순서 라디오 버튼과 텍스트 박스
    en_zh_container = tk.Frame(direction_frame, bg='#2e2e2e')
    en_zh_container.pack(side='left', padx=5)
    radio_en_zh = tk.Radiobutton(en_zh_container, text="", variable=direction_var, value="영중", 
                  font=label_font, bg='#2e2e2e', fg='white', selectcolor='black',
                  relief='flat', borderwidth=0, highlightthickness=0, indicatoron=1)
    radio_en_zh.pack(side='left')
    en_zh_frame = tk.Frame(en_zh_container, bg='#2e2e2e', relief='solid', borderwidth=1, highlightthickness=1, highlightcolor='#ffffff', highlightbackground='#666666')
    en_zh_frame.pack(side='left')
    en_zh_label = tk.Label(en_zh_frame, text="영중", font=label_font, bg='#2e2e2e', fg='white')
    en_zh_label.pack(padx=5, pady=2)
    
    # 중영 순서 라디오 버튼과 텍스트 박스
    zh_en_container = tk.Frame(direction_frame, bg='#2e2e2e')
    zh_en_container.pack(side='left', padx=5)
    radio_zh_en = tk.Radiobutton(zh_en_container, text="", variable=direction_var, value="중영", 
                  font=label_font, bg='#2e2e2e', fg='white', selectcolor='black',
                  relief='flat', borderwidth=0, highlightthickness=0, indicatoron=1)
    radio_zh_en.pack(side='left')
    zh_en_frame = tk.Frame(zh_en_container, bg='#2e2e2e', relief='solid', borderwidth=1, highlightthickness=1, highlightcolor='#ffffff', highlightbackground='#666666')
    zh_en_frame.pack(side='left')
    zh_en_label = tk.Label(zh_en_frame, text="중영", font=label_font, bg='#2e2e2e', fg='white')
    zh_en_label.pack(padx=5, pady=2)
    
    # 라디오 버튼과 레이블에 클릭 이벤트 추가
    en_zh_label.bind('<Button-1>', lambda e: direction_var.set("영중"))
    en_zh_frame.bind('<Button-1>', lambda e: direction_var.set("영중"))
    zh_en_label.bind('<Button-1>', lambda e: direction_var.set("중영"))
    zh_en_frame.bind('<Button-1>', lambda e: direction_var.set("중영"))
    
    # 중한 순서 라디오 버튼과 텍스트 박스
    zh_kor_container = tk.Frame(direction_frame, bg='#2e2e2e')
    zh_kor_container.pack(side='left', padx=5)
    radio_zh = tk.Radiobutton(zh_kor_container, text="", variable=direction_var, value="중한", 
                  font=label_font, bg='#2e2e2e', fg='white', selectcolor='black',
                  relief='flat', borderwidth=0, highlightthickness=0, indicatoron=1)
    radio_zh.pack(side='left')
    zh_kor_frame = tk.Frame(zh_kor_container, bg='#2e2e2e', relief='solid', borderwidth=1, highlightthickness=1, highlightcolor='#ffffff', highlightbackground='#666666')
    zh_kor_frame.pack(side='left')
    zh_kor_label = tk.Label(zh_kor_frame, text="중한", font=label_font, bg='#2e2e2e', fg='white')
    zh_kor_label.pack(padx=5, pady=2)
    
    # 라디오 버튼과 레이블에 클릭 이벤트 추가
    zh_kor_label.bind('<Button-1>', lambda e: direction_var.set("중한"))
    zh_kor_frame.bind('<Button-1>', lambda e: direction_var.set("중한"))
    
    # 한중 순서 라디오 버튼과 텍스트 박스
    kor_zh_container = tk.Frame(direction_frame, bg='#2e2e2e')
    kor_zh_container.pack(side='left', padx=5)
    radio_kor = tk.Radiobutton(kor_zh_container, text="", variable=direction_var, value="한중", 
                  font=label_font, bg='#2e2e2e', fg='white', selectcolor='black',
                  relief='flat', borderwidth=0, highlightthickness=0, indicatoron=1)
    radio_kor.pack(side='left')
    kor_zh_frame = tk.Frame(kor_zh_container, bg='#2e2e2e', relief='solid', borderwidth=1, highlightthickness=1, highlightcolor='#ffffff', highlightbackground='#666666')
    kor_zh_frame.pack(side='left')
    kor_zh_label = tk.Label(kor_zh_frame, text="한중", font=label_font, bg='#2e2e2e', fg='white')
    kor_zh_label.pack(padx=5, pady=2)
    
    # 라디오 버튼과 레이블에 클릭 이벤트 추가
    kor_zh_label.bind('<Button-1>', lambda e: direction_var.set("한중"))
    kor_zh_frame.bind('<Button-1>', lambda e: direction_var.set("한중"))
    
    # 2. 음성 설정 섹션
    section_frame2 = tk.Frame(settings_frame, bg='#2e2e2e')
    section_frame2.pack(pady=10, fill='x')
    
    # 섹션 제목과 내용을 같은 줄에 배치
    section_header2 = tk.Frame(section_frame2, bg='#2e2e2e')
    section_header2.pack(fill='x', padx=20)
    tk.Label(section_header2, text="2. 음성 설정", font=("Helvetica", 26, "bold"), fg='#4CAF50', bg='#2e2e2e', anchor='w').pack(side='left', padx=(0, 20))
    
    # 음성 설정 프레임 (같은 줄에 추가)
    voice_frame = tk.Frame(section_header2, bg='#2e2e2e')
    voice_frame.pack(side='left', fill='x')
    
    # 영어 음성 설정
    tk.Label(voice_frame, text="영어:", font=label_font, fg='white', bg='#2e2e2e').pack(side='left')
    eng_option_menu = ttk.Combobox(voice_frame, textvariable=eng_voice_var, values=english_voices, width=8, font=entry_font)
    eng_option_menu.pack(side='left', padx=(0, 10))
    
    # 중국어 음성 설정
    tk.Label(voice_frame, text="중국:", font=label_font, fg='white', bg='#2e2e2e').pack(side='left')
    zh_option_menu = ttk.Combobox(voice_frame, textvariable=zh_voice_var, values=chinese_voices, width=8, font=entry_font)
    zh_option_menu.pack(side='left', padx=(0, 10))
    
    # 한글 음성 설정
    tk.Label(voice_frame, text="한국:", font=label_font, fg='white', bg='#2e2e2e').pack(side='left')
    kor_option_menu = ttk.Combobox(voice_frame, textvariable=kor_voice_var, values=korean_voices, width=4, font=entry_font)
    kor_option_menu.pack(side='left', padx=(0, 10))
    
    # 입력 필드 스타일 설정
    entry_style = {
        'font': entry_font,
        'bg': '#2e2e2e',
        'fg': 'white',
        'insertbackground': 'white',
        'width': 5,
        'relief': 'solid',  # 테두리 스타일
        'highlightthickness': 1,  # 테두리 두께
        'highlightcolor': '#ffffff',  # 테두리 색상
        'highlightbackground': '#666666'  # 비활성 상태 테두리 색상
    }
    
    # 3. 단어 범위 섹션
    section_frame3 = tk.Frame(settings_frame, bg='#2e2e2e')
    section_frame3.pack(pady=10, fill='x')
    
    # 섹션 제목과 내용을 같은 줄에 배치
    section_header3 = tk.Frame(section_frame3, bg='#2e2e2e')
    section_header3.pack(fill='x', padx=20)
    tk.Label(section_header3, text="3. 단어 범위", font=("Helvetica", 26, "bold"), fg='#4CAF50', bg='#2e2e2e', anchor='w').pack(side='left', padx=(0, 20))
    
    # 단어 범위 프레임 (같은 줄에 추가)
    range_frame = tk.Frame(section_header3, bg='#2e2e2e')
    range_frame.pack(side='left', fill='x')
    
    tk.Label(range_frame, text="시작:", font=label_font, fg='white', bg='#2e2e2e', width=4, anchor='w').pack(side='left', padx=(5, 0))
    tk.Entry(range_frame, textvariable=start_var, **entry_style).pack(side='left', padx=(0, 10))
    tk.Label(range_frame, text="끝:", font=label_font, fg='white', bg='#2e2e2e', width=4, anchor='w').pack(side='left', padx=(5, 0))
    tk.Entry(range_frame, textvariable=end_var, **entry_style).pack(side='left', padx=(0, 10))
    
    # 4. 반복 설정 섹션
    section_frame4 = tk.Frame(settings_frame, bg='#2e2e2e')
    section_frame4.pack(pady=10, fill='x')
    
    # 섹션 제목과 내용을 같은 줄에 배치
    section_header4 = tk.Frame(section_frame4, bg='#2e2e2e')
    section_header4.pack(fill='x', padx=20)
    tk.Label(section_header4, text="4. 반복 설정", font=("Helvetica", 26, "bold"), fg='#4CAF50', bg='#2e2e2e', anchor='w').pack(side='left', padx=(0, 20))
    
    # 반복 설정 프레임 (같은 줄에 추가)
    repeat_frame = tk.Frame(section_header4, bg='#2e2e2e')
    repeat_frame.pack(side='left', fill='x')
    
    # 영어 반복 레이블과 입력 필드
    eng_repeat_label = tk.Label(repeat_frame, text="영어:", font=label_font, fg='white', bg='#2e2e2e', width=4, anchor='w')
    eng_repeat_label.pack(side='left', padx=(5, 0))
    eng_repeat_entry = tk.Entry(repeat_frame, textvariable=eng_repeat_var, **entry_style)
    eng_repeat_entry.pack(side='left', padx=(0, 10))
    
    # 한글 반복 레이블과 입력 필드
    kor_repeat_label = tk.Label(repeat_frame, text="한국:", font=label_font, fg='white', bg='#2e2e2e', width=4, anchor='w')
    kor_repeat_label.pack(side='left', padx=(5, 0))
    kor_repeat_entry = tk.Entry(repeat_frame, textvariable=kor_repeat_var, **entry_style)
    kor_repeat_entry.pack(side='left', padx=(0, 10))
    
    # 중국어 반복 레이블과 입력 필드
    zh_repeat_label = tk.Label(repeat_frame, text="중국:", font=label_font, fg='white', bg='#2e2e2e', width=4, anchor='w')
    zh_repeat_label.pack(side='left', padx=(5, 0))
    zh_repeat_entry = tk.Entry(repeat_frame, textvariable=zh_repeat_var, **entry_style)
    zh_repeat_entry.pack(side='left', padx=(0, 10))
    
    # 5. 시간 설정 섹션
    section_frame5 = tk.Frame(settings_frame, bg='#2e2e2e')
    section_frame5.pack(pady=10, fill='x')
    
    # 섹션 제목과 내용을 같은 줄에 배치
    section_header5 = tk.Frame(section_frame5, bg='#2e2e2e')
    section_header5.pack(fill='x', padx=20, pady=(20, 10))
    tk.Label(section_header5, text="5. 시간 설정", font=("Helvetica", 26, "bold"), fg='#4CAF50', bg='#2e2e2e', anchor='w').pack(side='left', padx=(0, 20))
    
    # 시간 설정 프레임 (같은 줄에 추가)
    time_frame = tk.Frame(section_header5, bg='#2e2e2e')
    time_frame.pack(side='left', fill='x')
    
    # 첫 번째 간격 레이블과 입력 필드
    spacing_label = tk.Label(time_frame, text="간격:", font=label_font, fg='white', bg='#2e2e2e', width=4, anchor='w')
    spacing_label.pack(side='left', padx=(5, 0))
    tk.Entry(time_frame, textvariable=spacing_var, width=3, font=entry_font, bg='#3e3e3e', fg='white', insertbackground='white').pack(side='left', padx=(0, 10))
    
    # 툴팁 추가
    create_tooltip(spacing_label, "첫 단어와 해석 사이의 간격(초)")
    
    # 두 번째 간격 레이블과 입력 필드
    delay_label = tk.Label(time_frame, text="다음단어:", font=label_font, fg='white', bg='#2e2e2e', width=8, anchor='w')
    delay_label.pack(side='left', padx=(5, 0))
    tk.Entry(time_frame, textvariable=delay_var, width=3, font=entry_font, bg='#3e3e3e', fg='white', insertbackground='white').pack(side='left', padx=(0, 10))
    
    # 툴팁 추가
    create_tooltip(delay_label, "해석 후 다음 단어까지의 간격(초)")
    
    # 재생 속도 레이블과 입력 필드
    tk.Label(time_frame, text="속도:", font=label_font, fg='white', bg='#2e2e2e', width=4, anchor='w').pack(side='left', padx=(5, 0))
    tk.Entry(time_frame, textvariable=speed_var, width=3, font=entry_font, bg='#3e3e3e', fg='white', insertbackground='white').pack(side='left', padx=(0, 10))
    
    # 버튼 스타일 설정
    button_style = {
        'font': ("Helvetica", 24),
        'width': 12,
        'height': 2,
        'relief': 'raised'
    }
    
    # 버튼 프레임 위치 조정
    button_frame = tk.Frame(root, bg='#2e2e2e')
    button_frame.pack(side='bottom', pady=50)  # pady 20 -> 50으로 증가하여 위로 이동
    
    # 학습 시작 버튼 프레임
    start_button_frame = tk.Frame(button_frame, bg='#4CAF50', cursor='hand2')
    start_button_frame.pack(side='left', padx=10)
    
    # 학습 시작 버튼
    start_button = tk.Button(start_button_frame, 
                            text="학습 시작 📖",
                            command=start_learning,
                            bg='#4CAF50',
                            fg='black',
                            activebackground='#45a049',
                            activeforeground='black',
                            cursor='hand2',
                            **button_style)
    start_button.pack(expand=True, fill='both')
    
    # 버튼 프레임에도 클릭 이벤트 추가
    start_button_frame.bind('<Button-1>', lambda e: start_learning())
    
    # 녹화 시작 버튼 프레임
    record_button_frame = tk.Frame(button_frame, bg='#FF5722', cursor='hand2')
    record_button_frame.pack(side='left', padx=10)
    
    # 녹화 시작 버튼
    record_button = tk.Button(record_button_frame,
                             text="녹화 시작 🎥",
                             command=start_recording,
                             bg='#FF5722',
                             fg='black',
                             activebackground='#ff7043',
                             activeforeground='black',
                             cursor='hand2',
                             **button_style)
    record_button.pack(expand=True, fill='both')
    
    # 버튼 프레임에도 클릭 이벤트 추가
    record_button_frame.bind('<Button-1>', lambda e: start_recording())
    
    root.mainloop()

def return_to_initial(current_window):
    """초기화면으로 돌아가기"""
    if current_window is not None and current_window.winfo_exists():
        try:
            current_window.destroy()
        except:
            pass
    cleanup_temp_files()
    initial_setup()

def load_settings():
    try:
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # 필수 설정값 확인 및 기본값 적용
                for key, default_value in DEFAULT_SETTINGS.items():
                    if key not in settings:
                        settings[key] = default_value
                    # 음성 설정 유효성 검사
                    if key == 'zh_voice' and settings[key] not in chinese_voices:
                        settings[key] = 'XiaoXiao'  # 기본 중국어 음성
                    elif key == 'kor_voice' and settings[key] not in korean_voices:
                        settings[key] = '선희'  # 기본 한국어 음성
                return settings
        return DEFAULT_SETTINGS
    except Exception as e:
        print(f"설정 파일 로드 중 오류: {e}")
        return DEFAULT_SETTINGS

def save_settings(settings):
    """설정값을 파일에 저장"""
    try:
        # 현재 GUI의 모든 설정값을 저장
        current_settings = {
            'direction': direction_var.get(),
            'zh_voice': zh_voice_var.get(),
            'kor_voice': kor_voice_var.get(),
            'start_row': start_var.get(),
            'end_row': end_var.get(),
            'chinese_repeat': zh_repeat_var.get(),
            'korean_repeat': kor_repeat_var.get(),
            'word_delay': delay_var.get(),
            'spacing': spacing_var.get(),
            'speed': speed_var.get()
        }
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(current_settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"설정 파일 저장 중 오류: {e}")

# 영어 TTS 초기화 (전역 변수로 설정하여 재사용)
async def speak_edge_tts(text, output_file, voice="en-US-SteffanNeural", speed=1.0):
    """Edge TTS를 사용하여 텍스트를 음성으로 변환
    
    Args:
        text: 변환할 텍스트
        output_file: 저장할 파일 경로 (.wav)
        voice: 음성 ID
        speed: 재생 속도 (1.0이 기본)
    """
    try:
        # 배속 계산 (정확한 퍼센트 계산)
        speed_percentage = int((speed - 1.0) * 100)
        communicate = edge_tts.Communicate(text, voice, rate=f"+{speed_percentage}%")
        
        # 임시 MP3 파일로 먼저 저장
        temp_mp3 = output_file + ".temp.mp3"
        await communicate.save(temp_mp3)
        
        # MP3를 WAV로 변환
        try:
            audio_data = AudioSegment.from_mp3(temp_mp3)
            audio_data.export(output_file, format="wav")
            # 임시 파일 삭제
            if os.path.exists(temp_mp3):
                os.remove(temp_mp3)
        except Exception as e:
            print(f"오디오 변환 오류: {e}")
            # 변환 실패 시 원본 파일 이동
            if os.path.exists(temp_mp3):
                shutil.move(temp_mp3, output_file)
                
    except Exception as e:
        print(f"TTS 오류: {e}")
        traceback.print_exc()
        return False
    
    return True

def start_learning():
    """학습 시작 버튼 클릭 시 실행되는 함수"""
    # 현재 설정 저장
    current_settings = {
        'direction': direction_var.get(),
        'zh_voice': zh_voice_var.get(),
        'kor_voice': kor_voice_var.get(),
        'eng_voice': eng_voice_var.get(),
        'start_row': start_var.get(),
        'end_row': end_var.get(),
        'chinese_repeat': zh_repeat_var.get(),
        'korean_repeat': kor_repeat_var.get(),
        'english_repeat': eng_repeat_var.get(),
        'word_delay': delay_var.get(),
        'spacing': spacing_var.get(),
        'speed': speed_var.get()
    }
    
    save_settings(current_settings)
    
    root.destroy()
    settings = load_settings()
    
    # 언어 방향에 따라 반복 횟수 설정
    first_repeat = 1
    second_repeat = 1
    
    if settings['direction'] == '영한':
        first_repeat = int(settings['english_repeat'])
        second_repeat = int(settings['korean_repeat'])
    elif settings['direction'] == '한영':
        first_repeat = int(settings['korean_repeat'])
        second_repeat = int(settings['english_repeat'])
    elif settings['direction'] == '중한':
        first_repeat = int(settings['chinese_repeat'])
        second_repeat = int(settings['korean_repeat'])
    elif settings['direction'] == '한중':
        first_repeat = int(settings['korean_repeat'])
        second_repeat = int(settings['chinese_repeat'])
    elif settings['direction'] == '영중':
        first_repeat = int(settings['english_repeat'])
        second_repeat = int(settings['chinese_repeat'])
    else:  # 중영
        first_repeat = int(settings['chinese_repeat'])
        second_repeat = int(settings['english_repeat'])
    
    show_and_read_words(
        int(settings['start_row']),
        int(settings['end_row']),
        first_repeat,
        second_repeat,
        float(settings['speed']),
        float(settings['word_delay']),
        float(settings['spacing']),
        settings=settings
    )

def show_and_read_words(start_row, end_row, chinese_repeat, korean_repeat, speed, word_delay, spacing, settings=None):
    words = get_words_from_excel(start_row, end_row)
    if not words:  # 단어 목록이 비어있으면
        messagebox.showerror("에러", "단어 목록이 비어있습니다.\n엑셀 파일과 선택한 범위를 확인해주세요.")
        return_to_initial(None)  # 초기화면으로 돌아가기
        return
        
    # 언어 선택에 따른 단어 순서 변경
    direction = settings['direction']
    formatted_words = []
    for english, korean, chinese, row_num in words:
        if direction == '영한':
            formatted_words.append((english, korean, row_num))
        elif direction == '한영':
            formatted_words.append((korean, english, row_num))
        elif direction == '중한':
            formatted_words.append((chinese, korean, row_num))
        elif direction == '한중':
            formatted_words.append((korean, chinese, row_num))
        elif direction == '영중':
            formatted_words.append((english, chinese, row_num))
        elif direction == '중영':
            formatted_words.append((chinese, english, row_num))
    
    words = formatted_words
    total_words = len(words)
    is_paused = False
    current_after_id = None
    start_time = time.time()
    word_start_time = None
    start_time_str = time.strftime("%H:%M:%S")  # 시작 시각 문자열 저장
    
    # 설정값 로깅
    print(f"\n학습 설정")
    print(f"언어 선택: {settings['direction']}")
    print(f"간격: {settings['spacing']}초")
    print(f"다음 단어: {settings['word_delay']}초")
    print(f"재생 속도: {settings['speed']}배")
    if direction in ['영한', '한영']:
        print(f"영어 음성: {settings['eng_voice']}")
    else:
        print(f"중국어 음성: {settings['zh_voice']}")
    print(f"한글 음성: {settings['kor_voice']}")
    print(f"시작 시각: {start_time_str}")
    print("-" * 45)
    
    def format_time(seconds):
        """초를 mm:ss 형식으로 변환"""
        return f"{int(seconds//60):02d}:{int(seconds%60):02d}"

    async def prepare_first_audio():
        """첫 번째 단어의 음성만 생성"""
        audio_files = []
        first_word, second_word, _ = words[0]
        
        first_file = f'temp_first_0.wav'
        second_file = f'temp_second_0.wav'
        
        if direction == '영한':
            first_voice = english_voice_mapping[settings['eng_voice']]  # 영어 음성
            second_voice = korean_voice_mapping[settings['kor_voice']]  # 한글 음성
        elif direction == '한영':
            first_voice = korean_voice_mapping[settings['kor_voice']]  # 한글 음성
            second_voice = english_voice_mapping[settings['eng_voice']]  # 영어 음성
        elif direction == '중한':
            first_voice = chinese_voice_mapping[settings['zh_voice']]  # 중국어 음성
            second_voice = korean_voice_mapping[settings['kor_voice']]  # 한글 음성
        elif direction == '한중':
            first_voice = korean_voice_mapping[settings['kor_voice']]  # 한글 음성
            second_voice = chinese_voice_mapping[settings['zh_voice']]  # 중국어 음성
        elif direction == '영중':
            first_voice = english_voice_mapping[settings['eng_voice']]  # 영어 음성
            second_voice = chinese_voice_mapping[settings['zh_voice']]  # 중국어 음성
        else:  # 중영
            first_voice = chinese_voice_mapping[settings['zh_voice']]  # 중국어 음성
            second_voice = english_voice_mapping[settings['eng_voice']]  # 영어 음성
        
        first_text = first_word
        second_text = second_word
        
        # 배속 계산 수정 (정확한 퍼센트 계산)
        speed = float(settings['speed'])
        speed_percentage = int((speed - 1.0) * 100)
        
        # 첫 번째 음성 생성
        communicate = edge_tts.Communicate(first_text, first_voice, 
                                         rate=f"+{speed_percentage}%")
        await communicate.save(first_file)
        
        # 두 번째 음성 생성
        communicate = edge_tts.Communicate(second_text, second_voice, 
                                         rate=f"+{speed_percentage}%")
        await communicate.save(second_file)
        
        audio_files.extend([first_file, second_file])
        return audio_files
    
    async def prepare_remaining_audio(start_idx):
        """나머지 단어들의 음성을 백그라운드에서 생성"""
        audio_files = []
        for i, (first_word, second_word, row_num) in enumerate(words[start_idx:], start=start_idx):
            first_file = f'temp_first_{i}.wav'
            second_file = f'temp_second_{i}.wav'
            
            if direction == '영한':
                first_voice = english_voice_mapping[settings['eng_voice']]  # 영어 음성
                second_voice = korean_voice_mapping[settings['kor_voice']]  # 한글 음성
            elif direction == '한영':
                first_voice = korean_voice_mapping[settings['kor_voice']]  # 한글 음성
                second_voice = english_voice_mapping[settings['eng_voice']]  # 영어 음성
            elif direction == '중한':
                first_voice = chinese_voice_mapping[settings['zh_voice']]  # 중국어 음성
                second_voice = korean_voice_mapping[settings['kor_voice']]  # 한글 음성
            elif direction == '한중':
                first_voice = korean_voice_mapping[settings['kor_voice']]  # 한글 음성
                second_voice = chinese_voice_mapping[settings['zh_voice']]  # 중국어 음성
            elif direction == '영중':
                first_voice = english_voice_mapping[settings['eng_voice']]  # 영어 음성
                second_voice = chinese_voice_mapping[settings['zh_voice']]  # 중국어 음성
            else:  # 중영
                first_voice = chinese_voice_mapping[settings['zh_voice']]  # 중국어 음성
                second_voice = english_voice_mapping[settings['eng_voice']]  # 영어 음성
            
            first_text = first_word
            second_text = second_word
            
            # 배속 계산 수정 (정확한 퍼센트 계산)
            speed = float(settings['speed'])
            speed_percentage = int((speed - 1.0) * 100)
            
            # 첫 번째 음성 생성
            communicate = edge_tts.Communicate(first_text, first_voice, 
                                             rate=f"+{speed_percentage}%")
            await communicate.save(first_file)
            
            # 두 번째 음성 생성
            communicate = edge_tts.Communicate(second_text, second_voice, 
                                             rate=f"+{speed_percentage}%")
            await communicate.save(second_file)
            
            audio_files.extend([first_file, second_file])
        return audio_files

    async def play_audio_async(audio_file):
        """비동기 음성 재생"""
        try:
            if not os.path.exists(audio_file):
                print(f"파일을 찾을 수 없음: {audio_file}")
                return None
            
            # playsound를 사용하여 오디오 재생
            # 비동기 실행을 위해 별도 스레드에서 실행
            def play_sound():
                try:
                    playsound(audio_file)
                except Exception as e:
                    print(f"playsound 오류: {e}")
            
            # 스레드 생성 및 실행
            thread = threading.Thread(target=play_sound)
            thread.start()
            
            # 스레드가 종료될 때까지 대기
            while thread.is_alive():
                await asyncio.sleep(0.1)
                
            return audio_file
            
        except Exception as e:
            print(f"오디오 재생 오류: {e}")
            traceback.print_exc()
            return None

    def update_display(word_window, current_word, next_word=None, total_time=None, show_meaning=False):
        """화면 업데이트
        show_meaning: True이면 의미(두 번째 단어)도 표시, False이면 첫 번째 단어만 표시
        """
        # 진행 상황 업데이트
        current_index = words.index(current_word)
        progress_label.config(text=f"진행: {current_index + 1}/{total_words}")
        
        # 경과 시간 업데이트
        if total_time is not None:
            time_label.config(text=f"경과 시간: {format_time(total_time)}")
        
        # 단어 정보 업데이트
        number_label.config(text=f"{current_word[2]}번")
        word_label.config(text=current_word[0])  # 첫 번째 단어
        
        # 의미(두 번째 단어) 표시 여부에 따라 처리
        if show_meaning:
            meaning_label.config(text=current_word[1])  # 두 번째 단어 표시
            meaning_container.pack(pady=20, fill='x', padx=100)  # 의미 컨테이너 표시
        else:
            meaning_label.config(text="")  # 두 번째 단어 숨김
            meaning_container.pack_forget()  # 의미 컨테이너 숨김
        
        # 다음 단어 정보 업데이트
        if next_word and show_meaning:  # 의미가 표시될 때만 다음 단어도 표시
            next_label.config(text=f"next: {next_word[0]}")
            next_label.pack(pady=10)  # 다음 단어 레이블 표시
        else:
            next_label.config(text="")
            next_label.pack_forget()  # 다음 단어 레이블 숨김
        
        word_window.update()

    # 새 창 생성
    word_window = tk.Tk()
    word_window.title("단어 학습")
    word_window.geometry("1244x700+0+0")  # 16:9 비율로 변경 (가로 확장)
    word_window.configure(bg='#2e2e2e')

    # 윈도우 종료 플래그와 이벤트 루프 관리
    is_window_closed = False
    event_loop = None

    def on_closing():
        """윈도우가 닫힐 때 호출되는 함수"""
        nonlocal is_window_closed, event_loop
        is_window_closed = True
        
        # 이벤트 루프가 실행 중이면 모든 작업 취소
        if event_loop and not event_loop.is_closed():
            try:
                for task in asyncio.all_tasks(event_loop):
                    task.cancel()
            except Exception as e:
                print(f"작업 취소 중 오류: {e}")
        
        # 윈도우 종료
        try:
            word_window.destroy()
        except Exception as e:
            print(f"윈도우 종료 중 오류: {e}")
            
        # 초기 화면으로 돌아가기
        return_to_initial(None)

    word_window.protocol("WM_DELETE_WINDOW", on_closing)

    # 상단 정보 프레임
    info_frame = tk.Frame(word_window, bg='#2e2e2e')
    info_frame.pack(side='top', fill='x', pady=10)

    # 진행 상황 레이블
    progress_label = tk.Label(info_frame, text=f"진행: 0/{total_words}", 
                            font=("Helvetica", 24), fg='white', bg='#2e2e2e')  # 폰트 크기 증가
    progress_label.pack(side='left', padx=40)  # 패딩 증가

    # 경과 시간 레이블
    time_label = tk.Label(info_frame, text="경과 시간: 00:00", 
                         font=("Helvetica", 24), fg='white', bg='#2e2e2e')  # 폰트 크기 증가
    time_label.pack(side='right', padx=40)  # 패딩 증가

    # 단어 표시 프레임
    word_frame = tk.Frame(word_window, bg='#2e2e2e')
    word_frame.pack(expand=True, fill='both', padx=40, pady=(0, 20))  # 상단 패딩 감소
    
    # 단어 번호 레이블
    number_label = tk.Label(word_frame, text="", 
                           font=("Helvetica", 60, "bold"), fg='white', bg='#2e2e2e')  # 폰트 크기 증가
    number_label.pack(pady=(0, 10))  # 상단 패딩 감소
    
    # 단어 레이블 (가독성 향상을 위한 배경 추가)
    word_container = tk.Frame(word_frame, bg='#3e3e3e', padx=20, pady=10, 
                             relief='solid', borderwidth=0,
                             highlightbackground='#0A6E0A',  # 진한 초록색 외부 테두리
                             highlightcolor='#4CAF50',      # 밝은 초록색 내부 테두리
                             highlightthickness=9)          # 테두리 두께
    word_container.pack(pady=(0, 20), fill='x', padx=100)  # 상단 패딩 감소
    
    # 내부 테두리용 프레임
    inner_word_frame = tk.Frame(word_container, bg='#3e3e3e',
                               highlightbackground='#4CAF50',  # 밝은 초록색 내부 테두리
                               highlightcolor='#4CAF50',
                               highlightthickness=6)
    inner_word_frame.pack(fill='both', expand=True)
    
    word_label = tk.Label(inner_word_frame, text="", 
                         font=("Helvetica", 110, "bold"), fg='#4CAF50', bg='#3e3e3e')  # 초록색으로 변경
    word_label.pack(pady=10)
    
    # 의미 레이블 (가독성 향상을 위한 배경 추가)
    meaning_container = tk.Frame(word_frame, bg='#3e3e3e', padx=20, pady=10,
                                relief='solid', borderwidth=0,
                                highlightbackground='#0A4C6E',  # 진한 파란색 외부 테두리
                                highlightcolor='#2196F3',      # 밝은 파란색 내부 테두리
                                highlightthickness=9)          # 테두리 두께
    meaning_container.pack(pady=(0, 20), fill='x', padx=100)  # 상단 패딩 감소
    
    # 내부 테두리용 프레임
    inner_meaning_frame = tk.Frame(meaning_container, bg='#3e3e3e',
                                  highlightbackground='#2196F3',  # 밝은 파란색 내부 테두리
                                  highlightcolor='#2196F3',
                                  highlightthickness=6)
    inner_meaning_frame.pack(fill='both', expand=True)
    
    meaning_label = tk.Label(inner_meaning_frame, text="", 
                            font=("Helvetica", 90, "bold"), fg='white', bg='#3e3e3e')  # 폰트 크기 증가
    meaning_label.pack(pady=10)
    
    # 다음 단어 레이블
    next_label = tk.Label(word_frame, text="", 
                         font=("Helvetica", 54), fg='#aaaaaa', bg='#2e2e2e')  # 폰트 크기 증가, 색상 밝게
    next_label.pack(pady=(0, 10))  # 상단 패딩 감소
    
    # 설정 정보 레이블 (하단에 추가)
    settings_info = f"{direction} 간격: {settings['spacing']}초  |  다음 단어: {settings['word_delay']}초  |  배속: {settings['speed']}배"
    settings_label = tk.Label(word_frame, text=settings_info,
                            font=("Helvetica", 22), fg='#aaaaaa', bg='#2e2e2e')  # 폰트 크기 증가, 색상 밝게
    settings_label.pack(side='bottom', pady=10)

    # 버튼 프레임
    button_frame = tk.Frame(word_window, bg='#2e2e2e')
    button_frame.pack(side='bottom', pady=20)

    # 일시정지/재생 버튼 - 더 강한 색상 대비와 테두리 추가
    pause_button = tk.Button(
        button_frame, 
        text="일시정지", 
        command=lambda: toggle_pause(), 
        font=("Helvetica", 22, "bold"),
        bg='#4CAF50',  # 녹색 배경
        fg='black',    # 검은색 글씨로 변경하여 대비 강화
        activebackground='#45a049',  # 클릭 시 색상
        activeforeground='white',    # 클릭 시 글씨 색상
        relief=tk.RAISED,            # 버튼 테두리 스타일
        bd=3,                        # 테두리 두께
        padx=20, 
        pady=10
    )
    pause_button.pack(side='left', padx=20)

    # 처음으로 버튼 - 더 강한 색상 대비와 테두리 추가
    restart_button = tk.Button(
        button_frame, 
        text="처음으로", 
        command=lambda: return_to_initial(word_window), 
        font=("Helvetica", 22, "bold"),
        bg='#FF9800',  # 주황색 배경
        fg='black',    # 검은색 글씨로 변경하여 대비 강화
        activebackground='#e68a00',  # 클릭 시 색상
        activeforeground='white',    # 클릭 시 글씨 색상
        relief=tk.RAISED,            # 버튼 테두리 스타일
        bd=3,                        # 테두리 두께
        padx=20, 
        pady=10
    )
    restart_button.pack(side='left', padx=20)
    
    # 학습종료 버튼 - 더 강한 색상 대비와 테두리 추가
    exit_button = tk.Button(
        button_frame, 
        text="학습종료", 
        command=lambda: show_stats_and_exit(), 
        font=("Helvetica", 22, "bold"),
        bg='#F44336',  # 빨간색 배경
        fg='black',    # 검은색 글씨로 변경하여 대비 강화
        activebackground='#d32f2f',  # 클릭 시 색상
        activeforeground='white',    # 클릭 시 글씨 색상
        relief=tk.RAISED,            # 버튼 테두리 스타일
        bd=3,                        # 테두리 두께
        padx=20, 
        pady=10
    )
    exit_button.pack(side='left', padx=20)

    def toggle_pause():
        """일시정지/재생 토글"""
        nonlocal is_paused
        is_paused = not is_paused
        pause_button.config(
            text="재생" if is_paused else "일시정지", 
            bg='#2196F3' if is_paused else '#4CAF50',  # 상태에 따라 색상 변경
            fg='black'  # 글씨 색상 유지
        )
    
    def show_stats_and_exit():
        """학습 통계를 표시하고 초기화면으로 복귀"""
        nonlocal is_paused, is_window_closed
        
        # 일시정지 상태로 변경
        is_paused = True
        
        # 현재 시간 계산
        elapsed_time = time.time() - start_time
        
        # 통계 창 생성
        stats_window = tk.Toplevel(word_window)
        stats_window.title("학습 통계")
        stats_window.geometry("800x500+0+0")
        stats_window.configure(bg='#2e2e2e')
        stats_window.transient(word_window)  # 부모 창 위에 표시
        stats_window.grab_set()  # 모달 창으로 설정
        
        # 통계 프레임
        stats_frame = tk.Frame(stats_window, bg='#2e2e2e', padx=40, pady=40)
        stats_frame.pack(expand=True, fill='both')
        
        # 제목
        tk.Label(stats_frame, text="학습 통계", font=("Helvetica", 36, "bold"), 
                fg='white', bg='#2e2e2e').pack(pady=(0, 30))
        
        # 통계 정보
        stats_info = [
            f"학습 단어 수: {total_words}개",
            f"학습 시간: {format_time(elapsed_time)}",
            f"단어당 평균 시간: {format_time(elapsed_time/total_words) if total_words > 0 else '0:00'}",
            f"언어 방향: {settings['direction']}",
            f"학습 범위: {settings['start_row']}~{settings['end_row']}"
        ]
        
        # 통계 정보 표시
        for info in stats_info:
            tk.Label(stats_frame, text=info, font=("Helvetica", 24), 
                    fg='white', bg='#2e2e2e', anchor='w').pack(pady=10, fill='x')
        
        # 3초 후 초기화면으로 복귀
        stats_window.after(3000, lambda: [stats_window.destroy(), return_to_initial(word_window)])
        
        # 창 중앙에 표시
        stats_window.update_idletasks()
        width = stats_window.winfo_width()
        height = stats_window.winfo_height()
        x = (stats_window.winfo_screenwidth() // 2) - (width // 2)
        y = (stats_window.winfo_screenheight() // 2) - (height // 2)
        stats_window.geometry(f'{width}x{height}+{x}+{y}')

    async def play_words():
        """단어 재생"""
        nonlocal current_after_id, word_start_time, event_loop, is_window_closed
        temp_files = []
        start_learning_time = time.time()

        try:
            # 첫 번째 단어의 음성 파일 생성
            first_audio_files = await prepare_first_audio()
            if not first_audio_files or len(first_audio_files) != 2:
                print("Error: Failed to prepare first audio files")
                return
            
            # 나머지 단어들의 음성 파일 생성을 백그라운드에서 시작
            remaining_task = asyncio.create_task(prepare_remaining_audio(1))

            for i, (first_word, second_word, row_num) in enumerate(words):
                if is_window_closed:
                    break

                try:
                    if i > 0:  # 첫 번째 단어 이후부터는 백그라운드에서 생성된 파일 사용
                        first_file = f'temp_first_{i}.wav'
                        second_file = f'temp_second_{i}.wav'
                        
                        # 파일이 생성될 때까지 대기 (최대 5초)
                        wait_start = time.time()
                        while not (os.path.exists(first_file) and os.path.exists(second_file)):
                            if time.time() - wait_start > 5:
                                print(f"Error: Timeout waiting for audio files {first_file}, {second_file}")
                                return
                            await asyncio.sleep(0.1)
                            if is_window_closed:
                                return
                    else:  # 첫 번째 단어는 이미 생성된 파일 사용
                        first_file = first_audio_files[0]
                        second_file = first_audio_files[1]

                    temp_files.extend([first_file, second_file])

                    # 현재 단어와 다음 단어 정보
                    current_word = (first_word, second_word, row_num)
                    next_word = words[i + 1] if i < len(words) - 1 else None

                    # 첫 번째 단어만 표시 (의미 숨김)
                    if word_window.winfo_exists():
                        update_display(word_window, current_word, next_word, time.time() - start_learning_time, show_meaning=False)
                    else:
                        break

                    # 첫 번째 단어 재생 시작 시각 기록
                    current_time = time.strftime("%H:%M:%S.%03d", time.localtime())[:-4] + f"{int((time.time() % 1) * 1000):03d}"
                    print(f"[{current_time}] {row_num}번 {first_word}")

                    # 첫 번째 단어 반복 재생
                    first_repeat = int(settings['english_repeat']) if settings['direction'] in ['영한', '영중'] else \
                                 int(settings['chinese_repeat']) if settings['direction'] in ['중한', '중영'] else \
                                 int(settings['korean_repeat'])
                    
                    for _ in range(first_repeat):
                        if is_window_closed:
                            return
                        while is_paused:
                            if is_window_closed:
                                return
                            await asyncio.sleep(0.1)
                        await play_audio_async(first_file)

                    # 첫 번째 단어와 두 번째 단어 사이의 간격 (spacing)
                    if is_window_closed:
                        return
                    
                    # 첫 번째 단어 재생 완료 시각 기록
                    first_end_time = time.strftime("%H:%M:%S.%03d", time.localtime())[:-4] + f"{int((time.time() % 1) * 1000):03d}"
                    print(f"[{first_end_time}] 첫 번째 단어 재생 완료, {float(settings['spacing'])}초 대기")
                    
                    # 정확한 간격 적용
                    await asyncio.sleep(float(settings['spacing']))

                    # 두 번째 단어 재생 시작 시각 기록
                    current_time = time.strftime("%H:%M:%S.%03d", time.localtime())[:-4] + f"{int((time.time() % 1) * 1000):03d}"
                    print(f"[{current_time}] {row_num}번 {second_word}")

                    # 두 번째 화면 업데이트 (의미 표시) - 모든 단어에 대해 동일하게 처리
                    if is_window_closed:
                        return
                    try:
                        if word_window.winfo_exists():
                            # 화면 업데이트 확실히 적용
                            word_window.after(0, lambda: update_display(word_window, current_word, next_word, time.time() - start_learning_time, show_meaning=True))
                            # 업데이트가 적용될 시간 확보
                            await asyncio.sleep(0.1)
                        else:
                            break
                    except Exception as e:
                        print(f"Error during word playback: {e}")
                        break

                    # 두 번째 단어 반복 재생
                    second_repeat = int(settings['korean_repeat']) if settings['direction'] in ['영한', '중한'] else \
                                  int(settings['english_repeat']) if settings['direction'] in ['한영', '중영'] else \
                                  int(settings['chinese_repeat'])
                    
                    # 마지막 단어인 경우에도 두 번째 단어를 재생하도록 보장
                    for _ in range(max(1, second_repeat)):  # 최소 1회 이상 재생 보장
                        if is_window_closed:
                            return
                        while is_paused:
                            if is_window_closed:
                                return
                            await asyncio.sleep(0.1)
                        # 두 번째 단어 재생 중에도 화면 업데이트 유지
                        if is_window_closed:
                            return
                        try:
                            if word_window.winfo_exists():
                                word_window.after(0, lambda: update_display(word_window, current_word, next_word, time.time() - start_learning_time, show_meaning=True))
                        except Exception as e:
                            print(f"Error in play_words: {e}")
                            break
                        await play_audio_async(second_file)
                    
                    # 두 번째 단어 재생 완료 시각 기록
                    second_end_time = time.strftime("%H:%M:%S.%03d", time.localtime())[:-4] + f"{int((time.time() % 1) * 1000):03d}"
                    print(f"[{second_end_time}] 두 번째 단어 재생 완료")

                    # 다음 단어로 넘어가기 전 대기 또는 마지막 단어 후 통계 표시 전 대기
                    if i < len(words) - 1:  # 마지막 단어가 아닌 경우
                        if is_window_closed:
                            return
                        print(f"[{second_end_time}] 다음 단어로 넘어가기 전 {float(settings['word_delay'])}초 대기")
                        await asyncio.sleep(float(settings['word_delay']))
                    else:  # 마지막 단어인 경우
                        # 마지막 단어 재생 후 2초 대기 (화면 유지)
                        print(f"[{second_end_time}] 마지막 단어 재생 완료, 통계 표시 전 2초 대기")
                        # 화면 업데이트 상태 유지
                        if word_window.winfo_exists():
                            word_window.after(0, lambda: update_display(word_window, current_word, next_word, time.time() - start_learning_time, show_meaning=True))
                        await asyncio.sleep(2.0)
                        
                        # 통계 창 표시
                        if word_window.winfo_exists() and not is_window_closed:
                            print("통계 창 표시 중...")
                            word_window.after(0, show_stats_and_exit)
                            return  # 함수 종료

                except Exception as e:
                    print(f"Error during word playback: {e}")
                    traceback.print_exc()
                    if not word_window.winfo_exists():
                        break
            
            # 모든 단어 학습 완료 후 통계 표시 (마지막 단어가 아닌 경우에만 실행됨)
            if word_window.winfo_exists() and not is_window_closed:
                print("모든 단어 학습 완료, 통계 창 표시 중...")
                word_window.after(0, show_stats_and_exit)

        except Exception as e:
            print(f"Error in play_words: {e}")
        finally:
            # 임시 파일 정리
            for temp_file in temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                except Exception as e:
                    print(f"Error removing temp file {temp_file}: {e}")

    def run_async():
        nonlocal event_loop
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
        try:
            event_loop.run_until_complete(play_words())
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"비동기 실행 중 오류: {e}")
            traceback.print_exc()
        finally:
            # 모든 미완료 작업 취소
            pending_tasks = asyncio.all_tasks(event_loop)
            for task in pending_tasks:
                task.cancel()
            
            # 취소된 작업 완료 대기
            if pending_tasks:
                try:
                    event_loop.run_until_complete(asyncio.gather(*pending_tasks, return_exceptions=True))
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    print(f"작업 취소 중 오류: {e}")
            
            # 이벤트 루프 종료
            try:
                event_loop.run_until_complete(event_loop.shutdown_asyncgens())
                event_loop.close()
            except Exception as e:
                print(f"이벤트 루프 종료 중 오류: {e}")
                
    # 별도의 스레드에서 비동기 작업 실행
    thread = threading.Thread(target=run_async)
    thread.daemon = True
    thread.start()

    # 메인 루프 시작
    word_window.mainloop()

def get_words_from_excel(start_row, end_row):
    """엑셀 파일에서 단어 목록을 가져옴"""
    try:
        if not os.path.exists(EXCEL_PATH):
            messagebox.showerror("에러", f"엑셀 파일을 찾을 수 없습니다.\n파일 경로: {EXCEL_PATH}")
            return []
            
        # 파일 크기 확인
        if os.path.getsize(EXCEL_PATH) == 0:
            messagebox.showerror("에러", "엑셀 파일이 비어있습니다.")
            return []
            
        try:
            workbook = openpyxl.load_workbook(EXCEL_PATH, read_only=True, data_only=True)
            
            # 활성 시트 가져오기
            sheet = workbook.active
            if sheet is None:
                messagebox.showerror("에러", "엑셀 파일에 활성 시트가 없습니다.")
                return []
                
            # 시트의 최대 행 확인
            max_row = sheet.max_row
            
            if end_row > max_row:
                messagebox.showerror("에러", f"지정한 끝 행({end_row})이 시트의 최대 행({max_row})보다 큽니다.")
                return []
                
            words = []
            
            for row in range(start_row, min(end_row + 1, max_row + 1)):
                try:
                    english_cell = sheet[f'A{row}']  # 영어 단어 (A열)
                    korean_cell = sheet[f'B{row}']   # 한글 의미 (B열)
                    chinese_cell = sheet[f'C{row}']  # 중국어 단어 (C열)
                    
                    if english_cell is None or korean_cell is None or chinese_cell is None:
                        continue
                        
                    english_word = english_cell.value
                    korean_meaning = korean_cell.value
                    chinese_word = chinese_cell.value
                    
                    if english_word and korean_meaning and chinese_word:  # None 값 체크
                        # 문자열로 변환
                        english_word = str(english_word).strip()
                        korean_meaning = str(korean_meaning).strip()
                        chinese_word = str(chinese_word).strip()
                        
                        # 한글 띄어쓰기 정리
                        korean_meaning = korean_meaning.replace(" ", "")  # 모든 공백 제거
                        
                        words.append((english_word, korean_meaning, chinese_word, row))
                except Exception as e:
                    continue
                    
            workbook.close()
            
            if not words:
                messagebox.showerror("에러", f"지정한 범위({start_row}-{end_row})에서 단어를 찾을 수 없습니다.")
                return []
                
            return words
            
        except Exception as e:
            messagebox.showerror("엑셀 파일 오류", 
                f"엑셀 파일을 읽는 중 오류가 발생했습니다.\n"
                f"파일이 손상되었을 수 있습니다.\n"
                f"오류 내용: {str(e)}")
            return []
            
    except Exception as e:
        messagebox.showerror("에러", f"예상치 못한 오류가 발생했습니다.\n{str(e)}")
        traceback.print_exc()
        return []

async def create_word_video(words, output_path, settings):
    """단어 비디오 생성"""
    temp_files = []
    clips = []
    total_words = len(words)
    direction = settings['direction']
    
    try:
        # 임시 디렉토리 생성
        temp_dir = os.path.join(os.path.dirname(output_path), 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        # 설정 정보 문자열 생성
        settings_info = f"간격: {settings['spacing']}초  |  다음 단어: {settings['word_delay']}초  |  배속: {settings['speed']}배"
        
        for i, (first_word, second_word, row_num) in enumerate(words):
            # 첫 번째 화면 생성 (첫 번째 단어만 표시)
            first_text = f"{row_num}. {first_word}"
            first_img = create_word_image(first_text, total_words=total_words, is_first_screen=True)
            first_temp = os.path.join(temp_dir, f'temp_img_first_{i}.png')
            temp_files.append(first_temp)
            Image.fromarray(first_img).save(first_temp)
            
            # 첫 번째 음성 생성
            first_audio = os.path.join(temp_dir, f'temp_audio_first_{i}.wav')
            temp_files.append(first_audio)
            
            # 언어 방향에 따라 음성 선택
            if direction == '영한':
                first_voice = english_voice_mapping[settings['eng_voice']]
                second_voice = korean_voice_mapping[settings['kor_voice']]
            elif direction == '한영':
                first_voice = korean_voice_mapping[settings['kor_voice']]
                second_voice = english_voice_mapping[settings['eng_voice']]
            elif direction == '중한':
                first_voice = chinese_voice_mapping[settings['zh_voice']]
                second_voice = korean_voice_mapping[settings['kor_voice']]
            elif direction == '한중':
                first_voice = korean_voice_mapping[settings['kor_voice']]
                second_voice = chinese_voice_mapping[settings['zh_voice']]
            elif direction == '영중':
                first_voice = english_voice_mapping[settings['eng_voice']]
                second_voice = chinese_voice_mapping[settings['zh_voice']]
            else:  # 중영
                first_voice = chinese_voice_mapping[settings['zh_voice']]
                second_voice = english_voice_mapping[settings['eng_voice']]
            
            # 음성 생성 (MP3로 생성 후 WAV로 변환)
            try:
                communicate = edge_tts.Communicate(first_word, first_voice, rate=f"+{int((float(settings['speed'])-1)*100)}%")
                temp_mp3 = first_audio + ".temp.mp3"
                await communicate.save(temp_mp3)
                audio_data = AudioSegment.from_mp3(temp_mp3)
                audio_data.export(first_audio, format="wav")
                if os.path.exists(temp_mp3):
                    os.remove(temp_mp3)
            except Exception as e:
                print(f"첫 번째 단어 음성 생성 중 오류: {e}")
                # 오류 발생 시 빈 오디오 파일 생성
                silent_audio = AudioSegment.silent(duration=500)  # 500ms 무음
                silent_audio.export(first_audio, format="wav")
            
            # 첫 번째 클립 생성 - 첫 번째 단어 재생 후 spacing 시간만큼 지속
            first_clip = ImageClip(first_temp).set_duration(float(settings['spacing']))
            first_audio_clip = AudioFileClip(first_audio)
            first_clip = first_clip.set_audio(first_audio_clip)
            clips.append(first_clip)
            
            # 두 번째 화면 생성 (첫 번째 단어와 두 번째 단어 모두 표시)
            second_text = f"{row_num}. {first_word}\n{second_word}"
            if i < len(words) - 1:
                next_first, _, next_row = words[i + 1]
                second_text += f"\nNext: {next_first}"
            
            # 설정 정보 추가
            settings_info = f"간격: {settings['spacing']}초  |  다음 단어: {settings['word_delay']}초  |  배속: {settings['speed']}배"
            second_img = create_word_image(second_text, total_words=total_words, is_first_screen=False, settings_info=settings_info)
            second_temp = os.path.join(temp_dir, f'temp_img_second_{i}.png')
            temp_files.append(second_temp)
            Image.fromarray(second_img).save(second_temp)
            
            # 두 번째 음성 생성
            second_audio = os.path.join(temp_dir, f'temp_audio_second_{i}.wav')
            temp_files.append(second_audio)
            
            # 음성 생성 (MP3로 생성 후 WAV로 변환)
            try:
                communicate = edge_tts.Communicate(second_word, second_voice, rate=f"+{int((float(settings['speed'])-1)*100)}%")
                temp_mp3 = second_audio + ".temp.mp3"
                await communicate.save(temp_mp3)
                audio_data = AudioSegment.from_mp3(temp_mp3)
                audio_data.export(second_audio, format="wav")
                if os.path.exists(temp_mp3):
                    os.remove(temp_mp3)
            except Exception as e:
                print(f"두 번째 단어 음성 생성 중 오류: {e}")
                # 오류 발생 시 빈 오디오 파일 생성
                silent_audio = AudioSegment.silent(duration=500)  # 500ms 무음
                silent_audio.export(second_audio, format="wav")
            
            # 두 번째 클립 생성 - 두 번째 단어 재생 후 word_delay 시간만큼 지속
            second_clip = ImageClip(second_temp).set_duration(float(settings['word_delay']))
            second_audio_clip = AudioFileClip(second_audio)
            second_clip = second_clip.set_audio(second_audio_clip)
            clips.append(second_clip)
        
        # 최종 비디오 생성
        final_clip = concatenate_videoclips(clips)
        final_clip.write_videofile(
            output_path, 
            fps=30,  # fps 증가
            codec='libx264', 
            audio_codec='aac',
            bitrate='8000k'  # 비트레이트 설정 추가
        )
        
    except Exception as e:
        print(f"비디오 생성 중 오류: {e}")
        traceback.print_exc()
    finally:
        # 임시 파일 정리
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"Error removing temp file {temp_file}: {e}")
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Error removing temp directory {temp_dir}: {e}")

def create_word_image(word, font_size=80, width=1920, height=1080, is_first_screen=True, total_words=10, settings_info=None):
    """단어 이미지 생성
    is_first_screen: True이면 첫 번째 단어만 표시, False이면 첫 번째 단어와 두 번째 단어 모두 표시
    """
    # 고해상도 이미지 생성 (1920x1080)
    image = Image.new('RGB', (width, height), color='#2e2e2e')
    draw = ImageDraw.Draw(image)
    
    try:
        # macOS 시스템 폰트 경로
        korean_font_path = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
        chinese_font_path = "/System/Library/Fonts/STHeiti Medium.ttc"  # 중국어 폰트 추가
        
        # 중국어 문자 감지 함수
        def contains_chinese(text):
            if text:
                for char in text:
                    if '\u4e00' <= char <= '\u9fff':
                        return True
            return False
        
        # 텍스트에 따라 적절한 폰트 선택
        def get_font(text, size):
            if contains_chinese(text):
                return ImageFont.truetype(chinese_font_path, size)
            else:
                return ImageFont.truetype(korean_font_path, size)
        
        # 고해상도에 맞게 폰트 크기 조정
        main_font_size = 170     # 메인 단어 폰트 크기
        number_font_size = 90    # 단어 번호
        progress_font_size = 36  # 진행률 폰트 크기
        next_font_size = 80      # 다음 단어 폰트 크기
        settings_font_size = 34  # 설정 정보 폰트 크기
        
        # 기본 폰트는 한국어 폰트로 설정
        number_font = ImageFont.truetype(korean_font_path, number_font_size)
        progress_font = ImageFont.truetype(korean_font_path, progress_font_size)
        settings_font = ImageFont.truetype(korean_font_path, settings_font_size)
        
        # main_font와 next_font는 텍스트 분석 후 설정
    except:
        main_font = ImageFont.load_default()
        number_font = ImageFont.load_default()
        progress_font = ImageFont.load_default()
        next_font = ImageFont.load_default()
        settings_font = ImageFont.load_default()
    
    # 테두리 두께 설정 - Edge600-706.py 스타일
    outer_border_width = 9
    inner_border_width = 6
    
    # 텍스트 분리
    parts = word.split("\nNext: ")
    main_text = parts[0]
    next_text = parts[1] if len(parts) > 1 else None
    
    # 메인 텍스트 처리
    if ". " in main_text:
        number, text = main_text.split(". ", 1)
        if number.isdigit():
            number = int(number)
            words = text.split("\n")
            
            # 상단 정보 프레임 (진행 상황)
            progress_text = f"진행: {number}/{total_words}"
            draw.text((60, 30), progress_text, font=progress_font, fill='white')
            
            # 경과 시간 (녹화에서는 표시하지 않음)
            # 대신 오른쪽에 단어 번호 표시
            number_text = f"{number}번"
            draw.text((width - 180, 30), number_text, font=progress_font, fill='white')
            
            # 단어와 의미 표시 (중국어 폰트 적용)
            if len(words) >= 1:
                first_word = words[0]
                
                # 첫 번째 단어 폰트 선택
                main_font_first = get_font(first_word, main_font_size)
                
                # 텍스트 위치 계산 및 그리기
                bbox1 = draw.textbbox((0, 0), first_word, font=main_font_first)
                text_width1 = bbox1[2] - bbox1[0]
                text_height1 = bbox1[3] - bbox1[1]
                x1 = (width - text_width1) // 2
                y1 = height * 0.3 - 30  # 위치 조정
                
                # 단어 배경 그리기
                padding = 30
                # 학습 화면과 동일한 비율로 너비 조정
                box_width = width - 300  # 전체 너비에서 좌우 패딩 제외
                box_x_start = (width - box_width) // 2
                box_x_end = box_x_start + box_width
                
                # Edge600-706.py 스타일의 이중 테두리 적용
                # 바깥쪽 테두리 - 진한 초록색
                outer_color = '#0A6E0A'  # 진한 초록색
                draw.rectangle([(box_x_start - outer_border_width, y1 - padding - outer_border_width), 
                               (box_x_end + outer_border_width, y1 + text_height1 + padding + outer_border_width)], 
                              fill=outer_color)
                
                # 안쪽 배경
                draw.rectangle([(box_x_start, y1 - padding), 
                               (box_x_end, y1 + text_height1 + padding)], 
                              fill='#3e3e3e')
                
                # 안쪽 테두리 - 밝은 초록색
                inner_color = '#4CAF50'  # 밝은 초록색
                draw.rectangle([(box_x_start, y1 - padding), 
                               (box_x_end, y1 + text_height1 + padding)], 
                              outline=inner_color, width=inner_border_width)
                
                # 단어 텍스트 그리기
                draw.text((x1, y1), first_word, font=main_font_first, fill='#4CAF50')  # 초록색으로 변경
                
                # 두 번째 단어 (첫 화면이 아닐 때만)
                if not is_first_screen and len(words) > 1:
                    second_word = words[1]
                    main_font_second = get_font(second_word, main_font_size)
                    
                    bbox2 = draw.textbbox((0, 0), second_word, font=main_font_second)
                    text_width2 = bbox2[2] - bbox2[0]
                    text_height2 = bbox2[3] - bbox2[1]
                    x2 = (width - text_width2) // 2
                    y2 = height * 0.55 - 30  # 위치 조정
                    
                    # 의미 배경 그리기 - Edge600-706.py 스타일의 이중 테두리 적용
                    # 바깥쪽 테두리 - 진한 파란색
                    outer_color_meaning = '#0A4C6E'  # 진한 파란색
                    draw.rectangle([(box_x_start - outer_border_width, y2 - padding - outer_border_width), 
                                   (box_x_end + outer_border_width, y2 + text_height2 + padding + outer_border_width)], 
                                  fill=outer_color_meaning)
                    
                    # 안쪽 배경
                    draw.rectangle([(box_x_start, y2 - padding), 
                                   (box_x_end, y2 + text_height2 + padding)], 
                                  fill='#3e3e3e')
                    
                    # 안쪽 테두리 - 밝은 파란색
                    inner_color_meaning = '#2196F3'  # 밝은 파란색
                    draw.rectangle([(box_x_start, y2 - padding), 
                                   (box_x_end, y2 + text_height2 + padding)], 
                                  outline=inner_color_meaning, width=inner_border_width)
                    
                    # 의미 텍스트 그리기
                    draw.text((x2, y2), second_word, font=main_font_second, fill='white')
                    
                    # 다음 단어 표시 (두 번째 화면에서만)
                    if next_text:
                        next_display = f"next: {next_text}"
                        # 다음 단어에 맞는 폰트 선택
                        next_font = get_font(next_text, next_font_size)
                        bbox_next = draw.textbbox((0, 0), next_display, font=next_font)
                        text_width_next = bbox_next[2] - bbox_next[0]
                        x_next = (width - text_width_next) // 2
                        y_next = height * 0.8 - 30  # 위치 조정
                        draw.text((x_next, y_next), next_display, font=next_font, fill='#aaaaaa')  # 색상 밝게
                
                # 설정 정보 (하단에 추가, 두 번째 화면에서만)
                if not is_first_screen:
                    if settings_info is None:
                        settings_info = "간격: 2초  |  다음 단어: 2초  |  배속: 1배"
                    # 설정 정보는 항상 한국어이므로 한국어 폰트 사용
                    settings_font = ImageFont.truetype(korean_font_path, settings_font_size)
                    bbox_settings = draw.textbbox((0, 0), settings_info, font=settings_font)
                    text_width_settings = bbox_settings[2] - bbox_settings[0]
                    x_settings = (width - text_width_settings) // 2
                    y_settings = height - 60  # 하단에 위치
                    draw.text((x_settings, y_settings), settings_info, font=settings_font, fill='#aaaaaa')
    
    return np.array(image)

def cleanup_temp_files():
    """임시 파일들을 삭제하는 함수"""
    try:
        # 임시 디렉토리 정리
        temp_dir = os.path.join(os.path.dirname(SCRIPT_DIR), 'temp')
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            
        # 현재 디렉토리의 임시 파일 정리
        for pattern in ['temp_*.wav', 'temp_*.wav.temp.wav', 'temp_first_*.wav', 'temp_second_*.wav']:
            for temp_file in glob.glob(pattern):
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except Exception as e:
                        print(f"파일 삭제 실패: {temp_file}, 오류: {e}")
                        
        # 스크립트 디렉토리의 임시 파일 정리
        script_dir_path = os.path.dirname(os.path.abspath(__file__))
        for pattern in ['temp_*.wav', 'temp_*.wav.temp.wav', 'temp_first_*.wav', 'temp_second_*.wav']:
            for temp_file in glob.glob(os.path.join(script_dir_path, pattern)):
                if os.path.exists(temp_file):
                    try:
                        os.remove(temp_file)
                    except Exception as e:
                        print(f"파일 삭제 실패: {temp_file}, 오류: {e}")
    except Exception as e:
        print(f"임시 파일 정리 중 오류: {e}")
        traceback.print_exc()

def start_recording():
    """녹화 시작 버튼 클릭 시 실행되는 함수"""
    # 현재 설정 저장
    current_settings = {
        'direction': direction_var.get(),
        'zh_voice': zh_voice_var.get(),
        'kor_voice': kor_voice_var.get(),
        'eng_voice': eng_voice_var.get(),
        'start_row': start_var.get(),
        'end_row': end_var.get(),
        'chinese_repeat': DEFAULT_SETTINGS['chinese_repeat'],
        'korean_repeat': DEFAULT_SETTINGS['korean_repeat'],
        'english_repeat': DEFAULT_SETTINGS['english_repeat'],
        'word_delay': delay_var.get(),
        'spacing': spacing_var.get(),
        'speed': speed_var.get()
    }
    
    save_settings(current_settings)
    
    root.destroy()
    settings = load_settings()
    
    # 단어 목록 가져오기
    words = get_words_from_excel(int(settings['start_row']), int(settings['end_row']))
    if not words:  # 단어 목록이 비어있으면
        messagebox.showerror("에러", "단어 목록이 비어있습니다.\n엑셀 파일과 선택한 범위를 확인해주세요.")
        return_to_initial(None)  # 초기화면으로 돌아가기
        return
    
    # 언어 선택에 따른 단어 순서 변경
    direction = settings['direction']
    formatted_words = []
    for english, korean, chinese, row_num in words:
        if direction == '영한':
            formatted_words.append((english, korean, row_num))
        elif direction == '한영':
            formatted_words.append((korean, english, row_num))
        elif direction == '중한':
            formatted_words.append((chinese, korean, row_num))
        elif direction == '한중':
            formatted_words.append((korean, chinese, row_num))
        elif direction == '영중':
            formatted_words.append((english, chinese, row_num))
        elif direction == '중영':
            formatted_words.append((chinese, english, row_num))
    
    # 바탕화면에 저장 폴더 생성
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    video_folder = os.path.join(desktop_path, 'WordVideo')
    os.makedirs(video_folder, exist_ok=True)
    
    # 현재 시간을 파일명에 추가하여 중복 방지
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    video_filename = f'단어학습_{settings["direction"]}_{settings["start_row"]}-{settings["end_row"]}_{timestamp}.mp4'
    video_path = os.path.join(video_folder, video_filename)
    
    # 변환된 단어 목록으로 비디오 생성
    try:
        asyncio.run(create_word_video(
            formatted_words,
            video_path,
            settings
        ))
        
        # 녹화 완료 후 메시지 표시
        messagebox.showinfo("녹화 완료", f"영상이 성공적으로 저장되었습니다.\n\n저장 위치: {video_path}")
    except Exception as e:
        messagebox.showerror("녹화 오류", f"영상 생성 중 오류가 발생했습니다.\n\n오류 내용: {str(e)}")
        print(f"비디오 생성 중 오류: {e}")
        traceback.print_exc()
    finally:
        # 초기 화면으로 돌아가기
        return_to_initial(None)

if __name__ == "__main__":
    try:
        initial_setup()
    except Exception as e:
        print(f"프로그램 실행 중 오류 발생: {e}")
        traceback.print_exc()
