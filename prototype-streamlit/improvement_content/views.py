"""개선안·시뮬레이션·결과 화면. 저장된 최종 노트북 결과만 보여주며 모델은 다시 실행하지 않는다.

화면 구성: 패널 안에 번호 제목(kicker) → 결론 제목 → 카드 → 그래프 순서로 보여주고, 세부 내용은 expander에 접어 둔다.
카드·그래프는 st.html로 그린다.
"""
import json
import xml.etree.ElementTree as ET
from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

# 데이터 파일 경로 (이 파일과 같은 폴더의 data/)
DATA_FILE = Path(__file__).parent / "data" / "simulation_results.json"
# 시나리오 이름: 긴 이름은 지도·표에, 짧은 이름은 그래프 라벨에 쓴다
SCENARIOS = {"A": "A · 기존 터미널별 운영", "B": "B · 인접 터미널 공유", "C": "C · 신항 전체 통합"}
SHORT = {"A": "A 기존", "B": "B 인접 공유", "C": "C 전체 통합"}
# 글자 번호 없는 시나리오 이름 (카드 제목용)
NAME = {key: value.split(" · ")[1] for key, value in SCENARIOS.items()}
# 터미널별 인접 터미널 (B 시나리오에서 함께 검토하는 선석 범위)
NEIGHBORS = {
    "PNC": ["HJNC", "PNIT"], "HJNC": ["PNC", "DGT"],
    "DGT": ["HJNC", "BCT"], "BCT": ["DGT", "BNCT"],
    "BNCT": ["BCT", "HPNT"], "HPNT": ["BNCT", "PNIT"],
    "PNIT": ["PNC", "HPNT"],
}
# 전체 정책의 실현율은 원문에 정수 반올림 값만 있어 따로 보관한다 (없는 시간대는 표시하지 않는다)
ROUNDED_REAL = {24: dict(zip("ABC", [88, 100, 100])),
                48: dict(zip("ABC", [85, 100, 100])),
                96: dict(zip("ABC", [78, 98, 100]))}

# 패널·카드·그래프용 스타일. 코랄·네이비 팔레트을 쓰고 .pv 안에서만 적용한다
PV_CSS = """
.improvement-content-heading{padding-top:32px}
.pv{color:#0A0F1F}
.pv .panel{background:#F8F9FA;border-radius:14px;padding:40px clamp(20px,11%,110px) 34px}
.pv .kick{margin-bottom:6px;color:#1D3557;font-size:13px}
.pv h2{margin:0 0 6px;color:#0A0F1F;font-size:26px;line-height:1.4;font-weight:700}
.pv .sub{margin:0 0 22px;color:#526573;font-size:15px}
.pv .sec{margin:26px 0 10px;color:#0A0F1F;font-size:14px;font-weight:700}
.pv .grid{display:grid;gap:14px}
.pv .g2{grid-template-columns:repeat(2,minmax(0,1fr))}
.pv .g3{grid-template-columns:repeat(3,minmax(0,1fr))}
.pv .g4{grid-template-columns:repeat(4,minmax(0,1fr))}
.pv .card{background:#fff;border:1px solid #E2E5EA;border-radius:12px;padding:18px 20px}
.pv .card b{display:block;margin:2px 0 6px;color:#0A0F1F;font-size:16px}
.pv .cap{color:#526573;font-size:14px;line-height:1.55}
.pv .g4 .card{padding:16px 16px}
.pv .g4 .cap{font-size:13px}
.pv .num{margin:4px 0;color:#0A0F1F;font-size:34px;font-weight:700;line-height:1.2}
.pv .num small{margin-left:4px;color:#526573;font-size:15px;font-weight:400}
.pv .flow{display:flex;gap:10px;align-items:stretch;margin-bottom:6px}
.pv .step{flex:1;display:flex;align-items:center;justify-content:center;padding:16px;background:#FFF0ED;border-radius:10px;color:#0A0F1F;font-size:15px;font-weight:600;text-align:center}
.pv .arrow{align-self:center;color:#526573}
.pv .badge{display:inline-block;margin-bottom:6px;padding:2px 10px;border-radius:99px;background:#FFF0ED;color:#1D3557;font-size:13px;font-weight:600}
.pv .badge.off{background:#e9eef2;color:#526573}
.pv .mt{margin-bottom:12px;color:#0A0F1F;font-size:15px;font-weight:700}
.pv .brow{display:flex;align-items:center;gap:12px;margin:10px 0;font-size:14px}
.pv .bn{width:104px;color:#526573}
.pv .track{flex:1;height:16px;background:#F8F9FA;border-radius:4px;overflow:hidden}
.pv .bar{display:block;height:100%;background:#aab5bf;border-radius:4px}
.pv .bar.hi{background:#FF6F61}
.pv .bv{width:84px;text-align:right;color:#0A0F1F;font-weight:600}
.pv .take{margin-top:16px;padding:14px 18px;border-left:3px solid #FF6F61;background:#fff;font-size:15px;color:#0A0F1F}
.pv .foot{margin-top:12px;color:#526573;font-size:13px;line-height:1.6}
.pv ul.lim{margin:0;padding-left:20px;color:#3b4b58;font-size:15px;line-height:1.8}
.pv ul.lim b{display:inline;font-size:inherit}
.pv table{width:100%;border-collapse:collapse;font-size:14px}
.pv th{padding:10px 12px;border-bottom:2px solid #E2E5EA;color:#526573;font-weight:600;text-align:right}
.pv td{padding:9px 12px;border-bottom:1px solid #F8F9FA;text-align:right}
.pv th:nth-child(-n+3),.pv td:nth-child(-n+3){text-align:left}
.pv tr.sel td{background:#FFF0ED;color:#0A0F1F;font-weight:600}
@media(max-width:760px){.pv .g3,.pv .g4{grid-template-columns:repeat(2,minmax(0,1fr))}.pv .flow{flex-direction:column}.pv .arrow{transform:rotate(90deg)}}
"""


