import streamlit as st
import anthropic
import base64
from datetime import datetime

st.set_page_config(page_title="Claude AI 학습 도우미", page_icon="🎓", layout="centered")

# 세션 초기화
for k, v in {
    "chat_history": [], "messages_for_api": [],
    "total_input_tokens": 0, "total_output_tokens": 0, "dark_mode": False
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

CURRENT_YEAR = datetime.now().year

def get_grade_system(age):
    if CURRENT_YEAR >= 2027:
        return "5등급제"
    if age >= 19:
        return "9등급제"
    return "5등급제"

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
    "과학": "과학 전문 교사로서 물리 화학 생물 지구과학의 원리를 쉽게 설명해주세요.",
    "사회": "사회 전문 교사로서 역사 지리 정치 경제 사회문화를 친절하고 정확하게 가르쳐주세요.",
    "정보/코딩": "정보 전문 교사로서 프로그래밍 알고리즘을 쉽게 설명하고 코드 예시를 포함해주세요.",
}

MODELS = {
    "claude-sonnet-4-20250514": {"display": "Claude Sonnet 4", "icon": "⚡", "input_price": 3.0, "output_price": 15.0},
    "claude-opus-4-20250514": {"display": "Claude Opus 4", "icon": "🧠", "input_price": 15.0, "output_price": 75.0},
}

GRADE_9_INFO = [
    (1, "4% 이하", "#7c3aed"), (2, "4~11%", "#2563eb"), (3, "11~23%", "#0891b2"),
    (4, "23~40%", "#059669"), (5, "40~60%", "#65a30d"), (6, "60~77%", "#d97706"),
    (7, "77~89%", "#ea580c"), (8, "89~96%", "#dc2626"), (9, "96~100%", "#9f1239"),
]

GRADE_5_INFO = [
    (1, "A (90점 이상)", "#7c3aed"), (2, "B (80~89점)", "#2563eb"),
    (3, "C (70~79점)", "#059669"), (4, "D (60~69점)", "#d97706"),
    (5, "E (60점 미만)", "#dc2626"),
]

def grade_color_9(g):
    c = ["#7c3aed","#2563eb","#0891b2","#059669","#65a30d","#d97706","#ea580c","#dc2626","#9f1239"]
    return c[min(max(round(g)-1,0),8)]

def grade_color_5(g):
    c = ["#7c3aed","#2563eb","#059669","#d97706","#dc2626"]
    return c[min(max(round(g)-1,0),4)]

def grade_label_9(g):
    labels = {1:"1등급 🏆 최상위",2:"2등급 🥈 상위권",3:"3등급 상위권",4:"4등급 중상위권",5:"5등급 중위권",6:"6등급 중하위권",7:"7등급 하위권",8:"8등급 하위권",9:"9등급 최하위"}
    return labels.get(round(g), f"{g:.2f}등급")

def grade_label_5(g):
    labels = {1:"1등급 🏆 A 최상위",2:"2등급 🥈 B 상위",3:"3등급 C 중위",4:"4등급 D 하위",5:"5등급 E 최하위"}
    return labels.get(round(g), f"{g:.2f}등급")

# 테마
def get_theme(dark):
    if dark:
        return dict(BG="#0f1117",CARD="#1e2130",BORDER="#2e3250",TEXT="#e8eaf6",TEXT2="#9fa8da",MUTED="#5c6bc0",INPUT="#1a1f36",INPUT_B="#3949ab",TAG_BG="#283593",TAG_T="#c5cae9",TAG_BD="#3949ab",USER_BG="#1a237e",AI_BG="#1b2838",TOK_BG="#151929",SUC_BG="#1b2e22",SUC_BD="#2e7d32",SUC_T="#66bb6a",DIV="#2e3250",HL_BG="#1a1040",HL_BD="#4527a0")
    return dict(BG="#f4f6fb",CARD="#ffffff",BORDER="#e3e8f0",TEXT="#1a1a2e",TEXT2="#5a6a85",MUTED="#9ca3af",INPUT="#ffffff",INPUT_B="#c5cae9",TAG_BG="#ede7f6",TAG_T="#4527a0",TAG_BD="#b39ddb",USER_BG="#e8eaf6",AI_BG="#f3e5f5",TOK_BG="#f8f9fc",SUC_BG="#f0fdf4",SUC_BD="#bbf7d0",SUC_T="#166534",DIV="#e3e8f0",HL_BG="#ede7f6",HL_BD="#ce93d8")

