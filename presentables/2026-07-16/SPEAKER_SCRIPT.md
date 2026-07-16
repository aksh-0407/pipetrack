# Speaker script, pipeline walkthrough + today's work
*(my notes, first person, say it in my own words, don't read verbatim)*

## 0. Opening (30 sec)
"The system takes the 7 synchronised camera feeds and produces, for every player, a single 3D skeleton
and a consistent identity across all cameras for the whole delivery. I'll walk the pipeline end to end, 
from 2D detection to the final refined 3D, then show before/after and what I changed since the last
build. I'll flag honestly what worked, what didn't, and what's still open."

Keep one line ready: *"Everything's on the calibrated ground plane, because that's where cricket geometry
is well-behaved, the players are on a flat pitch and calibration is cm-accurate."*

---

## 1. P1, 2D inference *(the eyes)*
- **What:** for each camera frame, find every person (a detector draws boxes) and estimate their 2D
 skeleton inside each box (26 joints, "Halpe-26", the usual body joints plus the **feet**).
- **How / intuition:** it's **top-down**, first "where are the people," then "what pose is each one in."
 The detector is **RTMDet**; the pose model is **RTMPose**. Top-down = the pose model sees a clean
 cropped person, so per-joint accuracy is high.
- **Why feet matter:** feet on the ground give us the most reliable "where on the pitch is this player."
- **Key limitation (be honest):** everything downstream inherits P1. If the detector misses a dark or
 distant umpire, no later stage can invent them. That detector-recall bound is our biggest front-end gap.

## 2. Stage 01, stabilization *(steady the shaky 2D)*
- **What:** off-the-shelf keypoints jitter a pixel or two every frame even on a still player. This stage
 smooths each joint's path over time, once, before anything uses it.
- **Intuition:** clean the signal at the source so five later stages don't each re-fight the same shake.
- **How:** a **One-Euro filter**, a smoother that smooths hard when a joint is still but backs off the
 instant it moves fast, so we kill jitter without smearing a real bat-swing. Measured ~32% less jitter.
- **Note:** it's wired but opt-in (`--enable-stabilization`).

## 3. Stage 02, per-camera tracking *(follow each person within one camera)*
- **What:** link the per-frame boxes into short tracks *within each camera* ("this box now is the same
 person as that box last frame").
- **How / intuition:** **ByteTrack**-style two-pass matching + a **Kalman filter** (a little "where will
 they be next frame" predictor). We match on box-overlap **and body-pose similarity**, because
 **colour/jersey is useless here**, both teams wear near-identical kit, so we lean on pose shape.
- **Limitation:** the motion model is constant-velocity, which struggles with sharp cricket manoeuvres
 (a diving fielder), so tracks fragment there, stage 05 stitches those back.

## 4. Stage 03, cross-camera association *(the same human, seen from different cameras)*
- **What:** decide which player in camera A is the same physical person as which in camera B. This is the
 hard core of the whole system.
- **Intuition:** 7 cameras see the same ~13 people from different angles; this is the "these two blobs are
 the same human" matcher.
- **How:** we do it on the **ground plane**, a player's feet map to one spot on the pitch, so if two
 cameras' detections land on the same spot, they're probably the same person. We fuse several weak clues
 (ground position, body-pose shape, motion) rather than trust any one.
- **The hard part (say this, it's the honest answer to "why isn't it perfect"):** our co-observing camera
 pairs face each other (~opposite sides). That's **low parallax**, the usual cross-camera geometry
 ("epipolar") becomes unreliable there, and from opposite sides two different players can look almost
 identical. So the facing pairs are where identity is hardest, and that's the main reason cross-camera
 agreement sits around 0.88 not 0.99.

## 5. Stage 04, 3D lift *(cross the camera views into one 3D body)* **triangulation vs lifting**
- **What:** take a player's 2D skeleton as seen by several cameras at the same instant and reconstruct
 their **3D skeleton** in real-world metres.
- **This is the manager's question, say it clearly:**
 - **Triangulation** = combine the 2D observations from **two or more cameras** to pin a 3D point
 geometrically (like your two eyes giving depth). Needs ≥2 views. **This is what we actually do**, 
 per joint, with a robust method that ignores a bad camera (**RANSAC** + a weighted linear solve).
 - **Lifting** = *infer* 3D from a **single** 2D view using a learned body prior (no second camera).
 - **So: our stage is named "04 lift" but it is multi-view triangulation, not monocular lifting.** True
 single-view lifting is future work, needed for the ~39% of frames only one camera sees.
- **Limitation:** if only one camera sees a player, we can't triangulate, so no 3D for them yet.

## 6. Stage 05, global identity *(one lasting ID per player)*
- **What:** turn the per-frame matches into persistent IDs (P001…) that survive occlusion and camera
 hand-offs for the whole clip, the colours you see on the mosaic.
- **How / intuition:** an online tracker on the ground plane (a smarter Kalman that models acceleration,
 so a bowler speeding up is handled), plus an offline pass that stitches fragments back together. Hard
 rule: two people in the same camera-frame can never share an ID, that's guaranteed by construction.

## 7. Stage 06, roles
- **What:** label each ID as bowler / striker / non-striker / keeper / umpire from where they stand and
 move relative to the pitch. Purely geometric; never changes identity.

## 8. Stage 07, refine *(NEW, make the 3D physically real and smooth)* **you built this today**
- **The three things you flagged last time, fixed here:**
 1. **Impossible limbs / stretched bones** we rebuild the skeleton from the mid-hip outward with
 **constant, left-right-symmetric bone lengths**, and clamp joints so knees/elbows can't bend
 backward. So limb lengths stay real.
 2. **Hip wobble** we smooth the hip (the root) with a *lower* cutoff than the limbs, so the whole
 body stops shaking while genuine limb motion is kept.
 3. **Low-confidence joints** any joint the model isn't sure about is dropped and refilled from its
 neighbours in time, instead of trusted raw.
- **Intuition / honesty:** it runs *after* identity and only edits the 3D positions, it never touches
 IDs. It's offline, so we can use a zero-lag smoother. This is what makes the final skeleton look
 physically believable.

---

## 9. What changed since last time (V8 now)
- **Restructured** to a single clean 3D triangulation (Halpe-26 with feet), keyed to identity.
- **Cap fix** in association the facing-pair "same player split into two IDs" problem: agreement
 0.862 to 0.883 across 40 deliveries, and colocated ghost-ID pairs went to 0.
- **Teleport gate (A3)** the "marker flies across the field and back" artefact: **367 to 0** across 40,
 with no IDs lost. *(This is the visible ghost-marker fix you saw last time.)*
- **Partial-ghost drop** head-only / cut-off single-camera ghosts removed at output.
- **New refine stage** (above).

## 10. The hip-projection / lifting work you asked me to do, honest result
- I did three things: (a) **hip-to-ground emission**, use the triangulated hip projected straight down
 as the player's ground position instead of the noisy feet; (b) a **robust triangulation** refinement;
 (c) the **refine stage's hip de-wobble**.
- **Honest outcome:** (a) and (b) were **metric-neutral**, they didn't move the numbers, so I've left
 them as options, not defaults. The *visible* improvement in the markers came from the **teleport gate
 (A3)** and the **refine** stage, not from changing the position source. I'd rather tell you that
 straight than claim a win that isn't there.

---

## 11. Clips walk-through (good + bad, show progress both ways)
- **14_3 (good):** clean in both builds; current is steadier, shows we didn't break the easy case.
- **M2 (hard, the big win):** last build had markers teleporting; now the teleport gate holds them, 
 point at the specific spot (~9 s) where the old one jumps and the new one doesn't.
- **14_7 (still hard, be honest):** low cross-camera agreement (~0.50), this is the facing-pair
 low-parallax case; still our worst, and it's on the roadmap (better detector + single-view 3D).

---

## 12. Anticipated questions, crisp answers
- **"Lift or triangulation?"** Triangulation (multi-view geometry). The stage is *named* lift but
 triangulates. Monocular lifting is future work for single-camera frames.
- **"Did the hip projection work?"** Built and tested; it was metric-neutral, so it's an option not a
 default. The visible marker fix came from the teleport gate + refine.
- **"How do you match players with identical kit / no numbers?"** Ground-plane position first, then
 body-pose shape. Colour is statistically dead here, so we don't rely on it.
- **"Why is agreement ~0.88, not higher?"** The facing camera pairs are low-parallax; that's the
 fundamentally hard geometry. The cap fix recovered the safe headroom there.
- **"Do markers still teleport?"** No, the gate takes emitted teleports to 0. The underlying cause is
 a brief id mis-association; the gate suppresses the visible jump; the deeper fix (splittable clustering
 / 3D tracking) is on the roadmap.
- **"Players only one camera sees?"** ~39% of frames, no 3D yet; single-view lifting is the planned
 fix.
- **"How do you measure without ground truth?"** Proxy metrics, cross-camera agreement, teleport
 count, same-camera collisions (always 0), colocated ghosts. Real MOTA/IDF1/HOTA needs hand labels, a
 known gap I'd flag as next.
- **"Biggest remaining problem?"** The front of the pipe, detection recall (dark/distant players) and
 single-camera 3D coverage. That's where the next big gains are.
