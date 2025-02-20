import streamlit as st
import pandas as pd
import edge_tts
import asyncio
import os
import time
from pathlib import Path
import pygame
import wave
import soundfile as sf
from PIL import Image
import subprocess
import numpy as np
import traceback
import json
import base64
from gtts import gTTS
from pydub import AudioSegment
import io

## streamlit run en600st/en600_st_app.py

# 기본 경로 설정
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_PATH = SCRIPT_DIR / 'base/en600s-settings.json'
EXCEL_PATH = SCRIPT_DIR / 'base/en600new.xlsx'
TEMP_DIR = SCRIPT_DIR / 'temp'  # 임시 파일 저장 경로 추가

# base 폴더가 없으면 생성
if not (SCRIPT_DIR / 'base').exists():
    (SCRIPT_DIR / 'base').mkdir(parents=True)

# 언어 표시 매핑 수정
LANG_DISPLAY = {
    'korean': '한국어',
    'english': '영어',
    'chinese': '중국어',
    'japanese': '일본어',
    'vietnamese': '베트남어'  # 베트남어 추가
}

# 음성 매핑에 남성 음성 추가
VOICE_MAPPING = {
    'english': {
        "Steffan": "en-US-SteffanNeural",
        "Roger": "en-US-RogerNeural",
        "Sonia": "en-GB-SoniaNeural",
        "Brian": "en-US-BrianNeural",
        "Emma": "en-US-EmmaNeural",
        "Jenny": "en-US-JennyNeural",
        "Guy": "en-US-GuyNeural",
        "Aria": "en-US-AriaNeural",
        "Ryan": "en-GB-RyanNeural"
    },
    'korean': {
        "선희": "ko-KR-SunHiNeural",
        "인준": "ko-KR-InJoonNeural"
    },
    'chinese': {
        "샤오샤오": "zh-CN-XiaoxiaoNeural",
        "윈시": "zh-CN-YunxiNeural",
        "Yunjian": "zh-CN-YunjianNeural",
        "Yunyang": "zh-CN-YunyangNeural"
    },
    'japanese': {
        "Nanami": "ja-JP-NanamiNeural",
        "Keita": "ja-JP-KeitaNeural",
    },
    'vietnamese': {
        "HoaiMy": "vi-VN-HoaiMyNeural",  # 여성 음성
        "NamMinh": "vi-VN-NamMinhNeural"  # 남성 음성
    }
}

# 언어 설정
LANGUAGES = ['english', 'korean', 'chinese', 'japanese', 'vietnamese', 'none']

# 색상 매핑 추가
COLOR_MAPPING = {
    'white': '#FFFFFF',
    'black': '#000000',
    'green': '#00FF00',
    'blue': '#0000FF',
    'red': '#FF0000',
    'grey': '#808080',
    'ivory': '#FFFFF0',
    'pink': '#FFC0CB'
}

# Add this before the start_learning function
lang_mapping = {
    'english': {
        'text': lambda row: row[0],  # English text from column A
        'voice': lambda settings: get_voice_mapping('english', settings.get('eng_voice')),
        'second_voice': lambda settings: get_voice_mapping('english', settings.get('second_eng_voice')),  # 2순위 음성 추가
        'speed': lambda settings: settings.get('english_speed', 1.2)
    },
    'korean': {
        'text': lambda row: row[1],  # Korean text from column B
        'voice': lambda settings: get_voice_mapping('korean', settings.get('kor_voice')),
        'second_voice': lambda settings: get_voice_mapping('korean', settings.get('second_kor_voice')),  # 2순위 음성 추가
        'speed': lambda settings: settings.get('korean_speed', 1.2)
    },
    'chinese': {
        'text': lambda row: row[2],  # Chinese text from column C
        'voice': lambda settings: get_voice_mapping('chinese', settings.get('zh_voice')),
        'second_voice': lambda settings: get_voice_mapping('chinese', settings.get('second_zh_voice')),  # 2순위 음성 추가
        'speed': lambda settings: settings.get('chinese_speed', 1.2)
    },
    'japanese': {
        'text': lambda row: row[3],  # Japanese text from column D
        'voice': lambda settings: get_voice_mapping('japanese', settings.get('jp_voice')),
        'second_voice': lambda settings: get_voice_mapping('japanese', settings.get('second_jp_voice')),  # 2순위 음성 추가
        'speed': lambda settings: settings.get('japanese_speed', 1.2)
    },
    'vietnamese': {
        'text': lambda row: row[4],  # Vietnamese text from column E
        'voice': lambda settings: get_voice_mapping('vietnamese', settings.get('vi_voice')),
        'second_voice': lambda settings: get_voice_mapping('vietnamese', settings.get('second_vi_voice')),  # 2순위 음성 추가
        'speed': lambda settings: settings.get('vietnamese_speed', 1.2)
    }
}

