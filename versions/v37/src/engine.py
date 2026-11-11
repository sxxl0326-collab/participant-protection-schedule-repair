"""Exact own-duty flags, execution freezing, and standard lexicographic CP-SAT.

All witnesses are checked outside the solver encoding. UNKNOWN is never a denial.
"""
import copy
import time
from ortools.sat.python import cp_model
import mslib_repair as ms
import expanded_impact_study as ex


def indexed_build(item, freeze, td, history_outages):
    """Same scheduling semantics, index allocation terms once rather than scan W times."""
    d,original,h=item['d'],item['original'],item['deadline']
    m=cp_model.CpModel()
    starts=[m.new_int_var(0,h-dur,f's_{a}') for a,dur in enumerate(d['duration'])]
    m.add(starts[0]==0)
    alloc={};by_activity=[[] for _ in starts];by_person=[[] for _ in range(d['workers'])]
    intervals=[[] for _ in range(d['workers'])]
    for a in range(d['n']):
        per_worker={}
        for k,need in enumerate(d['demands'][a]):
            if not need:continue
            terms=[]
            for w in range(d['workers']):
                if not d['workforce'][w][k]:continue
                v=m.new_bool_var(f'x_{a}_{w}_{k}');alloc[a,w,k]=v;terms.append(v)
                per_worker.setdefault(w,[]).append(v)
                by_activity[a].append((w,k,v));by_person[w].append((a,k,v))
            m.add(sum(terms)==need)
        for w,terms in per_worker.items():
            y=m.new_bool_var(f'y_{a}_{w}');m.add(sum(terms)==y)
            intervals[w].append(m.new_optional_interval_var(starts[a],d['duration'][a],starts[a]+d['duration'][a],y,f'iv_{a}_{w}'))
        for b in d['successors'][a]:m.add(starts[b]>=starts[a]+d['duration'][a])
    events=([item['outage']] if item.get('outage') else [])+list(history_outages)
    for number,event in enumerate(events):
        intervals[event['worker']].append(m.new_interval_var(event['start'],event['end']-event['start'],event['end'],f'outage_{number}'))
    for ivs in intervals:m.add_no_overlap(ivs)
    changed=[];own_terms=[[] for _ in range(d['workers'])]
    for a,duration in enumerate(d['duration']):
        if not duration:continue
        old={tuple(x) for x in original['allocation'][a]}
        shifted=m.new_bool_var(f'shift_{a}')
        m.add(starts[a]!=original['start'][a]).only_enforce_if(shifted)
        m.add(starts[a]==original['start'][a]).only_enforce_if(shifted.Not())
        diffs=[shifted]
        for w,k,v in by_activity[a]:
            literal=v.Not() if (w,k) in old else v
            diffs.append(literal);own_terms[w].append(literal)
        for w,k in old:own_terms[w].append(shifted)
        ch=m.new_bool_var(f'changed_{a}');m.add_max_equality(ch,diffs);changed.append(ch)
    flags={}
    for w,terms in enumerate(own_terms):
        f=m.new_bool_var(f'own_affected_{w}');flags[w]=f
        if terms:m.add_max_equality(f,terms)
        else:m.add(f==0)
    if freeze:
        for a,v in enumerate(starts):
            if original['start'][a]<td:
                m.add(v==original['start'][a]);old={tuple(x) for x in original['allocation'][a]}
                for w,k,x in by_activity[a]:m.add(x==int((w,k) in old))
            elif a!=0:m.add(v>=td)
    return m,starts,alloc,sum(changed),sum(flags.values()),flags


def check(item, plan, freeze=True, td=None, history_outages=None):
    d, original = item['d'], item['original']
    ms.check(d, plan, item['deadline'], item.get('outage'))
    for event in history_outages or []:
        ms.check(d, plan, item['deadline'], event)
    if freeze:
        td = item['outage']['start'] if td is None else td
        for i in range(d['n']):
            if original['start'][i] < td:
                assert plan['start'][i] == original['start'][i], ('frozen start', i)
                assert sorted(plan['allocation'][i]) == sorted(original['allocation'][i]), ('frozen crew', i)
            elif i != 0:
                assert plan['start'][i] >= td, ('time lower bound', i)
    c = ms.metrics(d, original, plan)['changed_activities']
    dm = ex.direct_metrics(d, original, plan)
    return dict(plan=plan, c=c, g=dm['affected_workers'], affected=dm['worker_ids'])


