# Group 1 Output Contract

This is the Phase 0 target contract for Group 1 handoff records. It is implemented
and validated by `pose_estimation.cricket.contract`.

## Record shape

```json
{
  "schema_version": "g1_player_frame/v0",
  "match_id": "CCPL080626",
  "delivery_id": "CCPL080626M1_1_14_1",
  "camera_id": "cam_01",
  "frame_index": 212334,
  "frame_name": "frame_camera01_000212334.jpg",
  "players": [
    {
      "global_player_id": "P001",
      "local_track_id": "cam_01_trk_0001",
      "role": "unknown",
      "bbox_xywh_px": [100.0, 200.0, 80.0, 240.0],
      "bbox_xywh_norm": [0.039, 0.139, 0.031, 0.167],
      "track_confidence": 0.94,
      "pose_2d": {
        "skeleton": "coco_17",
        "keypoints_px": [[120.0, 220.0]],
        "keypoints_norm": [[0.047, 0.153]],
        "confidence": [0.91]
      },
      "pose_3d": {
        "keypoints_world_m": [[0.1, 8.2, 1.6]],
        "confidence": [0.88],
        "mean_reprojection_error_px": [3.4]
      }
    }
  ]
}
```

The compact JSON above shows one keypoint for readability. The implemented schema
requires 17 COCO keypoints, 17 2D confidence values, 17 3D keypoints when `pose_3d`
is present, and 17 3D confidence/reprojection values.

## Required conventions

- `schema_version` is `g1_player_frame/v0`.
- `camera_id` is `cam_01` through `cam_07`.
- `pose_2d.skeleton` is `coco_17`.
- Pixel coordinates are canonical.
- Normalized coordinates are compatibility fields relative to the full 2560x1440 frame.
- World coordinates are in the existing cricket calibration world, in metres.
- Real player names are out of scope. Anonymous IDs such as `P001` are sufficient.

## Role enum

Allowed role values:

- `bowler`
- `striker`
- `non_striker`
- `wicketkeeper`
- `umpire`
- `fielder`
- `unknown`

`unknown` is the default until role classification is implemented.

## Nullable fields by phase

- `global_player_id` may be null in P1/P2 intermediate outputs.
- `global_player_id` is required for final Group 1 handoff output.
- `pose_3d` may be null until cross-camera association and triangulation are available.
- `role` should remain `unknown` until P5 role classification assigns a stronger label.

## Validation evidence

Run the Phase 0 audit and inspect:

- `benchmarks/runs/<run_id>/contract_report.json`
- `benchmarks/runs/<run_id>/phase0_readiness.json`

