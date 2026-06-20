# Presentation Script (Aksh: Phases 0, 1, 2)

This is my speaking script for the Week 4 review. It is written to be **read from or
glanced at** while presenting. Emphasis is on the **why** and **how**, not just listing
what we did. Each section has: talking points, key numbers to say out loud, and likely
questions with answers.

**Order of delivery:** Opening → Weeks 1 to 3 → Phase 0 → Phase 1 → Mosaic video demo →
Phase 2 and roadmap → Hand off to Vedant.

**Companion documents (open these as I go):**
- [01_weeks1-3_research.md](01_weeks1-3_research.md)
- [02_week4_phase0_phase1.md](02_week4_phase0_phase1.md)
- [03_phase2_and_roadmap.md](03_phase2_and_roadmap.md)

---

## 0. Opening (about 45 seconds)

> "Our group, Group 1, owns the part of the cricket pipeline that takes raw footage from
> seven cameras and turns it into one clean, identified 3D skeleton per player, smooth
> enough for Unreal Engine to animate on broadcast. The work splits into seven phases. I
> will present the first three: Phase 0, the foundation; Phase 1, detecting players and
> their poses in each camera; and Phase 2, which is what we build next. Vedant will then
> take Phases 3 and 4, and Anshul takes 5 to 7."

Why frame it this way: it tells the professor the *shape* of the whole problem before any
jargon, and makes clear this is one connected pipeline, not scattered tasks.

---

## 1. Weeks 1 to 3: the research (about 2 minutes)

**The why:** "Before building anything, we had to choose a pose-estimation model. There
are dozens, and they disagree hugely on speed versus accuracy. Choosing wrong would waste
the whole internship."

**The key insight to land:** "We do not want the most accurate model, and we do not want
the fastest. The most accurate models are too slow for live broadcast; the fastest ones
drop joints when players overlap. We need the **middle ground**: fast enough for
real-time, accurate enough to look right." (Show the quadrant chart in
[01_weeks1-3_research.md](01_weeks1-3_research.md).)

**The how / what we built:**
- "We surveyed and **audited over 50 pose models** released after 2020, recording each
  one's accuracy and speed with the source for every number."
- "We built a **shared benchmarking repository** with a fixed protocol, so every model we
  test later is measured the same way and the results are reproducible across the team.
  This is what makes all our future numbers trustworthy and comparable."

**Key numbers to say:** "50-plus models audited; metrics like AP for accuracy and FPS and
latency for speed; all sourced from official papers and model cards."

**Land the bridge:** "That survey gave us a shortlist. When we got the real data and
needed a working pipeline fast, the survey told us to start with YOLO26x-pose as a quick,
deployable baseline. That is exactly what we did in Week 4."

---

## 2. Phase 0: foundation (about 1.5 minutes)

**The why:** "Phase 0 is the unglamorous but essential step: prove the ground is solid
before building on it. Confirm the data is complete and synchronised, the calibration
files actually work, and the format we hand to the other groups is agreed and frozen."

**The how:** "We wrote an **automated readiness audit**. It checks four things: the
dataset inventory, the calibration, the existing ball pipeline, and the output contract.
It writes compact evidence files we can re-run any time."

**The honest, important point:** "The audit splits into two statuses. Internally,
everything **passes**: 7 cameras, 600 frames each, all synchronised, calibration valid.
Externally, it is **blocked** on seven items that are **management decisions, not code**:
who owns the validation data, who labels the ground truth, and what accuracy counts as
passing. We surfaced and escalated these instead of guessing. So Phase 0 is technically
complete; the open items are decisions above our level."

**Why the contract matters:** "By freezing the output JSON now, even with the identity
and 3D fields left empty as placeholders, Groups 2 and 3 can start building against it in
parallel, before our later phases are done."

**Key numbers:** "7 cameras, 600 frames each, 2560 by 1440 resolution; 4 technical checks
all green; 7 external decisions escalated."

---

## 3. Phase 1: per-camera perception (about 2 minutes)

**The why:** "This is the front-end everything downstream depends on. For every camera
and every frame, we detect each person and estimate their 2D pose, meaning 17 body joints
with a confidence score each."

**Define gently:** "A bounding box is just a rectangle around each person. The 17
keypoints are standard body joints: shoulders, elbows, wrists, hips, knees, ankles, and
so on. Confidence is how sure the model is about each joint, which we use later to throw
out noise."

**The problem:** "The existing pipeline only detects the **ball**. Every detection was
labelled 'ball', no people, no joints. Detecting many players and their joints, on tight
crops at this resolution, is new work."

**The how and the model choice:** "We used **YOLO26x-pose** and ran it over the full
delivery. We chose it deliberately as our minimum-viable baseline: it does detection and
pose in one model, deploys easily, and gets us a working end-to-end pipeline fastest.
This matches the recommendation from our Week 1 to 3 survey. It is the starting point,
not the final model; we will benchmark stronger ones like RTMO and RTMW next."