T = get_theme(st.session_state.dark_mode)

st.markdown(f"""
<style>
.stApp{{background-color:{T['BG']};}}
.main-header{{text-align:center;padding:1.8rem 0 0.5rem;}}
.main-header h1{{background:linear-gradient(90deg,#7c3aed,#2563eb);-webkit-background-clip:text;-webkit-text-fill-color:transparent;font-size:2.2rem;font-weight:900;margin-bottom:0.2rem;}}
.main-header p{{color:{T['TEXT2']};font-size:0.93rem;}}
.card{{background:{T['CARD']};border:1px solid {T['BORDER']};border-radius:16px;padding:1.4rem;margin:0.7rem 0;box-shadow:0 2px 8px rgba(0,0,0,0.06);}}
.card h3{{color:{T['TEXT']};font-size:1.05rem;margin:0 0 0.9rem;}}
.career-card{{background:{T['HL_BG']};border:1px solid {T['HL_BD']};border-radius:16px;padding:1.4rem;margin:0.7rem 0;}}
.career-card h3{{color:{T['TEXT']};font-size:1.05rem;margin:0 0 0.9rem;}}
.grade-system-banner-9{{background:linear-gradient(135deg,#4c1d9520,#1e3a8a20);border:2px solid #6d28d9;border-radius:14px;padding:1rem 1.2rem;margin:0.7rem 0;text-align:center;}}
.grade-system-banner-5{{background:linear-gradient(135deg,#06402020,#065f4620);border:2px solid #059669;border-radius:14px;padding:1rem 1.2rem;margin:0.7rem 0;text-align:center;}}
.banner-title{{font-size:1.2rem;font-weight:800;margin-bottom:0.2rem;}}
.banner-sub{{color:{T['TEXT2']};font-size:0.83rem;}}
.tag{{display:inline-block;background:{T['TAG_BG']};color:{T['TAG_T']};border:1px solid {T['TAG_BD']};border-radius:999px;padding:0.2rem 0.75rem;font-size:0.75rem;font-weight:600;margin:0.15rem;}}
.tag-green{{background:#e8f5e9;color:#1b5e20;border-color:#a5d6a7;}}
.tag-blue{{background:#e3f2fd;color:#0d47a1;border-color:#90caf9;}}
.tag-orange{{background:#fff3e0;color:#e65100;border-color:#ffcc80;}}
.tag-purple{{background:#f3e5f5;color:#6a1b9a;border-color:#ce93d8;}}
.divider{{height:1px;background:linear-gradient(90deg,transparent,{T['DIV']},transparent);border:none;margin:1rem 0;}}
.grade-result{{background:linear-gradient(135deg,#7c3aed18,#2563eb18);border:2px solid #7c3aed55;border-radius:16px;padding:1.5rem;text-align:center;margin:0.8rem 0;}}
.grade-big{{font-size:3rem;font-weight:900;background:linear-gradient(90deg,#7c3aed,#2563eb);-webkit-background-clip:text;-webkit-text-fill-color:transparent;}}
.grade-label-text{{color:{T['TEXT2']};font-size:0.92rem;margin-top:0.3rem;}}
.grade-bar-wrap{{background:{T['BORDER']};border-radius:999px;height:12px;margin:0.9rem 0;overflow:hidden;}}
.grade-bar{{height:12px;border-radius:999px;transition:width 0.6s ease;}}
.subject-row{{background:{T['TOK_BG']};border:1px solid {T['BORDER']};border-radius:10px;padding:0.65rem 1rem;margin:0.3rem 0;display:flex;justify-content:space-between;align-items:center;color:{T['TEXT']};}}
.grade-table{{width:100%;border-collapse:collapse;font-size:0.83rem;}}
.grade-table th{{background:{T['TOK_BG']};color:{T['TEXT2']};padding:0.5rem 0.7rem;text-align:center;border:1px solid {T['BORDER']};}}
.grade-table td{{padding:0.45rem 0.7rem;text-align:center;border:1px solid {T['BORDER']};color:{T['TEXT']};}}
.chat-user{{background:{T['USER_BG']};border-left:3px solid #2563eb;border-radius:12px;padding:0.85rem 1.1rem;margin:0.35rem 0;color:{T['TEXT']};}}
.chat-ai{{background:{T['AI_BG']};border-left:3px solid #7c3aed;border-radius:12px;padding:0.85rem 1.1rem;margin:0.35rem 0;color:{T['TEXT']};}}
.chat-role{{font-weight:700;font-size:0.78rem;margin-bottom:0.3rem;}}
.chat-role-user{{color:#2563eb;}}
.chat-role-ai{{color:#7c3aed;}}
.token-card{{background:{T['TOK_BG']};border:1px solid {T['BORDER']};border-radius:12px;padding:0.85rem;text-align:center;}}
.token-card .label{{color:{T['TEXT2']};font-size:0.75rem;margin-bottom:0.15rem;}}
.token-card .value{{font-size:1.3rem;font-weight:700;}}
.ti .value{{color:#2563eb;}}
.to .value{{color:#7c3aed;}}
.tt .value{{color:#059669;}}
.tc .value{{color:#d97706;}}
.mode-bar{{background:{T['TOK_BG']};border:1px solid {T['BORDER']};border-radius:10px;padding:0.55rem 1rem;text-align:center;color:{T['TEXT']};font-weight:600;font-size:0.85rem;margin:0.5rem 0;}}
.success-msg{{background:{T['SUC_BG']};border:1px solid {T['SUC_BD']};border-radius:10px;padding:0.65rem 1rem;color:{T['SUC_T']};font-weight:600;text-align:center;margin-top:0.5rem;}}
.footer{{text-align:center;color:{T['MUTED']};font-size:0.76rem;padding:1.5rem 0 1rem;}}
.stTextArea textarea{{background:{T['INPUT']} !important;color:{T['TEXT']} !important;border:1px solid {T['INPUT_B']} !important;border-radius:10px !important;}}
.stTextArea textarea::placeholder{{color:{T['MUTED']} !important;}}
.stRadio label span,.stSelectbox label,.stSlider label{{color:{T['TEXT']} !important;}}
div[data-baseweb="select"]>div{{background:{T['INPUT']} !important;border-color:{T['INPUT_B']} !important;color:{T['TEXT']} !important;}}
.stButton>button[kind="primary"]{{background:linear-gradient(90deg,#7c3aed,#2563eb) !important;border:none !important;border-radius:10px !important;font-weight:700 !important;color:#fff !important;}}
.stButton>button[kind="primary"]:hover{{transform:translateY(-1px) !important;box-shadow:0 4px 16px rgba(124,58,237,0.35) !important;}}
.stNumberInput input{{background:{T['INPUT']} !important;color:{T['TEXT']} !important;border-color:{T['INPUT_B']} !important;}}
</style>
""", unsafe_allow_html=True)

