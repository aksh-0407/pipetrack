# Phase 1 - Per-Camera Perception

Phase 1 produces person bounding boxes and 2D COCO-17 keypoints for every camera
frame. It does not assign global IDs, roles, tracks, or 3D skeletons.

## Baseline command

Run the first full-delivery baseline with YOLO pose:

```bash
conda run -n cricket-yolo26x-pose \
  python scripts/run_cricket_p1_inference.py \
  --drive-root drive \
  --delivery-id CCPL080626M1_1_14_1 \
  --model-id yolo26x_pose \
  --run-id p1-yolo26x-CCPL080626M1_1_14_1 \
  --device auto \
  --inference-mode full_frame
```

The runner writes:

- `benchmarks/runs/<run_id>/run_manifest.json`
- `benchmarks/runs/<run_id>/p1_metrics.json`
- `benchmarks/runs/<run_id>/predictions/cam_*.jsonl`

Prediction JSONL files are raw model outputs and are ignored by git.

## Crop experiment

After the full-frame baseline:

```bash
conda run -n cricket-yolo26x-pose \
  python scripts/run_cricket_p1_inference.py \
  --drive-root drive \
  --delivery-id CCPL080626M1_1_14_1 \
  --model-id yolo26x_pose \
  --run-id p1-yolo26x-CCPL080626M1_1_14_1-crops \
  --device auto \
  --inference-mode crops
```

Crop outputs are converted back into full-frame pixel coordinates before writing the
Phase 1 contract records.

## Visual QA

```bash
python3 scripts/render_cricket_p1_overlays.py \
  --drive-root drive \
  --run-dir benchmarks/runs/p1-yolo26x-CCPL080626M1_1_14_1
```

Overlay images are written under `benchmarks/artifacts/<run_id>/overlays/`, which is
local-only. A compact `visual_qa_manifest.json` is written into the run folder.

## Contract boundary

Phase 1 records use `g1_player_frame/v0` with:

- `global_player_id: null`
- `local_track_id: null`
- `role: "unknown"`
- `pose_3d: null`

Those fields are filled by later phases.

