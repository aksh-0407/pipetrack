# Ball Pipeline Reuse Map

The existing dataset already contains a working ball pipeline. Phase 0 documents how
that single-point pipeline maps to the future multi-player, multi-joint pipeline.

| Existing ball artifact | Current meaning | Group 1 player/joint equivalent | Reuse decision |
|---|---|---|---|
| `*_2D.json` | ball detections per camera/frame | person bbox + 17 2D keypoints per camera/frame | mirror layout, change class and payload |
| `*_2D_cleaned.json` | selected/cleaned ball track observations | confidence-gated player/keypoint observations | reuse filtering concept, not ball-specific thresholds |
| `*_3D.json` | one triangulated ball point per frame | 17 triangulated joints per player/frame | reuse projection-matrix triangulation pattern |
| `*_3D_cleaned.json` | smoothed ball 3D track | smoothed 3D skeleton tracks | reuse cleaning stage, add skeleton constraints later |
| `*_3D_trimmed.json` | trimmed useful ball segment | valid player track windows | reuse trimming concept, criteria will differ |
| `*_reprojection.json` | ball reprojection error per camera | per-joint reprojection error per player/camera | reuse as geometry quality metric |
| `*_predicted_3D.json` | predicted ball continuation | not a Phase 0 player requirement | do not reuse for players in v0 |
| `*_speed.json` | ball speed | optional player/limb velocity features | defer to later phases |
| `*_EVENTS.json` | delivery events and DRS result | consumed later by G2/G3, not owned by G1 | read-only reference |
| `*_3D_unreal.json` | ball 3D export | skeleton/pose packet export | reuse coordinate-export concept, not file shape |

## Practical boundary

Phase 0 does not generalize the ball pipeline yet. It proves the existing pipeline is
present, readable, and geometrically consistent enough to use as a template.

Actual player implementation starts in P1:

```text
P1: person bbox + 2D keypoints
P2: per-camera tracklets
P3: cross-camera association
P4: global player IDs
P5: role labels
P6: clean 3D skeletons and Unreal export
```

## Evidence

Run:

```bash
python3 scripts/phase0_audit.py --drive-root drive --run-id phase0-local
```

Then inspect:

- `benchmarks/runs/phase0-local/events_pipeline_report.json`
- `benchmarks/runs/phase0-local/calibration_report.json`

