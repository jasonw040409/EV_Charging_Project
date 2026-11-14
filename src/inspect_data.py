"""Inspect five original API records, preserve timestamps; run assumed-battery pilots."""
import json,csv,math
from pathlib import Path
from datetime import datetime
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo
import numpy as np
from charging import Scenario,immediate,optimize,metrics,soc_from_power
from aging import evaluate
ROOT=Path(__file__).resolve().parents[1]

def main():
    x=json.loads((ROOT/'data/acn_sessions_raw.json').read_text())
    rows=[];pilots=[]
    for v in x['_items']:
        start=parsedate_to_datetime(v['connectionTime']);end=parsedate_to_datetime(v['disconnectTime'])
        local=start.astimezone(ZoneInfo(v['timezone']));duration=(end-start).total_seconds()/3600
        energy=v['kWhDelivered']
        if duration<=0 or energy<0:
            raise ValueError('Nonpositive window or negative delivered energy in raw sample')
        n=math.ceil(duration/.25)
        a=Scenario(n=n,dt=duration/n,target=.3+.9*energy/60)
        anomaly=parsedate_to_datetime(v['doneChargingTime'])>end if v.get('doneChargingTime') else False
        rows.append(dict(session_id=v['sessionID'],connection_utc=start.isoformat(),
            disconnect_utc=end.isoformat(),connection_local=local.isoformat(),duration_hours=duration,
            delivered_grid_kwh=energy,user_requested_kwh=None,
            user_inputs_present=v.get('userInputs') is not None,
            done_charging_after_disconnect=anomaly,assumed_capacity_kwh=60,assumed_initial_soc=.3,
            derived_target_soc=a.target))
        # Exact original window, equal slots <=15 min; no overnight translation.
        clock=local.hour+local.minute/60+local.second/3600+np.arange(n)*a.dt
        prices=np.where(((clock%24)>=16)&((clock%24)<21),.30,.15)
        try:a.validate()
        except ValueError as e:
            pilots.append(dict(session_id=v['sessionID'],status='excluded',reason=str(e)));continue
        for name,wp,ws in [('immediate',None,None),('cost_only',0,0),('power_penalty',1,0),('combined',1,10)]:
            p,info=(immediate(a),dict(status='deterministic')) if wp is None else optimize(prices,a,wp,ws)
            m=metrics(p,prices,a)
            assert m['energy_residual_kwh']<1e-6 and m['power_violation_kw']<1e-6
            assert m['target_residual']<1e-8 and m['soc_violation']<1e-8
            assert info.get('max_constraint_residual',0)<1e-6
            pilots.append(dict(session_id=v['sessionID'],strategy=name,interval_hours=a.dt,interval_count=a.n,**m,
                **evaluate(soc_from_power(p,a),a.dt),**info))
    with (ROOT/'data/sample_sessions.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=rows[0]);w.writeheader();w.writerows(rows)
    (ROOT/'data/inspection.json').write_text(json.dumps(dict(inspected_count=len(rows),records=rows),indent=2)+'\n')
    (ROOT/'results/real_session_pilot.json').write_text(json.dumps(pilots,indent=2)+'\n')
    print(f'Inspected {len(rows)} original records; {sum(r["done_charging_after_disconnect"] for r in rows)} timing flags; {len(pilots)} pilot outputs.')

if __name__=='__main__':main()
