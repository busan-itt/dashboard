"""Build the approved unified chart layout from notebook results and source records."""
from pathlib import Path
import base64, json, os
import numpy as np
import pandas as pd
from scipy import stats
PROJECT=Path(__file__).resolve().parents[2]
OUT=PROJECT/'prototype-streamlit/assets/correlation-analysis/unified'
OUT.mkdir(parents=True,exist_ok=True)
os.environ['MPLCONFIGDIR']=str(PROJECT/'prototype-streamlit/output/.matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
plt.rcParams.update({'font.family':'Malgun Gothic','font.size':13,'axes.unicode_minus':False,
 'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,
 'text.color':'#142f42','axes.labelcolor':'#526573','xtick.color':'#526573','ytick.color':'#142f42'})
BLUE='#185dac';TEAL='#187a72';ORANGE='#bd6043'
def encode(fig,name):
 p=OUT/(name+'.png');fig.savefig(p,dpi=110,bbox_inches='tight',pad_inches=.15,facecolor='white');plt.close(fig)
 with Image.open(p) as img:
  compact=img.convert('RGB').quantize(colors=128)
 compact.save(p,optimize=True)
 return p.name
def dot(labels,series,name):
 fig,ax=plt.subplots(figsize=(9.5,max(2.4,len(labels)*.59+1.2)))
 y=np.arange(len(labels))
 for i,(unit,values) in enumerate(series):
  off=(i-(len(series)-1)/2)*.38
  ax.scatter(values,y+off,s=65,color=TEAL if '항차' in unit else BLUE,label=unit,zorder=3,marker='D' if '항차' in unit else 'o')
  for x,pos in zip(values,y+off): ax.annotate(f'{x:.3f}',(x,pos),xytext=(9,0),textcoords='offset points',fontsize=11,va='center')
 ax.set(yticks=y,yticklabels=labels,xlim=(-1,1),xlabel='Pearson r',xticks=[-1,-.5,0,.5,1])
 ax.set_ylim(len(labels)-.5,-.5);ax.axvline(0,color='#a7b5c2',lw=1);ax.grid(axis='x',alpha=.15)
 ax.legend(loc='upper center',bbox_to_anchor=(.5,1.22),ncol=2,frameon=False,fontsize=11)
 fig.tight_layout();return encode(fig,name)
def scatter(x,y,xlabel,ylabel,unit,name):
 x=np.asarray(x);y=np.asarray(y);valid=np.isfinite(x)&np.isfinite(y);x=x[valid];y=y[valid]
 fig,ax=plt.subplots(figsize=(9.5,4.2))
 ax.scatter(x,y,s=21,alpha=.45,color=TEAL if '항차' in unit else BLUE,marker='D' if '항차' in unit else 'o',edgecolors='none')
 slope,intercept=np.polyfit(x,y,1);xx=np.array([x.min(),x.max()]);ax.plot(xx,slope*xx+intercept,color=ORANGE,lw=2)
 ax.set(xlabel=xlabel+' (시간)',ylabel=ylabel+' (시간)');ax.grid(alpha=.13)
 r=stats.pearsonr(x,y)
 ax.set_title(f'{unit} · N={len(x):,} · r={r.statistic:.3f}',loc='left',fontsize=13,pad=18)
 fig.tight_layout();return {'label':xlabel,'image':encode(fig,name),'r':round(float(r.statistic),4),'n':len(x)}
def arr(v): return np.frombuffer(base64.b64decode(v['bdata']),dtype=v['dtype']) if isinstance(v,dict) else np.array(v)
d=pd.read_csv(PROJECT/'analysis/dgt_odt_sample_outputs/항차별_본선작업완료지연시간_분석자료.csv')
assert len(d)==73
r=float(d['본선작업완료지연시간'].corr(d['야드 장치 기간']))
result={'dgt':{'title':'DGT_ODT','sample':'122건 · 73항차','definition':'장치 → 반출','unit':'항차별 TEU 가중평균',
 'comparison':dot(['본선작업완료지연시간'],[('항차별 TEU 가중평균',[r])],'unified-dgt-r'),
 'plots':[scatter(d['본선작업완료지연시간'],d['야드 장치 기간'],'본선작업완료지연시간','TEU 가중평균 장치 기간','적하모선 항차','unified-dgt-scatter')],
 'conclusion':'73항차에서 r=0.104, p=0.381. 유의한 선형 상관을 확인하지 못했다.',
 'note':'작업완료 지표는 반입 마감부터 마지막 본선 작업까지의 간격이다.'}}
berth_root=PROJECT/'analysis/dgt_odt_sample_outputs'
work=pd.read_csv(berth_root/'표7a_선석별_자부두환적작업물동량.csv')
berth_r=pd.read_csv(berth_root/'표8_적하선석별_본선작업완료지연시간_상관검정.csv')
assert work['총 작업량(TEU)'].tolist()==[95,185,136]
assert berth_r['항차수'].tolist()==[16,29,28]
result['dgt']['berth']=[]
for name,label in [('선석별_총본선작업물동량.png','선석별 양하·적하 환적 작업 물동량'),
                   ('선석별_본선작업완료지연시간_상관.png','적하 선석별 본선작업완료지연시간과 야드 장치 기간의 상관관계')]:
 filename='unified-dgt-berth-'+str(len(result['dgt']['berth']))+'.png'
 (OUT/filename).write_bytes((berth_root/name).read_bytes())
 result['dgt']['berth'].append({'image':filename,'label':label})
result['dgt']['berth_meta']='DGT ODT · 122건 · 208 TEU'
result['dgt']['berth_volume_note']='양하와 적하를 각각 집계한 작업량: B1 95 TEU · B2 185 TEU · B3 136 TEU. 총 작업량 416 TEU.'
result['dgt']['berth_correlation_note']='종속변수: 장치→반출 기간의 항차별 TEU 가중평균. B1 16항차 · B2 29항차 · B3 28항차. 세 선석 모두 Holm 보정 후 유의한 Pearson 상관을 확인하지 못했다.'
n=json.loads((PROJECT/'analysis/상관관계_분석_HJNC_ODT.ipynb').read_text(encoding='utf-8'))
p=next(o['data']['application/vnd.plotly.v1+json'] for o in n['cells'][30]['outputs'] if 'application/vnd.plotly.v1+json' in o.get('data',{}))
labels=['입항 지연시간*','작업시작전 대기시간','작업시간','작업 후 출항 대기시간','출항 지연시간*']
plots=[]
for i,label in enumerate(['작업시간','출항 지연시간*','입항 지연시간*','작업시작전 대기시간']):
 t=p['data'][2*i];assert len(arr(t['x']))==1490
 plots.append(scatter(arr(t['x']),arr(t['y']),label,'야드 장치 기간','컨테이너','unified-hjnc-'+str(i)))
result['hjnc']={'title':'HJNC_ODT','sample':'1,490건','definition':'장치 → 온샤시','unit':'컨테이너 기준',
 'comparison':dot(labels,[('컨테이너 기준',[.0620,.1124,.0920,-.0317,.1038])],'unified-hjnc-r'),
 'plots':plots,'conclusion':'5개 지표 모두 |r|<0.12. 선박 운영시간만으로 야드 장치 기간의 차이를 설명하기 어렵다.',
 'note':'* 입·출항 지연시간은 반입 일정 기준 경과시간을 뜻하는 대체지표이다.'}
result['hjnc']['berth_pending']=True
# Reproduce the supplied ITT notebook calculations in memory, without its display,
# plotting, or source-writing cells. These cells only read the specified inputs.
n=json.loads((PROJECT/'analysis/상관관계_분석_ITT_표본변경.ipynb').read_text(encoding='utf-8'))
ns={'__builtins__':__builtins__}
for i in [1,3,4,6,10]:
 code=''.join(n['cells'][i]['source'])
 # Suppress display only; all statistical calculations remain as supplied.
 code=code.replace('from IPython.display import display, Markdown','from IPython.display import Markdown\ndef display(*args, **kwargs): pass')
 exec(compile(code,f'itt-cell-{i}','exec'),ns)
data=ns['data'];corr=ns['results'];metrics=ns['metrics'];Y=ns['Y']
for key,direction in [('forward','DGT→HJNC'),('reverse','HJNC→DGT')]:
 g=data[data['환적방향'].eq(direction)]; series=[]
 for unit in ['방문 건','항차 평균']:
  vals=corr[corr['환적방향'].eq(direction)&corr['분석단위'].eq(unit)].set_index('지표').loc[metrics,'Pearson_r'].tolist()
  series.append((unit+' 기준',vals))
 plots=[]
 for i,metric in enumerate(metrics[:3]):
  a=g[[metric,Y,'모선항차']].dropna().groupby('모선항차').agg(X=(metric,'first'),Y=(Y,'mean'))
  plots.append(scatter(a.X,a.Y,labels[i],'항차 평균 총 야드 시간','HJNC 항차','unified-itt-'+key+str(i)))
 result[key]={'title':'DGT ↔ HJNC ITT','direction':direction,'sample':f'{len(g):,}건','definition':'두 터미널의 장치 → 온샤시 합계','unit':'방문 건 · 항차 평균',
  'comparison':dot(labels,series,'unified-itt-'+key+'-r'),'plots':plots,
  'conclusion':('항차 기준 5개 지표 모두 p>0.05. 뚜렷한 선형 상관을 확인하지 못했다.' if key=='forward' else '작업시작전 대기는 r=0.150, p=0.0003(579항차). 약한 양의 상관이 관측되었다.'),
  'note':f'총 야드 시간 계산 {g[Y].notna().sum():,}건. * 입·출항 지표는 예정 대비 지연과 구분한다.'}
 # ITT report explanatory variables are HJNC schedule metrics. Both the workload
 # and stratified correlations below therefore refer explicitly to HJNC berths.
 berths=sorted(g['선석'].dropna().unique())
 assert g['TEU'].notna().all() and g['선석'].notna().all()
 volume=g.groupby('선석')['TEU'].sum().reindex(berths,fill_value=0)
 operation='적하' if key=='forward' else '양하'
 fig,ax=plt.subplots(figsize=(9.5,4.0));x=np.arange(len(berths))
 unload=volume.values if operation=='양하' else np.zeros(len(berths))
 load=volume.values if operation=='적하' else np.zeros(len(berths))
 ax.bar(x,unload,color='#4e83af',label='양하',width=.6)
 ax.bar(x,load,bottom=unload,color='#dc9c56',label='적하',width=.6)
 for i,v in enumerate(volume):ax.annotate(f'{v:,.2f}'.rstrip('0').rstrip('.'),(i,v),xytext=(0,6),textcoords='offset points',ha='center',fontsize=11)
 ax.set(xticks=x,xticklabels=berths,xlabel='HJNC 선석',ylabel='환적 작업 물동량 (TEU)',title=f'{direction} · HJNC 선석별 환적 작업 물동량')
 ax.set_ylim(0,volume.max()*1.2);ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True);ax.legend(frameon=False)
 fig.tight_layout();volume_image=encode(fig,'unified-itt-'+key+'-berth-volume')
 matrix=np.full((len(berths),len(metrics)),np.nan);counts=np.zeros(matrix.shape,dtype=int)
 for row,berth in enumerate(berths):
  for col,metric in enumerate(metrics):
   v=g.loc[g['선석'].eq(berth),[metric,Y,'모선항차']].dropna()
   calls=v.groupby('모선항차').agg(X=(metric,'first'),Y=(Y,'mean'))
   counts[row,col]=len(calls)
   if len(calls)>=3 and calls.X.nunique()>1 and calls.Y.nunique()>1:
    matrix[row,col]=calls.X.corr(calls.Y)
 fig,ax=plt.subplots(figsize=(10,4.3))
 im=ax.imshow(matrix,cmap='RdBu_r',vmin=-1,vmax=1,aspect='auto')
 for i in range(len(berths)):
  for j in range(len(metrics)):
   txt=f'r={matrix[i,j]:.3f}\nn={counts[i,j]}' if np.isfinite(matrix[i,j]) else '계산 불가'
   ax.text(j,i,txt,ha='center',va='center',fontsize=11,color='white' if abs(matrix[i,j])>.6 else '#142f42')
 ax.set(yticks=np.arange(len(berths)),yticklabels=berths,xticks=np.arange(len(metrics)),
  xticklabels=['입항 지연*','작업시작전\n대기','작업시간','작업 후\n출항 대기','출항 지연*'],ylabel='HJNC 선석',xlabel='독립변수',title=f'{direction} · HJNC 선석별 야드 장치 기간 상관관계')
 ax.tick_params(length=0,pad=8);fig.colorbar(im,ax=ax,label='Pearson r',fraction=.045,pad=.04)
 fig.tight_layout();corr_image=encode(fig,'unified-itt-'+key+'-berth-correlation')
 result[key]['berth']=[{'image':volume_image,'label':'HJNC 선석별 양하·적하 작업량'},
  {'image':corr_image,'label':'HJNC 선석별 5개 독립변수와 총 야드 장치 기간의 상관계수'}]
 result[key]['berth_meta']=direction+f' · {len(g):,}건 · HJNC 선석 기준'
 result[key]['berth_volume_note']=f'HJNC에서 수행한 {operation} 작업량 {volume.sum():,.0f} TEU. 해당 방향의 DGT 작업은 이 그래프에 포함하지 않았다.'
 result[key]['berth_correlation_note']='종속변수: 두 터미널 총 야드 시간의 HJNC 항차별 평균. 각 칸의 n은 해당 선석·지표에서 계산 가능한 HJNC 항차수이다. * 반입 일정 기준 경과시간.'