# API 키
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except KeyError:
    st.error("❌ Streamlit Secrets에 ANTHROPIC_API_KEY를 추가해주세요.")
    st.stop()

# 헤더
st.markdown('<div class="main-header"><h1>🎓 Claude AI 학습 도우미</h1><p>고교학점제 맞춤 · 내신 계산 · AI 학습을 한 번에!</p></div>', unsafe_allow_html=True)

# 사이드바
with st.sidebar:
    st.markdown("### ⚙️ 설정")
    st.markdown("---")
    dark_toggle = st.toggle("🌙 다크 모드", value=st.session_state.dark_mode)
    if dark_toggle != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_toggle
        st.rerun()

    st.markdown("---")
    st.markdown("**🤖 AI 모델**")
    selected_model = st.selectbox("모델", list(MODELS.keys()), format_func=lambda k: f"{MODELS[k]['icon']} {MODELS[k]['display']}", label_visibility="collapsed")
    model_info = MODELS[selected_model]

    st.markdown("---")
    st.markdown("**🎂 나이 설정**")
    user_age = st.slider("나이", 14, 20, 17, label_visibility="collapsed")
    grade_system = get_grade_system(user_age)
    if user_age <= 15:
        age_inst = "중학생도 이해할 수 있도록 매우 쉽게 설명해주세요."
    elif user_age <= 17:
        age_inst = "고등학교 1~2학년 수준으로 설명해주세요."
    else:
        age_inst = "고등학교 3학년 수준으로 설명하고, 심화 내용도 포함해도 됩니다."
    st.caption(f"💡 {user_age}세 → **{grade_system}** 적용")

    st.markdown("---")
    st.markdown("**🎓 진로 & 희망 학과**")
    career_category = st.selectbox("계열", list(CAREER_DATA.keys()), label_visibility="collapsed")
    career_field = st.selectbox("세부 진로", list(CAREER_DATA[career_category].keys()), label_visibility="collapsed")
    dept_list = CAREER_DATA[career_category][career_field]
    dept_choice = st.selectbox("희망 학과", ["직접 입력"] + dept_list, label_visibility="collapsed")
    if dept_choice == "직접 입력":
        custom_dept = st.text_input("학과 입력", placeholder="예: 바이오메디컬공학과")
        final_dept = custom_dept.strip() if custom_dept.strip() else "미정"
    else:
        final_dept = dept_choice
    st.caption(f"📌 {career_field} → {final_dept}")

    st.markdown("---")
    st.markdown("**📱 앱 모드**")
    app_mode = st.radio("모드", ["💬 일반 모드", "📚 학습 모드", "🎓 고교학점제 모드"], label_visibility="collapsed")

    selected_subject = "국어"
    learning_feature = "💬 질문하기"
    quiz_difficulty = "보통"
    if app_mode == "📚 학습 모드":
        st.markdown("---")
        selected_subject = st.selectbox("📖 과목", list(SUBJECTS_STUDY.keys()), label_visibility="collapsed")
        learning_feature = st.radio("🎯 기능", ["💬 질문하기", "📝 퀴즈 모드", "📊 내신 계산기"], label_visibility="collapsed")
        if learning_feature == "📝 퀴즈 모드":
            quiz_difficulty = st.selectbox("퀴즈 난이도", ["쉬움", "보통", "어려움"])

    hschool_feature = "💬 진로 맞춤 질문"
    if app_mode == "🎓 고교학점제 모드":
        st.markdown("---")
        hschool_feature = st.radio("🎯 기능", ["💬 진로 맞춤 질문", "📘 추천 과목 안내", "📝 생기부 주제 추천", "🏃 활동 추천"], label_visibility="collapsed")

    st.markdown("---")
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.messages_for_api = []
        st.session_state.total_input_tokens = 0
        st.session_state.total_output_tokens = 0
        st.rerun()

    if st.session_state.chat_history:
        chat_export = "\n\n".join(f"[{'나' if m['role']=='user' else 'AI'}]\n{m['content']}" for m in st.session_state.chat_history)
        st.download_button("📥 대화 내보내기", chat_export, file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", mime="text/plain", use_container_width=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


# 유틸 함수
def calc_cost(in_t, out_t, mk):
    m = MODELS[mk]
    return (in_t / 1_000_000) * m["input_price"] + (out_t / 1_000_000) * m["output_price"]


def encode_image(f):
    b64 = base64.standard_b64encode(f.getvalue()).decode()
    mime = f.type if f.type in ["image/jpeg", "image/png", "image/gif", "image/webp"] else "image/png"
    return b64, mime


def build_system_prompt(extra=""):
    career_ctx = (
        f"학생 희망 진로: {career_field}\n희망 학과: {final_dept}\n"
        f"계열: {career_category}\n나이: {user_age}세\n내신 등급제: {grade_system}\n\n"
        f"답변 시 진로와 학과를 자연스럽게 연결해주세요. 무관한 질문이면 억지 연결은 불필요합니다."
    )
    age_ctx = f"사용자는 {user_age}세 고등학생입니다. {age_inst}"
    if app_mode == "💬 일반 모드":
        role = "당신은 친절하고 유능한 AI 학습 도우미입니다."
    elif app_mode == "📚 학습 모드":
        if learning_feature == "💬 질문하기":
            role = SUBJECTS_STUDY[selected_subject]
        elif learning_feature == "📝 퀴즈 모드":
            dm = {"쉬움": "기초적인", "보통": "중간 난이도의", "어려움": "심화된"}
            role = f"{SUBJECTS_STUDY[selected_subject]} 퀴즈 출제자로서 '문제 내줘'라고 하면 {dm[quiz_difficulty]} 문제를 1개 출제하세요."
        else:
            role = "당신은 친절한 AI 학습 도우미입니다."
    elif app_mode == "🎓 고교학점제 모드":
        role = f"당신은 고교학점제 전문 진로 상담 교사입니다. 학생의 진로({career_field})와 희망 학과({final_dept})에 맞게 유연하게 안내해주세요."
    else:
        role = "당신은 친절한 AI 학습 도우미입니다."
    parts = [age_ctx, career_ctx, role]
    if extra:
        parts.append(extra)
    parts.append("한국어로 답변해주세요.")
    return "\n\n".join(parts)


def call_ai_oneshot(user_text, system_text):
    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=selected_model, max_tokens=4096,
        system=system_text,
        messages=[{"role": "user", "content": user_text}]
    )
    return resp.content[0].text, resp.usage.input_tokens, resp.usage.output_tokens


