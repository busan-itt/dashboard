"""Publish selected saved notebook results, without running notebook code.

Notebook outputs are the authority; only HJNC charts are redrawn from saved
observations/summary tables. No source notebook or source data is modified.
"""
from pathlib import Path
from html import escape, unescape
import base64
import hashlib
import json
import os
import re

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT.parent
OUT = ROOT / 'assets' / 'correlation-analysis'
OUT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'output' / '.matplotlib'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({'font.family': 'Malgun Gothic', 'axes.unicode_minus': False,
                     'font.size': 13, 'axes.spines.top': False, 'axes.spines.right': False,
                     'text.color': '#142f42', 'axes.labelcolor': '#526573',
                     'figure.facecolor': 'white', 'savefig.facecolor': 'white'})

NAMES = {'dgt': '상관관계_분석_DGT_ODT.ipynb',
         'hjnc': '상관관계_분석_HJNC_ODT.ipynb',
         'itt': '상관관계_분석_ITT_표본변경.ipynb'}
BOOKS = {key: json.loads((PROJECT / 'analysis' / name).read_text(encoding='utf-8'))
         for key, name in NAMES.items()}


def tables(key, cell):
    result = []
    for output in BOOKS[key]['cells'][cell].get('outputs', []):
        html = ''.join(output.get('data', {}).get('text/html', []))
        for table in re.findall(r'<table\b.*?</table>', html, re.S):
            rows = []
            for row in re.findall(r'<tr\b.*?</tr>', table, re.S):
                rows.append([unescape(re.sub('<[^>]*>', '', val)).strip()
                             for val in re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.S)])
            # pandas outputs have a separate unnamed index column.
            if rows and rows[0] and rows[0][0] == '':
                rows = [row[1:] for row in rows]
            result.append(rows)
    return result


def table(key, cell, index=0):
    rows = tables(key, cell)[index]
    head = ''.join(f'<th scope="col">{escape(v)}</th>' for v in rows[0])
    body = ''.join('<tr>' + ''.join(f'<td>{escape(v)}</td>' for v in row) + '</tr>' for row in rows[1:])
    return f'<div class="report-table"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


def image(filename, caption):
    return f'<figure class="report-figure"><img data-report-image="{filename}" alt="{escape(caption)}"><figcaption>{escape(caption)}</figcaption></figure>'


def notebook_images(key, cell, captions):
    result = []
    outputs = [o['data']['image/png'] for o in BOOKS[key]['cells'][cell].get('outputs', [])
               if 'image/png' in o.get('data', {})]
    assert len(outputs) == len(captions), (key, cell)
    for i, (data, caption) in enumerate(zip(outputs, captions)):
        filename = f'{key}-{cell}-{i}.png'
        (OUT / filename).write_bytes(base64.b64decode(''.join(data)))
        result.append(image(filename, caption))
    return ''.join(result)


def section(title, text):
    return f'<section class="report-section"><h2>{title}</h2>{text}</section>'


def metrics(items):
    return '<div class="report-metrics">' + ''.join(
        f'<div><span>{label}</span><strong>{value}</strong></div>' for label, value in items) + '</div>'


def save_chart(fig, filename):
    fig.savefig(OUT / filename, dpi=160, bbox_inches='tight', pad_inches=.18)
    plt.close(fig)


def dot_chart(filename, title, labels, series):
    fig, ax = plt.subplots(figsize=(11.8, max(3.3, len(labels) * .62 + 1.4)))
    colors = ['#185dac', '#187a72']
    y = np.arange(len(labels))
    for i, (name, values) in enumerate(series):
        offset = (i - (len(series) - 1) / 2) * .22
        ax.scatter(values, y + offset, s=85, color=colors[i], label=name, zorder=3)
        for x, pos in zip(values, y + offset):
            ax.annotate(f'{x:.4f}', (x, pos), xytext=(8, 0), textcoords='offset points', va='center', fontsize=11)
    ax.set(yticks=y, yticklabels=labels, xlim=(-1, 1), xlabel='Pearson r', title=title)
    ax.invert_yaxis(); ax.axvline(0, color='#a7b5c2', lw=1)
    ax.grid(axis='x', alpha=.18); ax.legend(loc='lower right')
    fig.tight_layout(); save_chart(fig, filename)
    return image(filename, title)


# Validate the saved results before publishing. Counts refer to container visits,
# while correlation tests may use voyages or a smaller effective sample.
assert tables('dgt', 8)[0][1][0] == '122'
assert tables('dgt', 10)[0][1][1] == '73'
assert sum(int(row[1]) for row in tables('hjnc', 9)[0][1:]) == 1490
itt_counts = tables('itt', 6)[0]
assert any('17389' in row for row in itt_counts[1:])
assert any('20143' in row for row in itt_counts[1:])

