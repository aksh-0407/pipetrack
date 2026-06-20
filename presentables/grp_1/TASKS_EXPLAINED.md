# Group 1 — TASKS_EXPLAINED

The plain-language companion to [CORE_TASKS.md](CORE_TASKS.md). Same 8 phases, same plan — but
here the goal is **understanding**: what each task means, *why* we do it, and what every piece of
jargon actually refers to. If you're new to computer vision, read this first.

Audience: 2nd-year CS undergrad. No prior pose-estimation knowledge assumed.

*Citation tags (`[SRC]` authoritative repo file, `[DOCS]` internal write-up — inferred,
`[INFERRED]` our reasoning, `[WEB]` external) are used lightly here; the strict version lives in
[CORE_TASKS.md](CORE_TASKS.md).*

---

## 0. The problem in one paragraph

We have **7 cameras** all filming the **same cricket delivery** from different angles, already
calibrated and time-synced `[SRC: dataset/]`. We want the computer to do three things:
1. Notice every person on the field and give each one a sticky label — `P001`, `P002`, … — that
   **stays the same person** across all 7 camera views and across all 600 frames. That's **ReID**.
2. Figure out **what each person is doing** — bowler, batter, keeper, umpire, fielder. That's
   **role classification**.
3. Work out **where each person's body is in real 3D space**, smoothly enough to animate.

Why bother? Because two other teams build everything on top of this. If our IDs flicker or our
3D jitters, their stories and officiating tools break `[DOCS: docs/03_...md §1]`.

### The one idea that drives everything: trust geometry, not looks

Every player wears the **same kit**. So "they look similar, must be the same person" fails badly
`[SRC: Problem_Statement.xlsm, Known risks]`. But we *do* know exactly where each camera sits and
how it sees the world (calibration). So we lean on **geometry** — physical position and angles —
which doesn't care about jersey colour. Appearance is only a tie-breaker. This is why the plan
says "geometry-first" everywhere `[SRC: Problem_Statement.xlsm, Approach]`.

---

## 1. Glossary — every term, with an analogy

### The basics
| Term | Plain meaning | Analogy |
|---|---|---|
| **Detection / bounding box (bbox)** | A rectangle the computer draws around a person it found in an image. | Drawing a box around each face in a photo app. |
| **Keypoints / 2D pose** | 17 dots marking body joints (shoulders, elbows, knees…) in the flat image. | Connect-the-dots skeleton drawn on the photo. |
| **Confidence** | How sure the model is about each dot (0–1). | A weather forecast saying "70% chance". |
| **Frame** | One still image. 600 frames ≈ a few seconds of one delivery. | One page of a flip-book. |
| **Occlusion** | When one player hides part of another. | Someone walking in front of you at a concert. |
| **Side-on overlap** | Two players line up so the camera sees them merge. | Two people standing one-behind-the-other from your seat. |

### Identity & tracking
| Term | Plain meaning | Analogy |
|---|---|---|
| **ReID (re-identification)** | Recognising the *same* person again — later in time, or in another camera. | Spotting your friend again after they walked behind a pillar. |
| **Track / tracklet** | A single person's path stitched across frames *within one camera*. | Following one runner's lane with your eyes. |
| **track_id** | The local label a tracker gives one person in one camera. | A cloakroom ticket — only meaningful in that one cloakroom. |
| **global_player_id (`P001`)** | The single label that means the same person in **all** cameras. | Your passport number — the same everywhere. |
| **ID switch** | A mistake where two people swap labels. | A relay race where runners grab the wrong baton. |
| **Tracklet stitching** | Joining track pieces that got cut by occlusion/exit. | Taping together a torn film strip. |

