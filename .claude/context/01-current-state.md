# Current state (2026-07-14, commit acd0e8e)

- **Default stack: v8.1** (`configs/v8/`): tiled RTMDet-m (4×2+full, NMS 0.55, IoM 0.7,
  fp16 fast path) → RTMPose-X Halpe-26 → P1.5 One-Euro → P2 ByteTrack-style (no-spawn) →
  P3 tracklet graph + **union-lift merge** (W9) → P3.5 binding lift → P4 Singer-KF +
  min-cost-flow stitching + **colocated-id merge** (W9) → P5 roles v1.2 (bowling-end
  auto-flip) + peripheral suppression (W6) → P6 26-joint 3D (Butterworth, cheirality,
  dense-fill). Driver: `scripts/pipetrack/run_full_pipeline.py` (`--deliveries all`
  discovers from the input tree).
- **Production dataset**: `/home/ubuntu/pipetrack_v8/` on the L40S — 40 deliveries
  (CCPL080626 M1 overs 14/16/17; M2 overs 11/12 + innings-2 overs 3/4), all stages,
  README + final_panel.md + logs_production inside. Panel: agreement mean 0.862
  (0.527–0.992), reproj 3.07–3.56 px, collisions 0, coloc 0 on 38/40 (residual 1 pair on
  M1_1_14_7 and M2_1_11_3 — remaining-work §5b).
- **Local kept run trees** (`benchmarks/runs/`): `pipetrack_v8.1-w9` (8-delivery reference),
  `rtmpose-x-tiled-w5-full` (P1 input), `yolo26x-pose-full-db8`. Everything else archived
  as docs in `docs/runs/` and deleted.
- **Tests**: 212 passing (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH="" <env>/bin/python
  -m pytest -q`; env = `/home/aksh/miniconda3/envs/cricket-yolo26x-pose/bin/python`).
- **Mosaics delivered**: `artifacts/pipetrack_v8/mosaics/` (v8.1 `_14_4`, `_14_7`) +
  `artifacts/meeting_2026-07-13/`. The 8-batch and all-40 mosaic renders are PENDING
  (user decides timing; ~3.5 h CPU on the box, or faster after the VRAM/NVENC lead in
  05-active-threads).
- **Company handoff**: live — 3D data per delivery at
  `/home/ubuntu/pipetrack_v8/deliveries/<D>/{p6_3d/predictions, p4/diagnostics/ground_tracks.jsonl, p5/roles.json}`.
- Calibration provenance CONFIRMED by the team (one calibration for both matches).
