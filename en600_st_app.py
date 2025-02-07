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
from playsound import playsound
import base64

## streamlit run word_memory/en600_st_app.py

# 기본 경로 설정
SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_PATH = SCRIPT_DIR / 'settings.json'
EXCEL_PATH = SCRIPT_DIR / 'en600new.xlsx'

# 음성 매핑 설정
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
        "윈시": "zh-CN-YunxiNeural"
    }
}

# 언어 설정
LANGUAGES = ['english', 'korean', 'chinese', 'none']
LANG_DISPLAY = {'english': 'EN', 'korean': 'KO', 'chinese': 'CH', 'none': '없음'}

def initialize_session_state():
    """세션 상태 초기화"""
    if 'settings' not in st.session_state:
        # 저장된 설정 파일이 있으면 로드
        try:
            if SETTINGS_PATH.exists():
                with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                    st.session_state.settings = saved_settings
                    return
        except Exception as e:
            st.error(f"설정 파일 로드 중 오류: {e}")
        
        # 저장된 설정이 없으면 기본값 사용
        st.session_state.settings = {
            'first_lang': 'korean',
            'second_lang': 'english',
            'third_lang': 'chinese',
            'first_repeat': 1,
            'second_repeat': 1,
            'third_repeat': 0,
            'kor_voice': '선희',
            'eng_voice': 'Steffan',
            'zh_voice': '샤오샤오',
            'start_row': 1,
            'end_row': 10,
            'word_delay': 0.1,
            'spacing': 0.5,
            'english_speed': 2.0,
            'korean_speed': 2.0,
            'chinese_speed': 2.0,
            'subtitle_delay': 0.5,
            'keep_subtitles': True,
            'break_enabled': True,
            'break_interval': 20,
            'break_duration': 5,
            'next_sentence_time': 0.5,
            'english_font': 'Arial',
            'korean_font': '맑은 고딕',
            'chinese_font': 'SimSun',
            'english_color': '#FFFF00',
            'korean_color': '#FFFFFF',
            'chinese_color': '#00FF00',
            'english_font_size': 32,
            'korean_font_size': 32,
            'chinese_font_size': 32,
            'hide_subtitles': {
                'first_lang': False,
                'second_lang': False,
                'third_lang': False
            },
        }

    # break.wav 파일 존재 여부 확인
    break_sound_path = SCRIPT_DIR / 'break.wav'
    if not break_sound_path.exists():
        st.warning("브레이크 알림음 파일이 없습니다. 기본 알림음을 생성합니다.")
        try:
            # 기본 알림음 생성 (북소리)
            communicate = edge_tts.Communicate("띵", "ko-KR-SunHiNeural")
            asyncio.run(communicate.save(str(break_sound_path)))
        except Exception as e:
            st.error(f"알림음 생성 오류: {e}")

