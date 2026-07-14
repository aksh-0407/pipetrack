# Current state (2026-07-14, post-restructure branch `restructure/overhaul` → main)

> **REPO RESTRUCTURE landed 2026-07-14.** Code moved from `pose_estimation/` + `scripts/`
> into `src/{core,identity}` + `tools/`; stages renumbered; single conda env; benchmarking
> off `main`. See `04-conventions.md` for the full new layout + commands. Algorithm/pipeline
> behaviour is UNCHANGED (200 tests green under `pose-lab`); the deferred algorithm work is in
> `docs/changes_tbd.md` + `remaining-work.md`.

- **Default stack: v8.1** (now `configs/0N_*.yaml`): tiled RTMDet-m (4×2+full, NMS 0.55, IoM 0.7,
  fp16 fast path) → RTMPose-X Halpe-26 → 01 stabilization (One-Euro) → 02 tracking (no-spawn) →
  03 association (tracklet graph + union-lift, W9) → **04 lift** (binding, runs *before* global-id)
  → 05 global_id (Singer-KF + min-cost-flow stitching + colocated-id merge, W9) → 06 roles v1.2
  (bowling-end auto-flip) + peripheral suppression (W6) → terminal 07 lift3d (26-joint, Butterworth,
  cheirality). Driver: `src/main.py` → **`python -m main`** (`--deliveries all` discovers from the
  input tree; `--from-stage`/`--until-stage` select the window).
- **Env**: single **`pose-lab`** (clone of the old cricket-rtmpose-l = full mm-stack + torch 2.1
  + numpy/scipy/opencv, plus `ultralytics` for the kept YOLO-P1 alternate; editable install of the
  repo). All other `cricket-*`/`balltrack` envs deleted.
- **Tests**: 200 passing — `env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
  /home/aksh/miniconda3/envs/pose-lab/bin/python -m pytest -q`. (The ROS `launch_testing`
  pytest plugin on the system PYTHONPATH must be excluded — hence the two env vars.)
- **Local outputs** now live under gitignored `data/derived/{runs,mosaics}/` (was
  `benchmarks/runs/` + `artifacts/`). `benchmarks/` (22 GB) and `artifacts/` were untracked and
  then deleted from disk; benchmarking lives on the `benchmark` branch.
- **Production dataset (REMOTE, historical)**: `/home/ubuntu/pipetrack_v8/` on the L40S — 40
  deliveries, all stages, README + final_panel.md inside. Panel: agreement mean 0.862
  (0.527–0.992), reproj 3.07–3.56 px, collisions 0, coloc 0 on 38/40 (residual 1 pair on
  M1_1_14_7 and M2_1_11_3 — remaining-work §5b). NOTE: that remote tree predates the restructure,
  so its stage dirs use the old `p4/`, `p6_3d/`, `p5/` names — leave as-is.
- **Company handoff** (remote, historical dir names): 3D per delivery at
  `/home/ubuntu/pipetrack_v8/deliveries/<D>/{p6_3d/predictions, p4/diagnostics/ground_tracks.jsonl, p5/roles.json}`.
  New local runs use the renumbered `05_global_id/`, `07_lift3d/`, `06_roles/` names.
- Calibration provenance CONFIRMED by the team (one calibration for both matches).
- Models trimmed to 4 (`rtmpose_x_body8`, `rtmdet_m_person`, `rtmpose_l`, `yolo26x_pose`);
  `vedant2/`, `wheels/`, `pytest.ini`, and unused benchmark-model weights/clones removed.