# HJNC ODT source supplied by the user. Verify all saved plot observations,
# rather than accepting a match in row counts alone.
import re
h=pd.read_csv(PROJECT/'data/DATA/hjnc_hjnc.csv',low_memory=False).rename(columns={'야드 장치시간':'야드 장치 시간'})
assert len(h)==1490 and h['컨테이너번호'].is_unique
h['Y']=((pd.to_datetime(h['온샤시 시간'])-pd.to_datetime(h['야드 장치 시간'])).dt.total_seconds()/3600).round(1)
saved=pd.Series(arr(p['data'][0]['y']),index=[v[0] for v in p['data'][0]['customdata']])
assert set(h['컨테이너번호'])==set(saved.index)
assert np.allclose(h.set_index('컨테이너번호').Y.loc[saved.index],saved)
schedule=ns['schedule'].copy();canonical=ns['canonical_voyage'];schedule=schedule.set_index('모선항차')
for side in ['양하','적하']:
 h[side+'항차']=h[side+'모선항차'].map(canonical)
 h[side+'선석']=h[side+'항차'].map(schedule['선석'])
assert h[['양하선석','적하선석']].notna().all().all()
def teu(size):
 s=str(size).strip();m=re.match(r'^(20|40|45)(?:/|$)',s)
 if m:return {20:1,40:2,45:2.25}[int(m[1])]
 return {'2':1,'4':2,'L':2.25,'M':2.25}.get(s[:1],np.nan)
