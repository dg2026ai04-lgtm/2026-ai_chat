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
# 심플 & 모던 스타일
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* 밝은 배경 */
    .stApp {
        background-color: #f8f9fc;
    }

    /* 메인 헤더 */
    .main-header {
        text-align: center;
        padding: 2rem 0 1rem 0;
    }
    .main-header h1 {
        color: #1a1a2e;
        font-size: 2.4rem;
        font-weight: 800;
        margin-bottom: 0.3rem;
    }
    .main-header p {
        color: #6b7280;
        font-size: 1rem;
    }

    /* 카드 */
    .card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .card h3 {
        color: #1a1a2e;
        font-size: 1.1rem;
        margin: 0 0 1rem 0;
    }

    /* 구분선 */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, #d1d5db, transparent);
        border: none;
        margin: 1.2rem 0;
    }

    /* 토큰 카드 */
    .token-card {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
    }
    .token-card .label {
        color: #6b7280;
        font-size: 0.8rem;
        margin-bottom: 0.2rem;
    }
    .token-card .value {
        font-size: 1.6rem;
        font-weight: 700;
    }
    .token-input .value  { color: #2563eb; }
    .token-output .value { color: #7c3aed; }
    .token-total .value  { color: #059669; }

    /* 모델 뱃지 */
    .badge {
        display: inline-block;
        padding: 0.35rem 0.9rem;
        border-radius: 999px;
        font-weight: 600;
        font-size: 0.82rem;
    }
    .badge-sonnet {
        background: #eff6ff;
        color: #2563eb;
        border: 1px solid #bfdbfe;
    }
    .badge-opus {
        background: #f5f3ff;
        color: #7c3aed;
        border: 1px solid #ddd6fe;
    }

    /* 답변 박스 */
    .answer-box {
        background: #ffffff;
        border-left: 4px solid #7c3aed;
        border-radius: 0 12px 12px 0;
        padding: 1.2rem 1.5rem;
        color: #1f2937;
        line-height: 1.8;
    }

    /* 푸터 */
    .footer {
        text-align: center;
        color: #9ca3af;
        font-size: 0.8rem;
        padding: 2rem 0 1rem 0;
    }

    /* 텍스트 입력 영역 */
    .stTextArea textarea {
        background: #ffffff !important;
        color: #1f2937 !important;
        border: 1px solid #d1d5db !important;
        border-radius: 10px !important;
        font-size: 0.95rem !important;
    }
    .stTextArea textarea:focus {
        border-color: #7c3aed !important;
        box-shadow: 0 0 0 2px rgba(124,58,237,0.15) !important;
    }
    .stTextArea textarea::placeholder {
        color: #9ca3af !important;
    }

    /* 라디오 버튼 */
    .stRadio label span {
        color: #374151 !important;
    }

    /* 메인 버튼 */
    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #7c3aed, #2563eb) !important;
        border: none !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        padding: 0.55rem 2rem !important;
        color: #ffffff !important;
        transition: transform 0.15s, box-shadow 0.15s !important;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(124,58,237,0.3) !important;
    }

    /* 성공 알림 */
    .success-msg {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-radius: 10px;
        padding: 0.8rem 1rem;
        color: #166534;
        font-weight: 600;
        text-align: center;
        margin-top: 0.5rem;
    }
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

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# API 키 로드
# ─────────────────────────────────────────────
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except KeyError:
    st.error("❌ API 키가 설정되지 않았습니다. Streamlit Cloud Secrets에 `ANTHROPIC_API_KEY`를 추가해주세요.")
    st.stop()

# ─────────────────────────────────────────────
# 모델 정보
# ─────────────────────────────────────────────
MODELS = {
    "claude-sonnet-4-20250514": {
        "display": "Claude Sonnet 4",
        "desc": "빠르고 효율적",
        "badge_class": "badge-sonnet",
        "icon": "⚡"
    },
    "claude-opus-4-20250514": {
        "display": "Claude Opus 4",
        "desc": "강력하고 정교함",
        "badge_class": "badge-opus",
        "icon": "🧠"
    }
}

# ─────────────────────────────────────────────
# 모델 선택 카드
# ─────────────────────────────────────────────
st.markdown('<div class="card"><h3>⚙️ 모델 선택</h3>', unsafe_allow_html=True)

selected_model = st.radio(
    "모델 선택",
    options=list(MODELS.keys()),
    format_func=lambda k: f"{MODELS[k]['icon']}  {MODELS[k]['display']}  —  {MODELS[k]['desc']}",
    horizontal=True,
    label_visibility="collapsed"
)

info = MODELS[selected_model]
st.markdown(
    f'<span class="badge {info["badge_class"]}">'
    f'{info["icon"]}  {info["display"]} 선택됨</span>',
    unsafe_allow_html=True
)
st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 질문 입력 카드
# ─────────────────────────────────────────────
st.markdown('<div class="card"><h3>💬 질문 입력</h3>', unsafe_allow_html=True)

user_question = st.text_area(
    "질문을 입력하세요:",
    placeholder="예: 파이썬에서 리스트와 튜플의 차이점은 무엇인가요?",
    height=150,
    label_visibility="collapsed"
)

st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 전송 버튼
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
                st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
                st.markdown('<div class="card"><h3>💡 AI 답변</h3>', unsafe_allow_html=True)
                st.markdown(answer)
                st.markdown('</div>', unsafe_allow_html=True)

                # ── 토큰 사용량 ──
                st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
                st.markdown('<div class="card"><h3>📊 토큰 사용량</h3>', unsafe_allow_html=True)

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
                    f'<div class="success-msg">'
                    f'✅ {info["display"]} 응답 완료</div>',
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
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div class="footer">
    🔒 API 키는 Streamlit Secrets로 안전하게 관리됩니다<br>
    📌 당곡고등학교 AI 학습 도우미
</div>
""", unsafe_allow_html=True)
