# External Blockers

Phase 0 separates technical readiness from decisions that code cannot make. The audit
extracts these blockers from the shared spreadsheets and writes them to
`benchmarks/runs/<run_id>/external_blockers.json`.

## Blocking decisions

### Dataset access

DS-001 and DS-002 are still management-controlled items in the shared planning sheets.
Phase 0 code can verify the local `drive/dataset` copy, but it cannot decide:

- the official DS-001 owner;
- the official DS-001 Drive/path reference;
- which clips are reserved for DS-002 blind validation.

### Ground truth

The current dataset has frames and ball pipeline outputs, but no manual player labels.
To score Group 1 properly, someone must own and produce:

- player bbox labels;
- `coco_17` keypoint labels if 2D pose accuracy is scored directly;
- `global_player_id` labels across cameras/time;
- role labels;
- optional 3D reference labels if available.

### Validation thresholds

The validation sheet still needs targets for:

- cross-camera association accuracy;
- acceptable ID switches per delivery;
- role classification accuracy.

Without these, the system can produce reports, but it cannot honestly declare a model
or association method "good enough."

## Recommended decisions

Before treating P1 benchmarking as final:

1. confirm DS-001 owner and path;
2. select DS-002 blind validation subset;
3. assign one owner for manual ID/role labels;
4. choose annotation tooling;
5. set validation thresholds for the three management-input metrics.

## Evidence

Run the Phase 0 audit and inspect:

- `benchmarks/runs/<run_id>/external_blockers.json`
- `benchmarks/runs/<run_id>/phase0_readiness.json`

