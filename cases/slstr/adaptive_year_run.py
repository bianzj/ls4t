"""Run one SLSTR region/year with disk-aware worker selection.

The decision applies at year boundaries. It never changes a live process pool.
"""

import argparse
import json
import os
from pathlib import Path
import signal
from statistics import median
import subprocess
import sys
import time


def disk_busy_ms(device):
    for line in Path('/proc/diskstats').read_text().splitlines():
        fields = line.split()
        if fields[2] == device:
            return int(fields[12])
    raise RuntimeError(f'Disk {device} is absent from /proc/diskstats')


def available_gib():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1]) / 1024**2
    return 0.0


def history(path, region, stage):
    if not path.exists():
        return []
    records = []
    for line in path.read_text().splitlines():
        try:
            row = json.loads(line)
        except ValueError:
            continue
        report_path = path.parent / f"{row.get('region')}_{row.get('year')}_{row.get('stage')}.json"
        if (row.get('region') != region or row.get('stage') != stage
                or row.get('exit_code') != 0 or not valid_report(report_path, stage)):
            continue
        report = json.loads(report_path.read_text())
        report_elapsed = float(report.get('seconds' if stage == 'lst' else 'elapsed_s') or 0)
        # A later retry can replace the report at the same path. Its old timing
        # row must not become valid merely because the replacement succeeded.
        if report_elapsed <= 0 or abs(float(row.get('process_elapsed_s') or 0) - report_elapsed) > max(2, report_elapsed * .02):
            continue
        rate = float(row.get('rate') or 0)
        busy = float(row.get('disk_busy_pct') or 0)
        if len(records) >= 2 and busy < 60 and rate > 3 * median(float(x.get('rate') or 0) for x in records[-3:]):
            # Reprocessing already cached files is not a useful worker-count benchmark.
            continue
        records.append(row)
    return records


def valid_report(path, stage):
    try:
        report = json.loads(path.read_text())
    except (OSError, ValueError):
        return False
    if stage == 'lst':
        skipped = report.get('skipped', 0)
        failed = {row.get('scene') for row in report.get('failed_scenes', [])}
        return (report.get('scenes', 0) > 0 and 0 <= skipped <= report.get('max_scene_errors', 0)
                and len(failed) == skipped
                and len(report.get('updated_scenes', [])) + skipped == report['scenes']
                and all(not day.get('error') for day in report.get('days_report', [])))
    return (report.get('complete') is True and report.get('done') == report.get('queued')
            and len(report.get('errors', [])) + report.get('counts', {}).get('missing_input', 0)
                <= report.get('max_scene_errors', 0))


def choose_workers(rows, region, stage):
    if not rows:
        # The 2018 Amazon LST run at 12 workers was already observed at ~96% disk busy.
        return (10 if (region, stage) == ('amazon', 'lst') else 12), 'initial'
    last = rows[-1]
    workers = int(last['workers'])
    util = float(last.get('disk_busy_pct') or 0)
    rate = float(last.get('rate', 0))
    if len(rows) > 1:
        prev = rows[-2]
        prev_rate = float(prev.get('rate', 0))
        prev_workers = int(prev['workers'])
        if prev_rate > 0 and rate < prev_rate * 0.85 and workers != prev_workers:
            return prev_workers, 'restore_after_throughput_drop'
    if util >= 90 and workers > 8:
        return max(8, workers - 2), 'disk_busy_ge_90pct'
    if util < 70 and available_gib() >= 32 and os.getloadavg()[0] < os.cpu_count() * 0.7:
        return min(24, workers + 2), 'disk_busy_lt_70pct_with_headroom'
    return workers, 'hold'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--region', required=True)
    ap.add_argument('--stage', choices=('lst', 'components'), required=True)
    ap.add_argument('--year', type=int, required=True)
    ap.add_argument('--disk', required=True)
    ap.add_argument('--report', type=Path, required=True)
    ap.add_argument('--history', type=Path, required=True)
    ap.add_argument('command', nargs=argparse.REMAINDER)
    args = ap.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not command or '{workers}' not in command:
        ap.error('command must contain {workers}')
    rows = history(args.history, args.region, args.stage)
    workers, reason = choose_workers(rows, args.region, args.stage)
    command = [str(workers) if part == '{workers}' else part for part in command]
    print(f'ADAPT {args.region} {args.year} {args.stage}: workers={workers} reason={reason}', flush=True)
    start = time.monotonic()
    samples = []
    prior = (start, disk_busy_ms(args.disk))
    child = subprocess.Popen(command)
    try:
        while child.poll() is None:
            time.sleep(10)
            now = time.monotonic()
            busy = disk_busy_ms(args.disk)
            dt_ms = (now - prior[0]) * 1000
            samples.append(min(100.0, max(0.0, (busy - prior[1]) / dt_ms * 100)))
            prior = (now, busy)
    except KeyboardInterrupt:
        child.send_signal(signal.SIGINT)
        child.wait()
        return 130
    rc = child.wait()
    elapsed = time.monotonic() - start
    count = 0
    process_elapsed = elapsed
    try:
        report = json.loads(args.report.read_text())
        count = int(report.get('scenes' if args.stage == 'lst' else 'queued', 0))
        process_elapsed = float(report.get('seconds' if args.stage == 'lst' else 'elapsed_s') or elapsed)
    except (OSError, ValueError, TypeError):
        pass
    if rc == 0 and not valid_report(args.report, args.stage):
        rc = 3
    row = dict(region=args.region, year=args.year, stage=args.stage, workers=workers,
               reason=reason, disk=args.disk, disk_busy_pct=round(sum(samples) / len(samples), 1) if samples else None,
               disk_samples=len(samples), count=count, elapsed_s=round(elapsed, 1),
               process_elapsed_s=round(process_elapsed, 1),
               rate=round(count / process_elapsed, 3) if process_elapsed else 0, exit_code=rc,
               timestamp=time.strftime('%Y-%m-%dT%H:%M:%S%z'))
    with args.history.open('a') as file:
        file.write(json.dumps(row) + '\n')
    print(f'ADAPT RESULT {json.dumps(row)}', flush=True)
    return rc


if __name__ == '__main__':
    sys.exit(main())
