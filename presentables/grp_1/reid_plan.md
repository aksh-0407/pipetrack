The concrete plan, step by step
Step 1, per camera, per frame: run person detection + 2D pose (the full.md shortlist, with RTMO-l as a strong one-stage candidate for crowded, occluded scenes). Output: bbox + keypoints + per-keypoint confidence.

Step 2, per camera, across frames (temporal track): feed detections to a per-camera tracker so each person gets a local track id. Candidates to benchmark: DeepSORT and PipeTrack (Kalman motion + association). Output: tracklets per camera, exactly like selected_track_ids in the current ball *_2D.json, but one per person instead of one ball.

Step 3, across cameras, per frame (the ReID core): match local tracklets between cameras using geometry, not appearance:

Projection-matrix / triangulation consistency (the "neat trick"): triangulate a candidate person across a camera pair and reproject; a low per-camera pixel error means it is the same person. This reuses the exact reprojection check the ball pipeline already does.
Epipolar consistency: a keypoint in camera A must lie near its epipolar line in camera B.
Ground-plane test: project each person's foot/ankle to the surveyed pitch plane; two detections at the same world (x, y) are the same person.
Build a cost matrix from these geometric residuals and solve the camera-to-camera assignment (Hungarian).

Step 4, global ID: cluster the agreeing cross-camera matches into one global P00x per physical person (one identity, all 7 views).

Step 5, maintain over time: tracklet stitching + temporal smoothing to repair ID switches and bridge occlusion and exit/entry, so the global id survives the whole delivery.

