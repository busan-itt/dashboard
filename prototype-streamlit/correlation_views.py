"""Presentation views of the saved correlation reports; original figures and criteria."""
import json
from html import escape
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent
CHARTS = ROOT / 'assets/correlation-analysis/unified'


def load_reports():
    return json.loads((CHARTS/'reports.json').read_text(encoding='utf-8'))


TAKEAWAYS = {
    'dgt': '유의한 선형 상관을 확인하지 못함',
    'hjnc': '선박 운영시간만으로 야드 체류 차이를 설명하기 어려움',
    'forward': '뚜렷한 선형 상관을 확인하지 못함',
    'reverse': '작업 시작 전 대기와 약한 양의 상관',
}


def render_summary():
    st.html(ROOT/'correlation.css')
    reports = load_reports()
    with st.container(key='analysis_summary'):
        st.html('<header class="results-heading"><small>ANALYSIS</small><h1>분석 내용</h1><p>선박 운영시간과 야드 체류시간의 관계</p></header>')
        st.html('<section class="analysis-question"><h2>선박 운영시간과 야드 체류시간은 얼마나 관련이 있을까?</h2><p>검토한 지표의 선형 상관은 전반적으로 약함. HJNC → DGT의 작업 시작 전 대기에서는 약한 양의 상관 관측.</p></section>')
        links = []
        for path, name, keys in (
            ('analysis-dgt-odt', 'DGT_ODT', ('dgt',)),
            ('analysis-hjnc-odt', 'HJNC_ODT', ('hjnc',)),
            ('analysis-itt', 'DGT <-> HJNC ITT', ('forward','reverse')),
        ):
            conclusions = ''.join(f'<p>{escape(reports[key].get("direction", ""))}{" · " if "direction" in reports[key] else ""}{escape(TAKEAWAYS[key])}</p>' for key in keys)
            links.append(f'<a href="/{path}"><h2>{escape(name)}</h2>{conclusions}<span>분석 보기 →</span></a>')
        st.html('<nav class="analysis-destinations" aria-label="경로별 분석">'+''.join(links)+'</nav>')
        st.caption('경로별 측정 구간과 분석 단위는 서로 다름. 각 상세 화면의 분석 기준을 확인. 상관관계는 인과관계를 뜻하지 않음.')


def render_report(key, title):
    st.html(ROOT/'correlation.css')
    reports = load_reports()
    st.html(f'<header class="results-heading"><small>CORRELATION ANALYSIS</small><h1>{escape(title)}</h1><p>선박 운영시간 지표와 야드 장치 기간의 관계</p></header>')
    selected_key = key
    if key == 'itt':
        selected_key = st.radio('환적 방향', ('forward','reverse'), horizontal=True,
                                format_func=lambda v: {'forward':'DGT → HJNC','reverse':'HJNC → DGT'}[v], key='analysis_itt_direction')
    report = reports[selected_key]
    st.html(f'<section class="analysis-conclusion"><h2>{escape(TAKEAWAYS[selected_key])}</h2><p>{escape(report["conclusion"])}</p></section>')
    st.html('<dl class="analysis-criteria">'+''.join(f'<div><dt>{label}</dt><dd>{escape(value)}</dd></div>' for label,value in (
        ('기준 표본', report['sample']), ('측정 구간', report['definition']), ('분석 단위', report['unit'])))+'</dl>')
    st.caption(report['note'])

    st.subheader('운영시간 지표별 상관관계')
    st.image(CHARTS/report['comparison'], width='stretch', alt='운영시간 지표별 Pearson 상관계수. 공통 눈금 −1 ~ 1')
    st.caption('Pearson r · 공통 눈금 −1 ~ 1. 0에 가까울수록 선형 관계가 약함.')

    representative = max(report['plots'], key=lambda p: abs(p['r']))
    st.subheader('운영시간과 야드 체류시간')
    st.write(representative['label'])
    st.caption('화면에 제공된 산점도 중 |r|이 가장 큰 지표. 상관관계의 크기와 통계적 유의성은 구분.')
    st.image(CHARTS/representative['image'], width='stretch', alt=f'{representative["label"]}의 관측값과 선형 회귀선')
    st.caption(f'관측값: {representative["n"]:,} · r={representative["r"]:.3f} · 블루: 관측값 / 코랄: 선형 회귀선')

    with st.expander('지표별 상세 산점도와 상관계수'):
        selected = st.selectbox('운영시간 지표', range(len(report['plots'])),
                               format_func=lambda i: report['plots'][i]['label'], key=f'analysis_variable_{selected_key}')
        plot = report['plots'][selected]
        st.image(CHARTS/plot['image'], width='stretch', alt=f'{plot["label"]}의 상세 산점도')
        st.write(f'{plot["label"]} · N={plot["n"]:,} · r={plot["r"]:.3f}')
        st.dataframe([{'지표': p['label'],'N':p['n'],'Pearson r':p['r']} for p in report['plots']],
                     hide_index=True,width='stretch',column_config={'Pearson r':st.column_config.NumberColumn(format='%.4f')},alt='화면에 제공된 지표별 원본 상관계수와 표본 수')
    with st.expander('선석별 환적 작업 물동량'):
        st.write(report['berth_meta'])
        st.image(CHARTS/report['berth'][0]['image'],width='stretch',alt=report['berth'][0]['label'])
        st.write(report['berth_volume_note'])
    with st.expander('선석별 장치 기간 상관관계'):
        st.image(CHARTS/report['berth'][1]['image'],width='stretch',alt=report['berth'][1]['label'])
        st.write(report['berth_correlation_note'])
    st.caption('상관관계는 인과관계를 뜻하지 않음. 상관이 약하다는 결과를 관계가 없다는 뜻으로 해석하지 않음.')
    st.html('<nav class="analysis-next"><a href="/dashboard-summary">분석 내용</a><a href="/improvement">개선안 →</a></nav>')
