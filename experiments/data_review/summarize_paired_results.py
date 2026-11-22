"""Task 3: describe frozen real-session results with paired differences.

Standard library only. No new solves, downloads or edits to study inputs.
All changes are comparison minus reference; statistics are descriptive.
"""
import argparse
import collections
import csv
import hashlib
import json
import math
import statistics
from email.utils import parsedate_to_datetime as parse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
METHODS = ['immediate', 'cost_only', 'power_penalty', 'combined']
COMPARISONS = [('immediate', 'cost_only'), ('power_penalty', 'cost_only'),
               ('combined', 'cost_only'), ('combined', 'power_penalty')]
# Reporting tolerances classify tiny differences only; raw values are retained.
# They are not solver settings or thresholds for practical/physical significance.
METRICS = {
    'cost_dollars': ('dollars', 1e-7),
    'power_proxy': ('dimensionless', 1e-8),
    'high_soc_proxy': ('dimensionless', 1e-8),
    'peak_kw': ('kW', 1e-5),
    'calendar_increment_ppm': ('ppm of original capacity', 1e-6),
    'total_wall_seconds': ('seconds, single execution', None),
}


def percentile(values, fraction):
    values = sorted(values)
    position = (len(values) - 1) * fraction
    low = math.floor(position)
    high = math.ceil(position)
    return values[low] + (values[high] - values[low]) * (position - low)


