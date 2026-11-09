# Port Analytics Streamlit 시안

HTML A안의 메뉴 구성을 Streamlit 페이지로 옮긴 로컬 시안입니다. 상위 메뉴는 홈, 대시보드, 프로젝트 소개, 개선안, 초기 기획, 참고·출처입니다. 홈·대시보드·프로젝트 소개의 하위 메뉴는 각각 독립된 URL의 페이지로 열립니다.

기존 대시보드의 필터·지표·차트는 `기존 대시보드 기능` 하위 페이지에 있습니다. 수치는 UI 동작 확인용 샘플이며 실제 터미널 데이터가 아닙니다. AI 분석 요약과 개선안 등 자료가 아직 없는 부분은 자리 표시 문안만 둡니다.

`app_prototype.py`가 실행 파일입니다. 저장소의 `my-dev-final/.venv` 환경을 사용할 경우 PowerShell에서:

```powershell
cd C:\mine\edu-team\team-final-project\dashboard-front\prototype-streamlit
& C:\mine\edu-team\team-final-project\my-dev-final\.venv\Scripts\python.exe -m streamlit run app.py
```

별도 환경에서는 `pip install -r requirements.txt` 후 `python -m streamlit run app.py`로 실행합니다. 좌측 메뉴는 Streamlit의 기본 사이드바를 사용하며, 접은 뒤에도 펼치기 버튼이 남습니다.
