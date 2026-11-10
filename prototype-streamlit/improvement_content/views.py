"""Supplied HTML pages, with live selection of saved simulation conditions."""
from pathlib import Path
from base64 import b64encode
import re
import streamlit as st

ROOT = Path(__file__).parent


def render_section(section_id: str) -> None:
    if section_id == "s3":
        from .results_view import render_results
        render_results()
        return
    source = (ROOT / "assets" / "presentation.html").read_text(encoding="utf-8")
    match = re.search(rf'<section id="{re.escape(section_id)}">.*?</section>', source, re.S)
    if match is None:
        st.error("발표 자료의 해당 영역을 찾을 수 없습니다.")
        return
    content = match.group(0)
    css = (ROOT / "presentation.css").read_text(encoding="utf-8")
    if section_id == "s1":
        from .sharing_map import render_proposal
        render_proposal(content, css)
        return
    if section_id == "s2":
        encoded = b64encode((ROOT / 'assets' / 'schedule-comparison.svg').read_bytes()).decode('ascii')
        content = content.replace('<!-- schedule-comparison -->',
                                  f'<img class="schedule-diagram" src="data:image/svg+xml;base64,{encoded}" '
                                  'alt="기존 연결선 일정보다 24·48·96시간 앞당김을 요청하는 개념도. 실제 접안은 선석 배정 결과에 따라 달라짐.">')
    st.html(f'<style>{css}</style><div class="presentation-content">{content}</div>')
