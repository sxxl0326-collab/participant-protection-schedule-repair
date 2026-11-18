# Data provenance

[Project home](../../../README.md) · [Setup and commands](../README.md) · [Figure and table index](reproduction.md#figure-and-table-index)

The experimental inputs are basic categorical-skill project models from the
[MSLIB v2.2 release](https://github.com/MarioVanhoucke/MSLIB-Multi-Skilled-Resource-Constrained-Project-Library/releases/tag/v2.2).
Events, protection requests and repeated workdays are generated experimental conditions.
They are not observations of employee requests or organizational deployments.

The [saved-data archive](../data/saved_results.zip) records:

- the selected 60-model list in `supplement/mslib_inputs/selected_models60.csv`;
- the frozen selection result in `supplement/mslib_inputs/sampling_result.json`;
- the actual upstream ZIP identity and SHA-256 in `supplement/mslib_asset_identity_v20.json`;
- the normalized model, original plan, event and adopted schedule in the saved trajectory
  records used by the independent checkers.

The upstream v2.2 tag and some descriptive text referring to v2.1 differ. Archive identity
and file selection records identify the actual experimental inputs. Original upstream
documentation and rights remain authoritative.

No individual questionnaire responses are included. The public evidence covers only the
computational experiments. The standalone example uses synthetic worker identifiers.

See [artifact.json](../artifact.json) for the complete archive inventory and
[SHA256SUMS.txt](../SHA256SUMS.txt) for the recorded archive and file hashes.
