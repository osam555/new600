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
    'english': '영어',
    'korean': '한국어',
    'chinese': '중국어',
    'vietnamese': '베트남어',
    'japanese': '일본어',
    'thai': '태국어',
    'filipino': '필리핀어',
    'russian': '러시아어',
    'uzbek': '우즈베크어',
    'mongolian': '몽골어',
    'nepali': '네팔어',
    'myanmar': '미얀마어',
    'indonesian': '인도네시아어',
    'cambodian': '캄보디아어'
}

# 음성 매핑 확장 (edge-tts 지원 언어만)
VOICE_MAPPING = {
    'english': {
        "Steffan (US)": "en-US-SteffanNeural",
        "Jenny (US)": "en-US-JennyNeural",    # Jenny 추가 확인
        "Roger (US)": "en-US-RogerNeural",
        "Sonia (UK)": "en-GB-SoniaNeural",
        "Brian (US)": "en-US-BrianNeural",
        "Emma (US)": "en-US-EmmaNeural",
        "Guy (US)": "en-US-GuyNeural",
        "Aria (US)": "en-US-AriaNeural",
        "Ryan (UK)": "en-GB-RyanNeural"
    },
    'korean': {
        "선희": "ko-KR-SunHiNeural",
        "인준": "ko-KR-InJoonNeural"
    },
    'chinese': {
        'XiaoxiaoNeural': 'zh-CN-XiaoxiaoNeural',  # 정확한 음성 ID로 수정
        'Yunjian': 'zh-CN-YunjianNeural'
    },
    'vietnamese': {
        "HoaiMy": "vi-VN-HoaiMyNeural",  # 여성 음성
        "NamMinh": "vi-VN-NamMinhNeural"  # 남성 음성
    },
    'japanese': {
        "Nanami": "ja-JP-NanamiNeural",
        "Keita": "ja-JP-KeitaNeural",
    },
    'thai': {
        "Niwat": "th-TH-NiwatNeural",
        "Premwadee": "th-TH-PremwadeeNeural"
    },
    'filipino': {
        "Angelo": "fil-PH-AngeloNeural",
        "Blessica": "fil-PH-BlessicaNeural"
    },
    'russian': {
        "Dmitry": "ru-RU-DmitryNeural",
        "Svetlana": "ru-RU-SvetlanaNeural"
    },
    'uzbek': {
        "Dmitry": "ru-RU-DmitryNeural"  # 우즈벡어에 러시아어 드미트리 사용
    },
    'indonesian': {
        "Gadis": "id-ID-GadisNeural",
        "Ardi": "id-ID-ArdiNeural"
    }
}

# 언어 설정 업데이트 (엑셀 순서대로)
LANGUAGES = [
    'english', 'korean', 'chinese', 'vietnamese', 'japanese',
    'thai', 'filipino', 'russian', 'uzbek', 'mongolian',
    'nepali', 'myanmar', 'indonesian', 'cambodian', 'none'
]

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

