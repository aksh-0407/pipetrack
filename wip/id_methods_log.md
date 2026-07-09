# Identity / Re-ID — Methods Log (running lab notebook)

Every method tried for the **identity** overhaul (companion to `wip/id_issues.md` [the 6 failure
modes] and `wip/3d_location_methods_log.md` [the location work]). Append-only; newest at the bottom.
Same standing rules as the location log: **validate on all 8 deliveries** (lead with the worst,
_5/_6/_7/M2), read the metric panel **jointly**, and **never call a method a "win" without a
significant, generalised improvement** with zero same-camera-collision regression.

Run harness: `scripts/pipetrack/run_id_pipeline.py` (P3→P4 on the existing v3 P2, into
`benchmarks/runs/pipetrack_v5`, BLAS threads capped). Baseline frozen at
`benchmarks/runs/pipetrack_v3/_baseline_snapshot`. Every change is behind a config flag defaulting
to the current behaviour, so flags-off is byte-identical (verified: delivery 1 P3→P4 reproduced
0.952 / 12 IDs / 11 teleports / 0 collisions exactly, 2026-07-09).

Env: pipeline `cricket-rtmpose-l`; pytest `cricket-yolo26x-pose` with
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH="" OMP_NUM_THREADS=1`.

## BASELINE (v3, committed, all 8) — the bar to beat

| delivery | agreement | distinct IDs | teleports | collisions | single_cam | churn | verdict |
|---|---|---|---|---|---|---|---|
| M1_1_14_1 | 0.952 | 12 | 11 | 0 | 0.390 | 0.000 | pass |
| M1_1_14_2 | 0.977 | 11 | 7  | 0 | 0.480 | 0.000 | pass |
| M1_1_14_3 | 0.870 | 18 | 19 | 0 | 0.524 | 0.001 | pass |
| M1_1_14_4 | 0.857 | 13 | 15 | 0 | 0.514 | 0.000 | pass |
| M1_1_14_5 | 0.767 | 15 | 48 | 0 | 0.562 | 0.000 | warn |
| M1_1_14_6 | 0.802 | 25 | 52 | 0 | 0.464 | 0.002 | warn |
| M1_1_14_7 | 0.498 | 22 | 59 | 0 | 0.524 | 0.002 | warn |
| M2_1_12_1 | 0.778 | 20 | 171| 0 | 0.613 | 0.004 | fail |

Roster is ~13–15 people; ≤7 visible/camera. Over-segmentation (18–25 IDs on 3/5/6/7/M2) and the
0.50 cross-camera agreement on _7 are the headline defects.

---

## ID-1 — cross-camera under-merge on the low-parallax facing pairs

**Root cause (verified in code).** `tracklet_graph` requires an edge LLR ≥ `graph_llr_merge_threshold`
(2.0) to merge, but each cue is capped at `graph_llr_positive_cap` (1.5). On the facing pairs
appearance abstains (dead colour), motion abstains for static players, posture can abstain for
crouched/oblique bodies — leaving **ground alone (≤1.5 < 2.0)**, so a genuine same-player pair never
merges. Additionally the facing pairs use the *tighter* `opposite_pair_ground_gate_m` (2.5), which
under foot-projection noise can itself split a correct 2-view merge.

**Change (flag-gated, default off → byte-identical).**
- `graph_corrob_merge` + `graph_llr_merge_single` (1.2): a second, conservative merge pass admits an
  edge in `[single, threshold)` **only** when it has full co-visible support, **no observable cue
  disagrees** (every present cue LLR ≥ 0), it is the **mutual unambiguous best** for both endpoints'
  clusters, and it passes the cannot-link/veto check. Cannot manufacture chimeras a blanket threshold
  drop would.
- `graph_facing_gate_scale` (1.3): widen the graph hard-distance edge gate on the calibration-derived
  facing pairs only (2.75→3.575 m median-residual ceiling), where a tight gate splits correct merges.

Unit tests: 26 association/graph tests green with flags off (byte-identical).

**Result (all 8, v5 P3 config, P4 committed) — PARTIAL WIN, 2026-07-09.**

| delivery | agreement | Δ | ids | Δ | teleports | Δ | single_cam | Δ | collisions |
|---|---|---|---|---|---|---|---|---|---|
| _1 | 0.952 | — | 12 | — | 11 | — | 0.390 | — | 0 |
| _2 | 0.977 | — | 11 | — | 7 | — | 0.480 | — | 0 |
| _3 | 0.870 | — | 18 | — | 19 | — | 0.524 | — | 0 |
| _4 | 0.857 | — | 13 | — | 15 | — | 0.514 | — | 0 |
| _5 | 0.768 | +0.001 | 16 | +1 | 43 | -5 | 0.562 | — | 0 |
| _6 | 0.801 | -0.001 | 25 | — | 52 | — | 0.464 | — | 0 |
| _7 | **0.599** | **+0.102** | 24 | +2 | 46 | -13 | 0.473 | -0.051 | 0 |
| M2 | 0.770 | -0.008 | 22 | +2 | 156 | -15 | 0.613 | — | 0 |

- **The worst clip (_7) gains +0.102 cross-camera agreement** (0.498→0.599) — the single largest lever
  found for under-merge — with teleports −13 and single-camera rate −0.051 (more views bound together,
  the intended effect). Easy clips 1–4 **byte-identical** (no regression). Collisions stay 0 everywhere.
- **Trade-off:** distinct IDs rose +1/+2 on the hard clips. Mechanism: binding more facing-pair views
  promotes previously-demoted single-camera clusters into multi-camera bindings (single_cam rate drops),
  so real players earn ids — but temporal *fragmentation* is untouched by ID-1. That is the ID-2 lever
  (adaptive lost-window + descriptor re-entry + stitching), applied next on top of this P3 config.
- **Verdict: ACCEPTED as the ID-1 layer** — significant, generalised agreement gain on the hard clips,
  zero collision/easy-clip regression. Kept enabled in `configs/p3_association_v5.yaml`.

---

## ID-2 — fragmentation / over-segmentation (the big id-count lever)

**Root cause (measured, not guessed).** Two layers, isolated by reading the diagnostics:
1. **P4b stitching was inert.** `selected_stitch_link_count = 0` on every hard clip despite
   243–1429 *feasible* edges. `solve_flow` only stitches when an edge cost < the new-trajectory
   dummy (`w_spatial·new_traj_cost_factor = 1.0·0.5 = 0.5`), but a plausible stitch
   (`0.1·gap + 1.0·distance + …`) is almost always > 0.5 — so P4b never merged anything.
2. **The excess ids are ultra-short P4a fragments, not bindings.** The graph produced only
   **10–11 clean bindings** (≈ roster) on the hard clips, yet P4 emitted 18–25 ids. Dumping the
   M2 ground tracks showed 9 full-clip stable players + ~4 mid-length + **5 ids alive only 6–74
   frames** (P018 n=8, P019 n=6, P021 n=13, P020 n=21) — fragments/shadows from the many *demoted*
   clusters (38/41/87) that P4a briefly confirmed. A real player is present the whole 12 s clip.

**Changes (flag-gated, default off).**
- **Stitching v2** (`stitching.py`): pose-shape descriptor threaded per segment (`pose_by_id` from
  the tracker), a **hard pose gate** (`p4b.pose_stitch_max_distance`) so only same-build fragments
  merge, an optional `w_pose` term, Kalman-window-smoothed exit/entry velocities (not raw
  last-two-frame), and `new_traj_cost_factor` raised (0.5→3.0) so plausible stitches actually win.
- **Cardinality prior** (`p4a.min_emit_frames`, `runner.py`): after stitching, drop any id whose
  total frame-span < 30 (0.6 s) — a fragment, not a late entry — its detections become unlabelled.
- Plus the P4a layer already added: adaptive lost-window, pose veto in the chi² gate, descriptor-
  gated re-entry (these alone moved little; the diagnostics `pose_gate_vetoes`/`reentry_pose_rejects`
  rarely fire because P4a's *triangulated* pose descriptor needs parallax the facing pairs lack).

**Result (all 8, full v5 P3+P4 stack vs frozen baseline) — WIN, 2026-07-09.**

| clip | agreement | Δ | distinct IDs | Δ | teleports | Δ | collisions |
|---|---|---|---|---|---|---|---|
| _1 | 0.953 | +0.001 | 10 | **-2** | 2 | **-9** | 0 |
| _2 | 0.976 | -0.001 | 11 | — | 5 | -2 | 0 |
| _3 | 0.877 | +0.007 | 13 | **-5** | 11 | **-8** | 0 |
| _4 | 0.857 | — | 11 | -2 | 6 | **-9** | 0 |
| _5 | 0.770 | +0.003 | 12 | **-3** | 37 | **-11** | 0 |
| _6 | 0.803 | +0.001 | 16 | **-9** | 40 | **-12** | 0 |
| _7 | 0.600 | **+0.102** | 15 | **-7** | 44 | **-15** | 0 |
| M2 | 0.781 | +0.003 | 14 | **-6** | 166 | -5 | 0 |

- **Every clip's distinct-id count collapsed toward the ~13–15 roster** (no more 18–25), **teleports
  fell on every clip**, cross-camera agreement is stable-or-up everywhere (+0.102 on the worst clip),
  and **same-camera collisions stay 0**. Read jointly, this is a clean, generalised improvement — the
  first time all 8 sit at/near the true roster.
- **Remaining weak spot:** M2 teleports (166) — a genuine congested-crease ID-swap storm on the
  hardest clip (opposite bowling end, run-outs); next target. The `min_emit_frames` prior is
  conservative (30 frames); all dropped ids were 6–25-frame fragments, no real full-clip player lost
  (agreement never dropped). 152 unit tests green; flags-off remains byte-identical.
- **Config:** `configs/p3_association_v5.yaml` + `configs/p4_global_id_v5.yaml`.

---

## Ghost markers v2 + mosaic/BEV modernization (WS1/WS4)

- **`geometry.ground_point_visible_in`** (new): cheirality (via the pitch-oriented
  `camera_axis_lookat` forward axis) + per-camera in-frame test — the visibility primitive the old
  ghost code lacked (it reprojected in-frame points that were actually *behind* the camera).
- **Ghosts for disappeared ids in ALL visible cameras** (`render_phase1_videos.py`): a last-known
  fused-position store lets a ghost be drawn for an id gone from *every* camera (not just occluded in
  one), in each camera that geometrically frames that ground, faded by age; "occluded" vs "lost"
  labels. Greyed ghost dots added to the bird's-eye view.
- **BEV rebuilt** as a metric field radar: uniform world→pixel scale (circles no longer distorted),
  30-yard ring, pitch strip + popping creases + stumps from world coordinates, scale bar, modern
  markers. Verified visually on _7 frame 40 — ghosts appear correctly across cam_01/03/04/05/06 and
  the roster greys out lost ids.
- **Fixes:** unified colour system on `identity_colors` (retired the standalone BEV's golden-ratio
  hash and its binding_id-vs-global_player_id hollow-marker join bug); NVENC now reported honestly in
  the video manifest (`ffmpeg/h264_nvenc`).
- **In-pipeline ghost verification** = the stitching-v2 pose gate + descriptor-gated re-entry: a lost
  id's fragment only re-joins its owner when the body-shape descriptor agrees (a gated auto-merge,
  cannot-link preserved), which is the "if a ghost coincides with a pose, same shape ⇒ same id" rule.

## Verdict so far (WS1–WS5)
The v5 stack is a clean, generalised identity win: distinct ids sit at/near the ~13–15 roster on all
8 (was 18–25 on the hard clips), teleports are down on every clip, cross-camera agreement is up on
the worst clip (+0.102) and never regresses, same-camera collisions remain 0, and the mosaics now
expose ghosts + a real field radar for diagnosis. Deferred (post-checkpoint): P4a billboard-posture
teleport veto on facing pairs, cross-delivery prior calibration for anchor-starved clips, and
reprojection-split for any residual chimeras.
