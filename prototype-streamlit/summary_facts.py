"""AI 요약에 쓰는 '사실 목록'과 저장된 요약 불러오기.

이 모듈은 앱(Streamlit)과 생성 코드가 함께 씁니다.
외부 API 패키지에 의존하지 않습니다.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent
# 미리 만들어 둔 AI 요약(선택). 현재 데이터와 지문이 맞을 때만 사용됨
SUMMARY_PATH = ROOT / 'assets' / 'ai-summary' / 'summary.json'


def _read_json(relative: str):
    """앱 폴더 기준 상대 경로의 JSON을 읽는다."""
    return json.loads((ROOT / relative).read_text(encoding='utf-8'))


def build_facts(routes, reports, simulation, scenarios) -> dict:
    """분석 결과 전체에서 AI가 근거로 삼을 내용을 하나의 딕셔너리로 만든다.

    여기에 들어간 값이 하나라도 바뀌면 facts_hash가 달라져 요약이 새로 만들어진다.
    """
    # 경로별 야드 체류 비중(%)
    route_shares = {r['route']: round(r['yard_share_pct'], 2) for r in routes}
    # 상관분석 전체에서 상관계수 절댓값의 최댓값
    max_abs_r = max(abs(p['r']) for rep in reports.values() for p in rep['plots'])
    # 시뮬레이션 기준 평균 체류시간(시간)
    baseline = simulation['baseline_mean_h_rounded']
    # 대표 조건(선별 48시간)의 운영 방식(A·B·C)별 결과
    scenario_facts = {
        key: {
            'reduction_pct': round(row['reduction_pct'], 2),
            'other_delay_min': round(row['other_delay_h'] * 60, 2),
            'mean_after_h': round(baseline * (1 - row['reduction_pct'] / 100), 1),
        }
        for key, row in sorted(scenarios.items())
    }
    # 현황 분석: 공정별 소요시간(초)
    stage_seconds = {
        item['name']: [[stage, seconds] for stage, seconds, _group in item['stages']]
        for item in _read_json('assets/preliminary-analysis/stage-durations.json')
    }
    return {
        # --- 대시보드 카드에 쓰는 핵심 값 ---
        'route_count': len(routes),
        'route_yard_share_pct': route_shares,
        'yard_share_min_pct': min(route_shares.values()),
        'yard_share_max_pct': max(route_shares.values()),
        'max_abs_correlation_r': round(max_abs_r, 3),
        'simulation_condition': {'policy': '선별', 'hours': 48},
        'baseline_mean_h': baseline,
        'scenarios': scenario_facts,
        # --- 분석 내용 전체 (이 부분이 바뀌어도 요약이 갱신되도록 포함) ---
        'current_state': [
            {k: r[k] for k in ('route', 'total_n', 'stage_n', 'reported_total_mean_h',
                               'reported_total_median_h', 'yard_share_pct') if k in r}
            for r in routes
        ],
        'stage_durations_seconds': stage_seconds,
        'correlation_reports': {
            key: {
                'title': rep.get('title'),
                'sample': rep.get('sample'),
                'definition': rep.get('definition'),
                'conclusion': rep.get('conclusion'),
                'note': rep.get('note'),
                'berth_correlation_note': rep.get('berth_correlation_note'),
                'plots': [{'label': p['label'], 'r': p['r'], 'n': p['n']} for p in rep['plots']],
            }
            for key, rep in reports.items()
        },
        'simulation_all_conditions': [
            {
                'policy': row['policy'], 'hours': row['hours'], 'scenario': row['scenario'],
                'reduction_pct': row['reduction_pct'],
                'other_delay_min': round(row['other_delay_h'] * 60, 2),
                'realization_pct': row.get('realization_pct'),
                'ci_lower_pct': row.get('ci_lower_pct'), 'ci_upper_pct': row.get('ci_upper_pct'),
            }
            for row in simulation['rows']
        ],
        # 시뮬레이션 노트북 출력(표·검증 결과)은 텍스트 그대로 전달
        'simulation_notes': {
            key: simulation[key]
            for key in ('sharing_results', 'uncertainty_results', 'holdout_results', 'ml_results')
            if key in simulation
        },
        'berth_sharing_neighbors': _read_json('improvement_content/data/berth-sharing-map.json').get('neighbors'),
    }


def facts_hash(facts: dict) -> str:
    """사실 목록의 지문(해시). 데이터가 바뀌면 값이 달라진다."""
    canonical = json.dumps(facts, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()[:16]


def read_saved(facts_digest: str):
    """summary.json이 현재 데이터(지문)와 맞으면 그 내용을, 아니면 None을 돌려준다."""
    try:
        saved = json.loads(SUMMARY_PATH.read_text(encoding='utf-8'))
        if saved.get('facts_hash') != facts_digest:
            return None  # 오래된 요약은 쓰지 않음
        return {'compact': saved['compact'], 'full': saved['full']}
    except (OSError, ValueError, KeyError, TypeError):
        return None  # 파일 없음·JSON 오류·구조 불일치


def to_items(summaries: dict | None, *, compact: bool):
    """{'compact': [...], 'full': [...]} 에서 화면용 (제목, 설명) 튜플을 꺼낸다."""
    if not summaries:
        return None
    try:
        return tuple((it['title'], it['description']) for it in summaries['compact' if compact else 'full'])
    except (KeyError, TypeError):
        return None