def initialize_session_state():
    """강제 초기화 추가"""
    if 'initialized' not in st.session_state:
        st.session_state.clear()
        st.session_state.initialized = True
        st.session_state.page = 'settings'
        
    # 기본 설정값 정의
    default_settings = {
        'first_lang': 'korean',
        'second_lang': 'english',
        'third_lang': 'chinese',
        'first_repeat': 0,
        'second_repeat': 1,
        'third_repeat': 1,  
        'eng_voice': 'Steffan',
        'kor_voice': '선희',
        'zh_voice': 'Yunjian',
        'jp_voice': 'Nanami',
        'vi_voice': 'HoaiMy',
        'second_eng_voice': 'Roger',  # 2순위 영어 음성 추가
        'second_kor_voice': '인준',   # 2순위 한국어 음성 추가
        'second_zh_voice': 'Yunyang', # 2순위 중국어 음성 추가
        'second_jp_voice': 'Keita',   # 2순위 일본어 음성 추가
        'second_vi_voice': 'NamMinh', # 2순위 베트남어 음성 추가
        'start_row': 1,
        'end_row': 50,
        'word_delay': 1,
        'spacing': 1.0,          # 기본값 1.0으로 명시
        'subtitle_delay': 1.0,   # 기본값 1.0으로 명시
        'next_sentence_time': 1.0,  # 기본값 1.0으로 명시
        'english_speed': 1.2,
        'korean_speed': 1.2,
        'chinese_speed': 1.2,
        'japanese_speed': 1.2,
        'vietnamese_speed': 1.2,
        'keep_subtitles': True,
        'break_enabled': True,
        'break_interval': 10,
        'break_duration': 10,
        'auto_repeat': True,
        'repeat_count': 5,  # 기본 반복 횟수 추가
        'english_font': 'Pretendard',
        'korean_font': 'Pretendard',
        'chinese_font': 'SimSun',
        'english_font_size': 32,
        'korean_font_size': 32,
        'chinese_font_size': 30,
        'japanese_font': 'PretendardJP-Light',
        'japanese_font_size': 30,
        'hide_subtitles': {
            'first_lang': False,
            'second_lang': False,
            'third_lang': False,
        },
        'english_color': '#00FF00',  # 다크모드: 초록색, 브라이트모드: 검정색
        'korean_color': '#00FF00',   # 다크모드: 초록색, 브라이트모드: 검정색
        'chinese_color': '#00FF00',  # 다크모드: 초록색, 브라이트모드: 검정색
        'japanese_color': '#00FF00' if st.get_option("theme.base") == "dark" else '#FFFFFF',  # 다크모드: 초록색, 라이트모드: 흰색
        'vietnamese_color': '#00FF00' if st.get_option("theme.base") == "dark" else '#FFFFFF',  # 다크모드: 초록색, 라이트모드: 흰색
        'japanese_speed': 2.0,  # 일본어 배속 기본값 추가
        'vietnamese_font': 'Arial',  # 베트남어 폰트 기본값 추가
        'vietnamese_font_size': 30,
        'vietnamese_speed': 1.0,
        'final_sound_enabled': True,  # 종료 음악 활성화 여부
        'final_sound_duration': 60,   # 종료 음악 재생 시간 (초)
    }
    
    # 설정이 없는 경우 기본값으로 초기화
    if 'settings' not in st.session_state:
        st.session_state.settings = default_settings
    else:
        # 기존 설정에 누락된 값이 있으면 기본값으로 보완
        for key, value in default_settings.items():
            if key not in st.session_state.settings:
                st.session_state.settings[key] = value

    # 학습 시간 관련 변수 초기화
    if 'start_time' not in st.session_state:
        st.session_state.start_time = time.time()
    
    # 오늘 날짜 확인
    current_date = time.strftime('%Y-%m-%d')
    
    # 학습 시간 파일 경로
    study_time_path = SCRIPT_DIR / 'study_time.json'
    
    # 파일에서 학습 시간 데이터 로드
    try:
        if study_time_path.exists():
            with open(study_time_path, 'r') as f:
                study_data = json.load(f)
                if study_data.get('date') == current_date:
                    st.session_state.today_total_study_time = study_data.get('time', 0)
                else:
                    st.session_state.today_total_study_time = 0
        else:
            st.session_state.today_total_study_time = 0
    except Exception:
        st.session_state.today_total_study_time = 0
    
    st.session_state.today_date = current_date
    st.session_state.last_update_time = time.time()

    # 다크 모드 감지
    is_dark_mode = st.get_option("theme.base") == "dark"
    
    # temp 폴더가 없으면 생성
    if not TEMP_DIR.exists():
        TEMP_DIR.mkdir(parents=True)
    
    # break.wav 파일 존재 여부 확인
    break_sound_path = SCRIPT_DIR / './base/break.wav'
    if not break_sound_path.exists():
        st.warning("브레이크 알림음 파일이 없습니다. 기본 알림음을 생성합니다.")
        try:
            # 기본 알림음 생성 (북소리)
            communicate = edge_tts.Communicate("딩동", "ko-KR-SunHiNeural")
            asyncio.run(communicate.save(str(break_sound_path)))
        except Exception as e:
            st.error(f"알림음 생성 오류: {e}")

    # 베트남어 음성 설정 확실히 초기화
    if 'vi_voice' not in st.session_state.settings:
        st.session_state.settings['vi_voice'] = 'HoaiMy'
    
    # 설정 저장
    save_settings(st.session_state.settings)

