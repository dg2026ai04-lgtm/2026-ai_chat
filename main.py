import streamlit as st
import anthropic
import base64
import json
from datetime import datetime

# ─────────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Claude AI 질문 앱",
    page_icon="🤖",
    layout="centered"
)

# ─────────────────────────────────────────────
# 세션 상태 초기화
# ─────────────────────────────────────────────
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "messages_for_api" not in st.session_state:
    st.session_state.messages_for_api = []
if "total_input_tokens" not in st.session_state:
    st.session_state.total_input_tokens = 0
if "total_output_tokens" not in st.session_state:
    st.session_state.total_output_tokens = 0
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False
if "quiz_active" not in st.session_state:
    st.session_state.quiz_active = False
if "quiz_subject" not in st.session_state:
    st.session_state.quiz_subject = ""
if "quiz_history" not in st.session_state:
    st.session_state.quiz_history = []

# ─────────────────────────────────────────────
# 다크/라이트 모드 스타일
# ─────────────────────────────────────────────
if st.session_state.dark_mode:
    BG = "#1a1a2e"
    CARD_BG = "#16213e"
    CARD_BORDER = "#2a2a4a"
    TEXT_PRIMARY = "#e0e0f0"
    TEXT_SECONDARY = "#a0a0c0"
    TEXT_MUTED = "#707090"
    INPUT_BG = "#1a1a3e"
    INPUT_BORDER = "#3a3a5a"
    TOKEN_BG = "#1e1e3a"
    ACCENT = "#7c3aed"
    SUCCESS_BG = "#1a2e1a"
    SUCCESS_BORDER = "#2e5a2e"
    SUCCESS_TEXT = "#4ade80"
    USER_BG = "#2a2a5a"
    AI_BG = "#1e293b"
    SHADOW = "rgba(0,0,0,0.2)"
    DIVIDER_COLORS = "#3a3a5a"
else:
    BG = "#f8f9fc"
    CARD_BG = "#ffffff"
    CARD_BORDER = "#e5e7eb"
    TEXT_PRIMARY = "#1a1a2e"
    TEXT_SECONDARY = "#6b7280"
    TEXT_MUTED = "#9ca3af"
    INPUT_BG = "#ffffff"
    INPUT_BORDER = "#d1d5db"
    TOKEN_BG = "#f9fafb"
    ACCENT = "#7c3aed"
    SUCCESS_BG = "#f0fdf4"
    SUCCESS_BORDER = "#bbf7d0"
    SUCCESS_TEXT = "#166534"
    USER_BG = "#eff6ff"
    AI_BG = "#f5f3ff"
    SHADOW = "rgba(0,0,0,0.04)"
    DIVIDER_COLORS = "#d1d5db"