def initialize_session_state():
    """강제 초기화 추가"""
    if 'initialized' not in st.session_state:
        st.session_state.clear()
        st.session_state.initialized = True
        st.session_state.page = 'settings'
        
    # 기본 설정값 정의
    default_settings = {
        'first_lang': 'korean',     # 1순위 한국어
        'second_lang': 'english',   # 2순위 영어
        'third_lang': 'english',    # 3순위 영어
        'first_repeat': 1,          # 1순위 1회
        'second_repeat': 1,         # 2순위 1회
        'third_repeat': 1,          # 3순위 1회
        'first_voice': '선희',      # 1순위 선희
        'second_voice': 'Steffan (US)',  # 2순위 스테판
        'third_voice': 'Jenny (US)',     # 3순위 제니
        'first_lang_speed': 2.0,    # 1순위 2.0배
        'second_lang_speed': 2.0,   # 2순위 2.0배
        'third_lang_speed': 3.0,    # 3순위 3.0배
        # 순위별 폰트 크기 기본값
        'first_lang_font_size': 32,
        'second_lang_font_size': 32,
        'third_lang_font_size': 32,
        # 순위별 색상 기본값
        'first_lang_color': '#00FF00',   # 초록색
        'second_lang_color': '#FFFFF0',  # 아이보리
        'third_lang_color': '#00FF00',   # 초록색
        'eng_voice': 'Steffan',
        'kor_voice': '선희',
        'zh_voice': 'XiaoxiaoNeural',  # 중국어 기본 음성을 여성(Xiaoxiao)으로 변경
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
    }
    
    # 설정이 없는 경우 기본값으로 초기화
    if 'settings' not in st.session_state:
        st.session_state.settings = default_settings.copy()
    else:
        # 기존 설정에 없는 키가 있다면 기본값으로 설정
        for key, value in default_settings.items():
            if key not in st.session_state.settings:
                st.session_state.settings[key] = value

    # 3순위 언어가 'none'으로 설정되어 있다면 'english'로 변경
    if st.session_state.settings.get('third_lang') == 'none':
        st.session_state.settings['third_lang'] = 'english'

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

    # CSS 스타일 업데이트
    st.markdown(f"""
        <style>
            /* 각 순위별 텍스트 스타일 */
            div[class*="first-lang-text"] {{
                font-size: {default_settings['first_lang_font_size']}px !important;
                color: {default_settings['first_lang_color']} !important;
                line-height: 1.5 !important;
                margin: 10px 0 !important;
            }}
            div[class*="second-lang-text"] {{
                font-size: {default_settings['second_lang_font_size']}px !important;
                color: {default_settings['second_lang_color']} !important;
                line-height: 1.5 !important;
                margin: 10px 0 !important;
            }}
            div[class*="third-lang-text"] {{
                font-size: {default_settings['third_lang_font_size']}px !important;
                color: {default_settings['third_lang_color']} !important;
                line-height: 1.5 !important;
                margin: 10px 0 !important;
            }}
        </style>
    """, unsafe_allow_html=True)

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
        
        # 서브헤더 스타일 CSS 수정
        st.markdown("""
            <style>
                /* 서브헤더 스타일 */
                .stMarkdown h2,
                .streamlit-expanderHeader,
                [data-testid="stSidebarNav"] h2,
                div[data-testid="stMarkdownContainer"] h2,
                .st-emotion-cache-1629p8f h2,
                .st-emotion-cache-1y4p8pa {
                    font-size: 1.2rem !important;
                    color: #00FF00 !important;
                    border-bottom: 2px solid #00FF00 !important;
                    padding-bottom: 0.3rem !important;
                    margin-top: 1rem !important;
                    margin-bottom: 1rem !important;
                    display: block !important;
                    width: 100% !important;
                }
            </style>
        """, unsafe_allow_html=True)

        
        settings = st.session_state.settings
        col1, col2 = st.columns([0.7, 0.3])
        with col1:
            st.markdown('<h1 style="font-size: 2rem; color: #FF0000;">도파민 대충영어 : 2배 한국어</h1>', unsafe_allow_html=True)
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
                
                # 선택된 시트 데이터 읽기
                df = pd.read_excel(
                    EXCEL_PATH,
                    sheet_name=selected_sheet,
                    header=0,
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
        st.subheader("언어 순위 설정")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # 1순위 언어 선택
            st.session_state.settings['first_lang'] = st.selectbox(
                "1순위 언어",
                LANGUAGES,
                index=LANGUAGES.index(st.session_state.settings.get('first_lang', 'korean')),
                key='first_lang'
            )
            if st.session_state.settings['first_lang'] != 'none':
                # 1순위 음성 선택
                first_lang = st.session_state.settings['first_lang']
                if first_lang in VOICE_MAPPING:
                    voices = VOICE_MAPPING[first_lang]
                    # 한국어일 경우 선희를 기본값으로
                    if first_lang == 'korean':
                        default_voice = '선희'
                    else:
                        female_voices = {k: v for k, v in voices.items() if 'female' in v.lower() or any(name in v.lower() for name in ['sunhi', 'jenny', 'sonia', 'emma', 'aria', 'xiaoxiao', 'hoaimy', 'nanami', 'premwadee', 'blessica', 'svetlana', 'gadis'])}
                        default_voice = list(female_voices.keys())[0] if female_voices else list(voices.keys())[0]
                    
                    settings['first_voice'] = st.selectbox(
                        "1순위 음성",
                        options=list(voices.keys()),
                        index=list(voices.keys()).index(settings.get('first_voice', default_voice)),
                        key='first_voice_select'
                    )
                
                # 반복 횟수 선택
                repeat_options = ['없음', '1', '2', '3', '4', '5']
                current_repeat = str(st.session_state.settings.get('first_repeat', 1))
                selected_repeat = st.selectbox(
                    "1순위 반복 횟수",
                    options=repeat_options,
                    index=repeat_options.index(current_repeat) if current_repeat in repeat_options else 1,
                    key='first_repeat_select'
                )
                st.session_state.settings['first_repeat'] = 0 if selected_repeat == '없음' else int(selected_repeat)

        with col2:
            # 2순위 언어 선택
            st.session_state.settings['second_lang'] = st.selectbox(
                "2순위 언어",
                LANGUAGES,
                index=LANGUAGES.index(st.session_state.settings.get('second_lang', 'english')),
                key='second_lang'
            )
            if st.session_state.settings['second_lang'] != 'none':
                # 2순위 음성 선택
                second_lang = st.session_state.settings['second_lang']
                if second_lang in VOICE_MAPPING:
                    voices = VOICE_MAPPING[second_lang]
                    # 영어일 경우 Steffan (US)를 기본값으로
                    if second_lang == 'english':
                        default_voice = 'Steffan (US)'
                    else:
                        male_voices = {k: v for k, v in voices.items() if 'male' in v.lower() or any(name in v.lower() for name in ['steffan', 'roger', 'brian', 'guy', 'ryan', 'injoon', 'yunjian', 'namminh', 'keita', 'niwat', 'angelo', 'dmitry', 'ardi'])}
                        default_voice = list(male_voices.keys())[0] if male_voices else list(voices.keys())[0]
                    
                    settings['second_voice'] = st.selectbox(
                        "2순위 음성",
                        options=list(voices.keys()),
                        index=list(voices.keys()).index(settings.get('second_voice', default_voice)),
                        key='second_voice_select'
                    )
                
                # 반복 횟수 선택
                repeat_options = ['없음', '1', '2', '3', '4', '5']
                current_repeat = str(st.session_state.settings.get('second_repeat', 1))
                selected_repeat = st.selectbox(
                    "2순위 반복 횟수",
                    options=repeat_options,
                    index=repeat_options.index(current_repeat) if current_repeat in repeat_options else 1,
                    key='second_repeat_select'
                )
                st.session_state.settings['second_repeat'] = 0 if selected_repeat == '없음' else int(selected_repeat)

        with col3:
            # 3순위 언어 선택
            st.session_state.settings['third_lang'] = st.selectbox(
                "3순위 언어",
                LANGUAGES,
                index=LANGUAGES.index(st.session_state.settings.get('third_lang', 'english')),
                key='third_lang'
            )
            if st.session_state.settings['third_lang'] != 'none':
                # 3순위 음성 선택
                third_lang = st.session_state.settings['third_lang']
                if third_lang in VOICE_MAPPING:
                    voices = VOICE_MAPPING[third_lang]
                    # 영어일 경우 Jenny (US)를 기본값으로
                    if third_lang == 'english':
                        default_voice = 'Jenny (US)'
                        if default_voice not in voices:
                            default_voice = list(voices.keys())[0]  # 없으면 첫 번째 음성 선택
                    else:
                        female_voices = {k: v for k, v in voices.items() if 'female' in v.lower() or any(name in v.lower() for name in ['sunhi', 'jenny', 'sonia', 'emma', 'aria', 'xiaoxiao', 'hoaimy', 'nanami', 'premwadee', 'blessica', 'svetlana', 'gadis'])}
                        default_voice = list(female_voices.keys())[0] if female_voices else list(voices.keys())[0]
                    
                    current_voice = settings.get('third_voice', default_voice)
                    if current_voice not in voices:
                        current_voice = default_voice
                    
                    settings['third_voice'] = st.selectbox(
                        "3순위 음성",
                        options=list(voices.keys()),
                        index=list(voices.keys()).index(current_voice),
                        key='third_voice_select'
                    )
                
                
                # 반복 횟수 선택
                repeat_options = ['없음', '1', '2', '3', '4', '5']
                current_repeat = str(st.session_state.settings.get('third_repeat', 1))
                selected_repeat = st.selectbox(
                    "3순위 반복 횟수",
                    options=repeat_options,
                    index=repeat_options.index(current_repeat) if current_repeat in repeat_options else 1,
                    key='third_repeat_select'
                )
                st.session_state.settings['third_repeat'] = 0 if selected_repeat == '없음' else int(selected_repeat)

        # 배속 옵션 설정 (슬라이더로 변경)
        with col1:
            # 1순위 언어 배속
            first_lang = settings['first_lang']
            if first_lang != 'none':
                settings['first_lang_speed'] = st.slider(
                    "1순위 언어 배속",
                    min_value=0.8,
                    max_value=4.0,
                    value=float(settings.get('first_lang_speed', 2.0)),
                    step=0.2,
                    format="%.1f",
                    key="first_speed_slider"
                )

        with col2:
            # 2순위 언어 배속
            second_lang = settings['second_lang']
            if second_lang != 'none':
                settings['second_lang_speed'] = st.slider(
                    "2순위 언어 배속",
                    min_value=0.8,
                    max_value=4.0,
                    value=float(settings.get('second_lang_speed', 2.0)),
                    step=0.2,
                    format="%.1f",
                    key="second_speed_slider"
                )

        with col3:
            # 3순위 언어 배속
            third_lang = settings['third_lang']
            if third_lang != 'none':
                settings['third_lang_speed'] = st.slider(
                    "3순위 언어 배속",
                    min_value=0.8,
                    max_value=4.0,
                    value=float(settings.get('third_lang_speed', 3.0)),
                    step=0.2,
                    format="%.1f",
                    key="third_speed_slider"
                )

        # 배속 설정 아래에 학습 시작 버튼 추가
        if st.button("▶️ 학습 시작", use_container_width=True, key="start_btn_speed"):
            save_settings(settings)
            st.session_state.page = 'learning'
            st.rerun()

        # 문장 재생 설정
        st.subheader("문장 재생")
        col1, col2, col3 = st.columns(3)
        
        # 0.1초부터 2초까지 0.1초 간격의 옵션 생성
        time_options = [round(x * 0.1, 1) for x in range(1, 21)]  # 0.1-2.0초
        
        with col1:
            settings['spacing'] = st.selectbox(
                "문장 간격(초)",
                options=time_options,
                index=time_options.index(float(settings.get('spacing', 1.0))),
                key="spacing"
            )

        with col2:
            settings['subtitle_delay'] = st.selectbox(
                "자막 먼저(초)",
                options=time_options,
                index=time_options.index(float(settings.get('subtitle_delay', 1.0))),
                key="subtitle_delay"
            )

        with col3:
            settings['break_interval'] = st.selectbox(
                "브레이크 문장",
                options=['없음', '5', '10', '15', '20'],
                index=0 if not settings.get('break_enabled', True) else 
                      ['없음', '5', '10', '15', '20'].index(str(settings.get('break_interval', 10))),
                key="break_interval"
            )
            settings['break_enabled'] = settings['break_interval'] != '없음'
            if settings['break_enabled']:
                settings['break_interval'] = int(settings['break_interval'])

        # 폰트 및 색상 설정
        st.subheader("폰트 크기 | 색깔")
        col1, col2, col3 = st.columns(3)

        with col1:
            # 1순위 언어 설정
            if first_lang != 'none':
                settings['first_lang_font_size'] = st.number_input(
                    "1순위 폰트 크기",
                    value=settings.get('first_lang_font_size', 32),
                    min_value=20,
                    max_value=50,
                    step=2,
                    key="first_lang_font_size"
                )
                selected_color = st.selectbox(
                    "1순위 색상",
                    options=list(COLOR_MAPPING.keys()),
                    index=list(COLOR_MAPPING.keys()).index('green'),
                    key="first_lang_color_select"
                )
                settings['first_lang_color'] = COLOR_MAPPING[selected_color]

        with col2:
            # 2순위 언어 설정
            if second_lang != 'none':
                settings['second_lang_font_size'] = st.number_input(
                    "2순위 폰트 크기",
                    value=settings.get('second_lang_font_size', 32),
                    min_value=20,
                    max_value=50,
                    step=2,
                    key="second_lang_font_size"
                )
                selected_color = st.selectbox(
                    "2순위 색상",
                    options=list(COLOR_MAPPING.keys()),
                    index=list(COLOR_MAPPING.keys()).index('ivory'),
                    key="second_lang_color_select"
                )
                settings['second_lang_color'] = COLOR_MAPPING[selected_color]

        with col3:
            # 3순위 언어 설정
            if third_lang != 'none':
                settings['third_lang_font_size'] = st.number_input(
                    "3순위 폰트 크기",
                    value=settings.get('third_lang_font_size', 32),
                    min_value=20,
                    max_value=50,
                    step=2,
                    key="third_lang_font_size"
                )
                selected_color = st.selectbox(
                    "3순위 색상",
                    options=list(COLOR_MAPPING.keys()),
                    index=list(COLOR_MAPPING.keys()).index('green'),
                    key="third_lang_color_select"
                )
                settings['third_lang_color'] = COLOR_MAPPING[selected_color]

        # CSS 스타일 업데이트 - 선택자 강화
        st.markdown(f"""
            <style>
                /* 각 순위별 텍스트 스타일 */
                .first-lang-text {{
                    font-size: {settings['first_lang_font_size']}px !important;
                    font-weight: normal !important;
                    color: {settings['first_lang_color']} !important;
                    line-height: 1.8 !important;
                    margin: 15px 0 !important;
                    padding: 5px 0 !important;
                }}
                .second-lang-text {{
                    font-size: {settings['second_lang_font_size']}px !important;
                    font-weight: normal !important;
                    color: {settings['second_lang_color']} !important;
                    line-height: 1.8 !important;
                    margin: 15px 0 !important;
                    padding: 5px 0 !important;
                }}
                .third-lang-text {{
                    font-size: {settings['third_lang_font_size']}px !important;
                    font-weight: normal !important;
                    color: {settings['third_lang_color']} !important;
                    line-height: 1.8 !important;
                    margin: 15px 0 !important;
                    padding: 5px 0 !important;
                }}

                /* Streamlit 마크다운 컨테이너 스타일 재정의 */
                div[data-testid="stMarkdownContainer"] .first-lang-text,
                div[data-testid="stMarkdownContainer"] .second-lang-text,
                div[data-testid="stMarkdownContainer"] .third-lang-text {{
                    font-size: inherit !important;
                    color: inherit !important;
                }}
            </style>
        """, unsafe_allow_html=True)

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

        # 기존 맨 아래 학습 시작 버튼 유지
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
            'english': 'Steffan (US)',
            'chinese': 'XiaoxiaoNeural',
            'japanese': 'Nanami',
            'vietnamese': 'HoaiMy',
            'thai': 'Niwat',
            'filipino': 'Angelo',
            'russian': 'Dmitry',
            'uzbek': 'Dmitry',  # 우즈벡어에 러시아어 드미트리 사용
            'indonesian': 'Gadis'
        }

        # 3순위 영어일 경우 제니로 설정
        if language == 'english' and voice_setting is None:
            return VOICE_MAPPING['english']['Jenny (US)']
            
        # 해당 언어가 음성 지원되는지 확인
        if language not in VOICE_MAPPING:
            return None
            
        # 설정된 음성이 없거나 매핑에 없는 경우 기본값 사용
        if not voice_setting or voice_setting not in VOICE_MAPPING.get(language, {}):
            voice_setting = default_voices.get(language)
            
        return VOICE_MAPPING[language][voice_setting]
    except Exception as e:
        st.error(f"음성 매핑 오류 ({language}): {str(e)}")
        return None