def pv_html(body):
    # 본문 HTML을 .pv 영역으로 감싸 st.html로 그린다
    st.html(f'<div class="pv">{body}</div>')


def pv_style():
    # 카드·그래프 스타일을 화면에 한 번 적용한다
    st.html(f"<style>{PV_CSS}</style>")


def panel(kicker, inner):
    # 번호 제목(kicker)과 본문을 하나의 둥근 패널로 감싼다
    return f'<div class="panel"><div class="kick">{escape(kicker)}</div>{inner}</div>'


def kpi(label, value, unit, *subs):
    # 숫자 카드 하나 (라벨, 큰 숫자, 단위, 보조 설명 여러 줄)
    lines = "".join(f'<div class="cap">{escape(s)}</div>' for s in subs if s)
    return (f'<div class="card"><div class="cap">{escape(label)}</div>'
            f'<div class="num">{escape(value)}<small>{escape(unit)}</small></div>{lines}</div>')


def bars(title, items, highlight=""):
    # A·B·C 막대 묶음. 가장 긴 막대가 트랙의 약 93%가 되도록 이 그래프의 최댓값 기준으로 길이를 정한다
    vmax = max(v for _, v, _ in items) * 1.075
    rows = ""
    for name, value, key in items:
        width = 0 if vmax <= 0 else min(100.0, max(1.0 if value > 0 else 0.0, value / vmax * 100))
        cls = "bar hi" if key == highlight else "bar"
        rows += (f'<div class="brow"><span class="bn">{escape(name)}</span>'
                 f'<span class="track"><span class="{cls}" style="width:{width:.1f}%"></span></span>'
                 f'<span class="bv">{value:.2f}{"분" if "지연" in title else "%"}</span></div>')
    return f'<div class="card"><div class="mt">{escape(title)}</div>{rows}</div>'


def scenario_map(scenario, terminal):
    """Illustrate model candidate terminals; this does not assign ships."""
    # 시나리오별 접안 후보 터미널 목록 (A: 자기 터미널, B: 자기+인접, C: 전체)
    candidates = ([terminal] if scenario == "A" else
                  [terminal, *NEIGHBORS[terminal]] if scenario == "B" else list(NEIGHBORS))
    uri = "http://www.w3.org/2000/svg"
    ET.register_namespace("", uri)
    ns = {"s": uri}
    # 배치도 SVG를 읽어 후보 터미널만 색을 바꾼다
    svg = ET.fromstring((Path(__file__).parent / "assets" / "berth-operation.svg").read_text(encoding="utf-8"))
    for group in svg.findall(".//s:g", ns):
        labels = group.findall("s:text", ns)
        name = next((t.text for t in labels if t.text in NEIGHBORS), None)
        if name is None:
            continue
        panel_rect = group.find("s:rect", ns)
        panel_rect.set("fill", "#1D3557" if name == terminal else "#FFA69E" if name in candidates else "#f3f5f6")
        for label in labels:
            label.set("fill", "#ffffff" if name == terminal else "#0A0F1F" if name in candidates else "#8698a3")
    # 배치도 안의 안내 문구를 선택한 시나리오에 맞게 바꾼다
    for text in svg.findall(".//s:text", ns):
        if text.text == "부산 신항 · 현재 선석 운영":
            text.text = SCENARIOS[scenario]
        elif text.text == "7개 터미널 독립 배정":
            text.text = f"기준 터미널 · {terminal}"
        elif text.text == "제공 지도 기반 개념도 · 터미널 위치 관계 단순화":
            text.text = "진한 파랑: 기준 터미널 · 연한 파랑: 추가 접안 후보 · 회색: 공유 범위 밖"
    return ET.tostring(svg, encoding="unicode"), candidates


def load_results():
    # 저장된 결과 JSON을 읽어 원본 dict와 DataFrame으로 돌려준다
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return data, pd.DataFrame(data["rows"])


def pick_row(df, policy, hours, scenario):
    # 정책·앞당김 시간·시나리오 조건에 맞는 결과 한 행을 고른다
    return df[(df.policy == policy) & (df.hours == hours) & (df.scenario == scenario)].iloc[0]


def realization(row, hours):
    # 선별 정책은 저장된 정밀값, 전체 정책은 원문의 정수 반올림 값을 쓴다 (없으면 None)
    if pd.notna(row.realization_pct):
        return float(row.realization_pct)
    value = ROUNDED_REAL.get(int(hours), {}).get(row.scenario)
    return None if value is None else float(value)


