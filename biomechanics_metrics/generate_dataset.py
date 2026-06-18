import numpy as np
import json
import os
import math

OUTPUT_DIR = "data/mock"
NUM_FRAMES = 100
NUM_CLIPS = 100  # Generating a large batch for accuracy testing

def generate_static_skeleton():
    skeleton = np.zeros((17, 3))
    z_ankle, z_knee, z_hip, z_shoulder, z_head = 0.1, 0.5, 1.0, 1.5, 1.75
    w_shoulder, w_hip = 0.4, 0.3

    # BUG 1 FIXED: every line was reassigning the local variable `skeleton` to a
    # plain Python list instead of writing into the numpy array by row index.
    skeleton[15] = [-w_hip/2,      0, z_ankle]    # L_Ankle
    skeleton[16] = [ w_hip/2,      0, z_ankle]    # R_Ankle
    skeleton[13] = [-w_hip/2,      0, z_knee]     # L_Knee
    skeleton[14] = [ w_hip/2,      0, z_knee]     # R_Knee
    skeleton[11] = [-w_hip/2,      0, z_hip]      # L_Hip
    skeleton[12] = [ w_hip/2,      0, z_hip]      # R_Hip
    skeleton[5]  = [-w_shoulder/2, 0, z_shoulder] # L_Shoulder
    skeleton[6]  = [ w_shoulder/2, 0, z_shoulder] # R_Shoulder
    skeleton[7]  = [-w_shoulder/2, 0, z_hip]      # L_Elbow
    skeleton[8]  = [ w_shoulder/2, 0, z_hip]      # R_Elbow
    skeleton[9]  = [-w_shoulder/2, 0, z_knee]     # L_Wrist
    skeleton[10] = [ w_shoulder/2, 0, z_knee]     # R_Wrist
    skeleton[0]  = [0,             0, z_head]      # Nose/Head
    return skeleton

def simulate_delivery_stride(true_release_frame, noise_level):
    base_skeleton = generate_static_skeleton()
    frames_data = np.zeros((NUM_FRAMES, 17, 3))
    y_positions = np.linspace(-8.0, -1.0, NUM_FRAMES)
    arm_length = 0.65 
    
    for t in range(NUM_FRAMES):
        current_skeleton = np.copy(base_skeleton)
        # Constant run-up speed
        current_skeleton[:, 1] += y_positions[t]
        
        # THE SIGMOID WHIP (Non-linear velocity)
        # k controls the sharpness of the kinetic snap. 
        # A value of 0.4 creates a sharp peak exactly at true_release_frame.
        k = 0.4 
        
        # Calculate the sigmoid value (0.0 to 1.0)
        try:
            sigmoid = 1 / (1 + math.exp(-k * (t - true_release_frame)))
        except OverflowError:
            sigmoid = 0.0 if t < true_release_frame else 1.0
            
        # Map the sigmoid to the rotation arc (0 to 1.5 PI)
        theta = sigmoid * 1.5 * math.pi
        
        pivot_y, pivot_z = current_skeleton, current_skeleton
        
        # Rotate Wrist
        current_skeleton = pivot_y - (arm_length * math.sin(theta))
        current_skeleton = pivot_z + (arm_length * math.cos(theta))
        
        # Rotate Elbow (with a slight bend)
        bend_offset = 0.1 * math.sin(theta)
        current_skeleton = pivot_y - ((arm_length/2) * math.sin(theta)) - bend_offset
        current_skeleton = pivot_z + ((arm_length/2) * math.cos(theta))
            
        # Inject randomized camera jitter
        current_skeleton += np.random.normal(0, noise_level, (17, 3))
        frames_data[t] = current_skeleton
        
    return frames_data

def export_batch():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    ground_truth = {}

    print(f"Generating {NUM_CLIPS} simulated deliveries...")

    for i in range(1, NUM_CLIPS + 1):
        clip_id = f"clip_{i:03d}"
        # Randomize the true release between frame 65 and 85
        true_release = int(np.clip(np.random.normal(75, 4), 65, 85))
        # Randomize the noise level (simulating good vs bad camera angles)
        noise_level = np.random.uniform(0.01, 0.05)

        tensor = simulate_delivery_stride(true_release, noise_level)
        ground_truth[clip_id] = true_release

        clip_payload = []
        for t in range(NUM_FRAMES):
            clip_payload.append({
                "camera_id": "rig_virtual_01",
                "frame_index": t,
                "players": [{
                    "global_player_id": "P001", "role": "bowler",
                    "pose_3d": {"keypoints_world": tensor[t].tolist()},
                    "pose_2d": {"keypoints": [], "confidence": np.random.uniform(0.85, 0.99, 17).tolist()},
                    "track_confidence": 0.98
                }]
            })

        with open(os.path.join(OUTPUT_DIR, f"{clip_id}.json"), 'w') as f:
            json.dump(clip_payload, f)

    # Save the answer key
    with open(os.path.join(OUTPUT_DIR, "_ground_truth.json"), 'w') as f:
        json.dump(ground_truth, f, indent=4)

    print("Dataset generation complete. Ground truth saved.")

if __name__ == "__main__":
    export_batch()