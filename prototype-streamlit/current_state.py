"""Presentation of the team's saved current-state analysis, without recomputation."""
import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from overview import BLUE, CORAL, snapshot

ROOT = Path(__file__).parent


def duration(seconds):
    days, remainder = divmod(seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    return ' '.join(f'{n}{unit}' for n, unit in ((days, '일'), (hours, '시간'), (minutes, '분'), (seconds, '초')) if n)


def stage_chart(route, yard):
    rows = [s for s in route['stages'] if (s[2] != 'other') == yard]
    frame = pd.DataFrame([{'공정': label, '시간': seconds / (86400 if yard else 60), '소요시간': duration(seconds)} for label, seconds, _ in rows])
    unit, limit = ('일', 12.5) if yard else ('분', 56.25)
    bars = alt.Chart(frame).mark_bar(size=23, color=CORAL if yard else BLUE).encode(
        x=alt.X('시간:Q', title=f'평균 소요시간 ({unit})', scale=alt.Scale(domain=[0, limit]), axis=alt.Axis(values=[0, 2, 4, 6, 8, 10] if yard else [0, 15, 30, 45])),
        y=alt.Y('공정:N', sort=frame['공정'].tolist(), title=None),
        tooltip=['공정:N', '소요시간:N'],
    )
    labels = bars.mark_text(align='left', dx=6, fontSize=13, color='#192C3A').encode(text='소요시간:N', color=alt.value('#192C3A'))
    return (bars + labels).properties(height=max(180, len(rows)*50+90), padding={'right':25, 'top':8}).configure_view(stroke=None).configure_axis(labelFontSize=13, titleFontSize=13, titleFontWeight='normal', labelPadding=8, ticks=False, domain=False, gridColor='#E9EEF1')


def share_chart(stages):
    rows = []
    for route in stages:
        total = sum(s[1] for s in route['stages'])
        left = 0
        for order, (kind, label) in enumerate((('yard1', '첫 번째 터미널 야드'), ('yard2', '두 번째 터미널 야드'), ('other', '그 외 공정'))):
            value = sum(s[1] for s in route['stages'] if s[2] == kind) / total * 100
            if value:
                rows.append({'경로': route['name'], '구간': label, '시작': left, '끝': left+value, '중앙': left+value/2, '비중': value, '표시': f'{value:.1f}%' if value > 10 else ''})
            left += value
    chart = alt.Chart(pd.DataFrame(rows))
    bars = chart.mark_bar(size=30).encode(
        x=alt.X('시작:Q', title='공정별 평균시간 합계 대비 비중 (%)', scale=alt.Scale(domain=[0,100]), axis=alt.Axis(values=[0,25,50,75,100])),
        x2='끝:Q', y=alt.Y('경로:N', sort=[r['name'] for r in stages], title=None),
        color=alt.Color('구간:N', scale=alt.Scale(domain=['첫 번째 터미널 야드','두 번째 터미널 야드','그 외 공정'], range=[BLUE,CORAL,'#7891A4']), legend=alt.Legend(title=None, orient='top', columns=1)),
        tooltip=['경로:N','구간:N',alt.Tooltip('비중:Q',format='.2f')],
    )
    labels = chart.mark_text(fontSize=13).encode(x='중앙:Q', y=alt.Y('경로:N', sort=[r['name'] for r in stages]), text='표시:N', color=alt.condition(alt.datum['구간']=='첫 번째 터미널 야드',alt.value('#FFFFFF'),alt.value('#192C3A')))
    return (bars+labels).properties(height=320).configure_view(stroke=None).configure_axis(labelFontSize=13,titleFontSize=13,titleFontWeight='normal',labelPadding=8,ticks=False,domain=False,gridColor='#E9EEF1').configure_legend(labelFontSize=13)


def overall_chart(routes):
    """One range per route keeps the two measures separate without paired bars."""
    frame = pd.DataFrame([{'경로':r['route'], '평균':r['reported_total_mean_h'], '중앙값':r['reported_total_median_h']} for r in routes])
    order = frame['경로'].tolist()
    base = alt.Chart(frame)
    lines = base.mark_rule(color='#CDD7DE', strokeWidth=3).encode(
        x=alt.X('중앙값:Q', title='전체 소요시간 (시간)', scale=alt.Scale(domain=[0,255])),
        x2='평균:Q', y=alt.Y('경로:N', sort=order, title=None))
    points = alt.Chart(frame.melt(id_vars='경로', var_name='지표', value_name='시간')).mark_point(filled=True, size=95).encode(
        x='시간:Q', y=alt.Y('경로:N', sort=order),
        color=alt.Color('지표:N', scale=alt.Scale(domain=['평균','중앙값'], range=[BLUE,CORAL]), legend=alt.Legend(title=None, orient='top')),
        tooltip=['경로:N','지표:N',alt.Tooltip('시간:Q',format='.2f')])
    mean_labels = base.mark_text(align='left',dx=9,fontSize=13,color='#192C3A').encode(x='평균:Q',y=alt.Y('경로:N',sort=order),text=alt.Text('평균:Q',format='.2f'))
    median_labels = base.mark_text(align='right',dx=-9,fontSize=13,color='#192C3A').encode(x='중앙값:Q',y=alt.Y('경로:N',sort=order),text=alt.Text('중앙값:Q',format='.2f'))
    return (lines+points+mean_labels+median_labels).properties(height=290).configure_view(stroke=None).configure_axis(labelFontSize=13,titleFontSize=13,titleFontWeight='normal',labelPadding=8,ticks=False,domain=False,gridColor='#E9EEF1').configure_legend(labelFontSize=13)


def stage_summary_chart(stages):
    """Two unit-separated panels in one summary figure, using saved stage means."""
    panels = []
    order = [r['name'] for r in stages]
    for yard, title, divisor, limit in ((True,'야드 체류 합계 · 일',86400,12.5), (False,'나머지 공정 합계 · 분',60,120)):
        rows = []
        for route in stages:
            seconds = sum(s[1] for s in route['stages'] if (s[2] != 'other') == yard)
            rows.append({'경로':route['name'],'시간':seconds/divisor,'소요시간':duration(seconds),'표시':f'{seconds/divisor:.2f}{"일" if yard else "분"}'})
        bars = alt.Chart(pd.DataFrame(rows)).mark_bar(size=22,color=CORAL if yard else BLUE).encode(
            x=alt.X('시간:Q',title=title,scale=alt.Scale(domain=[0,limit]),axis=alt.Axis(tickCount=5)),
            y=alt.Y('경로:N',sort=order,title=None), tooltip=['경로:N','소요시간:N'])
        labels = bars.mark_text(align='left',dx=6,fontSize=12,color='#192C3A').encode(text='표시:N',color=alt.value('#192C3A'))
        panels.append((bars+labels).properties(width=450,height=190))
    return alt.vconcat(*panels,spacing=22).resolve_scale(x='independent').configure_view(stroke=None).configure_axis(labelFontSize=13,titleFontSize=13,titleFontWeight='normal',labelPadding=8,ticks=False,domain=False,gridColor='#E9EEF1')


def render_current_state():
    routes, _, _, _ = snapshot()
    stages = json.loads((ROOT/'assets/preliminary-analysis/stage-durations.json').read_text(encoding='utf-8'))
    with st.container(key='current_state'):
        st.html('<header class="results-heading"><small>02 / CURRENT STATE</small><h1>현황 분석</h1><p>환적 경로별 전체 소요시간과 공정별 체류시간</p></header>')
        st.subheader('1. 분석 대상과 전체 소요시간')
        st.write('평균은 DGT → HJNC가 가장 길고, 모든 경로에서 중앙값보다 높음.')
        st.altair_chart(overall_chart(routes), width='stretch', alt='네 환적 경로별 평균과 중앙값의 전체 소요시간 비교')
        st.caption('전체 소요시간: 최초 반입부터 최종 반출까지. ITT는 두 터미널의 체류와 터미널 간 이동 포함.')
        with st.expander('분석 건수·경로별 상세 수치'):
            table = pd.DataFrame([{'경로':r['route'], '분석 건수':r['total_n'], '평균 (시간)':r['reported_total_mean_h'], '중앙값 (시간)':r['reported_total_median_h'], '야드 평균 합계 (시간)':r['yard_mean_sum_h'], '야드 비중 (%)':r['yard_share_pct']} for r in routes])
            st.dataframe(table, hide_index=True, width='stretch', column_config={c:st.column_config.NumberColumn(format='%.2f') for c in table.columns if c not in ('경로','분석 건수')}, alt='네 경로별 분석 건수와 기존 소요시간·야드 비중')

        st.subheader('2. 공정별 소요시간 비교')
        st.write('야드 체류는 수일, 나머지 공정은 분 단위. 시간이 집중된 구간은 야드.')
        st.altair_chart(stage_summary_chart(stages), width='content', alt='네 경로의 야드 체류 합계는 일, 나머지 공정 합계는 분 단위로 구분한 요약 비교')
        st.caption('개별 공정의 평균시간을 합산한 비교. ITT 야드는 두 터미널 합계이며, 나머지 공정에는 부두 간 이동 포함. 위·아래 그래프의 단위와 눈금은 서로 다름.')
        with st.expander('터미널·방향별 상세 그래프와 공정 수치'):
            st.write('ODT 야드 체류는 평균 약 8일. ITT 부두 간 이동은 두 방향 모두 평균 약 10분.')
            for index, route in enumerate(stages):
                with st.container(border=True, key=f'state_stage_detail_{index}'):
                    st.markdown(f'**{route["name"]}**')
                    for yard in (True, False):
                        st.caption('야드 체류 · 일 단위' if yard else '나머지 공정 · 분 단위')
                        st.altair_chart(stage_chart(route, yard), width='stretch', alt=f'{route["name"]}의 {"야드 체류" if yard else "나머지 공정"} 평균 소요시간')
                    st.dataframe(pd.DataFrame([{'공정':label,'평균 소요시간':duration(seconds),'초':seconds} for label,seconds,_ in route['stages']]),hide_index=True,width='stretch',alt=f'{route["name"]}의 공정별 원본 평균시간')

        st.subheader('3. 야드 장치 구간이 차지하는 시간 비중')
        st.write('네 경로 모두 공정별 평균시간 합계의 약 99.26~99.86%가 야드 체류.')
        st.altair_chart(share_chart(stages), width='stretch', alt='네 경로의 첫 번째·두 번째 터미널 야드 체류와 그 외 공정 비중')
        st.caption('정상적인 연결선 대기 포함. 야드 체류 전체가 줄일 수 있는 지연은 아님.')
        with st.expander('야드 비중 상세 수치와 집계 기준'):
            st.dataframe(pd.DataFrame([{'경로':r['route'],'야드 비중 (%)':r['yard_share_pct']} for r in routes]),hide_index=True,width='stretch',column_config={'야드 비중 (%)':st.column_config.NumberColumn(format='%.2f')},alt='네 경로의 기존 야드 체류 비중')
            st.write('야드 장치부터 온샤시까지의 평균시간 합계 ÷ 공정별 평균시간 합계. ITT는 두 터미널의 야드 시간 합산. 초 단위로 절삭된 공정 평균의 합산값이며, 컨테이너별 비중의 평균과 구분.')

        st.subheader('4. 선행 분석에서 도출한 문제와 분석 방향')
        st.html('<div class="state-conclusion"><strong>분석의 초점은 야드 체류시간</strong><p>체류 관련 요인을 분석하고, 일정 조정과 선석 공유 효과를 비교.</p></div>')
        st.html('<nav class="section-links"><a href="/dashboard-summary">분석 내용 →</a></nav>')
