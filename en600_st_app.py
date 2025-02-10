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

## streamlit run word_memory/en600_st_app.py

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
    'japanese': '일본어'
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
        "Naoki": "ja-JP-NaokiNeural"
    }
}

# 언어 설정
LANGUAGES = ['english', 'korean', 'chinese', 'japanese', 'none']

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
    """세션 상태 초기화"""
    if 'user_language' not in st.session_state:
        st.session_state.user_language = 'korean'  # 기본값 설정

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
    
    if 'settings' not in st.session_state:
        # 저장된 설정 파일이 있으면 로드
        try:
            if SETTINGS_PATH.exists():
                with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                    # 테마에 따라 색상 업데이트
                    if is_dark_mode:
                        saved_settings.update({
                            'english_color': '#00FF00',   # 초록색으로 변경
                            'korean_color': '#00FF00',   # 초록색으로 변경
                            'chinese_color': '#00FF00',  # 초록색으로 변경
                            'japanese_color': '#00FF00', # 초록색으로 변경
                        })
                    else:
                        saved_settings.update({
                            'english_color': '#000000',   # 검정색
                            'korean_color': '#000000',    # 검정색
                            'chinese_color': '#000000',   # 검정색
                            'japanese_color': '#000000' if is_dark_mode else '#FFFFFF',
                        })
                    st.session_state.settings = saved_settings
                    return
        except Exception as e:
            st.error(f"설정 파일 로드 중 오류: {e}")
        
        # 저장된 설정이 없으면 기본값 사용
        st.session_state.settings = {
            'first_lang': 'korean',
            'second_lang': 'english',
            'third_lang': 'chinese',
            'first_repeat': 0,
            'second_repeat': 1,
            'third_repeat': 1,  
            'kor_voice': '선희',
            'eng_voice': 'Steffan',
            'zh_voice': 'Yunjian',
            'jp_voice': 'Nanami',
            'start_row': 301,
            'end_row': 350,
            'word_delay': 0.5,
            'spacing': 0.5,
            'english_speed': 3.0,
            'korean_speed': 2.0,
            'chinese_speed': 2.0,
            'japanese_speed': 2.0,
            'subtitle_delay': 0.5,
            'keep_subtitles': True,
            'break_enabled': True,
            'break_interval': 10,
            'break_duration': 5,
            'next_sentence_time': 0.5,
            'english_font': 'Pretendard',
            'korean_font': 'Pretendard',
            'chinese_font': 'SimSun',
            'english_font_size': 32,
            'korean_font_size': 25,
            'chinese_font_size': 32,
            'japanese_font': 'PretendardJP-Light',
            'japanese_font_size': 28,
            'japanese_color': '#00FF00' if is_dark_mode else '#000000',
            'hide_subtitles': {
                'first_lang': False,
                'second_lang': False,
                'third_lang': False,
            },
            'auto_repeat': True,
            'repeat_count': 5,  # 기본 반복 횟수 추가
            'english_color': '#00FF00',  # 다크모드: 초록색, 브라이트모드: 검정색
            'korean_color': '#00FF00',   # 다크모드: 초록색, 브라이트모드: 검정색
            'chinese_color': '#00FF00',  # 다크모드: 초록색, 브라이트모드: 검정색
            'japanese_speed': 2.0,  # 일본어 배속 기본값 추가
        }

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