h['TEU']=h['Size/Type'].map(teu);assert h.TEU.notna().all()
for metric,(end,start) in zip(metrics,ns['formulas']):
 h[metric]=((h['적하항차'].map(schedule[end])-h['적하항차'].map(schedule[start])).dt.total_seconds()/3600).round(1)
assert h[metrics].notna().all().all()
assert abs(h[metrics[1]].corr(h.Y)-.1124)<.0001
for trace_index,metric in [(0,metrics[2]),(2,metrics[4]),(4,metrics[0]),(6,metrics[1])]:
 trace=p['data'][trace_index]
 saved_x=pd.Series(arr(trace['x']),index=[v[0] for v in trace['customdata']])
 assert np.allclose(h.set_index('컨테이너번호')[metric].loc[saved_x.index],saved_x)
berths=sorted(set(h['양하선석'])|set(h['적하선석']))
unload=h.groupby('양하선석').TEU.sum().reindex(berths,fill_value=0)
load=h.groupby('적하선석').TEU.sum().reindex(berths,fill_value=0)
fig,ax=plt.subplots(figsize=(9.5,4.0));x=np.arange(len(berths))
ax.bar(x,unload,color='#4e83af',label='양하',width=.6)
ax.bar(x,load,bottom=unload,color='#dc9c56',label='적하',width=.6)
for i,v in enumerate(unload+load):ax.annotate(f'{v:,.2f}'.rstrip('0').rstrip('.'),(i,v),xytext=(0,6),textcoords='offset points',ha='center',fontsize=11)
ax.set(xticks=x,xticklabels=berths,xlabel='HJNC 선석',ylabel='환적 작업 물동량 (TEU)',title='HJNC ODT · 선석별 양하·적하 환적 작업 물동량')
ax.set_ylim(0,(unload+load).max()*1.2);ax.grid(axis='y',alpha=.18);ax.set_axisbelow(True);ax.legend(frameon=False)
fig.tight_layout();vimg=encode(fig,'unified-hjnc-berth-volume')
matrix=np.full((len(berths),len(metrics)),np.nan);counts=np.zeros(matrix.shape,dtype=int)
for row,berth in enumerate(berths):
 for col,metric in enumerate(metrics):
  v=h.loc[h['적하선석'].eq(berth),[metric,'Y','적하항차']].dropna()
  calls=v.groupby('적하항차').agg(X=(metric,'first'),Y=('Y','mean'))
  counts[row,col]=len(calls)
  if len(calls)>=3 and calls.X.nunique()>1 and calls.Y.nunique()>1:matrix[row,col]=calls.X.corr(calls.Y)
