# Changes this cycle, accepted / rejected / neutral / open

Honest status of everything tried. (I will present the accepted and the rejected items plainly; I won't sell the marginal
ones as wins.)

## Accepted, in the pipeline, measured
| Change | What it does | Result |
|---|---|---|
| **Restructure** (Halpe-26, single binding-keyed triangulation) | one clean 3D lift keyed to identity; feet kept | the base for everything below |
| **Cap fix** (facing-pair under-merge) | lets a confident ground-match merge a split player across the facing cameras | agreement rose **0.782 to 0.916** (same 8); 40-set 0.853 to 0.883; ghost pairs to 0 |
| **Refine stage (07, NEW today)** | physics-valid bones + hip de-wobble + low-conf refill on the 3D | fixes the stretched-limb / backward-knee / shaky-hip issues you flagged |
| **Roles v1 solver** | epoch Hungarian role assignment | core-role coverage 24/32 to 29/32 |

## Built + measured win, awaiting your sign-off to make default
| Change | Result | Status |
|---|---|---|
| **A3 teleport gate** | emitted teleports fell **422 to 0** (same 8); 40-set 367 to 0, no IDs lost | 40-confirmed; needs your OK to enable by default |
| **IMPACT-2 partial-ghost drop** | drops head-only / cut-off single-cam ghosts; 13 dropped on 40, agreement held | clean; needs your mosaic verdict |

## Built but metric-neutral, kept as options, not defaults (honest)
| Change | Why parked |
|---|---|
| **1A hip-to-ground emission** (your ask) | projecting the triangulated hip to the ground was **metric-neutral**, didn't move the numbers |
| **1C robust triangulation refit** | marginal (reproj p95 6.61 to 6.56 px); RANSAC already robust |

## Enabled in production, but effect inconclusive on our test set (NOT claimed as wins)
`graph_shape_enabled`, `graph_split_enabled`, `graph_facing_gate_scale`, `use_measurement_covariance`
(distance-R), `adaptive_lost_window` are all **on** in the shipped config. Turning each off on the 8-clip
set is **byte-identical (shape/split/parallax) or noise-level (R/lost-window, ±0.0003 agreement)**, i.e.
they target hard-clip failures (chimeras, low-parallax) that barely occur in these 8. Whether they help on
the chimera-heavy 40-set worst clips is **not yet measured.** Presented as "in the pipeline, effect on hard
clips still being verified," not as wins.

## Rejected, with the reason
| Change | Why rejected |
|---|---|
| **Tracklet-id lock** | stabilised IDs by relabelling put a stable **wrong-person** ID on a player. A regression the baseline never had. |
| **1F single-view sticky-hip lift** | tried to give single-camera frames a hip position on a learned plane **raised** teleports (33 to 35); noisier than the foot. |

## Yet to be tried / tested, the roadmap
| Item | Why it matters |
|---|---|
| **Detector upgrade / RTMO** | detection recall (dark/distant umpires) is the front-end ceiling; misses here are unrecoverable |
| **OC-SORT for stage 02** | the constant-velocity tracker fragments on sharp cricket manoeuvres |
| **Single-view (PnP) 3D lift** | ~39% of frames are single-camera, so no 3D yet; this is the coverage gap |
| **Full decide-in-3D tracking** | run identity on the 3D pose, not just the 2D ground plane |
| **05b stitching fix** | fragments aren't being bridged (18 to 25 IDs vs ~11 roster) |
| **Identity ground truth** | every identity number is a *proxy* today; need labels for real MOTA/IDF1/HOTA |
| **40-hard-clip A/B** | to actually measure whether shape/split/parallax earn their place |
| **Config + minor bug tidy** | `emit_kalman_posterior` is on but ineffective; dataclass defaults disagree with the shipped YAML |
