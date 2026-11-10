"""Streamlit version of the Port Analytics portfolio prototype.

The legacy dashboard uses UI samples. Current-state and correlation report
pages display the team's notebook results.
"""

from __future__ import annotations

from base64 import b64encode
from html import escape
from math import sin
from pathlib import Path
import json

import pandas as pd
import streamlit as st
from improvement_content import views as improvement_views

ROOT = Path(__file__).parent
TERMINALS = (
    ("PNC", 198_000, 84, 31.8, 67.0, "#9FBBC9"),
    ("PNIT", 174_000, 76, 29.4, 62.0, "#6F98B0"),
    ("HJNC", 163_000, 71, 28.8, 59.0, "#1F4E68"),
    ("HPNT", 149_000, 66, 27.9, 64.0, "#C6D8E3"),
    ("BNCT", 139_000, 61, 27.1, 57.0, "#7FA6BB"),
    ("BCT", 118_000, 54, 25.8, 53.0, "#B0C9D8"),
)
CARGO_FACTORS = {"전체 화물": 1.0, "수입": 0.34, "수출": 0.31, "환적": 0.35}
MONTHS = pd.period_range("2025-11", periods=12, freq="M").strftime("%Y.%m").tolist()


def html(body: str) -> None:
    st.html(body)



def sample_state(period: int, terminal: str, cargo: str) -> dict:
    selected = [item for item in TERMINALS if terminal == "전체 터미널" or item[0] == terminal]
    factor = CARGO_FACTORS[cargo]
    current = []
    for index in range(12 - period, 12):
        total = sum(
            base * (1 + sin(index * 0.72 + terminal_index * 0.45) * 0.075)
            * (0.94 + index * 0.012) * factor
            for terminal_index, (_, base, *_rest) in enumerate(selected)
        )
        current.append(round(total))
    previous = [round(value * 0.956) for value in current]
    volume = sum(current)
    vessels = round(sum(item[2] for item in selected) * period * factor)
    productivity = sum(item[3] for item in selected) / len(selected)
    yard = sum(item[4] for item in selected) / len(selected)
    rows = []
    for index, (name, base, monthly_vessels, mph, occupancy, color) in enumerate(selected):
        value = round(base * period * factor * (1 + sin(index * 0.85 + period * 0.12) * 0.055))
        rows.append((name, value, round(monthly_vessels * period * factor), mph, occupancy, color))
    return {
        "months": MONTHS[-period:], "current": current, "previous": previous,
        "volume": volume, "vessels": vessels, "productivity": productivity,
        "yard": yard, "rows": sorted(rows, key=lambda row: row[1], reverse=True),
    }


def reset_filters() -> None:
    st.session_state.period = 12
    st.session_state.terminal = "전체 터미널"
    st.session_state.cargo = "전체 화물"


def dashboard() -> None:
    period = st.session_state.get("period", 12)
    terminal = st.session_state.get("terminal", "전체 터미널")
    cargo = st.session_state.get("cargo", "전체 화물")
    html(f"""
      <section class="hero">
        <div class="hero-copy"><p class="eyebrow">TERMINAL PERFORMANCE OVERVIEW</p>
          <h1>항만 운영 데이터를<br>한 곳에서 살펴봅니다.</h1>
          <p>대시보드와 프로젝트 문서를 함께 보여주는 포트폴리오 화면 시안입니다. 아래 지표는 동작 확인용 샘플입니다.</p>
        </div>
        <div class="hero-summary"><span class="sample-badge">SAMPLE DATA</span>
          <dl><div><dt>분석 기간</dt><dd>최근 {period}개월</dd></div>
            <div><dt>대상 터미널</dt><dd>{escape(terminal)}</dd></div>
            <div><dt>화물 구분</dt><dd>{escape(cargo)}</dd></div></dl>
        </div>
      </section>
    """)

    with st.container(key="filters"):
        html('<div class="filter-title"><h2>≡ &nbsp;분석 조건</h2><p>조건을 변경하면 모든 지표와 차트가 함께 갱신됩니다.</p></div>')
        columns = st.columns([1, 1, 1, 0.55], gap="small")
        with columns[0]:
            period = st.selectbox("분석 기간", [6, 12], index=1, format_func=lambda value: f"최근 {value}개월", key="period")
        with columns[1]:
            terminal = st.selectbox("터미널", ["전체 터미널", *(item[0] for item in TERMINALS)], key="terminal")
        with columns[2]:
            cargo = st.selectbox("화물 구분", list(CARGO_FACTORS), key="cargo")
        with columns[3]:
            st.button("초기화", on_click=reset_filters, width="stretch")

    state = sample_state(period, terminal, cargo)
    previous_total = sum(state["previous"])
    change = (state["volume"] / previous_total - 1) * 100
    yard_status = "안정 범위" if state["yard"] < 70 else "주의 범위"
    cards = (
        ("총 물동량", "TEU", f'{state["volume"]:,.0f} TEU', f'↑ {change:.1f}% 상승 · 이전 기간 대비'),
        ("선박 작업량", "VSL", f'{state["vessels"]:,}척', "샘플 기준"),
        ("평균 생산성", "MPH", f'{state["productivity"]:.1f} MPH', "샘플 기준"),
        ("야드 점유율", "YARD", f'{state["yard"]:.1f}%', f'{yard_status} · 샘플 기준'),
    )
    html('<section class="kpi-grid">' + "".join(
        f'<article class="kpi-card"><div><span>{label}</span><span>{code}</span></div>'
        f'<strong>{value}</strong><p>{detail}</p><i></i></article>'
        for label, code, value, detail in cards
    ) + '</section>')

    left, right = st.columns([1.65, 0.8], gap="medium")
    with left, st.container(key="trend_panel"):
        html(f'<div class="panel-head"><span>THROUGHPUT TREND</span><h2>월별 물동량 추이</h2>'
             f'<p><strong>{state["volume"]:,} TEU</strong>　선택 기간 누적 물동량</p></div>')
        chart = pd.DataFrame({"월": state["months"], "선택 기간": state["current"], "이전 기간": state["previous"]})
        st.line_chart(chart, x="월", y=["선택 기간", "이전 기간"], color=["#6F98B0", "#C6D8E3"], height=300)
    with right, st.container(key="status_panel"):
        html('<div class="panel-head"><span>YARD STATUS</span><h2>작업 상태 분포</h2><p>샘플 기준</p></div>')
        status = [("완료", 46, "#9FBBC9"), ("작업 중", 29, "#6F98B0"),
                  ("대기", 17, "#1F4E68"), ("점검", 8, "#D7E3EB")]
        legend = "".join(f'<div><i style="background:{color}"></i><span>{name}</span><strong>{share}%</strong></div>'
                         for name, share, color in status)
        html('<div class="donut"><span><strong>100%</strong><small>상태 분포</small></span></div>'
             f'<div class="status-list">{legend}</div>')

    with st.container(key="terminal_panel"):
        html('<div class="panel-head"><span>TERMINAL COMPARISON</span><h2>터미널별 물동량 비교</h2><p>단위: 샘플 TEU</p></div>')
        maximum = max(row[1] for row in state["rows"])
        bars = "".join(
            f'<div class="terminal-row"><strong>{name}</strong><div class="bar-track">'
            f'<i style="width:{value / maximum * 100:.1f}%;background:{color}"></i></div>'
            f'<span>{value:,} TEU</span></div>'
            for name, value, _vessels, _mph, _yard, color in state["rows"]
        )
        html(f'<div class="terminal-bars">{bars}</div>')

    with st.container(key="detail_panel"):
        html('<div class="panel-head"><span>DETAILED ANALYSIS</span><h2>터미널 운영 상세</h2>'
             f'<p>{escape(terminal)} · 최근 {period}개월 · {escape(cargo)}</p></div>')
        detail = pd.DataFrame(state["rows"], columns=["터미널", "물동량", "선박 작업", "생산성", "야드 점유율", "색상"])
        st.dataframe(detail.drop(columns="색상"), hide_index=True, width="stretch")

    st.info("시안 안내: 모든 수치는 화면 동작을 보여주기 위한 샘플입니다. 실제 터미널 실적이나 운영 상태를 의미하지 않습니다.")