async def get_voice_file(text, voice, speed=1.0, output_file=None):
    """음성 파일 생성"""
    try:
        if not text or not voice:
            return None

        # edge-tts 설정
        communicate = edge_tts.Communicate(text, voice, rate=f"+{int((speed-1)*100)}%")
        
        # 임시 파일 경로 생성
        if output_file is None:
            timestamp = int(time.time() * 1000)
            output_file = TEMP_DIR / f"temp_{timestamp}.wav"

        # 기존 파일 삭제
        if os.path.exists(output_file):
            os.remove(output_file)

        # 음성 파일 생성
        await communicate.save(str(output_file))
        await asyncio.sleep(0.1)  # 파일 저장 완료 대기

        return str(output_file)

    except Exception as e:
        if os.path.exists(output_file):
            os.remove(output_file)
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
    settings = st.session_state.settings
    
    try:
        # 선택된 시트의 데이터 읽기 - 최적화
        df = pd.read_excel(
            EXCEL_PATH,
            sheet_name=settings.get('selected_sheet', 0),
            header=0,  # 첫 번째 행을 헤더로 사용
            engine='openpyxl',
            nrows=settings['end_row']  # 필요한 행만 읽기
        )

        # 헤더 매핑 정의
        header_mapping = {
            'en-미국': 'english',
            'ko-한국': 'korean', 
            'zh-중국': 'chinese',
            'vi-베트남': 'vietnamese',
            'ja-일본': 'japanese',
            'th-태국': 'thai',
            'fil-필리핀': 'filipino',
            'ru-러시아': 'russian',
            'uz-우즈벡': 'uzbek',
            'mn-몽골': 'mongolian',
            'ne-네팔': 'nepali',
            'my-미얀마': 'myanmar',
            'id-인니': 'indonesian',
            'km-캄보': 'cambodian'
        }

        # 컬럼명 변경
        df = df.rename(columns=header_mapping)
        
        start_idx = settings['start_row'] - 1
        end_idx = settings['end_row'] - 1

        # 선택된 언어의 데이터만 로드
        text_data = {}
        for lang in [settings['first_lang'], settings['second_lang'], settings['third_lang']]:
            if lang != 'none':
                if lang in df.columns:  # 컬럼이 존재하는지 확인
                    text_data[lang] = df[lang].iloc[start_idx:end_idx+1].tolist()
                else:
                    text_data[lang] = [""] * (end_idx - start_idx + 1)

        total_sentences = end_idx - start_idx + 1
        
        # 학습 UI 생성
        progress, status, subtitles, speed_info = create_learning_ui()

        # 배속 설정 가져오기 함수 수정
        def get_speed_for_language(lang, order):
            """
            lang: 언어
            order: 순위 (first, second, third)
            """
            # 순위별로 설정된 배속값 반환
            return float(settings.get(f'{order}_lang_speed', {
                'first': 2.0,   # 1순위 기본 2.0배
                'second': 2.0,  # 2순위 기본 2.0배
                'third': 3.0    # 3순위 기본 3.0배
            }[order]))

        while True:
            for i in range(total_sentences):
                # 자막 표시 부분을 음성 재생과 분리
                # 1순위 자막
                first_lang = settings['first_lang']
                if first_lang != 'none' and not settings['hide_subtitles']['first_lang']:
                    subtitles[0].markdown(
                        f'<div class="first-lang-text {first_lang}-text">{text_data[first_lang][i]}</div>',
                        unsafe_allow_html=True
                    )

                # 2순위 자막
                second_lang = settings['second_lang']
                if second_lang != 'none' and not settings['hide_subtitles']['second_lang']:
                    subtitles[1].markdown(
                        f'<div class="second-lang-text {second_lang}-text">{text_data[second_lang][i]}</div>',
                        unsafe_allow_html=True
                    )

                # 3순위 자막
                third_lang = settings['third_lang']
                if third_lang != 'none' and not settings['hide_subtitles']['third_lang']:
                    subtitles[2].markdown(
                        f'<div class="third-lang-text {third_lang}-text">{text_data[third_lang][i]}</div>',
                        unsafe_allow_html=True
                    )

                # 음성 재생 부분
                try:
                    # 1순위 음성 재생
                    if first_lang in VOICE_MAPPING:
                        voice = get_voice_mapping(first_lang, settings['first_voice'])
                        if voice:
                            speed = get_speed_for_language(first_lang, 'first')
                            for _ in range(settings['first_repeat']):
                                try:
                                    voice_file = await get_voice_file(text_data[first_lang][i], voice, speed)
                                    if voice_file:
                                        play_audio(voice_file)
                                    if _ < settings['first_repeat'] - 1:
                                        await asyncio.sleep(float(settings.get('spacing', 1.0)))
                                except Exception as e:
                                    st.error(f"1순위 음성 재생 오류: {str(e)}")
                                    continue

                    # 2순위 음성 재생
                    if second_lang in VOICE_MAPPING:
                        voice = get_voice_mapping(second_lang, settings['second_voice'])
                        if voice:
                            speed = get_speed_for_language(second_lang, 'second')
                            for _ in range(settings['second_repeat']):
                                try:
                                    voice_file = await get_voice_file(text_data[second_lang][i], voice, speed)
                                    if voice_file:
                                        play_audio(voice_file)
                                    if _ < settings['second_repeat'] - 1:
                                        await asyncio.sleep(float(settings.get('spacing', 1.0)))
                                except Exception as e:
                                    st.error(f"2순위 음성 재생 오류: {str(e)}")
                                    continue

                    # 3순위 음성 재생
                    if third_lang in VOICE_MAPPING:
                        voice = get_voice_mapping(third_lang, settings['third_voice'])
                        if voice:
                            speed = get_speed_for_language(third_lang, 'third')
                            for _ in range(settings['third_repeat']):
                                try:
                                    voice_file = await get_voice_file(text_data[third_lang][i], voice, speed)
                                    if voice_file:
                                        play_audio(voice_file)
                                    if _ < settings['third_repeat'] - 1:
                                        await asyncio.sleep(float(settings.get('spacing', 1.0)))
                                except Exception as e:
                                    st.error(f"3순위 음성 재생 오류: {str(e)}")
                                    continue

                except Exception as e:
                    st.error(f"음성 재생 중 오류 발생: {str(e)}")
                    continue

                # 문장 간 간격
                await asyncio.sleep(float(settings.get('spacing', 1.0)))

    except Exception as e:
        st.error(f"학습 중 오류가 발생했습니다: {str(e)}")
        traceback.print_exc()
        return

