"""Home and dashboard summaries from the project's saved analysis results."""
from pathlib import Path
import json

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
BLUE, CORAL = '#3F617C', '#F4A78D'


def snapshot():
    routes = json.loads((ROOT/'output/preliminary-analysis-20261109/figure-data.json').read_text(encoding='utf-8'))
    reports = json.loads((ROOT/'assets/correlation-analysis/unified/reports.json').read_text(encoding='utf-8'))
    simulation = json.loads((ROOT/'improvement_content/data/simulation_all_results.json').read_text(encoding='utf-8'))
    scenarios = {r['scenario']: r for r in simulation['rows'] if r['policy'] == '선별' and r['hours'] == 48}
    return routes, reports, simulation, scenarios


def home_summaries():
    routes, reports, simulation, scenarios = snapshot()
    low, high = min(r['yard_share_pct'] for r in routes), max(r['yard_share_pct'] for r in routes)
    a, c = scenarios['A'], scenarios['C']
    max_r = max(abs(p['r']) for report in reports.values() for p in report['plots'])
    after = simulation['baseline_mean_h_rounded']*(1-c['reduction_pct']/100)
    return (
        ('환적 시간은 야드 체류에 집중', f"분석한 네 경로에서 야드 장치 구간은 공정별 평균시간 합계의 {low:.2f}~{high:.2f}%를 차지했습니다. 정상적인 연결선 대기도 포함됩니다."),
        ('선박 운영시간과의 선형 관계는 약함', f"화면에 제시한 주요 상관분석의 최대 |r|은 {max_r:.3f}입니다. 검토한 운영시간 지표만으로 야드 체류 차이를 설명하기 어렵습니다."),
        ('선별 일정 조정과 선석 공유를 함께 검토', f"선별 48시간 앞당김·전체 통합(C) 시뮬레이션에서 체류가 {c['reduction_pct']:.2f}% 감소했습니다. 모형 기준 평균 {simulation['baseline_mean_h_rounded']:.1f} → 약 {after:.1f}시간입니다."),
        ('선석 공유는 다른 선박의 추가 지연을 완화', f"같은 선별 48시간 조정에서 다른 선박 접안 지연은 A {a['other_delay_h']*60:.2f}분 → C {c['other_delay_h']*60:.2f}분이었습니다. 실제 도입 성과가 아닌 모형 비교 결과입니다."),
    )


def grouped_duration(frame):
    values = frame.melt(id_vars=['경로'], value_vars=['평균', '중앙값'], var_name='지표', value_name='시간')
    order = frame['경로'].tolist()
    bars = alt.Chart(values).mark_bar(size=14).encode(
        x=alt.X('시간:Q', title='소요시간 (시간)', scale=alt.Scale(domain=[0,255])),
        y=alt.Y('경로:N', sort=order, title=None),
        yOffset=alt.YOffset('지표:N', sort=['평균','중앙값']),
        color=alt.Color('지표:N', scale=alt.Scale(domain=['평균','중앙값'], range=[BLUE,CORAL]), legend=alt.Legend(title=None,orient='top')),
        tooltip=['경로:N','지표:N',alt.Tooltip('시간:Q',format='.2f')])
    labels=bars.mark_text(align='left',dx=5,color='#192C3A').encode(text=alt.Text('시간:Q',format='.2f'),color=alt.value('#192C3A'))
    return (bars+labels).properties(height=max(180,len(frame)*76)).configure_view(stroke=None)


def scenario_chart(scenarios, metric, scale, title, domain):
    names={'A':'A 기존 운영','B':'B 인접 공유','C':'C 전체 통합'}
    data=pd.DataFrame([{'운영 방식':names[key], '값':r[metric]*scale,'구분':'전체 통합' if key=='C' else '비교 운영'} for key,r in scenarios.items()])
    bars=alt.Chart(data).mark_bar(size=25).encode(
        x=alt.X('값:Q',title=title,scale=alt.Scale(domain=domain)),
        y=alt.Y('운영 방식:N',sort=list(names.values()),title=None),
        color=alt.Color('구분:N',scale=alt.Scale(domain=['비교 운영','전체 통합'],range=[BLUE,CORAL]),legend=None),
        tooltip=['운영 방식:N',alt.Tooltip('값:Q',title=title,format='.2f')])
    labels=bars.mark_text(align='left',dx=6,color='#192C3A').encode(text=alt.Text('값:Q',format='.2f'),color=alt.value('#192C3A'))
    return (bars+labels).properties(height=210).configure_view(stroke=None)