def create_settings_ui(return_to_learning=False):
    """설정 화면 UI 생성 (return_to_learning: 학습 화면으로 복귀 여부)"""
    settings = st.session_state.settings

    if return_to_learning:
        # 학습 중 설정 모드 - 간소화된 UI
        st.subheader("학습 설정")
        
        # 자동 반복 설정
        repeat_options = ['없음', '1', '2', '3', '4', '5']
        current_repeat = str(settings.get('repeat_count', '3'))
        if current_repeat not in repeat_options:
            current_repeat = '3'  # 기본값
        settings['repeat_count'] = st.selectbox(
            "자동 반복(횟수)",
            options=repeat_options,
            index=repeat_options.index(current_repeat),
            key="repeat_count_learning"
        )
        settings['auto_repeat'] = settings['repeat_count'] != '없음'
        if settings['auto_repeat']:
            settings['repeat_count'] = int(settings['repeat_count'])

        # 휴식 간격 설정
        break_options = ['없음', '5', '10', '15', '20']
        current_break = str(settings.get('break_interval', '10'))
        if current_break not in break_options:
            current_break = '10'  # 기본값
        settings['break_interval'] = st.selectbox(
            "휴식 간격(문장)",
            options=break_options,
            index=break_options.index(current_break),
            key="break_interval_learning"
        )
        settings['break_enabled'] = settings['break_interval'] != '없음'
        if settings['break_enabled']:
            settings['break_interval'] = int(settings['break_interval'])

        # 음악 듣기 설정
        final_sound_options = ['없음', '30초', '1분', '1분30초', '2분']
        final_sound_mapping = {'없음': 0, '30초': 30, '1분': 60, '1분30초': 90, '2분': 120}
        current_duration = '없음'
        for option, duration in final_sound_mapping.items():
            if duration == settings.get('final_sound_duration', 0):
                current_duration = option
                break

        selected_duration = st.selectbox(
            "종료 후 음악 듣기",
            options=final_sound_options,
            index=final_sound_options.index(current_duration),
            key="final_sound_duration_learning"
        )
        settings['final_sound_enabled'] = selected_duration != '없음'
        settings['final_sound_duration'] = final_sound_mapping[selected_duration]

        # 저장/취소 버튼
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            if st.button("💾 저장 후 학습 재개", type="primary"):
                save_settings(settings)
                st.session_state.page = 'learning'
                st.rerun()
        with col2:
            if st.button("❌ 취소"):
                st.session_state.page = 'learning'
                st.rerun()
    else:
        # 기본 설정 모드 - 전체 UI
        # 다크 모드 감지
        is_dark_mode = st.get_option("theme.base") == "dark"
        
        # 현재 설정 가져오기
        settings = st.session_state.settings
        
        # 테마가 변경되었을 때 색상 자동 업데이트
        if is_dark_mode:
            if settings['korean_color'] == '#000000':  # 이전에 브라이트 모드였다면
                settings.update({
                    'english_color': '#00FF00',   # 초록색
                    'korean_color': '#FFFFFF',    # 흰색
                    'chinese_color': '#00FF00',   # 초록색
                    'japanese_color': '#00FF00',
                    'vietnamese_color': '#00FF00',
                })
        else:
            if settings['korean_color'] == '#FFFFFF':  # 이전에 다크 모드였다면
                settings.update({
                    'english_color': '#000000',   # 검정색
                    'korean_color': '#000000',    # 검정색
                    'chinese_color': '#000000',   # 검정색
                    'japanese_color': '#FFFFFF',
                    'vietnamese_color': '#FFFFFF',
                })
        
        # CSS 스타일 추가 (다크 모드 대응)
        st.markdown("""
            <style>
                /* 기본 텍스트 색상 */
                .st-emotion-cache-1v0mbdj {
                    color: white !important;
                }
                
                /* 제목 (h1) 폰트 크기 및 색상 조정 */
                .st-emotion-cache-10trblm {
                    font-size: 1.5rem !important;
                    margin-bottom: 0px !important;
                    color: white !important;
                }
                
                /* 부제목 (h2) 폰트 크기 및 색상 조정 */
                .st-emotion-cache-1629p8f h2 {
                    font-size: 1.2rem !important;
                    margin-top: 1rem !important;
                    margin-bottom: 0.5rem !important;
                    color: white !important;
                }
                
                /* 입력 필드 레이블 색상 */
                .st-emotion-cache-1a7c8b8 {
                    color: white !important;
                }
                
                /* 체크박스 및 라디오 버튼 색상 */
                .st-emotion-cache-1a7c8b8 label {
                    color: white !important;
                }
                
                /* 숫자 입력 필드 스타일 */
                div[data-testid="stNumberInput"] {
                    max-width: 150px;
                }
                
                /* 숫자 입력 필드 레이블 스타일 */
                div[data-testid="stNumberInput"] label {
                    font-size: 15px !important;
                    color: white !important;
                }
                
                /* 숫자 입력 필드 입력창 스타일 */
                div[data-testid="stNumberInput"] input {
                    font-size: 15px !important;
                    padding: 4px 8px !important;
                    color: white !important;
                    background-color: #1E1E1E !important;
                }
                
                /* 셀렉트 박스 스타일 */
                div[data-testid="stSelectbox"] label {
                    color: white !important;
                }
                
                /* 셀렉트 박스 입력창 스타일 */
                div[data-testid="stSelectbox"] select {
                    color: white !important;
                    background-color: #1E1E1E !important;
                }
                
                /* 체크박스 스타일 */
                div[data-testid="stCheckbox"] label {
                    color: white !important;
                }
                
                /* 색상 선택기 스타일 */
                div[data-testid="stColorPicker"] label {
                    color: white !important;
                }
            </style>
        """, unsafe_allow_html=True)
        
        settings = st.session_state.settings
        col1, col2 = st.columns([0.7, 0.3])
        with col1:
            st.markdown('<h1 style="font-size: 1.5rem; color: #00FF00;">도파민 대충영어 : 2배 한국어</h1>', unsafe_allow_html=True)
        with col2:
            # 엑셀 파일에서 최대 행 수 가져오기
            try:
                df = pd.read_excel(
                    EXCEL_PATH,
                    header=None,
                    engine='openpyxl'
                )
                max_row = len(df)
            except Exception as e:
                st.error(f"엑셀 파일 읽기 오류: {e}")
                return
            
            # 학습 시작 버튼 (첫 화면에서만 표시)
            if st.button("▶️ 학습 시작", use_container_width=True, key="start_btn"):
                st.session_state.page = 'learning'
                st.rerun()

        # 학습 시작 버튼 스타일
        st.markdown("""
            <style>
                /* 학습 시작/종료 버튼 스타일 */
                div[data-testid="stButton"] > button {
                    width: 100% !important;
                    height: 3em !important;
                    font-size: 1.2rem !important;
                }
            </style>
        """, unsafe_allow_html=True)

        # 시작/종료 번호와 반복 횟수 설정
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            settings['start_row'] = st.number_input("시작번호",
                                                  value=settings['start_row'],
                                                  min_value=1,
                                                  max_value=max_row,
                                                  key="start_row_input",
                                                  format="%d")
        with col2:
            settings['end_row'] = st.number_input("종료번호",
                                                value=settings['end_row'],
                                                min_value=1,
                                                max_value=max_row,
                                                key="end_row_input",
                                                format="%d")
        with col3:
            settings['repeat_count'] = st.selectbox("반복 횟수",
                                                 options=['없음', '1', '2', '3', '4', '5'],
                                                 index=0 if not settings.get('auto_repeat', True) else settings.get('repeat_count', 5),
                                                 key="repeat_count_input")
            settings['auto_repeat'] = settings['repeat_count'] != '없음'
            if settings['auto_repeat']:
                settings['repeat_count'] = int(settings['repeat_count'])

        # 언어 순위 설정
        st.subheader("자막 | 음성 | 속도")
        col1, col2, col3 = st.columns(3)
        with col1:
            settings['first_lang'] = st.selectbox("1번째     언어",
                options=['korean', 'english', 'chinese', 'japanese', 'vietnamese'],
                index=['korean', 'english', 'chinese', 'japanese', 'vietnamese'].index(settings['first_lang']),
                format_func=lambda x: LANG_DISPLAY[x],
                key="settings_first_lang")
            current_repeat = settings.get('first_repeat', 1)
            settings['first_repeat'] = st.selectbox("음성 재생(횟수)",
                                      options=[0, 1, 2, 3],
                                      index=current_repeat,
                                      format_func=lambda x: '없음' if x == 0 else f'{x}회',
                                      key="first_repeat")

        with col2:
            settings['second_lang'] = st.selectbox("2번째 언어",
                options=['korean', 'english', 'chinese', 'japanese', 'vietnamese'],
                index=['korean', 'english', 'chinese', 'japanese', 'vietnamese'].index(settings['second_lang']),
                format_func=lambda x: LANG_DISPLAY[x],
                key="settings_second_lang")
            # 2순위 음성 선택 추가
            if settings['second_lang'] == 'english':
                settings['second_eng_voice'] = st.selectbox("2순위 영어 음성",
                    options=list(VOICE_MAPPING['english'].keys()),
                    index=list(VOICE_MAPPING['english'].keys()).index(settings.get('second_eng_voice', 'Roger')),
                    key="second_eng_voice")
            elif settings['second_lang'] == 'korean':
                settings['second_kor_voice'] = st.selectbox("2순위 한국어 음성",
                    options=list(VOICE_MAPPING['korean'].keys()),
                    index=list(VOICE_MAPPING['korean'].keys()).index(settings.get('second_kor_voice', '인준')),
                    key="second_kor_voice")
            elif settings['second_lang'] == 'chinese':
                settings['second_zh_voice'] = st.selectbox("2순위 중국어 음성",
                    options=list(VOICE_MAPPING['chinese'].keys()),
                    index=list(VOICE_MAPPING['chinese'].keys()).index(settings.get('second_zh_voice', 'Yunyang')),
                    key="second_zh_voice")
            elif settings['second_lang'] == 'japanese':
                settings['second_jp_voice'] = st.selectbox("2순위 일본어 음성",
                    options=list(VOICE_MAPPING['japanese'].keys()),
                    index=list(VOICE_MAPPING['japanese'].keys()).index(settings.get('second_jp_voice', 'Keita')),
                    key="second_jp_voice")
            elif settings['second_lang'] == 'vietnamese':
                settings['second_vi_voice'] = st.selectbox("2순위 베트남어 음성",
                    options=list(VOICE_MAPPING['vietnamese'].keys()),
                    index=list(VOICE_MAPPING['vietnamese'].keys()).index(settings.get('second_vi_voice', 'NamMinh')),
                    key="second_vi_voice")

            current_repeat = settings.get('second_repeat', 1)
            settings['second_repeat'] = st.selectbox("음성 재생(횟수)",
                                       options=[0, 1, 2, 3],
                                       index=current_repeat,
                                       format_func=lambda x: '없음' if x == 0 else f'{x}회',
                                       key="second_repeat")

        with col3:
            settings['third_lang'] = st.selectbox("3번째 언어",
                options=['korean', 'english', 'chinese', 'japanese', 'vietnamese'],
                index=['korean', 'english', 'chinese', 'japanese', 'vietnamese'].index(settings['third_lang']),
                format_func=lambda x: LANG_DISPLAY[x],
                key="settings_third_lang")
            current_repeat = settings.get('third_repeat', 1)
            settings['third_repeat'] = st.selectbox("음성 재생(횟수)",
                                      options=[0, 1, 2, 3],
                                      index=current_repeat,
                                      format_func=lambda x: '없음' if x == 0 else f'{x}회',
                                      key="third_repeat")

        # 문장 재생 설정
        st.subheader("문장 재생")
        col1, col2, col3, col4 = st.columns(4)
        
        # 0.1초부터 2초까지 0.1초 간격의 옵션 생성
        time_options = [round(x * 0.1, 1) for x in range(1, 21)]  # 0.1-2.0초
        
        with col1:
            current_spacing = round(float(settings.get('spacing', 1.0)), 1)  # 기본값 1.0
            current_spacing = max(0.1, min(current_spacing, 2.0))
            try:
                spacing_index = time_options.index(current_spacing)
            except ValueError:
                spacing_index = time_options.index(1.0)  # 기본값 1.0초
            settings['spacing'] = st.selectbox("문장 간격(초)",
                                            options=time_options,
                                            index=spacing_index,
                                            key="spacing")

        with col2:
            current_delay = round(float(settings.get('subtitle_delay', 1.0)), 1)  # 기본값 1.0
            current_delay = max(0.1, min(current_delay, 2.0))
            try:
                delay_index = time_options.index(current_delay)
            except ValueError:
                delay_index = time_options.index(1.0)  # 기본값 1.0초
            settings['subtitle_delay'] = st.selectbox("자막 딜레이(초)",
                                                   options=time_options,
                                                   index=delay_index,
                                                   key="subtitle_delay")

        with col3:
            current_next = round(float(settings.get('next_sentence_time', 1.0)), 1)  # 기본값 1.0
            current_next = max(0.1, min(current_next, 2.0))
            try:
                next_index = time_options.index(current_next)
            except ValueError:
                next_index = time_options.index(1.0)  # 기본값 1.0초
            settings['next_sentence_time'] = st.selectbox("다음 문장(초)",
                                                       options=time_options,
                                                       index=next_index,
                                                       key="next_sentence_time")

        with col4:
            settings['break_interval'] = st.selectbox("브레이크 문장",
                                                  options=['없음', '5', '10', '15', '20'],
                                                  index=0 if not settings.get('break_enabled', True) else 
                                                        ['없음', '5', '10', '15', '20'].index(str(settings.get('break_interval', 10))),
                                                  key="break_interval_input")
            settings['break_enabled'] = settings['break_interval'] != '없음'
            if settings['break_enabled']:
                settings['break_interval'] = int(settings['break_interval'])

        # 자막 숨김 옵션을 한 줄로 배치하고 자막 유지 모드를 첫 번째로 이동
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            settings['keep_subtitles'] = st.checkbox("자막유지 모드",
                                                  value=settings.get('keep_subtitles', True),
                                                  key="keep_subtitles_checkbox")
        with col2:
            hide_first = st.checkbox("1번째 자막 숨김",
                                   value=settings['hide_subtitles']['first_lang'],
                                   key="first_hide")
        with col3:
            hide_second = st.checkbox("2번째 자막 숨김",
                                    value=settings['hide_subtitles']['second_lang'],
                                    key="second_hide")
        with col4:
            hide_third = st.checkbox("3번째 자막 숨김",
                                   value=settings['hide_subtitles']['third_lang'],
                                   key="third_hide")

        # 폰트 및 색상 설정 섹션
        st.subheader("폰트 크기 | 색깔")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            settings['korean_font_size'] = st.number_input("한글",
                                                        value=settings['korean_font_size'],
                                                        min_value=10,
                                                        max_value=50,
                                                        step=1,
                                                        key="korean_font_size_learning")
            default_color = 'green'  # 기본값을 초록색으로 변경
            selected_color = st.selectbox("한글",
                                        options=list(COLOR_MAPPING.keys()),
                                        index=list(COLOR_MAPPING.keys()).index(default_color),
                                        key="korean_color_select")
            settings['korean_color'] = COLOR_MAPPING[selected_color]

        with col2:
            settings['english_font_size'] = st.number_input("영어",
                                                        value=settings['english_font_size'],
                                                        min_value=10,
                                                        max_value=50,
                                                        step=1,
                                                        key="english_font_size_learning")
            default_color = 'green'  # 기본값을 초록색으로 변경
            selected_color = st.selectbox("영어",
                                        options=list(COLOR_MAPPING.keys()),
                                        index=list(COLOR_MAPPING.keys()).index(default_color),
                                        key="english_color_select")
            settings['english_color'] = COLOR_MAPPING[selected_color]

        with col3:
            settings['chinese_font_size'] = st.number_input("중국어",
                                                        value=settings['chinese_font_size'],
                                                        min_value=10,
                                                        max_value=50,
                                                        step=1,
                                                        key="chinese_font_size_learning")
            default_color = 'green'  # 기본값을 초록색으로 변경
            selected_color = st.selectbox("중국어",
                                        options=list(COLOR_MAPPING.keys()),
                                        index=list(COLOR_MAPPING.keys()).index(default_color),
                                        key="chinese_color_select")
            settings['chinese_color'] = COLOR_MAPPING[selected_color]

        with col4:
            settings['japanese_font_size'] = st.number_input("일본어",
                                                        value=settings['japanese_font_size'],
                                                        min_value=10,
                                                        max_value=50,
                                                        step=1,
                                                        key="japanese_font_size_learning")
            default_color = 'green' if st.get_option("theme.base") == "dark" else 'white'
            selected_color = st.selectbox("일본어",
                                        options=list(COLOR_MAPPING.keys()),
                                        index=list(COLOR_MAPPING.keys()).index(default_color),
                                        key="japanese_color_select")
            settings['japanese_color'] = COLOR_MAPPING[selected_color]

        with col5:
            settings['vietnamese_font_size'] = st.number_input("베트남어",
                                                        value=settings['vietnamese_font_size'],
                                                        min_value=10,
                                                        max_value=50,
                                                        step=1,
                                                        key="vietnamese_font_size_learning")
            default_color = 'green' if st.get_option("theme.base") == "dark" else 'white'
            selected_color = st.selectbox("베트남어",
                                          options=list(COLOR_MAPPING.keys()),
                                          index=list(COLOR_MAPPING.keys()).index(default_color),
                                          key="vietnamese_color_select")
            settings['vietnamese_color'] = COLOR_MAPPING[selected_color]

        # 폰트 크기 변경 시 즉시 반영을 위한 CSS 업데이트
        st.markdown(f"""
            <style>
                .english-text {{
                    font-size: {settings['english_font_size']}px !important;
                    color: {settings['english_color']} !important;
                }}
                .korean-text {{
                    font-size: {settings['korean_font_size']}px !important;
                    color: {settings['korean_color']} !important;
                }}
                .chinese-text {{
                    font-size: {settings['chinese_font_size']}px !important;
                    color: {settings['chinese_color']} !important;
                }}
                .japanese-text {{
                    font-size: {settings['japanese_font_size']}px !important;
                    color: {settings['japanese_color']} !important;
                }}
                .vietnamese-text {{
                    font-size: {settings['vietnamese_font_size']}px !important;
                    color: {settings['vietnamese_color']} !important;
                }}
            </style>
        """, unsafe_allow_html=True)

        # 입력 필드에 CSS 클래스 적용
        st.markdown("""
            <style>
                /* 숫자 입력 필드 스타일 */
                div[data-testid="stNumberInput"] {
                    max-width: 150px;
                }
                
                /* 숫자 입력 필드 레이블 스타일 */
                div[data-testid="stNumberInput"] label {
                    font-size: 15px !important;
                }
                
                /* 숫자 입력 필드 입력창 스타일 */
                div[data-testid="stNumberInput"] input {
                    font-size: 15px !important;
                    padding: 4px 8px !important;
                }
            </style>
        """, unsafe_allow_html=True)

        # 저장/취소 버튼
        col1, col2 = st.columns([0.8, 0.2])
        with col1:
            if st.button("💾 저장 후 학습 재개", type="primary"):
                save_settings(settings)
                if return_to_learning:
                    st.session_state.page = 'learning'
                    st.rerun()
        with col2:
            if st.button("❌ 취소"):
                if return_to_learning:
                    st.session_state.page = 'learning'
                    st.rerun()

        # 저장/취소 버튼 스타일
        st.markdown("""
            <style>
                /* 저장 버튼 스타일 */
                div[data-testid="stButton"] > button:first-child {
                    background-color: #00FF00 !important;
                    color: black !important;
                }
                /* 취소 버튼 스타일 */
                div[data-testid="stButton"] > button:last-child {
                    background-color: #FF0000 !important;
                    color: white !important;
                }
            </style>
        """, unsafe_allow_html=True)

