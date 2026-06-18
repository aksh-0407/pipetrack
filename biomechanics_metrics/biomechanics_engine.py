import numpy as np
from scipy.signal import savgol_filter
from sklearn.cluster import KMeans

class BiomechanicsPipeline:
    def __init__(self, fps=50):
        self.fps = fps
        self.KP = {
            'L_Shoulder': 5, 'R_Shoulder': 6,
            'L_Hip': 11, 'R_Hip': 12,
            'L_Elbow': 7, 'R_Elbow': 8,
            'L_Wrist': 9, 'R_Wrist': 10,
            'L_Knee': 13, 'R_Knee': 14,
            'L_Ankle': 15, 'R_Ankle': 16
        }

    def normalize_coordinates(self, pose_data, bowling_from_north=False):
        normalized_data = np.copy(pose_data)
        if bowling_from_north:
            normalized_data[:, :, 1] = -normalized_data[:, :, 1]
        return normalized_data

    def apply_kinematic_filter(self, pose_data, window=7, poly=2):
        if len(pose_data) < window:
            window = len(pose_data) if len(pose_data) % 2 != 0 else len(pose_data) - 1
        return savgol_filter(pose_data, window_length=window, polyorder=poly, axis=0)

    # --- THE OLD PROXY (METHOD B) ---
    def estimate_proxy_release(self, smoothed_data, wrist_idx):
        wrist_coords = smoothed_data[:, wrist_idx, :]
        # Pad the velocity array to maintain frame count alignment
        velocities = np.pad(np.linalg.norm(np.diff(wrist_coords, axis=0), axis=1), (1,0), 'edge')
        return np.argmax(velocities)

    # --- THE NEW COMPOSITE ALGORITHM (METHODS 1 + 2) ---
    def compute_composite_release(self, smoothed_data, shoulder_idx, elbow_idx, wrist_idx):
        """
        Blends 3D Elbow Angle (Method 1) with the Kinetic Chain (Method 2).
        """
        S = smoothed_data[:, shoulder_idx, :]
        E = smoothed_data[:, elbow_idx, :]
        W = smoothed_data[:, wrist_idx, :]

        # 1. Kinematic Chain Velocities (Method 2)
        v_S = np.pad(np.linalg.norm(np.diff(S, axis=0), axis=1), (1,0), 'edge')
        v_E = np.pad(np.linalg.norm(np.diff(E, axis=0), axis=1), (1,0), 'edge')
        v_W = np.pad(np.linalg.norm(np.diff(W, axis=0), axis=1), (1,0), 'edge')

        # Normalize Wrist Velocity to
        norm_v_W = (v_W - v_W.min()) / (v_W.max() - v_W.min() + 1e-9)

        # 2. 3D Elbow Extension Angle (Method 1)
        u = S - E # Vector from Elbow to Shoulder
        v = W - E # Vector from Elbow to Wrist
        
        dot_uv = np.sum(u * v, axis=1)
        norm_u = np.linalg.norm(u, axis=1)
        norm_v = np.linalg.norm(v, axis=1)
        
        # Calculate angle in radians and normalize (pi radians / 180 degrees = 1.0)
        cos_theta = np.clip(dot_uv / (norm_u * norm_v + 1e-9), -1.0, 1.0)
        angle_rad = np.arccos(cos_theta)
        norm_angle = angle_rad / np.pi 

        # 3. Apply Sequential Deceleration Penalties
        shoulder_peak_frame = np.argmax(v_S)
        elbow_peak_frame = np.argmax(v_E)

        composite_scores = np.zeros(len(smoothed_data))
        for t in range(len(smoothed_data)):
            # The physical snap happens *after* the shoulder decelerates
            if t < shoulder_peak_frame:
                kinetic_multiplier = 0.1 # Heavy penalty for premature spikes
            elif t < elbow_peak_frame:
                kinetic_multiplier = 0.5 # Medium penalty
            else:
                kinetic_multiplier = 1.0 # Optimal kinetic window
                
            # Composite Score = Velocity * Straightness * Sequence Timing
            composite_scores[t] = norm_v_W[t] * norm_angle[t] * kinetic_multiplier

        return np.argmax(composite_scores)

class BroadcastAnalytics(BiomechanicsPipeline):
    def __init__(self, fps=50):
        super().__init__(fps)
        # (Keep your existing calculate_step_out_distance, cluster_bowling_angles, compute_body_zones here)