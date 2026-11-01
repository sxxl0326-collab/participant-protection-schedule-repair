"""Recompute saved Tables II–IV in a clean directory, without solver calls."""
from pathlib import Path
from zipfile import ZipFile
from collections import Counter
from statistics import mean
import argparse,json,csv,tempfile,subprocess,sys,os,importlib.util

H=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def safe_extract(archive,directory):
    root=directory.resolve()
    with ZipFile(archive) as z:
        for info in z.infolist():
            target=(root/info.filename).resolve()
            assert target.is_relative_to(root),info.filename
        z.extractall(root)
def write_csv(path,header,rows):
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f);w.writerow(header);w.writerows(rows)
def main(output):
    output=Path(output).resolve();output.mkdir(parents=True,exist_ok=True)
    names=['First','Random','RoundRobin','LeastRecent','Linear']
    base=read(H/'computational_evidence/BASE_EVIDENCE.json')
    with tempfile.TemporaryDirectory(prefix='ppsr_saved_') as td:
        root=Path(td);safe_extract(H/'computational_evidence'/base['archive'],root);S=root/'supplement'
        env=os.environ.copy();env.pop('PYTHONPATH',None);env['PYTHONNOUSERSITE']='1'
        reports={}
        for name in ['verify_v24.py','verify_v29.py']:
            result=subprocess.run([sys.executable,'-B',str(S/name)],cwd=S,env=env,capture_output=True,text=True,encoding='utf-8')
            (output/(name+'.stdout.txt')).write_text(result.stdout,encoding='utf-8')
            assert result.returncode==0,(name,result.stderr)
            reports[name]=json.loads(result.stdout.strip().splitlines()[-1])
            assert reports[name]['status']=='PASS'
        summary=read(S/'v24_factorial_summary.json');controls=read(S/'v29_evidence.json')
        rows=[]
        for p in names:
            q=controls['proportions'][p]
            rows.append([p,summary['means']['NoRequest'][p]['max_I'],summary['means']['AcceptedRequests'][p]['max_I'],
                         q['history_n'],q['history_acceptable'],q['history_fraction'],887-q['history_n'],
                         q['uniform_n'],q['uniform_acceptable'],q['uniform_fraction']])
        write_csv(output/'table_II.csv',['policy','no_request_max_I','enforced_max_I','natural_history','acceptable_history',
                  'natural_history_fraction','additional_history','natural_uniform','acceptable_uniform','natural_uniform_fraction'],rows)
        rows=[]
        for p in names:
            q=summary['means']['AcceptedRequests'][p]
            states=dict(sum((Counter(r['arms']['AcceptedRequests'][p]['states']) for r in summary['rows']),Counter()))
            rows.append([p,*[q[k] for k in ['max_I','sd','gini','distinct','max_shift']],json.dumps(states,sort_keys=True)])
        write_csv(output/'table_III.csv',['policy','max_I','SD','Gini','distinct_impacted','max_shift','saved_statuses'],rows)
        spec=importlib.util.spec_from_file_location('verify_closedloop_v35',H/'supplement/verify_closedloop_v35.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        reports['closedloop']=module.run(H/'supplement/closedloop_records_v35.json.gz',
                                         H/'supplement/closedloop_summary_v35.json',S/'v24_witness_check.py')
        own=read(H/'supplement/closedloop_summary_v35.json')
        rows=[]
        for p in names:
            q=own['policies'][p]
            rows.append([p,*[q[k] for k in ['delivered','refusals','unknown','C','G','concession_days','mean_max_I','mean_max_shift','seconds']],
                         json.dumps(q['states'],sort_keys=True),json.dumps(q['raw_states'],sort_keys=True)])
        write_csv(output/'table_IV_closedloop.csv',['policy','delivered','refusals','unknown','C','G','concession_days',
                  'mean_max_I','mean_max_shift','recorded_stage_seconds','selected_statuses','raw_solver_statuses'],rows)
        result=dict(status='PASS',source='Saved schedules, requests, histories and solver statuses',
                    solver_calls=0,table_files=['table_II.csv','table_III.csv','table_IV_closedloop.csv'],
                    independent_checks=reports,
                    scope='Positive schedules/history/objective arithmetic checked; saved negative/optimal statuses are not independent proof traces. Confidence-interval code and seeds are supplied separately; this entry replays schedules and regenerates table values.')
        (output/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'status':'PASS','solver_calls':0,'output':str(output),'closedloop_policy_days':reports['closedloop']['policy_days']}))
        return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',default=str(H/'reproduced_tables'));args=ap.parse_args();main(args.output)
