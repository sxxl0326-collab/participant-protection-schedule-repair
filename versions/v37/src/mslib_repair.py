"""Unchanged checker/metric functions extracted from the experiment source."""

def check(d, sol, horizon, outage=None):
    assert len(sol['start']) == len(sol['allocation']) == d['n']
    assert sol['start'][0] == 0
    resource_intervals = [[] for _ in range(d['workers'])]
    for i, (start, crew) in enumerate(zip(sol['start'], sol['allocation'])):
        end = start + d['duration'][i]
        assert isinstance(start, int) and start >= 0 and end <= horizon
        assert end <= sol['start'][-1]
        assert len({w for w, k in crew}) == len(crew)
        counts = [0] * d['skills']
        for w, k in crew:
            assert 0 <= w < d['workers'] and 0 <= k < d['skills']
            assert d['workforce'][w][k]
            counts[k] += 1
            if d['duration'][i] > 0:
                resource_intervals[w].append((start, end))
                if outage and w == outage['worker']:
                    assert end <= outage['start'] or start >= outage['end']
        assert counts == d['demands'][i]
        for j in d['successors'][i]:
            assert end <= sol['start'][j]
    for intervals in resource_intervals:
        intervals.sort()
        assert all(a[1] <= b[0] for a, b in zip(intervals, intervals[1:]))
    return True

def metrics(d, original, solution):
    changed, affected = [], set()
    for i in range(d['n']):
        if d['duration'][i] == 0:
            continue
        if (original['start'][i] != solution['start'][i] or
            sorted(original['allocation'][i]) != sorted(solution['allocation'][i])):
            changed.append(i)
            affected.update(w for w, k in original['allocation'][i])
            affected.update(w for w, k in solution['allocation'][i])
    return dict(changed_activities=len(changed), affected_workers=len(affected),
                activity_ids=changed, worker_ids=sorted(affected))