def document_page(kicker: str, title: str, description: str, body: str = "") -> None:
    html(f'''<div class="portfolio-page"><div class="page-heading"><span>{escape(kicker)}</span>
      <h1>{escape(title)}</h1><p>{escape(description)}</p></div>{body}</div>''')


def card(kicker: str, title: str, description: str, extra: str = "") -> str:
    return (f'<article class="portfolio-card"><small>{escape(kicker)}</small>'
            f'<h2>{escape(title)}</h2><p>{escape(description)}</p>{extra}</article>')


def landing(kicker: str, title: str, description: str, links: tuple[tuple[str, str], ...]) -> None:
    nav = '<nav class="section-links" aria-label="하위 페이지">' + ''.join(
        f'<a href="/{escape(path)}">{escape(label)}</a>' for path, label in links
    ) + '</nav>'
    document_page(kicker, title, description, nav)


def home_icon(name: str) -> str:
    paths = {
        "home": '<path d="m3 10 9-7 9 7v10a1 1 0 0 1-1 1h-5v-8H9v8H4a1 1 0 0 1-1-1Z"/>',
        "dashboard": '<path d="M3 21V13h4v8Zm7 0V8h4v13Zm7 0V3h4v18Z"/>',
        "intro": '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h4"/>',
        "analysis": '<path d="m12 3 10 5-10 5L2 8Zm-10 9 10 5 10-5M2 16l10 5 10-5"/>',
        "improvement": '<path d="M9 18h6m-6 3h6M8 14a7 7 0 1 1 8 0c-1 .8-1 2-1 4H9c0-2 0-3.2-1-4Z"/>',
        "attachments": '<path d="m8 12 6-6a3 3 0 0 1 4 4l-8 8a5 5 0 0 1-7-7l9-9a4 4 0 0 1 6 6l-9 9a2 2 0 0 1-3-3l8-8"/>',
        "arrow": '<path d="M4 12h16m-6-6 6 6-6 6"/>',
    }
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" '
            f'aria-hidden="true">{paths[name]}</svg>')