def create_settings_ui():
    """설정 화면 UI 생성"""
    
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
            })
    else:
        if settings['korean_color'] == '#FFFFFF':  # 이전에 다크 모드였다면
            settings.update({
                'english_color': '#000000',   # 검정색
                'korean_color': '#000000',    # 검정색
                'chinese_color': '#000000',   # 검정색
                'japanese_color': '#FFFFFF',
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
            
        if st.button("학습 시작", use_container_width=True, key="start_learning_btn"):
            # 최종 유효성 검사
            error_messages = []
            start_row = settings['start_row']
            end_row = settings['end_row']
            
            if start_row > end_row:
                error_messages.append("🚨 시작 번호는 종료 번호보다 작아야 합니다")
            if end_row > max_row:
                error_messages.append(f"🚨 종료 번호는 {max_row}을 초과할 수 없습니다")
            if not (1 <= start_row <= max_row):
                error_messages.append(f"🚨 시작 번호는 1~{max_row} 사이여야 합니다")
            if not (1 <= end_row <= max_row):
                error_messages.append(f"🚨 종료 번호는 1~{max_row} 사이여야 합니다")

            if error_messages:
                for msg in error_messages:
                    st.error(msg)
            else:
                st.session_state.page = 'learning'
                st.rerun()

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

    # 언어 순서 설정
    st.subheader("자막 | 음성 | 속도")
    col1, col2, col3 = st.columns(3)
    with col1:
        settings['first_lang'] = st.selectbox("1순위 언어",
            options=['korean', 'english', 'chinese', 'japanese'],
            index=['korean', 'english', 'chinese', 'japanese'].index(settings['first_lang']),
            format_func=lambda x: LANG_DISPLAY[x],
            key="settings_first_lang")
        first_repeat = st.number_input("음성 재생(횟수)",
                                     value=settings['first_repeat'],
                                     min_value=0,
                                     key="first_repeat",
                                     format="%d")
        speed_key = f"{settings['first_lang']}_speed"
        first_speed = st.number_input("음성 속도(배)",
                                    value=settings[speed_key],
                                    min_value=0.1,
                                    step=0.1,
                                    format="%.1f",
                                    key="first_speed")
        settings[speed_key] = first_speed

    with col2:
        settings['second_lang'] = st.selectbox("2순위 언어",
            options=['korean', 'english', 'chinese', 'japanese'],
            index=['korean', 'english', 'chinese', 'japanese'].index(settings['second_lang']),
            format_func=lambda x: LANG_DISPLAY[x],
            key="settings_second_lang")
        second_repeat = st.number_input("음성 재생(횟수)",
                                      value=settings['second_repeat'],
                                      min_value=0,
                                      key="second_repeat",
                                      format="%d")
        speed_key = f"{settings['second_lang']}_speed"
        second_speed = st.number_input("음성 속도(배)",
                                     value=settings[speed_key],
                                     min_value=0.1,
                                     step=0.1,
                                     format="%.1f",
                                     key="second_speed")
        settings[speed_key] = second_speed

    with col3:
        settings['third_lang'] = st.selectbox("3순위 언어",
            options=['korean', 'english', 'chinese', 'japanese'],
            index=['korean', 'english', 'chinese', 'japanese'].index(settings['third_lang']),
            format_func=lambda x: LANG_DISPLAY[x],
            key="settings_third_lang")
        third_repeat = st.number_input("음성 재생(횟수)",
                                     value=settings['third_repeat'],
                                     min_value=0,
                                     key="third_repeat",
                                     format="%d")
        speed_key = f"{settings['third_lang']}_speed"
        third_speed = st.number_input("음성 속도(배)",
                                    value=settings[speed_key],
                                    min_value=0.1,
                                    step=0.1,
                                    format="%.1f",
                                    key="third_speed")
        settings[speed_key] = third_speed

    # 문장 재생 설정
    st.subheader("문장 재생")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        spacing = st.number_input("문장 간격(초)",
                                value=settings['spacing'],
                                min_value=0.1,
                                step=0.1,
                                format="%.1f",
                                key="spacing")
    with col2:
        subtitle_delay = st.number_input("자막 딜레이(초)",
                                       value=settings['subtitle_delay'],
                                       min_value=0.1,
                                       step=0.1,
                                       format="%.1f",
                                       key="subtitle_delay")
    with col3:
        next_sentence_time = st.number_input("다음 문장(초)",
                                           value=settings['next_sentence_time'],
                                           min_value=0.1,
                                           step=0.1,
                                           format="%.1f",
                                           key="next_sentence_time")
    with col4:
        settings['break_interval'] = st.selectbox("브레이크 문장 갯수",
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

    # 빈 공간 추가
    st.markdown("<div style='height: 1em'></div>", unsafe_allow_html=True)

    # 폰트 및 색상 설정 섹션
    st.subheader("폰트 설정")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        col1_1, col1_2 = st.columns([0.7, 0.3])
        with col1_1:
            settings['korean_font'] = st.selectbox("한글 폰트",
                                                options=['Pretendard', '맑은 고딕', '나눔고딕', '굴림'],
                                                index=['Pretendard', '맑은 고딕', '나눔고딕', '굴림'].index(settings['korean_font']),
                                                key="korean_font_learning")
        with col1_2:
            settings['korean_font_size'] = st.number_input("크기",
                                                        value=settings['korean_font_size'],
                                                        min_value=10,
                                                        max_value=50,
                                                        step=1,
                                                        key="korean_font_size_learning")

    with col2:
        col2_1, col2_2 = st.columns([0.7, 0.3])
        with col2_1:
            settings['english_font'] = st.selectbox("영어 폰트",
                                                  options=['Pretendard', 'Arial', 'Times New Roman', 'Verdana'],
                                                  index=['Pretendard', 'Arial', 'Times New Roman', 'Verdana'].index(settings['english_font']),
                                                  key="english_font_learning")
        with col2_2:
            settings['english_font_size'] = st.number_input("크기",
                                                        value=settings['english_font_size'],
                                                        min_value=10,
                                                        max_value=50,
                                                        step=1,
                                                        key="english_font_size_learning")

    with col3:
        col3_1, col3_2 = st.columns([0.7, 0.3])
        with col3_1:
            settings['chinese_font'] = st.selectbox("중국어 폰트",
                                                  options=['SimSun', 'Microsoft YaHei', 'SimHei'],
                                                  index=['SimSun', 'Microsoft YaHei', 'SimHei'].index(settings['chinese_font']),
                                                  key="chinese_font_learning")
        with col3_2:
            settings['chinese_font_size'] = st.number_input("크기",
                                                        value=settings['chinese_font_size'],
                                                        min_value=10,
                                                        max_value=50,
                                                        step=1,
                                                        key="chinese_font_size_learning")

    with col4:
        col4_1, col4_2 = st.columns([0.7, 0.3])
        with col4_1:
            settings['japanese_font'] = st.selectbox("일본어 폰트",
                                                  options=['PretendardJP-Light', 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', 'MS Gothic'],
                                                  index=['PretendardJP-Light', 'Hiragino Kaku Gothic ProN', 'Hiragino Sans', 'MS Gothic'].index(settings['japanese_font']),
                                                  key="japanese_font_learning")
        with col4_2:
            settings['japanese_font_size'] = st.number_input("크기",
                                                        value=settings['japanese_font_size'],
                                                        min_value=10,
                                                        max_value=50,
                                                        step=1,
                                                        key="japanese_font_size_learning")

    # 색상 설정 수정
    st.subheader("색상 설정")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        default_color = 'green'  # 기본값을 초록색으로 변경
        selected_color = st.selectbox("한글 색상",
                                    options=list(COLOR_MAPPING.keys()),
                                    index=list(COLOR_MAPPING.keys()).index(default_color),
                                    key="korean_color_select")
        settings['korean_color'] = COLOR_MAPPING[selected_color]

    with col2:
        default_color = 'green'  # 기본값을 초록색으로 변경
        selected_color = st.selectbox("영어 색상",
                                    options=list(COLOR_MAPPING.keys()),
                                    index=list(COLOR_MAPPING.keys()).index(default_color),
                                    key="english_color_select")
        settings['english_color'] = COLOR_MAPPING[selected_color]

    with col3:
        default_color = 'green'  # 기본값을 초록색으로 변경
        selected_color = st.selectbox("중국어 색상",
                                    options=list(COLOR_MAPPING.keys()),
                                    index=list(COLOR_MAPPING.keys()).index(default_color),
                                    key="chinese_color_select")
        settings['chinese_color'] = COLOR_MAPPING[selected_color]

    with col4:
        default_color = 'green'  # 기본값을 초록색으로 변경
        selected_color = st.selectbox("일본어 색상",
                                    options=list(COLOR_MAPPING.keys()),
                                    index=list(COLOR_MAPPING.keys()).index(default_color),
                                    key="japanese_color_select")
        settings['japanese_color'] = COLOR_MAPPING[selected_color]

    # 폰트 크기 변경 시 즉시 반영을 위한 CSS 업데이트
    st.markdown(f"""
        <style>
            .english-text {{
                font-size: {settings['english_font_size']}px !important;
            }}
            .korean-text {{
                font-size: {settings['korean_font_size']}px !important;
            }}
            .chinese-text {{
                font-size: {settings['chinese_font_size']}px !important;
            }}
            .japanese-text {{
                font-size: {settings['japanese_font_size']}px !important;
            }}
        </style>
    """, unsafe_allow_html=True)

    # 입력 필드에 CSS 클래스 적용
    st.markdown("""
        <style>
            /* 숫자 입력 필드 스타일 */
            div[data-testid="stNumberInput"] {{
                max-width: 150px;
            }}
            
            /* 숫자 입력 필드 레이블 스타일 */
            div[data-testid="stNumberInput"] label {{
                font-size: 15px !important;
            }}
            
            /* 숫자 입력 필드 입력창 스타일 */
            div[data-testid="stNumberInput"] input {{
                font-size: 15px !important;
                padding: 4px 8px !important;
            }}
        </style>
    """, unsafe_allow_html=True)

    # 설정값 업데이트
    settings.update({
        'first_lang': settings['first_lang'],
        'second_lang': settings['second_lang'],
        'third_lang': settings['third_lang'],
        'first_repeat': first_repeat,
        'second_repeat': second_repeat,
        'third_repeat': third_repeat,
        'eng_voice': settings['eng_voice'],
        'kor_voice': settings['kor_voice'],
        'zh_voice': settings['zh_voice'],
        'jp_voice': settings['jp_voice'],
        'spacing': spacing,
        'subtitle_delay': subtitle_delay,
        'keep_subtitles': settings['keep_subtitles'],
        'break_enabled': settings['break_enabled'],
        'hide_subtitles': {
            'first_lang': hide_first,
            'second_lang': hide_second,
            'third_lang': hide_third,
        },
        'english_font': settings['english_font'],
        'korean_font': settings['korean_font'],
        'chinese_font': settings['chinese_font'],
        'english_font_size': settings['english_font_size'],
        'korean_font_size': settings['korean_font_size'],
        'chinese_font_size': settings['chinese_font_size'],
        'japanese_font': settings['japanese_font'],
        'japanese_font_size': settings['japanese_font_size'],
        'japanese_color': settings['japanese_color'],
    })

    # 설정값 업데이트
    settings.update({
        'start_row': settings['start_row'],
        'end_row': settings['end_row']
    })

    # Save settings
    save_settings(settings)

    # CSS에 일본어 폰트 추가
    st.markdown(f"""
        <style>
        @font-face {{
            font-family: 'PretendardJP-Light';
            src: url('{str(SCRIPT_DIR / "base/PretendardJP-Light.otf")}') format('opentype');
        }}
        </style>
    """, unsafe_allow_html=True)

def play_audio(file_path):
    """음성 파일 재생"""
    try:
        if not file_path or not os.path.exists(file_path):
            st.error(f"파일 경로 오류: {file_path}")
            return

        # base64 인코딩
        with open(file_path, 'rb') as f:
            audio_bytes = f.read()
        audio_base64 = base64.b64encode(audio_bytes).decode()

        # HTML audio 태그로 재생
        st.markdown(f"""
            <audio autoplay style="display: none">
                <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
            </audio>
        """, unsafe_allow_html=True)

        # soundfile로 파일 길이 계산
        data, samplerate = sf.read(file_path)
        duration = len(data) / samplerate
        
        # 오디오 재생이 끝날 때까지 대기
        time.sleep(duration)

    except Exception as e:
        st.error(f"음성 재생 오류: {e}")
    finally:
        # 임시 파일 삭제
        if file_path and TEMP_DIR in Path(file_path).parents:
            try:
                os.remove(file_path)
            except Exception as e:
                st.error(f"임시 파일 삭제 오류: {e}")

async def create_audio(text, voice, speed=1.0):
    """음성 파일 생성"""
    try:
        if not text or not voice:
            return None

        # 임시 파일 이름 생성 (타임스탬프 추가)
        output_file = TEMP_DIR / f"temp_{int(time.time()*1000)}.wav"

        # 배속 계산
        if speed > 1:
            rate_str = f"+{int((speed - 1) * 100)}%"
        else:
            rate_str = f"-{int((1 - speed) * 100)}%"

        # 음성 생성
        communicate = edge_tts.Communicate(text, voice, rate=rate_str)
        await communicate.save(str(output_file))
        
        # 파일 생성 확인
        if output_file.exists() and output_file.stat().st_size > 0:
            return str(output_file)
        else:
            st.error(f"음성 파일 생성 실패: {text[:20]}...")
            return None

    except Exception as e:
        st.error(f"음성 생성 오류: {e}")
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
        
        # 한글 배속 정보
        ko_speed = st.session_state.settings['korean_speed']
        ko_speed_text = str(int(ko_speed)) if ko_speed.is_integer() else f"{ko_speed:.1f}"
        speed_info.append(f"한글 {ko_speed_text}배")
        
        # 영어 배속 정보
        eng_speed = st.session_state.settings['english_speed']
        eng_speed_text = str(int(eng_speed)) if eng_speed.is_integer() else f"{eng_speed:.1f}"
        speed_info.append(f"영어 {eng_speed_text}배")
        
        # 배속 정보를 하나의 문자열로 결합
        speed_display = " | ".join(speed_info)
    
    # 자막을 위한 빈 컨테이너
    subtitles = [st.empty() for _ in range(3)]
    
    return progress, status, subtitles

async def create_break_audio():
    """브레이크 음성 생성"""
    break_msg = "쉬는 시간입니다, 5초간의 여유를 느껴보세요"
    break_voice = VOICE_MAPPING['korean']['선희']
    audio_file = await create_audio(break_msg, break_voice, 1.0)
    return audio_file

async def start_learning():
    """학습 시작"""
    settings = st.session_state.settings
    sentence_count = 0
    repeat_count = 0  # 현재 반복 횟수
    
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
        selected_data = df.iloc[start_idx:end_idx+1, :3]
        
        english = selected_data.iloc[:, 0].tolist()
        korean = selected_data.iloc[:, 1].tolist()
        chinese = selected_data.iloc[:, 2].tolist()
        japanese = df.iloc[start_idx:end_idx+1, 4].tolist()  # E열(인덱스 4)에서 일본어 읽기
        total_sentences = len(english)
        
    except PermissionError:
        st.error("엑셀 파일이 다른 프로그램에서 열려있습니다. 파일을 닫고 다시 시도해주세요.")
        return
    except Exception as e:
        st.error(f"엑셀 파일 읽기 오류: {e}")
        return

    # 학습 UI 생성
    progress = st.progress(0)
    status = st.empty()
    
    # 상단 컨트롤 패널
    col1, col2 = st.columns([0.5, 0.5])  # 2개 컬럼으로 변경
    with col1:
        if st.button("⏸️ 일시정지", use_container_width=True, key="pause_btn"):
            st.warning("일시정지 중입니다. 계속하려면 '재개' 버튼을 누르세요.")
            if st.button("▶️ 재개", use_container_width=True, key="resume_btn"):
                st.rerun()
    with col2:
        if st.button("⏹️ 학습 종료", use_container_width=True, key="stop_btn"):
            st.session_state.page = 'settings'
            st.rerun()

    # 실시간 설정 변경 UI
    with st.expander("학습 설정", expanded=False):
        # 제일 윗줄에 자동 반복, 브레이크, 파이널 음성 재생 옵션 추가
        col1, col2, col3 = st.columns(3)
        with col1:
            settings['auto_repeat'] = st.checkbox("자동 반복 활성화",
                                                value=settings.get('auto_repeat', True),
                                                key="auto_repeat_learning")
            settings['repeat_count'] = st.number_input("자동 반복 회수",
                                                     value=settings.get('repeat_count', 5),
                                                     min_value=1,
                                                     max_value=100,
                                                     step=1,
                                                     key="repeat_count_learning",
                                                     disabled=not settings['auto_repeat'])
        with col2:
            settings['break_enabled'] = st.checkbox("브레이크 활성화",
                                                  value=settings.get('break_enabled', True),
                                                  key="break_enabled_learning")
            settings['break_interval'] = st.number_input("브레이크 회수",
                                                       value=settings.get('break_interval', 10),
                                                       min_value=1,
                                                       max_value=100,
                                                       step=1,
                                                       key="break_interval_learning",
                                                       disabled=not settings['break_enabled'])
        with col3:
            settings['final_sound_enabled'] = st.checkbox("학습 완료 음성 재생",
                                                        value=settings.get('final_sound_enabled', True),
                                                        key="final_sound_enabled_learning")
            settings['final_sound_duration'] = st.number_input("재생 시간 (초)",
                                                             value=settings.get('final_sound_duration', 30),
                                                             min_value=1,
                                                             max_value=300,
                                                             step=1,
                                                             key="final_sound_duration_learning",
                                                             disabled=not settings['final_sound_enabled'])

        # 배속 설정
        st.subheader("배속 설정")
        col1, col2, col3 = st.columns(3)
        with col1:
            settings['korean_speed'] = st.number_input("한글 배속",
                                                     value=settings['korean_speed'],
                                                     min_value=0.1,
                                                     step=0.1,
                                                     format="%.1f",
                                                     key="korean_speed_learning")
        with col2:
            settings['english_speed'] = st.number_input("영어 배속",
                                                      value=settings['english_speed'],
                                                      min_value=0.1,
                                                      step=0.1,
                                                      format="%.1f",
                                                      key="english_speed_learning")
        with col3:
            settings['chinese_speed'] = st.number_input("중국어 배속",
                                                      value=settings['chinese_speed'],
                                                      min_value=0.1,
                                                      step=0.1,
                                                      format="%.1f",
                                                      key="chinese_speed_learning")

        # 반복 설정
        st.subheader("반복 설정")
        col1, col2, col3 = st.columns(3)
        with col1:
            settings['first_repeat'] = st.number_input("1순위 반복",
                                                     value=settings['first_repeat'],
                                                     min_value=0,
                                                     step=1,
                                                     key="first_repeat_learning")
        with col2:
            settings['second_repeat'] = st.number_input("2순위 반복",
                                                      value=settings['second_repeat'],
                                                      min_value=0,
                                                      step=1,
                                                      key="second_repeat_learning")
        with col3:
            settings['third_repeat'] = st.number_input("3순위 반복",
                                                     value=settings['third_repeat'],
                                                     min_value=0,
                                                     step=1,
                                                     key="third_repeat_learning")

        # 음성 설정
        st.subheader("음성 설정")
        col1, col2, col3, col4 = st.columns(4)  # 4개의 컬럼으로 변경
        with col1:
            settings['kor_voice'] = st.selectbox("한글 음성",
                                               options=list(VOICE_MAPPING['korean'].keys()),
                                               index=list(VOICE_MAPPING['korean'].keys()).index(settings['kor_voice']),
                                               key="kor_voice_learning")
        with col2:
            settings['eng_voice'] = st.selectbox("영어 음성",
                                               options=list(VOICE_MAPPING['english'].keys()),
                                               index=list(VOICE_MAPPING['english'].keys()).index(settings['eng_voice']),
                                               key="eng_voice_learning")
        with col3:
            current_zh_voice = settings.get('zh_voice', 'Yunjian')
            try:
                zh_index = list(VOICE_MAPPING['chinese'].keys()).index(current_zh_voice)
            except ValueError:
                zh_index = list(VOICE_MAPPING['chinese'].keys()).index('Yunjian')  # 잘못된 값이면 기본값 사용
                settings['zh_voice'] = 'Yunjian'  # 설정값 업데이트

            settings['zh_voice'] = st.selectbox("중국어 음성",
                                             options=list(VOICE_MAPPING['chinese'].keys()),
                                             index=zh_index,
                                             key="zh_voice_learning")
        with col4:
            settings['jp_voice'] = st.selectbox("일본어 음성",
                                              options=list(VOICE_MAPPING['japanese'].keys()),
                                              index=list(VOICE_MAPPING['japanese'].keys()).index(settings.get('jp_voice', 'Nanami')),
                                              key="jp_voice_learning")

        # 폰트 설정
        st.subheader("폰트 설정")
        col1, col2, col3 = st.columns(3)
        with col1:
            settings['korean_font'] = st.selectbox("한글 폰트",
                                                 options=['Pretendard', '맑은 고딕', '나눔고딕', '굴림'],
                                                 index=['Pretendard', '맑은 고딕', '나눔고딕', '굴림'].index(settings['korean_font']),
                                                 key="korean_font_learning")
        with col2:
            settings['english_font'] = st.selectbox("영어 폰트",
                                                  options=['Pretendard', 'Arial', 'Times New Roman', 'Verdana'],
                                                  index=['Pretendard', 'Arial', 'Times New Roman', 'Verdana'].index(settings['english_font']),
                                                  key="english_font_learning")
        with col3:
            settings['chinese_font'] = st.selectbox("중국어 폰트",
                                                  options=['SimSun', 'Microsoft YaHei', 'SimHei'],
                                                  index=['SimSun', 'Microsoft YaHei', 'SimHei'].index(settings['chinese_font']),
                                                  key="chinese_font_learning")

    # 자막 표시를 위한 빈 컨테이너
    subtitles = [st.empty() for _ in range(3)]
    
    # 이전 문장 자막 저장용 변수
    prev_subtitles = {'second': None, 'third': None}

    while True:
        for i, (eng, kor, chn, jpn) in enumerate(zip(english, korean, chinese, japanese)):
            # 언어별 텍스트와 음성 매핑
            lang_mapping = {
                'korean': {'text': kor, 'voice': VOICE_MAPPING['korean'][settings['kor_voice']], 'speed': settings['korean_speed']},
                'english': {'text': eng, 'voice': VOICE_MAPPING['english'][settings['eng_voice']], 'speed': settings['english_speed']},
                'chinese': {'text': chn, 'voice': VOICE_MAPPING['chinese'][settings['zh_voice']], 'speed': settings['chinese_speed']},
                'japanese': {'text': jpn, 'voice': VOICE_MAPPING['japanese'][settings.get('jp_voice', 'Nanami')], 'speed': settings.get('japanese_speed', 2.0)}
            }

            progress.progress((i + 1) / total_sentences)
            
            # 진행 상태와 배속 정보 표시
            speed_info = []
            
            # 순위에 따라 실제 재생되는 음성의 배속만 표시
            for lang in [settings['first_lang'], settings['second_lang'], settings['third_lang']]:
                if lang == 'korean' and settings['first_repeat'] > 0:
                    ko_speed = settings['korean_speed']
                    ko_speed_text = str(int(ko_speed)) if ko_speed.is_integer() else f"{ko_speed:.1f}"
                    speed_info.append(f"한글 {ko_speed_text}배")
                elif lang == 'english' and settings['second_repeat'] > 0:
                    eng_speed = settings['english_speed']
                    eng_speed_text = str(int(eng_speed)) if eng_speed.is_integer() else f"{eng_speed:.1f}"
                    speed_info.append(f"영어 {eng_speed_text}배")
                elif lang == 'chinese' and settings['third_repeat'] > 0:
                    zh_speed = settings['chinese_speed']
                    zh_speed_text = str(int(zh_speed)) if zh_speed.is_integer() else f"{zh_speed:.1f}"
                    speed_info.append(f"중국어 {zh_speed_text}배")
            
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
                f'<span style="color: red">{sentence_number_display}</span> | '
                f'<span style="color: #00FF00">{i+1}/{total_sentences}</span> | '
                f'<span style="color: #00FF00">{speed_display}</span> | '
                f'<span style="color: red">학습: {int((current_time - st.session_state.start_time) / 60):02d}분</span> | '
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
                </style>
            """, unsafe_allow_html=True)

            # 순위별 자막 표시
            for rank, (lang, repeat) in enumerate([
                (settings['first_lang'], settings['first_repeat']),
                (settings['second_lang'], settings['second_repeat']),
                (settings['third_lang'], settings['third_repeat'])
            ]):
                if not settings['hide_subtitles'][f'{["first", "second", "third"][rank]}_lang']:
                    text = lang_mapping[lang]['text']
                    font = settings[f'{lang}_font']
                    color = settings[f'{lang}_color']
                    size = settings[f'{lang}_font_size']
                    
                    subtitles[rank].markdown(
                        f'<div class="{lang}-text" style="font-family: {font}; '
                        f'color: {color}; font-size: {size}px;">{text}</div>',
                        unsafe_allow_html=True
                    )

            # 순위별 음성 재생
            for lang, repeat in [
                (settings['first_lang'], settings['first_repeat']),
                (settings['second_lang'], settings['second_repeat']),
                (settings['third_lang'], settings['third_repeat'])
            ]:
                for _ in range(repeat):
                    audio_file = await create_audio(
                        lang_mapping[lang]['text'],
                        lang_mapping[lang]['voice'],
                        lang_mapping[lang]['speed']
                    )
                    if audio_file:
                        play_audio(audio_file)
                        if _ < repeat - 1:  # 마지막 반복이 아닌 경우에만 대기
                            await asyncio.sleep(settings['spacing'])

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
                    break_msg = "쉬는 시간입니다, 5초간의 휴식을 느껴보세요"
                    break_audio = await create_audio(break_msg, VOICE_MAPPING['korean']['선희'], 1.0)
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
                    break
                
        except Exception as e:
            st.error(f"완료 알림음 재생 오류: {e}")
            traceback.print_exc()

def create_personalized_ui():
    """개인별 맞춤 UI 생성"""
    st.title("개인별 설정 기억하기")

    # 언어 선택
    selected_language = st.selectbox(
        "사용할 언어를 선택하세요",
        options=['korean', 'english', 'chinese', 'japanese'],
        index=['korean', 'english', 'chinese', 'japanese'].index(st.session_state.user_language)
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

def main():
    # 세션 상태 초기화
    initialize_session_state()
    
    # 페이지 라우팅
    if 'page' not in st.session_state:
        st.session_state.page = 'settings'
    
    if st.session_state.page == 'settings':
        create_settings_ui()
    elif st.session_state.page == 'learning':
        # 학습 중에도 설정 UI 표시
        st.markdown(
            '<h1 style="font-size: 1.5rem; color: #00FF00;">도파민 대충영어 : 2배 한국어</h1>',
            unsafe_allow_html=True
        )
        # 학습 시작
        asyncio.run(start_learning())
    elif st.session_state.page == 'personalized':
        # 개인별 맞춤 UI 생성
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

if __name__ == "__main__":
    main()