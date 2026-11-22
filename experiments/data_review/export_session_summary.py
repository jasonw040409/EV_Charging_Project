"""Task 1: export recorded session facts and explicitly assumed SOC targets.

Standard-library only. Reads frozen JSON; never imports/runs the optimizer.
Run from any directory: python3 /path/to/this/script.py
Use --help for alternate frozen cohorts/settings. Relative paths are repo-relative.
"""
import argparse
import csv
import hashlib
import json
import math
from datetime import timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]


def resolve(value):
    path = Path(value)
    return path.resolve() if path.is_absolute() else (ROOT / path).resolve()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def records(path):
    obj = json.loads(path.read_text())
    return obj['_items'] if isinstance(obj, dict) else obj


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cohort', default='results/nov18/cohort.json')
    parser.add_argument('--controls', default='data/acn_sessions_raw.json')
    parser.add_argument('--output-dir', default='results/data_review_nov21')
    parser.add_argument('--capacity-kwh', type=float, default=60.)
    parser.add_argument('--efficiency', type=float, default=.9)
    parser.add_argument('--initial-socs', nargs='+', type=float, default=[.3, .6, .75])
    parser.add_argument('--maximum-soc', type=float, default=.9)
    args = parser.parse_args()
    if not (math.isfinite(args.capacity_kwh) and args.capacity_kwh > 0 and
            0 < args.efficiency <= 1 and 0 < args.maximum_soc <= 1 and
            all(0 <= s <= args.maximum_soc for s in args.initial_socs)):
        parser.error('Invalid battery assumptions')
    if len(set(args.initial_socs)) != len(args.initial_socs):
        parser.error('Starting SOC assumptions must be unique')
    source, controls, output = map(resolve, [args.cohort, args.controls, args.output_dir])
    input_hashes = {str(p): digest(p) for p in {source, controls}}
    data = records(source)
    control_ids = {r['sessionID'] for r in records(controls)}
    if not data:
        raise ValueError('Empty cohort')
    seen = set()
    rows = []
    target_columns = [(s, f'derived_target_soc_pct_start_{s * 100:g}pct')
                      for s in args.initial_socs]
    for record in data:
        sid = record['sessionID']
        if not sid or sid in seen:
            raise ValueError(f'Missing/duplicate session ID: {sid}')
        seen.add(sid)
        start = parsedate_to_datetime(record['connectionTime'])
        end = parsedate_to_datetime(record['disconnectTime'])
        if start.tzinfo is None or end.tzinfo is None:
            raise ValueError(f'Timestamps require timezone: {sid}')
        seconds = (end - start).total_seconds()
        energy = float(record['kWhDelivered'])
        if seconds <= 0 or not math.isfinite(energy) or energy < 0:
            raise ValueError(f'Invalid window/energy: {sid}')
        local_zone = ZoneInfo(record['timezone'])
        stop = (parsedate_to_datetime(record['doneChargingTime'])
                if record.get('doneChargingTime') else None)
        if stop is not None and stop.tzinfo is None:
            raise ValueError(f'Charging-stop timestamp requires timezone: {sid}')
        flags = []
        if stop is None:
            flags.append('charging_stop_missing')
        elif stop < start:
            flags.append('charging_stop_before_connection')
        elif stop > end:
            flags.append('charging_stop_after_disconnect')
        row = dict(
            cohort_label=f'S{len(rows) + 1}', session_id=sid,
            raw_record_id=record.get('_id', ''), station_id=record.get('stationID', ''),
            space_id=record.get('spaceID', ''), original_control=sid in control_ids,
            source_timezone=record['timezone'],
            connection_utc=start.astimezone(timezone.utc).isoformat(),
            disconnect_utc=end.astimezone(timezone.utc).isoformat(),
            connection_local=start.astimezone(local_zone).isoformat(),
            disconnect_local=end.astimezone(local_zone).isoformat(),
            connected_hours=seconds / 3600,
            recorded_delivered_kwh=energy,
            charging_stop_local=stop.astimezone(local_zone).isoformat() if stop else '',
            timing_flags=';'.join(flags),
            user_inputs_present=record.get('userInputs') is not None,
            assumed_capacity_kwh=args.capacity_kwh, assumed_efficiency=args.efficiency,
        )
        for initial, column in target_columns:
            # Never cap/round the modeled target to make an assumption feasible.
            row[column] = 100 * (initial + args.efficiency * energy / args.capacity_kwh)
        rows.append(row)
    output.mkdir(parents=True, exist_ok=True)
    destinations = [output / 'session_summary.csv', output / 'session_summary_manifest.json']
    if any(p.resolve() in {source, controls} for p in destinations):
        raise ValueError('Output cannot overwrite an input')
    with destinations[0].open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    manifest = dict(
        session_count=len(rows), input_sha256=input_hashes,
        assumptions=dict(capacity_kwh=args.capacity_kwh, efficiency=args.efficiency,
                         initial_soc_fractions=args.initial_socs, maximum_soc=args.maximum_soc),
        derived_target_note='Hypothetical targets in percent, not measured SOC. Values are not capped at maximum SOC.',
        observed_fields_note='Delivered energy is recorded; treating it as grid-side is a modeling convention. UTC/local times describe the same events.',
        optional_input_note='user_inputs_present indicates presence only; no requested-energy value is inferred or extracted.',
        label_note='S labels preserve cohort order for this export. Join across versions using session_id, not S label.',
        timing_note='Empty timing_flags means no listed timestamp flag was detected, not proof of overall data quality.',
        export_command_settings=vars(args), optimizer_executed=False,
    )
    destinations[1].write_text(json.dumps(manifest, indent=2, allow_nan=False) + '\n')
    for path, previous in input_hashes.items():
        if digest(Path(path)) != previous:
            raise RuntimeError(f'Input changed during export: {path}')
    print(f'Exported {len(rows)} session rows to {destinations[0]}')
    print('No optimizer runs. Source JSON hashes unchanged.')


if __name__ == '__main__':
    main()