def home() -> None:
    summaries = (
        ("항만 물류 흐름 분석", "연도별·부두별 물동량을 바탕으로 부산항 물류 흐름과 변화를 살펴봅니다."),
        ("인프라 투자 계획 수립", "물동량 추이와 처리량을 통해 시설 확충과 운영 개선의 검토 방향을 정리합니다."),
        ("수출입 물량 예측", "수출입 물량의 변동 패턴을 살펴 향후 수요 분석의 기초 자료로 활용합니다."),
        ("항만 경쟁력 비교 연구", "주요 항만의 물동량을 비교하고 부산항의 현황과 개선 방향을 검토합니다."),
    )
    summary_body = ''.join(
        f'<div class="home-summary-item"><h3>{escape(title)}</h3><p>{escape(description)}</p></div>'
        for title, description in summaries
    )
    destinations = (
        ("dashboard", "대시보드", "분석 내용을 한눈에 확인합니다.", "dashboard", ()),
        ("intro", "프로젝트 소개", "프로젝트 배경과 목표를 소개합니다.", "intro",
         (("intro-problem", "문제제기"), ("intro-status", "현황 분석"))),
        ("dashboard-summary", "분석 내용", "데이터와 분석 과정을 살펴봅니다.", "analysis", ()),
        ("improvement", "개선안", "분석을 바탕으로 제안한 개선안을 확인합니다.", "improvement",
         (("intro-solution", "시뮬레이션"), ("simulation", "시뮬레이션 결과"),
          ("improvement-results", "개선안 결과"))),
        ("attachments", "첨부", "사용한 데이터와 초기 개선안 기획을 확인합니다.", "attachments",
         (("used-data", "사용한 데이터"), ("planning", "초기 개선안 기획"))),
    )
    navigation = []
    for path, title, description, icon, children in destinations:
        child_links = ''.join(
            f'<a href="{escape(child_path)}">{escape(label)}</a>' for child_path, label in children
        )
        navigation.append(
            f'<article class="home-nav-card"><a class="home-card-link" href="{escape(path)}" '
            f'aria-label="{escape(title)} 열기"><span class="home-card-icon">{home_icon(icon)}</span>'
            f'<div class="home-card-copy"><h3>{escape(title)}</h3><p>{escape(description)}</p></div>'
            f'<span class="home-card-arrow">{home_icon("arrow")}</span></a>'
            + (f'<nav class="home-card-children" aria-label="{escape(title)} 하위 목차">{child_links}</nav>'
               if children else '')
            + '</article>'
        )
    html(f'''<div class="home-page">
      <header class="home-heading"><h1>부산항 데이터 분석 프로젝트</h1>
        <p>프로젝트의 핵심 내용을 확인하고, 필요한 페이지로 이동하세요.</p></header>
      <section class="home-summary" aria-labelledby="home-summary-title">
        <div class="home-summary-label"><h2 id="home-summary-title"><span>Quick <b>AI</b></span><br>Summary</h2>
          <p>AI 요약</p><small>예시 문안</small></div>
        <div class="home-summary-content">{summary_body}</div>
      </section>
      <section class="home-explore" aria-labelledby="home-explore-title">
        <div class="home-explore-heading"><h2 id="home-explore-title">프로젝트 둘러보기</h2>
          <p>원하는 목차를 선택해 자세한 내용을 확인하세요.</p></div>
        <div class="home-nav-grid">{''.join(navigation)}</div>
      </section>
    </div>''')


def home_analysis() -> None:
    document_page("ANALYSIS SUMMARY", "분석 내용 요약", "홈 / 분석 내용 요약",
                  card("ANALYSIS SUMMARY", "분석 내용 요약",
                       "현재 프로젝트에 포함된 대시보드와 문서형 화면을 소개합니다. 수치와 차트는 UI 동작을 확인하기 위한 샘플이며, 실제 분석 결과 문안은 아직 연결되지 않았습니다.",
                       '<div class="chips"><span>대시보드 지표</span><span>분석 기록</span><span>자료 이미지</span></div>'))


def home_ai() -> None:
    document_page("AI SUMMARY", "AI 분석 요약", "홈 / AI 분석 요약",
                  card("AI SUMMARY", "AI 분석 요약", "AI 분석 결과 또는 요약 문안이 현재 시안에 없어, 내용 확정 후 연결할 자리입니다."))


def dashboard_home() -> None:
    landing("DASHBOARD", "대시보드", "분석 내용을 확인합니다.",
            (("dashboard-data", "분석 내용"),))


def attachments() -> None:
    landing("ATTACHMENTS", "첨부", "사용한 데이터와 초기 개선안 기획을 확인합니다.",
            (("used-data", "사용한 데이터"), ("planning", "초기 개선안 기획")))


def used_data() -> None:
    document_page("DATA SOURCES", "사용한 데이터", "첨부 / 사용한 데이터",
                  card("CONTENT PLACEHOLDER", "사용한 데이터",
                       "분석에 사용한 데이터의 출처, 수집 기간, 주요 항목을 정리할 페이지입니다."))


def dashboard_summary() -> None:
    landing("ANALYSIS", "분석 내용", "환적 경로별 상관관계 분석과 결론을 확인합니다.",
            (("analysis-dgt-odt", "DGT_ODT"), ("analysis-hjnc-odt", "HJNC_ODT"),
             ("analysis-itt", "DGT <-> HJNC ITT")))


def correlation_report(key: str, title: str) -> None:
    with st.container(key="correlation_report"):
        render_correlation_report(key, title)