st.markdown(f"""
<style>
    .stApp {{
        background-color: {BG};
    }}
    .main-header {{
        text-align: center;
        padding: 1.5rem 0 0.5rem 0;
    }}
    .main-header h1 {{
        color: {TEXT_PRIMARY};
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }}
    .main-header p {{
        color: {TEXT_SECONDARY};
        font-size: 0.95rem;
    }}
    .card {{
        background: {CARD_BG};
        border: 1px solid {CARD_BORDER};
        border-radius: 14px;
        padding: 1.3rem;
        margin: 0.8rem 0;
        box-shadow: 0 1px 3px {SHADOW};
    }}
    .card h3 {{
        color: {TEXT_PRIMARY};
        font-size: 1.05rem;
        margin: 0 0 0.8rem 0;
    }}
    .divider {{
        height: 1px;
        background: linear-gradient(90deg, transparent, {DIVIDER_COLORS}, transparent);
        border: none;
        margin: 1rem 0;
    }}
    .token-card {{
        background: {TOKEN_BG};
        border: 1px solid {CARD_BORDER};
        border-radius: 12px;
        padding: 0.9rem;
        text-align: center;
    }}
    .token-card .label {{
        color: {TEXT_SECONDARY};
        font-size: 0.78rem;
        margin-bottom: 0.15rem;
    }}
    .token-card .value {{
        font-size: 1.4rem;
        font-weight: 700;
    }}
    .token-input .value  {{ color: #2563eb; }}
    .token-output .value {{ color: #7c3aed; }}
    .token-total .value  {{ color: #059669; }}
    .token-cost .value   {{ color: #d97706; }}
    .badge {{
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 999px;
        font-weight: 600;
        font-size: 0.78rem;
    }}
    .badge-sonnet {{
        background: #eff6ff;
        color: #2563eb;
        border: 1px solid #bfdbfe;
    }}
    .badge-opus {{
        background: #f5f3ff;
        color: #7c3aed;
        border: 1px solid #ddd6fe;
    }}
    .chat-user {{
        background: {USER_BG};
        border-radius: 12px;
        padding: 0.9rem 1.1rem;
        margin: 0.4rem 0;
        color: {TEXT_PRIMARY};
        border-left: 3px solid #2563eb;
    }}
    .chat-ai {{
        background: {AI_BG};
        border-radius: 12px;
        padding: 0.9rem 1.1rem;
        margin: 0.4rem 0;
        color: {TEXT_PRIMARY};
        border-left: 3px solid #7c3aed;
    }}
    .chat-role {{
        font-weight: 700;
        font-size: 0.8rem;
        margin-bottom: 0.3rem;
    }}
    .chat-role-user {{ color: #2563eb; }}
    .chat-role-ai {{ color: #7c3aed; }}
    .success-msg {{
        background: {SUCCESS_BG};
        border: 1px solid {SUCCESS_BORDER};
        border-radius: 10px;
        padding: 0.7rem 1rem;
        color: {SUCCESS_TEXT};
        font-weight: 600;
        text-align: center;
        margin-top: 0.5rem;
    }}
    .footer {{
        text-align: center;
        color: {TEXT_MUTED};
        font-size: 0.78rem;
        padding: 1.5rem 0 1rem 0;
    }}
    .stTextArea textarea {{
        background: {INPUT_BG} !important;
        color: {TEXT_PRIMARY} !important;
        border: 1px solid {INPUT_BORDER} !important;
        border-radius: 10px !important;
    }}
    .stTextArea textarea::placeholder {{
        color: {TEXT_MUTED} !important;
    }}
    .stRadio label span,
    .stSelectbox label,
    .stSlider label {{
        color: {TEXT_PRIMARY} !important;
    }}
    .stButton > button[kind="primary"] {{
        background: linear-gradient(90deg, #7c3aed, #2563eb) !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        color: #ffffff !important;
    }}
    .stButton > button[kind="primary"]:hover {{
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(124,58,237,0.3) !important;
    }}
    .mode-indicator {{
        background: {TOKEN_BG};
        border: 1px solid {CARD_BORDER};
        border-radius: 10px;
        padding: 0.6rem 1rem;
        text-align: center;
        color: {TEXT_PRIMARY};
        font-weight: 600;
        font-size: 0.9rem;
        margin: 0.5rem 0;
    }}
    /* 다크모드 selectbox 텍스트 */
    .stSelectbox div[data-baseweb="select"] {{
        color: {TEXT_PRIMARY} !important;
    }}
    div[data-baseweb="select"] > div {{
        background-color: {INPUT_BG} !important;
        border-color: {INPUT_BORDER} !important;
    }}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 헤더
# ─────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🤖 Claude AI 질문 앱</h1>
    <p>Claude AI에게 무엇이든 질문해보세요!</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# API 키 로드
# ─────────────────────────────────────────────
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except KeyError:
    st.error("❌ API 키가 설정되지 않았습니다. Streamlit Cloud Secrets에 `ANTHROPIC_API_KEY`를 추가해주세요.")
    st.stop()

# ─────────────────────────────────────────────
# 모델 정보 & 가격 (1M 토큰당 USD)
# ─────────────────────────────────────────────
MODELS = {
    "claude-sonnet-4-20250514": {
        "display": "Claude Sonnet 4",
        "desc": "빠르고 효율적",
        "badge_class": "badge-sonnet",
        "icon": "⚡",
        "input_price": 3.0,
        "output_price": 15.0
    },
    "claude-opus-4-20250514": {
        "display": "Claude Opus 4",
        "desc": "강력하고 정교함",
        "badge_class": "badge-opus",
        "icon": "🧠",
        "input_price": 15.0,
        "output_price": 75.0
    }
}

# 과목별 시스템 프롬프트
SUBJECTS = {
    "국어": "당신은 국어 전문 교사입니다. 문학, 문법, 독해, 작문 등 국어 과목에 대해 친절하고 정확하게 가르쳐주세요.",
    "영어": "당신은 영어 전문 교사입니다. 문법, 어휘, 독해, 회화, 영작 등 영어 과목에 대해 친절하고 정확하게 가르쳐주세요.",
    "수학": "당신은 수학 전문 교사입니다. 풀이 과정을 단계별로 자세히 보여주고, 개념을 쉽게 설명해주세요. 수식은 명확하게 작성해주세요.",
    "과학": "당신은 과학 전문 교사입니다. 물리, 화학, 생물, 지구과학 등 과학 과목에 대해 원리를 쉽게 설명해주세요.",
    "사회": "당신은 사회 전문 교사입니다. 역사, 지리, 정치, 경제, 사회문화 등에 대해 친절하고 정확하게 가르쳐주세요.",
    "정보/코딩": "당신은 정보(컴퓨터과학) 전문 교사입니다. 프로그래밍, 알고리즘, 자료구조 등을 쉽게 설명해주세요. 코드 예시를 포함해주세요."
}

# ─────────────────────────────────────────────
# 사이드바 설정
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"### ⚙️ 설정")

    # 다크/라이트 모드 토글
    st.markdown("---")
    dark_toggle = st.toggle(
        "🌙 다크 모드",
        value=st.session_state.dark_mode
    )
    if dark_toggle != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_toggle
        st.rerun()

    # 모델 선택
    st.markdown("---")
    st.markdown("**🤖 AI 모델**")
    selected_model = st.selectbox(
        "모델 선택",
        options=list(MODELS.keys()),
        format_func=lambda k: f"{MODELS[k]['icon']} {MODELS[k]['display']}",
        label_visibility="collapsed"
    )
    model_info = MODELS[selected_model]

    # 나이 설정
    st.markdown("---")
    st.markdown("**🎂 나이 설정**")
    user_age = st.slider("나이", min_value=8, max_value=80, value=17, label_visibility="collapsed")

    age_instruction = ""
    if user_age <= 10:
        age_instruction = "아주 쉽고 재미있는 말로 설명해주세요. 초등학생 저학년도 이해할 수 있도록 해주세요."
    elif user_age <= 13:
        age_instruction = "쉽고 친근한 말로 설명해주세요. 초등학생 고학년~중학생 수준으로 설명해주세요."
    elif user_age <= 16:
        age_instruction = "중학생~고등학생이 이해할 수 있는 수준으로 설명해주세요."
    elif user_age <= 19:
        age_instruction = "고등학생이 이해할 수 있는 수준으로 설명해주세요. 필요하면 심화 내용도 포함해주세요."
    elif user_age <= 25:
        age_instruction = "대학생 수준으로 전문적이지만 이해하기 쉽게 설명해주세요."
    else:
        age_instruction = "성인 수준으로 전문적으로 설명해주세요."

    st.caption(f"💡 {user_age}세 맞춤 답변을 제공합니다")

    # 앱 모드 선택
    st.markdown("---")
    st.markdown("**📱 앱 모드**")
    app_mode = st.radio(
        "모드 선택",
        options=["💬 일반 모드", "📚 학습 모드"],
        label_visibility="collapsed"
    )

    # 학습 모드 세부 설정
    if app_mode == "📚 학습 모드":
        st.markdown("---")
        st.markdown("**📖 과목 선택**")
        selected_subject = st.selectbox(
            "과목",
            options=list(SUBJECTS.keys()),
            label_visibility="collapsed"
        )

        st.markdown("**🎯 학습 기능**")
        learning_feature = st.radio(
            "기능",
            options=["💬 질문하기", "📝 퀴즈 모드"],
            label_visibility="collapsed"
        )

        if learning_feature == "📝 퀴즈 모드":
            quiz_difficulty = st.selectbox(
                "퀴즈 난이도",
                options=["쉬움", "보통", "어려움"],
            )

    # 대화 초기화
    st.markdown("---")
    if st.button("🗑️ 대화 초기화", use_container_width=True):
        st.session_state.chat_history = []
        st.session_state.messages_for_api = []
        st.session_state.total_input_tokens = 0
        st.session_state.total_output_tokens = 0
        st.session_state.quiz_active = False
        st.session_state.quiz_history = []
        st.rerun()

    # 대화 내보내기
    if st.session_state.chat_history:
        chat_text = ""
        for msg in st.session_state.chat_history:
            role = "나" if msg["role"] == "user" else "AI"
            chat_text += f"[{role}]\n{msg['content']}\n\n"

        st.download_button(
            "📥 대화 내보내기",
            data=chat_text,
            file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 현재 모드 표시
# ─────────────────────────────────────────────
if app_mode == "💬 일반 모드":
    st.markdown(
        f'<div class="mode-indicator">💬 일반 모드 &nbsp;|&nbsp; '
        f'{model_info["icon"]} {model_info["display"]} &nbsp;|&nbsp; '
        f'🎂 {user_age}세</div>',
        unsafe_allow_html=True
    )
else:
    feature_text = "질문하기" if learning_feature == "💬 질문하기" else "퀴즈 모드"
    st.markdown(
        f'<div class="mode-indicator">📚 학습 모드 &nbsp;|&nbsp; '
        f'📖 {selected_subject} &nbsp;|&nbsp; '
        f'🎯 {feature_text} &nbsp;|&nbsp; '
        f'🎂 {user_age}세</div>',
        unsafe_allow_html=True
    )

# ─────────────────────────────────────────────
# 시스템 프롬프트 구성
# ─────────────────────────────────────────────
def build_system_prompt():
    parts = []

    # 나이 맞춤
    parts.append(f"사용자는 {user_age}세입니다. {age_instruction}")

    if app_mode == "📚 학습 모드":
        # 과목 프롬프트
        parts.append(SUBJECTS[selected_subject])

        if learning_feature == "📝 퀴즈 모드":
            diff_map = {
                "쉬움": "기초적인",
                "보통": "중간 난이도의",
                "어려움": "도전적이고 심화된"
            }
            diff_text = diff_map[quiz_difficulty]

            parts.append(
                f"당신은 {selected_subject} 퀴즈 출제자입니다. "
                f"사용자가 '퀴즈 시작' 또는 '문제 내줘'라고 하면 {diff_text} {selected_subject} 문제를 1개 출제해주세요. "
                f"사용자가 답을 하면 정답인지 확인하고, 해설을 제공한 뒤, 다음 문제를 낼지 물어보세요. "
                f"점수도 추적해주세요."
            )
    else:
        parts.append("당신은 친절하고 도움이 되는 AI 어시스턴트입니다. 사용자의 질문에 정확하고 이해하기 쉽게 답변해주세요.")

    parts.append("한국어로 답변해주세요.")

    return "\n\n".join(parts)


# ─────────────────────────────────────────────
# 비용 계산 함수
# ─────────────────────────────────────────────
def calculate_cost(input_tokens, output_tokens, model_key):
    m = MODELS[model_key]
    input_cost = (input_tokens / 1_000_000) * m["input_price"]
    output_cost = (output_tokens / 1_000_000) * m["output_price"]
    return input_cost + output_cost


# ─────────────────────────────────────────────
# 이미지 인코딩 함수
# ─────────────────────────────────────────────
def encode_image(uploaded_file):
    bytes_data = uploaded_file.getvalue()
    base64_image = base64.standard_b64encode(bytes_data).decode("utf-8")

    mime_type = uploaded_file.type
    if mime_type not in ["image/jpeg", "image/png", "image/gif", "image/webp"]:
        mime_type = "image/png"

    return base64_image, mime_type


# ─────────────────────────────────────────────
# 대화 기록 표시
# ─────────────────────────────────────────────
if st.session_state.chat_history:
    st.markdown('<div class="card"><h3>💬 대화 기록</h3>', unsafe_allow_html=True)

    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            display_content = msg.get("display_content", msg["content"])
            st.markdown(
                f'<div class="chat-user">'
                f'<div class="chat-role chat-role-user">👤 나</div>'
                f'{display_content}</div>',
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

# ─────────────────────────────────────────────
# 이미지 업로드
# ─────────────────────────────────────────────
st.markdown('<div class="card"><h3>📎 이미지 업로드 (선택사항)</h3>', unsafe_allow_html=True)

uploaded_image = st.file_uploader(
    "이미지를 업로드하세요",
    type=["png", "jpg", "jpeg", "gif", "webp"],
    label_visibility="collapsed"
)

if uploaded_image:
    st.image(uploaded_image, caption="업로드된 이미지", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 질문 입력
# ─────────────────────────────────────────────
if app_mode == "📚 학습 모드" and learning_feature == "📝 퀴즈 모드":
    placeholder_text = "퀴즈를 시작하려면 '문제 내줘'라고 입력하세요! 또는 답을 입력하세요."
    card_title = "📝 퀴즈"
else:
    placeholder_text = "예: 파이썬에서 리스트와 튜플의 차이점은 무엇인가요?"
    card_title = "💬 질문 입력"

st.markdown(f'<div class="card"><h3>{card_title}</h3>', unsafe_allow_html=True)

user_question = st.text_area(
    "질문을 입력하세요:",
    placeholder=placeholder_text,
    height=120,
    label_visibility="collapsed"
)

st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 전송 버튼
# ─────────────────────────────────────────────
if st.button("🔍  AI에게 질문하기", type="primary", use_container_width=True):

    if not user_question.strip() and not uploaded_image:
        st.warning("⚠️ 질문을 입력하거나 이미지를 업로드해주세요!")
    else:
        with st.spinner("🤔 AI가 답변을 생성하는 중..."):
            try:
                client = anthropic.Anthropic(api_key=api_key)

                # 사용자 메시지 구성
                user_content = []
                display_text = user_question if user_question.strip() else "(이미지만 전송)"

                # 이미지가 있으면 추가
                if uploaded_image:
                    b64_image, mime = encode_image(uploaded_image)
                    user_content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime,
                            "data": b64_image
                        }
                    })
                    display_text = f"📎 [이미지 첨부] {user_question}" if user_question.strip() else "📎 [이미지 첨부] 이 이미지에 대해 설명해주세요."

                # 텍스트 추가
                text_to_send = user_question.strip() if user_question.strip() else "이 이미지에 대해 설명해주세요."
                user_content.append({
                    "type": "text",
                    "text": text_to_send
                })

                # 대화 기록에 추가 (표시용)
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": text_to_send,
                    "display_content": display_text
                })

                # API용 메시지 기록에 추가
                st.session_state.messages_for_api.append({
                    "role": "user",
                    "content": user_content
                })

                # 시스템 프롬프트
                system_prompt = build_system_prompt()

                # API 호출
                response = client.messages.create(
                    model=selected_model,
                    max_tokens=4096,
                    system=system_prompt,
                    messages=st.session_state.messages_for_api
                )

                # 응답 추출
                answer = response.content[0].text
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens

                # 누적 토큰
                st.session_state.total_input_tokens += input_tokens
                st.session_state.total_output_tokens += output_tokens

                # 대화 기록에 AI 응답 추가
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer
                })

                # API용 기록에도 추가 (대화 맥락 유지)
                st.session_state.messages_for_api.append({
                    "role": "assistant",
                    "content": answer
                })

                st.rerun()

            except anthropic.AuthenticationError:
                st.error("❌ API 키가 올바르지 않습니다.")
                st.session_state.chat_history.pop()
                st.session_state.messages_for_api.pop()
            except anthropic.RateLimitError:
                st.error("⏳ 요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.")
                st.session_state.chat_history.pop()
                st.session_state.messages_for_api.pop()
            except anthropic.APIError as e:
                st.error(f"🚨 API 오류: {e}")
                st.session_state.chat_history.pop()
                st.session_state.messages_for_api.pop()
            except Exception as e:
                st.error(f"❗ 오류 발생: {e}")
                st.session_state.chat_history.pop()
                st.session_state.messages_for_api.pop()

# ─────────────────────────────────────────────
# 누적 사용량 & 비용 표시
# ─────────────────────────────────────────────
if st.session_state.total_input_tokens > 0 or st.session_state.total_output_tokens > 0:
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="card"><h3>📊 누적 사용량 & 비용</h3>', unsafe_allow_html=True)

    total_in = st.session_state.total_input_tokens
    total_out = st.session_state.total_output_tokens
    total_all = total_in + total_out
    total_cost = calculate_cost(total_in, total_out, selected_model)
    cost_krw = total_cost * 1400  # 대략적 환율

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
        <div class="token-card token-input">
            <div class="label">📥 입력 토큰</div>
            <div class="value">{total_in:,}</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="token-card token-output">
            <div class="label">📤 출력 토큰</div>
            <div class="value">{total_out:,}</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="token-card token-total">
            <div class="label">🔢 총 토큰</div>
            <div class="value">{total_all:,}</div>
        </div>""", unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="token-card token-cost">
            <div class="label">💰 예상 비용</div>
            <div class="value">${total_cost:.4f}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown(
        f'<div class="success-msg">'
        f'💰 예상 비용: ${total_cost:.4f} (약 {cost_krw:.1f}원) &nbsp;|&nbsp; '
        f'{model_info["icon"]} {model_info["display"]} 사용 중</div>',
        unsafe_allow_html=True
    )

    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 푸터
# ─────────────────────────────────────────────
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div class="footer">
    🔒 API 키는 Streamlit Secrets로 안전하게 관리됩니다<br>
    📌 당곡고등학교 AI 학습 도우미
</div>
""", unsafe_allow_html=True)
