"""분석 결과가 바뀐 뒤 AI 요약을 다시 만드는 스크립트 (앱 밖에서 직접 실행).

사용법 (prototype-streamlit 폴더에서):
    pip install -r requirements-dev.txt
    export ANTHROPIC_API_KEY=...            # Windows PowerShell: $env:ANTHROPIC_API_KEY="..."
    python generate_summary.py              # 요약 생성 -> assets/ai-summary/summary.json
    python generate_summary.py --dry-run    # API 호출 없이 사실 목록과 프롬프트만 출력

생성한 summary.json을 커밋하면 앱이 그 요약을 보여줍니다.
데이터(JSON)를 고친 뒤 이 스크립트를 다시 실행하지 않으면, 앱은 오래된 요약 대신
기존 템플릿 문장을 보여줍니다(summary_facts.facts_hash 비교).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

from overview import snapshot
from summary_facts import SUMMARY_PATH, build_facts, facts_hash

# 사용할 모델 (환경변수 SUMMARY_MODEL로 바꿀 수 있음)
MODEL = os.environ.get('SUMMARY_MODEL', 'claude-sonnet-5-5')
MAX_ATTEMPTS = 3

# 모델이 따라야 할 고정 규칙. 숫자 고정, 모형 결과 단서, 출력 형식을 못 박는다.
SYSTEM_PROMPT = """당신은 항만 물류 데이터 분석 대시보드의 요약 문장을 쓰는 편집자입니다.
아래 '사실 목록' JSON만 근거로 한국어 요약을 작성하세요.

규칙:
1. 숫자는 사실 목록에 있는 값만 그대로 쓰세요. 계산하거나 새 숫자를 만들거나 반올림을 바꾸지 마세요.
2. 시뮬레이션 결과는 모형 비교 결과이며 실제 도입 성과가 아닙니다. 시뮬레이션을 말하는 문장에는 이 점이 드러나야 합니다.
3. 상관계수가 작으면 '선형 관계가 약하다'까지만 말하고, 원인이나 인과를 단정하지 마세요.
4. 야드 체류 비중은 공정별 평균시간 합계 기준이며 정상적인 연결선 대기를 포함합니다.
5. '입증', '보장', '확실', '반드시' 같은 단정 표현을 쓰지 마세요.
6. 제목은 30자 이내, 설명은 한 문장(compact는 80자 이내, full은 140자 이내)으로 쓰세요.

출력은 아래 형태의 JSON 하나만 내세요. 코드 블록이나 다른 설명은 붙이지 마세요.
{"compact": [{"title": "...", "description": "..."}, ... 4개],
 "full":    [{"title": "...", "description": "..."}, ... 4개]}
