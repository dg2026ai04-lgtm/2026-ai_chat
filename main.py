import streamlit as st
import anthropic
import base64
from datetime import datetime

# ─────────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Claude AI 학습 도우미",
    page_icon="🎓",
    layout="centered"
)

# ─────────────────────────────────────────────
# 세션 상태 초기화
# ─────────────────────────────────────────────
defaults = {
    "chat_history": [],
    "messages_for_api": [],
    "total_input_tokens": 0,
    "total_output_tokens": 0,
    "dark_mode": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
# 현재 연도 & 등급제 판별 함수
# ─────────────────────────────────────────────
CURRENT_YEAR = datetime.now().year  # 2026, 2027, ... 자동 반영

def get_grade_system(age: int) -> str:
    """
    나이(만 나이 기준)를 받아 등급제 반환.
    
    ▸ 2026년 기준
      - 19세 (2008년생, 고3) → 9등급제
      - 18세 이하 (2009년생~, 고2 이하) → 5등급제
    
    ▸ 2027년 이후
      - 모든 나이 → 5등급제
    """
    if CURRENT_YEAR >= 2027:
        return "5등급제"
    # 2026년 기준
    if age >= 19:
        return "9등급제"
    else:
        return "5등급제"

# ─────────────────────────────────────────────
# 고교학점제 / 진로 데이터
# ─────────────────────────────────────────────
CAREER_DATA = {
    "🔬 이공계": {
        "의학/약학/간호": ["의학과", "치의학과", "한의학과", "약학과", "간호학과", "의생명과학과"],
        "컴퓨터/AI/소프트웨어": ["컴퓨터공학과", "소프트웨어학과", "인공지능학과", "데이터사이언스학과", "정보보안학과"],
        "수학/통계": ["수학과", "통계학과", "데이터사이언스학과", "금융수학과"],
        "물리/천문/우주": ["물리학과", "천문학과", "우주항공학과", "핵공학과"],
        "화학/화공": ["화학과", "화학공학과", "신소재공학과", "고분자공학과"],
        "건축/토목/환경": ["건축학과", "건축공학과", "토목공학과", "환경공학과", "도시공학과"],
    },
    "📚 인문/사회계": {
        "법학/행정": ["법학과", "행정학과", "경찰행정학과", "공공정책학과"],
        "경제/경영/무역": ["경제학과", "경영학과", "무역학과", "회계학과", "금융학과"],
        "심리/상담/사회복지": ["심리학과", "상담학과", "사회복지학과", "청소년학과"],
        "교육/사범": ["교육학과", "국어교육과", "영어교육과", "수학교육과", "과학교육과"],
        "언론/미디어": ["언론정보학과", "신문방송학과", "미디어커뮤니케이션학과"],
    },
    "🎨 예체능": {
        "디자인/미술": ["시각디자인학과", "산업디자인학과", "패션디자인학과", "순수미술학과"],
        "음악": ["음악학과", "피아노학과", "성악과", "작곡과", "실용음악학과"],
        "체육/스포츠": ["체육학과", "스포츠과학과", "스포츠의학과"],
    },
    "🔍 탐색 중": {
        "진로 탐색 중": ["미정"],
    }
}

SUBJECTS_STUDY = {
    "국어": "국어 전문 교사로서 문학, 문법, 독해, 작문을 친절하고 정확하게 가르쳐주세요.",
    "영어": "영어 전문 교사로서 문법, 어휘, 독해, 회화, 영작을 친절하고 정확하게 가르쳐주세요.",
    "수학": "수학 전문 교사로서 풀이 과정을 단계별로 자세히 보여주고 개념을 쉽게 설명해주세요.",
    "과학": "과학 전문 교사로서 물리·화학·생물·지구과학의 원리를 쉽게 설명해주세요.",
    "사회": "사회 전문 교사로서 역사·지리·정치·경제·사회문화를 친절하고 정확하게 가르쳐주세요.",
    "정보/코딩": "정보 전문 교사로서 프로그래밍·알고리즘을 쉽게 설명하고 코드 예시를 포함해주세요.",
}

MODELS = {
    "claude-sonnet-4-20250514": {
        "display": "Claude Sonnet 4",
        "icon": "⚡",
        "input_price": 3.0,
        "output_price": 15.0,
    },
    "claude-opus-4-20250514": {
        "display": "Claude Opus 4",
        "icon": "🧠",
        "input_price": 15.0,
        "output_price": 75.0,
    },
}

# ─────────────────────────────────────────────
# 등급제 상세 데이터
# ─────────────────────────────────────────────

# 9등급제: 석차 비율 기준
GRADE_9_INFO = [
    (1, "4% 이하",    "#7c3aed"),
    (2, "4~11%",      "#2563eb"),
    (3, "11~23%",     "#0891b2"),
    (4, "23~40%",     "#059669"),
    (5, "40~60%",     "#65a30d"),
    (6, "60~77%",     "#d97706"),
    (7, "77~89%",     "#ea580c"),
    (8, "89~96%",     "#dc2626"),
    (9, "96~100%",    "#9f1239"),
]

# 5등급제: 성취도(A/B/C/D/E) 기반
GRADE_5_INFO = [
    (1, "A (90점 이상)",         "#7c3aed"),
    (2, "B (80점 이상 ~ 90점 미만)", "#2563eb"),
    (3, "C (70점 이상 ~ 80점 미만)", "#059669"),
    (4, "D (60점 이상 ~ 70점 미만)", "#d97706"),
    (5, "E (60점 미만)",          "#dc2626"),
]

def grade_color_9(g: float) -> str:
    colors = ["#7c3aed","#2563eb","#0891b2","#059669",
              "#65a30d","#d97706","#ea580c","#dc2626","#9f1239"]
    idx = min(max(round(g) - 1, 0), 8)
    return colors[idx]

def grade_color_5(g: float) -> str:
    colors = ["#7c3aed","#2563eb","#059669","#d97706","#dc2626"]
    idx = min(max(round(g) - 1, 0), 4)
    return colors[idx]

def grade_label_9(g: float) -> str:
    labels = {
        1:"1등급 🏆 최상위", 2:"2등급 🥈 상위권",
        3:"3등급 상위권",    4:"4등급 중상위권",
        5:"5등급 중위권",    6:"6등급 중하위권",
        7:"7등급 하위권",    8:"8등급 하위권",
        9:"9등급 최하위",
    }
    return labels.get(round(g), f"{g:.2f}등급")

def grade_label_5(g: float) -> str:
    labels = {
        1:"1등급 🏆 A (최상위)",
        2:"2등급 🥈 B (상위)",
        3:"3등급 C (중위)",
        4:"4등급 D (하위)",
        5:"5등급 E (최하위)",
    }
    return labels.get(round(g), f"{g:.2f}등급")

def bar_pct_9(g: float) -> float:
    """1등급=100%, 9등급=0%"""
    return max(0.0, min(100.0, (9 - g) / 8 * 100))

def bar_pct_5(g: float) -> float:
    """1등급=100%, 5등급=0%"""
    return max(0.0, min(100.0, (5 - g) / 4 * 100))

# ─────────────────────────────────────────────
# 다크/라이트 테마
# ─────────────────────────────────────────────
def get_theme(dark: bool) -> dict:
    if dark:
        return {
            "BG":"#0f1117","CARD":"#1e2130","BORDER":"#2e3250",
            "TEXT":"#e8eaf6","TEXT2":"#9fa8da","MUTED":"#5c6bc0",
            "INPUT":"#1a1f36","INPUT_B":"#3949ab",
            "TAG_BG":"#283593","TAG_T":"#c5cae9","TAG_BD":"#3949ab",
            "USER_BG":"#1a237e","AI_BG":"#1b2838","TOK_BG":"#151929",
            "SUC_BG":"#1b2e22","SUC_BD":"#2e7d32","SUC_T":"#66bb6a",
            "DIV":"#2e3250","HL_BG":"#1a1040","HL_BD":"#4527a0",
        }
    else:
        return {
            "BG":"#f4f6fb","CARD":"#ffffff","BORDER":"#e3e8f0",
            "TEXT":"#1a1a2e","TEXT2":"#5a6a85","MUTED":"#9ca3af",
            "INPUT":"#ffffff","INPUT_B":"#c5cae9",
            "TAG_BG":"#ede7f6","TAG_T":"#4527a0","TAG_BD":"#b39ddb",
            "USER_BG":"#e8eaf6","AI_BG":"#f3e5f5","TOK_BG":"#f8f9fc",
            "SUC_BG":"#f0fdf4","SUC_BD":"#bbf7d0","SUC_T":"#166534",
            "DIV":"#e3e8f0","HL_BG":"#ede7f6","HL_BD":"#ce93d8",
        }

T = get_theme(st.session_state.dark_mode)

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown(f"""
<style>
  .stApp {{ background-color:{T['BG']}; }}

  .main-header {{ text-align:center; padding:1.8rem 0 0.5rem; }}
  .main-header h1 {{
    background:linear-gradient(90deg,#7c3aed,#2563eb);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    font-size:2.2rem; font-weight:900; margin-bottom:0.2rem;
  }}
  .main-header p {{ color:{T['TEXT2']}; font-size:0.93rem; }}

  .card {{
    background:{T['CARD']}; border:1px solid {T['BORDER']};
    border-radius:16px; padding:1.4rem; margin:0.7rem 0;
    box-shadow:0 2px 8px rgba(0,0,0,0.06);
  }}
  .card h3 {{ color:{T['TEXT']}; font-size:1.05rem; margin:0 0 0.9rem; }}

  .career-card {{
    background:{T['HL_BG']}; border:1px solid {T['HL_BD']};
    border-radius:16px; padding:1.4rem; margin:0.7rem 0;
  }}
  .career-card h3 {{ color:{T['TEXT']}; font-size:1.05rem; margin:0 0 0.9rem; }}

  /* 등급제 배너 */
  .grade-system-banner-9 {{
    background:linear-gradient(135deg,#4c1d9520,#1e3a8a20);
    border:2px solid #6d28d9;
    border-radius:14px; padding:1rem 1.2rem; margin:0.7rem 0;
    text-align:center;
  }}
  .grade-system-banner-5 {{
    background:linear-gradient(135deg,#06402020,#065f4620);
    border:2px solid #059669;
    border-radius:14px; padding:1rem 1.2rem; margin:0.7rem 0;
    text-align:center;
  }}
  .banner-title {{ font-size:1.2rem; font-weight:800; margin-bottom:0.2rem; }}
  .banner-sub   {{ color:{T['TEXT2']}; font-size:0.83rem; }}

  .tag {{
    display:inline-block; background:{T['TAG_BG']}; color:{T['TAG_T']};
    border:1px solid {T['TAG_BD']}; border-radius:999px;
    padding:0.2rem 0.75rem; font-size:0.75rem; font-weight:600; margin:0.15rem;
  }}
  .tag-green  {{ background:#e8f5e9; color:#1b5e20; border-color:#a5d6a7; }}
  .tag-blue   {{ background:#e3f2fd; color:#0d47a1; border-color:#90caf9; }}
  .tag-orange {{ background:#fff3e0; color:#e65100; border-color:#ffcc80; }}
  .tag-purple {{ background:#f3e5f5; color:#6a1b9a; border-color:#ce93d8; }}

  .divider {{
    height:1px;
    background:linear-gradient(90deg,transparent,{T['DIV']},transparent);
    border:none; margin:1rem 0;
  }}

  /* 내신 결과 */
  .grade-result {{
    background:linear-gradient(135deg,#7c3aed18,#2563eb18);
    border:2px solid #7c3aed55; border-radius:16px;
    padding:1.5rem; text-align:center; margin:0.8rem 0;
  }}
  .grade-big {{
    font-size:3rem; font-weight:900;
    background:linear-gradient(90deg,#7c3aed,#2563eb);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
  }}
  .grade-label-text {{ color:{T['TEXT2']}; font-size:0.92rem; margin-top:0.3rem; }}
  .grade-bar-wrap {{
    background:{T['BORDER']}; border-radius:999px;
    height:12px; margin:0.9rem 0; overflow:hidden;
  }}
  .grade-bar {{
    height:12px; border-radius:999px;
    transition:width 0.6s ease;
  }}
  .subject-row {{
    background:{T['TOK_BG']}; border:1px solid {T['BORDER']};
    border-radius:10px; padding:0.65rem 1rem; margin:0.3rem 0;
    display:flex; justify-content:space-between; align-items:center;
    color:{T['TEXT']};
  }}

  /* 등급 기준표 */
  .grade-table {{ width:100%; border-collapse:collapse; font-size:0.83rem; }}
  .grade-table th {{
    background:{T['TOK_BG']}; color:{T['TEXT2']};
    padding:0.5rem 0.7rem; text-align:center;
    border:1px solid {T['BORDER']};
  }}
  .grade-table td {{
    padding:0.45rem 0.7rem; text-align:center;
    border:1px solid {T['BORDER']}; color:{T['TEXT']};
  }}

  /* 채팅 */
  .chat-user {{
    background:{T['USER_BG']}; border-left:3px solid #2563eb;
    border-radius:12px; padding:0.85rem 1.1rem; margin:0.35rem 0;
    color:{T['TEXT']};
  }}
  .chat-ai {{
    background:{T['AI_BG']}; border-left:3px solid #7c3aed;
    border-radius:12px; padding:0.85rem 1.1rem; margin:0.35rem 0;
    color:{T['TEXT']};
  }}
  .chat-role {{ font-weight:700; font-size:0.78rem; margin-bottom:0.3rem; }}
  .chat-role-user {{ color:#2563eb; }}
  .chat-role-ai   {{ color:#7c3aed; }}

  /* 토큰 */
  .token-card {{
    background:{T['TOK_BG']}; border:1px solid {T['BORDER']};
    border-radius:12px; padding:0.85rem; text-align:center;
  }}
  .token-card .label {{ color:{T['TEXT2']}; font-size:0.75rem; margin-bottom:0.15rem; }}
  .token-card .value {{ font-size:1.3rem; font-weight:700; }}
  .ti .value {{ color:#2563eb; }}
  .to .value {{ color:#7c3aed; }}
  .tt .value {{ color:#059669; }}
  .tc .value {{ color:#d97706; }}

  .mode-bar {{
    background:{T['TOK_BG']}; border:1px solid {T['BORDER']};
    border-radius:10px; padding:0.55rem 1rem; text-align:center;
    color:{T['TEXT']}; font-weight:600; font-size:0.85rem; margin:0.5rem 0;
  }}
  .success-msg {{
    background:{T['SUC_BG']}; border:1px solid {T['SUC_BD']};
    border-radius:10px; padding:0.65rem 1rem; color:{T['SUC_T']};
    font-weight:600; text-align:center; margin-top:0.5rem;
  }}
  .footer {{
    text-align:center; color:{T['MUTED']};
    font-size:0.76rem; padding:1.5rem 0 1rem;
  }}

  .stTextArea textarea {{
    background:{T['INPUT']} !important; color:{T['TEXT']} !important;
    border:1px solid {T['INPUT_B']} !important; border-radius:10px !important;
  }}
  .stTextArea textarea::placeholder {{ color:{T['MUTED']} !important; }}
  .stRadio label span, .stSelectbox label, .stSlider label {{
    color:{T['TEXT']} !important;
  }}
  div[data-baseweb="select"] > div {{
    background:{T['INPUT']} !important; border-color:{T['INPUT_B']} !important;
    color:{T['TEXT']} !important;
  }}
  .stButton > button[kind="primary"] {{
    background:linear-gradient(90deg,#7c3aed,#2563eb) !important;
    border:none !important; border-radius:10px !important;
    font-weight:700 !important; color:#fff !important;
  }}
  .stButton > button[kind="primary"]:hover {{
    transform:translateY(-1px) !important;
    box-shadow:0 4px 16px rgba(124,58,237,0.35) !important;
  }}
  .stNumberInput input {{
    background:{T['INPUT']} !important; color:{T['TEXT']} !important;
    border-color:{T['INPUT_B']} !important;
  }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# API 키
# ─────────────────────────────────────────────
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except KeyError:
    st.error("❌ Streamlit Secrets에 ANTHROPIC_API_KEY를 추가해주세요.")
    st.stop()

# ─────────────────────────────────────────────
# 헤더
# ─────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>🎓 Claude AI 학습 도우미</h1>
  <p>고교학점제 맞춤 · 내신 계산 · AI 학습을 한 번에!</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 사이드바
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ 설정")

    # 다크모드
    st.markdown("---")
    dark_toggle = st.toggle("🌙 다크 모드", value=st.session_state.dark_mode)
    if dark_toggle != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_toggle
        st.rerun()

    # 모델
    st.markdown("---")
    st.markdown("**🤖 AI 모델**")
    selected_model = st.selectbox(
        "모델", list(MODELS.keys()),
        format_func=lambda k: f"{MODELS[k]['icon']} {MODELS[k]['display']}",
        label_visibility="collapsed"
    )
    model_info = MODELS[selected_model]

    # 나이
    st.markdown("---")
    st.markdown("**🎂 나이 설정**")
    user_age = st.slider("나이", 14, 20, 17, label_visibility="collapsed")

    # 등급제 자동 판별
    grade_system = get_grade_system(user_age)

    if user_age <= 15:
        age_inst = "중학생도 이해할 수 있도록 매우 쉽게 설명해주세요."
    elif user_age <= 17:
        age_inst = "고등학교 1~2학년 수준으로 설명해주세요."
    else:
        age_inst = "고등학교 3학년 수준으로 설명하고, 심화 내용도 포함해도 됩니다."

    st.caption(f"💡 {user_age}세 → **{grade_system}** 적용")

    # 진로/학과
    st.markdown("---")
    st.markdown("**🎓 진로 & 희망 학과 설정**")
    st.caption("모든 모드에서 진로 맞춤 답변에 활용됩니다!")

    career_category = st.selectbox(
        "계열", list(CAREER_DATA.keys()), label_visibility="collapsed"
    )
    career_field = st.selectbox(
        "세부 진로",
        list(CAREER_DATA[career_category].keys()),
        label_visibility="collapsed"
    )
    dept_list = CAREER_DATA[career_category][career_field]
    dept_choice = st.selectbox(
        "희망 학과", ["직접 입력"] + dept_list, label_visibility="collapsed"
    )
    if dept_choice == "직접 입력":
        custom_dept = st.text_input("희망 학과 직접 입력", placeholder="예: 바이오메디컬공학과")
        final_dept = custom_dept.strip() if custom_dept.strip() else "미정"
    else:
        final_dept = dept_choice

    st.caption(f"📌 {career_field} → {final_dept}")

    # 앱 모드
    st.markdown("---")
    st.markdown("**📱 앱 모드**")
    app_mode = st.radio(
        "모드",
        ["💬 일반 모드", "📚 학습 모드", "🎓 고교학점제 모드"],
        label_visibility="collapsed"
    )

    selected_subject = "국어"
    learning_feature = "💬 질문하기"
    quiz_difficulty = "보통"
    if app_mode == "📚 학습 모드":
        st.markdown("---")
        st.markdown("**📖 과목**")
        selected_subject = st.selectbox(
            "과목", list(SUBJECTS_STUDY.keys()), label_visibility="collapsed"
        )
        st.markdown("**🎯 기능**")
        learning_feature = st.radio(
            "기능",
            ["💬 질문하기", "📝 퀴즈 모드", "📊 내신 계산기"],
            label_visibility="collapsed"
        )
        if learning_feature == "📝 퀴즈 모드":
            quiz_difficulty = st.selectbox("퀴즈 난이도", ["쉬움", "보통", "어려움"])

    hschool_feature = "💬 진로 맞춤 질문"
    if app_mode == "🎓 고교학점제 모드":
        st.markdown("---")
        st.markdown("**🎯 기능**")
        hschool_feature = st.radio(
            "기능",
            ["💬 진로 맞춤 질문", "📘 추천 과목 안내",
             "📝 생기부 주제 추천", "🏃 활동 추천"],
            label_visibility="collapsed"
        )

    # 대화 관리
    st.markdown("---")
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.messages_for_api = []
        st.session_state.total_input_tokens = 0
        st.session_state.total_output_tokens = 0
        st.rerun()

    if st.session_state.chat_history:
        chat_export = "\n\n".join(
            f"[{'나' if m['role']=='user' else 'AI'}]\n{m['content']}"
            for m in st.session_state.chat_history
        )
        st.download_button(
            "📥 대화 내보내기", chat_export,
            file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain", use_container_width=True
        )

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 유틸 함수
# ─────────────────────────────────────────────
def calc_cost(in_t, out_t, model_key):
    m = MODELS[model_key]
    return (in_t/1_000_000)*m["input_price"] + (out_t/1_000_000)*m["output_price"]

def encode_image(f):
    b64 = base64.standard_b64encode(f.getvalue()).decode()
    mime = f.type if f.type in ["image/jpeg","image/png","image/gif","image/webp"] else "image/png"
    return b64, mime

def build_system_prompt(extra_context: str = ""):
    career_context = (
        f"학생의 희망 진로: {career_field}\n"
        f"학생의 희망 학과: {final_dept}\n"
        f"계열: {career_category}\n"
        f"나이: {user_age}세\n"
        f"적용 내신 등급제: {grade_system}\n\n"
        f"답변 시 이 진로와 학과를 자연스럽게 연결 지어 설명해주세요. "
        f"단, 진로와 무관한 질문이라면 억지로 연결하지 않아도 됩니다."
    )
    age_context = f"사용자는 {user_age}세 고등학생입니다. {age_inst}"

    if app_mode == "💬 일반 모드":
        role = "당신은 친절하고 유능한 AI 학습 도우미입니다."
    elif app_mode == "📚 학습 모드":
        if learning_feature == "💬 질문하기":
            role = SUBJECTS_STUDY[selected_subject]
        elif learning_feature == "📝 퀴즈 모드":
            diff_map = {"쉬움":"기초적인","보통":"중간 난이도의","어려움":"심화된"}
            role = (
                f"{SUBJECTS_STUDY[selected_subject]} "
                f"퀴즈 출제자로서 '문제 내줘'라고 하면 {diff_map[quiz_difficulty]} "
                f"문제를 1개 출제하세요. 정답 확인 후 해설 제공 및 점수 추적을 해주세요."
            )
        else:
            role = "당신은 친절한 AI 학습 도우미입니다."
    elif app_mode == "🎓 고교학점제 모드":
        role = (
            f"당신은 고교학점제 전문 진로 상담 교사입니다. "
            f"학생의 진로({career_field})와 희망 학과({final_dept})에 맞게 "
            f"과목 선택, 생기부 작성, 활동 계획, 대학 입시 전략을 "
            f"구체적이고 유연하게 안내해주세요."
        )
    else:
        role = "당신은 친절한 AI 학습 도우미입니다."

    parts = [age_context, career_context, role]
    if extra_context:
        parts.append(extra_context)
    parts.append("한국어로 답변해주세요.")
    return "\n\n".join(parts)

def call_ai(user_text: str, system_override: str = None, one_shot: bool = False):
    client = anthropic.Anthropic(api_key=api_key)
    system = system_override or build_system_prompt()
    messages = (
        [{"role":"user","content":user_text}]
        if one_shot
        else st.session_state.messages_for_api + [{"role":"user","content":user_text}]
    )
    response = client.messages.create(
        model=selected_model, max_tokens=4096,
        system=system, messages=messages
    )
    return (
        response.content[0].text,
        response.usage.input_tokens,
        response.usage.output_tokens,
    )

# ─────────────────────────────────────────────
# 모드 인디케이터
# ─────────────────────────────────────────────
# 등급제 배지
gs_badge = (
    f'<span class="tag tag-purple">📊 {grade_system}</span>'
)

if app_mode == "💬 일반 모드":
    mode_text = f"💬 일반 모드 | {model_info['icon']} {model_info['display']} | 🎂 {user_age}세 | 🎓 {career_field} → {final_dept}"
elif app_mode == "📚 학습 모드":
    mode_text = f"📚 학습 모드 | 📖 {selected_subject} | 🎯 {learning_feature} | 🎂 {user_age}세 | 🎓 {final_dept}"
else:
    mode_text = f"🎓 고교학점제 | 🔍 {career_field} | 🏫 {final_dept} | 🎂 {user_age}세"

st.markdown(f'<div class="mode-bar">{mode_text} | 📊 {grade_system}</div>', unsafe_allow_html=True)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# 📊 내신 계산기
# ═══════════════════════════════════════════════════════════
if app_mode == "📚 학습 모드" and learning_feature == "📊 내신 계산기":

    # ── 등급제 배너 ──
    if grade_system == "9등급제":
        st.markdown(f"""
        <div class="grade-system-banner-9">
            <div class="banner-title" style="color:#7c3aed;">📊 9등급제 (석차등급제)</div>
            <div class="banner-sub">
                2008년생 이전 (현재 {CURRENT_YEAR}년 기준 19세 이상) · 상대평가<br>
                석차 백분율에 따라 1~9등급으로 산출
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="grade-system-banner-5">
            <div class="banner-title" style="color:#059669;">📊 5등급제 (성취도등급제)</div>
            <div class="banner-sub">
                2009년생 이후 (현재 {CURRENT_YEAR}년 기준 18세 이하) · 절대평가<br>
                {'2027년부터 전 학년 5등급제 적용' if CURRENT_YEAR >= 2027 else ''}<br>
                성취도(A/B/C/D/E)에 따라 1~5등급으로 산출
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="card"><h3>📊 내신 등급 계산기</h3>', unsafe_allow_html=True)

    # ── 등급 기준표 ──
    with st.expander(f"📌 {grade_system} 기준표 보기"):
        if grade_system == "9등급제":
            rows = "".join([
                f"<tr><td><b style='color:{c}'>{g}등급</b></td>"
                f"<td>{r}</td></tr>"
                for g, r, c in GRADE_9_INFO
            ])
            st.markdown(f"""
            <table class="grade-table">
              <tr><th>등급</th><th>석차 비율</th></tr>
              {rows}
            </table>
            <p style="color:{T['TEXT2']}; font-size:0.8rem; margin-top:0.6rem;">
            ※ 동점자가 있을 경우 동점자 모두 상위 등급 처리
            </p>
            """, unsafe_allow_html=True)
        else:
            rows = "".join([
                f"<tr><td><b style='color:{c}'>{g}등급</b></td>"
                f"<td>{r}</td></tr>"
                for g, r, c in GRADE_5_INFO
            ])
            st.markdown(f"""
            <table class="grade-table">
              <tr><th>등급</th><th>성취도 기준</th></tr>
              {rows}
            </table>
            <p style="color:{T['TEXT2']}; font-size:0.8rem; margin-top:0.6rem;">
            ※ 5등급제는 절대평가로, 원점수 기준으로 등급이 결정됩니다.<br>
            ※ 단위수(학점)를 반영한 가중 평균으로 평균 등급을 계산합니다.
            </p>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # ── 계산 방식 안내 ──
    if grade_system == "9등급제":
        st.markdown(f"""
        <p style="color:{T['TEXT2']}; font-size:0.86rem; margin-bottom:0.8rem;">
        ✅ <b>계산 방식:</b> (각 과목 등급 × 단위수)의 합 ÷ 총 단위수 = 평균 등급<br>
        📌 국어·수학·영어·사회·과학 등 <b>석차등급이 산출되는 과목</b>을 입력하세요.<br>
        ⚠️ 체육·예술·교양 등 성취도(A/B/C)만 나오는 과목은 제외됩니다.
        </p>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <p style="color:{T['TEXT2']}; font-size:0.86rem; margin-bottom:0.8rem;">
        ✅ <b>계산 방식:</b> (각 과목 등급 × 단위수)의 합 ÷ 총 단위수 = 평균 등급<br>
        📌 <b>1등급(A)=90점 이상, 2등급(B)=80점대, 3등급(C)=70점대,<br>
        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;4등급(D)=60점대, 5등급(E)=60점 미만</b><br>
        ⚠️ 진로선택 과목은 A/B/C만 나오므로 별도 관리 필요합니다.
        </p>
        """, unsafe_allow_html=True)

    # ── 과목 입력 ──
    st.markdown(f"**과목 입력**")
    num_subjects = st.number_input(
        "입력할 과목 수", min_value=1, max_value=20, value=5, step=1
    )

    c_h1, c_h2, c_h3 = st.columns([3, 2, 2])
    c_h1.markdown(f"<b style='color:{T['TEXT']}'>과목명</b>", unsafe_allow_html=True)
    c_h2.markdown(f"<b style='color:{T['TEXT']}'>단위수</b>", unsafe_allow_html=True)
    max_grade = 9 if grade_system == "9등급제" else 5
    c_h3.markdown(
        f"<b style='color:{T['TEXT']}'>등급 (1~{max_grade})</b>",
        unsafe_allow_html=True
    )

    subject_entries = []
    for i in range(int(num_subjects)):
        c1, c2, c3 = st.columns([3, 2, 2])
        with c1:
            sname = st.text_input(
                f"과목_{i}", placeholder=f"예: 국어",
                key=f"sname_{i}", label_visibility="collapsed"
            )
        with c2:
            unit = st.number_input(
                f"단위_{i}", min_value=1, max_value=8, value=3,
                key=f"unit_{i}", label_visibility="collapsed"
            )
        with c3:
            grade = st.number_input(
                f"등급_{i}", min_value=1, max_value=max_grade, value=min(3, max_grade),
                key=f"grade_{i}", label_visibility="collapsed"
            )
        if sname.strip():
            subject_entries.append({
                "name": sname.strip(),
                "unit": int(unit),
                "grade": int(grade),
            })

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 계산 버튼 ──
    if st.button("🔢 내신 계산하기", type="primary", use_container_width=True):
        if not subject_entries:
            st.warning("⚠️ 과목명을 하나 이상 입력해주세요!")
        else:
            total_units  = sum(s["unit"]           for s in subject_entries)
            weighted_sum = sum(s["grade"]*s["unit"] for s in subject_entries)
            avg_grade    = weighted_sum / total_units

            # 등급제별 표시
            if grade_system == "9등급제":
                bar_pct   = bar_pct_9(avg_grade)
                bar_color = grade_color_9(avg_grade)
                glabel    = grade_label_9(avg_grade)
                max_g     = 9
            else:
                bar_pct   = bar_pct_5(avg_grade)
                bar_color = grade_color_5(avg_grade)
                glabel    = grade_label_5(avg_grade)
                max_g     = 5

            # 결과 카드
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="grade-result">
                <div style="color:{T['TEXT2']}; font-size:0.8rem; margin-bottom:0.3rem;">
                    📊 {grade_system} 기준
                </div>
                <div class="grade-big">{avg_grade:.2f}등급</div>
                <div class="grade-label-text">{glabel}</div>
                <div class="grade-bar-wrap">
                    <div class="grade-bar"
                         style="width:{bar_pct:.1f}%; background:{bar_color};"></div>
                </div>
                <div style="color:{T['TEXT2']}; font-size:0.82rem;">
                    총 단위수: {total_units}단위 &nbsp;|&nbsp;
                    등급×단위 합계: {weighted_sum} &nbsp;|&nbsp;
                    최고 {max_g}등급 기준
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 과목별 상세
            st.markdown(
                f"<div style='color:{T['TEXT2']}; font-size:0.82rem; "
                f"font-weight:700; margin:0.8rem 0 0.4rem;'>📋 과목별 상세</div>",
                unsafe_allow_html=True
            )
            for s in subject_entries:
                gc = grade_color_9(s["grade"]) if grade_system=="9등급제" else grade_color_5(s["grade"])
                st.markdown(f"""
                <div class="subject-row">
                    <span><b>{s['name']}</b></span>
                    <span style="color:{T['TEXT2']};">{s['unit']}단위</span>
                    <span><b style="color:{gc};">{s['grade']}등급</b></span>
                    <span style="color:{T['MUTED']}; font-size:0.8rem;">
                        {s['grade']*s['unit']}점
                    </span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

            # ── AI 분석 ──
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            with st.spinner("🤖 AI가 내신을 분석하고 진로 맞춤 피드백을 생성하는 중..."):

                subject_summary = "\n".join(
                    f"- {s['name']}: {s['unit']}단위 {s['grade']}등급"
                    for s in subject_entries
                )

                # 등급제별 분석 기준 설명
                if grade_system == "9등급제":
                    grade_system_desc = (
                        "9등급 상대평가 석차등급제입니다. "
                        "1등급(상위 4%), 2등급(상위 11%), 3등급(상위 23%) 기준으로 분석해주세요. "
                        "수시 학생부교과전형은 보통 1~2등급대를 요구합니다."
                    )
                else:
                    grade_system_desc = (
                        "5등급 절대평가 성취도등급제입니다. "
                        "1등급(90점 이상/A), 2등급(80점대/B), 3등급(70점대/C) 기준으로 분석해주세요. "
                        "2025 개정 교육과정 적용 학생으로, 대학별 반영 방식이 다를 수 있음을 안내해주세요."
                    )

                analysis_prompt = f"""
학생 정보:
- 나이: {user_age}세
- 적용 내신 등급제: {grade_system}
- 희망 진로: {career_field}
- 희망 학과: {final_dept}
- 계열: {career_category}

현재 내신 성적:
{subject_summary}

계산된 평균 내신 등급: {avg_grade:.2f}등급 ({grade_system} 기준)

[등급제 분석 기준]
{grade_system_desc}

위 정보를 바탕으로 다음을 분석해주세요:

1. **현재 내신 수준 평가**
   - {grade_system} 기준으로 {avg_grade:.2f}등급의 의미를 설명해주세요.
   - {final_dept} 목표 시 현재 성적이 충분한지 솔직하게 평가해주세요.

2. **과목별 분석**
   - 잘하는 과목과 개선이 필요한 과목을 분석해주세요.
   - {career_field} 진로에서 특히 중요한 과목을 강조해주세요.

3. **목표 등급 제시**
   - {final_dept} 진학을 위한 목표 등급을 구체적으로 알려주세요.
   - 어느 과목에서 몇 등급을 올리면 평균이 어떻게 변하는지 알려주세요.

4. **학습 전략 추천**
   - {user_age}세 학생에게 맞는 구체적인 학습 전략을 제안해주세요.
   - {career_field} 진로와 연결된 공부 방향도 안내해주세요.

5. **격려 메시지**
   - 학생의 상황에 맞는 진심 어린 응원 메시지를 남겨주세요.

정해진 틀 없이, 이 학생의 상황에 맞는 유연하고 따뜻한 조언을 부탁드립니다.
"""
                try:
                    ai_system = (
                        f"당신은 고등학교 내신 분석 전문가이자 진로 상담 교사입니다. "
                        f"학생에게 적용되는 등급제({grade_system})를 정확히 이해하고 분석해주세요. "
                        f"학생의 진로({career_field})와 희망 학과({final_dept})를 깊이 이해하고 "
                        f"현실적이면서도 따뜻한 조언을 해주세요. "
                        f"한국 대학 입시 제도(수시·정시·학생부교과전형 등)를 정확히 이해하고 답변해주세요. "
                        f"한국어로 답변해주세요."
                    )
                    answer, in_tok, out_tok = call_ai(
                        analysis_prompt, system_override=ai_system, one_shot=True
                    )
                    st.session_state.total_input_tokens  += in_tok
                    st.session_state.total_output_tokens += out_tok

                    st.markdown(
                        '<div class="card"><h3>🤖 AI 내신 분석 & 진로 맞춤 피드백</h3>',
                        unsafe_allow_html=True
                    )
                    st.markdown(answer)
                    st.markdown('</div>', unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"AI 분석 중 오류 발생: {e}")

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="footer">🔒 API 키는 Streamlit Secrets로 안전하게 관리됩니다<br>'
        f'📌 당곡고등학교 AI 학습 도우미</div>',
        unsafe_allow_html=True
    )
    st.stop()

# ═══════════════════════════════════════════════════════════
# 🎓 고교학점제 모드 — 진로 카드
# ═══════════════════════════════════════════════════════════
if app_mode == "🎓 고교학점제 모드":
    st.markdown(f"""
    <div class="career-card">
        <h3>🎓 나의 진로 설정</h3>
        <span class="tag tag-blue">📂 {career_category}</span>
        <span class="tag tag-blue">🔍 {career_field}</span>
        <span class="tag tag-orange">🏫 {final_dept}</span>
        <span class="tag">🎂 {user_age}세</span>
        <span class="tag tag-purple">📊 {grade_system}</span>
        <p style="color:{T['TEXT2']}; font-size:0.82rem; margin-top:0.7rem; margin-bottom:0;">
        💡 아래 채팅에서 진로·학과에 맞는 맞춤형 AI 답변을 받을 수 있습니다!
        </p>
    </div>
    """, unsafe_allow_html=True)

    feature_guide = {
        "💬 진로 맞춤 질문": f"'{career_field}' 분야나 '{final_dept}' 입시에 관해 무엇이든 물어보세요!",
        "📘 추천 과목 안내": f"고교학점제에서 '{final_dept}' 진학에 유리한 과목을 물어보세요!",
        "📝 생기부 주제 추천": f"'{career_field}' 관련 생기부 보고서 주제 추천을 받아보세요!",
        "🏃 활동 추천": f"'{final_dept}' 입시에 도움되는 비교과 활동을 추천받아보세요!",
    }
    st.markdown(f"""
    <div style="background:{T['TOK_BG']}; border:1px solid {T['BORDER']};
                border-radius:12px; padding:0.9rem 1.1rem; margin:0.5rem 0;">
        <span style="color:{T['TEXT2']}; font-size:0.88rem;">
        💬 {feature_guide.get(hschool_feature, '질문을 입력해주세요!')}
        </span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# 💬 대화 기록
# ═══════════════════════════════════════════════════════════
if st.session_state.chat_history:
    st.markdown('<div class="card"><h3>💬 대화 기록</h3>', unsafe_allow_html=True)
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="chat-user">'
                f'<div class="chat-role chat-role-user">👤 나</div>'
                f'{msg.get("display_content", msg["content"])}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="chat-ai">'
                f'<div class="chat-role chat-role-ai">🤖 AI</div>'
                f'{msg["content"]}</div>',
                unsafe_allow_html=True
            )
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# 📎 이미지 업로드 + 💬 질문
# ═══════════════════════════════════════════════════════════
st.markdown('<div class="card"><h3>📎 이미지 업로드 (선택)</h3>', unsafe_allow_html=True)
uploaded_image = st.file_uploader(
    "이미지", type=["png","jpg","jpeg","gif","webp"],
    label_visibility="collapsed"
)
if uploaded_image:
    st.image(uploaded_image, caption="업로드된 이미지", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# 플레이스홀더
extra_context_for_prompt = ""
if app_mode == "🎓 고교학점제 모드":
    ph_map = {
        "💬 진로 맞춤 질문": f"예: {career_field} 분야에서 고등학교 때 뭘 준비해야 할까요?",
        "📘 추천 과목 안내": f"예: {final_dept} 가려면 어떤 과목을 들어야 하나요?",
        "📝 생기부 주제 추천": f"예: {career_field} 관련 탐구 주제 추천해줘",
        "🏃 활동 추천": f"예: {final_dept} 입시에 도움되는 동아리 추천해줘",
    }
    placeholder = ph_map.get(hschool_feature, "질문을 입력하세요")
    card_title  = f"🎓 {hschool_feature}"
    feature_ctx = {
        "📘 추천 과목 안내": (
            f"학생이 고교학점제에서 어떤 과목을 선택하면 좋을지 묻고 있습니다. "
            f"{career_field} 진로와 {final_dept} 입시에 맞는 과목을 추천하고 이유를 설명해주세요."
        ),
        "📝 생기부 주제 추천": (
            f"학생이 생기부에 기록할 탐구 주제를 요청하고 있습니다. "
            f"{career_field}와 {final_dept} 관련성이 높고 실제로 탐구 가능한 주제를 여러 개 제안해주세요."
        ),
        "🏃 활동 추천": (
            f"학생이 비교과 활동 추천을 요청하고 있습니다. "
            f"{career_field} 진로와 {final_dept} 입시에 도움되는 동아리·봉사·대회 등을 추천해주세요."
        ),
    }
    extra_context_for_prompt = feature_ctx.get(hschool_feature, "")
elif app_mode == "📚 학습 모드" and learning_feature == "📝 퀴즈 모드":
    placeholder = "퀴즈를 시작하려면 '문제 내줘'라고 입력하세요!"
    card_title  = "📝 퀴즈"
else:
    placeholder = "무엇이든 질문해보세요! (진로 맞춤 답변을 드립니다)"
    card_title  = "💬 질문 입력"

st.markdown(f'<div class="card"><h3>{card_title}</h3>', unsafe_allow_html=True)
user_question = st.text_area(
    "질문", placeholder=placeholder,
    height=120, label_visibility="collapsed"
)
st.markdown('</div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
# 🔍 전송
# ═══════════════════════════════════════════════════════════
if st.button("🔍  AI에게 질문하기", type="primary", use_container_width=True):
    if not user_question.strip() and not uploaded_image:
        st.warning("⚠️ 질문을 입력하거나 이미지를 업로드해주세요!")
    else:
        with st.spinner("🤔 AI가 답변을 생성하는 중..."):
            try:
                user_content = []
                display_text = user_question.strip() if user_question.strip() else "(이미지만 전송)"

                if uploaded_image:
                    b64_img, mime = encode_image(uploaded_image)
                    user_content.append({
                        "type": "image",
                        "source": {"type":"base64","media_type":mime,"data":b64_img}
                    })
                    display_text = (
                        f"📎 [이미지] {user_question}"
                        if user_question.strip() else "📎 [이미지만 전송]"
                    )

                text_to_send = user_question.strip() if user_question.strip() else "이 이미지에 대해 설명해주세요."
                user_content.append({"type":"text","text":text_to_send})

                st.session_state.chat_history.append({
                    "role": "user",
                    "content": text_to_send,
                    "display_content": display_text,
                })
                st.session_state.messages_for_api.append({
                    "role": "user", "content": user_content
                })

                client = anthropic.Anthropic(api_key=api_key)
                response = client.messages.create(
                    model=selected_model, max_tokens=4096,
                    system=build_system_prompt(extra_context=extra_context_for_prompt),
                    messages=st.session_state.messages_for_api
                )
                answer  = response.content[0].text
                in_tok  = response.usage.input_tokens
                out_tok = response.usage.output_tokens

                st.session_state.total_input_tokens  += in_tok
                st.session_state.total_output_tokens += out_tok
                st.session_state.chat_history.append({"