dgt = metrics([('분석 대상', '122건 · 208 TEU'), ('상관검정 단위', '적하모선 73항차'),
               ('장치→반출 평균', '203.21시간')])
dgt += '<p class="report-note">현황 분석과 기준 표본은 122건으로 같다. 이 보고서의 종속변수는 <strong>장치→반출</strong>이며, 현황 분석의 야드 장치 구간인 <strong>장치→온샤시</strong>와 측정 종료 시점이 다르다. 현황 분석의 반입→반출 평균은 203.43시간이다.</p>'
dgt += section('1. 분석 지표와 장치 기간',
    '<p>항차별 마지막 컨테이너 작업완료 시각과 반입 마감 시각의 간격이 장치 기간과 관련되는지 살펴보았다. 같은 항차의 컨테이너는 설명변수를 공유하므로, 적하모선항차별 TEU 가중평균 장치 기간을 한 관측값으로 비교하였다.</p>'
    '<p><strong>X:</strong> 관측된 마지막 본선 작업완료 시각 − 반입 마감 시각<br><strong>Y:</strong> 반출 시각 − 야드 장치 시각</p>'
    + table('dgt', 8, 0)
    + '<p>보고서의 ‘본선작업완료지연시간’은 반입 마감과 마지막 작업 사이의 간격이다. 예정 작업완료 시각 대비 지연을 직접 측정한 값은 아니다.</p>')
dgt += section('2. 본선 작업완료 시각과 장치 기간의 상관관계',
    notebook_images('dgt', 11, ['적하모선 73항차의 본선작업완료지연시간과 TEU 가중평균 장치 기간'])
    + table('dgt', 10, 0) + table('dgt', 10, 1)
    + '<p><strong>Pearson r=0.104, p=0.381</strong>로 유의수준 0.05에서 유의한 선형 상관을 확인하지 못했다. Spearman ρ=0.130, p=0.272이며, 단변량 R²는 약 0.011이다.</p>')
dgt += section('3. 선석별 작업 물동량과 상관관계',
    '<p>122건·208 TEU의 양하와 적하를 각각 집계한 총 본선 작업량은 416 TEU이다. 이는 해당 표본의 작업량이며 DGT 전체 물동량은 아니다.</p>'
    + notebook_images('dgt', 17, ['선석별 양하·적하 작업 물동량', '적하 선석별 장치 기간과 본선 작업완료 지표의 상관계수'])
    + table('dgt', 16, 2)
    + '<p>총 작업량은 B2가 185 TEU로 가장 컸다. 선석별 Pearson·Spearman 검정은 Holm 보정 후 유의수준 0.05에서 유의하지 않았다. B2의 순위 상관계수는 0.429이지만 보정 p값은 0.0606이다.</p>')
dgt += section('4. 화물 유형별 장치 기간과 상관관계',
    '<p>일반 적컨 108건, 냉동 5건, 위험물 9건을 비교하였다. 전체 122건은 모두 적컨이며, 아래 그래프의 ‘적컨’ 범주는 냉동·위험물을 제외한 일반 적컨이다.</p>'
    + notebook_images('dgt', 21, ['화물 유형별 물동량과 장치 기간', '화물 유형별 본선 작업완료 지표의 상관계수'])
    + table('dgt', 20, 1)
    + '<p>TEU 가중평균 장치 기간은 일반 적컨 194.87시간, 냉동 148.01시간, 위험물 203.39시간이었다. 화물 유형별 검정도 Holm 보정 후 유의하지 않았다. 냉동·위험물은 항차수가 적어 추정의 불확실성이 크다.</p>')
dgt += section('5. 결론', '<blockquote>현재 표본에서는 본선 작업완료 지표 하나만으로 장치 기간의 차이를 설명할 충분한 근거를 확인하지 못했다.</blockquote><p>선석·화물 유형별 차이는 관측 특성으로 해석한다. 유의하지 않은 상관은 선박 일정의 영향이 전혀 없다는 증명이 아니며, 선박 지연이 장기 장치를 유발한다는 인과관계를 확인한 결과도 아니다.</p>')

