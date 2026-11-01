"""Own-history recency/rotation extension on the same 50x20 archived events."""
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
from collections import Counter
from copy import deepcopy
from statistics import mean
import argparse,json,time,importlib.util
from study_v6.sessions import load_inputs,request,oracle_response,protects
from study_v6 import common as c
from study_v4.workdays import daily_item,impacts
from study_v2.engine import Repair,check
from study_v19.joint import FaceRepair,dump

OUT=c.ROOT/'results/revision_v35_20261101/own_history'
POLICIES=('LeastRecent','RoundRobin')

def freeze():
    path=OUT/'protocol.json'
    if path.exists():
        p=c.read(path)
        for n,d in p['sources'].items():assert c.sha(c.ROOT/n)==d,n
        return p
    models=c.read(c.CORE/'workdays_protocol.json')['models']
    files=[Path(__file__),c.ROOT/'study_v19/own_history.py',c.ROOT/'study_v19/joint.py',
           c.ROOT/'study_v6/sessions.py',c.ROOT/'study_v2/engine.py',c.ROOT/'study_v4/workdays.py']
    inputs=[c.CORE/'workday_setups'/f'{m}.json' for m in models]
    p=dict(version='v35',models=models,days=20,policies=list(POLICIES),processes=4,
           query_seconds=4,selection_seconds=4,solver_seed=41,workers_per_solver=1,
           design='Exploratory extension frozen before new solves, prompted by prior-result review. Same 50 models and 1000 proved fresh-day events; no replacement or resampling. Each policy requests its own top-three non-outage workers by cumulative I, ties workerID ascending. Requests, accepted menus and actual C/G may diverge.',
           response='Reuse V20 protocol implementation: ordered caps (0,0),(0,1),(1,0),(1,1), 4s per query, UNKNOWN not refusal. Adopt checked protection witness or checked strict fallback. Then fix its actual C,G and enforce P iff a protection witness was found. Selection has its own 4s; retain checked initial witness if no no-worse candidate is returned. Every adopted non-outage impact and retained-duty shift updates own history.',
           rules={'LeastRecent':'last-impact day starts at -1; minimize sum(((last_w+1)*(n*n+1)+w)*a_w), outage weight 0; update last_w to current day for adopted non-outage impacts.',
                  'RoundRobin':'cursor starts 0; exclude outage from cyclic ring; minimize sum(rank_w*a_w), ranks 1..n-1; advance cursor after furthest-ranked adopted non-outage impact.'},
           cost_scope='Measured response+selection/check stages, archived setup proof cost excluded. Historical comparator timings came from their original batch; not a controlled speed benchmark.',
           sources={str(f.relative_to(c.ROOT)):c.sha(f) for f in files},
           inputs={str(f.relative_to(c.ROOT)):c.sha(f) for f in inputs})
    dump(path,p);return p

def weights_for(s,h,last,cursor,outage):
    n=len(h);ring=[(cursor+i)%n for i in range(n) if (cursor+i)%n!=outage]
    rank={w:i+1 for i,w in enumerate(ring)}
    weights={w:0 if w==outage else ((last[w]+1)*(n*n+1)+w if s=='LeastRecent' else rank[w]) for w in range(n)}
    return weights,ring