def pct(value):
    # 값이 없으면 줄표, 있으면 소수 첫째 자리까지 표시한다
    return "—" if value is None else f"{value:.1f}"


def ci_text(row):
    # 시나리오 A의 95% 구간 문구 (값이 없으면 안내 문구)
    if pd.isna(row.ci_lower_pct) or pd.isna(row.ci_upper_pct):
        return "값 없음"
    return f"{row.ci_lower_pct:.2f}~{row.ci_upper_pct:.2f}%"


def source_note(data):
    # 결과 근거(조건, 확인 날짜, 저장소 링크)를 화면 아래에 한 번 표시한다
    st.caption("2025년 자료 기반 · 반복 100회 · 최소 연결 간격 24시간 · GitHub 확인 2026.11.09")
    st.markdown(f"[최종 노트북과 결과 근거]({data['source_url']}) · "
                "[분석 저장소](https://github.com/busan-itt/analysis) · "
                "[데이터 저장소](https://github.com/busan-itt/data)")


def introduction():
    """개선안 화면: 가정 → 현황 수치 → 비교할 세 운영 방식. 세부 제안서 내용은 접어 둔다."""
    # 제안서 본문(JSON)과 경로별 체류 집계를 읽는다
    proposal_file = Path(__file__).parent / "data" / "proposal.json"
    proposal = json.loads(proposal_file.read_text(encoding="utf-8"))
    sections = proposal["sections"]
    routes = json.loads((Path(__file__).parent / "data" / "observed_routes.json").read_text(encoding="utf-8"))
    assets = Path(__file__).parent / "assets"

    pv_style()
    # 경로별 평균 체류 카드 4개 (집계 파일의 값을 그대로 쓴다)
    route_cards = "".join(
        kpi(r["route"].replace("ODT", "자부두").replace("ITT", "타부두"),
            f"{r['yard_mean_sum_h']:.1f}", "시간", f"{r['stage_n']:,}건")
        for r in routes)
    # 비교하는 세 가지 운영 방식 카드
    scenario_cards = "".join(
        f'<div class="card"><b>{escape(SCENARIOS[key])}</b><div class="cap">{escape(text)}</div></div>'
        for key, text in zip("ABC", ["자기 터미널 선석만 사용",
                                     "인접 터미널 선석까지 함께 사용",
                                     "7개 터미널 선석을 모두 사용"]))
    pv_html(panel("1 · 개선안", f"""
<h2>선석을 함께 쓰면 환적 컨테이너의 야드 체류가 줄어드는지 검증한다</h2>
<p class="sub">신항 7개 터미널(PNC, PNIT, HPNT, HJNC, BNCT, BCT, DGT)이 선석을 따로 운영합니다.</p>
<div class="flow"><div class="step">선석 공동 활용</div><span class="arrow">→</span>
<div class="step">선박 대기시간 감소</div><span class="arrow">→</span>
<div class="step">모선·연결선 연계 개선</div><span class="arrow">→</span>
<div class="step">야드 체류시간 감소</div></div>
<div class="sec">환적 경로별 평균 야드 체류시간</div>
<div class="grid g4">{route_cards}</div>
<p class="foot">대시보드 현황 분석 집계 기준 · 타부두는 두 터미널의 야드 체류 합계 · 정상적인 연결선 대기 포함</p>
<div class="sec">비교하는 세 가지 운영 방식</div>
<div class="grid g3">{scenario_cards}</div>"""))

    # 아래는 질문이 나왔을 때 펼쳐 보는 세부 내용 (기존 탭 내용을 그대로 옮김)
    with st.expander("지표 집계 기준"):
        st.markdown("첨부 대시보드의 현황 분석 집계표를 사용합니다. 야드 장치부터 온샤시까지의 평균시간이며, "
                    "타부두는 출발·도착 터미널 구간을 합산했습니다. 제안서 본문의 분석과는 전처리·표본 범위가 달라 "
                    "일부 수치가 다를 수 있습니다. 정상적인 연결선 대기도 포함합니다.")
    with st.expander("현황과 문제점"):
        st.markdown("### 1) 현재 운영 방식")
        st.image(str(assets / "transfer-flow.svg"), width="stretch")
        st.caption("자부두는 동일 터미널 내 환적, 타부두는 터미널 간 이동과 양쪽 야드 체류가 발생합니다. 온샤시 등 세부 작업은 간략화했습니다.")
        st.markdown("**선석 운영 방식**")
        st.image(str(assets / "berth-operation.svg"), width="stretch")
        st.caption("각 터미널이 개별적으로 선석을 배정하므로 다른 터미널의 여유 선석을 바로 활용하기 어렵습니다.")
        st.markdown("부산 신항의 PNC, PNIT, HPNT, HJNC, BNCT, BCT, DGT 7개 터미널은 "
                    "각각 선석을 독립적으로 운영하고 선박을 배정합니다. 한 터미널에 입항이 집중되더라도 "
                    "다른 터미널의 여유 선석을 바로 활용하기 어렵습니다.")
        st.markdown("### 2) 분석에서 확인된 사실" + sections["1. 현황 및 문제점"].split("### 2) 분석에서 확인된 사실", 1)[1])
    with st.expander("개선 방안: 선석 공유에서 통합운영까지"):
        st.markdown(sections["2. 개선 방안"])
    with st.expander("기대효과와 판단 기준"):
        # 제안 단계 문구를 모델 조건에 한정된 표현으로 바꿔 표시한다
        effects = sections["3. 기대효과"]
        effects = effects.replace("**가정 성립**. 선석 통합이 체류 저감에 효과 있음",
                                  "모델 조건에서 가정을 지지. 선석 통합의 체류 저감 가능성 확인")
        effects = effects.replace("가정 불성립. 체류 원인은 연결선 일정, 장치 정책 등 다른 곳에 있음",
                                  "해당 조건에서 가정이 지지되지 않음. 연결선 일정·장치 정책 등 추가 원인 검토")
        st.markdown(effects)
        st.caption("시뮬레이션의 결과 해석은 해당 모델의 조건에 한정됩니다. 관측 상관관계나 모델 결과만으로 실제 운영의 인과관계를 확정하지 않습니다.")
    with st.expander("적용 범위, 분석 근거와 용어"):
        st.markdown("### 적용 범위와 한계")
        st.markdown(sections["적용 범위 및 한계"])
        st.markdown("### 분석 근거와 용어")
        st.markdown(sections["4. 분석 근거 및 용어"])
    with st.expander("제안서 전체 본문 확인"):
        st.markdown(proposal["content"])
        st.download_button("최신 제안서 원본 내려받기", (Path(__file__).parent / "data" / "제안서.ipynb").read_bytes(),
                           file_name="제안서.ipynb", mime="application/x-ipynb+json")
    st.markdown("**다음 단계** · [시뮬레이션 방식과 조건](/simulation) · [시뮬레이션 결과 비교](/simulation#simulation-results)")