def render_dashboard():
    routes, reports, simulation, scenarios = snapshot()
    c=scenarios['C']
    low, high=min(r['yard_share_pct'] for r in routes),max(r['yard_share_pct'] for r in routes)
    st.html('''<header class="results-heading"><small>TRANSSHIPMENT ANALYSIS</small>
      <h1>환적 체류시간 분석 대시보드</h1>
      <p>DGT·HJNC 네 환적 경로의 현황과 선석 공유 시뮬레이션 결과를 살펴봅니다.</p></header>''')
    cards=[('분석 대상',f'{len(routes)}개 경로','DGT·HJNC 자부두 및 양방향 타부두'),
           ('야드 장치 시간 비중',f'{low:.2f}~{high:.2f}%','공정별 평균시간 합계 기준'),
           ('모형의 야드 체류 감소',f"{c['reduction_pct']:.2f}%",'선별 48시간 · 전체 통합(C)'),
           ('모형의 다른 선박 지연',f"{c['other_delay_h']*60:.2f}분",f"같은 조정 조건에서 A는 {scenarios['A']['other_delay_h']*60:.2f}분")]
    st.html('<section class="results-kpis">'+''.join(f'<article><span>{label}</span><strong>{value}</strong><p>{detail}</p></article>' for label,value,detail in cards)+'</section>')

    with st.container(border=True):
        st.subheader('환적 경로별 현황')
        category=st.segmented_control('환적 구분',['전체 경로','자부두 (ODT)','타부두 (ITT)'],default='전체 경로',key='overview_route_type')
        selected=[r for r in routes if category in (None,'전체 경로') or ('ODT' in r['route'])==(category=='자부두 (ODT)')]
        frame=pd.DataFrame([{'경로':r['route'],'평균':r['reported_total_mean_h'],'중앙값':r['reported_total_median_h']} for r in selected])
        left,right=st.columns([1.55,1],gap='large')
        with left:
            st.markdown('**전체 소요시간 · 평균과 중앙값**')
            st.altair_chart(grouped_duration(frame),width='stretch')
            st.caption('최초 반입부터 최종 반출까지의 시간입니다. ITT는 터미널 간 이동시간을 포함합니다.')
        with right:
            st.markdown('**공정별 평균시간 중 야드 장치 비중**')
            for r in selected:
                st.html(f'<div class="yard-share-row"><span>{r["route"]}</span><strong>{r["yard_share_pct"]:.2f}%</strong><div><i style="width:{r["yard_share_pct"]:.4f}%"></i></div></div>')
            st.caption('공정별 평균시간 합계 대비 야드 장치 구간 합계의 비중입니다. 정상적인 연결선 대기도 포함되며, 전체를 제거 가능한 지연으로 해석할 수 없습니다.')
        table=pd.DataFrame([{'경로':r['route'],'분석 건수':r['total_n'],'전체 평균 (시간)':r['reported_total_mean_h'],'전체 중앙값 (시간)':r['reported_total_median_h'],'야드 평균 합계 (시간)':round(r['yard_mean_sum_h'],2),'야드 비중 (%)':round(r['yard_share_pct'],2)} for r in selected])
        st.dataframe(table,hide_index=True,width='stretch',column_config={name:st.column_config.NumberColumn(format='%.2f') for name in table.columns if name not in ('경로','분석 건수')})
        st.caption('각 경로의 분석 표본입니다. 경로별 건수를 부산항 전체 물동량이나 고유 컨테이너 수로 해석하지 않습니다.')

    with st.container(border=True):
        st.subheader('분석에서 확인한 점')
        st.write('선박 운영시간 지표와 야드 체류의 선형 관계는 전반적으로 약했습니다. 이를 바탕으로 연결선 일정 조정과 선석 공유를 모형에서 비교했습니다. 상관관계는 인과관계를 의미하지 않습니다.')
        st.html('<nav class="section-links"><a href="/analysis-dgt-odt">DGT ODT 분석</a><a href="/analysis-hjnc-odt">HJNC ODT 분석</a><a href="/analysis-itt">ITT 분석</a></nav>')

    with st.container(border=True):
        st.subheader('대표 시뮬레이션 · 선별 48시간 앞당김')
        baseline=simulation['baseline_mean_h_rounded'];after=baseline*(1-c['reduction_pct']/100)
        st.write(f'최소 연결 간격 24시간 조건에서 기존 운영(A), 인접 공유(B), 전체 통합(C)을 비교했습니다. C의 평균 야드 체류는 모형 기준 {baseline:.1f}시간에서 약 {after:.1f}시간으로 감소했습니다.')
        left,right=st.columns(2,gap='large')
        with left:
            st.markdown('**야드 체류 감소율**')
            st.altair_chart(scenario_chart(scenarios,'reduction_pct',1,'감소율 (%)',[0,12]),width='stretch')
        with right:
            st.markdown('**다른 선박의 추가 접안 지연**')
            st.altair_chart(scenario_chart(scenarios,'other_delay_h',60,'추가 지연 (분)',[0,22]),width='stretch')
        st.caption('감소율은 일정 조정 전 A 대비, 추가 지연은 동일한 선별 48시간 조정에서의 비교입니다. 기준 227.2시간은 시뮬레이션 표본의 값이며 위 경로별 현황의 통합 평균이 아닙니다. 실제 도입 성과를 의미하지 않습니다.')
        st.html('<nav class="section-links"><a href="/simulation">다른 조정 조건 비교</a><a href="/improvement-results">개선안 결과와 한계</a></nav>')

    with st.expander('집계 기준과 출처'):
        st.write('현황: 팀의 저장된 경로별 집계. 야드 시간은 장치부터 온샤시까지이며 ITT는 두 터미널 합계입니다. 전체 평균과 공정별 평균 합계는 절삭·반올림으로 미세한 차이가 있습니다.')
        st.write('시뮬레이션: 2025년 자료를 사용한 저장 결과 중 선별 48시간 조건입니다. 현황 분석과 시뮬레이션은 표본·집계 기준을 구분해 읽어 주세요.')
        st.markdown(f'[시뮬레이션 원본 노트북]({simulation["source_url"]}) · [현황 집계 자료](https://github.com/busan-itt/dashboard/blob/main/prototype-streamlit/output/preliminary-analysis-20261109/figure-data.json)')