hjnc = metrics([('분석 대상', '1,490건'), ('야드 체류시간 평균', '195.9시간'), ('72시간 이상', '87.0%')])
hjnc += '<p class="report-note">현황 분석과 기준 건수는 1,490건으로 같다. 야드 체류시간도 <strong>장치→온샤시</strong>로 같다. 본 보고서는 컨테이너별 시간을 0.1시간 단위로 반올림해 사용하였다.</p>'
dist = tables('hjnc', 9)[0][1:]
fig, ax = plt.subplots(figsize=(11.8, 4.4))
values = [int(row[1]) for row in dist]
bars = ax.barh([r[0] for r in dist], values, color=['#a7b5c2'] * 3 + ['#187a72', '#185dac'], height=.58)
for bar, row in zip(bars, dist):
    ax.text(bar.get_width()+15, bar.get_y()+bar.get_height()/2, f'{row[1]}건 · {row[2]}%', va='center')
ax.invert_yaxis(); ax.set(xlim=(0, 1320), xlabel='컨테이너 수', title='HJNC ODT 야드 체류시간 구간별 분포')
ax.grid(axis='x', alpha=.15); fig.tight_layout(); save_chart(fig, 'hjnc-distribution.png')
hjnc += section('1. 야드 체류시간과 장기 체류 분포',
    '<p>장치부터 온샤시까지 평균 195.9시간, 중앙값 168.9시간으로 평균이 약 27시간 길었다. 최솟값은 1.9시간, 최댓값은 885.0시간이었다.</p>'
    + image('hjnc-distribution.png', '1,490건 중 120시간 이상 1,093건, 72시간 이상 1,296건')
    + '<p><strong>120시간 이상은 73.4%</strong>로 가장 많았고, 72시간 이상은 87.0%였다. 일부 장기 체류가 평균을 높이는 분포를 보였다.</p>')
labels = ['입항 지연시간(대체지표)', '작업시작전 대기시간', '작업시간', '작업 후 출항 대기시간', '출항 지연시간(대체지표)']
rs = [float(row[2]) for row in tables('hjnc', 28)[0][1:]]
hjnc += section('2. 현재 적하 선박의 운영시간과 야드 체류시간',
    '<p>선박 시간 지표 5개와 야드 체류시간을 컨테이너 1,490건 기준으로 비교하였다. 같은 항차의 컨테이너는 같은 선박 시간 값을 공유하므로 탐색적인 상관계수로 해석한다.</p>'
    '<p>입항 지연시간은 입항일시 − 반입 시작일시, 출항 지연시간은 출항일시 − 반입 마감일시이다. 둘 다 반입 일정 기준 경과시간이며 예정 입·출항 시각 대비 실제 지연과 구분한다. 작업시작전 대기는 작업 시작 − 입항, 작업시간은 완료 − 시작, 작업 후 출항 대기는 출항 − 작업 완료로 계산한다.</p>'
    + dot_chart('hjnc-current-correlation.png', '현재 선박 시간 지표와 야드 체류시간', labels, [('컨테이너 1,490건', rs)]))
plotly = next(o['data']['application/vnd.plotly.v1+json'] for o in BOOKS['hjnc']['cells'][30]['outputs'] if 'application/vnd.plotly.v1+json' in o.get('data', {}))
def arr(value):
    return np.frombuffer(base64.b64decode(value['bdata']), dtype=value['dtype']) if isinstance(value, dict) else np.asarray(value)
titles = ['작업시간', '출항 지연시간(대체지표)', '입항 지연시간(대체지표)', '작업시작전 대기시간']
for i, title in enumerate(titles):
    scatter, line = plotly['data'][2*i:2*i+2]
    x,y = arr(scatter['x']),arr(scatter['y'])
    assert len(x)==len(y)==1490
    fig, ax = plt.subplots(figsize=(11.8,4.6))
    ax.scatter(x,y,s=14,alpha=.35,color='#185dac')
    ax.plot(arr(line['x']),arr(line['y']),color='#bc5c43',lw=2)
    ax.set(xlabel=title+' (시간)',ylabel='야드 체류시간 (시간)',title=f'{title}와 야드 체류시간 · r={np.corrcoef(x,y)[0,1]:.4f}')
    ax.grid(alpha=.15);fig.tight_layout();filename=f'hjnc-scatter-{i}.png';save_chart(fig,filename)
    hjnc += image(filename, f'{title} · 컨테이너 1,490건의 실제 관측값과 회귀선')