def get_voice_mapping(language, voice_setting):
    """안전하게 음성 매핑을 가져오는 함수"""
    try:
        # 기본값 설정
        default_voices = {
            'korean': '선희',
            'english': 'Steffan',
            'chinese': 'Yunjian',
            'japanese': 'Nanami',
            'vietnamese': 'HoaiMy'
        }
        
        # 설정된 음성이 없거나 매핑에 없는 경우 기본값 사용
        if not voice_setting or voice_setting not in VOICE_MAPPING.get(language, {}):
            voice_setting = default_voices.get(language)
            
        return VOICE_MAPPING[language][voice_setting]
    except Exception as e:
        st.error(f"음성 매핑 오류 ({language}): {str(e)}")
        # 기본값 반환
        return VOICE_MAPPING[language][default_voices[language]]

async def create_audio(text, voice, speed=1.0):
    """음성 파일 생성 함수 수정"""
    try:
        if not text or not voice:
            return None

        output_file = TEMP_DIR / f"temp_{int(time.time()*1000)}.wav"
        
        # 속도 설정을 percentage로 변환
        if speed > 1:
            rate_str = f"+{int((speed - 1) * 100)}%"
        else:
            rate_str = f"-{int((1 - speed) * 100)}%"

        communicate = edge_tts.Communicate(text, voice, rate=rate_str)
        await communicate.save(str(output_file))
        return str(output_file)

    except Exception as e:
        st.error(f"음성 생성 오류: {str(e)}")
        return None

