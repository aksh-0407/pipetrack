The remaining Phase 0 work is decision work, not engineering work. The audit found 7 external blockers in external_blockers.json, grouped into these areas.
1. DS-001: Official Control Dataset
DS-001 is supposed to be the main sprint/control dataset. The local drive/dataset is technically usable, but the programme sheet still has unresolved official metadata.
Needs decisions:
Who owns DS-001?
What is the official Drive/path for DS-001?
What is the capture date?
Is the current local dataset the official DS-001, or only a working copy?
Will DS-001 get manual ground truth, or is it only for development runs?
Why it matters: without this, people may benchmark on different copies or refer to different clip sets as “the dataset.”
2. DS-002: Blind Validation Subset
DS-002 is the held-out validation set. This is the dataset interns/models should not tune against.
Needs decisions:
Which exact deliveries/clips are DS-002?
Where is DS-002 stored?
Who can access it before validation week?
When will it be labelled?
Is DS-002 selected from the current 8 deliveries, or from another dataset?
Will it include all 7 cameras per delivery?
Why it matters: without DS-002, we can build and test, but we cannot honestly claim final validation. Everything is just development-set performance.
3. Dataset Access / Canonical Source
The open questions sheet still marks dataset access as “MANAGEMENT INPUT REQUIRED.”
Needs decisions:
Is the Google Drive link the canonical source?
Should the repo-local drive/ folder be treated as official, or just a local mirror?
Who is responsible for keeping local copies synced?
What should be committed versus kept local?
Why it matters: if the team works from inconsistent data copies, model outputs, labels, and validation reports will not line up.
4. Ground Truth Owner
This is the biggest practical blocker. The current dataset has frames and ball outputs, but no manual player labels.
Needs decisions:
Who is responsible for creating ground truth?
Who reviews/approves labels?
Which deliveries and frames should be labelled first?
Are we labelling every frame or sampled frames?
Are labels per-camera only, cross-camera, or both?
Minimum labels needed:
person bbox;
2D COCO-17 keypoints if pose accuracy is scored;
global_player_id across cameras/time;
role label;
optional 3D reference if available.
Why it matters: without ground truth, we can run models and visually inspect outputs, but cannot compute real ReID accuracy, role accuracy, or ID-switch metrics.
5. Annotation Tooling
Closely tied to ground truth ownership: the team must choose the actual labelling workflow.
Needs decisions:
Which tool: CVAT, Label Studio, custom JSON, spreadsheet-assisted review, etc.
What schema should labels export in?
Do labels use cam_01 style camera IDs and absolute frame numbers?
How are cross-camera identities assigned?
How are uncertain labels represented?
How are corrections/versioning handled?
Why it matters: bad annotation format creates rework. The output should map directly into the Phase 0 contract and validation scripts.
6. Validation Targets
Three official targets are unset:
Cross-camera association accuracy: target required.
ID switches per delivery: acceptable threshold required.
Role classification accuracy: target required.
These must become numbers, for example:
text



cross-camera association accuracy >= X%
ID switches per delivery <= Y
role classification accuracy >= Z%

Why it matters: without thresholds, we can report metrics but cannot say pass/fail.
7. G2/G3 Contract Sign-Off
The contract is implemented now, but Groups 2 and 3 still need to accept it as the handoff shape.
Needs decisions:
Do Groups 2/3 accept g1_player_frame/v0?
Are pixel coordinates enough, or do they require normalized coordinates too?
Do they need frame-level JSON, JSONL, or per-delivery files?
Is pose_3d nullable acceptable until later phases?
Are global_player_id, role, track_confidence, and pose_3d.keypoints_world_m sufficient?
Why it matters: Phase 0 engineering froze a sensible contract, but the consumers must agree before we treat it as the programme contract.
Bottom line: Phase 0 implementation is complete, but Phase 0 external readiness is not. The next meeting should resolve DS-001, DS-002, annotation ownership/tooling, validation thresholds, and G2/G3 contract sign-off.