def run(mid):
    p=freeze();path=OUT/'models'/f'{mid}.json'
    item,manifest,ledger,_=load_inputs(mid);n=item['d']['workers']
    if path.exists():
        r=c.read(path)
        assert r['protocol_sha256']==c.sha(OUT/'protocol.json')
        if r['finished']:return mid
    else:r=dict(model_id=mid,size=item['size'],finished=False,protocol_sha256=c.sha(OUT/'protocol.json'),days=[],
                history={s:[0]*n for s in POLICIES},last={s:[-1]*n for s in POLICIES},
                cursor={s:0 for s in POLICIES},shift={s:[0]*n for s in POLICIES})
    for day in range(20):
        event=ledger['days'][day]['accepted']['event'];setup=ledger['days'][day]['accepted']['setup']
        inp=daily_item(item,manifest,event);outage=event['worker']
        if len(r['days'])==day:r['days'].append(dict(day=day,event=event,cstar=setup['cstar'],gstar=setup['gstar'],policies={}))
        row=r['days'][day]
        for s in POLICIES:
            if s in row['policies']:continue
            started=time.perf_counter();h=r['history'][s];P=request(h,outage,3)
            response={};repair=Repair(inp,seconds=4,seed=41)
            repair.cstar=setup['cstar'];repair.gstar=setup['gstar'];repair._hint=setup['witness']
            oracle_response(repair,inp,setup,P,response,lambda:None,diagnose=lambda *_:dict(status='not_requested',members=[]))
            response_seconds=time.perf_counter()-started;initial=response['selected_witness']
            weights,ring=weights_for(s,h,r['last'][s],r['cursor'][s],outage)
            ss=time.perf_counter();face=FaceRepair(inp,seconds=4,seed=41)
            face.target_c=initial['c'];face.target_g=initial['g'];face._hint=initial
            raw=face._solve(objective=weights,protected=P if response['protection_witness'] else [],fixed=False)
            assert raw['status'] not in ('INFEASIBLE','MODEL_INVALID')
            candidate=raw.get('witness');score=lambda w:sum(weights[i] for i in w['affected'])
            if candidate and score(candidate)<=score(initial):w=candidate;status=raw['status']
            else:w=initial;status='FALLBACK';assert raw['status']!='OPTIMAL'
            assert check(inp,w['plan'])==w and (w['c'],w['g'])==(initial['c'],initial['g'])
            if response['protection_witness']:assert protects(w,P)
            before=h[:];last_before=r['last'][s][:];cursor_before=r['cursor'][s]
            affected=set(w['affected'])-{outage}
            for i in affected:h[i]+=1;r['last'][s][i]=day
            if s=='RoundRobin' and affected:r['cursor'][s]=(max(affected,key=ring.index)+1)%n
            intensity=impacts(item,w,outage)
            r['shift'][s]=[a+b for a,b in zip(r['shift'][s],intensity['absolute_start_shift'])]
            row['policies'][s]=dict(P=P,history_before=before,history_after=h[:],last_before=last_before,
                cursor_before=cursor_before,response=response,weights=weights,raw=raw,status=status,witness=w,
                intensity=intensity,delivered=protects(w,P),response_seconds=response_seconds,
                selection_seconds=time.perf_counter()-ss,total_seconds=time.perf_counter()-started)
            dump(path,r)
    r['finished']=True;dump(path,r);return mid

