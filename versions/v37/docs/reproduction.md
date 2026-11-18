# Reproduction guide

[Project home](../../../README.md) · [Setup and commands](../README.md) · [Experimental design](experimental_design.md) · [Data provenance](data.md)

## Figure and table index

The paths beginning with `supplement/` refer to members of the
[saved-data archive](../data/saved_results.zip). Download the fixed snapshot, then
list the members with `python -m zipfile -l data/saved_results.zip` from `versions/v37`.

| Paper item | Available material | How to inspect it |
| --- | --- | --- |
| Fig. 1 · Protocol example | [Standalone synthetic event on the same base model](../data/example_set4_1335.json) and [example code](../demo.py) | Run `python -B demo.py --protect W8` for a fresh request. This runnable event uses `set4_1335`. Its output need not match all details of the illustrated event. |
| Fig. 2 · Request outcomes and cost pilot | `supplement/v19_projection.json.gz`, `supplement/v28_request_controls.json`, and `supplement/v19_cost/summary.json` | Inspect saved request results and session timings. Cost summaries describe the four archived events. |
| Fig. 3 · Refusals and Hall example | `supplement/v23_explanations.json.gz`, `supplement/v23_explanation_comparison.json`, and `supplement/hall_example.json` | Inspect saved diagnostics, evidence coverage, and the Hall obstruction example. |
| Fig. 4 · Matched-policy outcomes | `supplement/v24_projection.json.gz`, `supplement/v25_completion_sensitivity.json`, and the [matched-policy CSV](../results/table_III.csv) | Use the saved policy trajectories for model-level comparisons. The CSV gives aggregate outcomes. |
| Table I · Core notation | [Model and query implementation](../src/engine.py) | Read the variable and query definitions in the implementation. |
| Table II · Protection and selection | [Reference CSV](../results/table_II.csv) | Run `python -B verify.py` to rebuild the table. |
| Table III · Base protection maps | `supplement/scalability_summary.csv` | Read the archived scale and classification summary. |
| Table IV · Matched policy outcomes | [Reference CSV](../results/table_III.csv) | Run `python -B verify.py` to rebuild the table. |
| Table V · Closed-loop outcomes | [Reference CSV](../results/table_IV_closedloop.csv) | Run `python -B verify.py` to rebuild the table. |

The index points to evidence records and executable checks. The standard verifier
regenerates the three reference CSVs. Figure source records can be inspected from the archive.

## Saved-result replay

Run `python -B verify.py` from `versions/v37`. The entry checks file hashes, safely extracts
`data/saved_results.zip` into a temporary directory, and runs three independent replay
checks. It does not modify the reference archive.

| Evidence | Saved source inside the archive | Check |
| --- | --- | --- |
| Matched two-arm/five-policy experiment | `supplement/v24_projection.json.gz` and the v19/v23 source projections | `verify_v24.py` checks 10,000 policy-days, witnesses, objectives and burden updates |
| Uniform-request controls and common-optimal sensitivity | `supplement/v29_evidence.json`, shared pools and joint-request records | `verify_v29.py` checks positive schedules, saved negative-status dominance and capacity arithmetic |
| Own-history closed loop | `supplement/closedloop_records_v35.json.gz` | `verify_closedloop_v35.py` checks 5,000 policy-days, generated requests, menu order, adopted witnesses and history updates |

The regenerated CSVs must equal the reference files byte-for-byte. Current manuscript
Table II maps to `table_II.csv`, Table IV to `table_III.csv`, and Table V to
`table_IV_closedloop.csv`. Table III is the base-map scale summary
(`supplement/scalability_summary.csv` inside the archive). Filenames retain legacy numbering.
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
verification command specifically regenerates the three numerical CSVs and runs the checks listed
above. `artifact.json` lists every public archive member.

## Reuse and data rights

The project uses public MSLIB model inputs and synthetic scheduling events. Their upstream
rights are unchanged. See `data.md` for the source tag, selection list and archive identity.
No license is inferred merely from public accessibility.

## Frozen design recount

`python -B verify_design_details.py` verifies the candidate indices, Least-recent weights,
977-day status intersection, Poisson request denominators, exhaustive pair totals and
combined-relaxation counts. It writes `reproduced_archival/design_details.json` and uses
no solver. The underlying saved schedules and numerical CSVs are unchanged.
