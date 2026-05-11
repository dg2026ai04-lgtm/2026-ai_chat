import streamlit as st
import anthropic


def run_grade_calculator(
    user_age,
    grade_system,
    career_field,
    final_dept,
    career_category,
    age_inst,
    selected_model,
    model_info,
    api_key,
    T,
    MODELS,
    CURRENT_YEAR
):
    """
    내신 등급 계산기 전체 UI + AI 분석
    학습 모드 → 내신 계산기 선택 시 호출됨
    """

    # ─────────────────────────────────────
    # 등급제 데이터
    # ─────────────────────────────────────

    # 9등급제: 석차 비율 기준 (상대평가)
    GRADE_9_INFO = [
        (1, "상위 4% 이하",      "#7c3aed"),
        (2, "상위 4% ~ 11%",     "#2563eb"),
        (3, "상위 11% ~ 23%",    "#0891b2"),
        (4, "상위 23% ~ 40%",    "#059669"),
        (5, "상위 40% ~ 60%",    "#65a30d"),
        (6, "상위 60% ~ 77%",    "#d97706"),
        (7, "상위 77% ~ 89%",    "#ea580c"),
        (8, "상위 89% ~ 96%",    "#dc2626"),
        (9, "상위 96% ~ 100%",   "#9f1239"),
    ]

    # 5등급제: 석차 비율 기준 (상대평가, 2025 개정 교육과정)
    GRADE_5_INFO = [
        (1, "상위 10% 이하",     "#7c3aed"),
        (2, "상위 10% ~ 34%",    "#2563eb"),
        (3, "상위 34% ~ 66%",    "#059669"),
        (4, "상위 66% ~ 90%",    "#d97706"),
        (5, "상위 90% ~ 100%",   "#dc2626"),
    ]

    # ─────────────────────────────────────
    # 색상 함수
    # ─────────────────────────────────────
    def grade_color(g):
        if grade_system == "9등급제":
            colors = [
                "#7c3aed", "#2563eb", "#0891b2", "#059669",
                "#65a30d", "#d97706", "#ea580c", "#dc2626", "#9f1239"
            ]
            idx = min(max(round(g) - 1, 0), 8)
        else:
            colors = ["#7c3aed", "#2563eb", "#059669", "#d97706", "#dc2626"]
            idx = min(max(round(g) - 1, 0), 4)
        return colors[idx]

    # ─────────────────────────────────────
    # 라벨 함수
    # ─────────────────────────────────────
    def grade_label(g):
        if grade_system == "9등급제":
            labels = {
                1: "1등급 🏆 최상위 (상위 4%)",
                2: "2등급 🥈 상위권 (상위 11%)",
                3: "3등급 🥉 상위권 (상위 23%)",
                4: "4등급 중상위권 (상위 40%)",
                5: "5등급 중위권 (상위 60%)",
                6: "6등급 중하위권 (상위 77%)",
                7: "7등급 하위권 (상위 89%)",
                8: "8등급 하위권 (상위 96%)",
                9: "9등급 최하위",
            }
        else:
            labels = {
                1: "1등급 🏆 최상위 (상위 10%)",
                2: "2등급 🥈 상위권 (상위 34%)",
                3: "3등급 중위권 (상위 66%)",
                4: "4등급 하위권 (상위 90%)",
                5: "5등급 최하위 (하위 10%)",
            }
        return labels.get(round(g), f"{g:.2f}등급")

    # ─────────────────────────────────────
    # 막대 퍼센트 함수
    # ─────────────────────────────────────
    def bar_percentage(g):
        if grade_system == "9등급제":
            return max(0.0, min(100.0, (9 - g) / 8 * 100))
        else:
            return max(0.0, min(100.0, (5 - g) / 4 * 100))

    # ─────────────────────────────────────
    # 등급제 배너
    # ─────────────────────────────────────
    if grade_system == "9등급제":
        st.markdown(f"""
        <div class="grade-system-banner-9">
            <div class="banner-title" style="color:#7c3aed;">
                📊 9등급제 (석차등급제)
            </div>
            <div class="banner-sub">
                2008년생 이전 ({CURRENT_YEAR}년 기준 19세 이상)<br>
                상대평가 · 석차 백분율에 따라 1~9등급 산출
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        extra_note = ""
        if CURRENT_YEAR >= 2027:
            extra_note = "<br>📌 2027년부터 전 학년 5등급제 적용"
        st.markdown(f"""
        <div class="grade-system-banner-5">
            <div class="banner-title" style="color:#059669;">
                📊 5등급제 (석차등급제)
            </div>
            <div class="banner-sub">
                2009년생 이후 ({CURRENT_YEAR}년 기준 18세 이하)<br>
                상대평가 · 석차 비율에 따라 1~5등급 산출
                {extra_note}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ─────────────────────────────────────
    # 계산기 메인 카드
    # ─────────────────────────────────────
    st.markdown(
        '<div class="card"><h3>📊 내신 등급 계산기</h3>',
        unsafe_allow_html=True
    )

    max_grade = 9 if grade_system == "9등급제" else 5

    # ── 등급 기준표 ──
    with st.expander(f"📌 {grade_system} 등급 기준표 보기"):
        info_list = GRADE_9_INFO if grade_system == "9등급제" else GRADE_5_INFO
        header = "석차 비율"

        table_rows = ""
        for g, desc, color in info_list:
            table_rows += (
                f"<tr>"
                f"<td><b style='color:{color};'>{g}등급</b></td>"
                f"<td>{desc}</td>"
                f"</tr>"
            )

        st.markdown(f"""
        <table class="grade-table">
            <tr><th>등급</th><th>{header}</th></tr>
            {table_rows}
        </table>
        """, unsafe_allow_html=True)

        if grade_system == "9등급제":
            st.markdown(f"""
            <p style="color:{T['TEXT2']}; font-size:0.82rem; margin-top:0.6rem;">
            ※ 석차등급은 <b>상대평가</b>로, 같은 점수라도 응시자 수에 따라 등급이 달라질 수 있습니다.<br>
            ※ 동점자가 있을 경우 동점자 모두 상위 등급으로 처리됩니다.
            </p>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <p style="color:{T['TEXT2']}; font-size:0.82rem; margin-top:0.6rem;">
            ※ 5등급제도 <b>상대평가</b>로, 석차 백분율에 따라 등급이 결정됩니다.<br>
            ※ 기존 9등급제보다 등급 구간이 넓어 등급 간 변별력이 줄어듭니다.<br>
            ※ 1등급(상위 10%)은 9등급제의 1~2등급 사이에 해당합니다.
            </p>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # ── 계산 방식 안내 ──
    st.markdown(f"""
    <p style="color:{T['TEXT2']}; font-size:0.88rem; margin-bottom:1rem;">
    ✅ <b>계산 공식</b><br>
    <code style="background:{T['TOK_BG']}; padding:0.3rem 0.6rem; border-radius:6px;
                 color:{T['TEXT']}; font-size:0.85rem;">
    평균 등급 = (각 과목 등급 × 단위수)의 합 ÷ 총 단위수
    </code><br><br>
    📌 {grade_system} 기준 (1~{max_grade}등급) · 상대평가<br>
    📌 단위수(학점수)가 큰 과목이 평균에 더 큰 영향을 미칩니다.
    </p>
    """, unsafe_allow_html=True)

    # ── 과목 입력 안내 ──
    if grade_system == "9등급제":
        st.markdown(f"""
        <p style="color:{T['TEXT2']}; font-size:0.83rem; margin-bottom:0.8rem;">
        ⚠️ <b>석차등급이 산출되는 과목만 입력하세요.</b><br>
        체육, 예술, 교양 등 성취도(P/A/B/C)만 나오는 과목은 제외됩니다.
        </p>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <p style="color:{T['TEXT2']}; font-size:0.83rem; margin-bottom:0.8rem;">
        ⚠️ <b>석차등급(1~5)이 산출되는 과목만 입력하세요.</b><br>
        체육, 예술, 교양 등 등급이 산출되지 않는 과목은 제외됩니다.
        </p>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # ── 과목 수 선택 ──
    st.markdown(f"**📝 과목 입력**")
    num_subjects = st.number_input(
        "입력할 과목 수",
        min_value=1,
        max_value=20,
        value=6,
        step=1,
        help="이번 학기에 석차등급이 나오는 과목 수를 입력하세요."
    )

    # ── 헤더 ──
    col_h1, col_h2, col_h3 = st.columns([3, 2, 2])
    col_h1.markdown(
        f"<b style='color:{T['TEXT']}'>📖 과목명</b>",
        unsafe_allow_html=True
    )
    col_h2.markdown(
        f"<b style='color:{T['TEXT']}'>📐 단위수 (학점)</b>",
        unsafe_allow_html=True
    )
    col_h3.markdown(
        f"<b style='color:{T['TEXT']}'>🏅 등급 (1~{max_grade})</b>",
        unsafe_allow_html=True
    )

    # ── 과목별 입력 ──
    default_subjects = ["국어", "수학", "영어", "한국사", "통합과학", "통합사회"]
    entries = []

    for i in range(int(num_subjects)):
        c1, c2, c3 = st.columns([3, 2, 2])
        default_name = default_subjects[i] if i < len(default_subjects) else ""

        with c1:
            sname = st.text_input(
                f"과목명_{i}",
                value=default_name,
                placeholder="과목명 입력",
                key=f"calc_sname_{i}",
                label_visibility="collapsed"
            )
        with c2:
            unit = st.number_input(
                f"단위수_{i}",
                min_value=1,
                max_value=8,
                value=3,
                key=f"calc_unit_{i}",
                label_visibility="collapsed"
            )
        with c3:
            grade = st.number_input(
                f"등급_{i}",
                min_value=1,
                max_value=max_grade,
                value=min(3, max_grade),
                key=f"calc_grade_{i}",
                label_visibility="collapsed"
            )

        if sname.strip():
            entries.append({
                "name": sname.strip(),
                "unit": int(unit),
                "grade": int(grade)
            })

    st.markdown('</div>', unsafe_allow_html=True)

    # ─────────────────────────────────────
    # 계산 버튼
    # ─────────────────────────────────────
    if st.button("🔢  내신 등급 계산하기", type="primary", use_container_width=True):

        if not entries:
            st.warning("⚠️ 과목명을 하나 이상 입력해주세요!")
            return

        # ── 가중평균 계산 ──
        total_units = sum(s["unit"] for s in entries)
        weighted_sum = sum(s["grade"] * s["unit"] for s in entries)
        avg_grade = weighted_sum / total_units

        bar_pct = bar_percentage(avg_grade)
        bar_col = grade_color(avg_grade)
        g_label = grade_label(avg_grade)

        # ─────────────────────────────────
        # 결과 카드
        # ─────────────────────────────────
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="grade-result">
            <div style="color:{T['TEXT2']}; font-size:0.82rem; margin-bottom:0.3rem;">
                📊 {grade_system} 기준 · 상대평가 평균 내신 등급
            </div>
            <div class="grade-big">{avg_grade:.2f}등급</div>
            <div class="grade-label-text">{g_label}</div>
            <div class="grade-bar-wrap">
                <div class="grade-bar"
                     style="width:{bar_pct:.1f}%; background:{bar_col};">
                </div>
            </div>
            <div style="color:{T['TEXT2']}; font-size:0.82rem; margin-top:0.3rem;">
                📐 총 단위수: <b>{total_units}단위</b> &nbsp;|&nbsp;
                🔢 등급×단위 합계: <b>{weighted_sum}</b> &nbsp;|&nbsp;
                📏 {max_grade}등급 기준
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ─────────────────────────────────
        # 과목별 상세
        # ─────────────────────────────────
        st.markdown(f"""
        <div style="color:{T['TEXT2']}; font-size:0.85rem;
                    font-weight:700; margin:1rem 0 0.5rem;">
            📋 과목별 상세 내역
        </div>
        """, unsafe_allow_html=True)

        for s in entries:
            gc = grade_color(s["grade"])
            contribution = s["grade"] * s["unit"]
            pct = (contribution / weighted_sum * 100) if weighted_sum > 0 else 0

            st.markdown(f"""
            <div class="subject-row">
                <span style="flex:3;"><b>{s['name']}</b></span>
                <span style="flex:1.5; text-align:center; color:{T['TEXT2']};">
                    {s['unit']}단위
                </span>
                <span style="flex:1.5; text-align:center;">
                    <b style="color:{gc};">{s['grade']}등급</b>
                </span>
                <span style="flex:2; text-align:right; color:{T['MUTED']}; font-size:0.8rem;">
                    {contribution}점 ({pct:.1f}%)
                </span>
            </div>
            """, unsafe_allow_html=True)

        # ─────────────────────────────────
        # 등급 분포 요약
        # ─────────────────────────────────
        grade_counts = {}
        for s in entries:
            g = s["grade"]
            grade_counts[g] = grade_counts.get(g, 0) + 1

        dist_tags = ""
        for g in sorted(grade_counts.keys()):
            gc = grade_color(g)
            cnt = grade_counts[g]
            dist_tags += (
                f'<span style="display:inline-block; background:{gc}22; '
                f'color:{gc}; border:1px solid {gc}55; border-radius:999px; '
                f'padding:0.2rem 0.7rem; font-size:0.78rem; font-weight:600; '
                f'margin:0.15rem;">'
                f'{g}등급: {cnt}과목</span> '
            )

        st.markdown(f"""
        <div style="margin:1rem 0 0.5rem;">
            <span style="color:{T['TEXT2']}; font-size:0.82rem; font-weight:700;">
                📊 등급 분포:
            </span><br>
            {dist_tags}
        </div>
        """, unsafe_allow_html=True)

        # ─────────────────────────────────
        # 시뮬레이션: 1등급씩 올렸을 때
        # ─────────────────────────────────
        st.markdown(f"""
        <div style="color:{T['TEXT2']}; font-size:0.85rem;
                    font-weight:700; margin:1rem 0 0.5rem;">
            🎯 만약 등급을 올린다면? (시뮬레이션)
        </div>
        """, unsafe_allow_html=True)

        simulations = []
        for s in entries:
            if s["grade"] > 1:
                new_ws = weighted_sum - s["unit"]
                new_avg = new_ws / total_units
                diff = avg_grade - new_avg
                simulations.append({
                    "name": s["name"],
                    "unit": s["unit"],
                    "current": s["grade"],
                    "new_grade": s["grade"] - 1,
                    "new_avg": new_avg,
                    "improvement": diff,
                })

        if simulations:
            simulations.sort(key=lambda x: x["improvement"], reverse=True)
            for sim in simulations[:5]:
                imp_color = "#059669" if sim["improvement"] > 0.1 else "#65a30d"
                st.markdown(f"""
                <div class="subject-row">
                    <span style="flex:3;">
                        <b>{sim['name']}</b>
                        <span style="color:{T['MUTED']}; font-size:0.78rem;">
                            ({sim['current']}→{sim['new_grade']}등급)
                        </span>
                    </span>
                    <span style="flex:2; text-align:center; color:{T['TEXT2']};">
                        {sim['unit']}단위
                    </span>
                    <span style="flex:2; text-align:right;">
                        평균 <b style="color:{imp_color};">
                        {sim['new_avg']:.2f}</b>등급
                        <span style="color:{imp_color}; font-size:0.78rem;">
                            (▲{sim['improvement']:.2f})
                        </span>
                    </span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown(f"""
            <p style="color:{T['TEXT2']}; font-size:0.8rem; margin-top:0.5rem;">
            💡 단위수가 큰 과목의 등급을 올리면 평균이 더 크게 변합니다!
            </p>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <p style="color:{T['TEXT2']}; font-size:0.85rem;">
            🏆 모든 과목이 1등급이에요! 완벽합니다!
            </p>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # ─────────────────────────────────
        # 9등급 ↔ 5등급 환산 참고
        # ─────────────────────────────────
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="color:{T['TEXT2']}; font-size:0.85rem; font-weight:700;
                    margin-bottom:0.5rem;">
            📐 9등급제 ↔ 5등급제 환산 참고표
        </div>
        <table class="grade-table">
            <tr>
                <th>9등급제</th>
                <th>석차 비율</th>
                <th>5등급제</th>
                <th>석차 비율</th>
            </tr>
            <tr>
                <td><b style="color:#7c3aed;">1등급</b></td>
                <td>~4%</td>
                <td rowspan="2"><b style="color:#7c3aed;">1등급</b></td>
                <td rowspan="2">~10%</td>
            </tr>
            <tr>
                <td><b style="color:#2563eb;">2등급</b></td>
                <td>~11%</td>
            </tr>
            <tr>
                <td><b style="color:#0891b2;">3등급</b></td>
                <td>~23%</td>
                <td rowspan="2"><b style="color:#2563eb;">2등급</b></td>
                <td rowspan="2">~34%</td>
            </tr>
            <tr>
                <td><b style="color:#059669;">4등급</b></td>
                <td>~40%</td>
            </tr>
            <tr>
                <td><b style="color:#65a30d;">5등급</b></td>
                <td>~60%</td>
                <td><b style="color:#059669;">3등급</b></td>
                <td>~66%</td>
            </tr>
            <tr>
                <td><b style="color:#d97706;">6등급</b></td>
                <td>~77%</td>
                <td rowspan="2"><b style="color:#d97706;">4등급</b></td>
                <td rowspan="2">~90%</td>
            </tr>
            <tr>
                <td><b style="color:#ea580c;">7등급</b></td>
                <td>~89%</td>
            </tr>
            <tr>
                <td><b style="color:#dc2626;">8등급</b></td>
                <td>~96%</td>
                <td rowspan="2"><b style="color:#dc2626;">5등급</b></td>
                <td rowspan="2">~100%</td>
            </tr>
            <tr>
                <td><b style="color:#9f1239;">9등급</b></td>
                <td>~100%</td>
            </tr>
        </table>
        <p style="color:{T['TEXT2']}; font-size:0.8rem; margin-top:0.5rem;">
        ※ 위 환산표는 석차 비율 기준 대략적인 참고용입니다.
        </p>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # ─────────────────────────────────
        # 🤖 AI 분석
        # ─────────────────────────────────
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        with st.spinner("🤖 AI가 내신을 분석하고 진로 맞춤 피드백을 생성하는 중..."):

            subject_summary = "\n".join([
                f"- {s['name']}: {s['unit']}단위 {s['grade']}등급"
                for s in entries
            ])

            if grade_system == "9등급제":
                grade_system_desc = (
                    "9등급 상대평가 석차등급제입니다.\n"
                    "1등급(상위 4%), 2등급(상위 11%), 3등급(상위 23%), "
                    "4등급(상위 40%), 5등급(상위 60%), 6등급(상위 77%), "
                    "7등급(상위 89%), 8등급(상위 96%), 9등급(나머지) 기준.\n"
                    "수시 학생부교과전형은 보통 1~3등급을 요구합니다.\n"
                    "정시는 수능 위주이므로 내신과 별개로 봅니다."
                )
            else:
                grade_system_desc = (
                    "5등급 상대평가 석차등급제입니다.\n"
                    "1등급(상위 10%), 2등급(상위 34%), 3등급(상위 66%), "
                    "4등급(상위 90%), 5등급(나머지) 기준.\n"
                    "기존 9등급제보다 등급 구간이 넓어 등급 간 변별력이 줄어들며, "
                    "대학별로 5등급제 반영 방식이 다를 수 있습니다.\n"
                    "5등급제 1등급(상위 10%)은 9등급제의 약 1~2등급 사이에 해당합니다."
                )

            sim_text = ""
            if simulations:
                sim_text = "\n\n[시뮬레이션 - 각 과목 1등급씩 올렸을 때]\n"
                for sim in simulations[:3]:
                    sim_text += (
                        f"- {sim['name']} ({sim['current']}→{sim['new_grade']}등급): "
                        f"평균 {sim['new_avg']:.2f}등급 (▲{sim['improvement']:.2f})\n"
                    )

            analysis_prompt = f"""
학생 정보:
- 나이: {user_age}세
- 적용 내신 등급제: {grade_system} (상대평가)
- 희망 진로 분야: {career_field}
- 희망 학과: {final_dept}
- 계열: {career_category}

현재 내신 성적:
{subject_summary}

📊 계산된 평균 내신 등급: {avg_grade:.2f}등급 ({grade_system} 기준)
📐 총 단위수: {total_units}단위
{sim_text}

[등급제 분석 기준]
{grade_system_desc}

위 정보를 바탕으로 다음을 상세히 분석해주세요:

1. **현재 내신 수준 평가**
   - {grade_system} 기준으로 {avg_grade:.2f}등급의 의미를 설명해주세요.
   - {final_dept}를 목표로 할 때 현재 성적이 충분한지 솔직하게 평가해주세요.
   - 해당 학과의 일반적인 입학 성적 수준과 비교해주세요.

2. **과목별 세부 분석**
   - 잘하고 있는 과목과 개선이 필요한 과목을 짚어주세요.
   - {career_field} 진로에서 특히 중요한 과목을 강조해주세요.
   - 어떤 과목에 집중 투자하면 효율적인지 단위수와 함께 분석해주세요.

3. **목표 등급 & 구체적 전략**
   - {final_dept} 진학을 위해 평균 몇 등급을 목표로 해야 하는지 알려주세요.
   - 시뮬레이션 결과를 참고해서 어느 과목을 올리면 좋을지 제안해주세요.
   - 수시/정시 각 전형별로 어떤 전략이 유리할지 안내해주세요.

4. **학습 전략 추천**
   - {user_age}세 학생에게 맞는 구체적이고 실천 가능한 학습 전략을 제안해주세요.
   - {career_field} 진로와 연결된 공부 방향도 안내해주세요.

5. **격려 메시지**
   - 학생의 현재 상황에 맞는 진심 어린 응원 메시지를 남겨주세요.

⚠️ 정해진 틀 없이, 이 학생의 실제 상황에 맞는 유연하고 따뜻한 조언을 해주세요.
"""

            ai_system = (
                f"당신은 고등학교 내신 분석 전문가이자 입시 상담 교사입니다. "
                f"학생에게 적용되는 등급제({grade_system}, 상대평가)를 정확히 이해하고 분석해주세요. "
                f"학생의 진로({career_field})와 희망 학과({final_dept})를 깊이 이해하고 "
                f"현실적이면서도 따뜻한 조언을 해주세요. "
                f"한국 대학 입시 제도(수시 학생부교과, 학생부종합, 논술, 정시 등)를 "
                f"정확히 이해하고 답변해주세요. "
                f"한국어로 답변해주세요."
            )

            try:
                client = anthropic.Anthropic(api_key=api_key)
                response = client.messages.create(
                    model=selected_model,
                    max_tokens=4096,
                    system=ai_system,
                    messages=[{"role": "user", "content": analysis_prompt}]
                )

                answer = response.content[0].text
                in_tok = response.usage.input_tokens
                out_tok = response.usage.output_tokens

                st.session_state.total_input_tokens += in_tok
                st.session_state.total_output_tokens += out_tok

                st.markdown(
                    '<div class="card">'
                    '<h3>🤖 AI 내신 분석 & 진로 맞춤 피드백</h3>',
                    unsafe_allow_html=True
                )
                st.markdown(answer)

                cost = (
                    (in_tok / 1_000_000) * MODELS[selected_model]["input_price"]
                    + (out_tok / 1_000_000) * MODELS[selected_model]["output_price"]
                )
                st.markdown(f"""
                <div class="success-msg">
                    ✅ 분석 완료 | 📥 {in_tok:,} + 📤 {out_tok:,} 토큰
                    | 💰 ${cost:.4f} (약 {cost * 1400:.0f}원)
                    | {model_info['icon']} {model_info['display']}
                </div>
                """, unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)

            except anthropic.AuthenticationError:
                st.error("❌ API 키가 올바르지 않습니다.")
            except anthropic.RateLimitError:
                st.error("⏳ 요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.")
            except Exception as e:
                st.error(f"❗ AI 분석 중 오류 발생: {e}")
