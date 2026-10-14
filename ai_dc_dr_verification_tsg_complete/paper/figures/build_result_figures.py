"""Generate main-paper charts from finalized, explicitly scoped result tables."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parents[2]; F=P/'paper/figures'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8.5,'axes.labelsize':8.5,'axes.titlesize':9,'xtick.labelsize':8.5,'ytick.labelsize':8.5,'legend.fontsize':8.5,'pdf.fonttype':42,'ps.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
d=pd.read_csv(P/'experiments/exp31_risk_execution_composition/results/final/risk_frontier_summary.csv')
d=d[d.split.eq('locked')].set_index('method').loc[['archived_joint','exact_mse_total_only','active_tail_fraction_0.50']]
labels=['Original joint','Exact total-only','Active tail']; colors=['#777777','#d55e00','#0072b2']
fig,axes=plt.subplots(2,1,figsize=(3.5117,2.5),layout='constrained')
for ax,col,title in zip(axes,['false_credit_mean_mwh','false_credit_tail_mwh'],['Mean false credit','Worst-14-day mean']):
 ax.barh(labels,d[col],color=colors,height=.6);ax.invert_yaxis();ax.set_xlim(0,float(d[col].max())*1.25);ax.set_title(title,loc='left',pad=2);ax.set_xlabel('False credit (MWh/day)',labelpad=1);ax.grid(axis='x',alpha=.17);ax.set_axisbelow(True)
 for i,v in enumerate(d[col]):ax.text(v+.015,i,f'{v:.3f}',va='center',fontsize=8.5)
for ext in ['pdf','png']:fig.savefig(F/f'fig_risk_tail_tradeoff.{ext}',dpi=320)
plt.close(fig)
d=pd.read_csv(P/'experiments/exp32_matched_gate_capacity/results/final/runtime_capacity_cells.csv')
d=d[d.method.eq('runtime_direct_total_tail')]
fig,ax=plt.subplots(figsize=(3.5117,2.5),layout='constrained')
for (day,g),color,marker in zip(d.groupby('day'),['#0072b2','#d55e00','#009e73'],['o','s','^']):
 g=g.sort_values('nominal_reference_peak_utilization')
 ax.plot(g.nominal_reference_peak_utilization*100,g.maximum_achieved_capacity_utilization*100,color=color,marker=marker,markersize=4,lw=1,label=f'Day {day}')
ax.axhline(100,color='#555',ls='--',lw=.8,label='Capacity limit')
ax.set(xlabel='Nominal reference utilization (%)',ylabel='Executed peak utilization (%)',xlim=(15,115),ylim=(10,108),xticks=[20,80,98,110]);ax.grid(alpha=.18);ax.legend(frameon=False,loc='upper left',bbox_to_anchor=(0,1.28),ncol=2,fontsize=8,columnspacing=1.1,handlelength=1.4,borderaxespad=0)
for ext in ['pdf','png']:fig.savefig(F/f'fig_runtime_capacity.{ext}',dpi=320)
plt.close(fig)
