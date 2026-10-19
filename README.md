# Participant Protection in Stable Schedule Repair

Saved evidence, source snapshots and offline verification for a computational
study of participant protection in schedule repair. The manuscript follows the
IEEE US-Letter conference template and contains six pages, including references.

## Download

Open this repository's **Releases** and download the versioned evidence ZIP.
The release description records the corresponding SHA-256 and verification
report. Use the same version for the manuscript and its evidence.

## Verify offline

1. Extract the evidence ZIP into a new folder.
2. Open a terminal in that folder.
3. Run `python -B verify.py` with Python 3.10 or later.
4. Confirm that the final output contains `"status": "PASS"`.

The saved-evidence checker uses the Python standard library. It does not need
internet access, an optimization solver installation or new optimization calls.

## Contents and scope

- `manuscript/`: the corresponding editable Word manuscript, PDF, figure source
  data, editable vector figures and manuscript-generation sources.
- `paper/walkthrough/`: a self-contained computational example; open `index.html`
  locally. This is an archived example, not a live solver or evaluated interface.
- `v8_pairs/`: all 40,542 affected-pair queries from fourteen selected two-outage
  cases: 19,830 compatible, 20,701 incompatible and eleven unresolved queries.
- `v10/`: the matched-allowance count-first experiment and its saved trajectories.
- `v9/`: the underlying coordination and repeated-workday evidence package.

The manifest binds the exact released bytes. Positive schedules, impact
histories and arithmetic are replayed and checked. Solver claims of infeasibility
or optimality are retained solver results, not independently checked formal
proof traces. Eleven unresolved pair queries are not certified refusals.
Source snapshots support inspection; fresh optimizer runs require the original
project layout and its documented dependencies. The self-contained checker is
the supported offline replay route.

## Interpretation

Requests and menu acceptance are simulated. The experiments do not establish
employee preferences, usability, human negotiation or perceived fairness.
Recorded timing phases are not controlled end-to-end latency benchmarks.
The two-outage structural results are conditional on the selected cases.

## Upstream data and rights

The study uses the public MSLIB multi-skilled project library, release 2.2.
Preserve the upstream citation and access information in the package. The
archive contains selected derived parameters and evidence rather than an
unlicensed mirror of the upstream library. Third-party rights remain with their
owners. No new licence for third-party data, templates or papers is implied.

AI assistance is disclosed in the manuscript. Responsibility for the scientific
claims and final publication remains with the authors.
