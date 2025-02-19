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
import librosa
import psutil
import gc
import hashlib

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
    'vietnamese': '베트남어',
    'filipino': '필리핀어',
    'thai': '태국어',
    'russian': '러시아어',
    'uzbek': '우즈베크어',
    'mongolian': '몽골어',
    'nepali': '네팔어',
    'burmese': '미얀마어',
    'indonesian': '인도네시아어',
    'khmer': '캄보디아어'
}

# 음성 매핑에 새로운 언어 추가
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
        "HoaiMy": "vi-VN-HoaiMyNeural",
        "NamMinh": "vi-VN-NamMinhNeural"
    },
    'filipino': {
        "James": "fil-PH-JamesNeural",
        "Rosa": "fil-PH-RosaNeural"
    },
    'thai': {  # 태국어
        "Niwat": "th-TH-NiwatNeural",
        "Premwadee": "th-TH-PremwadeeNeural"
    },
    'russian': {  # 러시아어
        "Dmitry": "ru-RU-DmitryNeural",
        "Svetlana": "ru-RU-SvetlanaNeural"
    },
    'uzbek': {  # 우즈베크어
        "Sardor": "uz-UZ-SardorNeural",
        "Madina": "uz-UZ-MadinaNeural"
    },
    'mongolian': {  # 몽골어
        "Bataa": "mn-MN-BataaNeural",
        "Yesui": "mn-MN-YesuiNeural"
    },
    'nepali': {  # 네팔어
        "Hemkala": "ne-NP-HemkalaNeural",
        "Sagar": "ne-NP-SagarNeural"
    },
    'burmese': {  # 미얀마어
        "Thura": "my-MM-ThuraNeural",
        "Nilar": "my-MM-NilarNeural"
    },
    'indonesian': {  # 인도네시아어
        "Ardi": "id-ID-ArdiNeural",
        "Gadis": "id-ID-GadisNeural"
    },
    'khmer': {  # 캄보디아어
        "Piseth": "km-KH-PisethNeural",
        "Sreymom": "km-KH-SreymomNeural"
    }
}

# 언어 설정 업데이트
LANGUAGES = ['english', 'korean', 'chinese', 'japanese', 'vietnamese', 'filipino', 
            'thai', 'russian', 'uzbek', 'mongolian', 'nepali', 'burmese', 
            'indonesian', 'khmer', 'none']

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

LANGUAGE_MAPPING = {
    'en': {'code': 'en-US', 'name': '미국'},
    'ko': {'code': 'ko-KR', 'name': '한국'},
    'zh': {'code': 'zh-CN', 'name': '중국'},
    'vi': {'code': 'vi-VN', 'name': '베트남'},
    'ja': {'code': 'ja-JP', 'name': '일본'},
    'th': {'code': 'th-TH', 'name': '태국'},
    'tl': {'code': 'tl-PH', 'name': '필리핀'},
    'ru': {'code': 'ru-RU', 'name': '러시아'},
    'uz': {'code': 'uz-UZ', 'name': '우즈벡'},
    'mn': {'code': 'mn-MN', 'name': '몽골'},
    'ne': {'code': 'ne-NP', 'name': '네팔'},
    'my': {'code': 'my-MM', 'name': '미얀마'},
    'id': {'code': 'id-ID', 'name': '인니'},
    'km': {'code': 'km-KH', 'name': '캄보디아'}
}