def render_correlation_report(key: str, title: str) -> None:
    st.html(ROOT / "correlation.css")
    report_root = ROOT / "assets" / "correlation-analysis"
    chart_root = report_root / "unified"
    reports = json.loads((chart_root / "reports.json").read_text(encoding="utf-8"))
    document_page("CORRELATION ANALYSIS", title, "독립변수와 야드 장치 기간의 관계")
    selected_key = key
    if key == "itt":
        selected_key = st.radio(
            "환적 방향", ("forward", "reverse"), horizontal=True,
            format_func=lambda value: {"forward": "DGT → HJNC", "reverse": "HJNC → DGT"}[value],
            key="analysis_itt_direction",
        )
    report = reports[selected_key]

    def figure(filename: str, description: str) -> str:
        encoded = b64encode((chart_root / filename).read_bytes()).decode("ascii")
        return (f'<figure class="report-figure"><img src="data:image/png;base64,{encoded}" '
                f'alt="{escape(description)}"></figure>')

    summary = '<div class="correlation-page"><div class="report-metrics">' + ''.join(
        f'<div><span>{label}</span><strong>{escape(value)}</strong></div>'
        for label, value in (("기준 표본", report["sample"]), ("측정 구간", report["definition"]),
                             ("분석 단위", report["unit"]))
    ) + '</div><section class="report-section"><div class="report-section-title"><h2>독립변수별 상관관계</h2><span>공통 눈금 −1 ~ 1</span></div>'
    summary += figure(report["comparison"], "Pearson r · 공통 눈금 −1 ~ 1")
    summary += f'<p class="report-caption">{escape(report["note"])}</p></section></div>'
    html(summary)

    heading, selector = st.columns([3, 2], vertical_alignment="center")
    with heading:
        html('<div class="correlation-page"><h2 class="report-scatter-heading">관측값과 회귀선</h2></div>')
    with selector:
        selected_plot = st.selectbox(
            "독립변수", range(len(report["plots"])),
            format_func=lambda index: report["plots"][index]["label"],
            key=f"analysis_variable_{selected_key}",
        )
    plot = report["plots"][selected_plot]
    unit_class = "container" if selected_key == "hjnc" else "voyage"
    body = f'<div class="correlation-page"><section class="report-section report-scatter"><div class="report-legend"><span><b class="report-dot {unit_class}"></b>실제 관측값</span><span><b class="report-line"></b>선형 회귀선</span></div>'
    body += figure(plot["image"], f'{plot["label"]} · 실제 관측값과 선형 회귀선 · N={plot["n"]:,} · r={plot["r"]:.3f}')
    body += '</section><section class="report-section"><h2>선석별 환적 작업 물동량</h2>'
    body += f'<p class="report-caption">{escape(report["berth_meta"])}</p>'
    body += figure(report["berth"][0]["image"], report["berth"][0]["label"])
    body += f'<p>{escape(report["berth_volume_note"])}</p></section>'
    body += '<section class="report-section"><h2>선석별 장치 기간 상관관계</h2>'
    body += figure(report["berth"][1]["image"], report["berth"][1]["label"])
    body += f'<p>{escape(report["berth_correlation_note"])}</p></section>'
    body += '<section class="report-section"><h2>분석 결론</h2>'
    body += f'<blockquote>{escape(report["conclusion"])}</blockquote>'
    body += '<p class="report-caption">상관관계는 인과관계를 의미하지 않습니다.</p></section></div>'
    html(body)


def analysis_dgt_odt() -> None:
    correlation_report("dgt", "DGT_ODT")


def analysis_hjnc_odt() -> None:
    correlation_report("hjnc", "HJNC_ODT")


def analysis_itt() -> None:
    correlation_report("itt", "DGT <-> HJNC ITT")


def intro() -> None:
    landing("PROJECT OVERVIEW", "프로젝트 소개", "문제제기와 현황 분석을 각각의 페이지에서 확인합니다.",
            (("intro-problem", "문제제기"), ("intro-status", "현황 분석")))


def analysis_figure(filename: str, description: str) -> str:
    chart_path = ROOT / "assets" / "preliminary-analysis" / filename
    encoded = b64encode(chart_path.read_bytes()).decode("ascii")
    image_id = f'problem-chart-{chart_path.stem}'
    return (f'<figure class="problem-analysis-figure">'
            f'<img id="{image_id}" src="data:image/png;base64,{encoded}" '
            f'alt="{escape(description)}"></figure>')


def process_flow(kind: str) -> str:
    """Accessible process diagrams with local, decorative SVG line icons."""
    ship = '<path d="M4 19h32l-4 9H10Z"/><path d="M9 19V9h19v10M14 9V5h6v4M14 14h4m5 0h2M4 32q4-4 8 0t8 0t8 0t8 0"/>'
    crane = '<path d="M7 33V5h4v28M7 6h27L11 15M7 33H3m8 0h5M30 7v8"/><rect x="22" y="24" width="14" height="9" rx="1"/>'
    yard = '<rect x="4" y="23" width="15" height="10" rx="1"/><rect x="21" y="23" width="15" height="10" rx="1"/><rect x="12" y="11" width="15" height="10" rx="1"/><path d="M9 26v4m5-4v4m12-4v4m5-4v4M17 14v4m5-4v4"/>'
    truck = '<rect x="3" y="12" width="21" height="16" rx="1"/><path d="M24 19h8l5 6v3H24M29 20v5h7M3 28h34M8 16v7m5-7v7m5-7v7"/><circle cx="10" cy="30" r="3"/><circle cx="30" cy="30" r="3"/>'
    icons = {
        "arrival": ship, "departure": ship, "yard": yard, "truck": truck,
        "unload": crane + '<path d="M30 15v6m-3-3 3 3 3-3"/>',
        "load": crane + '<path d="M30 21v-6m-3 3 3-3 3 3"/>',
    }
    middle = [("yard", "야드·선측 장치", "동일 터미널", False)] if kind == "odt" else [
        ("yard", "출발 부두 장치", "A부두 야드", False),
        ("truck", "부두 간 이동", "트럭으로 운송", True),
        ("yard", "도착 부두 장치", "B부두 야드", True),
    ]
    steps = [("arrival", "입항", "모선 도착", False), ("unload", "양하", "컨테이너 내리기", False),
             *middle, ("load", "적하", "연결선에 싣기", False), ("departure", "출항", "연결선 출발", False)]
    items = []
    for index, (icon, label, detail, extra) in enumerate(steps, 1):
        stroke = "#C3836F" if extra else "#526D82"
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" '
               f'fill="none" stroke="{stroke}" stroke-width="1.7" stroke-linecap="round" '
               f'stroke-linejoin="round">{icons[icon]}</svg>')
        encoded = b64encode(svg.encode("utf-8")).decode("ascii")
        icon_image = f'<img src="data:image/svg+xml;base64,{encoded}" alt="" width="48" height="48">'
        items.append(f'<li class="process-step{" process-step-extra" if extra else ""}">'
                     f'<span class="process-number">{index:02d}</span><span class="process-icon">{icon_image}</span>'
                     f'<strong>{label}</strong><small>{detail}</small></li>')
    name = "자부두" if kind == "odt" else "타부두"
    return (f'<ol class="problem-icon-flow" style="--step-count:{len(steps)}" '
            f'aria-label="{name} 환적 처리 순서">{"".join(items)}</ol>')


