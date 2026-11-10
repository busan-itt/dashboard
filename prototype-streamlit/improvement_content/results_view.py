"""Presentation of saved simulation outputs with unchanged comparison baselines."""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from overview import scenario_chart

ROOT = Path(__file__).parent
HOURS = (24, 48, 96)
APPROXIMATE_REALIZATION = {24: (88, 100), 48: (85, 100), 96: (78, 100)}


def realization_values(policy, hours, rows):
    a, c = rows['A'], rows['C']
    if a['realization_pct'] is not None and c['realization_pct'] is not None:
        return a['realization_pct'], c['realization_pct'], False
    a_value, c_value = APPROXIMATE_REALIZATION[hours]
    return a_value, c_value, True


def render_results():
    data = json.loads((ROOT/'data/simulation_all_results.json').read_text(encoding='utf-8'))
    st.html(ROOT/'presentation.css')
    with st.container(key='simulation_results'):
        lead = st.container()
        with st.container(border=True):
            policy_column, hours_column = st.columns(2, gap='large')
            with policy_column:
                policy = st.segmented_control('연결선 조정 방식', ['선별','전체'], default='선별', key='live_policy') or '선별'
            with hours_column:
                if st.session_state.get('live_hours', 48) not in HOURS:
                    st.session_state.live_hours = 48
                hours = st.segmented_control('요청 앞당김 시간', HOURS, default=48,
                                            format_func=lambda h: f'{h}시간', key='live_hours') or 48
        rows = {r['scenario']:r for r in data['rows'] if r['policy']==policy and r['hours']==hours}
        a, c = rows['A'], rows['C']
        real_a, real_c, approximate = realization_values(policy, hours, rows)
        prefix = '약 ' if approximate else ''
        baseline = data['baseline_mean_h_rounded']
        after = baseline * (1-a['reduction_pct']/100)
        low, high = min(r['reduction_pct'] for r in rows.values()), max(r['reduction_pct'] for r in rows.values())
        with lead:
            st.html(f'<header class="results-heading"><small>3 · 시뮬레이션 결과</small><h1>시뮬레이션 결과</h1>'
                    f'<p>{policy} 조정 · {hours}시간 앞당김 · 최소 연결 간격 24시간</p></header>'
                    f'<div class="sim-result-takeaway"><strong>야드 체류 감소율 {low:.2f}~{high:.2f}%</strong>'
                    f'<p>다른 선박의 추가 지연: A {a["other_delay_h"]*60:.2f}분 → C {c["other_delay_h"]*60:.2f}분</p></div>')
        cards = (
            ('A 기존 운영','야드 체류 감소율',f'{a["reduction_pct"]:.2f}%',f'{baseline:.1f}시간 → 약 {after:.1f}시간'),
            ('A 기존 운영','다른 선박 추가 지연',f'{a["other_delay_h"]*60:.2f}분','선석 공유 없이 일정 조정'),
            ('C 전체 통합','다른 선박 추가 지연',f'{c["other_delay_h"]*60:.2f}분','일정 조정과 선석 공유'),
            ('C 전체 통합','일정 조정 실현율',f'{real_c:.1f}%',f'A {prefix}{real_a:.1f}% → C {prefix}{real_c:.1f}%'),
        )
        st.html('<div class="sim-result-kpis">'+''.join(
            f'<article><small>{scenario}</small><span>{label}</span><strong>{value}</strong><p>{detail}</p></article>'
            for scenario,label,value,detail in cards)+'</div>')
        st.caption('체류 감소율·평균은 일정 조정 전 A 대비. 다른 선박 지연은 같은 일정 조정 조건에서 A·B·C 비교.')
        st.subheader('A·B·C 운영 방식 비교')
        st.markdown('**야드 체류 감소율**')
        st.altair_chart(scenario_chart(rows,'reduction_pct',1,'감소율 (%)',[0,20]),width='stretch',alt=f'{policy} {hours}시간 조정에서 A·B·C의 야드 체류 감소율')
        st.markdown('**다른 선박의 추가 접안 지연**')
        st.altair_chart(scenario_chart(rows,'other_delay_h',60,'추가 지연 (분)',[0,30]),width='stretch',alt=f'{policy} {hours}시간 조정에서 A·B·C의 다른 선박 추가 접안 지연')
        st.caption('모든 선택 조건에 같은 눈금 적용: 감소율 0–20% · 추가 지연 0–30분. 실제 도입 성과가 아닌 저장된 모형 결과.')

        with st.expander('상세 수치와 해석 기준'):
            table = []
            for scenario in 'ABC':
                r = rows[scenario]
                realization = r['realization_pct']
                if realization is None and scenario in ('A','C'):
                    realization = real_a if scenario=='A' else real_c
                table.append({'운영 방식':scenario,'야드 체류 감소율 (%)':r['reduction_pct'],
                              '다른 선박 추가 지연 (분)':r['other_delay_h']*60,
                              '일정 조정 실현율 (%)':realization})
            st.dataframe(pd.DataFrame(table),hide_index=True,width='stretch',
                         column_config={c:st.column_config.NumberColumn(format='%.2f') for c in table[0] if c!='운영 방식'},alt='선택한 조건의 A·B·C 기존 결과 수치')
            st.write(f'평균 체류는 반올림된 {baseline:.1f}시간 기준 근사치. 위 평균 체류는 A의 감소율로 계산.')
            st.write(f'A의 95% 구간: {a["ci_lower_pct"]:.2f}~{a["ci_upper_pct"]:.2f}%. B·C의 구간은 이 자료에 없음.')
            st.write('일정 조정 실현율: 앞당김 요청이 실제 접안 일정에 반영된 정도. 전체 정책 실현율은 기존 화면의 정수 반올림 값을 유지하며, B의 실현율 자료가 없으면 빈칸으로 표시.')
            st.write('네 KPI의 결과가 함께 확인된 24·48·96시간만 선택 가능. 화면에서 모델을 다시 실행하지 않음.')
            st.markdown(f'[최종 시뮬레이션 원본]({data["source_url"]})')
        st.html('<nav class="analysis-next"><a href="/improvement-results">개선안 결과 →</a></nav>')
