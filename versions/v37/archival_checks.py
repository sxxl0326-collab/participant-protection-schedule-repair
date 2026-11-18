"""Descriptive checks of existing synthetic records; no solver calls."""
from pathlib import Path
from zipfile import ZipFile
from statistics import mean, median
import gzip, json, hashlib, csv

ROOT=Path(__file__).resolve().parent
OUTPUT=ROOT/'reproduced_archival'; OUTPUT.mkdir(exist_ok=True)
ARCHIVE=ROOT/'data/saved_results.zip'
with ZipFile(ARCHIVE) as z:
    def read(n):
        b=z.read(n)
        return json.loads(gzip.decompress(b) if n.endswith('.gz') else b)
    factorial=read('supplement/v24_projection.json.gz')
    pilot=read('supplement/v19_projection.json.gz')['cost']

policies=('First','Random','RoundRobin','LeastRecent','Linear')
rows=[]
for mid, model in sorted(factorial.items()):
    days=model['days']; assert len(days)==20
    ever=set().union(*(set(d['P']) for d in days))
    n=len(days[0]['arms']['NoRequest']['First']['history_before'])
    never=set(range(n))-ever
    for arm in ('NoRequest','AcceptedRequests'):
        for policy in policies:
            hist=[0]*n
            for d in days:
                p=d['arms'][arm][policy]
                assert p['history_before']==hist
                for w in p['witness']['affected']:
                    if w!=d['event']['worker']:hist[w]+=1
                assert hist==p['history_after']
            rows.append(dict(model_id=mid,arm=arm,policy=policy,
                             ever_requested=len(ever),never_requested=len(never),
                             max_ever=max((hist[w] for w in ever),default=None),
                             max_never=max((hist[w] for w in never),default=None),
                             total_ever=sum(hist[w] for w in ever),total_never=sum(hist[w] for w in never)))
summary={}
for policy in policies:
    summary[policy]={}
    for arm in ('NoRequest','AcceptedRequests'):
        rr=[r for r in rows if r['policy']==policy and r['arm']==arm and r['ever_requested'] and r['never_requested']]
        summary[policy][arm]={k:mean(r[k] for r in rr if r[k] is not None) for k in ('max_ever','max_never','total_ever','total_never')}
        summary[policy][arm]['models_with_both_groups']=sum(r['ever_requested']>0 and r['never_requested']>0 for r in rr)

cost=[]
for ctx in pilot:
    r=ctx['record'];methods=r['methods'];exact=methods['Exact'];sample=methods['Sample20']
    eq=exact['requests'];sq=sample['requests'];assert len(eq)==len(sq)==20
    assert all(a['P']==b['P'] for a,b in zip(eq,sq))
    common=r['loading_seconds']+r['building_seconds']+r['proof_seconds']
    for n in (1,5,20):
        miss=[i for i,q in enumerate(sq[:n]) if not q['delivered']]
        extra=sum(eq[i]['total_request_seconds'] for i in miss)
        base=sample['prefixes'][str(n)]['total_seconds']
        assert abs(base-common-sum(q['total_request_seconds'] for q in sq[:n]))<1e-5
        cost.append(dict(model_id=r['model_id'],n=n,misses=len(miss),
                         exact_seconds=exact['prefixes'][str(n)]['total_seconds'],
                         sample_seconds=base,added_exact_recorded_seconds=extra,
                         hybrid_additive_charge_seconds=base+extra))
result=dict(status='PASS',models=len(factorial),solver_calls=0,
            data_sha256=hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),
            grouping='Fixed within each model: ever in the archived History request set over all 20 days versus never in it. Counts exclude the day\'s outage worker. Empty groups are omitted, never scored as zero. Policy histories are replayed from saved affected sets.',
            scope='Descriptive archival subgroup comparison at the same History-selected realized daily C/G. Group membership is selected by the archived First-based request history; this is not a causal estimate of harm or a human fairness measure.',
            requester_comparison=summary,
            hybrid_scope='Additive archival charge only: Sample20 recorded session cost plus recorded Exact request cost at the same missed-request indices. It preserves the original Exact stream states, so it does not time a hybrid execution, account for changed hints/caches, or establish a speed ranking.',
            pilot_hybrid_rows=cost,
            pilot_hybrid_medians={str(n):{k:median(r[k] for r in cost if r['n']==n) for k in ('exact_seconds','sample_seconds','added_exact_recorded_seconds','hybrid_additive_charge_seconds')} for n in (1,5,20)})
(OUTPUT/'archival_checks.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
with (OUTPUT/'requester_groups.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(json.dumps({k:result[k] for k in ('status','models','solver_calls','requester_comparison','pilot_hybrid_medians')}))
