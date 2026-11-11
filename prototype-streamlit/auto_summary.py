"""분석 결과(JSON)의 값을 조건으로 판단해 홈의 '분석 핵심 요약' 문장을 만든다.

외부 API나 키 없이 파이썬 규칙만 쓴다. 데이터가 바뀌면 같은 기준으로 문장도 바로 바뀐다.
판단 기준(임계값)은 아래 상수에 모아 두었으므로, 문장이 왜 그렇게 나왔는지는 이 파일에서 확인할 수 있다.
"""
from __future__ import annotations

import math

# ---- 판단 기준 -------------------------------------------------------------
YARD_ALMOST_ALL = 95   # 야드 비중이 모든 경로에서 이 값(%) 이상이면 '거의 전부'
YARD_MOST = 70         # 이 값 이상이면 '대부분'
YARD_HALF = 50         # 이 값 이상이면 '절반 이상'
YARD_SPREAD = 10       # 경로 간 비중 차이가 이 값(%p) 이상이면 최저·최고 경로를 함께 적음

R_WEAK = 0.3           # |r|이 이 값 미만이면 '약한 상관'
R_STRONG = 0.5         # |r|이 이 값 이상이면 '뚜렷한 상관'
P_LEVEL = 0.05         # 통계적 유의 기준

REDUCTION_BIG = 15     # 체류시간 감소율(%) 구간: 크게
REDUCTION_CLEAR = 5    # 뚜렷하게
REDUCTION_SMALL = 1    # 소폭 (이 값 미만이면 '거의 변화 없음')
SAME_GAP = 1           # A와 C의 감소율 차이가 이 값(%p) 미만이면 '비슷하다'고 봄

DELAY_GONE = 0.9       # 다른 선박 지연이 기존 대비 이 비율 이상 줄면 '거의 해소'
DELAY_REDUCED = 0.3    # 이 비율 이상 줄면 '감소'
DELAY_SAME = 0.1       # 이 비율 안쪽의 변화면 '큰 차이 없음', 그보다 늘면 '증가'

CONDITION = '선별 48시간 앞당김'  # 대표 시뮬레이션 조건 (overview.snapshot()과 같은 조건)
COUNT_WORDS = {1: '한', 2: '두', 3: '세', 4: '네', 5: '다섯', 6: '여섯', 7: '일곱', 8: '여덟'}


# ---- 작은 도우미 -----------------------------------------------------------
def route_phrase(count: int) -> str:
    """경로 수를 '네 경로'처럼 자연스럽게 읽히는 말로 바꾼다."""
    return f'{COUNT_WORDS[count]} 경로' if count in COUNT_WORDS else f'{count}개 경로'


def pct_span(low: float, high: float) -> str:
    """최솟값과 최댓값이 같으면 하나만, 다르면 '99.26~99.86%'처럼 범위로 적는다."""
    return f'{low:.2f}%' if f'{low:.2f}' == f'{high:.2f}' else f'{low:.2f}~{high:.2f}%'


def minutes(hours: float) -> str:
    """시간 값을 분으로 바꿔 적는다. 사실상 0이면 '0분'."""
    value = hours * 60
    return '0분' if value < 0.005 else f'{value:.2f}분'


def p_value(r: float, n: int) -> float:
    """상관계수 r과 표본 수 n으로 양측 p값을 구한다(피셔 z 근사). 보고서 값과 소수 셋째 자리까지 맞는다."""
    if n <= 3:
        return 1.0
    if abs(r) >= 1:
        return 0.0
    z = math.atanh(r) * math.sqrt(n - 3)
    return math.erfc(abs(z) / math.sqrt(2))


def fmt_p(p: float) -> str:
    return 'p<0.001' if p < 0.001 else f'p={p:.3f}'


