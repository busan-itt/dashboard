"""Navigation and catalog of existing project data artifacts."""
import json
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent


def render_attachments():
    st.html('<header class="results-heading"><small>ATTACHMENTS</small><h1>첨부</h1><p>분석 자료와 초기 기획 문서</p></header>'
            '<nav class="intro-destinations attachment-destinations" aria-label="첨부 자료">'
            '<a href="/used-data"><h2>사용한 데이터</h2><p>입력자료 범위, 분석 기준과 화면에 사용한 집계 파일</p><span>자료 보기 →</span></a>'
            '<a href="/planning"><h2>초기 개선안 기획</h2><p>프로젝트 초기의 개선 아이디어와 기획 자료</p><span>자료 보기 →</span></a></nav>')


def render_used_data():
    routes = json.loads((ROOT/'assets/preliminary-analysis/figure-data.json').read_text(encoding='utf-8'))
    reports = json.loads((ROOT/'assets/correlation-analysis/unified/reports.json').read_text(encoding='utf-8'))
    simulation = json.loads((ROOT/'improvement_content/data/simulation_all_results.json').read_text(encoding='utf-8'))
    with st.container(key='attachment_data'):
        st.html('<header class="results-heading"><small>DATA SOURCES</small><h1>사용한 데이터</h1><p>시뮬레이션 입력자료와 발표에 사용한 집계 자료</p></header>')
        st.subheader('자료 범위')
        st.dataframe(pd.DataFrame([
            {'자료':'환적 컨테이너','범위':'DGT·HJNC 자부두 및 양방향 타부두','주요 항목':'반입·장치·온샤시·반출 시각'},
            {'자료':'선석배정현황','범위':'PNC·PNIT·HPNT·HJNC·BNCT·BCT·DGT','주요 항목':'접안·출항 일정, 선석 점유'},
            {'자료':'선박 제원','범위':'시뮬레이션에 연결한 선박 자료','주요 항목':'선박 길이 등 배정 조건'},
            {'자료':'PORT-MIS','범위':'선석 자료와 연결한 입항 기록','주요 항목':'실제 입항 시각'},
        ]),hide_index=True,width='stretch',alt='최종 시뮬레이션에 명시된 입력자료의 범위와 주요 항목')
        st.caption('입력자료 구성은 2025년 자료 기반 최종 시뮬레이션 기준. 현황·상관분석의 표본과 집계 단위는 아래 기준을 별도로 적용.')
        st.markdown(f'[시뮬레이션 원본 · 입력자료 구성]({simulation["source_url"]})')
        st.subheader('발표에 사용한 집계 파일')
        st.caption('아래 파일은 화면에 사용한 집계·저장 결과이며, 컨테이너별 원자료는 아님.')
        for title, description, path in (
            ('환적 경로별 현황','평균·중앙값, 분석 건수와 야드 체류 비중',ROOT/'assets/preliminary-analysis/figure-data.json'),
            ('상관분석 결과','표본·측정 구간·상관계수와 기존 분석 결론',ROOT/'assets/correlation-analysis/unified/reports.json'),
            ('시뮬레이션 저장 결과',f'{len(simulation["rows"])}개 조건의 체류 감소율·추가 지연 등',ROOT/'improvement_content/data/simulation_all_results.json'),
        ):
            with st.container(border=True):
                st.markdown(f'**{title}**')
                st.caption(description)
                st.download_button('집계 파일 받기 · JSON',data=path.read_bytes(),file_name=path.name,mime='application/json',key=f'attachment_{path.stem}')
        with st.expander('표본 수와 분석 기준'):
            st.markdown('**현황 분석**')
            st.dataframe(pd.DataFrame([{'경로':r['route'],'분석 건수':r['total_n']} for r in routes]),hide_index=True,width='stretch',alt='기존 현황 분석의 네 경로별 표본 수')
            st.write('전체 소요시간은 최초 반입부터 최종 반출까지. 야드 체류는 장치부터 온샤시까지이며, ITT는 두 터미널 합계.')
            st.markdown('**상관분석**')
            st.dataframe(pd.DataFrame([{'경로':label,'기준 표본':reports[key]['sample'],'측정 구간':reports[key]['definition'],'분석 단위':reports[key]['unit']} for key,label in (
                ('dgt','DGT_ODT'),('hjnc','HJNC_ODT'),('forward','DGT → HJNC ITT'),('reverse','HJNC → DGT ITT'))]),hide_index=True,width='stretch',alt='경로별 상관분석의 기존 표본·측정 구간·분석 단위')
            st.write('DGT ODT의 장치→반출과 HJNC ODT의 장치→온샤시는 서로 다른 측정 구간. ITT의 총 야드 시간 계산 표본은 방향별 상세 화면의 기준을 적용.')
            st.markdown('**시뮬레이션**')
            st.write(f'선석은 7개 터미널, 환적 체류는 DGT·HJNC 표본. 모형 기준 평균 {simulation["baseline_mean_h_rounded"]:.1f}시간은 현황의 통합 평균과 구분. 화면은 저장된 결과를 표시하며 모델을 다시 실행하지 않음.')
        st.html('<nav class="attachment-back"><a href="/attachments">첨부 →</a></nav>')