class Repair:
    def __init__(self, item, freeze=True, td=None, history_outages=None, seconds=4, seed=41):
        self.item = item
        self.freeze, self.td = freeze, item['outage']['start'] if td is None else td
        self.history_outages = history_outages or []
        self.seconds, self.seed = seconds, seed
        self.cstar = item.get('cstar')
        self.gstar = item.get('gstar')
        self._template = None
        self._hint = None

    def _build(self):
        if self._template is None:
            self._template=indexed_build(self.item,self.freeze,self.td,self.history_outages)
        t,starts,alloc,C,G,flags=self._template
        m=t.clone()
        # OR-Tools expressions use stable proto indices; clones preserve these.
        # Reuse index expressions, while every new constraint lives on the clone.
        return m,starts,alloc,C,G,flags

    def _solve(self, objective=None, protected=(), affected=(), c=None, g=None,
               fixed=True, seed=None, randomize=False, blocked=()):
        begin=time.perf_counter()
        m,starts,alloc,C,G,F=self._build()
        if c is not None:m.add(C<=c)
        elif fixed:
            if self.cstar is None:raise ValueError('C* not certified')
            m.add(C==self.cstar)
        if g is not None:m.add(G<=g)
        elif fixed:
            if self.gstar is None:raise ValueError('G* not certified')
            m.add(G==self.gstar)
        for w in protected:m.add(F[w]==0)
        for w in affected:m.add(F[w]==1)
        for ids in blocked:
            ids=set(ids)
            m.add_bool_or([F[w].Not() if w in ids else F[w] for w in F])
        if objective=='C':m.minimize(C)
        elif objective=='G':m.minimize(G)
        elif isinstance(objective,dict):m.minimize(sum(v*F[w] for w,v in objective.items()))
        if self._hint is not None and not randomize:
            plan=self._hint['plan']
            for a,v in enumerate(starts):m.add_hint(v,plan['start'][a])
            for (a,w,k),v in alloc.items():m.add_hint(v,int([w,k] in plan['allocation'][a]))
        solver=cp_model.CpSolver()
        solver.parameters.num_search_workers=1
        solver.parameters.random_seed=self.seed if seed is None else seed
        solver.parameters.randomize_search=randomize
        if randomize:solver.parameters.search_branching=cp_model.RANDOMIZED_SEARCH
        remaining=self.seconds-(time.perf_counter()-begin)
        if remaining<=0:return dict(status='UNKNOWN',reason='construction_budget',seconds=time.perf_counter()-begin)
        solver.parameters.max_time_in_seconds=remaining
        code=solver.solve(m)
        row=dict(status=solver.status_name(code),seconds=time.perf_counter()-begin,seed=self.seed if seed is None else seed)
        if code in (cp_model.FEASIBLE,cp_model.OPTIMAL):
            plan=dict(start=[solver.value(v) for v in starts],allocation=[[] for _ in starts])
            for (a,w,k),v in alloc.items():
                if solver.value(v):plan['allocation'][a].append([w,k])
            witness=check(self.item,plan,self.freeze,self.td,self.history_outages)
            assert witness['c']==solver.value(C) and witness['g']==solver.value(G)
            assert all(solver.value(F[w])==int(w in witness['affected']) for w in F), 'own-duty flag must be equivalent'
            assert not set(protected)&set(witness['affected'])
            assert set(affected)<=set(witness['affected'])
            if fixed and c is None:assert witness['c']==self.cstar
            if fixed and g is None:assert witness['g']==self.gstar
            if c is not None:assert witness['c']<=c
            if g is not None:assert witness['g']<=g
            row.update(witness=witness)
            if objective is not None:
                row.update(cost=int(round(solver.objective_value)),bound=solver.best_objective_bound)
        return row

    def setup(self):
        c=self._solve('C',fixed=False)
        if c['status']!='OPTIMAL':return dict(status='C_UNPROVED',c_result=c)
        self.cstar=c['witness']['c']; self._hint=c['witness']
        # Fix C exactly for second stage, leave G unconstrained.
        g=self._solve('G',c=self.cstar,fixed=False)
        if g['status']!='OPTIMAL':return dict(status='G_UNPROVED',cstar=self.cstar,c_result=c,g_result=g)
        self.gstar=g['witness']['g']; self._hint=g['witness']
        return dict(status='OPTIMAL',cstar=self.cstar,gstar=self.gstar,c_result=c,g_result=g,witness=g['witness'])

    def query_protect(self,P,c=None,g=None):
        # Supplying only one cap keeps the other objective at its strict optimum.
        return self._solve(protected=tuple(P),c=c,g=g)

    def query_affect(self,w):return self._solve(affected=(w,))

    def query_cost(self,P,c=None,g=None):
        return self._solve(objective={w:1 for w in P},c=c,g=g)

    def solve_tiebreak(self,weights=None,seed=None,randomize=False):
        weights=None if weights is None else (dict(enumerate(weights)) if not isinstance(weights,dict) else weights)
        return self._solve(objective=weights,seed=seed,randomize=randomize)

    def protection_map(self):
        rows=[]
        for w in range(self.item['d']['workers']):
            if w==self.item['outage']['worker']:continue
            p=self.query_protect([w]); a=self.query_affect(w)
            ps=p['status'] in ('OPTIMAL','FEASIBLE'); ass=a['status'] in ('OPTIMAL','FEASIBLE')
            if p['status']=='INFEASIBLE':kind='forced'
            elif a['status']=='INFEASIBLE':kind='safe'
            elif ps and ass:kind='flexible'
            else:kind='unresolved'
            assert not(p['status']=='INFEASIBLE' and a['status']=='INFEASIBLE')
            rows.append(dict(worker=w,kind=kind,protect=p,affect=a))
        return rows

    def enumerate_affected_sets(self,cap=30):
        sets=[];calls=[]
        for _ in range(cap):
            r=self._solve(blocked=sets);calls.append({k:v for k,v in r.items() if k!='witness'})
            if r['status']=='INFEASIBLE':return dict(sets=sets,complete=True,calls=calls)
            if 'witness' not in r:return dict(sets=sets,complete=False,reason='UNKNOWN',calls=calls)
            ids=sorted(r['witness']['affected']);assert ids not in sets;sets.append(ids)
        # The cap reports a lower bound; no uncharged extra solve to imply completeness.
        return dict(sets=sets,complete=False,reason='cap',calls=calls)