# ---- 1. 환적 시간의 구성(야드 체류) ----------------------------------------
def yard_card(routes, compact):
    shares = [(r['route'], r['yard_share_pct']) for r in routes]
    low_name, low = min(shares, key=lambda item: item[1])
    high_name, high = max(shares, key=lambda item: item[1])
    span = pct_span(low, high)
    paths = route_phrase(len(routes))

    if low >= YARD_ALMOST_ALL:
        title = '환적 시간은 거의 전부 야드 체류'
    elif low >= YARD_MOST:
        title = '환적 시간의 대부분은 야드 체류'
    elif low >= YARD_HALF:
        title = '환적 시간의 절반 이상이 야드 체류'
    elif high >= YARD_HALF:
        title = '경로에 따라 야드 체류 비중이 크게 다름'
    else:
        title = '야드 체류는 환적 시간의 일부'

    if compact:
        lead = f'{paths} 모두 야드 비중 {span}.' if low >= YARD_HALF else f'경로별 야드 비중 {span}.'
        return title, f'{lead} 연결선을 기다리는 시간 포함.'

    text = f'분석한 {paths}에서 야드 장치 구간은 공정별 평균시간 합계의 {span}를 차지했습니다.'
    if high - low >= YARD_SPREAD:
        text += f' 가장 낮은 곳은 {low_name}({low:.2f}%), 가장 높은 곳은 {high_name}({high:.2f}%)입니다.'
    return title, text + ' 정상적인 연결선 대기도 포함된 값입니다.'


# ---- 2. 선박 운영시간과의 상관 ---------------------------------------------
def correlation_plots(reports):
    """모든 상관분석 그래프를 한 목록으로 펼치고, r·n으로 p값을 계산해 붙인다."""
    plots = []
    for rep in reports.values():
        scope = rep.get('title', '')
        if rep.get('direction'):
            scope += f" {rep['direction']}"
        for plot in rep['plots']:
            plots.append({
                'scope': scope, 'label': plot['label'].rstrip('*'),
                'r': plot['r'], 'n': plot['n'], 'p': p_value(plot['r'], plot['n']),
            })
    return plots


def correlation_card(reports, compact):
    plots = correlation_plots(reports)
    top = max(plots, key=lambda item: abs(item['r']))
    max_r = abs(top['r'])
    significant = [item for item in plots if item['p'] < P_LEVEL]
    notable = [item for item in plots if abs(item['r']) >= R_WEAK]

    if max_r < R_WEAK:
        title = '선박 운영시간과의 상관관계는 약함' if compact else '선박 운영시간과의 선형 관계는 약함'
        if significant:
            title = title.replace('는 약함', '는 대체로 약함')
    elif max_r < R_STRONG:
        title = '운영시간 지표 일부에서 상관이 관측됨'
    else:
        title = '운영시간 지표와 뚜렷한 상관이 있음'

    if compact:
        if max_r < R_WEAK and not significant:
            return title, '분석한 운영시간 지표만으로는 야드 체류 차이를 설명하기 어려움.'
        if max_r < R_WEAK:
            return title, f'유의한 지표가 있어도 |r| 최대 {max_r:.2f}. 야드 체류 차이를 설명하기엔 부족함.'
        return title, (f"{top['label']} r={top['r']:+.2f}(|r|≥{R_WEAK} 지표 {len(notable)}/{len(plots)}개). "
                       '상관이 있다고 원인으로 단정하기는 어려움.')

    text = f'화면에 제시한 상관분석 {len(plots)}개 지표 중 가장 큰 |r|은 {max_r:.3f}입니다.'
    if max_r < R_WEAK:
        text += ' 검토한 운영시간 지표만으로는 야드 체류 차이를 설명하기 어렵습니다.'
        if len(significant) == 1:
            s = significant[0]
            text += (f" 다중비교 보정 전 기준으로 유의한 지표는 {s['scope']}의 '{s['label']}'"
                     f"(r={s['r']:.3f}, {fmt_p(s['p'])}) 하나이고, 상관 자체는 약합니다.")
        elif significant:
            max_sig_r = max(abs(item['r']) for item in significant)
            text += (f' 다중비교 보정 전 기준으로 유의한 지표는 {len(significant)}개지만 '
                     f'모두 |r|이 {max_sig_r:.2f} 이하로 약합니다.')
    else:
        text += (f" 가장 큰 상관은 {top['scope']}의 '{top['label']}' 지표이고, "
                 f"r={top['r']:+.3f}({fmt_p(top['p'])}, n={top['n']:,})입니다."
                 f' |r|이 {R_WEAK} 이상인 지표는 {len(notable)}개이며, 상관이 곧 원인을 뜻하지는 않습니다.')
    return title, text


