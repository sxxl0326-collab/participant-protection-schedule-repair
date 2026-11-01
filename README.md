# Participant Protection in Stable Schedule Repair

## Current version: PP-SR-20261101-v35

Use the [v35 version directory](versions/v35) for the manuscript and evidence.

- [Working manuscript PDF](versions/v35/paper.pdf)
- [Download the matching evidence ZIP](https://github.com/sxxl0326-collab/participant-protection-schedule-repair/raw/refs/heads/main/versions/v35/PP-SR-20261101-v35.zip)
- [Manuscript/package SHA-256 and verification record](versions/v35/release_manifest.json)
- [Table II](versions/v35/table_II.csv), [Table III](versions/v35/table_III.csv), and [closed-loop Table IV](versions/v35/table_IV_closedloop.csv)

Historical Release assets correspond to earlier manuscripts. The v35 manuscript
and evidence are bound by `versions/v35/release_manifest.json`.

## Verify and regenerate saved results

Extract the v35 evidence ZIP into a **new directory**, open a terminal there, and run:

```sh
python -B verify.py
python -B recompute_tables.py --output reproduced_tables
```

Both commands use Python 3.10+ standard-library modules, require no network or
solver, and end in `"status": "PASS"`. They check byte integrity, independently
replay positive schedules and histories, and regenerate the saved table values.
The local clean-directory check passed before publication.

Verification of saved runs is different from rerunning all optimization.
Fresh solves require the documented original project layout and OR-Tools 9.11;
source snapshots, inputs, time limits and seeds are included in the artifact.
Solver-confirmed negative/optimal statuses are retained results, not external
UNSAT/optimality proof traces.

## Evaluation scope

The manuscript reports computational simulations. It does not report a user
study or establish employee preferences, workplace acceptance or perceived
fairness. The new own-history comparison includes Least-recent and Round-robin;
requests and actual budgets can differ between policies. Author samples remain
in the working manuscript and must be resolved before conference submission.

## Data and rights

The artifact retains the MSLIB release identity, exact-input manifests and
upstream citations. Third-party rights remain with their owners; no new licence
for third-party data, templates or papers is implied. Questionnaire materials
and individual participant response files are excluded. AI assistance is
disclosed in the manuscript; the authors remain responsible for all claims.
