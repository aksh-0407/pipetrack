import os
import json
import numpy as np
import glob
from biomechanics_engine import BroadcastAnalytics

DATA_DIR = "data/mock"

def load_clip_tensor(filepath):
    with open(filepath, 'r') as f:
        clip_data = json.load(f)

    tensor_data = []
    for frame in clip_data:
        # BUG 3 FIXED: frame["players"] is a list; subscripting it with a string key
        # ("pose_3d") raised TypeError: list indices must be integers, not str.
        # Fixed by indexing element [0] to get the player dict first.
        keypoints = frame["players"][0]["pose_3d"]["keypoints_world"]
        tensor_data.append(keypoints)
    return np.array(tensor_data)  # Shape: (100, 17, 3)

if __name__ == "__main__":
    print("Initializing Analytics Engine...")
    analytics = BroadcastAnalytics(fps=50)

    gt_path = os.path.join(DATA_DIR, "_ground_truth.json")
    if not os.path.exists(gt_path):
        raise FileNotFoundError("Run generate_dataset.py first.")

    with open(gt_path, 'r') as f:
        ground_truth = json.load(f)

    clip_files = sorted(glob.glob(os.path.join(DATA_DIR, "clip_*.json")))

    # Tracking metrics
    proxy_errors = []
    composite_errors = []

    print("\nRunning algorithms over dataset...")
    for fp in clip_files:
        clip_id = os.path.basename(fp).replace(".json", "")
        true_release = ground_truth[clip_id]

        raw_pose_data = load_clip_tensor(fp)
        normalized_data = analytics.normalize_coordinates(raw_pose_data)
        smoothed_data = analytics.apply_kinematic_filter(normalized_data)

        # 1. Run Old Method (Raw Velocity Peak)
        proxy_release = analytics.estimate_proxy_release(smoothed_data, analytics.KP['R_Wrist'])

        # 2. Run New Method (Composite 3D Angle + Sequence)
        composite_release = analytics.compute_composite_release(
            smoothed_data,
            analytics.KP['R_Shoulder'],
            analytics.KP['R_Elbow'],
            analytics.KP['R_Wrist']
        )

        # Calculate absolute errors
        proxy_errors.append(abs(proxy_release - true_release))
        composite_errors.append(abs(composite_release - true_release))

    # --- CALCULATE FINAL ACCURACY METRICS ---
    proxy_errors = np.array(proxy_errors)
    composite_errors = np.array(composite_errors)

    total_clips = len(clip_files)

    print("\n" + "="*45)
    print("   ALGORITHM ACCURACY REPORT (100 Clips)")
    print("="*45)
    print(f"Old Method (Velocity Only):")
    print(f"  - Mean Absolute Error : {np.mean(proxy_errors):.2f} frames")
    print(f"  - Exact Matches (0 err): {np.sum(proxy_errors == 0)} / {total_clips}")
    print(f"  - Usable (<= 2 err)   : {np.sum(proxy_errors <= 2)} / {total_clips}")
    print("-" * 45)
    print(f"New Method (Composite 3D + Kinematic):")
    print(f"  - Mean Absolute Error : {np.mean(composite_errors):.2f} frames")
    print(f"  - Exact Matches (0 err): {np.sum(composite_errors == 0)} / {total_clips}")
    print(f"  - Usable (<= 2 err)   : {np.sum(composite_errors <= 2)} / {total_clips}")
    print("="*45)