def methodology():
    """시뮬레이션 화면: 진행 3단계 → 조정 방식 → 실험 조건. 입력·검증·지도는 접어 둔다."""
    data, _ = load_results()
    pv_style()

    # 진행 과정 3단계 카드 (4차가 최종 반영)
    steps = [("1~2차", False, "선석 공유 비교", "기존 운영과 B·C를 비교하고 모델 검증"),
             ("3차", False, "연결선 일정 앞당김", "연결선을 앞당겨 체류 감소 가능성 확인"),
             ("4차 · 최종 반영", True, "반복 검증", "반복 실험과 불확실성 구간, 상·하반기 검증")]
    step_cards = "".join(
        f'<div class="card"><span class="badge{"" if on else " off"}">{escape(stage)}</span>'
        f'<b>{escape(title)}</b><div class="cap">{escape(text)}</div></div>'
        for stage, on, title, text in steps)
    # 연결선 조정 방식 두 가지
    policy_cards = "".join(
        f'<div class="card"><b>{escape(title)}</b><div class="cap">{escape(body)}</div></div>'
        for title, body in [("전체 조정", "앞당길 수 있는 모든 연결선"),
                            ("선별 조정", "싣는 환적 컨테이너 − 내리는 환적 컨테이너가 양수인 연결선만")])
    # 실험 조건 카드 3개 (앞당김 시간·반복 횟수·최소 간격은 저장된 결과 파일에서 읽는다)
    hours_label = "·".join(str(h) for h in sorted({r["hours"] for r in data["rows"]}))
    condition_cards = (kpi("요청 앞당김", hours_label, "시간") +
                       kpi("최소 연결 간격", str(data["min_gap_h"]), "시간") +
                       kpi("반복 실험", str(data["repetitions"]), "회"))
    pv_html(panel("2 · 시뮬레이션", f"""
<h2>같은 입항 수요로 A·B·C를 비교하고, 연결선 일정 조정을 더해 검증했다</h2>
<p class="sub">선석 공유만으로는 접안 대기는 줄었지만 야드 체류 감소를 확인하기 어려워, 연결선을 앞당기는 방식을 추가했습니다.</p>
<div class="grid g3">{step_cards}</div>
<div class="sec">조정 방식과 실험 조건</div>
<div class="grid g2">{policy_cards}</div>
<div class="grid g3" style="margin-top:14px">{condition_cards}</div>
<p class="foot">2025년 자료 · 선석은 7개 터미널, 환적 체류는 DGT·HJNC 표본 ·
새 체류 = max(0, 기존 체류 + 연결선 접안 변화 − 모선 접안 변화)</p>"""))

    # 아래는 질문이 나왔을 때 펼쳐 보는 세부 내용
    with st.expander("시나리오별 선석 공유 범위 (배치도)"):
        scenario = st.segmented_control("운영 시나리오", list(SCENARIOS), default="A",
                                        format_func=lambda s: SCENARIOS[s], key="method_scenario")
        st.caption({"A": "기존 운영 · 자기 터미널의 선석만 접안 후보로 사용합니다.",
                    "B": "인접 공유 · 자기 터미널과 노트북에서 설정한 인접 터미널의 선석을 함께 검토합니다.",
                    "C": "전체 통합 · 신항 7개 터미널의 선석을 접안 후보로 검토합니다."}[scenario or "A"])
        terminal = st.selectbox("기준 터미널", list(NEIGHBORS), index=1, key="method_terminal")
        image, candidates = scenario_map(scenario or "A", terminal)
        st.image(image, width="stretch")
        st.markdown("**접안 후보** · " + " · ".join(candidates))
        st.caption("지도는 노트북에서 설정한 접안 후보 범위를 설명합니다. 후보 터미널에 실제 배정되었다는 의미는 아닙니다.")
    with st.expander("입력 자료와 접안 배정 규칙"):
        st.table(pd.DataFrame({
            "입력 자료": ["7개 터미널 선석배정", "선박 제원", "PORT-MIS 입항", "DGT·HJNC 환적"],
            "활용": ["접안·출항·점유시간 정리", "선박 길이와 연속 안벽 공간 비교", "실제 입항 시각 연결", "모선·연결선과 야드 체류 연결"],
        }))
        for column, title, body in zip(st.columns(3),
                                       ["① 도착 순서", "② 공간 확인", "③ 접안 배정"],
                                       ["도착한 선박부터 순서대로 처리합니다(FCFS).",
                                        "선박 길이와 연속 안벽 공간, 시간대별 점유 상태를 확인합니다.",
                                        "자기 터미널을 우선 사용하고, 시나리오에 따라 공유 후보를 검토합니다."]):
            with column.container(border=True):
                st.markdown(f"**{title}**")
                st.markdown(body)
    with st.expander("체류시간 계산과 일정 조정 순서"):
        st.markdown("모선 접안 → 최소 연결 간격 확보 → 연결선 도착 일정 조정 → 선석 재배정 → 새 야드 체류 계산")
        st.markdown("새 체류 = max(0, 기존 체류 + 연결선 접안 변화 − 모선 접안 변화)")
        st.markdown("연결선으로 앞당긴 선박이 다른 컨테이너에는 모선이 될 수 있습니다. "
                    "두 역할을 함께 반영하므로 요청 앞당김 시간 전체가 체류 감소로 이어지는 것은 아닙니다.")
    with st.expander("비교 지표와 검증 방법"):
        st.table(pd.DataFrame({"비교 지표": ["평균 야드 체류시간", "야드 체류 감소율", "다른 선박 평균 접안 지연", "일정 조정 실현율"],
                               "의미": ["컨테이너 체류가 얼마나 짧아지는가", "기존 A 대비 얼마나 줄었는가", "조정하지 않은 선박에 지연이 생기는가", "요청한 앞당김이 얼마나 실제 접안으로 실현되는가"]}))
        st.markdown("- **100회 반복**: 선박 길이 결측의 무작위 보완에 따른 결과 변동 점검\n"
                    "- **군집 부트스트랩 500회**: 연결선 표본 구성에 따른 불확실성 점검\n"
                    "- **상·하반기 분리 검증**: 상반기로 정한 기준을 하반기에 검증")
        st.caption("기상·도선·예선·크레인 등 실제 지연 원인 전체, 선사의 일정 변경 가능성, 터미널 이동에 따른 하역 생산성 변화는 검증되지 않았습니다.")
    with st.expander("1~6차 상세 내용과 시뮬레이션 기록"):
        stages = [
            ("1차", "통합운영 가능성 탐색", "기존 운영과 신항 전체 통합운영을 비교했습니다.", "simulation.ipynb"),
            ("2차", "운영 시나리오와 모델 검증", "A·B·C 시나리오와 PORT-MIS 입항 시각을 반영하고, 모델 검증과 민감도 분석을 추가했습니다.", "simulation_v2.ipynb"),
            ("3차", "연결선 일정으로 분석 확장", "연결선 단위로 일정을 앞당겨 야드 체류 감소 가능성과 감소 목표를 검토했습니다.", "simulation_v3.ipynb"),
            ("4차", "결과의 변동과 재현성 검증", "반복 시뮬레이션과 불확실성 구간을 추가하고, 하반기 자료에서도 효과가 유지되는지 검증했습니다.", "simulation_v4.ipynb"),
            ("5차", "외부 대기시간 보정 시뮬레이션", "외부 평균 대기시간 8.7시간을 기준으로 보정 시뮬레이션을 진행했습니다. 기간과 대기 정의가 달라 최종 결론에는 사용하지 않았습니다.", "simulation_v5.ipynb"),
            ("6차", "머신러닝으로 입력 보완", "선석 점유시간과 선박 길이를 예측해 입력 품질을 보완하고, 결론의 방향이 유지되는지 점검했습니다.", "simulation_v6.ipynb"),
        ]
        st.markdown(":blue-badge[최종 반영] 4차 검증 구조 · 6차 입력 보완 일부  \n"
                    ":gray-badge[최종 제외] 5차 외부 대기시간 보정")
        st.caption("각 차수는 서로 다른 조건과 가정의 시뮬레이션이며, 최종본은 4차를 바탕으로 6차 일부를 반영했습니다.")
        for number, title, description, notebook in stages:
            status = {"4차": " · 최종 반영", "5차": " · 최종 제외", "6차": " · 일부 최종 반영"}.get(number, "")
            st.markdown(f"**{number} · {title}{status}**")
            st.markdown(description)
            st.markdown(f"[시뮬레이션 기록 보기 ↗](https://github.com/busan-itt/simulation/blob/main/simulation/{notebook})")
    st.markdown("**[시뮬레이션 결과 비교하기 →](/simulation#simulation-results)**")
    st.caption("결과 화면에서는 최종 노트북의 저장된 시뮬레이션 결과를 조회합니다. 이 페이지의 지도 선택은 모델을 새로 실행하지 않습니다.")
    source_note(data)


