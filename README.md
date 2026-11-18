# Participant Protection in Stable Schedule Repair

Code and saved synthetic experimental data for a coordinator–participant protocol for
schedule repair. The implementation answers duty-protection requests, checks repairs,
reports solver statuses, offers bounded concessions, and supports history-aware selection.

**[Open the fixed code and data snapshot](https://github.com/sxxl0326-collab/participant-protection-schedule-repair/tree/v1.0.0-code-data/versions/v37)**

## Verify the saved results

```sh
git clone --branch v1.0.0-code-data --single-branch https://github.com/sxxl0326-collab/participant-protection-schedule-repair.git
cd participant-protection-schedule-repair/versions/v37
python -B verify.py
```

Python 3.10+ and its standard library suffice for saved-result verification. The expected
last record is `"status": "PASS"`, with `"solver_calls": 0`. It checks 10,000 matched-policy
days and 5,000 own-history policy-days, and regenerates the saved numerical tables.
This replays positive schedules and saved records; it does not independently prove
negative solver statuses or rerun the optimization experiments.

## Run a new query

```sh
python -m pip install -r requirements.txt
python -B demo.py --protect W8
```

See the [project guide](versions/v37/README.md),
[experimental design](versions/v37/docs/experimental_design.md), and
[reproduction guide](versions/v37/docs/reproduction.md) for configuration and scope.
The [release](https://github.com/sxxl0326-collab/participant-protection-schedule-repair/releases/tag/v1.0.0-code-data)
fixes this snapshot; the `v37` directory name is retained to preserve earlier links.

This public repository contains code, synthetic experimental records and instructions.
It contains no manuscript files or individual human-study responses.