def audit():
    p=freeze();rows=[];checked=0
    for mid in p['models']:
        r=c.read(OUT/'models'/f'{mid}.json');assert r['finished'] and len(r['days'])==20
        item,manifest,ledger,_=load_inputs(mid);n=item['d']['workers']
        h={s:[0]*n for s in POLICIES};last={s:[-1]*n for s in POLICIES};cursor={s:0 for s in POLICIES};shift={s:[0]*n for s in POLICIES}
        for day,row in enumerate(r['days']):
            event=ledger['days'][day]['accepted']['event'];setup=ledger['days'][day]['accepted']['setup']
            assert event==row['event'];inp=daily_item(item,manifest,event);outage=event['worker']
            for s,q in row['policies'].items():
                assert q['P']==request(h[s],outage,3) and q['history_before']==h[s]
                assert q['last_before']==last[s] and q['cursor_before']==cursor[s]
                class Replay:
                    def query_protect(self,*a,**k):raise AssertionError('Audit attempted a new solve')
                replay=dict(calls=deepcopy(q['response']['calls']))
                oracle_response(Replay(),inp,setup,q['P'],replay,lambda:None,diagnose=lambda *_:dict(status='not_requested',members=[]))
                assert replay==q['response']
                for call in replay['calls']:
                    found=call['result'].get('witness')
                    if found:assert check(inp,found['plan'])==found;checked+=1
                weights,ring=weights_for(s,h[s],last[s],cursor[s],outage)
                assert weights=={int(k):v for k,v in q['weights'].items()}
                w=q['witness'];assert check(inp,w['plan'])==w;checked+=1
                initial=replay['selected_witness'];assert (w['c'],w['g'])==(initial['c'],initial['g'])
                candidate=q['raw'].get('witness');score=lambda w:sum(weights[i] for i in w['affected'])
                if candidate:assert check(inp,candidate['plan'])==candidate;checked+=1
                use=candidate is not None and score(candidate)<=score(initial)
                assert w==(candidate if use else initial) and q['status']==(q['raw']['status'] if use else 'FALLBACK')
                assert q['delivered']==protects(w,q['P'])
                if replay['protection_witness']:assert q['delivered']
                affected=set(w['affected'])-{outage}
                for i in affected:h[s][i]+=1;last[s][i]=day
                if s=='RoundRobin' and affected:cursor[s]=(max(affected,key=ring.index)+1)%n
                assert h[s]==q['history_after'];ii=impacts(item,w,outage);assert ii==q['intensity']
                shift[s]=[a+b for a,b in zip(shift[s],ii['absolute_start_shift'])]
        assert h==r['history'] and last==r['last'] and cursor==r['cursor'] and shift==r['shift']
        policies={}
        for s in POLICIES:
            qs=[d['policies'][s] for d in r['days']]
            policies[s]=dict(max_I=max(h[s]),max_shift=max(shift[s]),delivered=sum(q['delivered'] for q in qs),
                refusals=sum(q['response']['status']=='menu_certified_unprotectable' for q in qs),
                unknown=sum(q['response']['status']=='unresolved_menu' for q in qs),
                C=sum(q['witness']['c'] for q in qs),G=sum(q['witness']['g'] for q in qs),
                concession_days=sum(q['response']['selected_delta_c']>0 or q['response']['selected_delta_g']>0 for q in qs),
                actual_extra_C=sum(q['witness']['c']-d['cstar'] for d,q in zip(r['days'],qs)),
                actual_extra_G=sum(q['witness']['g']-d['gstar'] for d,q in zip(r['days'],qs)),
                seconds=sum(q['total_seconds'] for q in qs),states=dict(Counter(q['status'] for q in qs)),
                raw_states=dict(Counter(q['raw']['status'] for q in qs)))
        rows.append(dict(model_id=mid,size=r['size'],policies=policies))
    summary=dict(status='PASS',models=50,days_per_policy=1000,checked_witnesses=checked,rows=rows,policies={})
    for s in POLICIES:
        summary['policies'][s]=dict(mean_max_I=mean(r['policies'][s]['max_I'] for r in rows),
            mean_max_shift=mean(r['policies'][s]['max_shift'] for r in rows),
            **{k:sum(r['policies'][s][k] for r in rows) for k in ['delivered','refusals','unknown','C','G','concession_days','actual_extra_C','actual_extra_G','seconds']},
            states=dict(sum((Counter(r['policies'][s]['states']) for r in rows),Counter())),
            raw_states=dict(sum((Counter(r['policies'][s]['raw_states']) for r in rows),Counter())))
    dump(OUT/'summary.json',summary)
    print(json.dumps({k:v for k,v in summary.items() if k!='rows'}),flush=True)
    return summary

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['freeze','run','audit']);args=ap.parse_args()
    if args.mode=='freeze':print(json.dumps(freeze()))
    elif args.mode=='audit':audit()
    else:
        p=freeze();started=time.perf_counter()
        with ProcessPoolExecutor(max_workers=4) as pool:
            for f in as_completed([pool.submit(run,mid) for mid in p['models']]):print('DONE',f.result(),flush=True)
        audit();dump(OUT/'runtime.json',dict(wall_seconds=time.perf_counter()-started,processes=4))
