"""Read-only pilot audit. Writes only a separate reviews/nov14/pilot_audit.json.

Run: .venv/bin/python reviews/nov14/audit_pilot.py
No optimizer runs, API calls, or baseline imports. Standard library only.
"""
import csv
import hashlib
import json
import math
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
INPUTS = [
    'README.md', 'docs/data_access_assessment.md', 'docs/model_specification.md',
    'data/acn_sessions_raw.json', 'data/sample_sessions.csv', 'data/inspection.json',
    'results/real_session_pilot.json', 'results/interpretation.md',
    'src/inspect_data.py', 'src/charging.py', 'src/aging.py',
    'EV_Charging_Initial_Project_Plan.md',
]


def main():
    raw = json.loads((ROOT / INPUTS[3]).read_text())['_items']
    csv_rows = {r['session_id']: r for r in csv.DictReader((ROOT / INPUTS[4]).open())}
    inspection = json.loads((ROOT / INPUTS[5]).read_text())
    inspected = {r['session_id']: r for r in inspection['records']}
    pilot = json.loads((ROOT / INPUTS[6]).read_text())
    ids = {r['sessionID'] for r in raw}
    assert len(raw) == len(ids) == len(csv_rows) == len(inspected) == 5
    assert inspection['inspected_count'] == 5
    assert {r['session_id'] for r in pilot} == ids and len(pilot) == 20
    sessions = []
    for index, r in enumerate(raw, 1):
        sid = r['sessionID']
        start = parsedate_to_datetime(r['connectionTime'])
        end = parsedate_to_datetime(r['disconnectTime'])
        hours = (end - start).total_seconds() / 3600
        energy = r['kWhDelivered']
        target = .30 + .90 * energy / 60
        local = start.astimezone(ZoneInfo(r['timezone']))
        clock = local.hour + local.minute / 60 + local.second / 3600
        n = math.ceil(hours / .25)
        cheap_hours = sum(not (16 <= (clock + j * hours / n) % 24 < 21)
                          for j in range(n)) * hours / n
        rows = [v for v in pilot if v['session_id'] == sid]
        methods = {v['strategy']: v for v in rows}
        assert len(rows) == len(methods) == 4
        assert set(methods) == {'immediate', 'cost_only', 'power_penalty', 'combined'}
        for view in [csv_rows[sid], inspected[sid]]:
            assert abs(float(view['duration_hours']) - hours) < 1e-10
            assert abs(float(view['delivered_grid_kwh']) - energy) < 1e-10
            assert abs(float(view['derived_target_soc']) - target) < 1e-10
            assert abs(float(view['assumed_initial_soc']) - .30) < 1e-10
            assert abs(float(view['assumed_capacity_kwh']) - 60) < 1e-10
            assert datetime.fromisoformat(view['connection_utc']) == start
            assert datetime.fromisoformat(view['disconnect_utc']) == end
            assert datetime.fromisoformat(view['connection_local']) == local
            flag = view['done_charging_after_disconnect']
            if isinstance(flag, str):
                flag = flag == 'True'
            assert flag == (parsedate_to_datetime(r['doneChargingTime']) > end)
        for row in rows:
            assert row['status'] == ('deterministic' if row['strategy'] == 'immediate' else 'optimal')
            assert abs(row['grid_kwh'] - energy) < 1e-6
            assert abs(row['battery_kwh'] - .9 * energy) < 1e-6
            assert abs(row['departure_soc'] - target) < 1e-8
            assert row['interval_count'] == math.ceil(hours / .25)
            assert abs(row['interval_count'] * row['interval_hours'] - hours) < 1e-10
            assert row['high_soc_proxy'] == 0
            assert row['calendar_increment_ppm'] > 0
        power, combined = methods['power_penalty'], methods['combined']
        sensitivity = []
        for initial in [.30, .60, .75]:
            goal = initial + .9 * energy / 60
            energy_feasible = energy <= 7.2 * hours + 1e-9
            capacity_feasible = goal <= .9 + 1e-12
            sensitivity.append(dict(assumed_initial_soc=initial, derived_target_soc=goal,
                energy_window_feasible=energy_feasible, capacity_feasible=capacity_feasible,
                feasible=energy_feasible and capacity_feasible,
                threshold_crossed_if_feasible=goal > .7 if capacity_feasible and energy_feasible else None))
        sessions.append(dict(label=f'S{index}', session_id=sid, raw_id=r['_id'],
            station_id=r['stationID'], space_id=r['spaceID'],
            connection_utc=start.isoformat(), disconnect_utc=end.isoformat(),
            connection_local=start.astimezone(ZoneInfo(r['timezone'])).isoformat(),
            disconnect_local=end.astimezone(ZoneInfo(r['timezone'])).isoformat(),
            duration_hours=hours, delivered_grid_kwh=energy, derived_target_soc=target,
            cheap_slot_capacity_grid_kwh=cheap_hours * 7.2,
            done_charging_after_disconnect_seconds=(parsedate_to_datetime(r['doneChargingTime'])-end).total_seconds(),
            full_power_minimum_hours=energy/7.2,
            combined_minus_power={k:combined[k]-power[k] for k in
                ['cost_dollars','power_proxy','high_soc_proxy','peak_kw','calendar_increment_ppm']},
            saved_metrics={name:{k:v[k] for k in ['cost_dollars','power_proxy','high_soc_proxy',
                'peak_kw','calendar_increment_ppm']} for name,v in methods.items()},
            analytic_sensitivity=sensitivity))
    maxima={k:max(r.get(k,0) for r in pilot) for k in ['energy_residual_kwh',
        'power_violation_kw','soc_violation','target_residual','max_constraint_residual']}
    assert maxima['energy_residual_kwh'] < 1e-6
    assert maxima['power_violation_kw'] < 1e-6
    assert maxima['soc_violation'] < 1e-8
    assert maxima['target_residual'] < 1e-8
    assert maxima['max_constraint_residual'] < 1e-6
    output=dict(review_date='2026-11-14', sessions=5, generated_schedules=20,
        raw_missing_user_inputs=sum(r.get('userInputs') is None for r in raw),
        raw_missing_user_ids=sum(r.get('userID') is None for r in raw),
        input_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in INPUTS},
        checks='PASS: raw/CSV/inspection/result consistency, saved feasibility and inactive penalty',
        limitations='Saved pilot has aggregate metrics, not per-slot power/SOC trajectories. No new solves.',
        maximum_saved_residuals=maxima, records=sessions)
    (Path(__file__).parent/'pilot_audit.json').write_text(json.dumps(output,indent=2)+'\n')
    print(output['checks'])
    for initial in [.30,.60,.75]:
        cases=[v for s in sessions for v in s['analytic_sensitivity'] if v['assumed_initial_soc']==initial]
        print(f'Assumed SOC {initial:.0%}: {sum(v["feasible"] for v in cases)}/5 feasible; '
              f'{sum(v["threshold_crossed_if_feasible"] is True for v in cases)} feasible targets above 70%.')


if __name__ == '__main__':
    main()
