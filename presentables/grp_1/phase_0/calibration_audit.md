# Calibration Audit

The Phase 0 calibration audit verifies that the existing camera calibration is usable
for later cross-camera association and triangulation.

## Inputs checked

The audit reads:

- `Bundle_Adjusted_intrinsics.json`
- `Bundle_Adjusted_extrinsics.json`
- `camera_calibration_config.json`
- `pitch_calibration_config.json`
- `crop_mech.json`
- `CPL08626_coord_aligned.csv`
- existing ball `*_3D.json` and `*_reprojection.json` files

## Checks performed

### Matrix validation

For cameras `C01` through `C07`:

- intrinsic matrices must be finite `3x3`;
- projection matrices must be finite `3x4`;
- missing or malformed matrices are internal Phase 0 failures.

### Surveyed point projection

Surveyed world points are projected into every camera. The audit reports:

- number of surveyed points loaded;
- finite projection count per camera;
- in-frame projection count per camera;
- sample projected pixel coordinates.

This is a sanity check. It is not expected that every surveyed point is visible in every
tight DRS camera.

### Existing ball reprojection comparison

For each delivery, the audit:

1. loads the existing ball `*_3D.json`;
2. projects each 3D ball point into each camera using the calibration matrix;
3. compares the projected normalized coordinate with the coordinate stored in
   `*_reprojection.json`;
4. reports pixel deltas and the existing stored ball reprojection error statistics.

The projected-vs-stored reprojection delta checks whether our full-frame projection
convention matches the stored reprojection coordinate convention. If this is high while
the stored ball reprojection error remains low, the likely cause is crop or normalization
metadata in the existing ball artifact rather than a bad calibration matrix.

The stored ball reprojection error is the quality signal from the existing ball pipeline.
It shows how far the triangulated ball point was from the original 2D observation, and
is the number to compare against the "few px" expectation.

## Evidence

Run:

```bash
python3 scripts/phase0_audit.py --drive-root drive --run-id phase0-local
```

Then inspect:

- `benchmarks/runs/phase0-local/calibration_report.json`
- `benchmarks/runs/phase0-local/phase0_readiness.json`
