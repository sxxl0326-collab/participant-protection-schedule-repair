"""Unchanged checker/metric functions extracted from the experiment source."""

def direct_metrics(d,orig,sol):
    affected=set()
    for i in range(d['n']):
        old={tuple(v) for v in orig['allocation'][i]};new={tuple(v) for v in sol['allocation'][i]}
        affected.update(w for w,k in old.symmetric_difference(new))
        if orig['start'][i]!=sol['start'][i]:
            affected.update(w for w,k in old|new)
    return dict(affected_workers=len(affected),worker_ids=sorted(affected))