hjnc += '<p>5개 지표 모두 |r|&lt;0.12로 뚜렷한 선형 관계를 확인하기 어려웠다. 작업시작전 대기가 5시간을 초과한 7건을 별도로 비교한 민감도 분석에서도 r은 0.1124에서 0.0861로 바뀌어 약한 관계에 머물렀다. 기본 분석은 1,490건이다.</p>'
hjnc += section('3. 직전 선박과 후속 선박의 관계',
    '<p>동일 선석에서 직전에 입항한 선박의 운영시간과 후속 선박의 작업시작전 대기시간을 비교하였다. 이 분석은 컨테이너 분석과 구분되는 별도의 선박 항차 분석이다.</p>'
    + dot_chart('hjnc-previous-waiting.png', '직전 선박 지표와 후속 선박 작업시작전 대기시간',
                ['이전 선박 작업시간 · 996항차', '이전 입항→출항 경과시간 · 997항차', '선박 간 시간 간격 · 997항차'],
                [('선박 항차 기준', [-.0196,-.0177,-.0380])])
    + '<p>상관계수의 절댓값은 모두 0.04 미만으로 뚜렷한 선형 관계가 확인되지 않았다. 선박 점유시간이라는 명칭은 입항→출항 경과시간을 뜻한다.</p>')
hjnc += section('4. 직전 선박과 후속 컨테이너의 관계',
    '<p>컨테이너 1,490건과 적하모선 378항차를 각각 관측 단위로 비교하였다.</p>'
    + dot_chart('hjnc-previous-yard.png', '직전 선박 지표와 후속 컨테이너 야드 체류시간',
                ['이전 선박 작업시간', '이전 입항→출항 경과시간', '선박 간 시간 간격'],
                [('컨테이너 1,490건', [.0368,.0308,.0263]), ('적하모선 378항차', [-.1553,-.1561,.0224])])
    + '<p>컨테이너 기준에서는 0에 가까웠으며, 항차 기준에서는 일부 약한 음의 상관을 보였다. 항차당 컨테이너 수가 1~38건으로 달라 관측 단위별 가중 차이가 결과에 영향을 미쳤을 수 있다.</p>')
hjnc += section('5. 결론과 시뮬레이션 방향',
    '<blockquote>관측된 선박 운영시간의 길이만으로 컨테이너별 야드 체류시간 차이를 설명하기 어렵다.</blockquote><p>이는 선박 일정의 영향이 없다는 뜻은 아니다. 후속 단계에서는 선박 입출항 일정과 장치·온샤시 시각을 활용한 시뮬레이션 시나리오를 검토한다. 운영 조건 변경이 온샤시 시각에 미치는 영향은 별도의 가정과 제약조건을 명시해 해석한다.</p>')

itt = metrics([('DGT → HJNC', '17,389건'), ('HJNC → DGT', '20,143건'), ('전체 기준 표본', '37,532건')])
itt += '<p class="report-note">현황 분석과 방향별 기준 표본 건수가 같다. 건수는 환적 방문 기록 단위이며, 이 보고서의 종속변수는 <strong>두 터미널의 장치→온샤시 시간 합계</strong>이다. 현황 분석의 반입→최종 반출 전체 소요시간과 구분한다.</p>'
itt += section('1. 방향별 야드 장치 기간',
    '<p>DGT → HJNC의 총 야드 시간은 평균 216.579시간, 중앙값 174.625시간이다. HJNC → DGT는 평균 177.639시간, 중앙값 142.850시간이다.</p>'
    '<p>전체 기준 표본은 37,532건이며 총 야드 시간 계산에는 37,521건이 사용되었다. 방향별로 DGT → HJNC는 17,378건, HJNC → DGT는 20,143건이다. 따라서 평균은 각 지표의 실제 계산 건수와 함께 읽는다.</p>'
    + notebook_images('itt', 8, ['방향별 총 야드 장치 기간의 누적분포와 전체 분포'])
    + table('itt', 8)
    + '<p>DGT → HJNC는 두 터미널 시간을 함께 계산할 수 있는 17,378건의 평균이므로, 현황 분석에서 공정별 평균을 더한 값과 소수점 수준의 차이가 날 수 있다.</p>')