def intro_problem() -> None:
    st.html(ROOT / "problem.css")
    body = '''<div class="problem-page">
      <section class="problem-section" aria-labelledby="problem-background">
        <div class="problem-section-heading"><span>01 / BACKGROUND</span>
          <h2 id="problem-background">환적 비중이 높은 부산항, 터미널마다 다른 ITT 의존도</h2></div>
        <p class="problem-lead">부산항은 환적 비중이 높은 항만입니다. 터미널별 자부두 환적(ODT)과
          타부두 환적(ITT) 비율을 분석한 결과, ITT 의존도에는 큰 차이가 존재합니다.</p>
        <div class="problem-stat-grid">
          <article class="problem-stat"><h3>부산항 환적 비중</h3><strong>약 57<span>%</span></strong>
            <p>2025년 부산항 전체 물동량 대비</p></article>
          <article class="problem-stat"><h3>부산신항 환적 비중</h3><strong>약 84.3<span>%</span></strong>
            <p>2025년 부산항 전체 환적 대비</p></article>
          <article class="problem-stat"><h3>부산신항 ITT 비율</h3><strong>40<span>%</span></strong>
            <p>2025년 · 신항7부두 제외<br>전체 컨테이너 물동량 대비</p></article>
        </div>
        <p class="problem-caption">관련 자료: <a href="https://app.notion.com/p/406c0feefeda808d9091c15299f73844"
          target="_blank" rel="noopener noreferrer">프로젝트 중간 발표 자료</a></p>
      </section>

      <section class="problem-section" aria-labelledby="problem-process">
        <div class="problem-section-heading"><span>02 / PROCESS</span>
          <h2 id="problem-process">ODT와 ITT, 무엇이 다른가?</h2></div>
        <div class="problem-process-grid">
          <article class="problem-process-card"><span class="problem-type">ODT</span>
            <h3>자부두 환적</h3><p class="problem-english">On-Dock Transshipment</p>
            <p>양하와 적하를 동일한 터미널에서 처리합니다.</p>
            <!-- odt-process --></article>
          <article class="problem-process-card"><span class="problem-type">ITT</span>
            <h3>타부두 환적</h3><p class="problem-english">Inter-Terminal Transshipment</p>
            <p>컨테이너를 다른 터미널로 옮긴 뒤 적하합니다.</p>
            <!-- itt-process --></article>
        </div>
        <aside class="problem-callout"><strong>결정적 차이: 양하와 적하를 같은 터미널에서 처리하는가?</strong>
          <p>ITT에서는 부두 간 이동에 따라 추가 컨테이너 작업이 발생합니다.</p></aside>
      </section>

      <section class="problem-section" aria-labelledby="problem-impact">
        <div class="problem-section-heading"><span>03 / WHY ODT</span>
          <h2 id="problem-impact">부산항은 왜 ODT를 지향하는가?</h2></div>
        <p>부두 사이의 추가 운송을 줄여 환적 비용과 시간을 낮추고, 선사의 부산항 이용을 유도하기 위해서입니다.
          해양수산부와 부산항만공사도 ITT와 분산 운영으로 발생하는 문제를 개선 대상으로 제시하고 있습니다.</p>
        <div class="problem-table-wrap"><table class="problem-evidence-table">
          <caption>기관별로 제시한 문제와 근거 자료</caption>
          <thead><tr><th scope="col">기관</th><th scope="col">명시한 문제</th><th scope="col">근거</th></tr></thead>
          <tbody>
            <tr><th scope="row">해양수산부</th><td><strong>추가 물류비 발생</strong></td><td>2023년 BPA 집계를 인용해 부산항 ITT
              연간 232만 TEU와 추가 물류비 551억 원을 제시했습니다. <strong>2025년 수치는 아닙니다.</strong>
              <a href="https://www.mof.go.kr/doc/ko/selectDoc.do?bbsSeq=10&amp;docSeq=59556&amp;menuSeq=971"
                target="_blank" rel="noopener noreferrer">해양수산부 보도자료 · 2024.12.11.</a></td></tr>
            <tr><th scope="row">해양수산부</th><td><strong>선석 관리의 비효율</strong></td><td>소규모·분산 운영의 문제를 지적하고,
              단일 운영사가 해운동맹 물량을 처리하면 선석 관리 효율화와 ITT 최소화가 가능하다고 설명합니다.
              <a href="https://www.mof.go.kr/doc/ko/selectDoc.do?bbsSeq=10&amp;docSeq=59556&amp;menuSeq=971"
                target="_blank" rel="noopener noreferrer">해양수산부 보도자료 · 2024.12.11.</a></td></tr>
            <tr><th scope="row">부산항만공사</th><td><strong>항만 생산성 저하</strong></td><td>북항·신항의 이원화와 다수 운영사 체제로 인한
              타부두 환적화물 이동, 그에 따른 생산성 저하를 개선 대상으로 명시했습니다.
              <a href="https://www.busanpa.com/board/view.bpa?boardId=BBS_0000031&amp;dataSid=27954&amp;menuCd=DOM_000000105002001000"
                target="_blank" rel="noopener noreferrer">부산항 컨테이너 물류효율 획기적으로 개선한다 · 2022.8.11.</a></td></tr>
            <tr><th scope="row">부산항만공사</th><td><strong>비용·시간 측면의 경쟁력 저하</strong></td><td>타부두 환적이 비용과 시간 측면에서
              부산항의 경쟁력을 저해해 왔다고 명시했습니다.
              <a href="https://www.busanpa.com/board/view.bpa?boardId=BBS_0000031&amp;dataSid=34129&amp;menuCd=DOM_000000105002001000"
                target="_blank" rel="noopener noreferrer">ITT 자동운송시스템 개발 완료 · 2025.9.9.</a></td></tr>
          </tbody></table></div>
      </section>

      <section class="problem-section" aria-labelledby="problem-causes">
        <div class="problem-section-heading"><span>04 / STRUCTURAL CAUSES</span>
          <h2 id="problem-causes">그럼에도 ITT를 해야 하는 이유</h2></div>
        <p>ITT는 터미널의 분리 운영과 선사의 기항 터미널 분산으로 발생합니다.</p>
        <div class="problem-cause-grid">
          <article class="problem-cause-card"><h3>다수 운영사가 터미널을 나누어 운영</h3>
            <p>부산항의 여러 터미널은 각각 다른 회사가 나누어 운영합니다. 컨테이너를 내린 배와
              그 컨테이너를 이어서 운송할 배가 서로 다른 터미널을 이용하면, 컨테이너를 다른 터미널로 옮겨야 합니다.
              해양수산부는 이러한 분산 운영 구조를 ITT 발생 원인으로 설명합니다.</p>
            <a href="https://www.mof.go.kr/doc/ko/selectDoc.do?bbsSeq=10&amp;docSeq=59556&amp;menuSeq=971"
              target="_blank" rel="noopener noreferrer">해양수산부 · 2024.12.11.</a></article>
          <article class="problem-cause-card"><h3>해운동맹의 이용 터미널 분산·변경</h3>
            <p>선사는 배를 운항하는 회사이고, 해운동맹은 선사들이 협력해 운송 서비스를 제공하는 체계입니다.
              같은 동맹에 속하거나 서로 협력하더라도 이용하는 터미널은 다를 수 있습니다.</p>
            <p>2017년에는 2M 동맹의 이용 터미널이 기존 2부두에서 1·3부두로 나뉘었고,
              협력 관계인 HMM은 주로 4부두를 이용했습니다. KMI는 연계 운송을 하는 선사들의 이용 터미널이
              떨어져 있는 것을 ITT 증가 요인으로 제시했습니다.</p>
            <a href="https://www.nkis.re.kr/subject_view1.do?eoSeq=66004&amp;otpId=KMI00052780&amp;otpSeq=0"
              target="_blank" rel="noopener noreferrer">KMI 연구보고서 · 2017 · 국가정책연구포털 수록 초록</a></article>
        </div>
      </section>

      <section class="problem-section problem-yard-section" aria-labelledby="problem-yard-focus">
        <div class="problem-section-heading"><span>05 / ANALYSIS FOCUS</span>
          <h2 id="problem-yard-focus">선행 분석: 야드 장치 기간에 집중</h2></div>
        <p>우리 팀은 선행 분석으로 다음 현상을 발견했습니다.</p>
        <aside class="problem-yard-finding">
          <blockquote>타부두 환적이든 자부두 환적이든, 환적 총 리드타임에서 가장 시간을 많이 잡아먹는 것</blockquote>
          <h3>⇒ ‘야드 장치 기간’</h3>
        </aside>
        <p>우리 팀은 자부두 환적(ODT)과 타부두 환적(ITT)의 소요시간을 공정별로 나누어,
          어느 구간에서 가장 많은 시간이 소요되는지 살펴보았다.</p>
        <p>분석 대상은 <strong>DGT ODT, HJNC ODT, DGT → HJNC ITT, HJNC → DGT ITT</strong>이다.
          전체 소요시간은 컨테이너의 최초 반입부터 최종 반출까지이며,
          야드 장치 기간은 야드에 장치된 시점부터 온샤시 시점까지로 정의하였다.</p>

      </section>
    </div>'''
    body = body.replace("<!-- odt-process -->", process_flow("odt"))
    body = body.replace("<!-- itt-process -->", process_flow("itt"))
    document_page("01 / INTRODUCTION", "문제 제기", "부산항의 환적 구조와 ITT가 발생하는 배경을 살펴봅니다.", body)


