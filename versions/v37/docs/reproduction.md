# Reproduction guide

## Saved-result replay

Run `python -B verify.py` from `versions/v37`. The entry checks file hashes, safely extracts
`data/saved_results.zip` into a temporary directory, and runs three independent replay
checks. It does not modify the reference archive.

| Evidence | Saved source inside the archive | Check |
| --- | --- | --- |
| Matched two-arm/five-policy experiment | `supplement/v24_projection.json.gz` and the v19/v23 source projections | `verify_v24.py` checks 10,000 policy-days, witnesses, objectives and burden updates |
| Uniform-request controls and common-optimal sensitivity | `supplement/v29_evidence.json`, shared pools and joint-request records | `verify_v29.py` checks positive schedules, saved negative-status dominance and capacity arithmetic |
| Own-history closed loop | `supplement/closedloop_records_v35.json.gz` | `verify_closedloop_v35.py` checks 5,000 policy-days, generated requests, menu order, adopted witnesses and history updates |

The regenerated CSVs must equal the reference Table II, III and IV files byte-for-byte.
Reports retain the provenance and scope of each check. In particular, replaying a saved
`OPTIMAL` or `INFEASIBLE` status does not produce an independent solver proof trace.

## Fresh optimization

`demo.py` uses the same repair query engine and original metric helper functions. It
proves the first two lexicographic objectives before making optimum-relative queries.
Every returned repair is also checked by `src/independent_checker.py`.

The `Repair` class exposes `query_protect(P)`, `query_affect(w)`, `query_cost(P)`,
`protection_map()`, `solve_tiebreak(weights)` and `enumerate_affected_sets(cap)`.
Use zero-based worker indices when calling these Python methods. For Burden-aware
selection, the weight of a non-outage worker is `1 + I[w]`, where `I[w]` is their previous
non-outage impact count.

The supplied demo is a fresh solve on one event, not a full-batch reproduction command.
Runtime limits can change proof completion and selected schedules across machines. The
archive preserves the measured runs used in the tables; do not substitute fresh outcomes
into those tables without regenerating the whole comparison.

## Supporting numerical evidence

The same data archive also contains Hall/precedence examples and refusal diagnostics,
the scale summary, two-outage compatibility records, the Poisson structural stress-test
summary, the four-event cost pilot, common-pool results and offline bounds. These retain
their original experiment identifiers. They are supporting records; the top-level
verification command specifically regenerates Tables II–IV and runs the checks listed
above. `artifact.json` lists every public archive member.

## Reuse and data rights

The project uses public MSLIB model inputs and synthetic scheduling events. Their upstream
rights are unchanged. See `data.md` for the source tag, selection list and archive identity.
No license is inferred merely from public accessibility.
