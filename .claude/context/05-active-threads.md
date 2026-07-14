# Active threads (2026-07-14 evening)

> **RESTRUCTURE 2026-07-14:** repo reorganised into `src/{core,identity}` + `tools/`, stages renumbered (`01…06`), single `pose-lab` env, benchmarking off `main`. New layout/commands: see `01-current-state.md` + `04-conventions.md`. The L40S box is UNCHANGED until it pulls the branch and rebuilds/renames its env — its `/home/ubuntu/...` paths and old `pN` stage-dir names below remain valid as-is.


## 1. RESOLVED (2026-07-14): mosaic + P1 "VRAM" optimization — VRAM was NOT the lever
Full writeup: `wip/optimization_findings_2026-07-14.md`. Measured on the L40S:
- **GPU decode is 3.2× SLOWER** than cv2 even on the idle L40S (per-image D2H copy +
  tensor reshape). NVENC is not the bottleneck at 1080p (encode overlaps the draw loop).
  The mosaic is CPU/memory-bandwidth-bound rasterisation. Force `QT_RENDER_GPU_DECODE=0`.
- Real lever = multiprocess across the 40 independent deliveries: **3.2× at 6-wide**
  (8-wide oversubscribes). Built `scripts/visualization/render_all_mosaics.py` (resumable,
  thread-capped, per-delivery logs). **All 40 rendered in 18.9 min, 0 fail** (~21× vs
  serial). Pack: `artifacts/mosaics_all40/` on the box (+ laptop copy).
- **P1 is GPU-compute bound at ~28 f/s using only 1.6 GB VRAM**; batch size is flat
  (batch-invariant). Idle SMs → data-parallel processes give 1.5× (2-wide) / 2.0× (3-wide).
  Built `scripts/inference/run_phase1_parallel.py` (delivery shards, resume-safe).
  Reminder: the sweep needs `--sweep --grid` TOGETHER; `--grid` alone starts a FULL run.
- CPU chain profile (clean serial): **P2 44%, P3 39%** dominate; triangulation already
  fast. Batch is core-bound at jobs=7.

## 1b. DSA optimizations SHIPPED (2026-07-14, byte-identical — user rule: accuracy first, zero output diff)
Full writeup: `wip/optimization_findings_2026-07-14.md`. User standard tightened to
**every speed change must be byte-identical** (appearance-disable was DROPPED — it moved
cycle-consistency 0.701→0.687).
- **P2 medoid cache (the big win)**: `track.py`/`config.py`. `gallery_repr` recomputed the
  O(K²) gallery medoid (K=30) every hit; cached pairwise cosines keyed by monotonic seq id
  → O(K) per update. **154s→10s per delivery (15.5×)**, bit-identical (proven vs baseline
  AND vs shipped production output, 3 deliveries × p2/p3/p4/p6). Flag `pose_medoid_incremental`.
- **P3 `ground_anchored_skeleton` vectorised** (`pose_shape.py`): per-joint loop → batched;
  bit-identical on 20k random cases + full-chain. Modest P3 win.
- Full single-delivery chain 348s→111s, byte-identical end-to-end. 212 tests pass.
- **No byte-identical win found** in: P4 (61% irreducible json.dumps), P3.5/P6 (already
  W10-PERF batched), P1.5 OneEuroFilter (stateful, risky, 4% phase — flagged), P3 appearance
  (output-changing, dropped). CPU batch is 8-vCPU-core-bound; more throughput needs DSA or
  more vCPUs (deliveries independent → scales ~linearly with cores).
- Changed files uncommitted on laptop+box (user runs commits): track.py, config.py,
  pose_shape.py + new render_all_mosaics.py, run_phase1_parallel.py.

## 2. Manager's reprojection questions (analysis DONE, answer in chat 2026-07-14)
Numbers measured on v8.1 (`_14_4`+`_14_7`, ~331k joint-view residuals):
- Panel metric (RANSAC inlier views, raw pre-smoothing triangulation): 3.07–3.56 px mean.
- Post-smoothing, all confident 2D views incl. fills: mean 6.8 px, MEDIAN 3.7 px,
  p95 24.5 px.
- WHERE high errors: hips 11–12 px mean (systematic cross-view keypoint-definition
  inconsistency, worst joint by far); fast limbs' tails (r_elbow p95 34 px); per-camera
  spread mild 6.0–8.3 px (no bad camera → calibration healthy).
- The "1 px" expectation is the CALIBRATION-TARGET standard (sub-pixel corners); ours is
  measured against POSE-MODEL keypoints whose own noise is 2–3 px (P1.5 jitter metric) plus
  cross-view definition offsets (hips!). Rig calibration itself was validated at ball-reproj
  p95 ≤ 4.5 px (wip/methods_log.md). 1 px mean vs detected keypoints is not achievable with
  any current 2D pose model at this resolution — the floor is the 2D noise, not calibration.
- Possible follow-ups if the manager wants movement: report median (3.7 px) + inlier metric
  consistently; exclude fills from the reported number; hip-specific handling (e.g. exclude
  hips from reproj reporting or add a hip-offset model); G1/G3 flags are implemented and
  un-A/B'd (remaining-work §2.1) — worth measuring, expected small.

## 3. Open user decisions
- Mosaic batch timing (blocked on the VRAM thread above, or run CPU renders now).
- UE packet export need (`export_ue_packets.py` never run on v8 data).
- Two production residual coloc pairs (M1_1_14_7, M2_1_11_3): relax colocated gates +
  re-run P4 for those two, or leave for mosaic arbitration (remaining-work §5b).
- Vedant global_id changelog still awaited; GT labelling still open.
