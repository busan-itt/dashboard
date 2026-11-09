# 개선안 파트 합치기 안내 (개선안 · 시뮬레이션 · 시뮬레이션 결과 · 개선안 결과)

목차·메뉴·app.py·전체 스타일은 포함하지 않았습니다. **목차 4개를 눌렀을 때 나오는 안쪽 내용**만 들어 있습니다.

## 목차 ↔ 함수 대응
| 목차 | 호출할 함수 | 화면 내용 |
|---|---|---|
| 개선안 | `improvement_views.introduction()` | 가정 → 현황 수치 → 비교할 세 운영 방식(A·B·C), 제안서 원본 다운로드 |
| 시뮬레이션 | `improvement_views.methodology()` | 검증 순서, 전체/선별 조정, 시뮬레이션 조건, 1~6차 기록(접힘) |
| 시뮬레이션 결과 | `improvement_views.simulation()` | 전체/선별 + 시간 슬라이더, KPI 4개(체류·감소율·접안 지연·일정 조정 실현율), 비교 그래프, "모든 결과 보기" 버튼 |
| 개선안 결과 | `improvement_views.project_conclusion()` | 대표 조건 KPI, 가장 큰 체류 감소 결과, 향후 보완 과제, 최종 개선안 |

## 합치는 방법 (3단계)
1. 이 폴더의 `improvement_views.py`, `data/`, `assets/`를 팀 `app.py`와 **같은 위치**에 복사합니다. (같은 이름 파일이 있으면 먼저 백업)
2. 팀 코드에서 `import improvement_views`
3. 각 목차의 페이지 함수 안에서 위 표의 함수를 한 줄씩 호출합니다.
```python
def page_improvement():      # 개선안 목차
    improvement_views.introduction()
def page_simulation():       # 시뮬레이션 목차
    improvement_views.methodology()
def page_result():           # 시뮬레이션 결과 목차
    improvement_views.simulation()
def page_conclusion():       # 개선안 결과 목차
    improvement_views.project_conclusion()
```
기존 페이지 안의 제목(`st.title` 등)은 팀 방식대로 두면 됩니다. 각 함수는 자체 제목 패널을 그립니다.

## 필요 환경
- Streamlit 1.64 이상, pandas
- 스타일은 `.pv` 클래스 안에서만 적용되어 팀 `styles.css`와 충돌하지 않습니다.

## 위젯·세션 key (팀 코드와 겹치지 않게 확인)
`result_policy`, `result_hours`, `show_all_results`, `show_all_results_button`, `method_scenario`, `method_terminal`

## 데이터를 바꿀 때
- 수치는 모두 `data/simulation_results.json`에서 읽습니다. 앞당김 시간(예: 168시간)이나 조건 수가 늘어난 JSON으로 교체하면 슬라이더·표·"N개 조건" 문구가 자동으로 따라갑니다.
- 단, 전체 정책의 실현율은 코드 상단 `ROUNDED_REAL`(24·48·96시간)에만 있어 다른 시간은 "—"로 표시됩니다.
- 현재 수치 전체는 `수치표.md`에 있습니다.

## 확인이 필요한 점
- 로컬(ChatGPT로 수정 중이던) 168시간·42개 조건 버전은 제가 받지 못해 이 JSON(18개 조건)으로 만들었습니다.
- "개선안 결과"의 향후 보완 과제 문구 4개는 보내주신 사진을 옮겨 적은 것이라 원문과 대조해 주세요.
- 대시보드의 DGT→HJNC 평균 체류(216.6시간)와 제안서의 값(282.81시간)이 서로 다릅니다. 발표 전 팀 확인이 필요합니다.
- 실제 Streamlit으로는 실행하지 못했고, Streamlit 호출을 기록하는 대역으로 수치·문구를 검증했습니다.