def intro_status() -> None:
    st.html(ROOT / "problem.css")
    body = '''<div class="problem-page"><div class="problem-analysis-content">
        <p>우리 팀은 자부두 환적(ODT)과 타부두 환적(ITT)의 소요시간을 공정별로 나누어,
          어느 구간에서 가장 많은 시간이 소요되는지 살펴보았다.</p>
        <p>분석 대상은 <strong>DGT ODT, HJNC ODT, DGT → HJNC ITT, HJNC → DGT ITT</strong>이다.
          전체 소요시간은 컨테이너의 최초 반입부터 최종 반출까지이며,
          야드 장치 기간은 야드에 장치된 시점부터 온샤시 시점까지로 정의하였다.</p>
        <section class="problem-analysis-block" aria-labelledby="problem-analysis-total">
          <h3 id="problem-analysis-total">1. 분석 대상과 전체 소요시간</h3>
          <p>분석 건수: DGT ODT 122건, HJNC ODT 1,490건, DGT → HJNC ITT 17,389건, HJNC → DGT ITT 20,143건</p>
          <p>각 경로의 전체 소요시간을 평균과 중앙값으로 비교하였다.
            ITT의 전체 소요시간에는 출발·도착 터미널에서의 체류시간과 터미널 간 이동시간이 포함된다.</p>
          <!-- analysis-total-figure -->
        </section>

        <section class="problem-analysis-block" aria-labelledby="problem-analysis-stages">
          <h3 id="problem-analysis-stages">2. 공정별 소요시간 비교</h3>
          <p>ODT는 동일 터미널 내의 반입부터 반출까지를 세 구간으로 구분하였다.
            ITT는 출발·도착 터미널의 작업 과정과 터미널 간 이동을 나누어 분석하였다.</p>
          <p>야드 체류는 일 단위, 나머지 공정은 분 단위의 가로 막대로 나누어 비교하였다.
            두 영역의 단위와 눈금이 다르므로, 같은 영역 안에서 경로별 시간을 비교한다.</p>
          <h4>자부두 환적(ODT)</h4>
          <!-- analysis-odt-stages-figure -->
          <p>ODT에서는 DGT와 HJNC 모두 <strong>야드 장치부터 온샤시까지 평균 약 8일</strong>이 소요되었다.
            반면 나머지 공정은 평균 수분에서 수십 분 수준이었다.</p>
          <h4>타부두 환적(ITT)</h4>
          <!-- analysis-itt-stages-figure -->
          <p>ITT에서도 두 터미널의 야드 장치 기간은 각각 수일에 달했다.
            터미널 간 이동시간은 두 방향 모두 평균 약 10분으로,
            <strong>시간이 집중되는 구간은 출발·도착 터미널의 야드 장치 구간</strong>이었다.</p>
        </section>

        <section class="problem-analysis-block" aria-labelledby="problem-analysis-share">
          <h3 id="problem-analysis-share">3. 야드 장치 구간이 차지하는 시간 비중</h3>
          <p>야드 장치 구간의 비중을 확인하기 위해, 각 분석에서
            <strong>공정별 평균시간 합계 대비 야드 장치 구간 평균시간 합계의 비중</strong>을 계산하였다.
            ITT는 두 터미널의 야드 장치 시간을 합산하였다.</p>
          <!-- analysis-share-figure -->
          <p>분석된 네 경로에서 야드 장치 구간은 평균 공정시간 합계의 <strong>약 99.26~99.86%</strong>를 차지하였다.
            ODT와 ITT 모두 야드 장치 구간에 대부분의 시간이 집중되어 있음을 확인하였다.</p>
        </section>

        <section class="problem-analysis-block" aria-labelledby="problem-analysis-direction">
          <h3 id="problem-analysis-direction">4. 선행 분석에서 도출한 문제와 분석 방향</h3>
          <blockquote class="problem-analysis-conclusion"><strong>자부두 환적과 타부두 환적 모두,
            환적 과정에서 가장 많은 시간을 차지하는 구간은 ‘야드 장치 기간’이었다.</strong></blockquote>
          <p class="problem-yard-goal">따라서 우리 팀은 <strong>‘야드 장치 기간’에 집중하여
            컨테이너의 전체 환적 소요시간을 줄이는 방안</strong>을 검토하고자 한다.</p>
          <p>후속 분석에서는 야드 장치 기간과 관련된 요인을 살펴보고,
            체류시간을 단축할 수 있는 개선 방향을 도출할 예정이다.</p>
        </section>
    </div></div>'''
    for marker, filename, description in (
        ("analysis-total-figure", "01-total-duration-v4.png", "네 환적 경로의 전체 소요시간 평균과 중앙값"),
        ("analysis-odt-stages-figure", "02a-odt-stage-duration-v7.png", "DGT ODT와 HJNC ODT의 공정별 평균 소요시간. 야드 체류는 일, 나머지 공정은 분 단위"),
        ("analysis-itt-stages-figure", "02b-itt-stage-duration-v7.png", "양방향 ITT의 공정별 평균 소요시간. 야드 체류는 일, 나머지 공정은 분 단위"),
        ("analysis-share-figure", "03-yard-share-v5.png", "네 환적 경로의 야드 장치 시간 비중. 약 99.26~99.86%"),
    ):
        body = body.replace(f"<!-- {marker} -->", analysis_figure(filename, description))
    document_page("02 / CURRENT STATE", "현황 분석", "환적 경로별 전체 소요시간과 공정별 분석 결과를 살펴봅니다.", body)


