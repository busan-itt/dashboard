# dashboard

부산 신항 환적 체류시간 대시보드. 실행에 필요한 코드·데이터·이미지·설명은 **`prototype-streamlit/`**에 모여 있습니다.

```powershell
python -m pip install -r prototype-streamlit/requirements.txt
python -m streamlit run prototype-streamlit/app_revised.py
```

실행 방법과 화면 구성은 [앱 README](prototype-streamlit/README.md), 개선안의 데이터·함수 설명은 [개선안 README](prototype-streamlit/improvement_content/README.md)를 참고하세요.

`improvement-part/`는 통합 전 원본입니다. 코드·데이터·이미지는 이미 통합되어 있고, 수치표와 유용한 설명도 앱 폴더로 옮겼으므로 제거해도 앱이 동작합니다. 중복 파일은 기존 통합본을 우선 유지했으며 `observed_routes.json`도 `prototype-streamlit/improvement_content/data/` 버전을 사용합니다.
