# Known bugs & latent issues — pipeline tracker

A living register of **defects and latent traps** found while documenting the pipeline (2026-07-16
pass). Distinct from the per-stage "Known issues" (design limitations) and from
[fixes-log.md](fixes-log.md) (the A/B ledger of *changes*). Each entry is cross-checked against the
code so nothing here is speculative.

**Status key:** 🔴 open · 🟠 open, root cause pinned · 🟡 needs verification · ✅ resolved / not-a-bug.
**Severity:** ★★★ corrupts output / highest leverage · ★★ material · ★ minor.

| ID | Title | Sev | Status | Stage |
|---|---|---|---|---|
| [BUG-1](#bug-1) | `emit_kalman_posterior` active but ineffective teleport guard | ★★ | 🟠 | 05 |
| [BUG-2](#bug-2) | ~~Distance-blind Kalman `R`~~ — RETRACTED (covariance-R is ON in prod) | — | ✅ | 05 |
| [BUG-3](#bug-3) | Splittable clustering IS on but conservative; sub-threshold chimeras persist | ★★ | 🟠 | 03 |
| [NB-2](#nb-2) | Dataclass config defaults disagree with production YAML (mis-diagnosis hazard) | ★★ | 🔴 | all |
| [BUG-4](#bug-4) | Detector-recall bound (dark/distant subjects lost) | ★★★ | 🟠 | P1 |
| [BUG-5](#bug-5) | 02 constant-velocity model breaks under manoeuvre | ★★★ | 🟠 | 02 |
| [BUG-6](#bug-6) | 05b stitching silently under-merges | ★★ | 🟠 | 05 |
| [BUG-7](#bug-7) | ~39% single-camera frames get no 3D pose | ★★ | 🟠 | 04 |
| [BUG-8](#bug-8) | 01 stabilization not wired into the default flow | ★ | 🔴 | 01 |
| [NB-1](#nb-1) | C07 global image size in config | — | ✅ not-a-bug | 03 |

---

## BUG-1 — `emit_kalman_posterior` is an *active but ineffective* teleport guard {#bug-1}
**Severity ★★ · 🟠 root cause pinned · stage 05**

- **Symptom:** `configs/05_global_id.yaml` sets `emit_kalman_posterior: true` and the code + docs present
  it as *the* fix that stops a single bad frame teleporting the reported track. Yet emitted teleports
  persist at **33 (8-set) / 367 (40-set)** with it on.
- **Verified (isolated off-vs-on A/B, `emit_ground_source=foot`, 8_init):** the emitted
  `ground_tracks.jsonl` **DIFFERS 8/8** between off and on — so the flag **is active and does change the
  emission** (the posterior branch at [runner.py:286](../../src/identity/p5_global_id/runner.py#L286)
  fires). It is **NOT a no-op.** (An earlier "byte-identical no-op" claim of mine was unsound — it
  compared true-vs-true — and is fully retracted.)
- **Root cause:** it is a **weak guard** — the χ²-gated Kalman posterior still *follows/admits* the
  mis-associated measurement (the gate is too permissive and the measurement noise `R` is distance-blind,
  [BUG-2](#bug-2)), so the emitted position moves but the teleport is not prevented.
- **Fix:** either tighten the gate + feed a distance-aware `R` (BUG-2) so the posterior can reject the
  outlier, or drop the misleading framing that it is *the* teleport fix. The **effective** fix already
  shipped is the hard drop-gate [A3 `emit_velocity_gate`](fixes-log.md) (teleports 367→0), which works
  regardless of this flag.

## BUG-2 — Distance-blind Kalman `R` — **NOT a bug in production (retracted)** {#bug-2}
**Severity — · ✅ already addressed in prod; ⚠️ dataclass-default hazard · stage 05**

- **Correction (2026-07-16):** this was mis-filed. The distance/uncertainty-dependent `R` **is enabled in
  production** — `configs/05_global_id.yaml` sets `use_measurement_covariance: true` (with `r_floor_m 0.15`,
  `r_ceiling_m 0.8`), fed by `emit_ground_cov: true` in `configs/03_association.yaml`. So the ground Kalman
  **does** scale its measurement trust by the per-cluster GN covariance ([track_manager.py `_measurement_R`](../../src/identity/p5_global_id/track_manager.py#L162)); it is **not** distance-blind in the shipped pipeline.
- **My error:** I read the *dataclass default* `use_measurement_covariance: bool = False` in
  [config.py:110](../../src/identity/p5_global_id/config.py#L110) and wrongly concluded it was off. The
  production YAML overrides it to `true`. The fixed per-role `R` (`ground_kalman.py:96`) is only the
  *flag-off fallback*.
- **Residual hazard (real, keep):** the **dataclass defaults disagree with the production YAML** for several
  flags (`use_measurement_covariance`, `graph_shape_enabled`, `graph_split_enabled`, `adaptive_lost_window`
  are all `False` in code but `True` in the YAML). Reading `config.py` alone is misleading — it burned this
  very analysis. *Fix:* align the dataclass defaults to production, or add a one-line "production truth =
  the YAML" note atop each config. Low effort, prevents future mis-diagnosis.
- **Does the covariance-R actually help?** Pending the OFF-vs-ON A/B (disable `use_measurement_covariance`
  and measure the loss) — running now.

## BUG-3 — Chimera split IS on, but conservative; sub-threshold chimeras persist {#bug-3}
**Severity ★★ · 🟠 partially addressed · stage 03**

- **Correction (2026-07-16):** the base clustering is merge-only union-find, **but production already runs
  the UNDO** — `configs/03_association.yaml` sets `graph_split_enabled: true`, which fires the F13
  chimera-veto/eviction pass ([tracklet_graph.py `_chimera_veto_pass`](../../src/identity/p3_association/tracklet_graph.py#L1332)):
  it lifts each multi-camera cluster, detects the torso-residual chimera signature, evicts the intruding
  camera's chunks into fresh clusters, and LLR-vetoes the pair so no later pass re-welds them. So chimeras
  **can** be split. (I previously called this "experimental / never un-merges" — wrong; it's on.)
- **Residual (real):** the split fires only above **conservative** thresholds
  (`graph_chimera_torso_residual_px: 30`, `graph_chimera_frame_fraction: 0.6` — the W4 over-split lesson),
  so a *mild* chimera whose torso residual stays under 30 px, or one present in <60% of frames, is **not**
  split and persists. The residual chimera rate (10–32% of ≥3-view clusters historically) needs
  re-measurement under the current on-config to size how much is left.
- **Proposed follow-up:** measure residual chimeras with split on; if material, consider a
  reprojection-gated correlation-clustering objective, or a graduated (not binary) split threshold. See
  [03 fix #2](03-association.md).

## BUG-4 — Detector-recall bound {#bug-4}
**Severity ★★★ · 🟠 root cause pinned · stage P1**

- **Symptom:** dark / distant / occluded subjects (the "dark umpire") are missed by detection, and a
  miss here is unrecoverable downstream.
- **Root cause:** RTMDet-m @ `bbox_thr=0.3`, chosen for speed and unbenchmarked for this domain.
- **Evidence:** the association layer contains machinery (`synthetic tracklets`,
  `apply_feet_approximation`) that exists *only* to paper over players the detector never tracked.
- **Proposed fix:** stronger detector (RTMDet-l/x, RT-DETR/Co-DETR) + per-camera adaptive `bbox_thr`. See
  [P1 fixes](00-inference.md).

## BUG-5 — Constant-velocity model breaks under manoeuvre {#bug-5}
**Severity ★★★ · 🟠 root cause pinned · stage 02**

- **Symptom:** tracks fragment exactly when players accelerate/turn/dive — which 05 then has to stitch
  back together.
- **Root cause:** the per-camera tracker uses a **constant-velocity** Kalman
  ([kalman.py:16](../../src/identity/p2_tracking/kalman.py#L16)); non-linear cricket motion violates its
  straight-line-steady-speed assumption, so gating drops the track.
- **Proposed fix:** OC-SORT observation-centric modules (built for non-linear motion). See
  [02 fix #1](02-tracking.md).

## BUG-6 — 05b stitching silently under-merges {#bug-6}
**Severity ★★ · 🟠 root cause pinned · stage 05**

- **Symptom:** the offline stitcher that should bridge fragments barely fires —
  `stitched_id_switch_proxy = 0` everywhere — so the distinct-id count stays inflated (18–25 vs a ~13
  roster).
- **Root cause:** the min-cost-flow feasibility gates (`temporal_gate_frames=120`, kinematic, occupancy)
  are too conservative for real occlusion gaps.
- **Proposed fix:** loosen bridging where occupancy proves two segments can't be simultaneous; add a
  pose/ReID descriptor to the stitch cost. See [05 fix #4](05-global-id.md).

## BUG-7 — Single-camera frames get no 3D pose {#bug-7}
**Severity ★★ · 🟠 root cause pinned · stage 04**

- **Symptom:** ~39% of player-frames are single-camera and receive **no** triangulated 3D pose.
- **Root cause:** triangulation needs ≥ 2 rays (`--min-views 2`); one ray can't be triangulated.
- **Proposed fix:** single-view → canonical-skeleton PnP lift (fit the player's learned 3D skeleton to
  the lone view). See [04 fix #2](04-lift.md). *(Note: the 1F single-view sticky-hip lift is a **rejected
  ** narrower attempt — it raised teleports; see fixes-log.)*

## BUG-8 — 01 stabilization not wired into the default delivery flow {#bug-8}
**Severity ★ · 🔴 open · stage 01**

- **Symptom:** the validated −32%-jitter stabilization stage exists but the batch driver doesn't run it
  before 02 by default, so its win isn't realised end-to-end.
- **Fix:** wire it into the driver behind its enable flag and add its jitter metric to the panel. See
  [01 fix #2](01-stabilization.md).

---

## NB-1 — C07 global image size in config {#nb-1}
**✅ investigated → NOT a bug · stage 03**

- **Claim:** `configs/03_association.yaml` hard-codes `image_w/h = 2560×1440` while cam_07 is ~3776×960,
  so C07 handling would be wrong.
- **Finding:** `load_image_sizes_from_drive` returns cam_07's true native size and threads it into the
  epipole test, the feet check, and `keypoints_norm`; the `config.image_w/h` default has **no
  consumers** (it's dead config). No behavioural bug. **Kept here so it isn't re-chased.** (Tidy-up: delete
  the dead config key to avoid future confusion.)

## NB-2 — Dataclass config defaults disagree with production YAML {#nb-2}
**Severity ★★ · 🔴 open · all stages (config hygiene)**

- **Symptom / hazard:** many feature flags are `False` in the Python dataclass defaults
  (`config.py`) but `True` in the shipped YAML (`configs/*.yaml`). Confirmed divergent:
  `use_measurement_covariance`, `graph_shape_enabled`, `graph_split_enabled`, `adaptive_lost_window`,
  `emit_ground_cov` (all off-in-code, **on-in-YAML**).
- **Impact:** reading `config.py` alone gives a **wrong** picture of what the pipeline runs. This directly
  caused two mis-filed "bugs" here (BUG-2, BUG-3) and a wasted on-vs-on A/B: the flags were already enabled
  in production but looked default-off in code. Anyone auditing the system from the dataclass will be
  misled.
- **Fix (low effort, high value):** either (a) set the dataclass defaults to match the production YAML so
  code and config agree, or (b) put a `# PRODUCTION TRUTH = configs/<x>.yaml; dataclass defaults are the
  library fallback` banner atop each config module and always audit the YAML. Prefer (a).
- **Rule going forward:** *the resolved config is `run_manifest.json` of an actual run* — verify flag state
  there, never from dataclass defaults.
