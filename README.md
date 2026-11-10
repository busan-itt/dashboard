# Port Insights

**Team: Bnct** · 부산신항의 환적 체류시간 분석과 선석통합운영 개선안을 보여주는 Streamlit 대시보드입니다.

## 프로젝트 소개

DGT·HJNC의 자부두 환적과 양방향 타부두 환적을 비교하고, 연결선 일정 조정과 터미널 간 선석 공유가 야드 체류시간과 다른 선박의 추가 접안 지연에 미치는 영향을 살펴봅니다.

| 화면 | 주요 내용 |
| --- | --- |
| 대시보드 | 네 환적 경로의 평균·중앙값, 야드 체류 비중, 대표 시뮬레이션 |
| 프로젝트 소개 | 문제제기, 전체 소요시간과 공정별 현황 분석 |
| 분석 내용 | 경로별 선박 운영시간과 야드 체류시간의 상관분석 |
| 개선안 | A·B·C 운영 방식의 선석 공유 지도와 검증 과정 |
| 시뮬레이션 결과 | 선별·전체 조정과 24·48·96시간 조건 비교 |
| 첨부 | 입력자료 설명, 집계 JSON 다운로드, 초기 기획 자료 |

## 실행

Python이 설치된 환경에서 저장소를 내려받고 앱 폴더로 이동합니다.

```powershell
git clone https://github.com/busan-itt/dashboard.git
cd dashboard/prototype-streamlit
python -m pip install -r requirements.txt
python -m streamlit run app_revised.py
```

실행 후 터미널에 표시된 로컬 주소를 브라우저에서 엽니다. 기본 주소는 `http://localhost:8501`입니다.

앱 폴더에서 실행해야 `.streamlit/config.toml`의 테마 설정이 적용됩니다. 실행 패키지는 Streamlit 1.66.1, pandas 2 이상·4 미만, Altair 6 이상·7 미만입니다.

## 폴더 구성

```text
prototype-streamlit/
├─ app_revised.py          # 실행 파일, 메뉴와 프로젝트 소개
├─ overview.py            # 홈 요약과 대시보드
├─ current_state.py       # 현황 분석
├─ correlation_views.py   # 상관분석
├─ attachments_views.py   # 자료 설명과 JSON 다운로드
├─ *.css                  # 화면 스타일
├─ .streamlit/config.toml # 테마
├─ requirements.txt       # 실행 패키지
├─ assets/
│  ├─ intro-analysis-flow*.svg    # 분석 흐름도
│  ├─ initial-plan/              # 화면에서 제공하는 초기 기획 자료
│  ├─ preliminary-analysis/      # 현황 집계와 공정별 평균시간
│  └─ correlation-analysis/unified/ # 상관분석 결과와 사용 중인 그래프
└─ improvement_content/
   ├─ __init__.py
   ├─ views.py            # 개선안과 검증 과정, 결론
   ├─ sharing_map.py      # 운영 방식별 선석 공유 지도
   ├─ results_view.py     # 시뮬레이션 조건 비교
   ├─ presentation.css
   ├─ assets/            # 발표 내용과 일정 비교 그림
   └─ data/              # 선석 공유 관계와 시뮬레이션 저장 결과
```

## 데이터와 기능

아래 경로는 `prototype-streamlit/` 기준입니다.

- 홈·대시보드·현황 분석은 `assets/preliminary-analysis/figure-data.json`과 `stage-durations.json`을 사용합니다.
- 상관분석은 `assets/correlation-analysis/unified/reports.json`에 연결된 그래프를 표시합니다.
- 개선안은 `improvement_content/data/berth-sharing-map.json`으로 운영 방식 A·B·C의 공유 범위를 보여줍니다.
- 시뮬레이션은 `improvement_content/data/simulation_all_results.json`의 저장된 42개 조건을 사용합니다. 결과 화면에서는 24·48·96시간의 18개 조건을 비교하며, 168시간 결과는 개선안 결과의 상세 항목에서 확인합니다.
- 사용한 데이터 페이지에서 현황·상관분석·시뮬레이션 JSON을 다운로드할 수 있습니다.

화면에서 원자료를 다시 분석하거나 시뮬레이션 모델을 실행하지 않습니다. 현황의 경로별 통계와 시뮬레이션 기준 평균 227.2시간은 서로 다른 집계이며, 모형 결과는 실제 도입 성과와 구분합니다. 자료의 원본 링크와 분석 기준은 앱의 각 화면에 표시합니다.

### 시뮬레이션 운영 방식

| 구분 | 선석 이용 범위 |
| --- | --- |
| A · 기존 운영 | 자기 터미널 |
| B · 인접 공유 | 자기 터미널과 모형에 지정된 인접 터미널 |
| C · 전체 통합 | 부산신항 7개 터미널 |

B의 인접 관계는 `berth-sharing-map.json`에 정의되어 있으며, 인접 터미널의 이웃까지 자동으로 확대하지 않습니다.

## 저장소 관리

이 저장소에는 현재 앱 실행에 필요한 파일과 이 안내만 남겨 두었습니다. 이전 시안, 미사용 그래프·제안서·노트북, 그래프 생성 도구와 중복 산출물은 Git 기록에서 확인할 수 있습니다.
