"""Replay saved schedules and regenerate Tables II--IV, without solver calls."""
from pathlib import Path
from zipfile import ZipFile
from collections import Counter
from statistics import mean
import argparse, csv, hashlib, importlib.util, json, os, subprocess, sys, tempfile

HOME = Path(__file__).resolve().parent

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def write_csv(path, header, rows):
    with path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.writer(stream)
        writer.writerow(header)
        writer.writerows(rows)

def run(output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=True)
    config = read(HOME / 'artifact.json')
    archive = HOME / config['data_archive']
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == config['data_sha256']
    names = ['First', 'Random', 'RoundRobin', 'LeastRecent', 'Linear']
    reports = {}
    with tempfile.TemporaryDirectory(prefix='ppsr_saved_') as directory:
        root = Path(directory).resolve()
        with ZipFile(archive) as package:
            assert sorted(package.namelist()) == sorted(config['archive_files'])
            for entry in package.infolist():
                assert (root / entry.filename).resolve().is_relative_to(root)
            package.extractall(root)
        data = root / 'supplement'
        environment = os.environ.copy()
        environment.pop('PYTHONPATH', None)
        environment['PYTHONNOUSERSITE'] = '1'
        for filename in ['verify_v24.py', 'verify_v29.py']:
            result = subprocess.run([sys.executable, '-B', str(data / filename)],
                cwd=data, env=environment, capture_output=True, text=True, encoding='utf-8')
            (output / (filename + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
            assert result.returncode == 0, (filename, result.stderr)
            report = json.loads(result.stdout.strip().splitlines()[-1])
            assert report['status'] == 'PASS'
            reports[filename] = report
        summary = read(data / 'v24_factorial_summary.json')
        controls = read(data / 'v29_evidence.json')
        rows = []
        for policy in names:
            row = controls['proportions'][policy]
            rows.append([policy, summary['means']['NoRequest'][policy]['max_I'],
                summary['means']['AcceptedRequests'][policy]['max_I'],
                row['history_n'], row['history_acceptable'], row['history_fraction'],
                887-row['history_n'], row['uniform_n'], row['uniform_acceptable'], row['uniform_fraction']])
        write_csv(output / 'table_II.csv', ['policy','no_request_max_I','enforced_max_I',
            'natural_history','acceptable_history','natural_history_fraction','additional_history',
            'natural_uniform','acceptable_uniform','natural_uniform_fraction'], rows)
        rows = []
        for policy in names:
            row = summary['means']['AcceptedRequests'][policy]
            states = dict(sum((Counter(r['arms']['AcceptedRequests'][policy]['states'])
                              for r in summary['rows']), Counter()))
            rows.append([policy, *[row[k] for k in ['max_I','sd','gini','distinct','max_shift']],
                         json.dumps(states, sort_keys=True)])
        write_csv(output / 'table_III.csv', ['policy','max_I','SD','Gini','distinct_impacted',
                                          'max_shift','saved_statuses'], rows)
        spec = importlib.util.spec_from_file_location('closedloop_checker', data / 'verify_closedloop_v35.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        reports['closedloop'] = module.run(data / 'closedloop_records_v35.json.gz',
            data / 'closedloop_summary_v35.json', data / 'v24_witness_check.py')
        summary = read(data / 'closedloop_summary_v35.json')
        rows = []
        for policy in names:
            row = summary['policies'][policy]
            rows.append([policy, *[row[k] for k in ['delivered','refusals','unknown','C','G',
                'concession_days','mean_max_I','mean_max_shift','seconds']],
                json.dumps(row['states'], sort_keys=True), json.dumps(row['raw_states'], sort_keys=True)])
        write_csv(output / 'table_IV_closedloop.csv', ['policy','delivered','refusals','unknown','C','G',
            'concession_days','mean_max_I','mean_max_shift','recorded_stage_seconds',
            'selected_statuses','raw_solver_statuses'], rows)
    for name in ['table_II.csv', 'table_III.csv', 'table_IV_closedloop.csv']:
        assert (output / name).read_bytes() == (HOME / 'results' / name).read_bytes(), name
    report = {'status':'PASS', 'solver_calls':0, 'table_files':[
        'table_II.csv','table_III.csv','table_IV_closedloop.csv'], 'independent_checks':reports,
        'scope':'Checks positive schedules, impact/history arithmetic and saved result consistency. '
                'Saved INFEASIBLE/OPTIMAL statuses are not independently proved by this replay.'}
    (output / 'verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'status':'PASS','solver_calls':0,
                     'matched_policy_days':reports['verify_v24.py']['policy_days'],
                     'closedloop_policy_days':reports['closedloop']['policy_days']}))
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='reproduced')
    run(parser.parse_args().output)
