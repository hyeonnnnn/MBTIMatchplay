"""MBTI Matchplay - MBTI 기반 선택형 미연시 게임"""

import streamlit as st
import json
import random
from pathlib import Path

from utils.ai_client import generate_response, generate_character_images


# Page config
st.set_page_config(
    page_title="MBTI Matchplay",
    page_icon="💕",
    layout="centered"
)

# Constants
MBTI_TYPES = [
    "INTJ", "INTP", "ENTJ", "ENTP",
    "INFJ", "INFP", "ENFJ", "ENFP",
    "ISTJ", "ISFJ", "ESTJ", "ESFJ",
    "ISTP", "ISFP", "ESTP", "ESFP"
]

EXPRESSIONS = {
    "bad": ("pout", "삐짐"),
    "ok": ("smile", "미소"),
    "good": ("big_smile", "활짝")
}

GENDER_OPTIONS = ["여성", "남성"]
FACE_OPTIONS = ["귀여운 얼굴", "시크한 얼굴", "청순한 얼굴", "카리스마 있는 얼굴", "부드러운 얼굴"]
HAIR_OPTIONS = ["긴 검은 머리", "긴 갈색 머리", "단발 검은 머리", "짧은 검은 머리", "긴 금발", "짧은 갈색 머리", "은발"]
EYE_OPTIONS = ["갈색 눈", "검은 눈", "파란 눈", "초록 눈", "보라색 눈"]
OUTFIT_OPTIONS = ["캐주얼 의상", "정장", "교복", "원피스", "후드티와 청바지", "세미정장"]
ATMOSPHERE_OPTIONS = ["따뜻하고 친근한", "시크하고 도도한", "밝고 활발한", "차분하고 지적인", "신비롭고 몽환적인"]

def calculate_grade(mbti: str, tags: list) -> tuple:
    """Calculate grade based on MBTI match with answer tags.

    Args:
        mbti: Character's MBTI (e.g., "INFP")
        tags: List of MBTI dimension tags for the answer (e.g., ["I", "N", "F"])

    Returns:
        Tuple of (grade, delta) where grade is "good"/"ok"/"bad"
    """
    mbti_letters = list(mbti)  # ["I", "N", "F", "P"]
    match_count = sum(1 for tag in tags if tag in mbti_letters)

    if match_count >= 3:
        return ("good", 30)
    elif match_count == 2:
        return ("ok", 10)
    else:
        return ("bad", -10)


@st.cache_data
def load_questions():
    """Load questions from JSON file."""
    path = Path(__file__).parent / "data" / "questions.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["questions"]


