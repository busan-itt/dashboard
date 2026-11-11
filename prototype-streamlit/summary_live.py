"""앱 안에서 AI 요약을 가져온다.

순서: (1) 저장된 summary.json이 현재 데이터와 맞으면 사용
      (2) 아니면 API 키가 있을 때 앱이 직접 새로 생성(데이터 버전당 1회, 이후 캐시)
      (3) 키가 없거나 실패하면 None -> 호출한 쪽이 기존 템플릿 문장을 사용
"""
from __future__ import annotations

import json
import os
import time

import streamlit as st

from summary_core import DEFAULT_MODEL, generate
from summary_facts import facts_hash, read_saved, to_items

RETRY_AFTER_SEC = 600  # 생성이 실패하면 이 시간 동안은 다시 호출하지 않음(요금·지연 폭주 방지)
_failed_until: dict[str, float] = {}  # 데이터 지문별 '다시 시도 가능 시각'


def _secret(name: str):
    """Streamlit Secrets 또는 환경변수에서 값을 읽는다. 없으면 None."""
    try:
        value = st.secrets.get(name)  # secrets 파일이 없으면 예외가 날 수 있음
    except Exception:
        value = None
    return value or os.environ.get(name)


# 캐시 키는 digest(데이터 지문)뿐이다. 밑줄로 시작하는 인자는 캐시 키에서 제외된다.
@st.cache_data(show_spinner='분석 결과가 바뀌어 AI 요약을 새로 만드는 중입니다…', max_entries=4)
def _generate_cached(digest: str, _facts_json: str, _api_key: str, _model: str):
    return generate(json.loads(_facts_json), api_key=_api_key, model=_model, max_attempts=2, log=print)


def _generate_live(digest: str, facts: dict):
    """API로 요약을 만든다. 키가 없거나 최근에 실패했거나 이번에 실패하면 None."""
    api_key = _secret('ANTHROPIC_API_KEY')
    if not api_key or time.time() < _failed_until.get(digest, 0):
        return None
    try:
        return _generate_cached(digest, json.dumps(facts, ensure_ascii=False), api_key,
                                _secret('SUMMARY_MODEL') or DEFAULT_MODEL)
    except Exception as exc:  # 네트워크·검증 실패 등 어떤 오류든 화면은 깨지지 않게
        _failed_until[digest] = time.time() + RETRY_AFTER_SEC
        print(f'AI 요약 생성 실패: {type(exc).__name__}: {str(exc)[:200]}')  # 키는 출력하지 않음
        return None


def get_ai_summaries(facts: dict, *, compact: bool):
    """화면에 쓸 (제목, 설명) 튜플 4개를 돌려준다. 쓸 수 있는 AI 요약이 없으면 None."""
    digest = facts_hash(facts)
    summaries = read_saved(digest) or _generate_live(digest, facts)
    return to_items(summaries, compact=compact)
