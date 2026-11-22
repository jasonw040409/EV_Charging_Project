"""Task 2: read saved study inputs/results and export quality/exclusion tables.

Standard library only; no downloads, optimizer runs, or baseline edits.
Run: python3 experiments/data_review/summarize_data_quality.py
"""
import argparse
import collections
import csv
import hashlib
import json
from email.utils import parsedate_to_datetime as parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
METHODS = {'immediate', 'cost_only', 'power_penalty', 'combined'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study-dir', default='results/nov18')
    parser.add_argument('--output-dir', default='results/data_review_nov21')
    args = parser.parse_args()
    study = (ROOT / args.study_dir).resolve()
    output = (ROOT / args.output_dir).resolve()
    names = ['selection_ledger.json', 'cohort.json', 'metrics.json', 'exclusions.json']
    hashes = {name: hashlib.sha256((study / name).read_bytes()).hexdigest() for name in names}
    ledger, cohort, metrics, exclusions = [json.loads((study / n).read_text()) for n in names]
    byid = {r['sessionID']: r for r in cohort}
    if len(byid) != len(cohort):
        raise ValueError('Cohort contains duplicate session IDs')
    additions = {r['session_id'] for r in ledger if r['selected_addition']}
    if not additions <= set(byid):
        raise ValueError('Selected additions do not match cohort')
    if any(r['selected_addition'] and r['screening_reasons'] for r in ledger):
        raise ValueError('A selected addition has a screening exclusion')

    flags = {}
    for r in cohort:
        start, end = parse(r['connectionTime']), parse(r['disconnectTime'])
        stop = parse(r['doneChargingTime']) if r.get('doneChargingTime') else None
        flags[r['sessionID']] = 'charging_stop_outside_connected_window' if stop and not start <= stop <= end else ''
    real = [r for r in metrics if r.get('family') == 'real']
    cases = collections.defaultdict(list)
    for r in real:
        if r['session_id'] not in byid or bool(r['timing_flag']) != bool(flags[r['session_id']]):
            raise ValueError('Saved metric/cohort flag mismatch')
        cases[r['case']].append(r)
    for case, group in cases.items():
        if len(group) != 4 or {r['method'] for r in group} != METHODS:
            raise ValueError(f'Incomplete four-method result: {case}')
        if len({(r['session_id'], r['scenario']['initial']) for r in group}) != 1:
            raise ValueError(f'Mixed session/SOC case: {case}')
    excluded_real = [r for r in exclusions if r.get('family') == 'real']
    infeasible = [r for r in excluded_real if r['status'] == 'analytically_infeasible']
    failures = [r for r in excluded_real if r['status'] != 'analytically_infeasible']
    if set(cases) & {r['case'] for r in infeasible}:
        raise ValueError('A case is both completed and analytically infeasible')
    reason_counts = collections.Counter(reason for r in ledger for reason in set(r['screening_reasons']))
    eligible = sum(not r['screening_reasons'] for r in ledger)
    excluded_candidates = sum(bool(r['screening_reasons']) for r in ledger)
    summary = []

    def add(stage, measure, count, unit, denominator, note):
        summary.append(dict(stage=stage, measure=measure, count=count, unit=unit,
                            denominator=denominator, explanation=note))

    add('candidate_screening', 'candidate_ledger_rows', len(ledger), 'candidate records', len(ledger), 'Frozen screening ledger; not selected evaluation cohort')
    add('candidate_screening', 'eligible_additions', eligible, 'candidate records', len(ledger), 'No logged screening reasons')
    add('candidate_screening', 'selected_additions', len(additions), 'unique sessions', eligible, 'Selected by duration/energy-bin rule before optimization')
    add('candidate_screening', 'eligible_not_selected', eligible-len(additions), 'candidate records', eligible, 'Valid candidates left unused by sampling; not failures')
    add('candidate_screening', 'not_eligible_as_additions', excluded_candidates, 'candidate records', len(ledger), 'Includes already-retained controls/duplicates, not just bad data')
    add('selected_cohort', 'sessions', len(cohort), 'unique sessions', len(cohort), 'Original controls plus selected additions')
    add('selected_cohort', 'retained_original_controls', len(cohort)-len(additions), 'unique sessions', len(cohort), 'Kept as reference cases, including flagged diagnostic control')
    add('selected_cohort', 'timing_flagged', sum(bool(v) for v in flags.values()), 'unique sessions', len(cohort), 'Charging-stop timestamp outside connection window')
    add('selected_cohort', 'without_this_timing_flag', sum(not v for v in flags.values()), 'unique sessions', len(cohort), 'No detected stop-order flag; not a guarantee of overall data quality')
    add('selected_cohort', 'missing_user_inputs', sum(r.get('userInputs') is None for r in cohort), 'unique sessions', len(cohort), 'No user-requested energy/departure inferred')
    add('selected_cohort', 'missing_user_id', sum(r.get('userID') is None for r in cohort), 'unique sessions', len(cohort), 'Cannot establish unique driver/vehicle identity')
    add('scenario_evaluation', 'completed_four_method_cases', len(cases), 'session/SOC scenarios', '', 'Same recorded session can have several assumed arrival SOCs')
    add('scenario_evaluation', 'analytically_infeasible_cases', len(infeasible), 'session/SOC scenarios', '', 'Impossible under the assumptions; recorded energy not reduced')
    add('scenario_evaluation', 'numerical_or_evaluation_failures', len(failures), 'logged failure entries', '', 'Distinct from analytical infeasibility; a case may have method-level entries')
    add('scenario_evaluation', 'successful_real_schedules', len(real), 'simulated schedules', '', 'Four methods per completed scenario, not independent real observations')
    breakdown = []
    starts = sorted({r['scenario']['initial'] for r in real + excluded_real})
    for initial in starts:
        done = [g for g in cases.values() if g[0]['scenario']['initial'] == initial]
        bad = [r for r in infeasible if r['scenario']['initial'] == initial]
        clean = sum(not flags[g[0]['session_id']] for g in done)
        breakdown.append(dict(assumed_initial_soc_pct=100*initial,
            completed_four_method_cases=len(done), analytically_infeasible_cases=len(bad),
            completed_clean_paired_cases=clean, completed_flagged_diagnostic_cases=len(done)-clean,
            successful_schedules=sum(len(g) for g in done)))
    details = []
    for r in excluded_real:
        a = r['scenario']
        reasons = []
        if a['target'] > a['maximum_soc']:
            reasons.append('derived target exceeds assumed maximum SOC')
        energy = a['capacity'] * (a['target']-a['initial'])/a['efficiency']
        if energy > a['maximum_power'] * a['n'] * a['dt'] + 1e-9:
            reasons.append('energy exceeds assumed power/window capacity')
        details.append(dict(session_id=r['session_id'], case=r['case'], status=r['status'],
            original_saved_reason=r['reason'], review_explanation='; '.join(reasons) or 'requires review of saved status/scenario',
            assumed_initial_soc_pct=a['initial']*100, derived_target_soc_pct=a['target']*100,
            assumed_maximum_soc_pct=a['maximum_soc']*100,
            recorded_delivered_kwh=byid[r['session_id']]['kWhDelivered']))
    reason_rows = [dict(reason=k, candidate_count=v, denominator=len(ledger),
                        counting_rule='Reasons overlap; do not add them to obtain excluded candidate count')
                   for k,v in sorted(reason_counts.items())]
    decisions = [dict(session_id=r['session_id'], selected_addition=r['selected_addition'],
        decision='selected_addition' if r['selected_addition'] else 'not_eligible_as_addition' if r['screening_reasons'] else 'eligible_not_selected',
        logged_reasons='; '.join(r['screening_reasons'])) for r in ledger]
    output.mkdir(parents=True, exist_ok=True)

    def export(name, rows):
        path = output / name
        if path.resolve() in {(study / n).resolve() for n in names}:
            raise ValueError('Cannot overwrite study inputs')
        if not rows:
            return
        with path.open('w', newline='', encoding='utf-8') as stream:
            w = csv.DictWriter(stream, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    export('data_quality_summary.csv', summary)
    export('candidate_screening_reasons.csv', reason_rows)
    export('candidate_decisions.csv', decisions)
    export('scenario_availability_by_soc.csv', breakdown)
    export('scenario_exclusion_details.csv', details)
    for name, before in hashes.items():
        if hashlib.sha256((study / name).read_bytes()).hexdigest() != before:
            raise RuntimeError(f'Study input changed: {name}')
    manifest = dict(source_directory=str(study), input_sha256=hashes,
                    optimizer_executed=False, original_study_inputs_unchanged=True,
                    reason_counts_overlap=True, scope='Summary of frozen evidence, not independent solver/model validation')
    (output / 'data_quality_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Candidate ledger: {len(ledger)}; eligible {eligible}; selected additions {len(additions)}; not eligible {excluded_candidates}.')
    print(f'Cohort: {len(cohort)} sessions; timing-flagged {sum(bool(v) for v in flags.values())}.')
    print(f'Completed real scenarios: {len(cases)}; infeasible {len(infeasible)}; successful real schedules {len(real)}.')
    print(f'Tables written to {output}. No optimizer runs or source edits.')


if __name__ == '__main__':
    main()
