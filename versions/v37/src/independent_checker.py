"""Independent physical and impact arithmetic; no solver imports."""
def check(item,td,outages,witness,C=None,G=None,P=(),A=()):
 d,old,plan=item['d'],item['original'],witness['plan'];starts=plan['start'];crews=plan['allocation']
 assert len(starts)==len(crews)==d['n'] and starts[0]==0
 occupied=[[] for _ in range(d['workers'])];affected=set();changed=0
 for a,(start,crew) in enumerate(zip(starts,crews)):
  duration=d['duration'][a];end=start+duration
  assert isinstance(start,int) and 0<=start and end<=item['deadline'] and end<=starts[-1]
  assert len({w for w,s in crew})==len(crew)
  assigned=[0]*d['skills']
  for w,s in crew:
   assert isinstance(w,int) and isinstance(s,int) and 0<=w<d['workers'] and 0<=s<d['skills'] and d['workforce'][w][s]
   assigned[s]+=1
   if duration:
    occupied[w].append((start,end))
    for outage in outages:
     if w==outage['worker']:assert end<=outage['start'] or start>=outage['end']
  assert assigned==d['demands'][a]
  for b in d['successors'][a]:assert end<=starts[b]
  if old['start'][a]<td:assert start==old['start'][a] and sorted(crew)==sorted(old['allocation'][a])
  elif a!=0:assert start>=td
  before,after={tuple(x) for x in old['allocation'][a]},{tuple(x) for x in crew}
  affected.update(w for w,s in before.symmetric_difference(after))
  if start!=old['start'][a]:affected.update(w for w,s in before|after)
  changed+=bool(duration and (start!=old['start'][a] or before!=after))
 for busy in occupied:
  busy.sort();assert all(x[1]<=y[0] for x,y in zip(busy,busy[1:]))
 assert witness['c']==changed and witness['g']==len(affected) and witness['affected']==sorted(affected)
 if C is not None:assert (changed,len(affected))==(C,G)
 assert not set(P)&affected and set(A)<=affected
 return affected

def shift(item,w,o):
 d,old=item['d'],item['original'];new=w['plan'];v=[0]*d['workers']
 for a in range(d['n']):
  if not d['duration'][a]:continue
  # Retention is a worker/activity pair, even if its skill role changed.
  before={v[0] for v in old['allocation'][a]};after={v[0] for v in new['allocation'][a]}
  for worker in before&after:
   if worker!=o:v[worker]+=abs(new['start'][a]-old['start'][a])
 return v

def gin(v):
 n=len(v);s=sum(v)
 return sum((2*i-n-1)*x for i,x in enumerate(sorted(v),1))/(n*s) if s else 0.