@st.cache_data
def load_mbti_traits():
    """Load MBTI traits from JSON file."""
    path = Path(__file__).parent / "data" / "mbti_traits.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def init_session_state():
    """Initialize session state variables."""
    defaults = {
        "screen": "start",
        "player_name": "",
        "mbti": "",
        "appearance_prefs": {},
        "affection": 30,
        "question_order": [],
        "current_q_idx": 0,
        "current_expression": "neutral",
        "character_images": {},
        "character_name": "",
        "log": [],
        "last_response": "",
        "last_grade": "ok",
        "show_response": False,
        "total_questions": 12
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def generate_character_name(mbti: str) -> str:
    """Generate a random Korean name based on MBTI."""
    first_names_female = [
        "서연", "지민", "유진", "하은", "수아", "민서", "채원", "지우", "예은", "시은",
        "이서", "아윤", "지아", "시아", "서윤", "윤아", "다인", "연우", "재이", "해린"
    ]

    first_names_male = [
        "민준", "서준", "도윤", "예준", "시우", "주원", "지호", "준서", "현우", "승현",
        "은우", "선우", "준", "건우", "유준", "로운", "하준", "서진", "시윤", "진우"
    ]

    gender = st.session_state.appearance_prefs.get("gender", "여성")
    if gender == "여성":
        return random.choice(first_names_female)
    return random.choice(first_names_male)


def render_loading_screen(message: str = "로딩 중..."):
    """Render a romantic loading screen with heart animation."""
    loading_messages = [
        "운명의 상대를 찾고 있어요...",
        "두근두근, 설레는 만남이 다가와요...",
        "당신만을 위한 이야기를 준비하고 있어요...",
        "사랑의 마법을 걸고 있어요...",
    ]
    import random
    sub_message = random.choice(loading_messages)

    st.markdown(f"""
    <style>
        @keyframes heartbeat {{
            0%, 100% {{ transform: scale(1); }}
            25% {{ transform: scale(1.1); }}
            50% {{ transform: scale(1); }}
            75% {{ transform: scale(1.15); }}
        }}
        @keyframes float {{
            0%, 100% {{ transform: translateY(0px) rotate(0deg); opacity: 1; }}
            50% {{ transform: translateY(-20px) rotate(5deg); opacity: 0.8; }}
        }}
        @keyframes shimmer {{
            0% {{ background-position: -200% center; }}
            100% {{ background-position: 200% center; }}
        }}
        .loading-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 60px 20px;
            background: linear-gradient(135deg, #fce4ec 0%, #f3e5f5 50%, #e8eaf6 100%);
            border-radius: 24px;
            margin: 40px 0;
            box-shadow: 0 12px 40px rgba(156, 39, 176, 0.15);
        }}
        .heart-container {{
            position: relative;
            width: 80px;
            height: 80px;
            margin-bottom: 24px;
        }}
        .main-heart {{
            font-size: 48px;
            animation: heartbeat 1.2s ease-in-out infinite;
            filter: drop-shadow(0 4px 12px rgba(233, 30, 99, 0.4));
        }}
        .floating-heart {{
            position: absolute;
            font-size: 16px;
            animation: float 2s ease-in-out infinite;
        }}
        .floating-heart:nth-child(2) {{ top: -10px; left: 0; animation-delay: 0.2s; }}
        .floating-heart:nth-child(3) {{ top: 0; right: -10px; animation-delay: 0.5s; }}
        .floating-heart:nth-child(4) {{ bottom: 10px; left: -15px; animation-delay: 0.8s; }}
        .floating-heart:nth-child(5) {{ bottom: 0; right: -5px; animation-delay: 1.1s; }}
        .loading-text {{
            font-size: 20px;
            font-weight: 600;
            color: #7b1fa2;
            margin-bottom: 8px;
            background: linear-gradient(90deg, #ec407a, #ab47bc, #7e57c2, #ec407a);
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: shimmer 3s linear infinite;
        }}
        .loading-subtext {{
            font-size: 14px;
            color: #9575cd;
            font-style: italic;
        }}
        .dot-animation {{
            display: inline-block;
        }}
        .dot-animation::after {{
            content: '';
            animation: dots 1.5s steps(4, end) infinite;
        }}
        @keyframes dots {{
            0%, 20% {{ content: ''; }}
            40% {{ content: '.'; }}
            60% {{ content: '..'; }}
            80%, 100% {{ content: '...'; }}
        }}
    </style>
    <div class="loading-container">
        <div class="heart-container">
            <span class="main-heart">💕</span>
            <span class="floating-heart">💗</span>
            <span class="floating-heart">💖</span>
            <span class="floating-heart">💓</span>
            <span class="floating-heart">✨</span>
        </div>
        <div class="loading-text">{message}<span class="dot-animation"></span></div>
        <div class="loading-subtext">{sub_message}</div>
    </div>
    """, unsafe_allow_html=True)


def render_affection_bar():
    """Render affection gauge bar."""
    affection = st.session_state.affection
    # 로맨틱한 그라데이션: 차가운 보라 → 따뜻한 핑크 → 열정의 로즈
    color = "#9b8aa8" if affection < 30 else "#e4a0b7" if affection < 70 else "#f06292"

    st.markdown(f"""
    <div style="margin: 10px 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
            <span>💔</span>
            <span style="font-weight: bold; color: #5c4a6b;">호감도: {affection}/100</span>
            <span>💕</span>
        </div>
        <div style="background: linear-gradient(90deg, #f3e5f5 0%, #fce4ec 100%); border-radius: 12px; height: 22px; overflow: hidden; box-shadow: inset 0 2px 4px rgba(0,0,0,0.1);">
            <div style="background: linear-gradient(90deg, {color} 0%, #f8bbd9 100%); height: 100%; width: {affection}%; transition: width 0.5s ease-out; border-radius: 12px;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_character_image():
    """Render current character image based on expression."""
    expr = st.session_state.current_expression
    images = st.session_state.character_images

    if expr in images and images[expr]:
        img_data = images[expr]
        st.markdown(
            f'''<div style="text-align: center;">
                <img src="data:image/png;base64,{img_data}" style="max-width: 300px; border-radius: 16px; box-shadow: 0 8px 24px rgba(156, 39, 176, 0.2); border: 3px solid #f8bbd9;">
            </div>''',
            unsafe_allow_html=True
        )
    else:
        st.markdown("""
        <div style="text-align: center; padding: 40px; background: linear-gradient(135deg, #fce4ec 0%, #f3e5f5 100%); border-radius: 16px;">
            <div style="font-size: 32px; animation: pulse 1.5s ease-in-out infinite;">💭</div>
            <p style="color: #9575cd; margin-top: 12px; font-style: italic;">캐릭터를 불러오는 중...</p>
        </div>
        <style>
            @keyframes pulse {
                0%, 100% { opacity: 1; transform: scale(1); }
                50% { opacity: 0.6; transform: scale(0.95); }
            }
        </style>
        """, unsafe_allow_html=True)


def render_start_screen():
    """Render the start/setup screen."""
    # Global styles for the start screen
    st.markdown("""
    <style>
        /* 전체 배경 */
        .stApp {
            background: linear-gradient(180deg, #fdf2f8 0%, #faf5ff 50%, #f0f9ff 100%) !important;
        }

        /* 텍스트 인풋 컨테이너 */
        .stTextInput {
            overflow: visible !important;
        }
        .stTextInput > div {
            overflow: visible !important;
            height: auto !important;
            max-height: none !important;
        }
        .stTextInput > div > div {
            overflow: visible !important;
            height: auto !important;
            max-height: none !important;
        }
        /* 텍스트 인풋 필드 */
        .stTextInput > div > div > input {
            background: linear-gradient(135deg, #ffffff 0%, #fdf2f8 100%) !important;
            border: 2px solid #d8b4fe !important;
            border-radius: 12px !important;
            padding: 14px 16px !important;
            height: auto !important;
            min-height: 48px !important;
            max-height: none !important;
            line-height: normal !important;
            box-sizing: border-box !important;
            overflow: visible !important;
            clip: auto !important;
            color: #581c87 !important;
            font-size: 16px !important;
            transition: all 0.3s ease !important;
        }
        .stTextInput > div > div > input:focus {
            border-color: #c084fc !important;
            box-shadow: 0 0 0 3px rgba(192, 132, 252, 0.3) !important;
        }
        .stTextInput > div > div > input::placeholder {
            color: #c4b5fd !important;
        }

        /* 셀렉트박스 (드롭다운) */
        .stSelectbox [data-baseweb="select"] {
            background: linear-gradient(135deg, #ffffff 0%, #fdf2f8 100%) !important;
            border: 2px solid #d8b4fe !important;
            border-radius: 12px !important;
            transition: all 0.3s ease !important;
        }
        .stSelectbox [data-baseweb="select"]:hover {
            border-color: #c084fc !important;
            box-shadow: 0 0 0 3px rgba(192, 132, 252, 0.2) !important;
        }
        .stSelectbox [data-baseweb="select"] > div {
            background: transparent !important;
            border: none !important;
            color: #581c87 !important;
            min-height: 48px !important;
        }
        .stSelectbox [data-baseweb="select"] > div:first-child {
            padding: 12px 16px !important;
            min-height: 48px !important;
            display: flex !important;
            align-items: center !important;
        }
        .stSelectbox [data-baseweb="select"] span {
            line-height: 1.4 !important;
            overflow: visible !important;
        }
        .stSelectbox svg {
            fill: #a855f7 !important;
        }

        /* 드롭다운 메뉴 */
        [data-baseweb="popover"] {
            background: #ffffff !important;
            border: 2px solid #e9d5ff !important;
            border-radius: 12px !important;
            box-shadow: 0 8px 24px rgba(168, 85, 247, 0.15) !important;
        }
        [data-baseweb="popover"] > div {
            background: #ffffff !important;
        }
        [data-baseweb="menu"] {
            background: #ffffff !important;
        }
        [data-baseweb="menu"] ul {
            background: #ffffff !important;
        }
        [data-baseweb="menu"] li {
            color: #581c87 !important;
            background: #ffffff !important;
        }
        [data-baseweb="menu"] li:hover {
            background: linear-gradient(135deg, #fae8ff 0%, #fdf2f8 100%) !important;
        }
        [data-baseweb="menu"] li[aria-selected="true"] {
            background: #f3e8ff !important;
        }
        /* 드롭다운 옵션 텍스트 */
        [role="option"] {
            color: #581c87 !important;
            background: #ffffff !important;
        }
        [role="option"]:hover {
            background: #faf5ff !important;
        }
        [role="listbox"] {
            background: #ffffff !important;
        }

        /* 버튼 기본 */
        .stButton > button {
            background: linear-gradient(135deg, #f9a8d4 0%, #c084fc 100%) !important;
            border: none !important;
            border-radius: 12px !important;
            color: white !important;
            font-weight: 600 !important;
            padding: 10px 24px !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 12px rgba(192, 132, 252, 0.3) !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(192, 132, 252, 0.4) !important;
            background: linear-gradient(135deg, #f472b6 0%, #a855f7 100%) !important;
        }
        .stButton > button:active {
            transform: translateY(0) !important;
        }

        /* Primary 버튼 (시작하기) */
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #ec4899 0%, #a855f7 50%, #6366f1 100%) !important;
            font-size: 18px !important;
            padding: 16px 32px !important;
            border-radius: 50px !important;
            box-shadow: 0 6px 24px rgba(168, 85, 247, 0.4) !important;
        }
        .stButton > button[kind="primary"]:hover {
            box-shadow: 0 8px 32px rgba(168, 85, 247, 0.5) !important;
        }

        /* 비활성화 버튼 */
        .stButton > button:disabled {
            background: linear-gradient(135deg, #e9d5ff 0%, #ddd6fe 100%) !important;
            color: #a78bfa !important;
            box-shadow: none !important;
        }

        /* 라벨 숨기기 */
        .stTextInput label, .stSelectbox label {
            color: #7c3aed !important;
            font-weight: 500 !important;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        @keyframes sparkle {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        @keyframes gradient-shift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .main-title {
            text-align: center;
            padding: 40px 20px;
            background: linear-gradient(135deg, #fce4ec 0%, #f3e5f5 30%, #e8eaf6 60%, #fce4ec 100%);
            background-size: 200% 200%;
            animation: gradient-shift 8s ease infinite;
            border-radius: 24px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(156, 39, 176, 0.15);
        }
        .title-icon {
            font-size: 48px;
            display: block;
            margin-bottom: 10px;
            animation: float 3s ease-in-out infinite;
        }
        .title-text {
            font-size: 36px;
            font-weight: 700;
            background: linear-gradient(135deg, #ec407a, #ab47bc, #7e57c2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0;
        }
        .subtitle {
            color: #9575cd;
            font-size: 16px;
            margin-top: 8px;
            font-style: italic;
        }
        .section-card {
            background: linear-gradient(135deg, #fce4ec 0%, #f3e5f5 100%) !important;
            border: 2px solid #e1bee7;
            border-radius: 20px;
            padding: 20px 24px;
            margin: 16px 0 8px 0;
            box-shadow: 0 4px 16px rgba(156, 39, 176, 0.12);
        }
        .section-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 0;
        }
        .section-icon {
            font-size: 24px;
            animation: sparkle 2s ease-in-out infinite;
        }
        .section-title {
            color: #6a1b9a !important;
            font-size: 18px;
            font-weight: 700;
            margin: 0;
            text-shadow: 0 1px 2px rgba(255,255,255,0.8);
        }
        .decorative-dots {
            text-align: center;
            color: #e1bee7;
            letter-spacing: 8px;
            margin: 20px 0;
        }
    </style>

    <div class="main-title">
        <span class="title-icon">💕</span>
        <h1 class="title-text">MBTI Matchplay</h1>
        <p class="subtitle">당신의 이상형을 만나는 로맨틱 시뮬레이션</p>
    </div>
    """, unsafe_allow_html=True)

    # Player name section
    st.markdown("""
    <div style="background: linear-gradient(135deg, #fce4ec 0%, #f3e5f5 100%); border: 2px solid #e1bee7; border-radius: 16px; padding: 16px 20px; margin: 16px 0 8px 0; box-shadow: 0 4px 12px rgba(156, 39, 176, 0.1);">
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="color: #6a1b9a; font-size: 17px; font-weight: 700;">당신의 이름은? (성 제외)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    player_name = st.text_input("이름", key="input_name", placeholder="이름을 입력하세요", label_visibility="collapsed")

    st.markdown('<p class="decorative-dots">• • •</p>', unsafe_allow_html=True)

    # MBTI selection section
    st.markdown("""
    <div style="background: linear-gradient(135deg, #fce4ec 0%, #f3e5f5 100%); border: 2px solid #e1bee7; border-radius: 16px; padding: 16px 20px; margin: 16px 0 8px 0; box-shadow: 0 4px 12px rgba(156, 39, 176, 0.1);">
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="color: #6a1b9a; font-size: 17px; font-weight: 700;">상대방의 MBTI를 선택하세요</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 랜덤 버튼 콜백
    def random_mbti():
        st.session_state.random_mbti = random.choice(MBTI_TYPES)

    # 랜덤 값이 있으면 사용
    default_idx = 0
    if "random_mbti" in st.session_state:
        default_idx = MBTI_TYPES.index(st.session_state.random_mbti) + 1

    selected_mbti = st.selectbox("MBTI 선택", options=[""] + MBTI_TYPES, index=default_idx, label_visibility="collapsed")
    st.button("🎲 랜덤 MBTI", on_click=random_mbti, use_container_width=True)

    # Show MBTI info
    if selected_mbti:
        traits = load_mbti_traits().get(selected_mbti, {})
        if traits:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f3e5f5 0%, #fce4ec 100%); padding: 20px; border-radius: 16px; margin: 12px 0; border-left: 4px solid #ab47bc;">
                <h4 style="color: #7b1fa2; margin: 0 0 12px 0;">💜 {selected_mbti} - {traits.get('name', '')}</h4>
                <div style="color: #5c4a6b; line-height: 1.8;">
                    <p style="margin: 6px 0;"><strong style="color: #8e6b8a;">말투:</strong> {traits.get('speech_style', '')}</p>
                    <p style="margin: 6px 0;"><strong style="color: #8e6b8a;">가치관:</strong> {traits.get('values', '')}</p>
                    <p style="margin: 6px 0;"><strong style="color: #8e6b8a;">좋아하는 것:</strong> {traits.get('likes', '')}</p>
                    <p style="margin: 6px 0;"><strong style="color: #8e6b8a;">싫어하는 것:</strong> {traits.get('dislikes', '')}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<p class="decorative-dots">• • •</p>', unsafe_allow_html=True)

    # Appearance preferences section
    st.markdown("""
    <div style="background: linear-gradient(135deg, #fce4ec 0%, #f3e5f5 100%); border: 2px solid #e1bee7; border-radius: 16px; padding: 16px 20px; margin: 16px 0 8px 0; box-shadow: 0 4px 12px rgba(156, 39, 176, 0.1);">
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="color: #6a1b9a; font-size: 17px; font-weight: 700;">이상형의 외모를 선택하세요</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        gender = st.selectbox("성별", GENDER_OPTIONS, key="gender_select")
        face_type = st.selectbox("얼굴상", FACE_OPTIONS, key="face_select")
        hair = st.selectbox("헤어스타일", HAIR_OPTIONS, key="hair_select")
    with col2:
        eyes = st.selectbox("눈", EYE_OPTIONS, key="eyes_select")
        outfit = st.selectbox("옷", OUTFIT_OPTIONS, key="outfit_select")
        atmosphere = st.selectbox("분위기", ATMOSPHERE_OPTIONS, key="atmosphere_select")

    st.markdown('<p class="decorative-dots">• • •</p>', unsafe_allow_html=True)

    # Start button with custom styling
    can_start = player_name and selected_mbti

    st.markdown("""
    <style>
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #ec407a 0%, #ab47bc 50%, #7e57c2 100%);
            border: none;
            padding: 16px 32px;
            font-size: 18px;
            font-weight: 600;
            border-radius: 50px;
            box-shadow: 0 6px 20px rgba(171, 71, 188, 0.4);
            transition: all 0.3s ease;
        }
        div.stButton > button[kind="primary"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(171, 71, 188, 0.5);
        }
        div.stButton > button[kind="primary"]:active {
            transform: translateY(0);
        }
    </style>
    """, unsafe_allow_html=True)

    if st.button("💕 시작하기", disabled=not can_start, use_container_width=True, type="primary"):
        # Save settings
        st.session_state.player_name = player_name
        st.session_state.mbti = selected_mbti
        st.session_state.appearance_prefs = {
            "gender": gender,
            "face_type": face_type,
            "hair": hair,
            "eyes": eyes,
            "outfit": outfit,
            "atmosphere": atmosphere
        }

        # Generate character
        st.session_state.character_name = generate_character_name(selected_mbti)

        # Select 12 random questions
        questions = load_questions()
        st.session_state.question_order = random.sample(range(len(questions)), 12)
        st.session_state.current_q_idx = 0
        st.session_state.total_questions = 12

        # Reset game state
        st.session_state.affection = 30
        st.session_state.log = []
        st.session_state.current_expression = "neutral"

        # Generate character images with custom loading screen
        loading_placeholder = st.empty()
        with loading_placeholder.container():
            render_loading_screen("당신의 이상형을 그리는 중")

        images = generate_character_images(
            st.session_state.appearance_prefs,
            selected_mbti
        )
        loading_placeholder.empty()

        # 이미지가 제대로 생성되었는지 확인
        has_valid_image = images and any(images.get(expr) for expr in ["smile", "pout", "big_smile", "neutral"])

        if has_valid_image:
            st.session_state.character_images = images
            # Transition to game
            st.session_state.screen = "game"
            st.rerun()
        else:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); padding: 20px; border-radius: 16px; text-align: center; border: 2px solid #f87171;">
                <p style="color: #b91c1c; font-size: 16px; margin: 0;">😢 캐릭터 이미지를 생성하지 못했어요.<br>잠시 후 다시 시도해주세요.</p>
            </div>
            """, unsafe_allow_html=True)

    if not can_start:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%); padding: 14px 20px; border-radius: 12px; text-align: center; border-left: 4px solid #ffb74d;">
            <span style="color: #e65100;">✨ 이름과 MBTI를 선택하면 운명의 만남이 시작돼요!</span>
        </div>
        """, unsafe_allow_html=True)


def render_game_screen():
    """Render the main game screen."""
    questions = load_questions()
    mbti_traits = load_mbti_traits()

    # 게임 화면 스타일
    st.markdown("""
    <style>
        /* 전체 배경 */
        .stApp {
            background: linear-gradient(180deg, #fdf2f8 0%, #faf5ff 50%, #f0f9ff 100%) !important;
        }

        /* 게임 헤더 카드 */
        .game-header {
            background: linear-gradient(135deg, #fce4ec 0%, #f3e5f5 50%, #e8eaf6 100%);
            border-radius: 20px;
            padding: 20px 24px;
            margin-bottom: 16px;
            box-shadow: 0 4px 16px rgba(156, 39, 176, 0.12);
            border: 2px solid #e1bee7;
        }
        .char-name {
            font-size: 28px;
            font-weight: 700;
            background: linear-gradient(135deg, #ec407a, #ab47bc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0;
        }
        .char-mbti {
            color: #9575cd;
            font-size: 14px;
            margin-top: 4px;
        }
        .question-count {
            background: linear-gradient(135deg, #f8bbd9 0%, #e1bee7 100%);
            color: #6a1b9a;
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
            display: inline-block;
        }

        /* 질문 카드 */
        .question-card {
            background: linear-gradient(135deg, #ffffff 0%, #fdf2f8 100%);
            border: 2px solid #f0abfc;
            border-radius: 16px;
            padding: 20px;
            margin: 16px 0;
            box-shadow: 0 4px 12px rgba(168, 85, 247, 0.1);
        }
        .question-text {
            color: #581c87;
            font-size: 18px;
            font-weight: 600;
            line-height: 1.6;
        }

        /* 선택지 라벨 */
        .options-label {
            color: #9575cd;
            font-size: 14px;
            font-weight: 600;
            margin: 16px 0 8px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* 구분선 */
        .game-divider {
            text-align: center;
            color: #e1bee7;
            letter-spacing: 8px;
            margin: 16px 0;
        }

        /* 버튼 스타일 */
        .stButton > button {
            background: linear-gradient(135deg, #f9a8d4 0%, #c084fc 100%) !important;
            border: none !important;
            border-radius: 12px !important;
            color: white !important;
            font-weight: 600 !important;
            padding: 12px 24px !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 12px rgba(192, 132, 252, 0.3) !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(192, 132, 252, 0.4) !important;
            background: linear-gradient(135deg, #f472b6 0%, #a855f7 100%) !important;
        }
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #ec4899 0%, #a855f7 50%, #6366f1 100%) !important;
            font-size: 16px !important;
            padding: 14px 28px !important;
            border-radius: 25px !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header
    char_name = st.session_state.character_name
    mbti = st.session_state.mbti
    mbti_name = mbti_traits[mbti]['name']
    total_q = st.session_state.get("total_questions", 12)
    current_q = st.session_state.current_q_idx + 1

    st.markdown(f"""
    <div class="game-header">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px;">
            <div>
                <h2 class="char-name">💕 {char_name}</h2>
                <p class="char-mbti">{mbti} · {mbti_name}</p>
            </div>
            <div class="question-count">💬 질문 {current_q}/{total_q}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🏠 로비로", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Affection bar
    render_affection_bar()

    st.markdown('<p class="game-divider">• • •</p>', unsafe_allow_html=True)

    # Character image
    render_character_image()

    st.markdown('<p class="game-divider">• • •</p>', unsafe_allow_html=True)

    # Current question
    q_idx = st.session_state.question_order[st.session_state.current_q_idx]
    question = questions[q_idx]
    player_name = st.session_state.player_name

    # Add player name to question with random suffix (fixed per question)
    if st.session_state.get("current_suffix_idx") != st.session_state.current_q_idx:
        st.session_state.current_suffix = random.choice(["..", "!", "~"])
        st.session_state.current_suffix_idx = st.session_state.current_q_idx
    question_text = f"{player_name}{st.session_state.current_suffix} {question['q']}"

    st.markdown(f"""
    <div class="question-card">
        <p class="question-text">Q{st.session_state.current_q_idx + 1}. {question_text}</p>
    </div>
    """, unsafe_allow_html=True)

    # Show AI response if available
    if st.session_state.get("show_response", False) and st.session_state.get("last_response", ""):
        expr_name = EXPRESSIONS.get(st.session_state.last_grade, ("neutral", ""))[1]
        # 감정에 따른 배경색: good=로즈, ok=라벤더, bad=쿨그레이
        grade = st.session_state.last_grade
        bg_color = "#fff0f5" if grade == "good" else "#f5f0ff" if grade == "ok" else "#f0eff4"
        border_color = "#f8bbd9" if grade == "good" else "#d4c4e8" if grade == "ok" else "#c5c0d0"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, {bg_color} 0%, #ffffff 100%); padding: 18px; border-radius: 16px; margin: 12px 0; color: #3d3450; border-left: 4px solid {border_color}; box-shadow: 0 2px 8px rgba(93, 74, 107, 0.08);">
            <strong style="color: #6b5b7a;">{st.session_state.character_name}</strong> <span style="color: #9b8aa8;">({expr_name})</span><br>
            <span style="line-height: 1.6;">{st.session_state.last_response}</span>
        </div>
        """, unsafe_allow_html=True)

        # Next question button
        if st.button("다음 질문 →", use_container_width=True, type="primary"):
            st.session_state.show_response = False
            st.session_state.current_q_idx += 1
            st.session_state.current_expression = "neutral"

            # Check ending conditions
            if st.session_state.affection <= 0:
                st.session_state.screen = "ending"
                st.session_state.ending_type = "failure"
            elif st.session_state.affection >= 100:
                st.session_state.screen = "ending"
                st.session_state.ending_type = "success"
            elif st.session_state.current_q_idx >= st.session_state.get("total_questions", 12):
                # Game finished - check final affection
                if st.session_state.affection >= 80:
                    st.session_state.screen = "ending"
                    st.session_state.ending_type = "success"
                else:
                    st.session_state.screen = "ending"
                    st.session_state.ending_type = "failure"

            st.rerun()
    else:
        # Answer options
        st.markdown('<p class="options-label">💭 선택지</p>', unsafe_allow_html=True)
        for i, option in enumerate(question["options"]):
            if st.button(option["text"], key=f"option_{i}", use_container_width=True):
                # Calculate grade based on MBTI match
                tags = option.get("tags", [])
                grade, delta = calculate_grade(st.session_state.mbti, tags)

                # Update affection
                st.session_state.affection = max(0, min(100, st.session_state.affection + delta))

                # Update expression
                expr_key, expr_name = EXPRESSIONS.get(grade, ("neutral", ""))
                st.session_state.current_expression = expr_key

                # Log the choice
                st.session_state.log.append({
                    "question": question["q"],
                    "answer": option["text"],
                    "grade": grade,
                    "delta": delta
                })

                # Generate AI response
                response = None
                try:
                    response = generate_response(
                        st.session_state.mbti,
                        mbti_traits,
                        question["q"],
                        option["text"],
                        grade
                    )
                except Exception:
                    pass

                # Fallback response if API fails
                if not response:
                    if grade == "good":
                        response = f"{player_name}, 정말 좋아! 그렇게 생각해줘서 고마워 💕"
                    elif grade == "ok":
                        response = f"음, 그렇구나~ 괜찮아, {player_name}!"
                    else:
                        response = f"{player_name}... 음... 그건 좀 아쉽네..."

                st.session_state.last_response = response
                st.session_state.last_grade = grade
                st.session_state.show_response = True
                st.rerun()


def render_ending_screen():
    """Render the ending screen."""
    is_success = st.session_state.ending_type == "success"
    player_name = st.session_state.player_name
    char_name = st.session_state.character_name

    # 엔딩 화면 스타일
    st.markdown("""
    <style>
        /* 전체 배경 */
        .stApp {
            background: linear-gradient(180deg, #fdf2f8 0%, #faf5ff 50%, #f0f9ff 100%) !important;
        }

        /* 엔딩 타이틀 */
        .ending-title {
            text-align: center;
            padding: 30px 20px;
            background: linear-gradient(135deg, #fce4ec 0%, #f3e5f5 30%, #e8eaf6 60%, #fce4ec 100%);
            background-size: 200% 200%;
            animation: gradient-shift 8s ease infinite;
            border-radius: 24px;
            margin-bottom: 24px;
            box-shadow: 0 8px 32px rgba(156, 39, 176, 0.15);
        }
        @keyframes gradient-shift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        .ending-title h1 {
            font-size: 32px;
            font-weight: 700;
            background: linear-gradient(135deg, #ec407a, #ab47bc, #7e57c2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin: 0;
        }
        .ending-title p {
            color: #9575cd;
            margin-top: 8px;
        }

        /* 결과 카드 */
        .stats-card {
            background: linear-gradient(135deg, #ffffff 0%, #fdf2f8 100%);
            border: 2px solid #e1bee7;
            border-radius: 16px;
            padding: 20px;
            margin: 16px 0;
            box-shadow: 0 4px 12px rgba(156, 39, 176, 0.1);
        }
        .stats-title {
            color: #6a1b9a;
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .stat-item {
            background: linear-gradient(135deg, #fce4ec 0%, #f3e5f5 100%);
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            border: 1px solid #f0abfc;
        }
        .stat-value {
            font-size: 24px;
            font-weight: 700;
            color: #7b1fa2;
        }
        .stat-label {
            font-size: 13px;
            color: #9575cd;
            margin-top: 4px;
        }

        /* 구분선 */
        .ending-divider {
            text-align: center;
            color: #e1bee7;
            letter-spacing: 8px;
            margin: 20px 0;
        }

        /* 버튼 */
        .stButton > button {
            background: linear-gradient(135deg, #f9a8d4 0%, #c084fc 100%) !important;
            border: none !important;
            border-radius: 12px !important;
            color: white !important;
            font-weight: 600 !important;
            padding: 12px 24px !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 12px rgba(192, 132, 252, 0.3) !important;
        }
        .stButton > button:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(192, 132, 252, 0.4) !important;
            background: linear-gradient(135deg, #f472b6 0%, #a855f7 100%) !important;
        }
        .stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #ec4899 0%, #a855f7 50%, #6366f1 100%) !important;
            font-size: 16px !important;
            padding: 14px 28px !important;
            border-radius: 25px !important;
        }

        /* Expander 스타일 */
        .streamlit-expanderHeader {
            background: linear-gradient(135deg, #fce4ec 0%, #f3e5f5 100%) !important;
            border-radius: 12px !important;
            color: #6a1b9a !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # 엔딩 타이틀
    st.markdown("""
    <div class="ending-title">
        <h1>💕 MBTI Matchplay</h1>
        <p>엔딩</p>
    </div>
    """, unsafe_allow_html=True)

    # Ending text
    if is_success:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #fce4ec 0%, #f8bbd9 50%, #f3e5f5 100%); padding: 40px 30px; border-radius: 24px; text-align: center; margin: 20px 0; box-shadow: 0 12px 40px rgba(240, 98, 146, 0.25); border: 2px solid #f8bbd9;">
            <div style="font-size: 48px; margin-bottom: 16px;">💕</div>
            <h2 style="color: #ad1457; font-size: 28px; margin-bottom: 20px;">성공 엔딩</h2>
            <p style="font-size: 17px; line-height: 2.2; color: #5c4a6b;">
                {char_name}이(가) 환하게 웃으며 {player_name}의 손을 잡았다.<br><br>
                <em style="color: #8e6b8a; font-size: 18px;">"{player_name}... 너랑 있으면 정말 행복해.<br>
                앞으로도 계속 함께하자, 응?"</em>
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #ede7f6 0%, #d1c4e9 50%, #e8e4f0 100%); padding: 40px 30px; border-radius: 24px; text-align: center; margin: 20px 0; box-shadow: 0 12px 40px rgba(103, 88, 124, 0.2); border: 2px solid #d1c4e9;">
            <div style="font-size: 48px; margin-bottom: 16px;">💔</div>
            <h2 style="color: #5e4a6b; font-size: 28px; margin-bottom: 20px;">실패 엔딩</h2>
            <p style="font-size: 17px; line-height: 2.2; color: #6b5b7a;">
                {char_name}이(가) 고개를 돌리며 말했다.<br><br>
                <em style="color: #8e7a9b; font-size: 18px;">"{player_name}... 우리 여기까지인 것 같아.<br>
                좋은 사람 만나."</em>
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<p class="ending-divider">• • •</p>', unsafe_allow_html=True)

    # Final stats
    affection = st.session_state.affection
    mbti = st.session_state.mbti
    question_count = len(st.session_state.log)

    st.markdown(f"""
    <div class="stats-card">
        <div class="stats-title">📊 게임 결과</div>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;">
            <div class="stat-item">
                <div class="stat-value">{affection}/100</div>
                <div class="stat-label">최종 호감도</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{mbti}</div>
                <div class="stat-label">상대 MBTI</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{question_count}개</div>
                <div class="stat-label">질문 수</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Choice log summary
    with st.expander("📝 선택 기록 보기"):
        good_count = sum(1 for log in st.session_state.log if log["grade"] == "good")
        ok_count = sum(1 for log in st.session_state.log if log["grade"] == "ok")
        bad_count = sum(1 for log in st.session_state.log if log["grade"] == "bad")

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #f3e5f5 0%, #fce4ec 100%); padding: 16px; border-radius: 12px; margin-bottom: 16px;">
            <p style="margin: 6px 0; color: #4a7c59;"><strong>😊 좋은 선택:</strong> {good_count}회 (+{good_count * 30})</p>
            <p style="margin: 6px 0; color: #7c6b4a;"><strong>🙂 보통 선택:</strong> {ok_count}회 (+{ok_count * 10})</p>
            <p style="margin: 6px 0; color: #7c4a5a;"><strong>😤 나쁜 선택:</strong> {bad_count}회 ({bad_count * -10})</p>
        </div>
        """, unsafe_allow_html=True)

        for i, log in enumerate(st.session_state.log):
            grade_emoji = "😊" if log["grade"] == "good" else "🙂" if log["grade"] == "ok" else "😤"
            grade_color = "#4a7c59" if log["grade"] == "good" else "#7c6b4a" if log["grade"] == "ok" else "#7c4a5a"
            st.markdown(f"""
            <div style="background: #ffffff; padding: 12px 16px; border-radius: 10px; margin: 8px 0; border-left: 3px solid {grade_color};">
                <p style="margin: 0; color: #581c87; font-weight: 600;">Q{i+1}. {log['question']}</p>
                <p style="margin: 6px 0 0 0; color: #6b5b7a;">→ {log['answer']} {grade_emoji} <span style="color: {grade_color};">({log['delta']:+d})</span></p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<p class="ending-divider">• • •</p>', unsafe_allow_html=True)

    # Restart button
    if st.button("🔄 로비로 돌아가기", use_container_width=True, type="primary"):
        # Clear session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()




def main():
    """Main application entry point."""
    init_session_state()

    # Route to appropriate screen
    if st.session_state.screen == "start":
        render_start_screen()
    elif st.session_state.screen == "game":
        render_game_screen()
    elif st.session_state.screen == "ending":
        render_ending_screen()


if __name__ == "__main__":
    main()