def describe(values):
    return dict(case_count=len(values), minimum=min(values),
                q1=percentile(values, .25), median=statistics.median(values),
                q3=percentile(values, .75),
                iqr=percentile(values, .75) - percentile(values, .25), maximum=max(values))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study-dir', default='results/nov18')
    parser.add_argument('--output-dir', default='results/data_review_nov21')
    args = parser.parse_args()
    study, output = [(ROOT / p).resolve() for p in [args.study_dir, args.output_dir]]
    names = ['metrics.json', 'cohort.json', 'exclusions.json']
    hashes = {n: hashlib.sha256((study / n).read_bytes()).hexdigest() for n in names}
    saved, cohort, exclusions = [json.loads((study / n).read_text()) for n in names]
    source = {r['sessionID']: r for r in cohort}
    if len(source) != len(cohort):
        raise ValueError('Duplicate cohort session IDs')
    groups = collections.defaultdict(dict)
    for row in saved:
        if row.get('family') != 'real':
            continue
        case, method = row['case'], row['method']
        if method not in METHODS or method in groups[case]:
            raise ValueError(f'Unexpected/duplicate method in {case}')
        if row['session_id'] not in source:
            raise ValueError(f'Session not in cohort: {case}')
        for metric in METRICS:
            if not math.isfinite(row[metric]):
                raise ValueError(f'Nonfinite result in {case}: {metric}')
        if row['solver']['status'] != ('deterministic' if method == 'immediate' else 'optimal'):
            raise ValueError(f'Unsuccessful saved solve: {case}')
        groups[case][method] = row
    method_groups = collections.defaultdict(list)
    change_groups = collections.defaultdict(list)
    paired_rows = []
    scenario_keys = set()
    for case, group in groups.items():
        if set(group) != set(METHODS):
            raise ValueError(f'Incomplete four-method case: {case}')
        reference = group['cost_only']
        sid, scenario = reference['session_id'], reference['scenario']
        identity = (sid, scenario['initial'])
        if identity in scenario_keys:
            raise ValueError('Duplicate session/starting-SOC scenario')
        scenario_keys.add(identity)
        raw = source[sid]
        start, end = parse(raw['connectionTime']), parse(raw['disconnectTime'])
        stop = parse(raw['doneChargingTime']) if raw.get('doneChargingTime') else None
        timing_flag = bool(stop and not start <= stop <= end)
        quality = 'flagged_diagnostic' if timing_flag else 'clean'
        initial = scenario['initial'] * 100
        for method, row in group.items():
            if row['session_id'] != sid or row['scenario'] != scenario:
                raise ValueError(f'Physical assumptions differ within {case}')
            if bool(row['timing_flag']) != timing_flag:
                raise ValueError(f'Timing flag mismatch: {case}')
            if abs(row['grid_kwh'] - raw['kWhDelivered']) >= 1e-6:
                raise ValueError(f'Recorded energy mismatch: {case}')
            if abs(row['departure_soc'] - scenario['target']) >= 1e-8:
                raise ValueError(f'Target mismatch: {case}')
            for metric in METRICS:
                method_groups[quality, initial, method, metric].append(row[metric])
        for compared, baseline in COMPARISONS:
            for metric, (unit, tolerance) in METRICS.items():
                a, b = group[compared][metric], group[baseline][metric]
                delta = a - b
                classification = ('timing_observation_only' if tolerance is None else
                                  'lower' if delta < -tolerance else
                                  'higher' if delta > tolerance else 'within_reporting_tolerance')
                row = dict(quality_group=quality, assumed_initial_soc_pct=initial,
                    session_id=sid, case=case, comparison_method=compared,
                    reference_method=baseline, metric=metric, unit=unit,
                    comparison_value=a, reference_value=b, change=delta,
                    classification=classification,
                    reporting_tolerance='' if tolerance is None else tolerance)
                paired_rows.append(row)
                change_groups[quality, initial, compared, baseline, metric].append(row)
    method_summary = []
    for (quality, initial, method, metric), values in sorted(method_groups.items()):
        method_summary.append(dict(quality_group=quality, assumed_initial_soc_pct=initial,
            method=method, metric=metric, unit=METRICS[metric][0], **describe(values)))
    pair_summary = []
    for (quality, initial, compared, baseline, metric), values in sorted(change_groups.items()):
        counts = collections.Counter(v['classification'] for v in values)
        pair_summary.append(dict(quality_group=quality, assumed_initial_soc_pct=initial,
            comparison_method=compared, reference_method=baseline, metric=metric,
            unit=METRICS[metric][0], **describe([v['change'] for v in values]),
            lower_cases=counts['lower'], higher_cases=counts['higher'],
            within_tolerance_cases=counts['within_reporting_tolerance'],
            timing_observations=counts['timing_observation_only']))
    overview = []
    for initial in sorted({r['scenario']['initial'] for r in saved + exclusions if r.get('family') == 'real'}):
        complete = [g for g in groups.values() if g['cost_only']['scenario']['initial'] == initial]
        excluded = [r for r in exclusions if r.get('family') == 'real' and
                    r['scenario']['initial'] == initial and r['status'] == 'analytically_infeasible']
        complete_ids = {g['cost_only']['session_id'] for g in complete}
        excluded_ids = {r['session_id'] for r in excluded}
        if complete_ids & excluded_ids:
            raise ValueError('A scenario is completed and infeasible')
        clean = sum(not g['cost_only']['timing_flag'] for g in complete)
        overview.append(dict(assumed_initial_soc_pct=initial * 100,
            cohort_sessions=len(cohort), completed_cases=len(complete), clean_paired_cases=clean,
            flagged_diagnostic_cases=len(complete)-clean, analytically_infeasible_cases=len(excluded_ids),
            unaccounted_or_failed_cases=len(source.keys()-complete_ids-excluded_ids)))
    output.mkdir(parents=True, exist_ok=True)
    exports = {'method_metric_summary.csv': method_summary,
               'paired_case_changes.csv': paired_rows, 'paired_change_summary.csv': pair_summary,
               'paired_comparison_counts.csv': overview}
    for name, rows in exports.items():
        if not rows:
            raise ValueError(f'No results for {name}')
        with (output / name).open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
    for name, before in hashes.items():
        if hashlib.sha256((study / name).read_bytes()).hexdigest() != before:
            raise RuntimeError('Input changed during summarization')
    manifest = dict(input_directory=str(study), input_sha256=hashes,
        metrics={k:dict(unit=v[0],reporting_tolerance=v[1]) for k,v in METRICS.items()},
        comparisons=COMPARISONS, quantile_rule='Linear interpolation at (n-1)*q, q=0.25/0.75',
        direction='comparison minus reference; smaller cost/scores/peak is lower, not proof of health benefit',
        paired_rule='Compute differences within each session/SOC case first, then summarize differences',
        tolerance_rule='Classify small changes only; preserve raw deltas. Not a physical significance test.',
        statistical_limit='Descriptive statistics only; repeated SOC assumptions are not independent real sessions. No confidence/significance claims.',
        timing_limit='Single saved executions; cost-only has two stages. No speed ranking from timing classification.',
        clean_rule='No saved/raw charging-stop ordering flag; not proof of overall data quality',
        aging_status='Conditional calendar estimates, pending independent model review',
        optimizer_executed=False, original_study_inputs_unchanged=True)
    (output / 'paired_results_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Completed {len(groups)} cases; exported {len(paired_rows)} per-case metric differences.')
    print('No optimization runs or baseline edits. Clean/flagged groups remain separate.')


if __name__ == '__main__':
    main()