def create_learning_ui():
    """학습 화면 UI 생성"""
    
    # 상단 컬럼 생성 - 진행 상태와 배속 정보를 위한 컬럼
    col1, col2 = st.columns([0.7, 0.3])
    
    with col1:
        progress = st.progress(0)
        status = st.empty()
    
        # 배속 정보 표시
        speed_info = []
        
        # 순위에 따라 실제 재생되는 음성의 배속만 표시
        for lang, repeat in [
            (st.session_state.settings['first_lang'], st.session_state.settings['first_repeat']),
            (st.session_state.settings['second_lang'], st.session_state.settings['second_repeat']),
            (st.session_state.settings['third_lang'], st.session_state.settings['third_repeat'])
        ]:
            if repeat > 0:  # 재생 횟수가 0보다 큰 경우만 표시
                speed = st.session_state.settings.get(f'{lang}_speed', 1.2)
                speed_text = str(int(speed)) if speed.is_integer() else f"{speed:.1f}"
                
                # 언어별 한글 표시
                lang_display = {
                    'korean': '한글',
                    'english': '영어',
                    'chinese': '중국어',
                    'japanese': '일본어',
                    'vietnamese': '베트남어'
                }.get(lang, lang)
                
                speed_info.append(f"{lang_display} {speed_text}배")
    
    with col2:
        if st.button("⚙️ 설정"):
            st.session_state.page = 'settings_from_learning'
            st.rerun()
        if st.button("⏹️ 종료"):
            st.session_state.page = 'settings'
            st.rerun()

    # 자막을 위한 빈 컨테이너
    subtitles = [st.empty() for _ in range(3)]

    return progress, status, subtitles, speed_info

