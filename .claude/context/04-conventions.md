# Working conventions (user directives, standing)

- **Evaluation standard**: frozen baseline; A/B on all 8 benchmark deliveries (or full 40
  for production claims); accept only significant GENERALIZED improvement; every change
  flag-gated with flags-off byte-identity PROVEN BY EXECUTION (cmp on real outputs, not
  reasoning); metrics read as a joint panel, never singly; same-camera collisions must stay 0.
  Primary axes: cross-camera agreement, distinct IDs vs ~13–15 roster, id-persistence,
  excess fragments, coloc; teleports are a noisy proxy (double-count occlusion re-acquisition
  — acceptable per the ID-constancy objective: occlusion teleports OK if the ID restores).
- **Composition principle**: judge fixes as composed stacks in pipeline order; don't drop a
  fix that hurts its own phase if later phases consume what it exposes.
- **Git**: NO AI/Claude co-authorship ever; short professional messages; user normally runs
  commits (they explicitly delegated one on 2026-07-14 — ask if unclear).
- **Monitors**: arm one at launch of EVERY long-running task, progress + failure coverage,
  report real wall-clock ETAs unprompted.
- **Mosaics**: render only when the user asks; roles shown ONLY in the roster panel (bottom
  right), never on player chips; body-paint identity overlay default ON.
- **Docs discipline**: fixes-log entry the moment a verdict lands (lab-notebook style);
  archived runs → docs/runs/ before deleting trees; open work lives ONLY in
  /remaining-work.md; wip/archive/ for executed plans.
- **User profile**: Quidich internship (PS-1); mentor meetings need clean docs + honest
  open-issues; the user reviews mosaics as final judge; prefers batch directives and
  timely unprompted progress updates.
- Laptop crashes historically (work in repo, sync often); it has been stable lately but
  don't leave long-running local state unsaved.

## Repo layout & commands (post-2026-07 restructure)

- **Layout**: `src/core/` (contract, schemas, ue_transform, calibration, keypoints, dataset,
  + `inference/` = P1) · `src/identity/common/` (geometry, triangulation, pose_shape, metrics)
  · `src/identity/pN_<stage>/` = `p1_stabilization, p2_tracking, p3_association, p4_lift,
  p5_global_id, p6_roles` · `src/identity/{export,visualization}` · `src/main.py` (orchestrator)
  · `tools/` (setup/audit/env, `diagnosis/`, `detector_bakeoff/`) · `configs/0N_<stage>.yaml`
  (+ `configs/reference/*.jpeg`) · outputs in gitignored `data/derived/{runs,mosaics}/`.
- **Imports**: `core.*`, `identity.*`, `tools.*` (src on path via `pip install -e .` /
  `pyproject.toml pythonpath`). Rule: `core` never imports `identity`.
- **Env**: `pose-lab` only. Run everything as `python -m main` / `python -m identity.id_pipeline`
  / `python -m core.inference.run_phase1_rtmpose_inference`.
- **Stage-dir names** in a run tree: `deliveries/<D>/{01_stabilization,02_tracking,03_association,
  04_lift,05_global_id,06_roles,07_lift3d,08_render,logs}/`. NOTE the pre-restructure remote
  production tree still uses old `p2/p3/p4/p5/p6_3d` names — don't rewrite those historical paths.
- **Tests**: `env -u PYTHONPATH PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
  /home/aksh/miniconda3/envs/pose-lab/bin/python -m pytest -q` (exclude the ROS pytest plugin).
- **Docs numbering**: `docs/critical-analysis/README.md` carries the label↔new-number map; the
  analysis keeps the historical P1–P6 labels, bridged by that map + per-phase-doc header notes.
