"""Simplified harbor map; scope comes from the pinned simulation's NEIGHBORS."""
from base64 import b64encode
from html import escape
import json
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).parent

# Relative positions traced conceptually from the user's reference map; not GIS.
TERMINALS = {
    'DGT': ('45,65 150,65 150,330 45,330', 98, 200),
    'HJNC': ('265,45 435,45 435,155 265,155', 350, 105),
    'PNC': ('445,45 690,45 690,155 445,155', 568, 105),
    'PNIT': ('700,45 950,45 950,155 700,155', 825, 105),
    'BCT': ('310,410 500,366 529,490 340,534', 420, 452),
    'BNCT': ('510,364 720,316 750,440 540,488', 630, 405),
    'HPNT': ('730,314 940,266 970,390 760,438', 850, 355),
}


def allowed_terminals(mode, terminal, neighbors):
    if mode == 'A':
        return {terminal}
    if mode == 'B':
        return {terminal, *neighbors[terminal]}
    return set(neighbors)


def map_svg(mode, terminal, neighbors):
    allowed = allowed_terminals(mode, terminal, neighbors)
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1020 570">',
             '<title>부산신항 선석 공유 범위</title>',
             '<rect width="1020" height="570" fill="#F2F5F6"/>',
             '<path d="M160 162H970V250L300 432 160 480Z" fill="#E4F0F5"/>',
             '<path d="M160 162H970M970 250 300 432 160 480" fill="none" stroke="#C4D7E1" stroke-width="2"/>',
             '<text x="570" y="262" text-anchor="middle" fill="#6A8899" font-size="20" font-family="Malgun Gothic,sans-serif">부산신항</text>']
    for name, (points, x, y) in TERMINALS.items():
        own = name == terminal
        shared = name in allowed and not own
        fill = '#3F617C' if own else '#FCE4DA' if shared else '#FFFFFF'
        stroke = '#192C3A' if own else '#C78770' if shared else '#C6D0D7'
        ink = '#FFFFFF' if own else '#192C3A'
        parts.append(f'<polygon points="{points}" fill="{fill}" stroke="{stroke}" stroke-width="{3 if own else 2}"/>')
        parts.append(f'<text x="{x}" y="{y}" text-anchor="middle" dominant-baseline="middle" fill="{ink}" font-size="25" font-weight="700" font-family="Malgun Gothic,sans-serif">{name}</text>')
        if own:
            parts.append(f'<text x="{x}" y="{y+28}" text-anchor="middle" fill="{ink}" font-size="15" font-family="Malgun Gothic,sans-serif">기준 터미널</text>')
    parts.append('</svg>')
    return ''.join(parts)


def render_proposal(content, css):
    data = json.loads((ROOT/'data/berth-sharing-map.json').read_text(encoding='utf-8'))
    neighbors = data['neighbors']
    before, after = content.split('<!-- sharing-map -->')
    # Native widgets sit between the unchanged proposal header and baseline figures.
    before = before.replace('<section id="s1">', '<div id="s1">')
    after = after.replace('</section>', '</div>')
    st.html(f'<style>{css}</style><div class="presentation-content">{before}</div></div>')
    with st.container(key='sharing_map_controls'):
        modes, terminals = st.columns([1.4, 1], gap='medium')
        with modes:
            mode = st.segmented_control('운영 방식', ['A','B','C'],
                                    format_func=lambda v: {'A':'A 기존 운영','B':'B 인접 공유','C':'C 전체 통합'}[v],
                                    default='B', key='sharing_map_mode') or 'B'
        with terminals:
            terminal = st.selectbox('기준 터미널', list(TERMINALS), key='sharing_map_terminal')
        allowed = allowed_terminals(mode, terminal, neighbors)
        ordered = [terminal] + [t for t in neighbors if t != terminal and t in allowed]
        label = f'{terminal} 기준 공유 가능: '+ ' · '.join(ordered)
        st.write(label)
        svg = b64encode(map_svg(mode, terminal, neighbors).encode('utf-8')).decode('ascii')
        st.html(f'<figure class="sharing-map"><img src="data:image/svg+xml;base64,{svg}" alt="{escape(label)}">'
                '<figcaption><span class="map-own">기준 터미널</span><span class="map-shared">추가 공유 가능</span><span class="map-other">공유 범위 밖</span></figcaption></figure>')
        st.caption('첨부 지도를 바탕으로 단순화한 위치 개념도. B는 자기 터미널과 모형에 지정된 인접 터미널만 이용하며, 인접 터미널의 이웃까지 확대하지 않음.')
        with st.expander('B의 인접 기준과 출처'):
            st.dataframe([{'기준 터미널':t,'인접 공유 대상':' · '.join(ns)} for t,ns in neighbors.items()],hide_index=True,width='stretch',alt='최종 시뮬레이션의 터미널별 인접 관계')
            st.markdown(f'[최종 시뮬레이션 · NEIGHBORS / SCENARIOS 정의]({data["source_url"]})')
    st.html(f'<div class="presentation-content"><div id="s1-reference">{after}</div>')