### Geometry (the heart of it)
| Term | Plain meaning | Analogy |
|---|---|---|
| **Calibration** | Knowing each camera's exact position, angle, and lens so we can do maths between cameras. | Surveyors knowing precisely where each telescope stands. |
| **Intrinsics** | A camera's *internal* properties (focal length, image centre). | The lens's own prescription. |
| **Extrinsics** | A camera's *position and rotation* in the world. | Where the tripod stands and which way it points. |
| **Projection matrix (3×4)** | The maths box that turns a 3D world point into a pixel for that camera. | A stamp that prints a 3D object onto that camera's film. |
| **Triangulation** | Using 2+ cameras' rays to pin a point's true 3D location. | Two coastguard stations crossing bearings to find a boat. |
| **Reprojection error** | Take the 3D point you computed, "re-stamp" it back into each camera, measure how far off the pixel is. Small = good. | Predicting where a star *should* appear in your telescope and checking it lands there. |
| **Epipolar line** | A point in camera A must sit somewhere along one specific line in camera B. | A laser pointer's beam: A's dot must fall along B's view of that beam. |
| **Ground-plane test** | Drop each player's feet onto the known pitch surface; same spot ⇒ same person. | Matching shadows on the floor instead of faces. |

### The maths/algorithm names (don't be scared of them)
| Term | What it does | Analogy |
|---|---|---|
| **Cost matrix** | A table of "how bad is it to call A and B the same person". | A compatibility-score grid for blind dates. |
| **Hungarian algorithm** | Picks the best one-to-one matching from that grid. | Seating planner that pairs guests with minimum unhappiness. |
| **RANSAC** | Throws out the one bad measurement that ruins an average. | Ignoring the obviously-wrong judge's score in gymnastics. |
| **Kalman filter** | Predicts where a moving thing goes next and corrects as data arrives. | Anticipating a ball's path to catch it. |
| **DeepSORT / ByteTrack / PipeTrack** | Ready-made trackers (Kalman + matching) we test. | Different brands of "follow that person" software. |
| **Temporal smoothing** | Removes frame-to-frame shakiness over time. | Image-stabilisation on a phone video. |
| **One-Euro / Savitzky-Golay filter** | Two specific smoothing recipes with different trade-offs. | Two camera "smoothing" presets — one fast, one cleaner. |

### 3D pose & animation (Phase 6)
| Term | Plain meaning | Analogy |
|---|---|---|
| **Inverse kinematics (IK)** | Given where the hand should be, compute the joint angles that put it there — legally. | Working out elbow/shoulder bend so your hand reaches a cup. |
| **Bone-length / joint-limit constraints** | Bones can't stretch and joints can't bend backwards. | A wooden puppet whose limbs are fixed length and hinge only one way. |
| **Foot-skate / foot-lock** | Bug where a planted foot slides on the ground; the fix pins it. | Gluing a standing foot so it stops ice-skating. |
| **Quaternion / SLERP** | A stable way to represent and smoothly blend rotations. | Smoothly steering a drone between two orientations without it flipping. |
| **Unreal / FBX / USD / Live Link** | The game engine that renders the final graphic, and the file/stream formats it eats. | Exporting your animation in a format the movie software can open. |

### Metrics (how we grade ourselves) — `[DOCS: docs/full.md]`
| Term | Meaning | Higher or lower better? |
|---|---|---|
| **AP / AP50-95** | Accuracy score for detection/keypoints across strictness levels. | Higher |
| **PCK** | % of keypoints close enough to truth. | Higher |
| **MPJPE** | Average 3D joint error in millimetres. | Lower |
| **Latency / FPS** | Time per frame / frames per second. | Lower latency, higher FPS |

---

## 2. What we already have, and what's missing

Think of the existing system as a **machine that tracks the cricket ball in 3D** and it already
works well `[SRC: dataset/events-data/]`. Its assembly line looks like this:

```
 2D detections  ->  cleaned 2D  ->  triangulated 3D  ->  cleaned 3D  ->  trimmed
   (per camera)                       (one point)                          |
                                                                            v
                            reprojection check  <----  predicted path / Unreal export
```

Two facts matter enormously:

1. **It only finds the ball.** Every detection is labelled `"ball"` — there is **no player
   detection at all** `[SRC: dataset/events-data/*_2D.json]`. Teaching the machine to find
   *players* (and their 17 joints) is literally our Phase 1 job.
