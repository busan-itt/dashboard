"""AI 요약에 쓰는 '사실 목록'과 저장된 요약 불러오기.

이 모듈은 앱(Streamlit)과 생성 스크립트가 함께 씁니다.
외부 API 패키지에 의존하지 않으므로 배포 환경(requirements.txt)을 바꾸지 않습니다.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

# 생성된 AI 요약이 저장되는 위치 (generate_summary.py가 만들고, 앱은 읽기만 함)
SUMMARY_PATH = Path(__file__).parent / 'assets' / 'ai-summary' / 'summary.json'


def build_facts(routes, reports, simulation, scenarios) -> dict:
    """저장된 분석 결과에서 AI가 근거로 삼을 숫자만 뽑아 하나의 딕셔너리로 만든다."""
    # 경로별 야드 체류 비중(%)을 이름과 함께 정리
    route_shares = {r['route']: round(r['yard_share_pct'], 2) for r in routes}
    # 상관분석 그래프 전체에서 상관계수 절댓값의 최댓값
    max_abs_r = max(abs(p['r']) for rep in reports.values() for p in rep['plots'])
    # 시뮬레이션 기준(앞당김 정책)의 평균 체류시간
    baseline = simulation['baseline_mean_h_rounded']
    # 운영 방식(A·B·C)별 감소율과 다른 선박의 추가 접안 지연(분)
    scenario_facts = {
        key: {
            'reduction_pct': round(row['reduction_pct'], 2),
            'other_delay_min': round(row['other_delay_h'] * 60, 2),
            # 기준 평균에 감소율을 적용한 모형상 평균 체류시간(시간)
            'mean_after_h': round(baseline * (1 - row['reduction_pct'] / 100), 1),
        }
        for key, row in sorted(scenarios.items())
    }
    return {
        'route_count': len(routes),
        'route_yard_share_pct': route_shares,
        'yard_share_min_pct': min(route_shares.values()),
        'yard_share_max_pct': max(route_shares.values()),
        'max_abs_correlation_r': round(max_abs_r, 3),
        'simulation_condition': {'policy': '선별', 'hours': 48},
        'baseline_mean_h': baseline,
        'scenarios': scenario_facts,
    }


def facts_hash(facts: dict) -> str:
    """사실 목록의 지문(해시). 데이터가 바뀌면 값이 달라져서 오래된 요약을 걸러낸다."""
    canonical = json.dumps(facts, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:16]


def load_ai_summaries(facts: dict, *, compact: bool):
    """저장된 AI 요약을 읽는다. 없거나, 깨졌거나, 현재 데이터와 맞지 않으면 None을 돌려준다."""
    try:
        saved = json.loads(SUMMARY_PATH.read_text(encoding='utf-8'))
        # 요약을 만든 시점의 데이터와 지금 데이터가 다르면 사용하지 않음(오래된 숫자 방지)
        if saved.get('facts_hash') != facts_hash(facts):
            return None
        items = saved['compact' if compact else 'full']
        return tuple((item['title'], item['description']) for item in items)
    except (OSError, ValueError, KeyError, TypeError):
        # 파일 없음·JSON 오류·구조 불일치 모두 기존 문장(템플릿)으로 되돌아가게 한다
        return None
