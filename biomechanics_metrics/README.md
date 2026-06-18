# Release Point Detection Analytics
**Team:** Group 2 – Broadcast Biomechanics  
**Context:** Phase 1 (Validation & Testing)  

## 1. Executive Summary
Group 2 is tasked with calculating the 3D Release Point (BT-101) and associated metrics (BT-102, BT-R104). Officially, finding the exact `release_frame` is the responsibility of Group 3 (Event Timeline). However, due to parallel development timelines, **Group 2 must autonomously estimate the release frame** to unblock our spatial analytics and K-Means clustering algorithms.

This document outlines the pipeline usage, how synthetic data is generated to test our logic, and the various methods explored for detecting the true release frame using purely 3D skeletal data (17 COCO keypoints).

---

## 2. Running the Pipeline Locally

### A. Data Generation
Because we are operating under a manual bypass strategy without live upstream data, we use a surrogate data generator to simulate 3D biomechanical tracking. 

To generate the dataset, run:
`python generate_dataset.py`

**What this does:**
* Synthesizes 100 delivery clips (100 frames each) of a pace bowler running down the pitch.
* Employs a non-linear "sigmoid whip" to accurately simulate the biomechanical acceleration and deceleration of the bowling arm.
* Injects randomized Gaussian noise to mimic multi-camera triangulation jitter.
* Exports the clips to `data/mock/clip_*.json` strictly adhering to the `Role_Event_Label_Schema.xlsx` contract.
* Generates a `_ground_truth.json` answer key for grading our algorithms.

### B. Executing the Analysis
To process the generated batch and grade the release point algorithms, run:
`python run_analysis.py`

**What this does:**
* Ingests the JSON batch and normalizes the world coordinates into a pitch-relative reference frame.
* Applies a Savitzky-Golay filter to smooth triangulation jitter while preserving velocity peaks.
* Executes both the Baseline and Composite detection algorithms (detailed below).
* Outputs a terminal report detailing the Mean Absolute Error (MAE) of our algorithms compared to the ground truth.

---

## 3. Implemented Detection Methods (In Codebase)
These algorithms are currently active in `biomechanics_engine.py` and are benchmarked automatically when running `run_analysis.py`.

### A. The Kinematic Velocity Proxy (The "Old" Baseline)
* **Status:** Implemented (`estimate_proxy_release`)
* **Concept:** Calculates the frame-to-frame 3D velocity magnitude of the bowling wrist. The frame with the absolute maximum velocity is flagged as the release frame.
* **Accuracy on Synthetic Data:** Mean Absolute Error (MAE) of ~1.05 frames.
* **Pros:** Extremely fast, mathematically simple, highly accurate on clean data for pace bowlers.
* **Cons:** Fragile. If there is triangulation noise, a glitch, or a fielder crosses the camera, a false velocity spike will trick the algorithm. 

### B. The Composite 3D + Kinematic Algorithm (The Current Champion)
* **Status:** Implemented (`compute_composite_release`)
* **Concept:** A blended heuristic combining spatial geometry and physics.
  1. **Wrist Velocity:** Normalizes wrist velocity (like Method A).
  2. **3D Elbow Angle:** Calculates the angle between the upper arm and forearm vectors. Peak extension (~180°) aligns with the release.
  3. **Sequential Deceleration (Kinetic Chain):** Applies penalty multipliers if the biomechanical sequence is wrong. The shoulder must peak/decelerate *before* the elbow, which peaks *before* the wrist.
* **Accuracy on Synthetic Data:** MAE of ~1.45 frames.
* **Pros:** Highly resistant to camera noise and triangulation jitter. False velocity spikes are ignored if the elbow isn't extended or the kinetic sequence is broken.
* **Cons:** Slightly more computationally expensive; relies on accurate shoulder/elbow tracking, not just the wrist.

---

## 4. Future / Alternative Paths of Work
If the Composite Method requires further refinement or fails in edge cases on the real Group 1 JSONs, the team can pursue these alternative methods.

### C. Centripetal Acceleration Drop-off (Calculus-Driven)
* **Status:** Brainstormed (Not Implemented)
* **Concept:** The bowling arm acts as a pendulum. The wrist experiences massive centripetal acceleration directed toward the shoulder during the swing. At release/follow-through, this rigid circular path breaks. 
* **Implementation Path:** Calculate the 3D acceleration vector of the wrist and project it onto the wrist-to-shoulder radial vector. Look for a massive, cliff-like drop in this value to mark the release.

### D. 1D CNN Temporal Surrogate (Data-Driven ML)
* **Status:** Brainstormed (Not Implemented - Phase 3 Potential)
* **Concept:** Instead of hardcoding physics rules, we train a lightweight 1D Convolutional Neural Network (CNN) on our synthetic JSONs and manual ground-truth data.
* **Implementation Path:** Pass the `(N_frames, 17, 3)` tensor into a CNN that convolves across time to output a predicted frame integer. Can be exported as `.onnx` for microsecond execution.

### E. Group 3 Event Gating (The Final Target Architecture)
* **Status:** Blocked (Waiting on upstream dependency)
* **Concept:** Group 3 provides the exact `release_frame` integer in their payload.
* **Implementation Path:** We disable our proxy heuristics and simply array-index our smoothed tensor: `release_point = smoothed_data[group3_release_frame, wrist_idx, :]`.

---

## 5. Discarded Methods
### F. Ball-Wrist Intersection (Geometric Ideal)
* **Status:** Impossible given current schema.
* **Reason:** This method tracks both the ball and the wrist, marking the release where their spatial vectors diverge. However, the upstream RTMPose pipeline provided by Group 1 **does not output ball tracking coordinates**. We only have 17 human keypoints.

---
## Summary for Developers
Right now, default to the **Composite 3D + Kinematic Algorithm** for all downstream metric calculations (BT-101, BT-T203, etc.). If you are modifying the pipeline, test your changes by running `python run_analysis.py` against the `mock` dataset to ensure the MAE stays below 2 frames.