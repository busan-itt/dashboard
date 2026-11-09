"""Streamlit version of the Port Analytics portfolio prototype.

All dashboard figures below are deterministic UI samples, not port records.
"""

from __future__ import annotations

from html import escape
from math import sin
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
TERMINALS = (
    ("PNC", 198_000, 84, 31.8, 67.0, "#185dac"),
    ("PNIT", 174_000, 76, 29.4, 62.0, "#0084c7"),
    ("HJNC", 163_000, 71, 28.8, 59.0, "#1b8b67"),
    ("HPNT", 149_000, 66, 27.9, 64.0, "#6d78b8"),
    ("BNCT", 139_000, 61, 27.1, 57.0, "#d47a21"),
    ("BCT", 118_000, 54, 25.8, 53.0, "#c84d4d"),
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
        st.line_chart(chart, x="월", y=["선택 기간", "이전 기간"], color=["#247cd5", "#aab6bd"], height=300)
    with right, st.container(key="status_panel"):
        html('<div class="panel-head"><span>YARD STATUS</span><h2>작업 상태 분포</h2><p>샘플 기준</p></div>')
        status = [("완료", 46, "#185dac"), ("작업 중", 29, "#1b8b67"),
                  ("대기", 17, "#d47a21"), ("점검", 8, "#c84d4d")]
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


def home() -> None:
    landing("PORT ANALYTICS", "홈", "분석 내용과 AI 분석 요약을 각각의 페이지에서 확인합니다.",
            (("home-analysis", "분석 내용 요약"), ("home-ai", "AI 분석 요약")))


def home_analysis() -> None:
    document_page("ANALYSIS SUMMARY", "분석 내용 요약", "홈 / 분석 내용 요약",
                  card("ANALYSIS SUMMARY", "분석 내용 요약",
                       "현재 프로젝트에 포함된 대시보드와 문서형 화면을 소개합니다. 수치와 차트는 UI 동작을 확인하기 위한 샘플이며, 실제 분석 결과 문안은 아직 연결되지 않았습니다.",
                       '<div class="chips"><span>대시보드 지표</span><span>분석 기록</span><span>자료 이미지</span></div>'))


def home_ai() -> None:
    document_page("AI SUMMARY", "AI 분석 요약", "홈 / AI 분석 요약",
                  card("AI SUMMARY", "AI 분석 요약", "AI 분석 결과 또는 요약 문안이 현재 시안에 없어, 내용 확정 후 연결할 자리입니다."))


def dashboard_home() -> None:
    landing("DASHBOARD", "대시보드", "분석 내용 요약과 대시보드 기능을 각각의 페이지에서 확인합니다.",
            (("dashboard-summary", "분석 내용 요약"), ("dashboard-data", "기존 대시보드 기능")))


def dashboard_summary() -> None:
    document_page("ANALYSIS SUMMARY", "분석 내용 요약", "대시보드 / 분석 내용 요약",
                  card("ANALYSIS SUMMARY", "분석 내용 요약",
                       "기존 대시보드의 지표와 차트는 동작 확인용 샘플입니다. 실제 분석 결과로 확정된 해석은 아직 이 시안에 없습니다."))


def intro() -> None:
    landing("PROJECT OVERVIEW", "프로젝트 소개", "문제 제기, 현황 분석, 개선안 소개를 각각의 페이지에서 확인합니다.",
            (("intro-problem", "문제 제기"), ("intro-status", "현황 분석"), ("intro-solution", "개선안 소개")))


def intro_problem() -> None:
    document_page("01 / INTRODUCTION", "문제 제기", "프로젝트 소개 / 문제 제기",
                  card("01 / INTRODUCTION", "항만 데이터를 읽고 설명하는 공간",
                       "대시보드에서 수치를 살펴보고, 이 페이지에서는 프로젝트 목적과 데이터 범위를 설명합니다. 실제 문제 정의 문안은 아직 확정되지 않았습니다.",
                       '<div class="chips"><span>문제 정의</span><span>데이터 범위</span><span>분석 방법</span></div>'))


def intro_status() -> None:
    document_page("02 / CURRENT STATE", "현황 분석", "프로젝트 소개 / 현황 분석",
                  card("02 / CURRENT STATE", "현황 분석",
                       "데이터의 집계 기준, 기간, 단위, 누락값을 확인한 뒤 지표 설명을 정리합니다. 실제 분석 결론은 아직 이 시안에 포함되지 않았습니다."))


def intro_solution() -> None:
    document_page("03 / IMPROVEMENT", "개선안 소개", "프로젝트 소개 / 개선안 소개",
                  card("03 / IMPROVEMENT", "개선안 소개",
                       "개선안의 배경과 핵심 방향을 요약할 자리입니다. 구체적인 내용은 자료가 확정된 뒤 독립된 개선안 페이지에 연결합니다."))


def improvement() -> None:
    document_page("IMPROVEMENT", "개선안", "제안 내용과 근거를 별도로 정리할 페이지입니다.",
                  card("CONTENT PLACEHOLDER", "개선안 본문",
                       "현재 시안에는 확정된 개선안 문서가 없습니다. 제안 내용, 적용 범위, 근거 자료가 준비되면 이 자리에 배치합니다."))


def planning() -> None:
    body = '''<div class="article-layout"><article class="portfolio-card article"><small>EXAMPLE DOCUMENT</small>
      <h2>데이터를 어떻게 읽었는가</h2><p>이 문서는 기존 분석 기록의 본문 스타일을 옮긴 예시입니다. 실제 분석 결과나 운영 성과를 주장하지 않습니다.</p>
      <h3>1. 확인할 내용</h3><p>데이터의 집계 기준, 기간, 단위, 누락값을 먼저 확인하고 지표에 붙일 설명을 정리합니다.</p>
      <h3>2. 해석의 범위</h3><p>차트에서 보이는 차이와 그 원인을 구분해 기록합니다. 근거가 없는 운영 효율이나 비용 효과는 단정하지 않습니다.</p>
      <blockquote>문서가 여러 개라면 같은 양식의 페이지를 메뉴에 추가할 수 있습니다.</blockquote></article>
      <aside class="portfolio-card"><small>DOCUMENT INFO</small><h2>문서 메모</h2>
      <p>제목, 작성일, 데이터 출처, 관련 링크를 배치할 수 있는 영역입니다.</p><hr><p>상태　예시 콘텐츠</p></aside></div>'''
    document_page("INITIAL PLAN", "초기 기획", "프로젝트 초기의 목표와 자료 조사 과정을 기록할 페이지입니다.", body)


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
pages = [
    st.Page(home, title="홈", icon=":material/home:", default=True),
    st.Page(home_analysis, title="분석 내용 요약", url_path="home-analysis"),
    st.Page(home_ai, title="AI 분석 요약", url_path="home-ai"),
    st.Page(dashboard_home, title="대시보드", icon=":material/dashboard:", url_path="dashboard"),
    st.Page(dashboard_summary, title="분석 내용 요약", url_path="dashboard-summary"),
    st.Page(dashboard, title="기존 대시보드 기능", url_path="dashboard-data"),
    st.Page(intro, title="프로젝트 소개", icon=":material/description:", url_path="intro"),
    st.Page(intro_problem, title="문제 제기", url_path="intro-problem"),
    st.Page(intro_status, title="현황 분석", url_path="intro-status"),
    st.Page(intro_solution, title="개선안 소개", url_path="intro-solution"),
    st.Page(improvement, title="개선안", icon=":material/trending_up:", url_path="improvement"),
    st.Page(planning, title="초기 기획", icon=":material/event_note:", url_path="planning"),
    st.Page(sources, title="참고·출처", icon=":material/source:", url_path="sources"),
]
current_page = st.navigation(pages, position="hidden")
groups = (
    (pages[0], pages[1:3]),
    (pages[3], pages[4:6]),
    (pages[6], pages[7:10]),
    (pages[10], ()),
    (pages[11], ()),
    (pages[12], ()),
)
active_parent = next(parent for parent, children in groups if current_page is parent or current_page in children)
active_href = active_parent.url_path
child_href = current_page.url_path if current_page is not active_parent else None
st.html(f'''<style>
  .stSidebar a[data-testid="stPageLink-NavLink"][href="{active_href}"],
  .stSidebar a[data-testid="stPageLink-NavLink"][href="{active_href}"]:hover {{
    background: #eef3f6; color: #142f42; border-radius: 24px 0 0 24px;
  }}
  .stSidebar a[data-testid="stPageLink-NavLink"][href="{active_href}"] span,
  .stSidebar a[data-testid="stPageLink-NavLink"][href="{active_href}"] p {{ color: #142f42; }}
  {f'.stSidebar .st-key-sidebar_submenu a[data-testid="stPageLink-NavLink"][href="{child_href}"] {{ color:#fff; font-weight:800; }}' if child_href else ''}
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
