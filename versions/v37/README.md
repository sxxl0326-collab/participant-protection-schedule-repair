# Participant Protection in Stable Schedule Repair

This directory contains the code, experimental data and reproduction instructions for
participant-level protection in stable schedule repair. It is the reproducibility entry
linked from the paper.

The solver first minimizes changed activities, then affected workers. Within that repair
space, it can query whether specified workers retain their duties, classify individual
protection opportunities, or select a repair using previous impact counts.

## 1. Get the project

```sh
git clone --branch v1.0.0-code-data --single-branch https://github.com/sxxl0326-collab/participant-protection-schedule-repair.git
cd participant-protection-schedule-repair/versions/v37
```

Alternatively, use **Code → Download ZIP** on the repository homepage, extract it, and
open a terminal in `versions/v37`. All commands below run from this directory.

## 2. Verify saved results — no solver or network needed

Requires Python 3.10 or later. No third-party Python packages are needed.

```sh
python -B verify.py
```

The last JSON record should contain `"status": "PASS"` and `"solver_calls": 0`.
The checker replays saved schedules and burden histories, checks protection constraints,
and regenerates the three CSV tables into `reproduced/`. These are compared byte-for-byte
with the reference files in `results/`.

| Output | Contents |
| --- | --- |
| [Table II](results/table_II.csv) | Request/no-request ablation and incidental delivery under History and Uniform requests |
| Table III | Base protection maps: `supplement/scalability_summary.csv` inside `data/saved_results.zip` |
| [Table IV](results/table_III.csv) | Matched-request impact, displacement and saved solve statuses |
| [Table V](results/table_IV_closedloop.csv) | Own-history requests, realized C/G, concessions, impact and statuses |
| `reproduced/verification.json` | Independent replay reports and verification scope |

This command checks saved evidence. It does not re-run all optimization experiments or
independently prove recorded negative/optimal solver statuses.

The CSV filenames retain historical table numbers. The mapping above follows the current
manuscript; the notation table is not a numerical replay output.

For generation rules, seed handling and descriptive archival checks, see
[experimental_design.md](docs/experimental_design.md). Run `python -B archival_checks.py`
to reproduce the requester-group and additive hybrid-cost summaries without a solver.

## 3. Run a fresh protection query

Requires OR-Tools 9.11.4210; no GPU is needed.

```sh
python -m pip install -r requirements.txt
python -B demo.py --protect W8
python -B demo.py --protect W8 W11 --map --output protection_map.json
```

The example is a synthetic outage on the public `set4_1335` model. Its event is supplied
in [data/example_set4_1335.json](data/example_set4_1335.json). Worker labels on the command
line are one-based (`W8`); saved worker indices are zero-based. It is a runnable event
example, rather than a promise to reproduce a particular figure's outage.

Each solver call uses one worker, seed 41 and a four-second limit by default. Change the
limit with `--seconds 20`. A request is tested at `(ΔC,ΔG) = (0,0), (0,1), (1,0), (1,1)`
in that order, stopping at the first checked protection witness. The program writes the
query statuses and full schedule to `demo_output.json`. If the stability optimum is not
proved within the limit, it reports that status and stops before making optimum-relative
claims. Timeouts remain `UNKNOWN`.

## 4. Code and data layout

```text
demo.py                         Fresh CP-SAT example and bounded request response
verify.py                       File hashes and saved-result replay
reproduce_tables.py              Regenerate three numerical CSVs (legacy filenames)
src/engine.py                    Repair model, exact queries, map and tie-breaking
src/independent_checker.py       Schedule/impact checker without solver imports
src/mslib_repair.py              Original feasibility/metric helper functions
src/expanded_impact_study.py      Original own-duty impact metric
data/example_set4_1335.json      Standalone example input
data/saved_results.zip           Allowlisted saved schedules and numerical evidence
results/                        Reference machine-readable tables
artifact.json                   Data archive identity and member list
SHA256SUMS.txt                   Public file hashes
docs/reproduction.md             Evidence map and method details
docs/data.md                     Input provenance and third-party source
```

Saved identifiers `Linear`, `RoundRobin` and `LeastRecent` mean **Burden-aware**,
**Round-robin** and **Least-recent**, respectively. Identifiers are retained so that the
recorded schedules, histories and CSVs remain traceable.

Positive repairs are checked independently of the solver encoding. `INFEASIBLE` is a
solver-confirmed refusal; a replayed assumption core and an independently checked
arithmetic obstruction provide different evidence. The artifact does not treat these
three guarantees as interchangeable.
