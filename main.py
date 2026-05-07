import streamlit as st
import anthropic

# ─────────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Claude AI 질문 앱",
    page_icon="🤖",
    layout="centered"
)

# ─────────────────────────────────────────────
# 커스텀 스타일
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* 전체 배경 */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    }

    /* 메인 타이틀 */
    .main-title {
        text-align: center;
        padding: 1.5rem 0 0.5rem 0;
    }
    .main-title h1 {
        background: linear-gradient(90deg, #00d2ff, #7b2ff7, #ff6a88);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0;
    }
    .main-title p {
        color: #a0a0c0;
        font-size: 1.05rem;
        margin-top: 0.3rem;
    }

    /* 카드 컨테이너 */
    .glass-card {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        backdrop-filter: blur(12px);
    }
    .glass-card h3 {
        color: #e0e0ff;
        margin-top: 0;
    }

    /* 사용량 카드 */
    .token-card {
        background: rgba(255,255,255,0.07);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 14px;
        padding: 1.2rem;
        text-align: center;
    }
    .token-card .label {
        color: #a0a0c0;
        font-size: 0.85rem;
        margin-bottom: 0.3rem;
    }
    .token-card .value {
        font-size: 1.8rem;
        font-weight: 700;
    }
    .token-input .value  { color: #00d2ff; }
    .token-output .value { color: #7b2ff7; }
    .token-total .value  { color: #ff6a88; }

    /* 모델 뱃지 */
    .model-badge {
        display: inline-block;
        padding: 0.4rem 1rem;
        border-radius: 999px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-sonnet {
        background: rgba(0,210,255,0.15);
        color: #00d2ff;
        border: 1px solid rgba(0,210,255,0.3);
    }
    .badge-opus {
        background: rgba(123,47,247,0.15);
        color: #b07aff;
        border: 1px solid rgba(123,47,247,0.3);
    }

    /* 답변 영역 */
    .answer-box {
        background: rgba(255,255,255,0.05);
        border-left: 4px solid #7b2ff7;
        border-radius: 0 12px 12px 0;
        padding: 1.2rem 1.5rem;
        color: #e0e0f0;
        line-height: 1.7;
        margin-top: 0.5rem;
    }

    /* 구분선 */
    .glow-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #7b2ff7, #00d2ff, transparent);
        border: none;
        margin: 1.5rem 0;
        border-radius: 2px;
    }

    /* 푸터 */
    .footer-text {
        text-align: center;
        color: #606080;
        font-size: 0.8rem;
        padding: 2rem 0 1rem 0;
    }

    /* Streamlit 기본 요소 색상 보정 */
    .stTextArea textarea {
        background: rgba(255,255,255,0.05) !important;
        color: #e0e0f0 !important;
        border: 1px solid rgba(255,255,255,0.15) !important;
        border-radius: 12px !important;
    }
    .stTextArea textarea::placeholder {
        color: #707090 !important;
    }

    /* 라디오 버튼 텍스트 */
    .stRadio label, .stRadio div[role="radiogroup"] label span {
        color: #c0c0e0 !important;
    }

    /* 버튼 */
    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #7b2ff7, #00d2ff) !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 1.05rem !important;
        padding: 0.6rem 2rem !important;
        transition: transform 0.2s, box-shadow 0.2s !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 24px rgba(123,47,247,0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 타이틀
# ─────────────────────────────────────────────
st.markdown("""
<div class="main-title">
    <h1>🤖 Claude AI 질문 앱</h1>
    <p>Claude AI에게 무엇이든 질문해보세요!</p>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# API 키 로드
# ─────────────────────────────────────────────
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except KeyError:
    st.error("❌ API 키가 설정되지 않았습니다. Streamlit Cloud의 Secrets에 `ANTHROPIC_API_KEY`를 추가해주세요.")
    st.stop()

# ─────────────────────────────────────────────
# 모델 정보 (나중에 4.6이 나오면 여기만 수정)
# ─────────────────────────────────────────────
MODELS = {
    "claude-sonnet-4-20250514": {
        "display": "Claude Sonnet 4",
        "desc": "⚡ 빠르고 효율적",
        "badge_class": "badge-sonnet",
        "icon": "⚡"
    },
    "claude-opus-4-20250514": {
        "display": "Claude Opus 4",
        "desc": "🧠 강력하고 정교함",
        "badge_class": "badge-opus",
        "icon": "🧠"
    }
}

# ─────────────────────────────────────────────
# 모델 선택
# ─────────────────────────────────────────────
st.markdown('<div class="glass-card"><h3>⚙️ 모델 선택</h3>', unsafe_allow_html=True)

selected_model = st.radio(
    "사용할 모델을 선택하세요:",
    options=list(MODELS.keys()),
    format_func=lambda k: f"{MODELS[k]['icon']} {MODELS[k]['display']}  —  {MODELS[k]['desc']}",
    horizontal=True,
    label_visibility="collapsed"
)

info = MODELS[selected_model]
st.markdown(
    f'<span class="model-badge {info["badge_class"]}">'
    f'{info["icon"]} {info["display"]} 선택됨</span>',
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 질문 입력
# ─────────────────────────────────────────────
st.markdown('<div class="glass-card"><h3>💬 질문 입력</h3>', unsafe_allow_html=True)

user_question = st.text_area(
    "질문을 입력하세요:",
    placeholder="예: 파이썬에서 리스트와 튜플의 차이점은 무엇인가요?",
    height=160,
    label_visibility="collapsed"
)

st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 질문 전송
# ─────────────────────────────────────────────
if st.button("🔍  AI에게 질문하기", type="primary", use_container_width=True):

    if not user_question.strip():
        st.warning("⚠️ 질문을 입력해주세요!")
    else:
        with st.spinner("🤔 AI가 답변을 생성하는 중..."):
            try:
                client = anthropic.Anthropic(api_key=api_key)

                response = client.messages.create(
                    model=selected_model,
                    max_tokens=4096,
                    messages=[
                        {"role": "user", "content": user_question}
                    ]
                )

                # 응답 추출
                answer = response.content[0].text
                input_tokens = response.usage.input_tokens
                output_tokens = response.usage.output_tokens
                total_tokens = input_tokens + output_tokens

                # ── 답변 표시 ──
                st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)
                st.markdown('<div class="glass-card"><h3>💡 AI 답변</h3>', unsafe_allow_html=True)
                st.markdown(answer)
                st.markdown('</div>', unsafe_allow_html=True)

                # ── 사용량 표시 ──
                st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)
                st.markdown('<div class="glass-card"><h3>📊 토큰 사용량</h3>', unsafe_allow_html=True)

                c1, c2, c3 = st.columns(3)

                with c1:
                    st.markdown(f"""
                    <div class="token-card token-input">
                        <div class="label">📥 입력 토큰</div>
                        <div class="value">{input_tokens:,}</div>
                    </div>""", unsafe_allow_html=True)

                with c2:
                    st.markdown(f"""
                    <div class="token-card token-output">
                        <div class="label">📤 출력 토큰</div>
                        <div class="value">{output_tokens:,}</div>
                    </div>""", unsafe_allow_html=True)

                with c3:
                    st.markdown(f"""
                    <div class="token-card token-total">
                        <div class="label">🔢 총 토큰</div>
                        <div class="value">{total_tokens:,}</div>
                    </div>""", unsafe_allow_html=True)

                st.markdown(
                    f'<br><center><span class="model-badge {info["badge_class"]}">'
                    f'✅ {info["display"]} 사용 완료</span></center>',
                    unsafe_allow_html=True
                )
                st.markdown('</div>', unsafe_allow_html=True)

            except anthropic.AuthenticationError:
                st.error("❌ API 키가 올바르지 않습니다. Secrets 설정을 확인해주세요.")
            except anthropic.RateLimitError:
                st.error("⏳ 요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.")
            except anthropic.APIError as e:
                st.error(f"🚨 API 오류: {e}")
            except Exception as e:
                st.error(f"❗ 오류 발생: {e}")

# ─────────────────────────────────────────────
# 푸터
# ─────────────────────────────────────────────
st.markdown('<div class="glow-divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div class="footer-text">
    🔒 API 키는 Streamlit Secrets로 안전하게 관리됩니다<br>
    📌 당곡고등학교 AI 학습 도우미
</div>
""", unsafe_allow_html=True)
