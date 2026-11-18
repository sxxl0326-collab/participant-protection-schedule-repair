"""Recount frozen computational design details; standard library, no solver."""
from pathlib import Path
from zipfile import ZipFile
from collections import Counter
import csv,gzip,io,json

ROOT=Path(__file__).resolve().parent
with ZipFile(ROOT/'data/saved_results.zip') as z:
    factorial=json.loads(gzip.decompress(z.read('supplement/v24_projection.json.gz')))
    poisson=json.loads(z.read('supplement/v23_poisson_summary.json'))
    pairs=json.loads(z.read('supplement/v27_pair_compatibility.json'))
    diagnostics=list(csv.DictReader(io.StringIO(z.read('supplement/v25_refusal_diagnostics.csv').decode('utf-8-sig'))))
    common=json.loads(z.read('supplement/v29_evidence.json'))['common_optimal']

accepted=attempts=replaced=least_recent_checks=0
intersection=[]
for mid,model in sorted(factorial.items()):
    mask=[]
    for day in model['days']:
        accepted+=1;candidate=day['event']['candidate']
        attempts+=candidate+1;replaced+=candidate>0
        for arm in ('NoRequest','AcceptedRequests'):
            q=day['arms'][arm]['LeastRecent'];last=q['last_before'];n=len(last);o=day['event']['worker']
            expected={str(w):0 if w==o else (last[w]+1)*(n*n+1)+w for w in range(n)}
            assert q['weights']==expected
            adopted=set(q['witness']['affected'])-{o}
            assert q['last_after']==[day['day'] if w in adopted else last[w] for w in range(n)]
            if day['day']==0:assert last==[-1]*n
            least_recent_checks+=1
        if all(day['arms']['AcceptedRequests'][p]['status']=='OPTIMAL' for p in ('Random','RoundRobin','LeastRecent','Linear')):mask.append(day['day'])
    saved=next(r for r in common['rows'] if r['model']==mid)
    assert mask==saved['day_mask'];intersection.extend((mid,d) for d in mask)
assert (accepted,attempts,replaced)==(1000,1012,8)
assert len(intersection)==977

eligible=[r for r in poisson['rows'] if (r.get('structure') or {}).get('complete') and r['structure']['k']>=2]
assert len(eligible)==35
counts=Counter()
for r in eligible:
    assert len(r['boundary'])==6
    for q in r['boundary']:
        kind='at' if q['size']==q['capacity'] else 'above'
        assert q['size'] in (q['capacity'],q['capacity']+1)
        counts[kind]+=1;counts[kind+'_infeasible']+=q['status']=='INFEASIBLE'
assert counts=={'at':105,'at_infeasible':54,'above':105,'above_infeasible':105}
assert pairs['models']==14 and pairs['totals']==dict(pairs=40542,compatible=19830,incompatible=20701,unknown=11)
assert all(r['pairs']==r['flexible']*(r['flexible']-1)//2 for r in pairs['rows'])
B={i for i,r in enumerate(diagnostics) if r['B'] in ('OPTIMAL','FEASIBLE')}
EB={i for i,r in enumerate(diagnostics) if r['EB'] in ('OPTIMAL','FEASIBLE')}
assert len(B)==22 and len(EB)==35 and B<=EB
assert sum(r['H'] in ('OPTIMAL','FEASIBLE') for r in diagnostics)==2
screen=json.loads((ROOT/'docs/evidence/frozen_workday_screening.json').read_text(encoding='utf-8'))
assert len(screen['failed_attempts'])==12 and all(q['status']=='C_UNPROVED' for q in screen['failed_attempts'])
assert len({(q['model'],q['day']) for q in screen['failed_attempts']})==8
report=dict(status='PASS',solver_calls=0,accepted_events=accepted,attempted_candidates=attempts,
            replaced_days=replaced,unproved_attempts=attempts-accepted,least_recent_weight_checks=least_recent_checks,
            common_optimal_days=len(intersection),poisson_complete_boundary_maps=len(eligible),boundary=dict(counts),
            affected_pairs=pairs['totals'],caps_only_successes=len(B),caps_plus_freezes_total_successes=len(EB),
            scope='Saved design/count/weight checks. Solver statuses are not independently reproved.')
output=ROOT/'reproduced_archival';output.mkdir(exist_ok=True)
(output/'design_details.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