def intro_solution() -> None:
    improvement_views.render_section("s2")


def improvement() -> None:
    improvement_views.render_section("s1")


def simulation() -> None:
    improvement_views.render_section("s3")


def improvement_results() -> None:
    improvement_views.render_section("s4")


def planning() -> None:
    st.html(ROOT / "planning.css")
    content_root = ROOT / "assets" / "initial-plan"
    body = (content_root / "content.html").read_text(encoding="utf-8")
    encoded = b64encode((content_root / "hjnc-pnc-road.png").read_bytes()).decode("ascii")
    body = body.replace("<!-- road-image -->", f"data:image/png;base64,{encoded}")
    document_page("INITIAL PLAN", "초기 개선안 기획", "내부통행로 활용 아이디어와 KPI, 측정 한계를 정리합니다.", body)


def sources() -> None:
    body = '''<div class="gallery-grid"><figure class="portfolio-card"><div class="image-placeholder">▧<strong>이미지 자리</strong><small>대시보드 화면 또는 분석 도표</small></div>
      <figcaption><strong>시각 자료 01</strong><span>실제 이미지로 교체할 자리입니다.</span></figcaption></figure>
      <figure class="portfolio-card"><div class="image-placeholder alt">▤<strong>문서 미리보기 자리</strong><small>보고서 표지 또는 자료 이미지</small></div>
      <figcaption><strong>자료 02</strong><span>파일 설명과 출처를 적을 수 있습니다.</span></figcaption></figure></div>
      <article class="portfolio-card reading"><small>SOURCE NOTE</small><h2>참고·출처</h2>
      <p>실제 분석 이미지나 출처 목록은 아직 포함되지 않았습니다. 검증된 자료 링크와 인용 정보를 추가할 자리입니다.</p></article>'''
    document_page("REFERENCES", "참고·출처", "자료 이미지, 문서, 데이터 출처를 모아 확인할 페이지입니다.", body)