fig,ax=plt.subplots(figsize=(10,4.3));im=ax.imshow(matrix,cmap='RdBu_r',vmin=-1,vmax=1,aspect='auto')
for i in range(len(berths)):
 for j in range(len(metrics)):
  txt=f'r={matrix[i,j]:.3f}\nn={counts[i,j]}' if np.isfinite(matrix[i,j]) else '계산 불가'
  ax.text(j,i,txt,ha='center',va='center',fontsize=11,color='white' if abs(matrix[i,j])>.6 else '#142f42')
ax.set(yticks=np.arange(len(berths)),yticklabels=berths,xticks=np.arange(len(metrics)),
 xticklabels=['입항 지연*','작업시작전\n대기','작업시간','작업 후\n출항 대기','출항 지연*'],ylabel='HJNC 적하 선석',xlabel='독립변수',title='HJNC ODT · 적하 선석별 야드 장치 기간 상관관계')
ax.tick_params(length=0,pad=8);fig.colorbar(im,ax=ax,label='Pearson r',fraction=.045,pad=.04)
fig.tight_layout();cimg=encode(fig,'unified-hjnc-berth-correlation')
result['hjnc']['berth_pending']=False
result['hjnc']['berth']=[{'image':vimg,'label':'HJNC ODT 선석별 양하·적하 작업 물동량'}, {'image':cimg,'label':'HJNC ODT 적하 선석별 상관계수'}]
result['hjnc']['berth_meta']=f'HJNC ODT · 1,490건 · {h.TEU.sum():,.0f} TEU'
result['hjnc']['berth_volume_note']=f'양하와 적하를 각각 집계한 총 작업량 {(unload+load).sum():,.0f} TEU. 해당 표본의 작업량이며 HJNC 전체 물동량은 아니다.'
result['hjnc']['berth_correlation_note']='종속변수: 장치→온샤시 기간의 적하 항차별 평균. n은 해당 적하 선석의 항차수이다. * 반입 일정 기준 경과시간. 선석별 결과는 원자료로 새로 계산한 탐색 분석이다.'
(OUT/'unified-berth-values.json').write_text(json.dumps({'hjnc_volume':{'unload':unload.to_dict(),'load':load.to_dict()},'hjnc_berth_r':matrix.tolist(),'hjnc_berth_n':counts.tolist()},ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'reports.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('Published unified reports:', ', '.join(result))