def create_personalized_ui():
    """개인별 맞춤 UI 생성"""
    st.title("개인별 설정 기억하기")

    # 언어 선택 - 문법 수정
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
    """음성 파일 재생"""
    try:
        if not os.path.exists(file_path):
            return

        # 파일 읽기
        with open(file_path, 'rb') as f:
            audio_bytes = f.read()

        if not audio_bytes:
            return

        # base64로 인코딩
        audio_base64 = base64.b64encode(audio_bytes).decode()
        
        # HTML 오디오 요소 생성
        st.markdown(f"""
            <audio autoplay="true">
                <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
            </audio>
        """, unsafe_allow_html=True)
        
        # 대기 시간
        duration = len(audio_bytes) / 32000  # 근사값
        time.sleep(max(duration + sentence_interval, 0.5))

    finally:
        try:
            if TEMP_DIR in Path(file_path).parents:
                os.remove(file_path)
        except:
            pass

async def wait_for_audio_complete(file_path=None):
    """음성 재생 완료 대기"""
    try:
        if file_path and os.path.exists(file_path):
            with wave.open(file_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / float(rate)
                await asyncio.sleep(duration)
        else:
            await asyncio.sleep(0.5)
    except Exception:
        # 기본 대기 시간
        await asyncio.sleep(0.5)

def load_excel_data():
    """엑셀 데이터 로드 함수"""
    try:
        # 엑셀 파일 읽기
        df = pd.read_excel(EXCEL_PATH)
        
        # 헤더 매핑 정의
        header_mapping = {
            'en-미국': 'english',
            'ko-한국': 'korean', 
            'zh-중국': 'chinese',
            'vi-베트남': 'vietnamese',
            'ja-일본': 'japanese',
            'th-태국': 'thai',
            'fil-필리핀': 'filipino',
            'ru-러시아': 'russian',
            'uz-우즈벡': 'uzbek',
            'mn-몽골': 'mongolian',
            'ne-네팔': 'nepali',
            'my-미얀마': 'myanmar',
            'id-인니': 'indonesian',
            'km-캄보': 'cambodian'
        }
        
        # 컬럼명 변경
        df = df.rename(columns=header_mapping)
        
        return df
        
    except Exception as e:
        st.error(f"엑셀 파일 로드 중 오류: {str(e)}")
        return None

def update_css_styles(settings):
    css_styles = ""
    # 기존 언어들의 스타일
    for lang in LANGUAGES:
        if lang != 'none':
            css_styles += f"""
                .{lang}-text {{
                    color: {settings.get(f'{lang}_color', settings.get('other_color', '#00FF00'))} !important;
                    font-size: {settings.get(f'{lang}_font_size', settings.get('other_font_size', 28))}px !important;
                    font-family: {settings.get(f'{lang}_font', settings.get('other_font', 'Arial'))} !important;
                }}
            """
    return css_styles

if __name__ == "__main__":
    main()
