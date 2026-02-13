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
    first_names_female = ["서연", "지민", "유진", "하은", "수아", "민서", "채원", "지우", "예은", "시은"]
    first_names_male = ["민준", "서준", "도윤", "예준", "시우", "주원", "지호", "준서", "현우", "승현"]

    gender = st.session_state.appearance_prefs.get("gender", "여성")
    if gender == "여성":
        return random.choice(first_names_female)
    return random.choice(first_names_male)


def render_affection_bar():
    """Render affection gauge bar."""
    affection = st.session_state.affection
    color = "#ff6b6b" if affection < 30 else "#ffd93d" if affection < 70 else "#6bcb77"

    st.markdown(f"""
    <div style="margin: 10px 0;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
            <span>💔</span>
            <span style="font-weight: bold;">호감도: {affection}/100</span>
            <span>💕</span>
        </div>
        <div style="background-color: #ddd; border-radius: 10px; height: 20px; overflow: hidden;">
            <div style="background-color: {color}; height: 100%; width: {affection}%; transition: width 0.5s;"></div>
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
            f'<div style="text-align: center;"><img src="data:image/png;base64,{img_data}" style="max-width: 300px; border-radius: 10px;"></div>',
            unsafe_allow_html=True
        )
    else:
        st.info("캐릭터 이미지를 불러오는 중...")


def render_start_screen():
    """Render the start/setup screen."""
    st.title("💕 MBTI Matchplay")
    st.markdown("### MBTI 기반 선택형 미연시 게임")
    st.markdown("---")

    # Player name
    st.subheader("당신의 이름은? (성 제외)")
    player_name = st.text_input("이름", key="input_name", placeholder="이름을 입력하세요")

    st.markdown("---")

    # MBTI selection
    st.subheader("상대방의 MBTI를 선택하세요")

    # 랜덤 버튼 콜백
    def random_mbti():
        st.session_state.random_mbti = random.choice(MBTI_TYPES)

    col1, col2 = st.columns([3, 1])
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.button("🎲 랜덤", on_click=random_mbti)

    # 랜덤 값이 있으면 사용
    default_idx = 0
    if "random_mbti" in st.session_state:
        default_idx = MBTI_TYPES.index(st.session_state.random_mbti) + 1

    with col1:
        selected_mbti = st.selectbox("MBTI 선택", options=[""] + MBTI_TYPES, index=default_idx)

    # Show MBTI info
    if selected_mbti:
        traits = load_mbti_traits().get(selected_mbti, {})
        if traits:
            with st.expander(f"{selected_mbti} - {traits.get('name', '')}", expanded=True):
                st.write(f"**말투**: {traits.get('speech_style', '')}")
                st.write(f"**가치관**: {traits.get('values', '')}")
                st.write(f"**좋아하는 것**: {traits.get('likes', '')}")
                st.write(f"**싫어하는 것**: {traits.get('dislikes', '')}")

    st.markdown("---")

    # Appearance preferences
    st.subheader("이상형의 외모를 선택하세요")

    col1, col2 = st.columns(2)
    with col1:
        gender = st.selectbox("성별", GENDER_OPTIONS, key="gender_select")
        face_type = st.selectbox("얼굴상", FACE_OPTIONS, key="face_select")
        hair = st.selectbox("헤어스타일", HAIR_OPTIONS, key="hair_select")
    with col2:
        eyes = st.selectbox("눈", EYE_OPTIONS, key="eyes_select")
        outfit = st.selectbox("옷", OUTFIT_OPTIONS, key="outfit_select")
        atmosphere = st.selectbox("분위기", ATMOSPHERE_OPTIONS, key="atmosphere_select")

    st.markdown("---")

    # Start button
    can_start = player_name and selected_mbti

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

        # Generate character images
        with st.spinner("당신의 이상형을 생성하고 있습니다... 잠시만 기다려주세요 🎨"):
            images = generate_character_images(
                st.session_state.appearance_prefs,
                selected_mbti
            )
            st.session_state.character_images = images

        # Transition to game
        st.session_state.screen = "game"
        st.rerun()

    if not can_start:
        st.warning("이름과 MBTI를 선택해주세요.")


def render_game_screen():
    """Render the main game screen."""
    questions = load_questions()
    mbti_traits = load_mbti_traits()

    # Header
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title(f"💕 {st.session_state.character_name}")
        st.caption(f"MBTI: {st.session_state.mbti} ({mbti_traits[st.session_state.mbti]['name']})")
    with col2:
        total_q = st.session_state.get("total_questions", 12)
        st.markdown(f"**질문 {st.session_state.current_q_idx + 1}/{total_q}**")
    with col3:
        if st.button("🏠 로비로", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Affection bar
    render_affection_bar()

    st.markdown("---")

    # Character image
    render_character_image()

    st.markdown("---")

    # Current question
    q_idx = st.session_state.question_order[st.session_state.current_q_idx]
    question = questions[q_idx]
    player_name = st.session_state.player_name

    # Add player name to question with random suffix (fixed per question)
    if st.session_state.get("current_suffix_idx") != st.session_state.current_q_idx:
        st.session_state.current_suffix = random.choice(["..", "!", "~"])
        st.session_state.current_suffix_idx = st.session_state.current_q_idx
    question_text = f"{player_name}{st.session_state.current_suffix} {question['q']}"
    st.subheader(f"Q{st.session_state.current_q_idx + 1}. {question_text}")

    # Show AI response if available
    if st.session_state.get("show_response", False) and st.session_state.get("last_response", ""):
        expr_name = EXPRESSIONS.get(st.session_state.last_grade, ("neutral", ""))[1]
        st.markdown(f"""
        <div style="background-color: #f0f8ff; padding: 15px; border-radius: 10px; margin: 10px 0; color: #000000;">
            <strong>{st.session_state.character_name}</strong> ({expr_name})<br>
            {st.session_state.last_response}
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
        st.markdown("**선택지:**")
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

    st.title("💕 MBTI Matchplay - 엔딩")
    st.markdown("---")

    # Ending text
    if is_success:
        st.markdown(f"""
        <div style="background-color: #ffe4ec; padding: 30px; border-radius: 15px; text-align: center; margin: 20px 0; color: #000000;">
            <h2 style="color: #000000;">💕 성공 엔딩 💕</h2>
            <p style="font-size: 18px; line-height: 1.8; color: #000000;">
                {char_name}이(가) 환하게 웃으며 {player_name}의 손을 잡았다.<br><br>
                "{player_name}... 너랑 있으면 정말 행복해.<br>
                앞으로도 계속 함께하자, 응?"
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background-color: #f0f0f0; padding: 30px; border-radius: 15px; text-align: center; margin: 20px 0; color: #000000;">
            <h2 style="color: #000000;">💔 실패 엔딩 💔</h2>
            <p style="font-size: 18px; line-height: 1.8; color: #000000;">
                {char_name}이(가) 고개를 돌리며 말했다.<br><br>
                "{player_name}... 우리 여기까지인 것 같아.<br>
                좋은 사람 만나."
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Final stats
    st.markdown("### 📊 게임 결과")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("최종 호감도", f"{st.session_state.affection}/100")
    with col2:
        st.metric("상대 MBTI", st.session_state.mbti)
    with col3:
        st.metric("질문 수", f"{len(st.session_state.log)}개")

    # Choice log summary
    with st.expander("📝 선택 기록 보기"):
        good_count = sum(1 for log in st.session_state.log if log["grade"] == "good")
        ok_count = sum(1 for log in st.session_state.log if log["grade"] == "ok")
        bad_count = sum(1 for log in st.session_state.log if log["grade"] == "bad")

        st.write(f"- 좋은 선택 (활짝): {good_count}회 (+{good_count * 10})")
        st.write(f"- 보통 선택 (미소): {ok_count}회 (+{ok_count * 5})")
        st.write(f"- 나쁜 선택 (삐짐): {bad_count}회 ({bad_count * -10})")

        st.markdown("---")

        for i, log in enumerate(st.session_state.log):
            grade_emoji = "😊" if log["grade"] == "good" else "🙂" if log["grade"] == "ok" else "😤"
            st.write(f"**Q{i+1}.** {log['question']}")
            st.write(f"→ {log['answer']} {grade_emoji} ({log['delta']:+d})")
            st.write("")

    st.markdown("---")

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