itt += section('2. 선박 운영시간과 야드 장치 기간의 상관관계',
    '<p>HJNC의 입항 지연시간, 작업시작전 대기시간, 작업시간, 작업 후 출항 대기시간, 출항 지연시간을 분석하였다. 입·출항 지연이라는 명칭은 각각 입항 − 반입 시작, 출항 − 반입 마감의 경과시간을 뜻한다. 나머지 세 지표는 각각 입항→작업 시작, 작업 시작→완료, 작업 완료→출항이다.</p>'
    '<p>방문 건 기준의 상관계수와 HJNC 항차 평균 기준을 비교하였다. 같은 항차의 선박 시간 값이 반복되므로, p값은 항차 기준으로 제시한다.</p>'
    + notebook_images('itt', 11, ['환적 방향별 방문 건 기준과 항차 평균 기준 Pearson 상관계수 비교'])
    + table('itt', 10)
    + '<p>HJNC → DGT의 작업시작전 대기는 항차 기준 <strong>r=0.1497, p=0.0003, 579항차</strong>로 약한 양의 상관을 보였다. 전체 합산의 같은 지표는 r=0.1029, p=0.0046이다. 여러 지표를 탐색한 결과이므로 인과관계로 확대하지 않는다. DGT → HJNC의 항차 기준 5개 지표는 모두 p&gt;0.05였다.</p>')
itt += section('3. 핵심 세 지표의 방향별 산점도',
    '<p>입항 지연시간, 작업시작전 대기시간, 작업시간을 방향별로 비교하였다. 각 점은 HJNC 항차별 평균 총 야드 시간이다.</p>'
    + notebook_images('itt', 13, ['방향별 핵심 세 지표와 총 야드 장치 기간 · 실제 계산 항차수와 r 표시'])
    + '<p>DGT → HJNC는 세 지표 모두 520항차이다. HJNC → DGT는 입항 지표 580항차, 작업시작전 대기와 작업시간은 각각 579항차이다.</p>')
long_rows = tables('itt', 15)[0][1:]
fig, ax = plt.subplots(figsize=(11.8,4.2))
y=np.arange(3)
for i, direction in enumerate(['DGT→HJNC','HJNC→DGT']):
    rows=[r for r in long_rows if r[0]==direction]
    vals=[float(r[-1]) for r in rows]
    bars=ax.barh(y+(i-.5)*.32, vals, height=.3,label=direction,color=['#185dac','#187a72'][i])
    for bar,v in zip(bars,vals): ax.text(v+1,bar.get_y()+bar.get_height()/2,f'{v:.2f}%',va='center',fontsize=11)
ax.set(yticks=y,yticklabels=['72시간 이상','168시간 이상','720시간 이상'],xlim=(0,105),xlabel='시간 계산 가능 방문 중 비율 (%)',title='방향별 장기 야드 장치 비율')
ax.invert_yaxis();ax.legend(loc='lower right');ax.grid(axis='x',alpha=.15)
fig.tight_layout();save_chart(fig,'itt-long-stay.png')
itt += section('4. 장기 장치 비중과 민감도 비교',
    image('itt-long-stay.png', '분모: DGT → HJNC 17,378건, HJNC → DGT 20,143건')
    + table('itt', 15, 0)
    + '<p>72시간 이상은 DGT → HJNC 89.50%, HJNC → DGT 80.23%이다. 168시간 이상도 각각 51.97%, 41.12%를 차지했다. 보고서의 3,900시간 기준 민감도 비교에서는 해당 기준을 넘는 DGT 야드 기록이 두 방향 모두 0건이어서, 기본 분석과 상관계수가 동일했다. 3,900시간은 운영상 공식 기준이 아니다.</p>')
itt += section('5. 결론',
    '<blockquote>방향별로 관련성의 크기가 다르며, HJNC → DGT의 작업시작전 대기에서 약한 양의 상관이 관측되었다.</blockquote><p>총 야드 시간에는 두 터미널 구간이 포함되지만 설명변수는 HJNC 선박 지표이다. 따라서 DGT의 체류까지 HJNC 작업의 결과라고 해석할 수 없다. 예정 대비 지연을 직접 측정한 지표도 아니므로, 이 결과만으로 ‘선박 지연 → 장기 장치’라는 원인 관계를 확정하지 않는다.</p>')

for key, body in [('dgt',dgt),('hjnc',hjnc),('itt',itt)]:
    footer=f'<p class="report-source">분석 출처: {escape(NAMES[key])}</p>'
    (OUT / f'{key}.html').write_text('<div class="correlation-page">'+body+footer+'</div>',encoding='utf-8')
manifest = {'sources': {name:hashlib.sha256((PROJECT/'analysis'/name).read_bytes()).hexdigest() for name in NAMES.values()},
            'baseline_counts': {'DGT ODT':122,'HJNC ODT':1490,'DGT → HJNC ITT':17389,'HJNC → DGT ITT':20143},
            'itt_effective_yard_counts': {'DGT → HJNC':17378,'HJNC → DGT':20143},
            'note': 'Published saved notebook results; source notebooks were not executed or modified.'}
(OUT/'source-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
print('Published DGT, HJNC and ITT report pages.')