# 모드 인디케이터
if app_mode == "💬 일반 모드":
    mt = f"💬 일반 모드 | {model_info['icon']} {model_info['display']} | 🎂 {user_age}세 | 🎓 {final_dept}"
elif app_mode == "📚 학습 모드":
    mt = f"📚 학습 모드 | 📖 {selected_subject} | 🎯 {learning_feature} | 🎂 {user_age}세"
else:
    mt = f"🎓 고교학점제 | 🔍 {career_field} | 🏫 {final_dept} | 🎂 {user_age}세"
st.markdown(f'<div class="mode-bar">{mt} | 📊 {grade_system}</div>', unsafe_allow_html=True)
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


# ────────────────────────────────────────
# 📊 내신 계산기
# ────────────────────────────────────────
if app_mode == "📚 학습 모드" and learning_feature == "📊 내신 계산기":
    if grade_system == "9등급제":
        st.markdown(f'<div class="grade-system-banner-9"><div class="banner-title" style="color:#7c3aed;">📊 9등급제 (석차등급제)</div><div class="banner-sub">2008년생 이전 ({CURRENT_YEAR}년 기준 19세 이상) · 상대평가</div></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="grade-system-banner-5"><div class="banner-title" style="color:#059669;">📊 5등급제 (성취도등급제)</div><div class="banner-sub">2009년생 이후 ({CURRENT_YEAR}년 기준 18세 이하) · 절대평가</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="card"><h3>📊 내신 등급 계산기</h3>', unsafe_allow_html=True)

    with st.expander(f"📌 {grade_system} 기준표 보기"):
        info_list = GRADE_9_INFO if grade_system == "9등급제" else GRADE_5_INFO
        header = "석차 비율" if grade_system == "9등급제" else "성취도 기준"
        rows = "".join([f"<tr><td><b style='color:{c}'>{g}등급</b></td><td>{r}</td></tr>" for g, r, c in info_list])
        st.markdown(f'<table class="grade-table"><tr><th>등급</th><th>{header}</th></tr>{rows}</table>', unsafe_allow_html=True)

    st.markdown("---")
    max_grade = 9 if grade_system == "9등급제" else 5
    st.markdown(f"<p style='color:{T['TEXT2']};font-size:0.86rem;'>✅ (각 과목 등급 × 단위수)의 합 ÷ 총 단위수 = 평균 등급 ({grade_system}, 1~{max_grade}등급)</p>", unsafe_allow_html=True)

    num_subjects = st.number_input("입력할 과목 수", min_value=1, max_value=20, value=5, step=1)
    ch1, ch2, ch3 = st.columns([3, 2, 2])
    ch1.markdown(f"<b style='color:{T['TEXT']}'>과목명</b>", unsafe_allow_html=True)
    ch2.markdown(f"<b style='color:{T['TEXT']}'>단위수</b>", unsafe_allow_html=True)
    ch3.markdown(f"<b style='color:{T['TEXT']}'>등급(1~{max_grade})</b>", unsafe_allow_html=True)

    entries = []
    for i in range(int(num_subjects)):
        c1, c2, c3 = st.columns([3, 2, 2])
        with c1:
            sn = st.text_input(f"s{i}", placeholder="예: 국어", key=f"sn_{i}", label_visibility="collapsed")
        with c2:
            un = st.number_input(f"u{i}", min_value=1, max_value=8, value=3, key=f"un_{i}", label_visibility="collapsed")
        with c3:
            gr = st.number_input(f"g{i}", min_value=1, max_value=max_grade, value=min(3, max_grade), key=f"gr_{i}", label_visibility="collapsed")
        if sn.strip():
            entries.append({"name": sn.strip(), "unit": int(un), "grade": int(gr)})

    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🔢 내신 계산하기", type="primary", use_container_width=True):
        if not entries:
            st.warning("⚠️ 과목명을 하나 이상 입력해주세요!")
        else:
            tu = sum(s["unit"] for s in entries)
            ws = sum(s["grade"] * s["unit"] for s in entries)
            avg = ws / tu

            if grade_system == "9등급제":
                bp = max(0, min(100, (9 - avg) / 8 * 100))
                bc = grade_color_9(avg)
                gl = grade_label_9(avg)
            else:
                bp = max(0, min(100, (5 - avg) / 4 * 100))
                bc = grade_color_5(avg)
                gl = grade_label_5(avg)

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f'<div class="grade-result"><div style="color:{T["TEXT2"]};font-size:0.8rem;margin-bottom:0.3rem;">📊 {grade_system} 기준</div><div class="grade-big">{avg:.2f}등급</div><div class="grade-label-text">{gl}</div><div class="grade-bar-wrap"><div class="grade-bar" style="width:{bp:.1f}%;background:{bc};"></div></div><div style="color:{T["TEXT2"]};font-size:0.82rem;">총 {tu}단위 | 등급×단위 합계: {ws}</div></div>', unsafe_allow_html=True)

            st.markdown(f"<div style='color:{T['TEXT2']};font-size:0.82rem;font-weight:700;margin:0.8rem 0 0.4rem;'>📋 과목별 상세</div>", unsafe_allow_html=True)
            for s in entries:
                gc = grade_color_9(s["grade"]) if grade_system == "9등급제" else grade_color_5(s["grade"])
                st.markdown(f'<div class="subject-row"><span><b>{s["name"]}</b></span><span style="color:{T["TEXT2"]};">{s["unit"]}단위</span><span><b style="color:{gc};">{s["grade"]}등급</b></span><span style="color:{T["MUTED"]};font-size:0.8rem;">{s["grade"]*s["unit"]}점</span></div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            with st.spinner("🤖 AI가 내신을 분석하는 중..."):
                subj_sum = "\n".join([f"- {s['name']}: {s['unit']}단위 {s['grade']}등급" for s in entries])
                if grade_system == "9등급제":
                    gsd = "9등급 상대평가 석차등급제. 1등급(상위4%), 2등급(상위11%), 3등급(상위23%) 기준."
                else:
                    gsd = "5등급 절대평가 성취도등급제. 1등급(90점이상/A), 2등급(80점대/B), 3등급(70점대/C)."

                prompt = f"""학생: {user_age}세, {grade_system}, 희망 진로: {career_field}, 희망 학과: {final_dept}
성적:\n{subj_sum}\n평균: {avg:.2f}등급 ({grade_system})
등급제 기준: {gsd}

분석해주세요:
1. 현재 내신 수준 평가 - {final_dept} 목표 시 충분한지
2. 과목별 분석 - 잘하는 과목, 개선 필요 과목, {career_field}에서 중요한 과목
3. 목표 등급 - {final_dept} 진학 위한 목표와 구체적 전략
4. 학습 전략 - {user_age}세에 맞는 공부법
5. 격려 메시지"""

                sys_text = f"고등학교 내신 분석 전문가이자 진로 상담 교사. {grade_system} 기준으로 분석. 한국 입시 제도를 이해하고 유연하게 조언. 한국어로 답변."
                try:
                    answer, it, ot = call_ai_oneshot(prompt, sys_text)
                    st.session_state.total_input_tokens += it
                    st.session_state.total_output_tokens += ot
                    st.markdown('<div class="card"><h3>🤖 AI 내신 분석 & 피드백</h3>', unsafe_allow_html=True)
                    st.markdown(answer)
                    st.markdown('</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"AI 분석 오류: {e}")

    # 사용량
    if st.session_state.total_input_tokens > 0:
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        ti = st.session_state.total_input_tokens
        to_ = st.session_state.total_output_tokens
        cost = calc_cost(ti, to_, selected_model)
        st.markdown(f'<div class="success-msg">💰 ${cost:.4f} (약 {cost*1400:.0f}원) | {model_info["icon"]} {model_info["display"]}</div>', unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="footer">🔒 API 키는 Streamlit Secrets로 안전하게 관리됩니다<br>📌 당곡고등학교 AI 학습 도우미</div>', unsafe_allow_html=True)
    st.stop()


# ────────────────────────────────────────
# 🎓 고교학점제 모드 카드
# ────────────────────────────────────────
if app_mode == "🎓 고교학점제 모드":
    st.markdown(f'<div class="career-card"><h3>🎓 나의 진로 설정</h3><span class="tag tag-blue">📂 {career_category}</span> <span class="tag tag-blue">🔍 {career_field}</span> <span class="tag tag-orange">🏫 {final_dept}</span> <span class="tag">🎂 {user_age}세</span> <span class="tag tag-purple">📊 {grade_system}</span><p style="color:{T["TEXT2"]};font-size:0.82rem;margin-top:0.7rem;margin-bottom:0;">💡 아래 채팅에서 맞춤형 AI 답변을 받을 수 있습니다!</p></div>', unsafe_allow_html=True)

    fg = {
        "💬 진로 맞춤 질문": f"'{career_field}' 분야나 '{final_dept}' 입시에 관해 물어보세요!",
        "📘 추천 과목 안내": f"고교학점제에서 '{final_dept}' 진학에 유리한 과목을 물어보세요!",
        "📝 생기부 주제 추천": f"'{career_field}' 관련 생기부 주제를 추천받아보세요!",
        "🏃 활동 추천": f"'{final_dept}' 입시에 도움되는 활동을 추천받아보세요!",
    }
    st.markdown(f'<div style="background:{T["TOK_BG"]};border:1px solid {T["BORDER"]};border-radius:12px;padding:0.9rem 1.1rem;margin:0.5rem 0;"><span style="color:{T["TEXT2"]};font-size:0.88rem;">💬 {fg.get(hschool_feature,"질문을 입력해주세요!")}</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


# ────────────────────────────────────────
# 💬 대화 기록
# ────────────────────────────────────────
if st.session_state.chat_history:
    st.markdown('<div class="card"><h3>💬 대화 기록</h3>', unsafe_allow_html=True)
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            dc = msg.get("display_content", msg["content"])
            st.markdown(f'<div class="chat-user"><div class="chat-role chat-role-user">👤 나</div>{dc}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-ai"><div class="chat-role chat-role-ai">🤖 AI</div>{msg["content"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)


# ────────────────────────────────────────
# 📎 이미지 + 💬 질문
# ────────────────────────────────────────
st.markdown('<div class="card"><h3>📎 이미지 업로드 (선택)</h3>', unsafe_allow_html=True)
uploaded_image = st.file_uploader("이미지", type=["png", "jpg", "jpeg", "gif", "webp"], label_visibility="collapsed")
if uploaded_image:
    st.image(uploaded_image, caption="업로드된 이미지", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

extra_ctx = ""
if app_mode == "🎓 고교학점제 모드":
    ph_map = {
        "💬 진로 맞춤 질문": f"예: {career_field} 분야에서 뭘 준비해야 할까요?",
        "📘 추천 과목 안내": f"예: {final_dept} 가려면 어떤 과목을 들어야 하나요?",
        "📝 생기부 주제 추천": f"예: {career_field} 관련 탐구 주제 추천해줘",
        "🏃 활동 추천": f"예: {final_dept} 입시에 도움되는 동아리 추천해줘",
    }
    placeholder = ph_map.get(hschool_feature, "질문을 입력하세요")
    card_title = f"🎓 {hschool_feature}"
    fc = {
        "📘 추천 과목 안내": f"{career_field} 진로와 {final_dept} 입시에 맞는 과목을 추천하고 이유를 설명해주세요.",
        "📝 생기부 주제 추천": f"{career_field}와 {final_dept} 관련 생기부 탐구 주제를 여러 개 제안해주세요.",
        "🏃 활동 추천": f"{career_field} 진로와 {final_dept} 입시에 도움되는 활동을 추천해주세요.",
    }
    extra_ctx = fc.get(hschool_feature, "")
elif app_mode == "📚 학습 모드" and learning_feature == "📝 퀴즈 모드":
    placeholder = "퀴즈를 시작하려면 '문제 내줘'라고 입력하세요!"
    card_title = "📝 퀴즈"
else:
    placeholder = "무엇이든 질문해보세요! (진로 맞춤 답변을 드립니다)"
    card_title = "💬 질문 입력"

st.markdown(f'<div class="card"><h3>{card_title}</h3>', unsafe_allow_html=True)
user_question = st.text_area("질문", placeholder=placeholder, height=120, label_visibility="collapsed")
st.markdown('</div>', unsafe_allow_html=True)


# ────────────────────────────────────────
# 🔍 전송
# ────────────────────────────────────────
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
                    user_content.append({"type": "image", "source": {"type": "base64", "media_type": mime, "data": b64_img}})
                    display_text = f"📎 [이미지] {user_question}" if user_question.strip() else "📎 [이미지만 전송]"

                text_to_send = user_question.strip() if user_question.strip() else "이 이미지에 대해 설명해주세요."
                user_content.append({"type": "text", "text": text_to_send})

                st.session_state.chat_history.append({"role": "user", "content": text_to_send, "display_content": display_text})
                st.session_state.messages_for_api.append({"role": "user", "content": user_content})

                client = anthropic.Anthropic(api_key=api_key)
                response = client.messages.create(
                    model=selected_model, max_tokens=4096,
                    system=build_system_prompt(extra=extra_ctx),
                    messages=st.session_state.messages_for_api
                )

                answer = response.content[0].text
                in_tok = response.usage.input_tokens
                out_tok = response.usage.output_tokens
                st.session_state.total_input_tokens += in_tok
                st.session_state.total_output_tokens += out_tok
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
                st.session_state.messages_for_api.append({"role": "assistant", "content": answer})
                st.rerun()

            except anthropic.AuthenticationError:
                st.error("❌ API 키가 올바르지 않습니다.")
                if st.session_state.chat_history:
                    st.session_state.chat_history.pop()
                if st.session_state.messages_for_api:
                    st.session_state.messages_for_api.pop()
            except anthropic.RateLimitError:
                st.error("⏳ 요청 한도를 초과했습니다.")
                if st.session_state.chat_history:
                    st.session_state.chat_history.pop()
                if st.session_state.messages_for_api:
                    st.session_state.messages_for_api.pop()
            except Exception as e:
                st.error(f"❗ 오류: {e}")
                if st.session_state.chat_history:
                    st.session_state.chat_history.pop()
                if st.session_state.messages_for_api:
                    st.session_state.messages_for_api.pop()


# ────────────────────────────────────────
# 📊 누적 사용량 & 비용
# ────────────────────────────────────────
if st.session_state.total_input_tokens > 0:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="card"><h3>📊 누적 사용량 & 비용</h3>', unsafe_allow_html=True)

    ti = st.session_state.total_input_tokens
    to_ = st.session_state.total_output_tokens
    tt = ti + to_
    cost = calc_cost(ti, to_, selected_model)
    krw = cost * 1400

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="token-card ti"><div class="label">📥 입력</div><div class="value">{ti:,}</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="token-card to"><div class="label">📤 출력</div><div class="value">{to_:,}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="token-card tt"><div class="label">🔢 합계</div><div class="value">{tt:,}</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="token-card tc"><div class="label">💰 비용</div><div class="value">${cost:.4f}</div></div>', unsafe_allow_html=True)

    st.markdown(f'<div class="success-msg">💰 ${cost:.4f} (약 {krw:.0f}원) | {model_info["icon"]} {model_info["display"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# 푸터
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown('<div class="footer">🔒 API 키는 Streamlit Secrets로 안전하게 관리됩니다<br>📌 당곡고등학교 AI 학습 도우미 · 고교학점제 맞춤 버전</div>', unsafe_allow_html=True)
