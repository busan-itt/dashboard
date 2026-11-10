"""Streamlit version of the Port Analytics portfolio prototype.

Home, dashboard and detail pages display the team's saved analysis results.
"""

from __future__ import annotations

from base64 import b64encode
from html import escape
from pathlib import Path
import json

import streamlit as st
from improvement_content import views as improvement_views
from overview import home_summaries, render_dashboard

ROOT = Path(__file__).parent

def html(body: str) -> None:
    st.html(body)



def dashboard() -> None:
    render_dashboard()


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
    summaries = home_summaries(compact=True)
    summary_body = ''.join(
        f'<div class="home-summary-item"><h3>{escape(title)}</h3><p>{escape(description)}</p></div>'
        for title, description in summaries
    )
    destinations = (
        ("dashboard", "대시보드", "환적 경로별 체류시간과 주요 분석 결과", "dashboard", ()),
        ("intro", "프로젝트 소개", "분석 배경과 부산신항 환적 현황", "intro",
         (("intro-problem", "문제제기"), ("intro-status", "현황 분석"))),
        ("dashboard-summary", "분석 내용", "선박 운영시간과 야드 체류시간의 관계", "analysis", ()),
        ("improvement", "개선안", "선석통합운영 제안과 시뮬레이션 결과", "improvement",
         (("intro-solution", "시뮬레이션"), ("simulation", "시뮬레이션 결과"),
          ("improvement-results", "개선안 결과"))),
        ("attachments", "첨부", "사용 데이터와 초기 기획 자료", "attachments",
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
      <header class="home-heading"><h1>부산신항의 선석통합운영을 통한 환적 체류시간 개선</h1>
        <p>프로젝트 기간 · 2026.10 ~ 2026.11</p></header>
      <section class="home-summary" aria-labelledby="home-summary-title">
        <div class="home-summary-label"><small>ANALYSIS SUMMARY</small>
          <h2 id="home-summary-title">분석 핵심 요약</h2></div>
        <div class="home-summary-content">{summary_body}</div>
        <p class="home-summary-note">야드 비중은 공정별 평균시간 합계 기준입니다. 모형 결과는 선별 48시간 앞당김·전체 통합 조건이며, 실제 도입 성과가 아닙니다.</p>
      </section>
      <section class="home-explore" aria-labelledby="home-explore-title">
        <div class="home-explore-heading"><h2 id="home-explore-title">프로젝트 둘러보기</h2>
          <p>원하는 목차를 선택해 자세한 내용을 확인하세요.</p></div>
        <div class="home-nav-grid">{''.join(navigation)}</div>
      </section>
    </div>''')


def home_analysis() -> None:
    body = ''.join(card("KEY FINDING", title, description) for title, description in home_summaries())
    document_page("ANALYSIS SUMMARY", "분석 핵심 요약", "현황 분석과 대표 시뮬레이션의 저장 결과", body)


def home_ai() -> None:
    home_analysis()


def dashboard_home() -> None:
    dashboard()


def attachments() -> None:
    from attachments_views import render_attachments
    render_attachments()


def used_data() -> None:
    from attachments_views import render_used_data
    render_used_data()


def dashboard_summary() -> None:
    from correlation_views import render_summary
    render_summary()


def correlation_report(key: str, title: str) -> None:
    with st.container(key="correlation_report"):
        render_correlation_report(key, title)


def render_correlation_report(key: str, title: str) -> None:
    from correlation_views import render_report
    render_report(key, title)


def analysis_dgt_odt() -> None:
    correlation_report("dgt", "DGT_ODT")


def analysis_hjnc_odt() -> None:
    correlation_report("hjnc", "HJNC_ODT")


def analysis_itt() -> None:
    correlation_report("itt", "DGT <-> HJNC ITT")


def intro() -> None:
    body = '''<div class="intro-overview">
      <dl class="intro-facts">
        <div><dt>분석 대상</dt><dd>DGT·HJNC의 자부두 환적과 양방향 타부두 환적</dd></div>
        <div><dt>분석 목표</dt><dd>체류시간이 긴 구간을 찾고, 일정 조정과 선석 공유에 따른 변화 비교</dd></div>
      </dl>
      <nav class="intro-destinations" aria-label="프로젝트 소개 하위 페이지">
        <a href="/intro-problem"><h2>문제제기</h2>
          <p>부산항의 환적 구조와 타부두 환적이 발생하는 배경</p><span>자세히 보기 →</span></a>
        <a href="/intro-status"><h2>현황 분석</h2>
          <p>네 환적 경로의 전체 소요시간과 공정별 체류시간</p><span>자세히 보기 →</span></a>
      </nav>
      <section class="intro-flow" aria-labelledby="intro-flow-title">
        <h2 id="intro-flow-title">분석 흐름</h2>
        <!-- intro-analysis-flow -->
        <p>시뮬레이션 결과는 실제 도입 성과와 구분해 비교.</p>
      </section>
    </div>'''
    flow = b64encode((ROOT / 'assets' / 'intro-analysis-flow.svg').read_bytes()).decode('ascii')
    mobile_flow = b64encode((ROOT / 'assets' / 'intro-analysis-flow-mobile.svg').read_bytes()).decode('ascii')
    body = body.replace('<!-- intro-analysis-flow -->',
                        f'<picture><source media="(max-width: 600px)" srcset="data:image/svg+xml;base64,{mobile_flow}">'
                        f'<img src="data:image/svg+xml;base64,{flow}" '
                        'alt="분석 흐름: 환적 경로 비교 → 야드 체류 분석 → 일정 조정·선석 공유 → 야드 체류 감소율과 다른 선박의 추가 지연 비교"></picture>')
    document_page(
        "PROJECT OVERVIEW", "프로젝트 소개",
        "부산신항의 환적 체류시간을 분석하고, 선석통합운영의 개선 효과를 시뮬레이션으로 비교한 프로젝트",
        body,
    )


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
    body = '''<div class="problem-page problem-presentation">
      <section class="problem-section" aria-labelledby="problem-background">
        <div class="problem-section-heading"><span>01 / BACKGROUND</span>
          <h2 id="problem-background">부산항과 부산신항의 환적 현황</h2></div>
        <p class="problem-lead">부산항은 환적 비중이 높고, 부산신항은 부산항 환적의 상당 부분을 처리.</p>
        <div class="problem-stat-grid">
          <article class="problem-stat"><h3>부산항 환적 비중</h3><strong>약 57<span>%</span></strong>
            <p>2025년 부산항 전체 물동량 대비</p></article>
          <article class="problem-stat"><h3>부산항 환적 중 신항 처리 비중</h3><strong>약 84.3<span>%</span></strong>
            <p>2025년 부산항 전체 환적 대비</p></article>
          <article class="problem-stat"><h3>부산신항 ITT 비율</h3><strong>40<span>%</span></strong>
            <p>2025년 · 신항7부두 제외<br>전체 컨테이너 물동량 대비</p></article>
        </div>
        <p class="problem-caption">관련 자료: <a href="https://app.notion.com/p/406c0feefeda808d9091c15299f73844"
          target="_blank" rel="noopener noreferrer">프로젝트 중간 발표 자료</a></p>
      </section>

      <section class="problem-section" aria-labelledby="problem-process">
        <div class="problem-section-heading"><span>02 / PROCESS</span>
          <h2 id="problem-process">자부두와 타부두 환적의 차이</h2></div>
        <div class="problem-process-grid">
          <article class="problem-process-card"><span class="problem-type">ODT</span>
            <h3>자부두 환적</h3><p class="problem-english">On-Dock Transshipment</p>
            <p>같은 터미널에서 양하와 적하</p>
            <!-- odt-process --></article>
          <article class="problem-process-card"><span class="problem-type">ITT</span>
            <h3>타부두 환적</h3><p class="problem-english">Inter-Terminal Transshipment</p>
            <p>다른 터미널로 이동한 뒤 적하</p>
            <!-- itt-process --></article>
        </div>
        <aside class="problem-callout"><strong>ITT에는 부두 간 운송과 추가 작업이 발생</strong>
          <p>양하와 적하를 서로 다른 터미널에서 처리하기 때문.</p></aside>
      </section>

      <section class="problem-section" aria-labelledby="problem-impact">
        <div class="problem-section-heading"><span>03 / WHY ODT</span>
          <h2 id="problem-impact">부두 간 이동에 따른 비용과 운영 부담</h2></div>
        <p>추가 운송은 비용과 시간을 늘리고, 분산 운영은 선석 관리와 항만 생산성에도 부담.</p>
        <div class="problem-table-wrap"><table class="problem-evidence-table">
          <caption>기관별로 제시한 문제와 근거 자료</caption>
          <thead><tr><th scope="col">기관</th><th scope="col">명시한 문제</th><th scope="col">근거</th></tr></thead>
          <tbody>
            <tr><th scope="row">해양수산부</th><td><strong>추가 물류비 발생</strong></td><td>2023년 BPA 집계: ITT 연간 232만 TEU · 추가 물류비 551억 원. <strong>2025년 수치와 구분.</strong>
              <a href="https://www.mof.go.kr/doc/ko/selectDoc.do?bbsSeq=10&amp;docSeq=59556&amp;menuSeq=971"
                target="_blank" rel="noopener noreferrer">해양수산부 보도자료 · 2024.12.11.</a></td></tr>
            <tr><th scope="row">해양수산부</th><td><strong>선석 관리의 비효율</strong></td><td>소규모·분산 운영에 따른 비효율. 통합 처리를 개선 방향으로 제시.
              <a href="https://www.mof.go.kr/doc/ko/selectDoc.do?bbsSeq=10&amp;docSeq=59556&amp;menuSeq=971"
                target="_blank" rel="noopener noreferrer">해양수산부 보도자료 · 2024.12.11.</a></td></tr>
            <tr><th scope="row">부산항만공사</th><td><strong>항만 생산성 저하</strong></td><td>북항·신항 이원화와 다수 운영사 체제에 따른 타부두 이동 및 생산성 저하.
              <a href="https://www.busanpa.com/board/view.bpa?boardId=BBS_0000031&amp;dataSid=27954&amp;menuCd=DOM_000000105002001000"
                target="_blank" rel="noopener noreferrer">부산항 컨테이너 물류효율 획기적으로 개선한다 · 2022.8.11.</a></td></tr>
            <tr><th scope="row">부산항만공사</th><td><strong>비용·시간 측면의 경쟁력 저하</strong></td><td>타부두 환적에 따른 추가 비용과 시간 부담.
              <a href="https://www.busanpa.com/board/view.bpa?boardId=BBS_0000031&amp;dataSid=34129&amp;menuCd=DOM_000000105002001000"
                target="_blank" rel="noopener noreferrer">ITT 자동운송시스템 개발 완료 · 2025.9.9.</a></td></tr>
          </tbody></table></div>
      </section>

      <section class="problem-section" aria-labelledby="problem-causes">
        <div class="problem-section-heading"><span>04 / STRUCTURAL CAUSES</span>
          <h2 id="problem-causes">타부두 환적이 발생하는 배경</h2></div>
        <p>컨테이너를 내리는 배와 싣는 배의 이용 터미널이 다르면 부두 간 이동이 필요.</p>
        <div class="problem-cause-grid">
          <article class="problem-cause-card"><h3>터미널의 분리 운영</h3>
            <p>운영사별로 터미널이 나뉘어 있어, 서로 다른 터미널을 이용하는 선박 사이에는 컨테이너 운송이 필요.</p>
            <a href="https://www.mof.go.kr/doc/ko/selectDoc.do?bbsSeq=10&amp;docSeq=59556&amp;menuSeq=971"
              target="_blank" rel="noopener noreferrer">해양수산부 · 2024.12.11.</a></article>
          <article class="problem-cause-card"><h3>선사별 이용 터미널의 분산</h3>
            <p>같은 해운동맹에 속한 선사라도 이용 터미널은 다를 수 있음.</p>
            <details class="problem-case"><summary>과거 사례 · 2017년</summary>
            <p>2017년 사례: 2M은 기존 2부두에서 1·3부두로 분산, 협력 관계인 HMM은 주로 4부두 이용.
              KMI는 이용 터미널의 분산을 ITT 증가 요인으로 제시.</p></details>
            <a href="https://www.nkis.re.kr/subject_view1.do?eoSeq=66004&amp;otpId=KMI00052780&amp;otpSeq=0"
              target="_blank" rel="noopener noreferrer">KMI 연구보고서 · 2017 · 국가정책연구포털 수록 초록</a></article>
        </div>
      </section>

      <section class="problem-section problem-yard-section" aria-labelledby="problem-yard-focus">
        <div class="problem-section-heading"><span>05 / ANALYSIS FOCUS</span>
          <h2 id="problem-yard-focus">분석 초점: 야드 체류시간</h2></div>
        <aside class="problem-yard-finding">
          <blockquote>자부두·타부두 모두 환적 시간의 대부분을 차지한 구간</blockquote>
          <h3>야드 장치 기간</h3>
        </aside>
        <p>자부두·타부두 환적을 공정별로 비교한 뒤, 야드 체류시간을 중심으로 후속 분석.</p>
        <p>분석 대상: <strong>DGT ODT, HJNC ODT, DGT → HJNC ITT, HJNC → DGT ITT</strong><br>
          전체 소요시간: 최초 반입부터 최종 반출까지<br>
          야드 장치 기간: 야드 장치부터 온샤시 시점까지</p>
        <a class="problem-next" href="/intro-status">현황 분석 →</a>
      </section>
    </div>'''
    body = body.replace("<!-- odt-process -->", process_flow("odt"))
    body = body.replace("<!-- itt-process -->", process_flow("itt"))
    document_page("01 / INTRODUCTION", "문제 제기", "부산항의 환적 구조와 타부두 환적이 발생하는 배경", body)


def intro_status() -> None:
    st.html(ROOT / "problem.css")
    from current_state import render_current_state
    render_current_state()


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


st.set_page_config(page_title="Port Analytics | 환적 체류시간 분석", layout="wide", initial_sidebar_state="auto")
st.html(ROOT / "styles.css")
st.html(ROOT / "home.css")
pages = [
    st.Page(home, title="홈", icon=":material/home:", default=True),
    st.Page(home_analysis, title="프로젝트 요약", url_path="home-analysis"),
    st.Page(home_ai, title="핵심 결과 요약", url_path="home-ai"),
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
    html('<div class="sidebar-brand"><span class="brand-mark">B</span><span><strong>Port Insights</strong><small>Team: Bnct</small></span></div>')
    st.caption("PROJECT")
    for parent, children in groups:
        st.page_link(parent, label=parent.title, icon=parent.icon, width="stretch")
        if children and parent is active_parent:
            with st.container(key="sidebar_submenu"):
                for child in children:
                    st.page_link(child, label=child.title, width="stretch")
    html('<div class="sidebar-foot"><i></i> 환적 체류시간 분석 </div>')
current_page.run()
