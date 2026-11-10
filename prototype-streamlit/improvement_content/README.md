# 개선안·시뮬레이션 통합 모듈

## 현재 화면: 첨부 발표 자료 반영

`port-analytics-improvement.zip`의 개선안 관련 내용만 반영했습니다. ZIP의 전체 앱·홈·분석·공통 스타일은 가져오지 않았습니다. 현재 `views.py`는 `assets/presentation.html`의 네 영역과 `presentation.css`를 사용하며, 화면은 네이비·화이트을 기본으로 하고 그래프에는 밝은 블루와 중간 톤 블루를 사용합니다.

| 실제 페이지 | 화면 영역 |
|---|---|
| 개선안 `/improvement` | `render_section("s1")` |
| 시뮬레이션 `/intro-solution` | `render_section("s2")` |
| 시뮬레이션 결과 `/simulation` | `render_section("s3")`, 정책·시간에 따른 동적 KPI·막대그래프 |
| 개선안 결과 `/improvement-results` | `render_section("s4")` |

`data/simulation_all_results.json`은 첨부본의 42개 저장 조건을 그대로 보관합니다. 결과 비교에서는 실현율까지 비교 가능한 24·48·96시간의 18개 조건을 표시하며, 결론은 첨부 HTML에 정리된 168시간의 최대 감소 결과도 보여줍니다. 정적인 HTML 결론과 JSON은 자료 갱신 시 함께 확인해야 합니다. 세션 키는 `live_policy`, `live_hours`입니다.

기존 `observed_routes.json`과 나머지 JSON·제안서·SVG는 변경하지 않았습니다. [수치표.md](수치표.md)는 기존 `simulation_results.json`의 18개 조건 참고표입니다. 이전 화면의 전체 결과 버튼·CSV·제안서 다운로드는 이번 첨부 발표 화면에 포함되어 있지 않습니다.

## 자료 관리

화면은 `from improvement_content import views as improvement_views`로 연결합니다. JSON·HTML·CSS 경로는 `views.py` 위치를 기준으로 찾으므로 `prototype-streamlit` 폴더만으로 실행할 수 있습니다.

전체 정책의 실현율은 첨부 코드의 정수 반올림 보정값(24·48·96시간)을 사용합니다. 최대 감소 조건인 168시간은 실현율 자료가 없어 결론에 해당 값을 표시하지 않습니다. 평균 체류는 반올림된 기준 227.2시간으로 계산한 근사치입니다.

시뮬레이션 결과는 저장된 출력이며 실제 모델을 다시 실행하지 않습니다. 정적인 발표 자료와 데이터의 수치·조건·출처를 함께 검토한 뒤 갱신하세요.
