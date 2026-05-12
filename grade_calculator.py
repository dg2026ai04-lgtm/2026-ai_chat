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
    GRADE_9_INFO = [
        (1, "상위 4% 이하",    "#7c3aed"),
        (2, "상위 4%~11%",     "#2563eb"),
        (3, "상위 11%~23%",    "#0891b2"),
        (4, "상위 23%~40%",    "#059669"),
        (5, "상위 40%~60%",    "#65a30d"),
        (6, "상위 60%~77%",    "#d97706"),
        (7, "상위 77%~89%",    "#ea580c"),
        (8, "상위 89%~96%",    "#dc2626"),
        (9, "상위 96%~100%",   "#9f1239"),
    ]

    GRADE_5_INFO = [
        (1, "상위 10% 이하",   "#7c3aed"),
        (2, "상위 10%~34%",    "#2563eb"),
        (3, "상위 34%~66%",    "#059669"),
        (4, "상위 66%~90%",    "#d97706"),
        (5, "상위 90%~100%",   "#dc2626"),
    ]

    def grade_color(g):
        if grade_system == "9등급제":
            colors = [
                "#7c3aed", "#2563eb", "#0891b2", "#059669",
                "#65a30d", "#d97706", "#ea580c", "#dc2626", "#9f1239"
            ]
            return colors[min(max(round(g) - 1, 0), 8)]
        colors = ["#7c3aed", "#2563eb", "#059669", "#d97706", "#dc2626"]
        return colors[min(max(round(g) - 1, 0), 4)]

    def grade_label(g):
        if grade_system == "9등급제":
            labels = {
                1: "1등급 최상위 (상위 4%)",
                2: "2등급 상위권 (상위 11%)",
                3: "3등급 상위권 (상위 23%)",
                4: "4등급 중상위권 (상위 40%)",
                5: "5등급 중위권 (상위 60%)",
                6: "6등급 중하위권 (상위 77%)",
                7: "7등급 하위권 (상위 89%)",
                8: "8등급 하위권 (상위 96%)",
                9: "9등급 최하위",
            }
        else:
            labels = {
                1: "1등급 최상위 (상위 10%)",
                2: "2등급 상위권 (상위 34%)",
                3: "3등급 중위권 (상위 66%)",
                4: "4등급 하위권 (상위 90%)",
                5: "5등급 최하위 (하위 10%)",
            }
        return labels.get(round(g), f"{g:.2f}등급")

    def bar_percentage(g):
        if grade_system == "9등급제":
            return max(0.0, min(100.0, (9 - g) / 8 * 100))
        return max(0.0, min(100.0, (5 - g) / 4 * 100))

    # ── 배너 ──
    if grade_system == "9등급제":
        st.markdown(
            '<div class="grade-system-banner-9">'
            '<div class="banner-title" style="color:#7c3aed;">9등급제 (석차등급제)</div>'
            '<div class="banner-sub">'
            f'2008년생 이전 ({CURRENT_YEAR}년 기준 19세 이상)<br>'
            '상대평가 · 석차 백분율에 따라 1~9등급 산출'
            '</div></div>',
            unsafe_allow_html=True
        )
    else:
        extra = "<br>2027년부터 전 학년 5등급제 적용" if CURRENT_YEAR >= 2027 else ""
        st.markdown(
            '<div class="grade-system-banner-5">'
            '<div class="banner-title" style="color:#059669;">5등급제 (석차등급제)</div>'
            '<div class="banner-sub">'
            f'2009년생 이후 ({CURRENT_YEAR}년 기준 18세 이하)<br>'
            f'상대평가 · 석차 비율에 따라 1~5등급 산출{extra}'
            '</div></div>',
            unsafe_allow_html=True
        )

    # ── 계산기 카드 ──
    st.markdown(
        '<div class="card"><h3>내신 등급 계산기</h3>',
        unsafe_allow_html=True
    )

    max_grade = 9 if grade_system == "9등급제" else 5
    info_list = GRADE_9_INFO if grade_system == "9등급제" else GRADE_5_INFO

    with st.expander(f"{grade_system} 등급 기준표 보기"):
        rows = "".join(
            f"<tr><td><b style='color:{c};'>{g}등급</b></td><td>{d}</td></tr>"
            for g, d, c in info_list
        )
        st.markdown(
            '<table class="grade-table">'
            '<tr><th>등급</th><th>석차 비율</th></tr>'
            f'{rows}</table>',
            unsafe_allow_html=True
        )
        if grade_system == "9등급제":
            st.markdown(
                f'<p style="color:{T["TEXT2"]};font-size:0.82rem;margin-top:0.6rem;">'
                '동점자가 있을 경우 동점자 모두 상위 등급으로 처리됩니다.</p>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<p style="color:{T["TEXT2"]};font-size:0.82rem;margin-top:0.6rem;">'
                '5등급제도 상대평가로, 석차 백분율에 따라 등급이 결정됩니다.<br>'
                '1등급(상위 10%)은 9등급제의 약 1~2등급 사이에 해당합니다.</p>',
                unsafe_allow_html=True
            )

    st.markdown("---")
    st.markdown(
        f'<p style="color:{T["TEXT2"]};font-size:0.88rem;margin-bottom:0.5rem;">'
        f'계산 공식: 평균 등급 = (각 과목 등급 x 단위수)의 합 / 총 단위수<br>'
        f'{grade_system} 기준 (1~{max_grade}등급) · 상대평가<br>'
        '단위수가 큰 과목이 평균에 더 큰 영향을 줍니다.<br>'
        '석차등급이 산출되는 과목만 입력하세요. 체육, 예술, 교양 등은 제외됩니다.</p>',
        unsafe_allow_html=True
    )
    st.markdown("---")

    # ── 과목 입력 ──
    num_subjects = st.number_input(
        "입력할 과목 수", min_value=1, max_value=20, value=6, step=1
    )

    h1, h2, h3 = st.columns([3, 2, 2])
    h1.markdown(
        f"<b style='color:{T['TEXT']};'>과목명</b>", unsafe_allow_html=True
    )
    h2.markdown(
        f"<b style='color:{T['TEXT']};'>단위수</b>", unsafe_allow_html=True
    )
    h3.markdown(
        f"<b style='color:{T['TEXT']};'>등급 (1~{max_grade})</b>",
        unsafe_allow_html=True
    )

    defaults = ["국어", "수학", "영어", "한국사", "통합과학", "통합사회"]
    entries = []

    for i in range(int(num_subjects)):
        c1, c2, c3 = st.columns([3, 2, 2])
        with c1:
            sname = st.text_input(
                f"s{i}",
                value=defaults[i] if i < len(defaults) else "",
                placeholder="과목명 입력",
                key=f"calc_sname_{i}",
                label_visibility="collapsed"
            )
        with c2:
            unit = st.number_input(
                f"u{i}", min_value=1, max_value=8, value=3,
                key=f"calc_unit_{i}", label_visibility="collapsed"
            )
        with c3:
            grade = st.number_input(
                f"g{i}", min_value=1, max_value=max_grade,
                value=min(3, max_grade),
                key=f"calc_grade_{i}", label_visibility="collapsed"
            )
        if sname.strip():
            entries.append({
                "name": sname.strip(),
                "unit": int(unit),
                "grade": int(grade)
            })

    st.markdown('</div>', unsafe_allow_html=True)

    # ── 계산 버튼 ──
    if st.button("내신 등급 계산하기", type="primary", use_container_width=True):
        if not entries:
            st.warning("과목명을 하나 이상 입력해주세요!")
            return

        total_units = sum(s["unit"] for s in entries)
        weighted_sum = sum(s["grade"] * s["unit"] for s in entries)
        avg_grade = weighted_sum / total_units
        bar_pct = bar_percentage(avg_grade)
        bar_col = grade_color(avg_grade)
        g_label = grade_label(avg_grade)

        # ── 결과 카드 ──
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="grade-result">'
            f'<div style="color:{T["TEXT2"]};font-size:0.82rem;margin-bottom:0.3rem;">'
            f'{grade_system} 기준 · 상대평가</div>'
            f'<div class="grade-big">{avg_grade:.2f}등급</div>'
            f'<div class="grade-label-text">{g_label}</div>'
            '<div class="grade-bar-wrap">'
            f'<div class="grade-bar" style="width:{bar_pct:.1f}%;background:{bar_col};"></div>'
            '</div>'
            f'<div style="color:{T["TEXT2"]};font-size:0.82rem;margin-top:0.3rem;">'
            f'총 단위수: {total_units}단위 | 등급x단위 합계: {weighted_sum} | {max_grade}등급 기준'
            '</div></div>',
            unsafe_allow_html=True
        )

        # ── 과목별 상세 ──
        st.markdown(
            f'<div style="color:{T["TEXT2"]};font-size:0.85rem;'
            'font-weight:700;margin:1rem 0 0.5rem;">과목별 상세 내역</div>',
            unsafe_allow_html=True
        )
        for s in entries:
            gc = grade_color(s["grade"])
            contrib = s["grade"] * s["unit"]
            pct = (contrib / weighted_sum * 100) if weighted_sum > 0 else 0
            st.markdown(
                '<div class="subject-row">'
                f'<span style="flex:3;"><b>{s["name"]}</b></span>'
                f'<span style="flex:1.5;text-align:center;color:{T["TEXT2"]};">'
                f'{s["unit"]}단위</span>'
                f'<span style="flex:1.5;text-align:center;">'
                f'<b style="color:{gc};">{s["grade"]}등급</b></span>'
                f'<span style="flex:2;text-align:right;color:{T["MUTED"]};font-size:0.8rem;">'
                f'{contrib}점 ({pct:.1f}%)</span>'
                '</div>',
                unsafe_allow_html=True
            )

        # ── 등급 분포 ──
        grade_counts = {}
        for s in entries:
            grade_counts[s["grade"]] = grade_counts.get(s["grade"], 0) + 1

        dist_html = ""
        for g in sorted(grade_counts.keys()):
            gc = grade_color(g)
            dist_html += (
                f'<span style="display:inline-block;background:{gc}22;color:{gc};'
                f'border:1px solid {gc}55;border-radius:999px;'
                f'padding:0.2rem 0.7rem;font-size:0.78rem;font-weight:600;margin:0.15rem;">'
                f'{g}등급: {grade_counts[g]}과목</span>'
            )
        st.markdown(
            f'<div style="margin:1rem 0 0.5rem;">'
            f'<span style="color:{T["TEXT2"]};font-size:0.82rem;font-weight:700;">'
            f'등급 분포: </span><br>{dist_html}</div>',
            unsafe_allow_html=True
        )

        # ── 시뮬레이션 ──
        st.markdown(
            f'<div style="color:{T["TEXT2"]};font-size:0.85rem;'
            'font-weight:700;margin:1rem 0 0.5rem;">'
            '만약 등급을 올린다면? (시뮬레이션)</div>',
            unsafe_allow_html=True
        )

        simulations = []
        for s in entries:
            if s["grade"] > 1:
                new_ws = weighted_sum - s["unit"]
                new_avg = new_ws / total_units
                simulations.append({
                    "name": s["name"],
                    "unit": s["unit"],
                    "current": s["grade"],
                    "new_grade": s["grade"] - 1,
                    "new_avg": new_avg,
                    "improvement": avg_grade - new_avg,
                })
        simulations.sort(key=lambda x: x["improvement"], reverse=True)

        if simulations:
            for sim in simulations[:5]:
                ic = "#059669" if sim["improvement"] > 0.1 else "#65a30d"
                st.markdown(
                    '<div class="subject-row">'
                    f'<span style="flex:3;"><b>{sim["name"]}</b> '
                    f'<span style="color:{T["MUTED"]};font-size:0.78rem;">'
                    f'({sim["current"]}→{sim["new_grade"]}등급)</span></span>'
                    f'<span style="flex:2;text-align:center;color:{T["TEXT2"]};">'
                    f'{sim["unit"]}단위</span>'
                    f'<span style="flex:2;text-align:right;">'
                    f'평균 <b style="color:{ic};">{sim["new_avg"]:.2f}</b>등급 '
                    f'<span style="color:{ic};font-size:0.78rem;">'
                    f'(+{sim["improvement"]:.2f})</span></span>'
                    '</div>',
                    unsafe_allow_html=True
                )
            st.markdown(
                f'<p style="color:{T["TEXT2"]};font-size:0.8rem;margin-top:0.5rem;">'
                '단위수가 큰 과목의 등급을 올리면 평균이 더 크게 변합니다!</p>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<p style="color:{T["TEXT2"]};font-size:0.85rem;">'
                '모든 과목이 1등급입니다!</p>',
                unsafe_allow_html=True
            )

        st.markdown('</div>', unsafe_allow_html=True)

        # ── 9↔5 환산표 ──
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(
            f'<div style="color:{T["TEXT2"]};font-size:0.85rem;'
            'font-weight:700;margin-bottom:0.5rem;">9등급제 vs 5등급제 환산 참고표</div>'
            '<table class="grade-table">'
            '<tr><th>9등급제</th><th>석차 비율</th><th>5등급제</th><th>석차 비율</th></tr>'
            '<tr>'
            '<td><b style="color:#7c3aed;">1등급</b></td><td>~4%</td>'
            '<td rowspan="2"><b style="color:#7c3aed;">1등급</b></td>'
            '<td rowspan="2">~10%</td>'
            '</tr>'
            '<tr>'
            '<td><b style="color:#2563eb;">2등급</b></td><td>~11%</td>'
            '</tr>'
            '<tr>'
            '<td><b style="color:#0891b2;">3등급</b></td><td>~23%</td>'
            '<td rowspan="2"><b style="color:#2563eb;">2등급</b></td>'
            '<td rowspan="2">~34%</td>'
            '</tr>'
            '<tr>'
            '<td><b style="color:#059669;">4등급</b></td><td>~40%</td>'
            '</tr>'
            '<tr>'
            '<td><b style="color:#65a30d;">5등급</b></td><td>~60%</td>'
            '<td><b style="color:#059669;">3등급</b></td><td>~66%</td>'
            '</tr>'
            '<tr>'
            '<td><b style="color:#d97706;">6등급</b></td><td>~77%</td>'
            '<td rowspan="2"><b style="color:#d97706;">4등급</b></td>'
            '<td rowspan="2">~90%</td>'
            '</tr>'
            '<tr>'
            '<td><b style="color:#ea580c;">7등급</b></td><td>~89%</td>'
            '</tr>'
            '<tr>'
            '<td><b style="color:#dc2626;">8등급</b></td><td>~96%</td>'
            '<td rowspan="2"><b style="color:#dc2626;">5등급</b></td>'
            '<td rowspan="2">~100%</td>'
            '</tr>'
            '<tr>'
            '<td><b style="color:#9f1239;">9등급</b></td><td>~100%</td>'
            '</tr>'
            '</table>'
            f'<p style="color:{T["TEXT2"]};font-size:0.8rem;margin-top:0.5rem;">'
            '위 환산표는 석차 비율 기준 대략적인 참고용입니다.</p>',
            unsafe_allow_html=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # ── AI 분석 ──
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        with st.spinner("AI가 내신을 분석하고 진로 맞춤 피드백을 생성하는 중..."):

            subj_sum = "\n".join(
                f"- {s['name']}: {s['unit']}단위 {s['grade']}등급"
                for s in entries
            )

            if grade_system == "9등급제":
                gsd = (
                    "9등급 상대평가 석차등급제.\n"
                    "1등급(상위 4%), 2등급(상위 11%), 3등급(상위 23%), "
                    "4등급(상위 40%), 5등급(상위 60%), 6등급(상위 77%), "
                    "7등급(상위 89%), 8등급(상위 96%), 9등급(나머지).\n"
                    "수시 학생부교과전형은 보통 1~3등급을 요구합니다."
                )
            else:
                gsd = (
                    "5등급 상대평가 석차등급제.\n"
                    "1등급(상위 10%), 2등급(상위 34%), 3등급(상위 66%), "
                    "4등급(상위 90%), 5등급(나머지).\n"
                    "기존 9등급제보다 등급 구간이 넓어 변별력이 줄어들며, "
                    "5등급제 1등급(상위 10%)은 9등급제의 약 1~2등급 사이에 해당합니다."
                )

            sim_text = ""
            if simulations:
                sim_text = "\n[시뮬레이션 - 각 과목 1등급씩 올렸을 때]\n"
                for sim in simulations[:3]:
                    sim_text += (
                        f"- {sim['name']} ({sim['current']}→{sim['new_grade']}등급): "
                        f"평균 {sim['new_avg']:.2f}등급 (+{sim['improvement']:.2f})\n"
                    )

            prompt = (
                f"학생 정보:\n"
                f"- 나이: {user_age}세\n"
                f"- 등급제: {grade_system} (상대평가)\n"
                f"- 희망 진로: {career_field}\n"
                f"- 희망 학과: {final_dept}\n"
                f"- 계열: {career_category}\n\n"
                f"현재 내신 성적:\n{subj_sum}\n\n"
                f"평균 내신 등급: {avg_grade:.2f}등급 ({grade_system})\n"
                f"총 단위수: {total_units}단위\n"
                f"{sim_text}\n"
                f"[등급제 기준]\n{gsd}\n\n"
                f"다음을 분석해주세요:\n"
                f"1. 현재 내신 수준 평가 - {final_dept} 목표 시 충분한지 솔직하게\n"
                f"2. 과목별 분석 - 잘하는 과목, 개선 필요 과목, {career_field}에서 중요한 과목\n"
                f"3. 목표 등급 - {final_dept} 진학을 위한 목표와 구체적 전략\n"
                f"4. 학습 전략 - {user_age}세에 맞는 공부법, {career_field} 연계 방향\n"
                f"5. 격려 메시지\n\n"
                f"정해진 틀 없이 이 학생의 상황에 맞는 유연하고 따뜻한 조언을 해주세요."
            )

            sys_text = (
                f"고등학교 내신 분석 전문가이자 입시 상담 교사입니다. "
                f"학생에게 적용되는 등급제({grade_system}, 상대평가)를 정확히 이해하고 분석해주세요. "
                f"학생의 진로({career_field})와 희망 학과({final_dept})를 깊이 이해하고 "
                f"현실적이면서도 따뜻한 조언을 해주세요. "
                f"한국 대학 입시 제도(수시 학생부교과, 학생부종합, 논술, 정시 등)를 "
                f"정확히 이해하고 한국어로 답변해주세요."
            )

            try:
                client = anthropic.Anthropic(api_key=api_key)
                response = client.messages.create(
                    model=selected_model,
                    max_tokens=4096,
                    system=sys_text,
                    messages=[{"role": "user", "content": prompt}]
                )
                answer = response.content[0].text
                in_tok = response.usage.input_tokens
                out_tok = response.usage.output_tokens

                st.session_state.total_input_tokens += in_tok
                st.session_state.total_output_tokens += out_tok

                cost = (
                    (in_tok / 1_000_000) * MODELS[selected_model]["input_price"]
                    + (out_tok / 1_000_000) * MODELS[selected_model]["output_price"]
                )

                st.markdown(
                    '<div class="card"><h3>AI 내신 분석 & 진로 맞춤 피드백</h3>',
                    unsafe_allow_html=True
                )
                st.markdown(answer)
                st.markdown(
                    '<div class="success-msg">'
                    f'분석 완료 | 입력 {in_tok:,} + 출력 {out_tok:,} 토큰 '
                    f'| ${cost:.4f} (약 {cost * 1400:.0f}원) '
                    f'| {model_info["icon"]} {model_info["display"]}'
                    '</div>',
                    unsafe_allow_html=True
                )
                st.markdown('</div>', unsafe_allow_html=True)

            except anthropic.AuthenticationError:
                st.error("API 키가 올바르지 않습니다.")
            except anthropic.RateLimitError:
                st.error("요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.")
            except Exception as e:
                st.error(f"AI 분석 중 오류 발생: {e}")
