# Phase 0 - Foundation Readiness

Phase 0 locks the foundation before Group 1 runs player detection, tracking, or
cross-camera association. The purpose is to prove four things:

1. the local `drive/dataset` payload is complete and synchronised enough to work on;
2. the calibration files can be loaded and used for projection/reprojection checks;
3. the output contract for Groups 2 and 3 is explicit;
4. unresolved management decisions are visible instead of hidden in assumptions.

## How to run

From the repository root:

```bash
python3 scripts/phase0_audit.py \
  --drive-root drive \
  --run-id phase0-ccpl080626 \
  --output-dir benchmarks/runs/phase0-ccpl080626 \
  --fail-on-internal-errors
```

Generated evidence is written to `benchmarks/runs/<run_id>/`:

- `phase0_readiness.json`
- `dataset_inventory.json`
- `calibration_report.json`
- `events_pipeline_report.json`
- `contract_report.json`
- `external_blockers.json`

These files are compact audit evidence. They must not include raw frames, model
outputs, or bulky artifacts.

## Completion checklist

- Dataset audit passes: all expected deliveries, cameras, frame counts, and frame id
  sync are reported.
- Calibration audit passes: calibration files load, matrices validate, surveyed points
  project, and existing ball reprojection is reproducible.
- Events pipeline audit passes: the existing ball artifact chain is present and its
  reprojection errors are summarised.
- Output contract validates in code and is documented in
  [output_contract.md](output_contract.md).
- Reuse map is documented in [reuse_map.md](reuse_map.md).
- External blockers are reported in [external_blockers.md](external_blockers.md) and
  `external_blockers.json`.

## Status semantics

`phase0_readiness.json` has separate internal and external status fields.

- `internal_status: pass` means the technical audit passed.
- `external_status: blocked` means management or annotation decisions are still open.
- `phase0_status: technically_complete_external_blocked` is acceptable for the code
  side of Phase 0; it means the remaining blockers are decisions, not implementation
  gaps.