async def create_break_audio():
    """브레이크 음성 생성"""
    break_msg = "쉬어가는 시간입니다, 5초간의 호흡을 느껴보세요"
    break_voice = VOICE_MAPPING['korean']['선희']
    audio_file = await create_audio(break_msg, break_voice, 1.0)
    return audio_file

async def start_learning():
    """학습 시작"""
    settings = st.session_state.settings
    sentence_count = 0
    repeat_count = 0
    
    # 엑셀에서 문장 가져오기
    try:
        # 엑셀 파일 읽기
        df = pd.read_excel(
            EXCEL_PATH,
            header=None,
            engine='openpyxl'
        )
        start_idx = settings['start_row'] - 1
        end_idx = settings['end_row'] - 1
        
        # 필요한 열만 선택 (존재하는 열만)
        english = df.iloc[start_idx:end_idx+1, 0].tolist()  # A열: 영어
        korean = df.iloc[start_idx:end_idx+1, 1].tolist()   # B열: 한국어
        chinese = df.iloc[start_idx:end_idx+1, 2].tolist()  # C열: 중국어
        japanese = df.iloc[start_idx:end_idx+1, 3].tolist() # D열: 일본어
        
        # 베트남어 열이 있는 경우에만 읽기
        vietnamese = []
        if len(df.columns) > 4:  # E열이 존재하는 경우
            vietnamese = df.iloc[start_idx:end_idx+1, 4].tolist()
        else:
            vietnamese = [""] * (end_idx - start_idx + 1)  # 빈 문자열로 채우기
        
        total_sentences = len(english)
        
    except PermissionError:
        st.error("엑셀 파일이 다른 프로그램에서 열려있습니다. 파일을 닫고 다시 시도해주세요.")
        return
    except Exception as e:
        st.error(f"엑셀 파일 읽기 오류: {e}")
        return

    # 학습 UI 생성 및 배속 정보 가져오기
    progress, status, subtitles, speed_info = create_learning_ui()
    
    # 자막을 위한 빈 컨테이너
    subtitles = [st.empty() for _ in range(3)]
    
    # 이전 문장 자막 저장용 변수
    prev_subtitles = {'second': None, 'third': None}

    while True:
        for i, (eng, kor, chn, jpn, vn) in enumerate(zip(english, korean, chinese, japanese, vietnamese)):
            # 언어별 텍스트와 음성 매핑 (재생 횟수 0인 경우 건너뛰기)
            lang_configs = []
            for lang, repeat in [
                (settings['first_lang'], settings['first_repeat']),
                (settings['second_lang'], settings['second_repeat']),
                (settings['third_lang'], settings['third_repeat'])
            ]:
                if repeat > 0:  # 0회면 제외
                    lang_configs.append({
                        'text': lang_mapping[lang]['text'](df.iloc[i]),
                        'voice': lang_mapping[lang]['voice'],
                        'speed': lang_mapping[lang]['speed'](settings),
                        'repeat': repeat
                    })

            # 실제 음성 재생 로직
            for config in lang_configs:
                for _ in range(config['repeat']):
                    # 음성 파일 생성 및 재생
                    audio_file = await create_audio(config['text'], config['voice'], config['speed'])
                    if audio_file:
                        play_audio(audio_file)
                        await asyncio.sleep(settings['word_delay'])

        # 학습 완료 시
        try:
            # 마지막 시간 업데이트
            current_time = time.time()
            time_diff = current_time - st.session_state.last_update_time
            if time_diff >= 60:
                minutes_to_add = int(time_diff / 60)
                st.session_state.today_total_study_time += minutes_to_add
                st.session_state.last_update_time = current_time
                # 학습 시간 저장
                save_study_time()
            
            # final.wav 재생 및 대기
            final_sound_path = SCRIPT_DIR / 'base/final.wav'
            if final_sound_path.exists() and settings.get('final_sound_enabled', True):
                final_duration = settings.get('final_sound_duration', 60)
                
                if final_duration > 0:
                    # 실제 오디오 길이 계산 (soundfile 사용)
                    try:
                        with sf.SoundFile(str(final_sound_path)) as f:
                            audio_duration = f.frames / f.samplerate
                    except Exception as e:
                        st.error(f"오디오 파일 읽기 오류: {e}")
                        audio_duration = final_duration  # 기본값 사용
                    
                    # 설정 시간과 실제 오디오 길이 중 짧은 시간 사용
                    play_duration = min(final_duration, audio_duration)
                    
                    status.info(f"🎵 학습 구간 완료! 종료 음악을 {play_duration:.1f}초 동안 재생합니다...")
                    
                    # 오디오 재생 시작
                    play_audio(str(final_sound_path))
                    
                    # 정확한 대기 시간 계산
                    start_time = time.time()
                    while time.time() - start_time < play_duration:
                        if st.session_state.page != 'learning':  # 중간에 종료 체크
                            break
                        await asyncio.sleep(0.1)  # 100ms 단위로 체크

            if settings['auto_repeat']:
                repeat_count += 1
                if repeat_count < settings['repeat_count']:
                    sentence_count = 0
                    status.info(f"반복 중... ({repeat_count + 1}/{settings['repeat_count']})")
                    continue
                else:
                    st.success(f"학습이 완료되었습니다! (총 {settings['repeat_count']}회 반복)")
                    st.session_state.page = 'settings'
                    st.rerun()
                    break
            else:
                st.success("학습이 완료되었습니다!")
                st.session_state.page = 'settings'
                st.rerun()
                
        except Exception as e:
            st.error(f"완료 알림음 재생 오류: {e}")
            traceback.print_exc()