2. **The assembly line shape is exactly what we need.** It already turns 2D → 3D, cleans it, and
   exports to Unreal — for *one* point. Our whole project is **upgrading it from one ball-point
   to many human joints, for many players** `[DOCS: grp_1/plan.md §3.3]`.

```
  THEM (today):   1 ball  -> 1 point in 3D
  US  (goal):     N players x 17 joints  -> N skeletons in 3D, each with a sticky ID + role
```

### A data note worth flagging
The cameras give us **images**, but nobody has yet written down "this is player P003, he's the
bowler" for any frame. That hand-written truth (called **ground truth**) is what we'd grade
ourselves against — and it doesn't exist yet `[SRC: Validation_Results.xlsx]`. We'll need someone
to annotate a subset, and ideally **more matches** later so we can prove it works beyond one game
`[INFERRED]`. *(This is a thing the team can help arrange.)*

---

## 3. The 8 phases — what & why, in order

The phases are ordered by **dependency**: each one needs the previous one's output. (You can't
track a player you haven't detected; you can't give a role to an identity you don't have yet.)

```
 P0  Understand + set up the data and the output format
  |
 P1  Find people + their joints, in each camera         (the "eyes")
  |
 P2  Follow each person across frames, per camera        (ReID across TIME)
  |
 P3  Match the same person across the 7 cameras  *core*  (ReID across ANGLES) <- geometry!
  |
 P4  Merge into ONE global ID per person; fix switches/gaps
  |
 P5  Label roles (bowler / batter / keeper / ...)
  |
 P6  Build smooth 3D skeletons + export to Unreal        (the "extension")
  |
 P7  Measure everything + write the reports + hand over
```

### P0 — Understand & set up
**What:** read the contract, lock the output format, check the cameras' calibration is sane, and
map which old machine parts we reuse. **Why:** if we don't agree the output format with the other
teams first, we'll build the wrong thing and redo it `[DOCS: docs/09_...md §10]`. *Could go
wrong:* starting before data access and ground-truth ownership are sorted — both are open
blockers `[SRC: Open_Questions_and_TODOs.xlsm]`.

### P1 — Find people and their joints (per camera)
**What:** for every camera and frame, draw a box around each person and place 17 joint dots on
them. **Why:** everything downstream is just "reasoning about these dots". **How:** test several
ready models (RTMPose, RTMO, etc.) on *our* footage and pick by accuracy-vs-speed — we don't
commit to one upfront `[DOCS: docs/full.md]`. *Could go wrong:* identical kits + tight zoomed-in
DRS shots make detection hard `[SRC: Problem_Statement.xlsm, Known risks]`.

### P2 — Follow each person through time (within one camera) — *ReID across frames*
**What:** connect a player's dots frame-to-frame so they keep one local ticket number even while
moving. **Why:** without this, every frame is strangers; we need continuity. **How:** Kalman-
based trackers (DeepSORT and friends) predict where someone will be next and match them
`[DOCS: reid_plan.md]`. *Could go wrong:* occlusion snaps the thread — we mark the gap for P4 to
mend.

```
 frame 1   frame 2   frame 3 (hidden)   frame 4
   o---------o          ?  <-- gap        o     same person, ID must survive
```

### P3 — Match the same person across cameras — *ReID across angles (THE CORE)*
**What:** decide that "person in camera 2" and "person in camera 5" are the same human. **Why:**
this is the actual deliverable — one identity seen from 7 angles. **How (pure geometry):**
- **Triangulate + reproject:** guess they're the same, compute their 3D point, stamp it back into
  every camera; if the pixels line up, they match `[SRC: events-data *_reprojection.json]`.
- **Epipolar line:** their position in camera A must fall on a specific line in camera B.
- **Ground plane:** their feet land on the same spot of the pitch.
Combine these into a score table and let the **Hungarian algorithm** pick the best pairing
`[DOCS: reid_plan.md Step 3]`. Looks (appearance) only break ties.

