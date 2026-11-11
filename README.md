# Participant Protection in Stable Schedule Repair

Code and experimental data for a coordinator–participant protocol for schedule repair.
The implementation answers duty-protection requests, returns checked schedules or solver
statuses, explores bounded concessions, and supports history-aware repair selection.

**[Open the reproducibility project](versions/v37/)** — installation, runnable example,
saved schedules, independent checks, and table-generation commands are provided together.

## Quick start

```sh
git clone https://github.com/sxxl0326-collab/participant-protection-schedule-repair.git
cd participant-protection-schedule-repair/versions/v37
python -B verify.py
```

Saved-result verification uses Python 3.10+ and the standard library. To solve a new
protection query, install the solver and run the supplied example:

```sh
python -m pip install -r requirements.txt
python -B demo.py --protect W8
```

See the [project README](versions/v37/README.md) for outputs, data provenance, and the
difference between replaying saved results and performing fresh optimization.