st.set_page_config(page_title="Port Analytics 시안", layout="wide", initial_sidebar_state="auto")
st.html(ROOT / "styles.css")
st.html(ROOT / "home.css")
pages = [
    st.Page(home, title="홈", icon=":material/home:", default=True),
    st.Page(home_analysis, title="프로젝트 요약", url_path="home-analysis"),
    st.Page(home_ai, title="AI 요약", url_path="home-ai"),
    st.Page(dashboard_home, title="대시보드", icon=":material/dashboard:", url_path="dashboard"),
    st.Page(dashboard, title="분석 내용", url_path="dashboard-data"),
    st.Page(improvement, title="개선안", url_path="dashboard-improvement"),
    st.Page(intro, title="프로젝트 소개", icon=":material/description:", url_path="intro"),
    st.Page(dashboard_summary, title="분석 내용", icon=":material/analytics:", url_path="dashboard-summary"),
    st.Page(improvement, title="개선안", icon=":material/trending_up:", url_path="improvement"),
    st.Page(attachments, title="첨부", icon=":material/folder:", url_path="attachments"),
    st.Page(planning, title="초기 개선안 기획", url_path="planning"),
    st.Page(sources, title="참고 기사, 논문 출처", url_path="sources"),
]
# Detail pages are shared by the landing links and sidebar submenus.
intro_pages = [
    st.Page(intro_problem, title="문제제기", url_path="intro-problem"),
    st.Page(intro_status, title="현황 분석", url_path="intro-status"),
]
improvement_pages = [
    st.Page(intro_solution, title="시뮬레이션", url_path="intro-solution"),
    st.Page(simulation, title="시뮬레이션 결과", url_path="simulation"),
    st.Page(improvement_results, title="개선안 결과", url_path="improvement-results"),
]
analysis_pages = [
    st.Page(analysis_dgt_odt, title="DGT_ODT", url_path="analysis-dgt-odt"),
    st.Page(analysis_hjnc_odt, title="HJNC_ODT", url_path="analysis-hjnc-odt"),
    st.Page(analysis_itt, title="DGT <-> HJNC ITT", url_path="analysis-itt"),
]
used_data_page = st.Page(used_data, title="사용한 데이터", url_path="used-data")
attachment_pages = (used_data_page, pages[10])
current_page = st.navigation(pages + intro_pages + analysis_pages + improvement_pages + [used_data_page], position="hidden")
groups = (
    (pages[0], ()),
    (pages[3], ()),
    (pages[6], intro_pages),
    (pages[7], analysis_pages),
    (pages[8], improvement_pages),
    (pages[9], attachment_pages),
)
# Preserve existing direct links without adding them to the sidebar contents.
linked_page_parents = {
    "home-analysis": pages[0],
    "home-ai": pages[0],
    "dashboard-data": pages[3],
    "dashboard-improvement": pages[3],
    "planning": pages[9],
    "sources": pages[9],
}
active_parent = next(
    (parent for parent, children in groups if current_page is parent or current_page in children),
    linked_page_parents.get(current_page.url_path, pages[0]),
)
active_href = active_parent.url_path
child_href = current_page.url_path if current_page is not active_parent else None
st.html(f'''<style>
  .stSidebar a[data-testid="stPageLink-NavLink"][href="{active_href}"],
  .stSidebar a[data-testid="stPageLink-NavLink"][href="{active_href}"]:hover {{
    background: #FFFFFF; color: #192C3A; border-radius: 24px 0 0 24px;
  }}
  .stSidebar a[data-testid="stPageLink-NavLink"][href="{active_href}"] span,
  .stSidebar a[data-testid="stPageLink-NavLink"][href="{active_href}"] p {{ color: #192C3A; }}
  {f'.stSidebar .st-key-sidebar_submenu a[data-testid="stPageLink-NavLink"][href="{child_href}"] {{ color:#FFFFFF; font-weight:800; }}' if child_href else ''}
</style>''')
with st.sidebar:
    html('<div class="sidebar-brand"><span class="brand-mark">P</span><span><strong>DATA ANALYTICS</strong><small>Busan Port Analytics</small></span></div>')
    st.caption("PROJECT")
    for parent, children in groups:
        st.page_link(parent, label=parent.title, icon=parent.icon, width="stretch")
        if children and parent is active_parent:
            with st.container(key="sidebar_submenu"):
                for child in children:
                    st.page_link(child, label=child.title, width="stretch")
    html('<div class="sidebar-foot"><i></i> HTML 화면 시안 </div>')
current_page.run()
