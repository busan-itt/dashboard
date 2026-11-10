"""Supplied HTML pages, with live selection of saved simulation conditions."""
from pathlib import Path
import json
import re
import streamlit as st

ROOT = Path(__file__).parent


def render_section(section_id: str) -> None:
    source = (ROOT / "assets" / "presentation.html").read_text(encoding="utf-8")
    match = re.search(rf'<section id="{re.escape(section_id)}">.*?</section>', source, re.S)
    if match is None:
        st.error("발표 자료의 해당 영역을 찾을 수 없습니다.")
        return
    content = dynamic_results() if section_id == "s3" else match.group(0)
    css = (ROOT / "presentation.css").read_text(encoding="utf-8")
    st.html(f'<style>{css}</style><div class="presentation-content">{content}</div>')


def dynamic_results() -> str:
    policy = st.segmented_control("연결선 조정 방식", ["선별", "전체"], default="선별", key="live_policy") or "선별"
    if st.session_state.get("live_hours", 48) not in [24, 48, 96]:
        st.session_state.live_hours = 48
    hours = st.select_slider("요청 앞당김 시간", options=[24, 48, 96],
                             value=48, format_func=lambda h: f"{h}시간", key="live_hours")
    st.caption("네 KPI의 결과가 함께 확인된 24·48·96시간을 비교합니다.")
    data = json.loads((ROOT / "data" / "simulation_all_results.json").read_text(encoding="utf-8"))
    rows = {r["scenario"]: r for r in data["rows"] if r["policy"] == policy and r["hours"] == hours}
    a, c = rows["A"], rows["C"]
    mean_after = data["baseline_mean_h_rounded"] * (1 - a["reduction_pct"] / 100)

    def bars(metric, unit, scale):
        max_value = max(float(r[metric]) * scale for r in rows.values())
        limit = max(max_value * 1.08, 0.01)
        labels = {"A": "A 기존", "B": "B 인접 공유", "C": "C 전체 통합"}
        html = ""
        for key in "ABC":
            value = float(rows[key][metric]) * scale
            width = value / limit * 100
            accent = " hi" if key == "C" else ""
            html += (f'<div class="brow"><span class="bn">{labels[key]}</span>'
                     f'<span class="track"><span class="bar{accent}" style="width:{width:.3f}%"></span></span>'
                     f'<span class="bv">{value:.2f}{unit}</span></div>')
        return html

    approximate = ""
    if a["realization_pct"] is not None and c["realization_pct"] is not None:
        real_a, real_c = a["realization_pct"], c["realization_pct"]
    elif policy == "전체" and hours in [24, 48, 96]:
        real_a, real_c = {24: (88, 100), 48: (85, 100), 96: (78, 100)}[hours]
        approximate = "약 "
    return f'''<section id="s3">
<div class="tag">3 · 시뮬레이션 결과</div>
<h1>{policy} 조정 {hours}시간 · 야드 체류와 접안 지연 비교</h1>
<p class="sub">{policy} 정책 · {hours}시간 앞당김 · 최소 연결 간격 24시간 · 기존 평균 227.2시간 대비</p>
<div class="grid g4">
<div class="card"><div class="cap">체류 감소율 (A)</div><div class="num">{a['reduction_pct']:.2f}<small>%</small></div><div class="cap">227.2시간 → 약 {mean_after:.1f}시간</div></div>
<div class="card"><div class="cap">다른 선박 지연 (A)</div><div class="num">{a['other_delay_h']*60:.2f}<small>분</small></div><div class="cap">공유 없이 일정만 조정할 때</div></div>
<div class="card"><div class="cap">다른 선박 지연 (C)</div><div class="num">{c['other_delay_h']*60:.2f}<small>분</small></div><div class="cap">전체 통합으로 선석 공유 시</div></div>
<div class="card"><div class="cap">일정 조정 실현율 (C)</div><div class="num">{real_c:.1f}<small>%</small></div><div class="cap">A {approximate}{real_a:.1f}% → C {approximate}{real_c:.1f}%</div></div>
</div>
<div class="grid g2" style="margin-top:12px">
<div class="card"><div class="mlabel">야드 체류 감소율</div>{bars('reduction_pct','%',1)}</div>
<div class="card"><div class="mlabel">다른 선박 접안 지연</div>{bars('other_delay_h','분',60)}</div>
</div>
<div class="take">같은 {hours}시간 조정 조건에서 A·B·C의 체류 감소율과 다른 선박의 지연, 일정 조정 실현율을 비교합니다.</div>
<p class="foot">최종 노트북의 조건별 저장 결과 · 평균 체류는 반올림된 227.2시간 기준 근사치 · A의 95% 구간 {a['ci_lower_pct']:.2f}~{a['ci_upper_pct']:.2f}% · 전체 정책 실현율은 정수 반올림 값</p>
</section>'''