def create_personalized_ui():
    """개인별 맞춤 UI 생성"""
    st.title("개인별 설정 기억하기")

    # 언어 선택
    selected_language = st.selectbox(
        "사용할 언어를 선택하세요",
        options=['korean', 'english', 'chinese', 'japanese', 'vietnamese'],
        index=['korean', 'english', 'chinese', 'japanese', 'vietnamese'].index(st.session_state.user_language)
    )

    # 선택한 언어를 세션 상태에 저장
    if selected_language != st.session_state.user_language:
        st.session_state.user_language = selected_language
        st.rerun()  # 변경된 언어를 반영하기 위해 페이지 새로고침

    # 선택한 언어에 따라 메시지 표시
    if st.session_state.user_language == 'korean':
        st.write("안녕하세요! 한국어로 표시됩니다.")
    elif st.session_state.user_language == 'english':
        st.write("Hello! This is displayed in English.")
    elif st.session_state.user_language == 'chinese':
        st.write("你好！这是用中文显示的。")
    elif st.session_state.user_language == 'japanese':
        st.write("こんにちは！これは日本語で表示されます。")
    elif st.session_state.user_language == 'vietnamese':
        st.write("Xin chào! Đây là dòng chữ tiếng Việt.")

def main():
    initialize_session_state()
    
    # 페이지 라우팅
    if st.session_state.page == 'settings':
        create_settings_ui()
    elif st.session_state.page == 'settings_from_learning':
        create_settings_ui(return_to_learning=True)  # 학습 중 설정 모드
    elif st.session_state.page == 'learning':
        asyncio.run(start_learning())
    elif st.session_state.page == 'personalized':
        create_personalized_ui()