def create_settings_ui():
    # 엑셀 파일에서 최대 행 수 확인
    try:
        df = pd.read_excel(EXCEL_PATH, header=None)
        max_row = len(df)
    except Exception as e:
        st.error(f"엑셀 파일 읽기 오류: {e}")
        max_row = 1  # 기본값 설정
        
    # 기본 폰트 크기 설정
    size = 24  # 기본 폰트 크기
    title_size = 32  # 제목 크기
    subtitle_size = 24  # 부제목 크기

    # CSS 스타일 업데이트
    st.markdown(f"""
        <style>
            /* 모든 UI 요소의 기본 폰트 크기 통일 */
            .stMarkdown, .stText, div, label, input, button, select, .stSelectbox, 
            div[data-baseweb="select"] span, .stNumberInput input {{
                font-size: {size}px !important;
            }}
            
            /* 제목 크기 조정 */
            .stTitle h1 {{
                font-size: {title_size}px !important;
            }}
            
            /* 부제목 크기 조정 */
            .stSubheader h2 {{
                font-size: {subtitle_size}px !important;
            }}
            
            /* 모든 입력 필드와 레이블 크기 증가 */
            .stNumberInput label, 
            .stSelectbox label, 
            .stCheckbox label,
            .stNumberInput input,
            .stSelectbox > div,
            .stCheckbox span p {{
                font-size: {size}px !important;
                line-height: 1.5 !important;
            }}
            
            /* 콤보박스 드롭다운 메뉴 */
            [data-baseweb="popover"] * {{
                font-size: {size}px !important;
            }}
            
            /* 버튼 텍스트 */
            .stButton > button {{
                font-size: {size}px !important;
                padding: 0.5rem 1rem !important;
            }}
            
            /* 일반 텍스트 */
            .stMarkdown p,
            .stText p,
            div[data-testid="stText"] p {{
                font-size: {size}px !important;
            }}
            
            /* 상태 메시지 */
            .stAlert p {{
                font-size: {size}px !important;
            }}
            
            /* 체크박스 텍스트 */
            .stCheckbox label span {{
                font-size: {size}px !important;
            }}
            
            /* 숫자 입력 필드 너비 조정 */
            .stNumberInput {{
                min-width: 150px !important;
            }}
            
            /* 콤보박스 스타일 수정 */
            div[data-baseweb="select"] {{
                min-height: 40px !important;
                line-height: 40px !important;
            }}
            
            /* 콤보박스 내부 텍스트 정렬 */
            div[data-baseweb="select"] > div {{
                min-height: 40px !important;
                padding: 5px 0 !important;
                display: flex !important;
                align-items: center !important;
            }}
            
            /* 드롭다운 메뉴 아이템 높이 */
            div[role="listbox"] [role="option"] {{
                min-height: 40px !important;
                line-height: 40px !important;
                padding: 5px 12px !important;
            }}
        </style>
    """, unsafe_allow_html=True)

    # 제목을 최상단에 배치
    st.title("도파민 대충영어")
    
    # 시작/종료 번호와 학습 시작 버튼을 제목 바로 아래에 배치
    col1, col2, col3 = st.columns([0.3, 0.3, 0.4])
    with col1:
        start_row = st.number_input("시작번호",
                                  value=st.session_state.settings['start_row'],
                                  min_value=1,
                                  max_value=max_row,
                                  key="start_row",
                                  format="%d")
    with col2:
        end_row = st.number_input("종료번호",
                                value=st.session_state.settings['end_row'],
                                min_value=1,
                                max_value=max_row,
                                key="end_row",
                                format="%d")
    with col3:
        st.markdown("""
        <style>
            div[data-testid="column"]:nth-child(3) button {{
                margin-top: 20px;  /* 기존 margin-top에서 10px 추가 */
                width: 50% !important;  /* 너비를 반으로 축소 */
            }}
        </style>
        """, unsafe_allow_html=True)
        if st.button("학습 시작", use_container_width=True):
            # 최종 유효성 검사
            error_messages = []
            
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
                st.session_state.settings.update({
                    'start_row': start_row,
                    'end_row': end_row
                })
                st.session_state.page = 'learning'
                st.rerun()

    # 빈 공간 추가
    st.markdown("<div style='height: 1em'></div>", unsafe_allow_html=True)

    # 1순위 설정
    col1, col2, col3 = st.columns(3)  # 동일한 너비로 설정
    with col1:
        first_lang = st.selectbox("1순위",
                                options=[LANG_DISPLAY[l] for l in LANGUAGES],
                                index=LANGUAGES.index(st.session_state.settings['first_lang']),
                                key="first_lang")
    with col2:
        first_repeat = st.number_input("반복",
                                     value=st.session_state.settings['first_repeat'],
                                     min_value=0,
                                     key="first_repeat",
                                     format="%d")
    with col3:
        speed_key = f"{st.session_state.settings['first_lang']}_speed"
        first_speed = st.number_input("배속",
                                    value=st.session_state.settings[speed_key],
                                    min_value=0.1,
                                    step=0.1,
                                    format="%.1f",
                                    key="first_speed")
        st.session_state.settings[speed_key] = first_speed

    # 2순위 설정
    col1, col2, col3 = st.columns(3)
    with col1:
        second_lang = st.selectbox("2순위",
                                 options=[LANG_DISPLAY[l] for l in LANGUAGES],
                                 index=LANGUAGES.index(st.session_state.settings['second_lang']),
                                 key="second_lang")
    with col2:
        second_repeat = st.number_input("반복 ",
                                      value=st.session_state.settings['second_repeat'],
                                      min_value=0,
                                      key="second_repeat",
                                      format="%d")
    with col3:
        speed_key = f"{st.session_state.settings['second_lang']}_speed"
        second_speed = st.number_input("배속 ",
                                     value=st.session_state.settings[speed_key],
                                     min_value=0.1,
                                     step=0.1,
                                     format="%.1f",
                                     key="second_speed")
        st.session_state.settings[speed_key] = second_speed

    # 3순위 설정
    col1, col2, col3 = st.columns(3)
    with col1:
        third_lang = st.selectbox("3순위",
                                options=[LANG_DISPLAY[l] for l in LANGUAGES],
                                index=LANGUAGES.index(st.session_state.settings['third_lang']),
                                key="third_lang")
    with col2:
        third_repeat = st.number_input("반복  ",
                                     value=st.session_state.settings['third_repeat'],
                                     min_value=0,
                                     key="third_repeat",
                                     format="%d")
    with col3:
        speed_key = f"{st.session_state.settings['third_lang']}_speed"
        third_speed = st.number_input("배속  ",
                                    value=st.session_state.settings[speed_key],
                                    min_value=0.1,
                                    step=0.1,
                                    format="%.1f",
                                    key="third_speed")
        st.session_state.settings[speed_key] = third_speed

    # 빈 공간 추가
    st.markdown("<div style='height: 1em'></div>", unsafe_allow_html=True)

    # 자막 숨김 옵션을 한 줄로 배치
    col1, col2, col3 = st.columns(3)
    with col1:
        hide_first = st.checkbox("1순위 자막 숨김",
                               value=st.session_state.settings['hide_subtitles']['first_lang'],
                               key="first_hide")
    with col2:
        hide_second = st.checkbox("2순위 자막 숨김",
                                value=st.session_state.settings['hide_subtitles']['second_lang'],
                                key="second_hide")
    with col3:
        hide_third = st.checkbox("3순위 자막 숨김",
                               value=st.session_state.settings['hide_subtitles']['third_lang'],
                               key="third_hide")

    # 빈 공간 추가
    st.markdown("<div style='height: 1em'></div>", unsafe_allow_html=True)

    # 음성 설정
    st.subheader("음성 설정")
    
    # 음성 선택기를 가로 한 줄로 배치
    col1, col2, col3 = st.columns(3)
    with col1:
        eng_voice = st.selectbox("EN 음성",
                               options=list(VOICE_MAPPING['english'].keys()),
                               index=list(VOICE_MAPPING['english'].keys()).index(st.session_state.settings['eng_voice']),
                               key="eng_voice")
    with col2:
        kor_voice = st.selectbox("KO 음성",
                               options=list(VOICE_MAPPING['korean'].keys()),
                               index=list(VOICE_MAPPING['korean'].keys()).index(st.session_state.settings['kor_voice']),
                               key="kor_voice")
    with col3:
        zh_voice = st.selectbox("CH 음성",
                              options=list(VOICE_MAPPING['chinese'].keys()),
                              index=list(VOICE_MAPPING['chinese'].keys()).index(st.session_state.settings['zh_voice']),
                              key="zh_voice")

    # 재생 설정
    st.subheader("재생 설정")
    
    # 4개의 입력창을 한 줄로 배치 (순서 변경)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        spacing = st.number_input("문장 간격(초)",
                                value=st.session_state.settings['spacing'],
                                min_value=0.1,
                                step=0.1,
                                format="%.1f",
                                key="spacing")
    with col2:
        subtitle_delay = st.number_input("자막 딜레이(초)",
                                       value=st.session_state.settings['subtitle_delay'],
                                       min_value=0.1,
                                       step=0.1,
                                       format="%.1f",
                                       key="subtitle_delay")
    with col3:
        next_sentence_time = st.number_input("다음 문장(초)",
                                           value=st.session_state.settings['next_sentence_time'],
                                           min_value=0.1,
                                           step=0.1,
                                           format="%.1f",
                                           key="next_sentence_time")
    with col4:
        break_interval = st.number_input("브레이크(문장)",
                                       value=st.session_state.settings['break_interval'],
                                       min_value=1,
                                       step=1,
                                       key="break_interval")

    # 자막 및 브레이크 설정
    col1, col2 = st.columns(2)
    with col1:
        keep_subtitles = st.checkbox("자막 유지",
                                   value=st.session_state.settings['keep_subtitles'],
                                   key="keep_subtitles")
    with col2:
        break_enabled = st.checkbox("🔄 브레이크",
                                  value=st.session_state.settings['break_enabled'],
                                  key="break_enabled")

    # 설정값 업데이트
    st.session_state.settings['hide_subtitles'] = {
        'first_lang': hide_first,
        'second_lang': hide_second,
        'third_lang': hide_third
    }

    # 폰트 및 색상 설정 섹션
    st.subheader("폰트 및 색상 설정")
    
    # 영어 폰트/색상/크기 설정
    col1, col2, col3 = st.columns(3)
    with col1:
        eng_font = st.selectbox("영어 폰트",
                              options=['Arial', 'Times New Roman', 'Verdana'],
                              index=['Arial', 'Times New Roman', 'Verdana'].index(st.session_state.settings.get('english_font', 'Arial')),
                              key="eng_font")
    with col2:
        eng_color = st.color_picker("영어 색상",
                                  value=st.session_state.settings.get('english_color', '#000000'),
                                  key="eng_color")
    with col3:
        eng_size = st.number_input("영어 폰트 크기",
                                 min_value=12,
                                 max_value=72,
                                 value=st.session_state.settings.get('english_font_size', 32),
                                 step=2,
                                 key="eng_font_size")
    
    # 한국어 폰트/색상/크기 설정
    col1, col2, col3 = st.columns(3)
    with col1:
        kor_font = st.selectbox("한국어 폰트",
                              options=['맑은 고딕', '나눔고딕', '굴림'],
                              index=['맑은 고딕', '나눔고딕', '굴림'].index(st.session_state.settings.get('korean_font', '맑은 고딕')),
                              key="kor_font")
    with col2:
        kor_color = st.color_picker("한국어 색상",
                                  value=st.session_state.settings.get('korean_color', '#0000FF'),
                                  key="kor_color")
    with col3:
        kor_size = st.number_input("한국어 폰트 크기",
                                 min_value=12,
                                 max_value=72,
                                 value=st.session_state.settings.get('korean_font_size', 32),
                                 step=2,
                                 key="kor_font_size")
    
    # 중국어 폰트/색상/크기 설정
    col1, col2, col3 = st.columns(3)
    with col1:
        zh_font = st.selectbox("중국어 폰트",
                             options=['SimSun', 'Microsoft YaHei', 'SimHei'],
                             index=['SimSun', 'Microsoft YaHei', 'SimHei'].index(st.session_state.settings.get('chinese_font', 'SimSun')),
                             key="zh_font")
    with col2:
        zh_color = st.color_picker("중국어 색상",
                                 value=st.session_state.settings.get('chinese_color', '#FF0000'),
                                 key="zh_color")
    with col3:
        zh_size = st.number_input("중국어 폰트 크기",
                                min_value=12,
                                max_value=72,
                                value=st.session_state.settings.get('chinese_font_size', 32),
                                step=2,
                                key="zh_font_size")

    # 폰트 크기 변경 시 즉시 반영을 위한 CSS 업데이트
    st.markdown(f"""
        <style>
            .english-text {{
                font-size: {eng_size}px !important;
            }}
            .korean-text {{
                font-size: {kor_size}px !important;
            }}
            .chinese-text {{
                font-size: {zh_size}px !important;
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

    # 설정값 업데이트 - 모든 설정값을 한 번에 업데이트
    st.session_state.settings.update({
        'first_lang': [k for k, v in LANG_DISPLAY.items() if v == first_lang][0],
        'second_lang': [k for k, v in LANG_DISPLAY.items() if v == second_lang][0],
        'third_lang': [k for k, v in LANG_DISPLAY.items() if v == third_lang][0],
        'first_repeat': first_repeat,
        'second_repeat': second_repeat,
        'third_repeat': third_repeat,
        'eng_voice': eng_voice,
        'kor_voice': kor_voice,
        'zh_voice': zh_voice,
        'spacing': spacing,
        'subtitle_delay': subtitle_delay,
        'keep_subtitles': keep_subtitles,
        'break_enabled': break_enabled,
        'hide_subtitles': {
            'first_lang': hide_first,
            'second_lang': hide_second,
            'third_lang': hide_third
        },
        'english_font': eng_font,
        'korean_font': kor_font,
        'chinese_font': zh_font,
        'english_color': eng_color,
        'korean_color': kor_color,
        'chinese_color': zh_color,
        'english_font_size': eng_size,
        'korean_font_size': kor_size,
        'chinese_font_size': zh_size,
    })

    # 설정값을 파일에 저장
    try:
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(st.session_state.settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"설정 저장 중 오류: {e}")

def play_audio(file_path):
    """음성 파일 재생"""
    try:
        if not os.path.exists(file_path):
            st.error(f"파일이 존재하지 않음: {file_path}")
            return
            
        # 오디오 파일을 base64로 인코딩
        with open(file_path, 'rb') as f:
            audio_bytes = f.read()
        
        # WAV 파일 길이 계산
        data, samplerate = sf.read(file_path)
        duration = len(data) / samplerate
            
        audio_base64 = base64.b64encode(audio_bytes).decode()
        
        # JavaScript로 자동 재생
        st.markdown(f"""
            <audio autoplay style="display: none">
                <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
            </audio>
        """, unsafe_allow_html=True)
        
        # 오디오 재생이 끝날 때까지 대기
        time.sleep(duration)
            
    except Exception as e:
        st.error(f"음성 재생 중 오류: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

def play_break_sound():
    """브레이크 알림음 재생"""
    try:
        break_sound_path = SCRIPT_DIR / 'break.wav'
        if break_sound_path.exists():
            with open(break_sound_path, 'rb') as f:
                audio_bytes = f.read()
            audio_base64 = base64.b64encode(audio_bytes).decode()
            st.markdown(f"""
                <audio autoplay style="display: none">
                    <source src="data:audio/wav;base64,{audio_base64}" type="audio/wav">
                </audio>
            """, unsafe_allow_html=True)
        else:
            st.warning("브레이크 알림음 파일이 없습니다: break.wav")
    except Exception as e:
        st.error(f"알림음 재생 오류: {e}")

async def create_audio(text, voice, speed=1.0):
    """음성 파일 생성"""
    try:
        output_file = f"temp_{int(time.time()*1000)}.wav"
        
        # 배속 계산 수정
        if speed > 1:
            rate_str = f"+{int((speed - 1) * 100)}%"
        else:
            rate_str = f"-{int((1 - speed) * 100)}%"
            
        communicate = edge_tts.Communicate(text, voice, rate=rate_str)
        await communicate.save(output_file)
        return output_file
    except Exception as e:
        st.error(f"음성 생성 오류: {e}")
        return None

def create_learning_ui():
    """학습 화면 UI 생성"""
    st.markdown(f"""
        <style>
            /* 재생설정 콤보박스 너비 축소 */
            div[data-testid="column"] .stNumberInput {{
                max-width: 120px !important;
            }}
            
            /* 자막 텍스트 스타일 */
            .english-text {{
                font-family: {st.session_state.settings['english_font']} !important;
                color: {st.session_state.settings['english_color']} !important;
                font-size: 32px !important;
                font-weight: bold !important;
            }}
            .korean-text {{
                font-family: {st.session_state.settings['korean_font']} !important;
                color: {st.session_state.settings['korean_color']} !important;
                font-size: 32px !important;
                font-weight: bold !important;
            }}
            .chinese-text {{
                font-family: {st.session_state.settings['chinese_font']} !important;
                color: {st.session_state.settings['chinese_color']} !important;
                font-size: 32px !important;
                font-weight: bold !important;
            }}
            
            /* 진행 상태 텍스트 스타일 */
            .stProgress > div > div > div > div {{
                font-size: 24px !important;
            }}
            
            /* 상태 메시지 텍스트 스타일 */
            div[data-testid="stText"] {{
                font-size: 24px !important;
            }}
        </style>
    """, unsafe_allow_html=True)
    
    # "학습 진행" 제목 제거
    
    # 진행 상황 표시
    progress = st.progress(0)
    status = st.empty()
    subtitles = [st.empty() for _ in range(3)]
    return progress, status, subtitles

async def start_learning():
    """학습 시작"""
    settings = st.session_state.settings
    
    # 엑셀에서 문장 가져오기
    try:
        df = pd.read_excel(EXCEL_PATH, header=None)
        start_idx = settings['start_row'] - 1
        end_idx = settings['end_row'] - 1
        selected_data = df.iloc[start_idx:end_idx+1, :3]
        
        english = selected_data.iloc[:, 0].tolist()
        korean = selected_data.iloc[:, 1].tolist()
        chinese = selected_data.iloc[:, 2].tolist()
        
    except Exception as e:
        st.error(f"엑셀 파일 읽기 오류: {e}")
        return
    
    # 학습 UI 생성
    progress, status, subtitles = create_learning_ui()
    
    # 상단 컨트롤 패널
    col1, col2, col3, col4 = st.columns([0.25, 0.25, 0.25, 0.25])
    with col1:
        if st.button("일시정지", use_container_width=True):
            st.warning("일시정지 중입니다. 계속하려면 '재개' 버튼을 누르세요.")
            if st.button("재개", use_container_width=True):
                st.rerun()
    with col2:
        if st.button("학습 종료", use_container_width=True):
            st.session_state.page = 'settings'
            st.rerun()
    with col3:
        auto_repeat = st.checkbox("자동 반복", value=True, key="auto_repeat")
    with col4:
        # 실시간 자막 토글 버튼
        hide_all = st.checkbox("전체 자막 숨기기", value=False, key="hide_all")
    
    # 언어별 음성 설정
    voice_settings = {
        'english': {'voice': VOICE_MAPPING['english'][settings['eng_voice']], 'speed': settings['english_speed']},
        'korean': {'voice': VOICE_MAPPING['korean'][settings['kor_voice']], 'speed': settings['korean_speed']},
        'chinese': {'voice': VOICE_MAPPING['chinese'][settings['zh_voice']], 'speed': settings['chinese_speed']}
    }
    
    # 학습 진행
    total_sentences = len(english)
    sentence_count = 0  # 문장 카운터 초기화
    
    while True:  # 자동 반복을 위한 무한 루프
        for i, (eng, kor, chn) in enumerate(zip(english, korean, chinese)):
            # 브레이크 체크 및 실행
            if settings['break_enabled'] and sentence_count > 0 and sentence_count % settings['break_interval'] == 0:
                status.warning(f"🔄 {settings['break_interval']}문장 완료! {settings['break_duration']}초간 휴식...")
                play_break_sound()  # 브레이크 알림음 재생
                time.sleep(settings['break_duration'])  # 설정된 시간만큼 휴식
                status.empty()
            
            # 진행률 업데이트
            progress.progress((i + 1) / total_sentences)
            status.text(f"학습 진행중... {i+1}/{total_sentences}")
            
            # 자막과 음성 처리
            texts = {'english': eng, 'korean': kor, 'chinese': chn}
            langs = [settings['first_lang'], settings['second_lang'], settings['third_lang']]
            repeats = [settings['first_repeat'], settings['second_repeat'], settings['third_repeat']]
            
            # 각 언어별 처리
            for j, (lang, repeat) in enumerate(zip(langs, repeats)):
                if lang != 'none':  # 언어가 선택된 경우
                    # 자막 표시 여부 결정
                    hide = settings['hide_subtitles'][f'{["first", "second", "third"][j]}_lang'] or hide_all
                    
                    # 자막 표시
                    if not hide:
                        subtitles[j].markdown(
                            f'<div class="{lang}-text" style="color: {settings[f"{lang}_color"]} !important;">{texts[lang]}</div>', 
                            unsafe_allow_html=True
                        )
                    elif not settings['keep_subtitles']:  # 자막 유지가 꺼져있을 때만 자막 지우기
                        subtitles[j].empty()
                    
                    # 음성 재생 (반복 횟수만큼)
                    if repeat > 0:
                        for _ in range(repeat):
                            audio_file = await create_audio(
                                texts[lang], 
                                voice_settings[lang]['voice'],
                                voice_settings[lang]['speed']
                            )
                            if audio_file:
                                play_audio(audio_file)
                                time.sleep(0.1)
                
                if not settings['keep_subtitles']:  # 자막 유지가 꺼져있을 때만 딜레이 적용
                    time.sleep(settings['subtitle_delay'])
            
            # 문장 카운터 증가
            sentence_count += 1
            
            # 문장 간 간격
            if i < total_sentences - 1:
                time.sleep(settings['spacing'])
        
        # 자동 반복이 꺼져 있으면 루프 종료
        if not auto_repeat:
            break
    
    st.success("학습이 완료되었습니다!")
    st.session_state.page = 'settings'
    st.rerun()

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
        col1, col2 = st.columns([0.7, 0.3])
        with col1:
            st.title("대충영어")
        with col2:
            if st.button("학습 중단", use_container_width=True):
                st.session_state.page = 'settings'
                st.rerun()
        
        asyncio.run(start_learning())
        # 학습이 끝나면 설정 페이지로 돌아가기
        st.session_state.page = 'settings'

if __name__ == "__main__":
    main()
