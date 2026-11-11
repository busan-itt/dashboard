"""AI 요약을 직접 만들어 summary.json으로 저장하는 스크립트 (선택 사항).

앱은 ANTHROPIC_API_KEY가 설정돼 있으면 데이터가 바뀔 때 스스로 요약을 새로 만듭니다.
이 스크립트는 그와 별개로 요약을 미리 만들어 저장하고 싶을 때(키가 앱에 없을 때 등) 씁니다.

사용법 (prototype-streamlit 폴더에서):
    pip install -r requirements-dev.txt
    export ANTHROPIC_API_KEY=...            # PowerShell: $env:ANTHROPIC_API_KEY="..."
    python generate_summary.py              # 요약 생성 -> assets/ai-summary/summary.json
    python generate_summary.py --dry-run    # API 호출 없이 사실 목록만 출력
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone

from overview import snapshot
from summary_core import DEFAULT_MODEL, SummaryError, generate
from summary_facts import SUMMARY_PATH, build_facts, facts_hash


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

    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print('ANTHROPIC_API_KEY 환경변수가 필요합니다.')
        return 1
    model = os.environ.get('SUMMARY_MODEL', DEFAULT_MODEL)
    try:
        result = generate(facts, api_key=api_key, model=model)
    except SummaryError as exc:
        # 실패하면 파일을 쓰지 않는다 -> 앱은 템플릿 문장(또는 앱 내 생성)을 계속 사용
        print(exc)
        return 1

    # 어떤 데이터·모델로 만들었는지 함께 기록해서 저장
    payload = {
        'facts_hash': facts_hash(facts),
        'model': model,
        'generated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        **result,
    }
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print('저장 완료:', SUMMARY_PATH)
    return 0


if __name__ == '__main__':
    sys.exit(main())