def save_settings(settings):
    """설정값을 파일에 저장"""
    try:
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"설정 저장 중 오류: {e}")

def save_study_time():
    """학습 시간을 파일에 저장"""
    study_time_path = SCRIPT_DIR / 'study_time.json'
    try:
        with open(study_time_path, 'w') as f:
            json.dump({
                'date': st.session_state.today_date,
                'time': st.session_state.today_total_study_time
            }, f)
    except Exception as e:
        st.error(f"학습 시간 저장 중 오류: {e}")

def get_setting(key, default_value):
    """안전하게 설정값을 가져오는 유틸리티 함수"""
    return st.session_state.settings.get(key, default_value)

def play_audio(file_path):
    """음성 파일 재생 - 고유 ID 추가 및 자동 재생 보장"""
    try:
        if not file_path or not os.path.exists(file_path):
            st.error(f"파일 경로 오류: {file_path}")
            return

        # 고유한 ID 생성 (타임스탬프 기반)
        audio_id = f"audio_{int(time.time() * 1000)}"
        
        # 파일을 바이트로 읽기
        with open(file_path, 'rb') as f:
            audio_bytes = f.read()
        audio_base64 = base64.b64encode(audio_bytes).decode()

        # HTML 오디오 요소 생성 (사용자 상호작용 후 재생)
        st.markdown(f"""
            <audio id="{audio_id}" controls hidden>
                <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
            </audio>
            <script>
                (function() {{
                    const audio = document.getElementById("{audio_id}");
                    // 사용자 상호작용 후 재생 시도
                    const playPromise = audio.play();
                    if (playPromise !== undefined) {{
                        playPromise.catch(error => {{
                            console.log('자동 재생 차단됨:', error);
                            // 수동 재생 트리거 추가
                            const playButton = document.createElement('button');
                            playButton.innerText = '재생 허용 필요';
                            playButton.style.position = 'fixed';
                            playButton.style.bottom = '20px';
                            playButton.style.right = '20px';
                            playButton.style.zIndex = 9999;
                            playButton.onclick = () => audio.play();
                            document.body.appendChild(playButton);
                        }});
                    }}
                }})();
            </script>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"음성 재생 오류: {str(e)}")

def save_learning_state(df, current_index, session_state):
    """
    학습 상태 저장 함수 개선
    """
    try:
        # 현재 학습 상태 저장
        state_data = {
            'current_index': current_index,
            'timestamp': time.time(),
            'total_rows': len(df),
            'progress': f"{current_index}/{len(df)}",
            'last_sentence': df.iloc[current_index]['english'] if current_index < len(df) else ""
        }
        
        # 파일 저장
        save_path = TEMP_DIR / 'learning_state.json'
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, ensure_ascii=False, indent=2)
            
        st.success(f"학습 상태가 저장되었습니다. (진행률: {state_data['progress']})")
        
        # 세션 상태 업데이트
        session_state.saved_index = current_index
        session_state.has_saved_state = True
        
        return True
        
    except Exception as e:
        st.error(f"저장 중 오류 발생: {str(e)}")
        return False

def load_learning_state():
    """
    학습 상태 불러오기 함수 개선
    """
    try:
        save_path = TEMP_DIR / 'learning_state.json'
        
        if not save_path.exists():
            return None
            
        with open(save_path, 'r', encoding='utf-8') as f:
            state_data = json.load(f)
            
        # 저장된 데이터 검증
        required_keys = ['current_index', 'timestamp', 'total_rows']
        if not all(key in state_data for key in required_keys):
            st.warning("저장된 상태 데이터가 유효하지 않습니다.")
            return None
            
        return state_data
        
    except Exception as e:
        st.error(f"상태 불러오기 중 오류 발생: {str(e)}")
        return None

def handle_resume_learning(df):
    """
    학습 재개 처리 함수
    """
    try:
        state_data = load_learning_state()
        if state_data is None:
            return 0
            
        # 저장된 상태와 현재 데이터 검증
        if state_data['total_rows'] != len(df):
            st.warning("저장된 데이터의 크기가 현재 데이터와 다릅니다.")
            return 0
            
        current_index = state_data['current_index']
        if 0 <= current_index < len(df):
            st.success(f"이전 학습 상태를 불러왔습니다. (진행률: {current_index}/{len(df)})")
            return current_index
        else:
            st.warning("유효하지 않은 인덱스입니다.")
            return 0
            
    except Exception as e:
        st.error(f"학습 재개 중 오류 발생: {str(e)}")
        return 0

if __name__ == "__main__":
    main()
