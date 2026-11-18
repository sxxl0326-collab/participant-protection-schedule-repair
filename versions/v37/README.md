# Reproduce the schedule-repair experiments

[Project home](../../README.md) · [Figure and table index](docs/reproduction.md#figure-and-table-index) · [Experimental design](docs/experimental_design.md) · [Data provenance](docs/data.md)

This guide covers two workflows. Saved-result replay checks the data behind the reported results. A fresh query runs the solver on a supplied example and returns a new outcome.

## Get the fixed snapshot

```sh
git clone --branch v1.0.1-code-data --single-branch https://github.com/sxxl0326-collab/participant-protection-schedule-repair.git
cd participant-protection-schedule-repair/versions/v37
```

For a download without Git, use **Source code (zip)** on the [release page](https://github.com/sxxl0326-collab/participant-protection-schedule-repair/releases/tag/v1.0.1-code-data), and open a terminal in `versions/v37`.

## Verify saved results

Use Python 3.10+. Requirements for replay are covered by the standard library.

```sh
python -B verify.py
python -B verify_design_details.py
```

| Command | Expected output |
| --- | --- |
| `verify.py` | `"status": "PASS"`, `"solver_calls": 0`, three verified CSVs and `reproduced/verification.json` |
| `verify_design_details.py` | `"status": "PASS"`, `"solver_calls": 0`, and `reproduced_archival/design_details.json` |
| `archival_checks.py` (optional) | Saved requester-group and additive hybrid-cost summaries |

The [reproduction guide](docs/reproduction.md#saved-result-replay) describes which checks replay feasible schedules, histories, aggregate tables, and recorded solver statuses.

## Run a new query

Use Python with [OR-Tools 9.11.4210](requirements.txt) available. The supplied example uses one CPU worker.

```sh
python -m pip install -r requirements.txt
python -B demo.py --protect W8
python -B demo.py --protect W8 W11 --map --output protection_map.json
```

The input is a [synthetic event](data/example_set4_1335.json) on MSLIB model `set4_1335`. Command-line worker labels are one-based (`W8`). Saved indices are zero-based. The solver first minimizes changed activities, then affected workers. It tests the requested duties at ordered increases `(0,0), (0,1), (1,0), (1,1)` and stops at the first independently checked repair.

The default output is `demo_output.json`. It contains setup status and, once the stability optima have been proved, the response at each menu entry tried and a schedule for any successful response. `--map` also queries individual protection states. If setup remains unproved, the example stops before making an optimum-relative protection claim. A query timeout is recorded as `UNKNOWN`.

The default limit is 4 s per solver call, including model construction. Use `--seconds 20` for more time. The example uses seed 41.

## Browse the files

| Path | Contents |
| --- | --- |
| [demo.py](demo.py), [src/engine.py](src/engine.py) | Example and CP-SAT repair model, queries and selection |
| [src/independent_checker.py](src/independent_checker.py) | Independent schedule and impact checks |
| [verify.py](verify.py), [verify_design_details.py](verify_design_details.py), [reproduce_tables.py](reproduce_tables.py) | Integrity checks, replay and table generation |
| [results/](results) | Reference CSVs |
| [data/saved_results.zip](data/saved_results.zip), [artifact.json](artifact.json), [SHA256SUMS.txt](SHA256SUMS.txt) | Evidence archive, member list and file hashes |

Saved policy labels `Linear`, `RoundRobin` and `LeastRecent` correspond to **Burden-aware**, **Round-robin** and **Least-recent**. The original labels and CSV filenames are retained for traceability.
