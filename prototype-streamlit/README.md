# Port Analytics Streamlit

부산 신항 환적 체류시간 분석과 개선안·시뮬레이션 결과를 함께 보여주는 앱입니다. 메인 실행 파일은 **`app_revised.py`**입니다. `app_prototype.py`는 이전 시안으로 남겨 둡니다.

## 실행

이 `prototype-streamlit` 폴더만 복사해도 실행할 수 있습니다. Python 환경에서 다음 명령을 실행합니다.

```powershell
cd prototype-streamlit
python -m pip install -r requirements.txt
python -m streamlit run app_revised.py
```

저장소 루트에서 실행할 수도 있습니다.

```powershell
python -m streamlit run prototype-streamlit/app_revised.py
```

Streamlit 버전은 `requirements.txt`의 1.66.1을 사용합니다. 앱은 CSS·이미지·데이터 경로를 각 Python 파일의 위치 기준으로 찾습니다.

## 폴더 구성

```text
prototype-streamlit/
├─ app_revised.py              # 메인, 메뉴와 페이지 연결
├─ app_prototype.py            # 이전 시안
├─ requirements.txt
├─ *.css                       # 공통·페이지별 스타일
├─ assets/                     # 현황·상관관계 분석 및 초기 기획 자료
├─ improvement_content/
│  ├─ __init__.py
│  ├─ views.py                 # 개선안·시뮬레이션 화면
│  ├─ README.md                # 함수 대응, 데이터 관리 및 검토 사항
│  ├─ 수치표.md                # 저장된 18개 조건의 수치
│  ├─ data/                   # JSON, 다운로드용 제안서 원본
│  └─ assets/                 # 개선안 SVG
└─ output/                     # 기존 분석 산출물·생성 스크립트
```

## 화면과 데이터

화면 기본 색은 네이비 `#192C3A`와 흰색 `#FFFFFF`입니다. 메뉴·제목·버튼은 네이비, 배경·카드는 흰색으로 구성합니다. 그래프에는 코랄 `#F4A78D`, 슬레이트 `#526D82`, 미스트 `#CCD9DF`를 비교·강조 색으로 사용합니다. 프로젝트 소개의 현황 분석 그래프도 같은 팔레트로 다시 그렸으며, 공정별 평균 소요시간은 야드 체류(일)와 나머지 공정(분)을 분리한 가로 막대로 표시합니다. 다른 분석 페이지의 기존 이미지 색상은 원본을 유지합니다.

- 개선안(`/improvement`): 첨부 발표 자료의 선석 공유 제안을 표시합니다.
- 시뮬레이션(`/intro-solution`): 검증 과정과 조건을 표시합니다.
- 시뮬레이션 결과(`/simulation`): 전체·선별 정책과 24·48·96시간의 저장된 결과를 비교합니다. 화면에서 모델을 다시 실행하지 않습니다.
- 개선안 결과(`/improvement-results`): 대표 KPI, 42개 조건 중 최대 체류 감소 결과, 보완 과제를 표시합니다.
- 현황·상관관계 페이지는 포함된 팀 분석 자료를 표시합니다. 기존 대시보드의 운영 지표는 UI 동작 확인용 샘플입니다. AI 요약 등 일부 페이지에는 자리 표시 문안이 남아 있습니다.

개선안 자료의 상세 설명은 [improvement_content/README.md](improvement_content/README.md), 전체 수치는 [수치표](improvement_content/수치표.md)를 참고하세요.

## 통합 원칙

`improvement-part`의 기능은 `from improvement_content import views as improvement_views`로 연결되어 있습니다. 기존 `improvement_content` 파일을 우선 유지했으며, 특히 `data/observed_routes.json`은 통합본을 그대로 사용합니다. 별도 `improvement-part` 폴더는 실행에 필요하지 않아 제거할 수 있습니다.
