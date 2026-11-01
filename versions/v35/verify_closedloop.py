"""Portable saved-trajectory audit. No solver or third-party Python package."""
from pathlib import Path
from collections import Counter
from statistics import mean
import argparse,gzip,json,hashlib,random,sys,importlib.util

def run(records_path,summary_path,checker_path):
    spec=importlib.util.spec_from_file_location('independent_checker',checker_path)
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    records=json.loads(gzip.decompress(Path(records_path).read_bytes()))
    summary=json.loads(Path(summary_path).read_text(encoding='utf-8'))
    names=['First','Random','RoundRobin','LeastRecent','Linear'];rows=[];checks=0;policy_days=0
    for mid,pkg in records.items():
        item=pkg['item'];n=item['d']['workers'];hist={s:[0]*n for s in names};last={s:[-1]*n for s in names};cursor={s:0 for s in names};shift={s:[0]*n for s in names}
        assert len(pkg['days'])==20
        for day,d in enumerate(pkg['days']):
            assert d['day']==day;event=d['event'];o=event['worker'];setup=d['setup_witness']
            helper.check(item,event['start'],[event],setup,d['cstar'],d['gstar']);checks+=1
            for s,q in d['policies'].items():
                policy_days+=1
                P=sorted((i for i in range(n) if i!=o),key=lambda i:(-hist[s][i],i))[:3]
                assert q['P']==P and q['history_before']==hist[s]
                calls=q['response']['calls'];response=q['response'];initial=response['selected_witness']
                chosen=None;expected=None
                menu=[(0,0),(0,1),(1,0),(1,1)]
                for j,call in enumerate(calls):
                    dc,dg=menu[j];assert (call['delta_c'],call['delta_g'])==(dc,dg)
                    raw=call['result'];assert raw['status'] in ['OPTIMAL','FEASIBLE','INFEASIBLE','UNKNOWN']
                    w=raw.get('witness')
                    if w:
                        assert w['c']<=d['cstar']+dc and w['g']<=d['gstar']+dg
                        helper.check(item,event['start'],[event],w,w['c'],w['g'],P);checks+=1
                    known=w or (setup if j==0 and not set(P)&set(setup['affected']) else None)
                    if raw['status']=='INFEASIBLE':assert known is None
                    if known:
                        chosen=known
                        strict=known['c']<=d['cstar'] and known['g']<=d['gstar']
                        expected='strict_protected' if strict else 'relaxed_protected'
                        assert j==len(calls)-1
                        break
                if chosen is None:
                    assert len(calls)==4;chosen=setup
                    expected='menu_certified_unprotectable' if all(x['result']['status']=='INFEASIBLE' for x in calls) else 'unresolved_menu'
                assert chosen==initial and response['status']==expected
                assert response['protection_witness']==(expected in ['strict_protected','relaxed_protected'])
                w=q['witness'];required=P if response['protection_witness'] else []
                helper.check(item,event['start'],[event],w,initial['c'],initial['g'],required);checks+=1
                assert (w['c'],w['g'])==(initial['c'],initial['g'])
                assert q['delivered']==(not set(P)&set(w['affected']))
                ring=[(cursor[s]+i)%n for i in range(n) if (cursor[s]+i)%n!=o]
                if s=='First':assert q['raw'] is None and w==initial
                else:
                    if s=='Random':
                        payload=json.dumps([2026102701,mid,day,'own_random'],sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
                        seed=int(hashlib.sha256(payload).hexdigest()[:8],16)%2147483647;rng=random.Random(seed)
                        weights={i:0 if i==o else rng.randint(1,10) for i in range(n)}
                    elif s=='Linear':weights={i:0 if i==o else 1+hist[s][i] for i in range(n)}
                    elif s=='LeastRecent':weights={i:0 if i==o else (last[s][i]+1)*(n*n+1)+i for i in range(n)}
                    else:weights={i:0 if i==o else ring.index(i)+1 for i in range(n)}
                    assert weights=={int(k):v for k,v in q['weights'].items()}
                    raw=q['raw'];candidate=raw.get('witness');score=lambda x:sum(weights[i] for i in x['affected'])
                    if candidate:
                        helper.check(item,event['start'],[event],candidate,initial['c'],initial['g'],required);checks+=1
                        assert raw['cost']==score(candidate)
                    use=candidate is not None and score(candidate)<=score(initial)
                    assert w==(candidate if use else initial)
                    assert q['status']==(raw['status'] if use else 'FALLBACK')
                delta=helper.shift(item,w,o);assert delta==q['intensity']['absolute_start_shift']
                shift[s]=[a+b for a,b in zip(shift[s],delta)]
                affected=set(w['affected'])-{o}
                for i in affected:hist[s][i]+=1;last[s][i]=day
                if s=='RoundRobin' and affected:cursor[s]=(max(affected,key=ring.index)+1)%n
                assert q['history_after']==hist[s]
        rows.append(dict(model_id=mid,policies={s:dict(max_I=max(hist[s]),max_shift=max(shift[s]),
            delivered=sum(d['policies'][s]['delivered'] for d in pkg['days']),
            refusals=sum(not d['policies'][s]['delivered'] and d['policies'][s]['response']['status']=='menu_certified_unprotectable' for d in pkg['days']),
            unknown=sum(not d['policies'][s]['delivered'] and d['policies'][s]['response']['status']!='menu_certified_unprotectable' for d in pkg['days']),
            C=sum(d['policies'][s]['witness']['c'] for d in pkg['days']),G=sum(d['policies'][s]['witness']['g'] for d in pkg['days']),
            concession_days=sum(d['policies'][s]['response']['selected_delta_c']>0 or d['policies'][s]['response']['selected_delta_g']>0 for d in pkg['days']),
            states=dict(Counter(d['policies'][s]['status'] for d in pkg['days']))) for s in names}))
    for s in names:
        expected=summary['policies'][s]
        assert expected['mean_max_I']==mean(r['policies'][s]['max_I'] for r in rows)
        assert expected['mean_max_shift']==mean(r['policies'][s]['max_shift'] for r in rows)
        for k in ['delivered','refusals','unknown','C','G','concession_days']:
            assert expected[k]==sum(r['policies'][s][k] for r in rows),(s,k)
        assert expected['states']==dict(sum((Counter(r['policies'][s]['states']) for r in rows),Counter()))
    return dict(status='PASS',models=len(rows),policy_days=policy_days,independent_schedule_checks=checks,
                no_solver_calls=True,scope='Independent positive schedule and history replay; saved solver statuses retained, not external UNSAT/optimality proof traces.')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--records',required=True);ap.add_argument('--summary',required=True);ap.add_argument('--checker',required=True);a=ap.parse_args()
    print(json.dumps(run(a.records,a.summary,a.checker)))
