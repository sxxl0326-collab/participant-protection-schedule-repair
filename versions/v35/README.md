# Participant protection evidence v35

Evidence ID: **PP-SR-20261101-v35**, 2026-11-01.

This package binds the six-page working manuscript to its saved computational
evidence. Author samples remain in the working manuscript at the author's request.
It reports computational simulations; it makes no user-study or perceived-fairness claim.

## Verify saved evidence offline

Extract the ZIP into a new directory and run with Python 3.10 or later:

```sh
python -B verify.py
```

The final line must contain `"status": "PASS"`. Only the Python standard library
is needed. The entry checks file hashes/template parts, then independently
replays positive schedules, requests, impacts, adopted histories and objective
arithmetic for Tables II/III and all five closed-loop policies. It makes no new
solver calls and does not validate external UNSAT or optimality proof traces.

## Regenerate the table values

```sh
python -B recompute_tables.py --output reproduced_tables
```

Outputs are `table_II.csv`, `table_III.csv`, `table_IV_closedloop.csv` and
`verification.json`. The closed-loop CSV includes delivered/refused/UNKNOWN,
actual C/G, concessions, maximum count, cumulative shift, recorded stage seconds,
selected statuses and raw solver statuses. First/Random/Burden-aware costs are
from their archived batch; recency/rotation costs are from the new batch.
Those times exclude archived setup proofs and are not a controlled speed test.

## Fresh optimization is a different operation

`verify.py` and `recompute_tables.py` inspect saved runs. They do not rerun the
experiments. Frozen extension rules, source, bootstrap seed and input identities
are in `supplement/own_history_protocol_v35.json`,
`supplement/own_history_source_v35.py`, `supplement/analyze_closedloop_source_v35.py`
and `supplement/closedloop_summary_v35.json`. Fresh optimization needs the original
project layout and documented OR-Tools 9.11 environment; the project command is
`python -m study_v35.own_history run`, followed by `python -m study_v35.analyze`.
Time-limited fresh runs may return different incumbents/statuses. The supported
self-contained route in this archive is saved-evidence replay, not reconstruction
of the complete historical computing environment.

## Important scopes

- The 977-day check recounts saved trajectories; original prior histories remain.
- The 82.7% idealized uniform-subset reference averages the same 278 requests
  used for the observed Random value 240/278; actual random-objective search is
  not assumed to sample feasible subsets uniformly.
- Own-history policies have their own requests and may adopt different C/G.
- UNKNOWN is not a refusal; independent arithmetic obstructions cover only a
  subset of solver-confirmed refusals.
- The MSLIB release identity, upstream citation and input manifests are retained.
  Third-party rights remain with their owners; no new licence is implied.

The package excludes questionnaire materials and individual participant records.
AI assistance is disclosed in the manuscript. This package does not constitute
a conference submission or confirmation of anonymity/camera-ready requirements.