def toggle_all_results():
    # "모든 결과 보기" 버튼을 누를 때마다 표시 여부를 뒤집는다
    st.session_state["show_all_results"] = not st.session_state.get("show_all_results", False)


def all_results_table(df, baseline, selected):
    # 저장된 모든 조건의 결과를 표로 만든다. 지금 선택한 정책·시간의 행은 강조한다
    rows = ""
    for r in df.sort_values(["policy", "hours", "scenario"], ascending=[False, True, True]).itertuples():
        near = baseline * (1 - r.reduction_pct / 100)                       # 근사 평균 체류
        real = realization(r, r.hours)
        css = ' class="sel"' if (r.policy, r.hours) == selected else ""
        rows += (f"<tr{css}><td>{escape(r.policy)}</td><td>{r.hours}시간</td><td>{escape(SHORT[r.scenario])}</td>"
                 f"<td>{r.reduction_pct:.2f}%</td><td>{near:.1f}</td><td>{r.other_delay_h * 60:.2f}</td>"
                 f"<td>{pct(real)}{'' if real is None else '%'}</td></tr>")
    return ('<div class="card"><table><thead><tr><th>정책</th><th>앞당김</th><th>운영</th><th>체류 감소율</th>'
            f'<th>평균 체류(시간)</th><th>다른 선박 지연(분)</th><th>실현율</th></tr></thead><tbody>{rows}</tbody></table></div>'
            '<p class="foot">평균 체류는 반올림된 기준 평균을 이용한 근사치 · 전체 정책 실현율은 원문의 정수 반올림 값 · 파란 줄은 지금 선택한 조건</p>')


