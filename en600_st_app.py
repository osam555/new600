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
SETTINGS_PATH = SCRIPT_DIR / '/base/en600s-settings.json'
EXCEL_PATH = SCRIPT_DIR / 'base/en600new.xlsx'
TEMP_DIR = SCRIPT_DIR / 'temp'  # 임시 파일 저장 경로 추가

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
        "윈시": "zh-CN-YunxiNeural",
        "Yunjian": "zh-CN-YunjianNeural",
        "Yunyang": "zh-CN-YunyangNeural"
    }
}

# 언어 설정
LANGUAGES = ['english', 'korean', 'chinese', 'none']
LANG_DISPLAY = {'english': 'EN', 'korean': 'KO', 'chinese': 'CH', 'none': '없음'}

def initialize_session_state():
    """세션 상태 초기화"""
    # temp 폴더가 없으면 생성
    if not TEMP_DIR.exists():
        TEMP_DIR.mkdir(parents=True)
    
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
            'first_repeat': 0,
            'second_repeat': 1,
            'third_repeat': 1,
            'kor_voice': '선희',
            'eng_voice': 'Steffan',
            'zh_voice': 'Yunjian',
            'start_row': 301,
            'end_row': 350,
            'word_delay': 0.5,
            'spacing': 0.5,
            'english_speed': 3.0,
            'korean_speed': 2.0,
            'chinese_speed': 2.0,
            'subtitle_delay': 0.5,
            'keep_subtitles': True,
            'break_enabled': True,
            'break_interval': 10,
            'break_duration': 5,
            'next_sentence_time': 0.5,
            'english_font': 'Pretendard',
            'korean_font': 'Pretendard',
            'chinese_font': 'SimSun',
            'english_color': '#00FF00',
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
            'auto_repeat': True,
            'auto_repeat_count': 5,  # 자동 반복 횟수 추가
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
    # CSS 스타일 추가
    st.markdown("""
        <style>
            /* 제목 (h1) 폰트 크기 조정 */
            .st-emotion-cache-10trblm {
                font-size: 1.5rem !important;
                margin-bottom: 0px !important;
            }
            
            /* 부제목 (h2) 폰트 크기 조정 */
            .st-emotion-cache-1629p8f h2 {
                font-size: 1.2rem !important;
                margin-top: 1rem !important;
                margin-bottom: 0.5rem !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    settings = st.session_state.settings
    col1, col2 = st.columns([0.7, 0.3])
    with col1:
        st.title("대충영어")
    with col2:
        # 엑셀 파일에서 최대 행 수 가져오기
        try:
            df = pd.read_excel(EXCEL_PATH, header=None)
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

    # 시작/종료 번호 입력창을 제목 바로 아래로 이동
    col1, col2 = st.columns(2)
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

    # 언어 순서 설정
    st.subheader("언어 순서")
    col1, col2, col3 = st.columns(3)
    with col1:
        settings['first_lang'] = st.selectbox("1순위 언어",
            options=['korean', 'english', 'chinese'],
            index=['korean', 'english', 'chinese'].index(settings['first_lang']),
            format_func=lambda x: LANG_DISPLAY[x],
            key="settings_first_lang")
        first_repeat = st.number_input("반복",
                                     value=settings['first_repeat'],
                                     min_value=0,
                                     key="first_repeat",
                                     format="%d")
        speed_key = f"{settings['first_lang']}_speed"
        first_speed = st.number_input("배속",
                                    value=settings[speed_key],
                                    min_value=0.1,
                                    step=0.1,
                                    format="%.1f",
                                    key="first_speed")
        settings[speed_key] = first_speed

    with col2:
        settings['second_lang'] = st.selectbox("2순위 언어",
            options=['korean', 'english', 'chinese'],
            index=['korean', 'english', 'chinese'].index(settings['second_lang']),
            format_func=lambda x: LANG_DISPLAY[x],
            key="settings_second_lang")
        second_repeat = st.number_input("반복",
                                      value=settings['second_repeat'],
                                      min_value=0,
                                      key="second_repeat",
                                      format="%d")
        speed_key = f"{settings['second_lang']}_speed"
        second_speed = st.number_input("배속",
                                     value=settings[speed_key],
                                     min_value=0.1,
                                     step=0.1,
                                     format="%.1f",
                                     key="second_speed")
        settings[speed_key] = second_speed

    with col3:
        settings['third_lang'] = st.selectbox("3순위 언어",
            options=['korean', 'english', 'chinese'],
            index=['korean', 'english', 'chinese'].index(settings['third_lang']),
            format_func=lambda x: LANG_DISPLAY[x],
            key="settings_third_lang")
        third_repeat = st.number_input("반복",
                                     value=settings['third_repeat'],
                                     min_value=0,
                                     key="third_repeat",
                                     format="%d")
        speed_key = f"{settings['third_lang']}_speed"
        third_speed = st.number_input("배속",
                                    value=settings[speed_key],
                                    min_value=0.1,
                                    step=0.1,
                                    format="%.1f",
                                    key="third_speed")
        settings[speed_key] = third_speed

    # 빈 공간 추가
    st.markdown("<div style='height: 1em'></div>", unsafe_allow_html=True)

    # 자막 숨김 옵션을 한 줄로 배치
    col1, col2, col3 = st.columns(3)
    with col1:
        hide_first = st.checkbox("1순위 자막 숨김",
                               value=settings['hide_subtitles']['first_lang'],
                               key="first_hide")
    with col2:
        hide_second = st.checkbox("2순위 자막 숨김",
                                value=settings['hide_subtitles']['second_lang'],
                                key="second_hide")
    with col3:
        hide_third = st.checkbox("3순위 자막 숨김",
                               value=settings['hide_subtitles']['third_lang'],
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
                               index=list(VOICE_MAPPING['english'].keys()).index(settings['eng_voice']),
                               key="eng_voice")
    with col2:
        kor_voice = st.selectbox("KO 음성",
                               options=list(VOICE_MAPPING['korean'].keys()),
                               index=list(VOICE_MAPPING['korean'].keys()).index(settings['kor_voice']),
                               key="kor_voice")
    with col3:
        zh_voice = st.selectbox("CH 음성",
                              options=list(VOICE_MAPPING['chinese'].keys()),
                              index=list(VOICE_MAPPING['chinese'].keys()).index(settings['zh_voice']),
                              key="zh_voice")

    # 재생 설정
    st.subheader("재생 설정")
    
    # 4개의 입력창을 한 줄로 배치 (순서 변경)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        spacing = st.number_input("문장 간격",
                                value=settings['spacing'],
                                min_value=0.1,
                                step=0.1,
                                format="%.1f",
                                key="spacing")
    with col2:
        subtitle_delay = st.number_input("자막 딜레이",
                                       value=settings['subtitle_delay'],
                                       min_value=0.1,
                                       step=0.1,
                                       format="%.1f",
                                       key="subtitle_delay")
    with col3:
        next_sentence_time = st.number_input("다음 문장",
                                           value=settings['next_sentence_time'],
                                           min_value=0.1,
                                           step=0.1,
                                           format="%.1f",
                                           key="next_sentence_time")
    with col4:
        break_interval = st.number_input("브레이크",
                                       value=settings['break_interval'],
                                       min_value=1,
                                       step=1,
                                       key="break_interval")

    # 자막 및 브레이크 설정
    col1, col2 = st.columns(2)
    with col1:
        keep_subtitles = st.checkbox("자막 유지",
                                   value=settings['keep_subtitles'],
                                   key="keep_subtitles")
    with col2:
        break_enabled = st.checkbox("🔄 브레이크",
                                  value=settings['break_enabled'],
                                  key="break_enabled")

    # 자동 반복 설정 추가
    col1, col2 = st.columns(2)
    with col1:
        settings['auto_repeat'] = st.checkbox("자동 반복", 
                                            value=settings.get('auto_repeat', True),
                                            key="auto_repeat_checkbox")
    with col2:
        settings['auto_repeat_count'] = st.number_input("반복 횟수",
                                                      value=settings.get('auto_repeat_count', 5),
                                                      min_value=1,
                                                      max_value=100,
                                                      key="auto_repeat_count_input")

    # 설정값 업데이트
    settings['hide_subtitles'] = {
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
                              options=['Pretendard', 'Arial', 'Times New Roman', 'Verdana'],
                              index=['Pretendard', 'Arial', 'Times New Roman', 'Verdana'].index(settings.get('english_font', 'Pretendard')),
                              key="eng_font")
    with col2:
        eng_color = st.color_picker("영어 색상",
                                  value=settings.get('english_color', '#000000'),
                                  key="eng_color")
    with col3:
        eng_size = st.number_input("영어 폰트",
                                 min_value=12,
                                 max_value=72,
                                 value=settings.get('english_font_size', 32),
                                 step=2,
                                 key="eng_font_size")
    
    # 한국어 폰트/색상/크기 설정
    col1, col2, col3 = st.columns(3)
    with col1:
        kor_font = st.selectbox("한글 폰트",
                              options=['Pretendard', '맑은 고딕', '나눔고딕', '굴림'],
                              index=['Pretendard', '맑은 고딕', '나눔고딕', '굴림'].index(settings.get('korean_font', 'Pretendard')),
                              key="kor_font")
    with col2:
        kor_color = st.color_picker("한글 색상",
                                  value=settings.get('korean_color', '#FFFFFF'),
                                  key="kor_color")
    with col3:
        kor_size = st.number_input("한글 폰트",
                                 min_value=12,
                                 max_value=72,
                                 value=settings.get('korean_font_size', 32),
                                 step=2,
                                 key="kor_font_size")
    
    # 중국어 폰트/색상/크기 설정
    col1, col2, col3 = st.columns(3)
    with col1:
        zh_font = st.selectbox("중문 폰트",
                             options=['SimSun', 'Microsoft YaHei', 'SimHei'],
                             index=['SimSun', 'Microsoft YaHei', 'SimHei'].index(settings.get('chinese_font', 'SimSun')),
                             key="zh_font")
    with col2:
        zh_color = st.color_picker("중문 색상",
                                 value=settings.get('chinese_color', '#FF0000'),
                                 key="zh_color")
    with col3:
        zh_size = st.number_input("중문 폰트",
                                min_value=12,
                                max_value=72,
                                value=settings.get('chinese_font_size', 32),
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
    settings.update({
        'first_lang': settings['first_lang'],
        'second_lang': settings['second_lang'],
        'third_lang': settings['third_lang'],
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

    # 설정값 업데이트
    settings.update({
        'start_row': settings['start_row'],
        'end_row': settings['end_row']
    })

    # Save settings
    save_settings(settings)

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
        # temp 폴더의 임시 파일만 삭제
        if os.path.exists(file_path) and TEMP_DIR in Path(file_path).parents:
            os.remove(file_path)

def play_break_sound():
    """브레이크 알림음 재생"""
    try:
        break_sound_path = SCRIPT_DIR / 'base/break.wav'
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
            st.warning("브레이크 알림음 파일이 없습니다: /base/break.wav")
    except Exception as e:
        st.error(f"알림음 재생 오류: {e}")

async def create_audio(text, voice, speed=1.0):
    """음성 파일 생성"""
    try:
        output_file = TEMP_DIR / f"temp_{int(time.time()*1000)}.wav"
        
        # 배속 계산 수정
        if speed > 1:
            rate_str = f"+{int((speed - 1) * 100)}%"
        else:
            rate_str = f"-{int((1 - speed) * 100)}%"
            
        communicate = edge_tts.Communicate(text, voice, rate=rate_str)
        await communicate.save(str(output_file))
        return str(output_file)
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
    repeat_count = 0  # 반복 횟수 카운터 추가
    
    # 엑셀에서 문장 가져오기
    try:
        df = pd.read_excel(EXCEL_PATH, header=None)
        start_idx = settings['start_row'] - 1
        end_idx = settings['end_row'] - 1
        selected_data = df.iloc[start_idx:end_idx+1, :3]
        
        english = selected_data.iloc[:, 0].tolist()
        korean = selected_data.iloc[:, 1].tolist()
        chinese = selected_data.iloc[:, 2].tolist()
        total_sentences = len(english)
        
    except Exception as e:
        st.error(f"엑셀 파일 읽기 오류: {e}")
        return

    # 학습 UI 생성
    progress = st.progress(0)
    status = st.empty()
    
    # 상단 컨트롤 패널
    col1, col2, col3, col4 = st.columns([0.25, 0.25, 0.25, 0.25])
    with col1:
        if st.button("일시정지", use_container_width=True, key="pause_btn"):
            st.warning("일시정지 중입니다. 계속하려면 '재개' 버튼을 누르세요.")
            if st.button("재개", use_container_width=True, key="resume_btn"):
                st.rerun()
    with col2:
        if st.button("학습 종료", use_container_width=True, key="stop_btn"):
            st.session_state.page = 'settings'
            st.rerun()
    with col3:
        auto_repeat = st.checkbox("자동 반복", value=settings.get('auto_repeat', True), key="auto_repeat_checkbox")
    with col4:
        hide_all = st.checkbox("전체 자막 숨기기", value=False, key="hide_all_checkbox")

    # 실시간 설정 변경 UI
    with st.expander("학습 설정 조정", expanded=False):
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
        col1, col2, col3 = st.columns(3)
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
            settings['zh_voice'] = st.selectbox("중국어 음성",
                                              options=list(VOICE_MAPPING['chinese'].keys()),
                                              index=list(VOICE_MAPPING['chinese'].keys()).index(settings['zh_voice']),
                                              key="zh_voice_learning")

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

        # 색상 설정
        st.subheader("색상 설정")
        col1, col2, col3 = st.columns(3)
        with col1:
            settings['korean_color'] = st.color_picker("한글 색상",
                                                     value=settings['korean_color'],
                                                     key="korean_color_learning")
        with col2:
            settings['english_color'] = st.color_picker("영어 색상",
                                                      value=settings['english_color'],
                                                      key="english_color_learning")
        with col3:
            settings['chinese_color'] = st.color_picker("중국어 색상",
                                                      value=settings['chinese_color'],
                                                      key="chinese_color_learning")

    # 자막 표시를 위한 빈 컨테이너
    subtitles = [st.empty() for _ in range(3)]

    while True:
        for i, (eng, kor, chn) in enumerate(zip(english, korean, chinese)):
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
            
            status.markdown(
                f'학습 진행중... {i+1}/{total_sentences} <span style="color: #00FF00"> | {speed_display}</span>',
                unsafe_allow_html=True
            )

            # 자막 표시
            if not hide_all:
                texts = {'english': eng, 'korean': kor, 'chinese': chn}
                colors = {
                    'english': settings['english_color'],
                    'korean': settings['korean_color'],
                    'chinese': settings['chinese_color']
                }
                fonts = {
                    'english': settings['english_font'],
                    'korean': settings['korean_font'],
                    'chinese': settings['chinese_font']
                }
                
                # 순위에 따라 자막 표시
                langs = [settings['first_lang'], settings['second_lang'], settings['third_lang']]
                for idx, lang in enumerate(langs):
                    # 해당 순위의 자막이 숨김 상태가 아닐 때만 표시
                    if not settings['hide_subtitles'][f"{['first', 'second', 'third'][idx]}_lang"]:
                        subtitles[idx].markdown(
                            f'<p style="font-family: {fonts[lang]}; color: {colors[lang]}; font-size: {settings[f"{lang}_font_size"]}px;">{texts[lang]}</p>',
                            unsafe_allow_html=True
                        )
                    else:
                        # 자막이 숨김 상태일 때는 빈 공간 표시
                        subtitles[idx].markdown("<p>&nbsp;</p>", unsafe_allow_html=True)

            # 음성 재생
            try:
                # 첫 번째 언어
                first_lang = settings['first_lang']
                if settings['first_repeat'] > 0:  # 반복 횟수가 0보다 클 때만 재생
                    if first_lang == 'korean':
                        audio_file = await create_audio(kor, VOICE_MAPPING['korean'][settings['kor_voice']], settings['korean_speed'])
                        play_audio(audio_file)
                        await asyncio.sleep(settings['spacing'])
                    elif first_lang == 'english':
                        audio_file = await create_audio(eng, VOICE_MAPPING['english'][settings['eng_voice']], settings['english_speed'])
                        play_audio(audio_file)
                        await asyncio.sleep(settings['spacing'])
                    elif first_lang == 'chinese':
                        audio_file = await create_audio(chn, VOICE_MAPPING['chinese'][settings['zh_voice']], settings['chinese_speed'])
                        play_audio(audio_file)
                        await asyncio.sleep(settings['spacing'])

                # 두 번째 언어
                second_lang = settings['second_lang']
                if settings['second_repeat'] > 0:  # 반복 횟수가 0보다 클 때만 재생
                    if second_lang == 'korean':
                        audio_file = await create_audio(kor, VOICE_MAPPING['korean'][settings['kor_voice']], settings['korean_speed'])
                        play_audio(audio_file)
                        await asyncio.sleep(settings['spacing'])
                    elif second_lang == 'english':
                        audio_file = await create_audio(eng, VOICE_MAPPING['english'][settings['eng_voice']], settings['english_speed'])
                        play_audio(audio_file)
                        await asyncio.sleep(settings['spacing'])
                    elif second_lang == 'chinese':
                        audio_file = await create_audio(chn, VOICE_MAPPING['chinese'][settings['zh_voice']], settings['chinese_speed'])
                        play_audio(audio_file)
                        await asyncio.sleep(settings['spacing'])

                # 세 번째 언어
                third_lang = settings['third_lang']
                if settings['third_repeat'] > 0:  # 반복 횟수가 0보다 클 때만 재생
                    if third_lang == 'korean':
                        audio_file = await create_audio(kor, VOICE_MAPPING['korean'][settings['kor_voice']], settings['korean_speed'])
                        play_audio(audio_file)
                        await asyncio.sleep(settings['spacing'])
                    elif third_lang == 'english':
                        audio_file = await create_audio(eng, VOICE_MAPPING['english'][settings['eng_voice']], settings['english_speed'])
                        play_audio(audio_file)
                        await asyncio.sleep(settings['spacing'])
                    elif third_lang == 'chinese':
                        audio_file = await create_audio(chn, VOICE_MAPPING['chinese'][settings['zh_voice']], settings['chinese_speed'])
                        play_audio(audio_file)
                        await asyncio.sleep(settings['spacing'])

            except Exception as e:
                st.error(f"음성 재생 오류: {e}")
                traceback.print_exc()

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
            # final.wav 재생
            final_sound_path = SCRIPT_DIR / 'base/final.wav'
            if final_sound_path.exists():
                play_audio(str(final_sound_path))
                await asyncio.sleep(1)

            if settings['auto_repeat']:
                repeat_count += 1
                if repeat_count < settings['auto_repeat_count']:
                    # 설정된 반복 횟수에 도달하지 않았으면 다시 시작
                    sentence_count = 0
                    status.info(f"자동 반복 중... ({repeat_count}/{settings['auto_repeat_count']})")
                    continue
                else:
                    # 설정된 반복 횟수에 도달하면 종료
                    st.success(f"학습이 완료되었습니다! (총 {settings['auto_repeat_count']}회 반복)")
            else:
                # 자동 반복이 꺼져 있으면 학습 종료
                st.success("학습이 완료되었습니다!")
            
            st.session_state.page = 'settings'
            st.rerun()
            break
                
        except Exception as e:
            st.error(f"완료 알림음 재생 오류: {e}")
            traceback.print_exc()

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
        
        # 학습 시작
        asyncio.run(start_learning())

def save_settings(settings):
    """설정값을 파일에 저장"""
    try:
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"설정 저장 중 오류: {e}")

if __name__ == "__main__":
    main()