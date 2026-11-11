"""AI 요약 생성의 공용 코드: 프롬프트, Claude 호출, 결과 검증.

앱(summary_live.py)과 수동 생성 스크립트(generate_summary.py)가 함께 사용합니다.
streamlit에는 의존하지 않습니다. anthropic 패키지는 호출 시점에만 불러옵니다.
"""
from __future__ import annotations

import json
import re

DEFAULT_MODEL = 'claude-sonnet-5-5'

# 모델이 따라야 할 고정 규칙: 근거 제한, 숫자 고정, 모형 결과 단서, 출력 형식
SYSTEM_PROMPT = """당신은 항만 물류 데이터 분석 대시보드의 '분석 핵심 요약'을 쓰는 편집자입니다.
아래 '사실 목록' JSON(현황, 상관분석, 시뮬레이션 전 조건, 검증 결과 포함)을 읽고, 지금 데이터가 말하는 핵심 4가지를 한국어로 요약하세요.

규칙:
1. 근거는 사실 목록뿐입니다. 숫자는 사실 목록에 있는 값만 그대로 쓰고, 계산하거나 새 숫자를 만들거나 반올림을 바꾸지 마세요.
2. 데이터가 말하는 방향을 그대로 쓰세요. 이전 요약이나 흔한 기대에 맞추지 말고, 값이 바뀌었으면 결론도 바뀐 대로 쓰세요.
3. 시뮬레이션 결과는 모형 비교 결과이며 실제 도입 성과가 아닙니다. 시뮬레이션을 말하는 문장에는 이 점이 드러나야 합니다.
4. 상관계수가 작으면 '선형 관계가 약하다'까지만 말하고 인과를 단정하지 마세요. 일부 지표가 통계적으로 유의했다면 그 한계도 반영하세요.
5. 야드 체류 비중은 공정별 평균시간 합계 기준이며 정상적인 연결선 대기를 포함합니다.
6. '입증', '보장', '확실', '반드시' 같은 단정 표현을 쓰지 마세요.
7. 시뮬레이션은 simulation_condition에 적힌 대표 조건을 기준으로 쓰세요.
8. 제목은 30자 이내, 설명은 한 문장(compact는 80자 이내, full은 140자 이내)으로 쓰세요.

출력은 아래 형태의 JSON 하나만 내세요. 코드 블록이나 다른 설명은 붙이지 마세요.
{"compact": [{"title": "...", "description": "..."}, ... 4개],
 "full":    [{"title": "...", "description": "..."}, ... 4개]}
네 항목의 주제 순서는 (1) 환적 시간의 구성(야드 체류) (2) 선박 운영시간과의 상관 (3) 시뮬레이션의 체류시간 감소 효과 (4) 선석 공유와 다른 선박 지연 입니다."""

NUMBER_RE = re.compile(r'\d+(?:\.\d+)?')  # 문장 속 숫자를 찾는 정규식
BANNED = ('입증', '보장', '확실', '반드시')  # 단정 표현
LIMITS = {'compact': 80, 'full': 140}  # 종류별 설명 길이 상한


class SummaryError(Exception):
    """요약 생성이 끝내 실패했을 때 발생."""


def allowed_numbers(facts) -> set[str]:
    """사실 목록(숫자와 텍스트 속 숫자)에 나온 모든 숫자를 '허용 숫자' 집합으로 만든다."""
    allowed: set[str] = set()

    def walk(value):
        if isinstance(value, dict):
            for v in value.values():
                walk(v)
        elif isinstance(value, (list, tuple)):
            for v in value:
                walk(v)
        elif isinstance(value, str):
            allowed.update(NUMBER_RE.findall(value))  # 노트북 출력 같은 텍스트 속 숫자
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            for digits in range(4):
                allowed.add(f'{value:.{digits}f}')  # 0~3자리 소수 표기
            allowed.add(str(value))

    walk(facts)
    return allowed


def validate(result, facts) -> list[str]:
    """모델 응답을 검사해 문제 목록을 돌려준다. 빈 목록이면 통과."""
    problems: list[str] = []
    if not isinstance(result, dict):
        return ['응답이 JSON 객체가 아님']
    allowed = allowed_numbers(facts)
    for kind, max_len in LIMITS.items():
        items = result.get(kind)
        if not isinstance(items, list) or len(items) != 4:
            problems.append(f'{kind}: 항목이 4개가 아님')
            continue
        for i, item in enumerate(items, 1):
            title = item.get('title') if isinstance(item, dict) else None
            desc = item.get('description') if isinstance(item, dict) else None
            if not isinstance(title, str) or not isinstance(desc, str):
                problems.append(f'{kind}[{i}]: title/description 형식 오류')
                continue
            if len(title) > 30 or len(desc) > max_len:
                problems.append(f'{kind}[{i}]: 길이 초과')
            # 사실 목록에 없는 숫자는 지어낸 숫자로 보고 거부
            for number in NUMBER_RE.findall(title + ' ' + desc):
                if number not in allowed:
                    problems.append(f'{kind}[{i}]: 허용되지 않은 숫자 {number}')
            if any(word in title + desc for word in BANNED):
                problems.append(f'{kind}[{i}]: 단정 표현 사용')
        # 시뮬레이션 항목(3·4번째) 중 하나에는 '실제 도입 성과' 단서가 있어야 함
        if len(items) == 4 and not any(
                isinstance(it, dict) and '실제 도입 성과' in (it.get('description') or '') for it in items[2:]):
            problems.append(f'{kind}: 모형 결과 단서("실제 도입 성과") 누락')
    return problems


def call_model(facts, *, api_key: str, model: str = DEFAULT_MODEL,
               feedback: list[str] | None = None, timeout: float = 45.0) -> dict:
    """Claude API를 한 번 호출해 요약 JSON을 받아 파싱한다."""
    import anthropic  # 필요할 때만 불러옴

    client = anthropic.Anthropic(api_key=api_key, timeout=timeout, max_retries=1)
    user_text = '사실 목록:\n' + json.dumps(facts, ensure_ascii=False)
    if feedback:
        # 이전 시도가 거부된 이유를 알려주고 고쳐 쓰게 한다
        user_text += '\n\n이전 응답이 아래 이유로 거부되었습니다. 고쳐서 다시 작성하세요:\n- ' + '\n- '.join(feedback)
    response = client.messages.create(
        model=model, max_tokens=1800, system=SYSTEM_PROMPT,
        messages=[{'role': 'user', 'content': user_text}],
    )
    text = ''.join(block.text for block in response.content if block.type == 'text').strip()
    text = re.sub(r'^```(?:json)?|```$', '', text, flags=re.MULTILINE).strip()  # 혹시 붙은 코드 블록 제거
    return json.loads(text)


def generate(facts, *, api_key: str, model: str = DEFAULT_MODEL, max_attempts: int = 3, log=print) -> dict:
    """호출→검증을 최대 max_attempts번 반복해 검증을 통과한 요약을 돌려준다. 실패하면 SummaryError."""
    feedback: list[str] | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            result = call_model(facts, api_key=api_key, model=model, feedback=feedback)
        except ValueError as exc:  # JSON 파싱 실패
            feedback = [f'JSON 형식 오류: {exc}']
            log(f'[{attempt}/{max_attempts}] {feedback[0]}')
            continue
        problems = validate(result, facts)
        if not problems:
            return {'compact': result['compact'], 'full': result['full']}
        feedback = problems
        log(f'[{attempt}/{max_attempts}] 검증 실패: ' + '; '.join(problems))
    raise SummaryError('검증을 통과한 요약을 얻지 못했습니다: ' + '; '.join(feedback or []))