def simulation():
    """시뮬레이션 결과 화면: 정책 버튼 + 시간 슬라이더 → 패널(KPI 4개 + 그래프 2개) → 모든 결과 버튼."""
    data, df = load_results()
    baseline = data["baseline_mean_h_rounded"]
    all_hours = sorted(int(h) for h in df.hours.unique())                    # 저장된 앞당김 시간 목록
    pv_style()

    # 조정 방식 버튼과 앞당김 시간 슬라이더 (선택을 해제해도 기본값으로 돌아간다)
    policy = st.segmented_control("연결선 조정 방식", ["선별", "전체"], default="선별",
                                  key="result_policy") or "선별"
    hours = st.select_slider("요청 앞당김 시간", options=all_hours,
                             value=48 if 48 in all_hours else all_hours[0],
                             format_func=lambda h: f"{h}시간", key="result_hours")
    st.caption(f"네 KPI의 결과가 함께 확인된 {'-'.join(str(h) for h in all_hours)}시간을 비교합니다.")

    # 선택한 조건의 A·B·C 행과 KPI 계산 (평균 체류는 반올림된 기준 평균으로 구한 근사치)
    rows = {s: pick_row(df, policy, hours, s) for s in "ABC"}
    a, c = rows["A"], rows["C"]
    reduction = float(a.reduction_pct)
    mean_after = baseline * (1 - reduction / 100)
    a_delay, c_delay = float(a.other_delay_h) * 60, float(c.other_delay_h) * 60
    a_real, c_real = realization(a, hours), realization(c, hours)

    # KPI 카드 4개: 시간이나 정책을 바꾸면 모두 함께 바뀐다
    real_sub = f"A {pct(a_real)}% → C {pct(c_real)}%" if c_real is not None else "원문에 기재되지 않은 조건"
    cards = (kpi("체류 감소율 (A)", f"{reduction:.2f}", "%", f"{baseline:.1f}시간 → 약 {mean_after:.1f}시간") +
             kpi("다른 선박 지연 (A)", f"{a_delay:.2f}", "분", "공유 없이 일정만 조정할 때") +
             kpi("다른 선박 지연 (C)", f"{c_delay:.2f}", "분", "전체 통합으로 선석 공유 시") +
             kpi("일정 조정 실현율 (C)", pct(c_real), "%" if c_real is not None else "", real_sub))
    # 그래프 2개 (같은 정책·앞당김 시간에서 A·B·C, 전체 통합 C를 강조)
    items_red = [(SHORT[s], float(rows[s].reduction_pct), s) for s in "ABC"]
    items_delay = [(SHORT[s], float(rows[s].other_delay_h) * 60, s) for s in "ABC"]

    pv_html(panel("3 · 시뮬레이션 결과", f"""
<h2>{escape(policy)} 조정 {hours}시간 · 야드 체류와 접안 지연 비교</h2>
<p class="sub">{escape(policy)} 정책 · {hours}시간 앞당김 · 최소 연결 간격 {data["min_gap_h"]}시간 · 기존 평균 {baseline:.1f}시간 대비</p>
<div class="grid g4">{cards}</div>
<div class="grid g2" style="margin-top:14px">
{bars("야드 체류 감소율", items_red, highlight="C")}
{bars("다른 선박 접안 지연", items_delay, highlight="C")}
</div>
<div class="take">같은 {hours}시간 조정 조건에서 A·B·C의 체류 감소율과 다른 선박의 지연, 일정 조정 실현율을 비교합니다.</div>
<p class="foot">최종 노트북의 조건별 저장 결과 · 평균 체류는 반올림된 {baseline:.1f}시간 기준 근사치 · A의 95% 구간 {ci_text(a)} · 전체 정책 실현율은 정수 반올림 값</p>"""))

    # 모든 결과 버튼: 누르면 저장된 모든 조건의 결과 표가 나타나고, 다시 누르면 접힌다
    show_all = st.session_state.get("show_all_results", False)
    st.button("모든 결과 접기" if show_all else "모든 결과 보기", key="show_all_results_button",
              on_click=toggle_all_results)
    if show_all:
        pv_html(all_results_table(df, baseline, (policy, hours)))
        st.download_button("전체 결과 CSV 내려받기", df.to_csv(index=False).encode("utf-8-sig"),
                           file_name="busan_itt_final_results.csv", mime="text/csv")

    # 아래는 질문이 나왔을 때 펼쳐 보는 세부 내용
    with st.expander("전체 조정과 선별 조정 비교"):
        chart = df[df.scenario == "C"].pivot(index="hours", columns="policy", values="reduction_pct").reset_index()
        st.bar_chart(chart, x="hours", y=["전체", "선별"], stack=False,
                     x_label="요청 앞당김(h)", y_label="기존 A 대비 체류 감소율(%) · C 기준", height=240)
    with st.expander("비교 기준과 결과 출처"):
        st.markdown("1~2차에서 시작한 선석 공유 비교, 3차의 연결선 조정, 4차의 반복 검증을 거쳐 정리한 "
                    "최종 노트북 저장 결과입니다. 이 화면에서 모델을 새로 실행하거나 결과를 보간하지 않습니다.")
        st.markdown("새 체류 = max(0, 기존 체류 + 연결선 접안 변화 − 모선 접안 변화). "
                    "같은 선박이 다른 컨테이너에는 모선이 되는 영향도 반영합니다.")
        st.markdown("환적 표본은 DGT·HJNC 자료입니다. 야드 체류와 전체 환적시간의 정의·표본은 다르며, "
                    "기상·도선·예선·크레인 등 실제 지연 원인 전체와 실제 선사의 일정 변경 가능성을 검증한 결과는 아닙니다.")
        source_note(data)
    st.markdown("**[프로젝트의 결론과 개선안 보기 →](/intro-solution#improvement-results)**")


