# Campaign knowledge — settled verdicts (do NOT re-litigate without new evidence)

Full record: docs/critical-analysis/fixes-log.md. Highlights:

**Detection**
- RTMDet only detects at its trained object scale: native hi-res (1280/2560) LOSES boxes;
  tiling wins (superset recall, min box 33→12 px).
- NMS 0.55 (from 0.3) lets both crossing players survive: +0.10–0.13 agreement — the
  largest single identity gain. IoM-0.7 containment kills seam fragments.
- Tiled fast path = crop slicing/resize in prefetch workers + direct
  data_preprocessor→predict (3.2× throughput; fp16 parity ≤3.7 px on usable joints).
  cProfile misleads on this codebase (per-call overhead) — use wall-clock section timing.

**Identity**
- Ghost-under-player = split identity (one player, two global ids in disjoint camera sets).
  Fixed by W9: P3 union-lift merge (one coherent 3D skeleton explaining all views = one
  person) + P4 colocated-id merge (co-located ≥25f within 0.75 m + never share a
  camera-frame + stature agrees). `coloc` panel column + verdict = permanent tripwire.
- Facing pairs C1↔C4, C2↔C6, C3↔C5 (co-observing, low parallax). Colour cue dead (d′≈0),
  bone ratios abstain; billboard posture (STATURE_QUANTITIES) is the facing-pair-capable
  shape channel.
- REJECTED with evidence: contested-camera down-weighting (−0.08 on its target clip);
  H3 posture policy (binding collapse); symmetric measurement-R (gate loosening);
  trainable ReID (no GT).
- P4b stitching is temporal-only; occupancy (same camera-frame) veto = the two-people test.

**Roles (v1.2)**: 6 Hungarian slots (bowler/striker/non-striker/keeper/2 umpires with
distinct geometry), latch + final uniqueness; direction = plausible-band run detection
(3–9.5 m/s — unbanded, tracking teleports fake 20–30 m/s "runs") else pre-shot two-sign
geometric cost. `_14_x` groups do NOT share one bowling end (proven: opposite clean runs).

**3D**: z=0 Gauss–Newton+Huber ground solve (cm-accurate calibration); cheirality =
origin-referenced sign test (det(M) formula wrong on this rig); triangulation core is
batched + bit-identical (W10-PERF); coverage gap = single-camera frames (F16 PnP lift is
the lever).

**Perf**: box CPU chain bottleneck is P3 (solve/IO, flat profile); P6 = 10 s/delivery.

**Incidents**: cam_07 pad-to-/32 (fast-path probes must cover the panoramic cam);
calibration provenance (copied laptop→box, verified + team-confirmed single session);
box-vs-local panels are near-parity not identical when P1 binaries differ.