네 항목의 주제 순서는 (1) 야드 체류 집중 (2) 운영시간과의 상관 (3) 시뮬레이션 감소 효과 (4) 선석 공유와 다른 선박 지연 입니다."""

NUMBER_RE = re.compile(r'\d+(?:\.\d+)?')  # 문장 속 숫자를 찾는 정규식
BANNED = ('입증', '보장', '확실', '반드시')  # 단정 표현 목록


def allowed_numbers(facts) -> set[str]:
    """사실 목록에 들어 있는 모든 숫자를 0~3자리 소수 표기로 펼쳐 '허용 숫자' 집합을 만든다."""
    allowed: set[str] = set()

    def walk(value):
        if isinstance(value, dict):
            for v in value.values():
                walk(v)
        elif isinstance(value, (list, tuple)):
            for v in value:
                walk(v)
        elif isinstance(value, (int, float)) and not isinstance(value, bool):
            for digits in range(4):
                allowed.add(f'{value:.{digits}f}')
            allowed.add(str(value))

    walk(facts)
    return allowed


def validate(result, facts) -> list[str]:
    """모델 응답을 검사해 문제 목록을 돌려준다. 빈 목록이면 통과."""
    problems: list[str] = []
    allowed = allowed_numbers(facts)
    limits = {'compact': 80, 'full': 140}  # 설명 길이 상한
    for kind, max_len in limits.items():
        items = result.get(kind)
        # 항목이 정확히 4개이고 제목·설명이 문자열인지 확인
        if not isinstance(items, list) or len(items) != 4:
            problems.append(f'{kind}: 항목이 4개가 아님')
            continue
        for i, item in enumerate(items, 1):
            title, desc = item.get('title'), item.get('description')
            if not isinstance(title, str) or not isinstance(desc, str):
                problems.append(f'{kind}[{i}]: title/description 형식 오류')
                continue
            if len(title) > 30 or len(desc) > max_len:
                problems.append(f'{kind}[{i}]: 길이 초과')
            # 사실 목록에 없는 숫자가 나오면 지어낸 숫자로 보고 거부
            for number in NUMBER_RE.findall(title + ' ' + desc):
                if number not in allowed:
                    problems.append(f'{kind}[{i}]: 허용되지 않은 숫자 {number}')
            if any(word in title + desc for word in BANNED):
                problems.append(f'{kind}[{i}]: 단정 표현 사용')
    # 시뮬레이션을 다루는 3·4번째 항목 중 하나에는 '실제 도입 성과' 단서가 반드시 있어야 함
    for kind in limits:
        items = result.get(kind) or []
        if len(items) == 4 and not any('실제 도입 성과' in (it.get('description') or '') for it in items[2:]):
            problems.append(f'{kind}: 모형 결과 단서("실제 도입 성과") 누락')
    return problems


def call_model(facts, feedback: list[str] | None = None) -> dict:
    """Claude API를 호출해 요약 JSON을 받아 파싱한다."""
    import anthropic  # 생성 스크립트에서만 필요하므로 여기서 가져옴 (앱 배포에는 불필요)

    client = anthropic.Anthropic()  # ANTHROPIC_API_KEY 환경변수를 자동으로 사용
    user_text = '사실 목록:\n' + json.dumps(facts, ensure_ascii=False, indent=2)
    if feedback:
        # 이전 시도에서 검증에 실패한 이유를 알려주고 다시 쓰게 한다
        user_text += '\n\n이전 응답이 아래 이유로 거부되었습니다. 고쳐서 다시 작성하세요:\n- ' + '\n- '.join(feedback)
    response = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=SYSTEM_PROMPT,
        messages=[{'role': 'user', 'content': user_text}],
    )
    text = ''.join(block.text for block in response.content if block.type == 'text').strip()
    text = re.sub(r'^```(?:json)?|```$', '', text, flags=re.MULTILINE).strip()  # 혹시 붙은 코드 블록 제거
    return json.loads(text)


def main() -> int:
    parser = argparse.ArgumentParser(description='AI 요약 생성')
    parser.add_argument('--dry-run', action='store_true', help='API 호출 없이 입력만 출력')
    args = parser.parse_args()

    # 앱과 똑같은 데이터 읽기 함수로 현재 사실 목록을 만든다
    facts = build_facts(*snapshot())
    if args.dry_run:
        print(json.dumps(facts, ensure_ascii=False, indent=2))
        print('facts_hash =', facts_hash(facts))
        return 0

    feedback: list[str] | None = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            result = call_model(facts, feedback)
        except ValueError as exc:  # JSON 파싱 실패
            feedback = [f'JSON 형식 오류: {exc}']
            print(f'[{attempt}/{MAX_ATTEMPTS}] {feedback[0]}')
            continue
        problems = validate(result, facts)
        if not problems:
            break
        feedback = problems
        print(f'[{attempt}/{MAX_ATTEMPTS}] 검증 실패:', *problems, sep='\n  - ')
    else:
        # 세 번 모두 실패하면 파일을 쓰지 않는다 -> 앱은 템플릿 문장을 계속 보여줌
        print('검증을 통과한 요약을 얻지 못해 summary.json을 갱신하지 않았습니다.')
        return 1

    # 어떤 데이터·모델로 만들었는지 함께 기록해서 저장
    payload = {
        'facts_hash': facts_hash(facts),
        'model': MODEL,
        'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'compact': result['compact'],
        'full': result['full'],
    }
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print('저장 완료:', SUMMARY_PATH)
    return 0


if __name__ == '__main__':
    sys.exit(main())