```
   Camera A            Camera B
   [  . p  ]  ----->   [   \      ]   p' lands on the line  => same person
                       [    \  p' ]
```
*Could go wrong:* two players overlapping side-on look identical from one camera — so we ask the
*other* cameras to break the tie `[SRC: Problem_Statement.xlsm, Known risks]`.

### P4 — One global ID + repair
**What:** fold the per-camera tickets and cross-camera matches into a single `P00x` per person,
then patch ID switches and occlusion gaps so it survives the whole delivery. **Why:** the other
teams need *one* stable handle per player. **Bonus:** early on we **hand-label** a few IDs (the
"manual-ID bridge") so Groups 2/3 aren't blocked while we automate `[DOCS: docs/09_...md §5]`.

### P5 — Roles
**What:** label each identity bowler/striker/non_striker/keeper/umpire/fielder/unknown. **Why:**
stories are role-specific ("show the bowler's run-up"). **How:** simple geometry rules + cricket
common sense ("keeper stands behind the striker's stumps", "only one bowler runs in")
`[SRC: Problem_Statement.xlsm, Approach]`; exact rules to confirm with Harsh `[INFERRED]`.

```
 behind striker's stumps?  -> keeper
 running in from far end?   -> bowler
 at a crease, set?          -> striker / non_striker
 still, in umpire spot?     -> umpire
 otherwise on field         -> fielder   (else: unknown)
```

### P6 — Smooth 3D skeletons + Unreal *(the extension)*
**What:** turn the matched 2D dots into a clean 3D skeleton and ship it to the game engine.
**Why:** the final graphic is rendered in **Unreal**, where any jitter shows as a twitching limb.
**How — a cleaning assembly line**, each stage killing one kind of noise:

```
 gating+RANSAC -> weighted triangulation -> reprojection reject -> time-smoothing
   -> bone-length/joint limits -> inverse kinematics + foot-lock -> rotation smoothing -> EXPORT
   (A)              (B)                  (C)                (D)        (E)            (F)            (G)
```
| Annoying glitch | Killed by |
|---|---|
| Dots shaking | gating (A) + smoothing (D) |
| One joint pops far away | RANSAC (A) + reprojection reject (C) |
| Limb missing when hidden | weighted triangulation (B) + IK fills it (F) |
| Bones changing length | bone constraints (E) |
| Standing foot slides | foot-lock (F) |
| Whole body shimmers | rotation smoothing (G) |

> **Honesty note:** the official sheet only *requires* IDs, roles, stable tracks, and uses 3D
> reprojection as a *check* `[SRC: Problem_Statement.xlsm; Validation_Results.xlsx]`. This whole
> 3D-cleaning + Unreal line is an **extension we're choosing to build** on top
> `[DOCS: grp_1/plan.md §8]`. FMPose3D / SAM3D / FreeMocap / OpenSim are only **time-boxed
> experiments** to look at, not commitments `[SRC: Experiment_Log.xlsx, W4]`.

### P7 — Measure, report, hand over
**What:** run on a held-out (blind) set, compute the scores, write the three reports, fill the
handover sheet. **Why:** "it looks good" isn't proof. **The five graded metrics:** association
accuracy, ID switches per delivery, role accuracy, track completeness, reprojection effect
`[SRC: Validation_Results.xlsx]`. *Catch:* the pass/fail targets for the first three are still
"management input required" — we literally can't say "accurate enough" until someone sets them.

---

## 4. How this maps to the week plan

The week plan `[DOCS: docs/06_Group1_Week_By_Week_Plan.md]` is the same work on a calendar:

| Phase | Roughly which week |
|---|---|
| P0, P1 | Week 1 |
| P2 | Week 2 |
| P3 | Week 3 |
| P4, P5 | Week 4 |
| P6 | spread across W2–W5 |
| P7 | Week 5 |

For the exact data shapes, candidate-model tables, and per-task exit criteria, switch to
[CORE_TASKS.md](CORE_TASKS.md).

---
*Team: Aksh (lead), Vedant, Anshul `[SRC: Problem_Statement.xlsm]`. Questions on any term above —
ask; this doc is meant to be expanded as we learn.*