def result_card(badge, r, baseline):
    # 최대 감소 결과 카드 하나: 조건 이름, 감소율, 평균 체류, 다른 선박 지연
    after = baseline * (1 - r.reduction_pct / 100)
    return (f'<div class="card"><span class="badge">{escape(badge)}</span>'
            f'<b>{escape(r.policy)} {int(r.hours)}시간 · {escape(NAME[r.scenario])}</b>'
            f'<div class="num">{r.reduction_pct:.2f}<small>% 감소</small></div>'
            f'<div class="cap">평균 야드 체류 약 {after:.1f}시간</div>'
            f'<div class="cap">다른 선박 추가 접안 지연 {r.other_delay_h * 60:.2f}분</div></div>')


def project_conclusion():
    """개선안 결과 화면: KPI 변화 → 저장된 조건 중 최대 감소 결과 → 향후 보완 과제 → 최종 개선안."""
    data, df = load_results()
    baseline = data["baseline_mean_h_rounded"]
    all_hours = sorted(int(h) for h in df.hours.unique())
    rep = 48 if 48 in all_hours else all_hours[0]                 # 대표 조건: 선별 · 48시간
    a, c = pick_row(df, "선별", rep, "A"), pick_row(df, "선별", rep, "C")
    mean_c = baseline * (1 - c.reduction_pct / 100)               # C의 근사 평균 체류
    a_delay, c_delay = a.other_delay_h * 60, c.other_delay_h * 60
    a_real, c_real = realization(a, rep), realization(c, rep)
    pv_style()

    # 저장된 모든 조건 중 체류 감소율이 가장 큰 행, 그리고 같은 정책·시간에서 접안 지연이 가장 작은 다른 시나리오
    top = df.loc[df.reduction_pct.idxmax()]
    others = df[(df.policy == top.policy) & (df.hours == top.hours) & (df.scenario != top.scenario)]
    second = others.loc[others.other_delay_h.idxmin()]
    gap = float(top.reduction_pct - second.reduction_pct)                   # 체류 감소율 차이(%p)
    delay_gap = float(top.other_delay_h - second.other_delay_h) * 60        # 접안 지연 차이(분)
    if gap >= 0 and delay_gap > 0:
        compare = (f"같은 {top.policy} {int(top.hours)}시간 조정에서 {top.scenario}의 체류 감소율은 {second.scenario}보다 {gap:.2f}%p 높았습니다. "
                   f"반면 {second.scenario}의 다른 선박 접안 지연은 {top.scenario}보다 {delay_gap:.2f}분 적었습니다. "
                   "체류 감소와 다른 선박의 지연을 함께 평가해야 합니다.")
    else:
        compare = f"같은 {top.policy} {int(top.hours)}시간 조정에서 체류 감소율과 다른 선박의 접안 지연을 함께 평가해야 합니다."
    # 최대 감소 조건의 실현율 수치가 저장 결과에 없으면 그 사실을 밝힌다
    missing = realization(top, top.hours) is None or realization(second, second.hours) is None
    caution = (f"{int(top.hours)}시간은 {top.hours / 24:g}일 앞당김 요청입니다. 실제 일정 변경 가능성은 검증되지 않았으며, "
               + ("이 조건의 실현율 수치는 확보된 저장 출력에 없어 제시하지 않았습니다. " if missing else "")
               + "실제 운영의 최적 조건으로 확정한 결과는 아닙니다.")

    cards = (kpi("평균 야드 체류", f"{mean_c:.1f}", "시간",
                 f"기존 {baseline:.1f} → 약 {mean_c:.1f}시간", f"약 {baseline - mean_c:.1f}시간 단축") +
             kpi("야드 체류 감소율", f"{c.reduction_pct:.2f}", "%", "일정 조정 전 A 대비", "체류시간 단축") +
             kpi("다른 선박 추가 접안 지연", f"{c_delay:.2f}", "분",
                 f"A {a_delay:.2f} → C {c_delay:.2f}분", f"{a_delay - c_delay:.2f}분 감소") +
             kpi("일정 조정 실현율", pct(c_real), "%", f"A {pct(a_real)} → C {pct(c_real)}%",
                 f"{(c_real - a_real):.1f}%p 증가" if None not in (a_real, c_real) else ""))
    todo = [("일정 변경 가능성", "선사가 실제로 앞당길 수 있는 범위와 최소 환적 소요시간 확인."),
            ("현장 조건 반영", "기상·도선·예선·크레인 등 추가 지연 요인과 터미널 이동에 따른 하역 생산성 변화 검증."),
            ("선석 공유 조건", "운영사·선사·항만 당국 간 협의, 장비 호환과 야드 연계 조건 검토."),
            ("자료 및 검증 범위", "DGT·HJNC 환적 표본의 결과를 신항 전체 화물로 확대하지 않고, 추가 자료를 확보해 적용 범위 검증.")]
    todo_html = "".join(f"<li><b>{escape(t)}:</b> {escape(x)}</li>" for t, x in todo)

    pv_html(panel("4 · 개선안 결과", f"""
<h2>연결선 선별 조정과 선석 공유로 야드 체류와 접안 지연을 줄인다</h2>
<p class="sub">프로젝트에서 확인한 KPI 변화와 최대 감소 결과, 실제 적용을 위한 보완 과제</p>
<div class="sec">1. KPI 변화 · 선별 {rep}시간 앞당김 + 신항 전체 통합(C)</div>
<div class="grid g4">{cards}</div>
<p class="foot">체류시간·감소율은 일정 조정 전 A 대비입니다. 추가 지연·실현율은 동일한 선별 {rep}시간 조정에서 A와 C를 비교했습니다. 평균 체류와 단축시간은 반올림된 기준 평균에 따른 근사치입니다.</p>
<div class="sec">2. 저장된 {len(df)}개 조건 중 가장 큰 야드 체류 감소 결과</div>
<div class="grid g2">
{result_card("체류 감소율 최대", top, baseline)}
{result_card("접안 지연을 함께 비교한 조건", second, baseline)}
</div>
<div class="take">{escape(compare)}</div>
<p class="foot">{escape(caution)}</p>
<div class="sec">3. 향후 보완 과제</div>
<div class="card"><ul class="lim">{todo_html}</ul></div>
<div class="take" style="margin-top:14px">최종 개선안: 연결선 일정의 선별 조정으로 야드 체류시간을 줄이고, 터미널 간 선석 공유로 다른 선박의 접안 지연을 완화합니다.</div>
<p class="foot">2025년 자료 기반 최종 노트북의 저장 결과 · 시뮬레이션 조건에서의 비교이며 실제 도입 성과를 의미하지 않습니다.</p>"""))

    # 아래는 질문이 나왔을 때 펼쳐 보는 세부 내용
    with st.expander("분석에서 확인한 내용"):
        st.markdown("- **야드 장기 체류와 환적 방향별 차이** 확인. 정상적인 연결선 대기도 포함되므로 체류 전체를 운영 지연으로 판단하지 않음.\n"
                    "- **개별 선박 시간 지표와 야드 체류시간의 뚜렷한 선형 관계는 확인하기 어려움.** 선석 배정과 모선·연결선의 연결 조건을 함께 검토.")
    with st.expander("시뮬레이션 검증 과정"):
        st.table(pd.DataFrame({
            "검증 과정": ["1~2차 · 선석 공유 비교", "3~4차 · 연결선 조정 및 반복 검증", "일정 조정 시 A·B·C 비교"],
            "확인한 내용": [
                "접안 대기시간은 감소했으나, 대기 감소만으로 야드 체류 감소를 확인하기는 어려움",
                "전체 조정보다 선별 조정에서 더 높은 야드 체류 감소율 확인",
                "선석 공유 시 다른 선박의 평균 접안 지연 감소, 요청 대비 일정 조정 실현율 증가",
            ],
        }))
        st.caption("최종본은 4차 검증 구조와 6차 입력 보완 일부를 반영했습니다. 5차 외부 대기시간 보정은 최종 결론에서 제외했습니다.")
    st.markdown("[시뮬레이션 결과 확인](/simulation#simulation-results) · [제안서 확인](/intro-solution)")
    source_note(data)
