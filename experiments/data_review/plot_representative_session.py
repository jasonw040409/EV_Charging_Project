"""Task 4, figure 1: presentation exports from frozen trajectories, no solves.

Run: .venv/bin/python experiments/data_review/plot_representative_session.py
"""
import argparse
import hashlib
import json
import os
from datetime import timedelta
from email.utils import parsedate_to_datetime as parse
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.mplconfig'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

METHODS = {
    'immediate': ('Immediate', 'tab:blue', '-', 1.8),
    'cost_only': ('Cost-only', 'tab:orange', '--', 2.4),
    'power_penalty': ('Power penalty', 'tab:green', '-', 1.4),
    'combined': ('Combined', 'tab:red', '-', 1.8),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study-dir', default='results/nov18')
    parser.add_argument('--case', default='real_1_soc60')
    parser.add_argument('--output-dir', default='results/data_review_nov21/figures')
    parser.add_argument('--pdf-dir', default='output/pdf/data_review_nov21')
    parser.add_argument('--slide', action='store_true', help='Concise 16:9 slide version; retains detailed caption separately')
    args = parser.parse_args()
    study, output, pdf_dir = [(ROOT / p).resolve() for p in
                              [args.study_dir, args.output_dir, args.pdf_dir]]
    names = ['trajectories.json', 'metrics.json', 'cohort.json']
    hashes = {n: hashlib.sha256((study / n).read_bytes()).hexdigest() for n in names}
    trajectories, metrics, cohort = [json.loads((study / n).read_text()) for n in names]
    traces = [r for r in trajectories if r['case'] == args.case]
    scores = [r for r in metrics if r['case'] == args.case]
    if len(traces) != 4 or len(scores) != 4:
        raise ValueError('Need exactly four saved trajectories and metric records')
    traces = {r['method']: r for r in traces}
    scores = {r['method']: r for r in scores}
    if set(traces) != set(METHODS) or set(scores) != set(METHODS):
        raise ValueError('Unexpected method set')
    first = traces['immediate']
    sid = first['session_id']
    raw = next(r for r in cohort if r['sessionID'] == sid)
    zone = ZoneInfo(raw['timezone'])
    start = parse(raw['connectionTime']).astimezone(zone)
    end = parse(raw['disconnectTime']).astimezone(zone)
    scenario = scores['immediate']['scenario']
    dt = first['interval_hours']
    times = [start + timedelta(hours=i * dt) for i in range(len(first['soc']))]
    if abs((times[-1]-end).total_seconds()) > 1e-5:
        raise ValueError('Trajectory does not span recorded connection window')
    for method, r in traces.items():
        if r['session_id'] != sid or r['interval_hours'] != dt or scores[method]['scenario'] != scenario:
            raise ValueError('Compared inputs differ')
        if len(r['power_kw']) + 1 != len(r['soc']) or len(r['soc']) != len(times):
            raise ValueError('Malformed trajectory')
        np.testing.assert_allclose(r['price_dollars_per_kwh'], first['price_dollars_per_kwh'], atol=0, rtol=0)
        np.testing.assert_allclose(np.diff(r['soc']), np.array(r['power_kw']) * dt * scenario['efficiency'] / scenario['capacity'], atol=1e-10)
        if abs(sum(r['power_kw'])*dt-raw['kWhDelivered']) > 1e-6:
            raise ValueError('Recorded energy mismatch')
        if abs(r['soc'][-1]-scenario['target']) > 1e-8:
            raise ValueError('Departure target mismatch')
    plt.style.use('default')
    plt.rcParams.update({'font.size': 12, 'axes.labelsize': 12,
                         'xtick.labelsize': 11, 'ytick.labelsize': 11,
                         'pdf.fonttype': 42, 'ps.fonttype': 42})
    fig, axes = plt.subplots(3, 1, figsize=(14, 7.875) if args.slide else (14, 9),
                             sharex=True, gridspec_kw={'height_ratios': [.8, 1.6, 1.7]})
    fig.subplots_adjust(left=.085, right=.975, bottom=.10, top=.91, hspace=.18)
    label = 'S2' if args.case == 'real_1_soc60' else args.case
    fig.suptitle(f'{label} charging schedules (assumed initial SOC: {scenario["initial"]:.0%})',
                 fontsize=16, fontweight='normal', y=.975)
    axes[0].stairs(first['price_dollars_per_kwh'], times, baseline=None,
                   color='black', linewidth=1.5)
    axes[0].set_ylabel('Price\n($/kWh)')
    axes[0].set_yticks([.15, .30]); axes[0].set_ylim(.10, .35)
    for method, (name, color, style, width) in METHODS.items():
        r = traces[method]
        axes[1].stairs(r['power_kw'], times, baseline=None, label=name,
                       color=color, linestyle=style, linewidth=width)
        axes[2].plot(times, np.array(r['soc'])*100, color=color, linestyle=style, linewidth=width)
    axes[1].set_ylabel('Grid power\n(kW)')
    axes[1].set_ylim(-.1, scenario['maximum_power']*1.14)
    axes[1].set_yticks([0, 2, 4, 6])
    axes[2].set_ylabel('Assumed SOC\n(%)')
    axes[2].axhline(scenario['reference_soc']*100, color='0.4', ls=':', lw=1.2)
    axes[2].annotate(f"{scenario['reference_soc']:.0%} penalty threshold",
                     xy=(times[-1], scenario['reference_soc']*100), xytext=(-8, 6),
                     textcoords='offset points', ha='right', va='bottom',
                     fontsize=11, color='0.3')
    axes[2].set_ylim(scenario['initial']*100-.8, scenario['target']*100+1.2)
    axes[2].set_xlabel(f'Local clock time ({start:%Z})', labelpad=9)
    axes[2].xaxis.set_major_locator(mdates.HourLocator(byhour=range(7, 19, 2), tz=zone))
    axes[2].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz=zone))
    for ax in axes:
        ax.set_xlim(times[0], times[-1])
        ax.grid(True, color='0.85', linewidth=.6, alpha=.7)
        ax.set_axisbelow(True)
    axes[1].legend(loc='upper right', ncol=2, fontsize=11, frameon=True, fancybox=False)
    output.mkdir(parents=True, exist_ok=True); pdf_dir.mkdir(parents=True, exist_ok=True)
    stem = 's2_soc60_schedules' if args.case == 'real_1_soc60' else args.case + '_schedules'
    if args.slide:
        stem += '_slide'
    png, pdf = output / (stem + '.png'), pdf_dir / (stem + '.pdf')
    fig.savefig(png, dpi=220, facecolor='white')
    fig.savefig(pdf, facecolor='white')
    plt.close(fig)
    a, b = scores['power_penalty'], scores['combined']
    caption = (f"For session {sid}, all four simulated methods deliver the recorded {raw['kWhDelivered']:.3f} grid kWh "
               f"within its original connection window. Starting SOC is assumed to be {scenario['initial']:.0%}, "
               f"with a derived target of {scenario['target']:.4%}. Combined optimization reduces the high-SOC "
               f"score from {a['high_soc_proxy']:.6f} to {b['high_soc_proxy']:.6f} relative to power-only, "
               f"while increasing peak grid power from {a['peak_kw']:.3f} to {b['peak_kw']:.3f} kW. "
               f"Both cost approximately ${b['cost_dollars']:.5f} under synthetic prices. "
               "The 70% threshold is illustrative; these results do not establish measured battery-health improvement. "
               "Scientific interpretation remains pending independent review.")
    # The caption describes the fixed representative case; require the known settings.
    if args.case != 'real_1_soc60':
        caption = f'Session {sid}; case {args.case}. Frozen simulated schedules; assumed SOC and synthetic prices. Review case-specific tradeoffs before use.'
    (output / (stem + '_caption.txt')).write_text(caption + '\n')
    for n, h in hashes.items():
        if hashlib.sha256((study / n).read_bytes()).hexdigest() != h:
            raise RuntimeError('Study input changed while plotting')
    manifest = dict(case=args.case, session_id=sid, slide_version=args.slide, study_directory=str(study), input_sha256=hashes,
        outputs=dict(png=str(png), pdf=str(pdf)), checks='PASS: common settings/prices, saved dynamics, energy, target and exact window',
        optimizer_executed=False, original_inputs_unchanged=True,
        visual_review='Must inspect exported PNG and rendered PDF after generation',
        caption=caption)
    (output / (stem + '_manifest.json')).write_text(json.dumps(manifest,indent=2)+'\n')
    print(png); print(pdf)


if __name__ == '__main__':
    main()