**Key numbers to say out loud:**
- "Across all 7 cameras and 600 frames each, that is **4,200 frames**, we produced
  **13,170 player detections** with **zero failed frames**."
- "Speed was **16.6 frames per second end-to-end**, and the pure model inference was
  about **11 milliseconds per frame**." (Show the per-camera bar chart.)

**Pre-empt the speed question:** "That 16.6 FPS includes reading 4K images off disk. The
model itself runs at about 11 milliseconds, roughly 90 FPS. Real-time throughput is a
later optimisation; Phase 1's goal was correct perception, which it meets."

---

## 4. Demo: the 7-camera mosaic video (about 2 minutes)

> Play the mosaic video here. Talking script while it plays:

**Set up what they are looking at:** "This is all seven cameras shown in one synchronised
grid, the same instant of the same delivery from seven angles. Each coloured box is a
detected player; the lines inside are the estimated skeleton."

**Point at the cameras:** "Top row and field cameras see the most players; this tight
side camera sees only one or two. Notice the detector is finding people correctly across
every angle."

**Now the honest gap, this is the key teaching moment:** "But watch closely. Three things
are wrong, and these are exactly what the next phases fix:"
1. "**The skeletons jitter** frame to frame. That is noise we have to smooth."
2. "**There are no identities.** The same player is treated as a brand-new person every
   frame and in every camera. Nothing links this player here to the same player there."
3. "**There are no roles.** Nothing yet knows who is the bowler, the striker, or the
   keeper."

**Close the demo:** "So detection works. The remaining job, identity, roles, and smooth
3D, is what Phases 2 through 7 deliver."

**Command to regenerate the video (if asked, or to have ready):**
```bash
python3 scripts/render_cricket_p1_videos.py \
  --drive-root drive \
  --run-dir benchmarks/runs/p1-yolo26x-CCPL080626M1_1_14_1
```
Output lands in `benchmarks/artifacts/p1-yolo26x-CCPL080626M1_1_14_1/videos/`: seven
per-camera MP4s plus the combined mosaic (`..._all_cameras.mp4`).

---

## 5. Phase 2 and the roadmap (about 1.5 minutes)

**Phase 2, our next week:** "Right now each camera detects players frame by frame with no
memory. Phase 2 gives each camera memory: we link a player's detections over time so they
keep one stable ID through movement and brief occlusion. The output is per-camera
'tracklets', one continuous path per person."

**The how:** "Standard multi-object tracking, adapted to our footage: a motion filter
predicts where each player should appear next, an appearance fingerprint helps confirm
matches, and we add a geometry prior from the calibrated cameras. We will benchmark a few
trackers and report ID switches per delivery and track completeness."

**Hand to the roadmap (show the diagram in
[03_phase2_and_roadmap.md](03_phase2_and_roadmap.md)):** "After Phase 2, Phase 3 matches
the same player across all seven cameras using **geometry**, because the kits are
identical, appearance alone fails; if two detections triangulate to the same real-world
point, they are the same person. Phase 4 turns that into one global ID per player. Phase
5 assigns cricket roles. Phase 6 builds and smooths the 3D and exports to Unreal. Phase 7
validates it."

**Hand off:** "Vedant will now take you through Phases 3 and 4 in detail."

---

## 6. Anticipated questions and answers

| Likely question | Short answer |
| --- | --- |
| **Why YOLO26x and not the most accurate model?** | It is our fast, deployable baseline to get a working end-to-end pipeline. We will benchmark stronger models (RTMO-l, RTMW-x) next; our Week 1 to 3 survey already shortlisted them. |
| **Why is the skeleton jittery? Is that a bug?** | No, it is expected. Per-frame detection has small errors; without tracking and smoothing (Phases 2 and 6) it shows as jitter. Removing it is precisely our later work. |
| **Why use 7 cameras?** | One camera cannot recover true depth. Multiple calibrated cameras let us triangulate joints into real 3D and stay robust when some views are occluded. |
| **What does "blocked" in Phase 0 mean? Did something fail?** | Nothing technical failed. "Blocked" means seven decisions need management input (data ownership, who labels ground truth, accuracy thresholds). We escalated them rather than assume. |
| **How will you tell identical-looking players apart across cameras?** | Geometry, not appearance. If detections in two cameras triangulate to the same world point and their feet land on the same pitch spot, they are the same person. This reuses the proven ball-tracking reprojection check. |
| **Is 16.6 FPS fast enough for live broadcast?** | That figure includes disk reads of 4K frames. Model inference is ~11 ms (~90 FPS). Real-time optimisation is a later step; Phase 1 targeted correctness. |
| **What is your ground truth / how do you measure accuracy?** | That is one of the escalated Phase 0 blockers: who produces manual ID, role, and 3D labels. Once set, Phase 7 measures association accuracy, ID switches, and role accuracy on a blind dataset. |

---

### One-line close

> "In four weeks we went from a research survey, to a frozen, validated foundation, to a
> working multi-camera detection pipeline producing 13,170 clean detections, and we have
> a clear, phase-by-phase plan to turn that into smooth, identified 3D for broadcast."
