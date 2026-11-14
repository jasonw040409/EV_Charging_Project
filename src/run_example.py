import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import csv,json,platform
import cvxpy
from charging import Scenario,immediate,optimize,soc_from_power,metrics
from aging import evaluate


def prices_for(a):
    h=np.arange(a.n)*a.dt
    return np.where(h<4,.30,np.where(h<9,.10,.24))


def main():
    a=Scenario();prices=prices_for(a);rows=[];powers={}
    for name,wp,ws in [('immediate',None,None),('cost_only',0,0),
                        ('power_penalty',1,0),('combined',1,10)]:
        if wp is None: p=immediate(a);info=dict(status='deterministic',max_constraint_residual=0.)
        else: p,info=optimize(prices,a,wp,ws)
        s=soc_from_power(p,a)
        # Do not clip computed schedules or repair energy: fail on material violations.
        m=metrics(p,prices,a)
        assert m['energy_residual_kwh']<1e-6 and m['power_violation_kw']<1e-6
        assert m['target_residual']<1e-8 and m['soc_violation']<1e-8
        assert info['max_constraint_residual']<1e-6
        row=dict(strategy=name,**m,**evaluate(s,a.dt),**info)
        rows.append(row);powers[name]=p
    out=ROOT/'results';out.mkdir(exist_ok=True)
    (out/'comparison.json').write_text(json.dumps(rows,indent=2)+'\n')
    fields=list(dict.fromkeys(k for r in rows for k in r))
    with (out/'comparison.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    with (out/'schedules.csv').open('w') as f:
        w=csv.writer(f);w.writerow(['elapsed_hours','price_dollars_per_kwh']+
            [f'{k}_kw' for k in powers]+[f'{k}_soc_start' for k in powers])
        for i in range(a.n):w.writerow([i*a.dt,prices[i]]+[p[i] for p in powers.values()]+
            [soc_from_power(p,a)[i] for p in powers.values()])
    lines=['| Strategy | Cost ($) | Power proxy | High-SOC proxy | Calendar increment (ppm) | Grid kWh |',
           '|---|---:|---:|---:|---:|---:|']
    for r in rows:lines.append(f"| {r['strategy']} | {r['cost_dollars']:.4f} | {r['power_proxy']:.6f} | {r['high_soc_proxy']:.6f} | {r['calendar_increment_ppm']:.4f} | {r['grid_kwh']:.6f} |")
    (out/'comparison.md').write_text('\n'.join(lines)+'\n\nCalendar-only extrapolation for a specified LFP cell, not total damage or measured life.\n')
    fig,axes=plt.subplots(3,1,figsize=(10,8),sharex=True,layout='constrained')
    t=np.arange(a.n+1)*a.dt
    axes[0].stairs(prices,t,color='black');axes[0].set_ylabel('Price ($/kWh)')
    for k,p in powers.items():
        axes[1].stairs(p,t,label=k.replace('_',' '))
        axes[2].plot(t,soc_from_power(p,a)*100,label=k.replace('_',' '))
    axes[1].set_ylabel('Grid power (kW)');axes[1].legend(ncol=2,fontsize=9)
    axes[2].set_ylabel('SOC (%)');axes[2].axhline(70,color='grey',ls=':',label='proxy threshold')
    axes[2].set_xticks(np.arange(0,13,2),['18:00','20:00','22:00','00:00','02:00','04:00','06:00'])
    axes[2].set_xlabel('Illustrative connected window (local clock)')
    for ax in axes:ax.grid(alpha=.2);ax.set_xlim(0,12)
    fig.suptitle('Equal energy, four charging schedules | synthetic prices')
    fig.savefig(out/'schedules.png',dpi=170);plt.close(fig)
    # A modest actual weight sweep, not an assertion about all weights.
    sweep=[]
    for wp in [0,.1,1,10]:
        for ws in [0,1,10]:
            p,info=optimize(prices,a,wp,ws)
            sweep.append(dict(**metrics(p,prices,a),
                              **evaluate(soc_from_power(p,a),a.dt),**info))
    (out/'weight_sweep.json').write_text(json.dumps(sweep,indent=2)+'\n')
    (out/'environment.json').write_text(json.dumps(dict(python=platform.python_version(),
        numpy=np.__version__,cvxpy=cvxpy.__version__,solver='CLARABEL',
        prior_history='365 days at 25 C and SOC .5; calendar only',
        synthetic_prices='18-22 .30;22-03 .10;03-06 .24 dollars/kWh',
        cost_only_tie_break='minimum squared power within $1e-8 of minimum cost'),indent=2)+'\n')
    print('\n'.join(lines))

if __name__=='__main__':main()