def format_column_header(lang_code):
    """
    언어 코드를 기반으로 '[코드]-[국가명]' 형식의 컬럼 헤더를 반환합니다.
    """
    if lang_code in LANGUAGE_MAPPING:
        return f"{lang_code}-{LANGUAGE_MAPPING[lang_code]['name']}"
    return lang_code

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
        'third_lang': 'none',  # 기본값을 'none'으로 변경
        'first_repeat': 0,
        'second_repeat': 1,
        'third_repeat': 0,  # 기본값 0으로 변경
        'eng_voice': 'Steffan',
        'kor_voice': '선희',
        'zh_voice': 'Yunjian',
        'jp_voice': 'Nanami',
        'vi_voice': 'HoaiMy',
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
        'english_color': '#FFFFF0',  # 아이보리 색상으로 변경
        'korean_color': '#00FF00',   # 다크모드: 초록색, 브라이트모드: 검정색
        'chinese_color': '#00FF00',  # 다크모드: 초록색, 브라이트모드: 검정색
        'japanese_color': '#00FF00' if st.get_option("theme.base") == "dark" else '#FFFFFF',  # 다크모드: 초록색, 라이트모드: 흰색
        'vietnamese_color': '#00FF00' if st.get_option("theme.base") == "dark" else '#FFFFFF',  # 다크모드: 초록색, 라이트모드: 흰색
        'japanese_speed': 2.0,  # 일본어 배속 기본값 추가
        'vietnamese_font': 'Arial',  # 베트남어 폰트 기본값 추가
        'vietnamese_font_size': 30,
        'vietnamese_speed': 1.0,
        'first_font_size': 32,
        'second_font_size': 32,
        'third_font_size': 32,
        'first_color': '#00FF00',   # 초록색
        'second_color': '#FFFFF0',  # 아이보리
        'third_color': '#00FF00',   # 초록색
        'fil_voice': 'James',  # 필리핀어 기본 음성
        'filipino_speed': 1.2,  # 필리핀어 기본 속도
        'filipino_font': 'Arial',  # 필리핀어 기본 폰트
        'filipino_font_size': 32,  # 필리핀어 기본 폰트 크기
        'thai_voice': 'Niwat',
        'russian_voice': 'Dmitry',
        'uzbek_voice': 'Sardor',
        'mongolian_voice': 'Bataa',
        'nepali_voice': 'Hemkala',
        'burmese_voice': 'Thura',
        'indonesian_voice': 'Ardi',
        'khmer_voice': 'Piseth',
        'thai_speed': 1.2,
        'russian_speed': 1.2,
        'uzbek_speed': 1.2,
        'mongolian_speed': 1.2,
        'nepali_speed': 1.2,
        'burmese_speed': 1.2,
        'indonesian_speed': 1.2,
        'khmer_speed': 1.2,
        'thai_font': 'Arial',
        'russian_font': 'Arial',
        'uzbek_font': 'Arial',
        'mongolian_font': 'Arial',
        'nepali_font': 'Arial',
        'burmese_font': 'Arial',
        'indonesian_font': 'Arial',
        'khmer_font': 'Arial',
        'thai_font_size': 32,
        'russian_font_size': 32,
        'uzbek_font_size': 32,
        'mongolian_font_size': 32,
        'nepali_font_size': 32,
        'burmese_font_size': 32,
        'indonesian_font_size': 32,
        'khmer_font_size': 32
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
        final_sound_options = ['없음', '30초', '1분', '1분30초']
        final_sound_mapping = {'없음': 0, '30초': 30, '1분': 60, '1분30초': 90}
        current_duration = '1분'  # 기본값
        for option, duration in final_sound_mapping.items():
            if duration == settings.get('final_sound_duration', 60):
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

        # 학습 시작 버튼 추가
        if st.button("▶️ 학습 시작", use_container_width=True, key="start_btn_learning"):
            save_settings(settings)
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
        
        # CSS 스타일 수정 - 서브헤더 색상을 초록색으로 변경
        st.markdown("""
            <style>
                /* 서브헤더 스타일 수정 */
                .stMarkdown h2,
                .streamlit-expanderHeader,
                [data-testid="stSidebarNav"] h2,
                div[data-testid="stMarkdownContainer"] h2,
                .st-emotion-cache-1629p8f h2 {
                    font-size: 1.2rem !important;
                    color: #00FF00 !important;  /* 초록색으로 변경 */
                    border-bottom: 2px solid #00FF00 !important;  /* 초록색 밑줄 추가 */
                    padding-bottom: 0.3rem !important;
                    margin-top: 1rem !important;
                    margin-bottom: 0.5rem !important;
                    display: inline-block !important;
                }

                /* 구분자 스타일 유지 */
                .separator {
                    color: #00FF00 !important;
                    font-size: 1.2rem !important;
                    padding: 0 0.5rem !important;
                    display: inline !important;
                    vertical-align: middle !important;
                    line-height: 1 !important;
                }

                /* 구분자 컨테이너 스타일 유지 */
                [data-testid="stMarkdownContainer"] {
                    display: inline !important;
                    white-space: nowrap !important;
                }
            </style>
        """, unsafe_allow_html=True)
        
        settings = st.session_state.settings
        col1, col2 = st.columns([0.7, 0.3])
        with col1:
            st.markdown('<h1 style="font-size: 1.5rem; color: #FF0000;">도파민 대충영어 : 2배 한국어</h1>', unsafe_allow_html=True)
        with col2:
            # 엑셀 파일에서 시트 선택 및 최대 행 수 가져오기
            try:
                # 엑셀 파일 전체 읽기
                excel_file = pd.ExcelFile(EXCEL_PATH)
                sheet_names = excel_file.sheet_names[:3]  # 처음 3개의 시트만 사용
                
                # 시트 선택 (기본값: 첫 번째 시트)
                selected_sheet = st.selectbox(
                    "주제 : 생활영어, 여행영어, 천일문",
                    options=sheet_names,
                    index=0,
                    key="sheet_select"
                )
                
                # 선택된 시트 데이터 읽기 - header=0으로 변경하여 첫 행을 헤더로 사용
                df = pd.read_excel(
                    EXCEL_PATH,
                    sheet_name=selected_sheet,
                    header=0,  # 첫 행을 헤더로 사용
                    engine='openpyxl'
                )
                max_row = len(df)
                
                # 선택된 시트 정보를 설정에 저장
                settings['selected_sheet'] = selected_sheet
                
            except Exception as e:
                st.error(f"엑셀 파일 읽기 오류: {e}")
                return
            
            # 학습 시작 버튼 추가 (이전 위치)
            if st.button("▶️ 학습 시작", use_container_width=True, key="start_btn_top"):
                save_settings(settings)
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
                    background-color: #00FF00 !important;
                    color: black !important;
                }
            </style>
        """, unsafe_allow_html=True)

        # 문장 범위 선택 UI 개선
        st.subheader("학습문장 선택")
        col1, col2 = st.columns(2)
        
        with col1:
            # 과 선택 (1~30과)
            lesson_options = [f"{i}과({(i-1)*20+1}~{i*20}번)" for i in range(1, 31)]
            current_lesson = (settings['start_row'] - 1) // 20 + 1  # 현재 과 계산
            selected_lesson = st.selectbox(
                "과 선택(20문장 30과)",
                options=lesson_options,
                index=current_lesson-1,
                key="lesson_select"
            )
            
            # 선택된 과에서 시작 번호 계산
            lesson_num = int(selected_lesson.split('과')[0])
            settings['start_row'] = (lesson_num - 1) * 20 + 1
            settings['end_row'] = lesson_num * 20
        
        with col2:
            # 범위 선택 (20개 또는 50개 단위)
            range_options = {
                "20문장(1과)": 20,
                "40문장(2과)": 40,
                "50문장": 50,
                "60문장(3과)": 60,
                "100문장": 100,
                "직접 입력": 0
            }
            selected_range = st.selectbox(
                "문장 개수(한번에 학습할 문장)",
                options=list(range_options.keys()),
                key="range_select"
            )
            
            if selected_range == "직접 입력":
                settings['end_row'] = st.number_input(
                    "종료 번호",
                    value=min(settings['start_row'] + 19, max_row),
                    min_value=settings['start_row'],
                    max_value=max_row,
                    key="end_row_input"
                )
            else:
                range_value = range_options[selected_range]
                settings['end_row'] = min(settings['start_row'] + range_value - 1, max_row)

        # 선택된 범위 표시
        st.info(f"선택된 범위: {settings['start_row']} ~ {settings['end_row']} (총 {settings['end_row'] - settings['start_row'] + 1}문장)")

        # 언어 순위 설정
        st.subheader("자막 | 음성 | 속도")
        col1, col2, col3 = st.columns(3)
        
        # 모든 지원 언어 리스트
        supported_languages = [
            'korean', 'english', 'chinese', 'japanese', 'vietnamese', 'filipino',
            'thai', 'russian', 'uzbek', 'mongolian', 'nepali', 'burmese', 
            'indonesian', 'khmer'
        ]
        
        with col1:
            settings['first_lang'] = st.selectbox("1번째 언어",
                options=supported_languages,
                index=supported_languages.index(settings['first_lang']),
                format_func=lambda x: LANG_DISPLAY[x],
                key="settings_first_lang")
            # 음성 재생 횟수를 선택박스로 변경
            current_repeat = max(1, min(settings.get('first_repeat', 1), 5))  # 1-5 사이로 제한
            settings['first_repeat'] = st.selectbox("음성 재생(횟수)",
                                      options=list(range(0, 3)),  # 0-2회
                                      index=current_repeat-1,  # 0-based index
                                      key="first_repeat")
            # 배속을 선택박스로 변경
            speed_options = [round(x * 0.2, 1) for x in range(4, 31)]  # 0.8-6.0배, 0.2간격
            speed_key = f"{settings['first_lang']}_speed"
            current_speed = round(float(settings.get(speed_key, 1.2)), 1)
            current_speed = max(0.8, min(current_speed, 6.0 if settings['first_lang'] == 'korean' else 4.0))
            try:
                speed_index = speed_options.index(current_speed)
            except ValueError:
                speed_index = speed_options.index(1.2)
            settings[speed_key] = st.selectbox("음성 속도(배)",
                                     options=speed_options,
                                     index=speed_index,
                                     key="first_speed")

        with col2:
            settings['second_lang'] = st.selectbox("2번째 언어",
                options=supported_languages,
                index=supported_languages.index(settings['second_lang']),
                format_func=lambda x: LANG_DISPLAY[x],
                key="settings_second_lang")
            # 음성 재생 횟수를 선택박스로 변경
            current_repeat = max(1, min(settings.get('second_repeat', 1), 5))  # 1-5 사이로 제한
            settings['second_repeat'] = st.selectbox("음성 재생(횟수)",
                                       options=list(range(1, 3)),  # 1-2회
                                       index=current_repeat-1,  # 0-based index
                                       key="second_repeat")
            # 배속을 선택박스로 변경
            speed_key = f"{settings['second_lang']}_speed"
            current_speed = round(float(settings.get(speed_key, 1.2)), 1)
            current_speed = max(0.8, min(current_speed, 6.0 if settings['second_lang'] == 'korean' else 4.0))
            try:
                speed_index = speed_options.index(current_speed)
            except ValueError:
                speed_index = speed_options.index(1.2)
            settings[speed_key] = st.selectbox("음성 속도(배)",
                                      options=speed_options,
                                      index=speed_index,
                                      key="second_speed")

        with col3:
            # 3순위 언어에는 'none' 옵션 추가
            third_options = ['none'] + supported_languages
            settings['third_lang'] = st.selectbox("3번째 언어",
                options=third_options,
                index=third_options.index(settings['third_lang']),
                format_func=lambda x: '없음' if x == 'none' else LANG_DISPLAY.get(x, x),
                key="settings_third_lang")
            
            # 'none'이 아닐 때만 음성 재생 횟수와 속도 설정 표시
            if settings['third_lang'] != 'none':
                # 음성 재생 횟수를 선택박스로 변경
                current_repeat = max(1, min(settings.get('third_repeat', 1), 5))  # 1-5 사이로 제한
                settings['third_repeat'] = st.selectbox("음성 재생(횟수)",
                                          options=list(range(1, 3)),  # 1-2회
                                          index=current_repeat-1,  # 0-based index
                                          key="third_repeat")
                # 배속을 선택박스로 변경
                speed_key = f"{settings['third_lang']}_speed"
                current_speed = round(float(settings.get(speed_key, 1.2)), 1)
                current_speed = max(0.8, min(current_speed, 6.0 if settings['third_lang'] == 'korean' else 4.0))
                try:
                    speed_index = speed_options.index(current_speed)
                except ValueError:
                    speed_index = speed_options.index(1.2)
                settings[speed_key] = st.selectbox("음성 속도(배)",
                                         options=speed_options,
                                         index=speed_index,
                                         key="third_speed")
            else:
                # 'none'일 때는 재생 횟수를 0으로 설정
                settings['third_repeat'] = 0

        # 학습 시작 버튼 추가 (자막|음성|속도 섹션 아래)
        if st.button("▶️ 학습 시작", use_container_width=True, key="start_btn_middle"):
            save_settings(settings)
            st.session_state.page = 'learning'
            st.rerun()

        # 문장 재생 설정
        st.subheader("문장 재생")
        col1, col2, col3, col4 = st.columns(4)
        
        # 0.1초부터 2초까지 0.1초 간격의 옵션 생성
        time_options = [round(x * 0.1, 1) for x in range(1, 21)]  # 0.1-2.0초
        
        with col1:
            current_spacing = round(float(settings.get('spacing', 1.0)), 1)
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
            current_delay = round(float(settings.get('subtitle_delay', 1.0)), 1)
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
            current_next = round(float(settings.get('next_sentence_time', 1.0)), 1)
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

        # 자막 숨김 옵션을 한 줄로 배치
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            settings['keep_subtitles'] = st.checkbox("자막유지 모드",
                                                  value=settings.get('keep_subtitles', True),
                                                  key="keep_subtitles_checkbox")
        with col2:
            hide_first = st.checkbox("1순위 자막 숨김",
                                   value=settings['hide_subtitles']['first_lang'],
                                   key="first_hide")
        with col3:
            hide_second = st.checkbox("2순위 자막 숨김",
                                    value=settings['hide_subtitles']['second_lang'],
                                    key="second_hide")
        with col4:
            hide_third = st.checkbox("3순위 자막 숨김",
                                   value=settings['hide_subtitles']['third_lang'],
                                   key="third_hide")

        # 폰트 크기 및 색상 설정
        st.subheader("폰트 크기 | 색깔")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**1순위 언어**")
            settings['first_font_size'] = st.number_input("폰트 크기",
                                                      value=settings.get('first_font_size', 32),
                                                      min_value=10,
                                                      max_value=50,
                                                      step=1,
                                                      key="first_font_size")
            default_color = 'green'  # 1순위 기본값: 초록색
            selected_color = st.selectbox("글자 색상",
                                        options=list(COLOR_MAPPING.keys()),
                                        index=list(COLOR_MAPPING.keys()).index(default_color),
                                        key="first_color_select")
            settings['first_color'] = COLOR_MAPPING[selected_color]

        with col2:
            st.markdown("**2순위 언어**")
            settings['second_font_size'] = st.number_input("폰트 크기",
                                                       value=settings.get('second_font_size', 32),
                                                       min_value=10,
                                                       max_value=50,
                                                       step=1,
                                                       key="second_font_size")
            default_color = 'ivory'  # 2순위 기본값: 아이보리
            selected_color = st.selectbox("글자 색상",
                                        options=list(COLOR_MAPPING.keys()),
                                        index=list(COLOR_MAPPING.keys()).index(default_color),
                                        key="second_color_select")
            settings['second_color'] = COLOR_MAPPING[selected_color]

        with col3:
            st.markdown("**3순위 언어**")
            settings['third_font_size'] = st.number_input("폰트 크기",
                                                      value=settings.get('third_font_size', 32),
                                                      min_value=10,
                                                      max_value=50,
                                                      step=1,
                                                      key="third_font_size")
            default_color = 'green'  # 3순위 기본값: 초록색
            selected_color = st.selectbox("글자 색상",
                                        options=list(COLOR_MAPPING.keys()),
                                        index=list(COLOR_MAPPING.keys()).index(default_color),
                                        key="third_color_select")
            settings['third_color'] = COLOR_MAPPING[selected_color]

        # 학습 시작 버튼 추가 (폰트 설정 아래)
        if st.button("▶️ 학습 시작", use_container_width=True, key="start_btn_bottom"):
            save_settings(settings)
            st.session_state.page = 'learning'
            st.rerun()

def get_voice_mapping(language, voice_setting):
    """안전하게 음성 매핑을 가져오는 함수"""
    try:
        # 기본값 설정
        default_voices = {
            'korean': '선희',
            'english': 'Steffan',
            'chinese': 'Yunjian',
            'japanese': 'Nanami',
            'vietnamese': 'HoaiMy',
            'filipino': 'James',
            'thai': 'Niwat',
            'russian': 'Dmitry',
            'uzbek': 'Sardor',
            'mongolian': 'Bataa',
            'nepali': 'Hemkala',
            'burmese': 'Thura',
            'indonesian': 'Ardi',
            'khmer': 'Piseth'
        }
        
        # 설정된 음성이 없거나 매핑에 없는 경우 기본값 사용
        if not voice_setting or voice_setting not in VOICE_MAPPING.get(language, {}):
            voice_setting = default_voices.get(language)
            
        return VOICE_MAPPING[language][voice_setting]
    except Exception as e:
        st.error(f"음성 매핑 오류 ({language}): {str(e)}")
        # 기본값 반환
        return VOICE_MAPPING[language][default_voices[language]]

async def get_voice_file(text, voice, speed=1.0, output_file=None):
    try:
        # 빈 텍스트 체크
        if not text or text.isspace():
            return None
            
        # 파일명 해시 생성
        text_hash = hashlib.md5(text.encode()).hexdigest()
        
        if output_file is None:
            output_file = TEMP_DIR / f"temp_{voice}_{speed}_{text_hash[:8]}.wav"
            
        # 이미 존재하는 파일이면 재사용
        if output_file.exists():
            return str(output_file)
            
        # 한국어 고속 재생을 위한 처리
        if voice.startswith("ko-") and speed > 3.0:
            # 3배속 이상일 때 특수 처리
            actual_speed = 2.0  # TTS 속도를 2배속으로 고정
            communicate = edge_tts.Communicate(text, voice, rate=f"+{int((actual_speed-1)*100)}%")
        else:
            # 일반적인 경우
            communicate = edge_tts.Communicate(text, voice, rate=f"+{int((speed-1)*100)}%")

        await communicate.save(str(output_file))

        # 한국어 고속 재생을 위한 후처리
        if voice.startswith("ko-") and speed > 3.0:
            # 오디오 파일 처리로 추가 배속
            y, sr = sf.read(str(output_file))
            speed_factor = speed / actual_speed  # 실제 배속 비율 계산
            
            # librosa로 배속 처리
            y_fast = librosa.effects.time_stretch(y, rate=speed_factor)
            
            # 볼륨 정규화 및 증폭
            y_norm = librosa.util.normalize(y_fast) * 1.5  # 볼륨을 1.5배로 증폭
            
            # 클리핑 방지
            y_norm = np.clip(y_norm, -1.0, 1.0)
            
            sf.write(str(output_file), y_norm, sr)

        return str(output_file)
    except Exception as e:
        st.warning(f"음성 생성 실패: {str(e)}")
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
    audio_file = await get_voice_file(break_msg, break_voice, 1.0)
    return audio_file

async def start_learning():
    """학습 시작"""
    try:
        # 시작 시 임시 파일 정리
        cleanup_temp_files()
        
        # 메모리 사용량 모니터링
        process = psutil.Process()
        if process.memory_info().rss > 400 * 1024 * 1024:  # 400MB 초과
            cleanup_temp_files()  # 임시 파일 정리
            if process.memory_info().rss > 500 * 1024 * 1024:  # 여전히 500MB 초과
                st.error("메모리 사용량이 너무 높습니다. 더 적은 문장을 선택해주세요.")
                return

        settings = st.session_state.settings
        sentence_count = 0
        repeat_count = 0
        
        # 선택된 시트의 데이터 읽기 - header=0으로 변경
        df = pd.read_excel(
            EXCEL_PATH,
            sheet_name=settings.get('selected_sheet', 0),
            header=0,  # 첫 행을 헤더로 사용
            engine='openpyxl'
        )
        start_idx = settings['start_row'] - 1
        end_idx = settings['end_row'] - 1
        
        # 모든 언어 열 읽기 (없는 열은 빈 문자열로 채우기)
        data = {
            'english': get_column_data(df, 'en-미국', start_idx, end_idx),
            'korean': get_column_data(df, 'ko-한국', start_idx, end_idx),
            'chinese': get_column_data(df, 'zh-중국', start_idx, end_idx),
            'japanese': get_column_data(df, 'ja-일본', start_idx, end_idx),
            'vietnamese': get_column_data(df, 'vi-베트남', start_idx, end_idx),
            'filipino': get_column_data(df, 'tl-필리핀', start_idx, end_idx),
            'thai': get_column_data(df, 'th-태국', start_idx, end_idx),
            'russian': get_column_data(df, 'ru-러시아', start_idx, end_idx),
            'uzbek': get_column_data(df, 'uz-우즈벡', start_idx, end_idx),
            'mongolian': get_column_data(df, 'mn-몽골', start_idx, end_idx),
            'nepali': get_column_data(df, 'ne-네팔', start_idx, end_idx),
            'burmese': get_column_data(df, 'my-미얀마', start_idx, end_idx),
            'indonesian': get_column_data(df, 'id-인니', start_idx, end_idx),
            'khmer': get_column_data(df, 'km-캄보디아', start_idx, end_idx)
        }

        total_sentences = len(data['english'])

        # 데이터 언패킹
        english, korean, chinese, japanese, vietnamese, filipino, thai, russian, \
        uzbek, mongolian, nepali, burmese, indonesian, khmer = [data[lang] for lang in [
            'english', 'korean', 'chinese', 'japanese', 'vietnamese', 'filipino',
            'thai', 'russian', 'uzbek', 'mongolian', 'nepali', 'burmese',
            'indonesian', 'khmer'
        ]]

        # 학습 UI 생성 및 배속 정보 가져오기
        progress, status, subtitles, speed_info = create_learning_ui()
        
        # 자막을 위한 빈 컨테이너
        subtitles = [st.empty() for _ in range(3)]
        
        # 이전 문장 자막 저장용 변수
        prev_subtitles = {'second': None, 'third': None}

        while True:
            for i, (eng, kor, chn, jpn, vn, fil, thai, rus, uzb, mng, nep, bur, ind, khm) in enumerate(zip(
                english, korean, chinese, japanese, vietnamese, filipino, thai, russian, 
                uzbek, mongolian, nepali, burmese, indonesian, khmer)):
                
                # 언어별 텍스트와 음성 매핑
                lang_mapping = {
                    'korean': {'text': kor, 'voice': get_voice_mapping('korean', settings.get('kor_voice')), 'speed': settings.get('korean_speed', 1.2)},
                    'english': {'text': eng, 'voice': get_voice_mapping('english', settings.get('eng_voice')), 'speed': settings.get('english_speed', 1.2)},
                    'chinese': {'text': chn, 'voice': get_voice_mapping('chinese', settings.get('zh_voice')), 'speed': settings.get('chinese_speed', 1.2)},
                    'japanese': {'text': jpn, 'voice': get_voice_mapping('japanese', settings.get('jp_voice')), 'speed': settings.get('japanese_speed', 1.2)},
                    'vietnamese': {'text': vn, 'voice': get_voice_mapping('vietnamese', settings.get('vi_voice')), 'speed': settings.get('vietnamese_speed', 1.2)},
                    'filipino': {'text': fil, 'voice': get_voice_mapping('filipino', settings.get('fil_voice')), 'speed': settings.get('filipino_speed', 1.2)},
                    'thai': {'text': thai, 'voice': get_voice_mapping('thai', settings.get('thai_voice')), 'speed': settings.get('thai_speed', 1.2)},
                    'russian': {'text': rus, 'voice': get_voice_mapping('russian', settings.get('russian_voice')), 'speed': settings.get('russian_speed', 1.2)},
                    'uzbek': {'text': uzb, 'voice': get_voice_mapping('uzbek', settings.get('uzbek_voice')), 'speed': settings.get('uzbek_speed', 1.2)},
                    'mongolian': {'text': mng, 'voice': get_voice_mapping('mongolian', settings.get('mongolian_voice')), 'speed': settings.get('mongolian_speed', 1.2)},
                    'nepali': {'text': nep, 'voice': get_voice_mapping('nepali', settings.get('nepali_voice')), 'speed': settings.get('nepali_speed', 1.2)},
                    'burmese': {'text': bur, 'voice': get_voice_mapping('burmese', settings.get('burmese_voice')), 'speed': settings.get('burmese_speed', 1.2)},
                    'indonesian': {'text': ind, 'voice': get_voice_mapping('indonesian', settings.get('indonesian_voice')), 'speed': settings.get('indonesian_speed', 1.2)},
                    'khmer': {'text': khm, 'voice': get_voice_mapping('khmer', settings.get('khmer_voice')), 'speed': settings.get('khmer_speed', 1.2)}
                }

                progress.progress((i + 1) / total_sentences)
                
                # 진행 상태와 배속 정보 표시
                speed_info = []
                
                # 순위에 따라 실제 재생되는 음성의 배속만 표시
                for lang, repeat in [
                    (settings['first_lang'], settings['first_repeat']),
                    (settings['second_lang'], settings['second_repeat']),
                    (settings['third_lang'], settings['third_repeat'])
                ]:
                    if repeat > 0:  # 재생 횟수가 0보다 큰 경우만 표시
                        speed = settings.get(f'{lang}_speed', 1.2)
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
                
                # 배속 정보를 하나의 문자열로 결합
                speed_display = " | ".join(speed_info)
                
                # 문장 번호 계산 (엑셀 행 번호 사용)
                sentence_number = start_idx + i + 1
                sentence_number_display = f"No.{sentence_number:03d}"
                
                # 현재 시간과 마지막 업데이트 시간의 차이를 계산
                current_time = time.time()
                time_diff = current_time - st.session_state.last_update_time
                
                # 1분(60초)마다 누적 시간 업데이트
                if time_diff >= 60:
                    minutes_to_add = int(time_diff / 60)
                    st.session_state.today_total_study_time += minutes_to_add
                    st.session_state.last_update_time = current_time
                    # 학습 시간 저장
                    save_study_time()
                
                # 상태 표시
                status.markdown(
                    f'<span style="color: red">{sentence_number_display}</span> '
                    f'<span class="separator">•</span> '
                    f'<span style="color: #00FF00">{i+1}/{total_sentences}</span> '
                    f'<span class="separator">•</span> '
                    f'<span style="color: #00FF00">{speed_display}</span> '
                    f'<span class="separator">•</span> '
                    f'<span style="color: red">학습: {int((current_time - st.session_state.start_time) / 60):02d}분</span> '
                    f'<span class="separator">•</span> '
                    f'<span style="color: #00FF00">오늘: {st.session_state.today_total_study_time:02d}분</span>',
                    unsafe_allow_html=True
                )

                # 실시간 CSS 업데이트
                st.markdown(f"""
                    <style>
                        div[data-testid="stMarkdownContainer"] {{
                            font-size: {settings['korean_font_size']}px !important;
                        }}
                        .korean-text {{
                            color: {settings['korean_color']} !important;
                        }}
                        .english-text {{
                            color: {settings['english_color']} !important;
                        }}
                        .chinese-text {{
                            color: {settings['chinese_color']} !important;
                        }}
                        .japanese-text {{
                            color: {settings['japanese_color']} !important;
                        }}
                        .vietnamese-text {{
                            color: {settings['vietnamese_color']} !important;
                        }}
                    </style>
                """, unsafe_allow_html=True)

                # 순위별 자막 표시
                for rank, (lang, repeat) in enumerate([
                    (settings['first_lang'], settings['first_repeat']),
                    (settings['second_lang'], settings['second_repeat']),
                    (settings['third_lang'], settings['third_repeat'])
                ]):
                    if lang != 'none':
                        # 자막 표시
                        if not settings['hide_subtitles'][f'{["first", "second", "third"][rank]}_lang']:
                            text = lang_mapping[lang]['text']
                            font = settings.get(f'{lang}_font', 'Arial')
                            color = settings.get(f'{["first", "second", "third"][rank]}_color', '#00FF00')
                            size = settings.get(f'{["first", "second", "third"][rank]}_font_size', 32)
                            
                            subtitles[rank].markdown(
                                f'<div class="{["first", "second", "third"][rank]}-text" style="font-family: {font}; '
                                f'color: {color}; font-size: {size}px;">{text}</div>',
                                unsafe_allow_html=True
                            )
                        
                        # 음성 재생 시도
                        for _ in range(repeat):
                            try:
                                audio_file = await get_voice_file(
                                    lang_mapping[lang]['text'],
                                    lang_mapping[lang]['voice'],
                                    lang_mapping[lang]['speed']
                                )
                                if audio_file:
                                    play_audio(audio_file)
                                    if _ < repeat - 1:
                                        await asyncio.sleep(settings['spacing'])
                            except Exception as e:
                                st.warning(f"{LANG_DISPLAY[lang]} 음성 재생 불가: {str(e)}")
                                await asyncio.sleep(1)  # 에러 시 1초 대기
                                continue

                # 다음 문장으로 넘어가기 전 대기
                await asyncio.sleep(settings['next_sentence_time'])

                # 브레이크 체크
                sentence_count += 1
                if settings['break_enabled'] and sentence_count % settings['break_interval'] == 0:
                    try:
                        status.warning(f"🔄 {settings['break_interval']}문장 완료! {settings['break_duration']}초간 휴식...")
                        
                        # 1. 먼저 break.wav 알림음 재생
                        break_sound_path = SCRIPT_DIR / 'base/break.wav'
                        if break_sound_path.exists():
                            play_audio(str(break_sound_path))
                            await asyncio.sleep(1)  # 알림음이 완전히 재생될 때까지 대기
                        
                        # 2. 브레이크 음성 메시지 생성 및 재생
                        break_msg = "쉬어가는 시간입니다, 5초간의 호흡을 느껴보세요"
                        break_audio = await get_voice_file(break_msg, VOICE_MAPPING['korean']['선희'], 1.0)
                        if break_audio:
                            play_audio(break_audio)
                            # 음성 메시지 재생 시간 계산 (대략적으로 메시지 길이에 따라)
                            await asyncio.sleep(3)  # 메시지가 재생될 때까지 대기
                        
                        # 3. 남은 휴식 시간 대기
                        remaining_time = max(0, settings['break_duration'] - 4)  # 알림음과 메시지 재생 시간을 고려
                        if remaining_time > 0:
                            await asyncio.sleep(remaining_time)
                        
                        status.empty()
                        
                    except Exception as e:
                        st.error(f"브레이크 처리 중 오류: {e}")
                        traceback.print_exc()

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
                
                # final.wav 재생
                final_sound_path = SCRIPT_DIR / 'base/final.wav'
                if final_sound_path.exists():
                    play_audio(str(final_sound_path))
                    await asyncio.sleep(1)
                
                if settings['auto_repeat']:
                    repeat_count += 1
                    if repeat_count < settings['repeat_count']:
                        # 반복 횟수가 남았으면 처음부터 다시 시작
                        sentence_count = 0
                        status.info(f"반복 중... ({repeat_count}/{settings['repeat_count']})")
                        continue
                    else:
                        # 반복 횟수를 모두 채우면 학습 종료
                        st.success(f"학습이 완료되었습니다! (총 {settings['repeat_count']}회 반복)")
                        st.session_state.page = 'settings'
                        st.rerun()
                
            except Exception as e:
                st.error(f"완료 알림음 재생 오류: {e}")
                traceback.print_exc()

        # 주기적으로 임시 파일 정리 (10문장마다)
        if sentence_count % 10 == 0:
            cleanup_temp_files()

    except PermissionError:
        st.error("엑셀 파일이 다른 프로그램에서 열려있습니다. 파일을 닫고 다시 시도해주세요.")
        return
    except Exception as e:
        cleanup_temp_files()  # 에러 발생 시에도 정리
        st.error(f"학습 중 오류 발생: {str(e)}")
        traceback.print_exc()

def get_column_data(df, column_name, start_idx, end_idx):
    """메모리 효율적인 데이터 로드"""
    try:
        if column_name in df.columns:
            # 청크 단위로 데이터 로드 (메모리 사용량 감소)
            chunk_size = 100
            result = []
            for chunk_start in range(start_idx, end_idx + 1, chunk_size):
                chunk_end = min(chunk_start + chunk_size, end_idx + 1)
                chunk = df.loc[chunk_start:chunk_end-1, column_name].tolist()
                result.extend(chunk)
            return result
        else:
            return [""] * (end_idx - start_idx + 1)
    except Exception as e:
        st.warning(f"{column_name} 열 읽기 실패: {str(e)}")
        return [""] * (end_idx - start_idx + 1)

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

def play_audio(file_path, sentence_interval=1.0, next_sentence=False):
    """
    음성 파일 재생 - 문장 간격 및 다음 문장 설정 적용
    """
    try:
        if not file_path or not os.path.exists(file_path):
            st.error(f"파일 경로 오류: {file_path}")
            return

        # WAV 파일에서 실제 재생 시간 계산
        try:
            with wave.open(file_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / float(rate)
        except Exception:
            with open(file_path, 'rb') as f:
                audio_bytes = f.read()
            duration = len(audio_bytes) / 32000

        # 파일을 바이트로 읽기
        with open(file_path, 'rb') as f:
            audio_bytes = f.read()
        audio_base64 = base64.b64encode(audio_bytes).decode()

        # 고유한 ID 생성
        audio_id = f"audio_{int(time.time() * 1000)}"
        
        # HTML 오디오 요소 생성
        st.markdown(f"""
            <audio id="{audio_id}" autoplay="true">
                <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
            </audio>
            <script>
                (function() {{
                    const audio = document.getElementById("{audio_id}");
                    
                    // 이전 오디오가 있으면 정지
                    if (window.currentAudio && window.currentAudio !== audio) {{
                        window.currentAudio.pause();
                        window.currentAudio.currentTime = 0;
                        window.currentAudio.remove();
                    }}
                    
                    // 현재 오디오를 전역 변수에 저장
                    window.currentAudio = audio;
                    window.audioEnded = false;
                    
                    // 재생 완료 이벤트
                    audio.onended = function() {{
                        window.audioEnded = true;
                        if (window.currentAudio === audio) {{
                            window.currentAudio = null;
                        }}
                        audio.remove();
                    }};

                    // 재생 시작 이벤트
                    audio.onplay = function() {{
                        window.audioEnded = false;
                    }};
                }})();
            </script>
        """, unsafe_allow_html=True)

        # 대기 시간 계산
        if next_sentence:
            # 다음 문장으로 빠르게 넘어가기
            wait_time = duration + 0.3  # 최소 대기 시간
        else:
            # 문장 간격 적용
            base_wait = duration
            
            # 긴 문장에 대한 추가 대기 시간
            if duration > 5:
                extra_wait = duration * 0.1  # 10% 추가
            else:
                extra_wait = 0.5
                
            # 사용자가 설정한 문장 간격 적용
            wait_time = base_wait + extra_wait + sentence_interval

        # 최소 대기 시간 보장
        wait_time = max(wait_time, duration + 0.3)
        
        time.sleep(wait_time)

    except Exception as e:
        st.error(f"음성 재생 오류: {str(e)}")
    finally:
        # 임시 파일 삭제
        try:
            if file_path and TEMP_DIR in Path(file_path).parents:
                os.remove(file_path)
        except Exception:
            pass

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

def cleanup_temp_files():
    """임시 파일 정리"""
    try:
        # 모든 임시 파일 삭제
        for file in TEMP_DIR.glob("*.wav"):
            try:
                file.unlink(missing_ok=True)  # Python 3.8+ 에서는 missing_ok 사용 가능
            except Exception:
                pass
        
        # 메모리 정리
        import gc
        gc.collect()
    except Exception:
        pass

if __name__ == "__main__":
    main()