# ---- 3. 시뮬레이션의 체류시간 감소 -----------------------------------------
def simulation_card(simulation, scenarios, compact):
    base = simulation['baseline_mean_h_rounded']
    a, c = scenarios['A'], scenarios['C']
    cut = c['reduction_pct']
    after = base * (1 - cut / 100)

    if abs(cut) < REDUCTION_SMALL:
        title_short = '시뮬레이션에서 야드 체류 거의 변화 없음'
        title_full = '선별 일정 조정과 선석 공유의 체류 감소 효과는 거의 없음'
    elif cut < 0:
        title_short = f'시뮬레이션에서 야드 체류 {abs(cut):.2f}% 증가'
        title_full = '선별 일정 조정과 선석 공유 후 체류가 오히려 늘어남'
    else:
        title_short = f'시뮬레이션에서 야드 체류 {cut:.2f}% 감소'
        title_full = '선별 일정 조정과 선석 공유를 함께 검토'

    if compact:
        return title_short, f'일정 조정·선석 공유 적용 시 평균 {base:.1f}시간 → 약 {after:.1f}시간.'

    if abs(cut) < REDUCTION_SMALL and cut >= 0:
        text = f'{CONDITION}·전체 통합(C) 시뮬레이션에서 감소율이 {cut:.2f}%에 그쳐 체류시간은 거의 변하지 않았습니다.'
    elif abs(cut) < REDUCTION_SMALL:
        text = f'{CONDITION}·전체 통합(C) 시뮬레이션에서 체류가 {abs(cut):.2f}% 늘어 거의 변하지 않았습니다.'
    elif cut < 0:
        text = f'{CONDITION}·전체 통합(C) 시뮬레이션에서 체류가 오히려 {abs(cut):.2f}% 늘었습니다.'
    else:
        text = f'{CONDITION}·전체 통합(C) 시뮬레이션에서 체류가 {cut:.2f}% 줄었습니다.'
    text += f' 모형 기준 평균 {base:.1f} → 약 {after:.1f}시간입니다.'
    if cut >= REDUCTION_BIG:
        text += ' 감소 폭이 큰 편입니다.'
    elif REDUCTION_SMALL <= cut < REDUCTION_CLEAR:
        text += ' 감소 폭은 크지 않습니다.'

    gap = cut - a['reduction_pct']  # 전체 통합(C)과 기존 운영(A)의 감소율 차이
    if abs(gap) < SAME_GAP and a['reduction_pct'] >= REDUCTION_SMALL:
        text += f" 기존 운영(A)에서도 {a['reduction_pct']:.2f}% 줄어, 체류 감소는 주로 일정 조정 효과로 보입니다."
    elif gap >= SAME_GAP:
        text += f" 감소율은 기존 운영(A)보다 {gap:.2f}%p 더 높습니다."
    elif gap <= -SAME_GAP:
        text += f" 감소율은 기존 운영(A)의 {a['reduction_pct']:.2f}%보다 {abs(gap):.2f}%p 낮습니다."
    return title_full, text


# ---- 4. 선석 공유와 다른 선박의 지연 ---------------------------------------
def delay_card(scenarios, compact):
    a_h, c_h = scenarios['A']['other_delay_h'], scenarios['C']['other_delay_h']
    drop = (a_h - c_h) / a_h if a_h > 0 else 0.0  # 기존 운영 대비 줄어든 비율

    if a_h <= 0 and c_h <= 0:
        title = '다른 선박의 추가 접안 지연은 없음'
    elif a_h <= 0:
        title = '선석 공유 후 다른 선박에 추가 지연이 생김'
    elif drop >= DELAY_GONE:
        title = '선석 공유로 다른 선박의 지연이 거의 해소됨' if compact else '선석 공유는 다른 선박의 추가 지연을 거의 없앰'
    elif drop >= DELAY_REDUCED:
        title = '선석 공유로 다른 선박의 지연 감소' if compact else '선석 공유는 다른 선박의 추가 지연을 완화'
    elif drop > -DELAY_SAME:
        title = '선석 공유해도 다른 선박의 지연은 큰 차이 없음'
    else:
        title = '선석 공유 후 다른 선박의 지연이 늘어남'

    a_text, c_text = minutes(a_h), minutes(c_h)
    if compact:
        return title, f'같은 일정 조정 조건에서 추가 접안 지연 {a_text}(기존 운영) → {c_text}(전체 통합).'
    return title, (f'같은 {CONDITION} 조정에서 다른 선박 접안 지연은 A {a_text} → C {c_text}이었습니다. '
                   '실제 도입 성과가 아닌 모형 비교 결과입니다.')


def build_summaries(routes, reports, simulation, scenarios, *, compact=False):
    """홈 카드에 쓸 (제목, 설명) 네 개를 돌려준다."""
    return (
        yard_card(routes, compact),
        correlation_card(reports, compact),
        simulation_card(simulation, scenarios, compact),
        delay_card(scenarios, compact),
    )
