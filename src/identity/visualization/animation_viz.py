import json
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

# Toggle this boolean to reverse the facing direction by 180 degrees
FLIP_FORWARD = True

# Specify the player ID to isolate and bound the camera to
TARGET_PLAYER = "P001"

CONNECTIONS = [
    ("head", "neck"), ("nose", "neck"),
    ("nose", "left_eye"), ("left_eye", "left_ear"),
    ("nose", "right_eye"), ("right_eye", "right_ear"),
    ("neck", "left_shoulder"), ("left_shoulder", "left_elbow"), ("left_elbow", "left_wrist"),
    ("neck", "right_shoulder"), ("right_shoulder", "right_elbow"), ("right_elbow", "right_wrist"),
    ("neck", "hip"),
    ("hip", "left_hip"), ("left_hip", "left_knee"), ("left_knee", "left_ankle"),
    ("left_ankle", "left_heel"), ("left_ankle", "left_big_toe"), ("left_ankle", "left_small_toe"),
    ("hip", "right_hip"), ("right_hip", "right_knee"), ("right_knee", "right_ankle"),
    ("right_ankle", "right_heel"), ("right_ankle", "right_big_toe"), ("right_ankle", "right_small_toe")
]

def calculate_facing_direction(joints, flip_forward=False):
    """Calculates the facing direction parallel to the ground plane."""
    try:
        rh = np.array(joints["right_hip"])
        lh = np.array(joints["left_hip"])
        v_hip = lh - rh
        v_hip_xy = np.array([v_hip[0], v_hip[1], 0.0])
        world_up = np.array([0.0, 0.0, 1.0])
        facing_vec = np.cross(v_hip_xy, world_up)
        
        norm = np.linalg.norm(facing_vec)
        if norm == 0:
            return np.array([0.0, 1.0, 0.0]) 
            
        facing_vec = facing_vec / norm
        if flip_forward:
            facing_vec = -facing_vec
        return facing_vec
    except KeyError:
        return np.array([0.0, 1.0, 0.0])

def load_frames(jsonl_file_path):
    """Reads a JSON Lines file and returns a list of frame data."""
    frames = []
    with open(jsonl_file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                frame_data = json.loads(line)
                frames.append(frame_data)
            except json.JSONDecodeError:
                print("Skipping invalid JSON line.")
    return frames

def animate_3d_poses(jsonl_file_path):
    frames_data = load_frames(jsonl_file_path)
    if not frames_data:
        print("No valid frame data found.")
        return

    # 1. Pre-calculate global bounds for the target player to keep the camera steady
    all_x, all_y, all_z = [], [], []
    for frame in frames_data:
        for player in frame.get("players", []):
            if TARGET_PLAYER and player.get("global_player_id") != TARGET_PLAYER:
                continue
            
            pose_3d_named = player.get("pose_3d_named")
            if not pose_3d_named:
                continue
                
            joints_relative = pose_3d_named.get("joints_root_relative_m", {})
            root_world = pose_3d_named.get("root_world_m", [0, 0, 0])
            
            for rel_coords in joints_relative.values():
                all_x.append(root_world[0] + rel_coords[0])
                all_y.append(root_world[1] + rel_coords[1])
                all_z.append(root_world[2] + rel_coords[2])

    if not all_x:
        print(f"No valid 3D joint data found for target player {TARGET_PLAYER}.")
        return

    # Create a fixed bounding box based purely on the target player's movements
    x_mid, y_mid, z_mid = np.mean([min(all_x), max(all_x)]), np.mean([min(all_y), max(all_y)]), np.mean([min(all_z), max(all_z)])
    max_range = max(max(all_x) - min(all_x), max(all_y) - min(all_y), max(all_z) - min(all_z)) / 2.0
    
    # Pad the range slightly to ensure joints don't clip the edges of the box
    max_range *= 0.5

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    player_colors = {}
    color_palette = plt.cm.get_cmap("tab10").colors

    def update(frame_idx):
        ax.clear()
        frame_data = frames_data[frame_idx]
        current_frame_id = frame_data.get("frame_index", frame_idx)

        # Enforce strict, equal axis limits derived from the target player's footprint
        ax.set_xlim3d([x_mid - max_range, x_mid + max_range])
        ax.set_ylim3d([y_mid - max_range, y_mid + max_range])
        ax.set_zlim3d([z_mid - max_range, z_mid + max_range])
        ax.set_box_aspect(aspect=(1, 1, 1))

        ax.set_xlabel('X World (meters)')
        ax.set_ylabel('Y World (meters)')
        ax.set_zlabel('Z World (meters)')
        ax.set_title(f'3D Pose Animation - Frame: {current_frame_id} (Locked to {TARGET_PLAYER})')

        for player in frame_data.get("players", []):
            player_id = player.get("global_player_id", "Unknown")
            
            if TARGET_PLAYER and player_id != TARGET_PLAYER:
                continue

            pose_3d_named = player.get("pose_3d_named")
            if not pose_3d_named:
                continue

            role = player.get("role", "unknown")
            joints_relative = pose_3d_named.get("joints_root_relative_m", {})
            root_world = pose_3d_named.get("root_world_m", [0, 0, 0])

            joints_world = {}
            for joint_name, rel_coords in joints_relative.items():
                joints_world[joint_name] = (
                    root_world[0] + rel_coords[0],
                    root_world[1] + rel_coords[1],
                    root_world[2] + rel_coords[2]
                )

            if not joints_world:
                continue

            xs = [coords[0] for coords in joints_world.values()]
            ys = [coords[1] for coords in joints_world.values()]
            zs = [coords[2] for coords in joints_world.values()]
            
            if player_id not in player_colors:
                player_colors[player_id] = color_palette[len(player_colors) % len(color_palette)]
            p_color = player_colors[player_id]

            # Scatter points
            ax.scatter(xs, ys, zs, label=f"{player_id} ({role})", color=p_color, s=25)

            # Draw bones
            for joint1, joint2 in CONNECTIONS:
                if joint1 in joints_world and joint2 in joints_world:
                    ax.plot([joints_world[joint1][0], joints_world[joint2][0]],
                            [joints_world[joint1][1], joints_world[joint2][1]],
                            [joints_world[joint1][2], joints_world[joint2][2]], 
                            color=p_color, alpha=0.6, linewidth=2)

            # Draw Facing Direction Arrow
            facing_dir = calculate_facing_direction(joints_world, flip_forward=FLIP_FORWARD)
            root_pos = np.array(joints_world.get("hip", root_world))
            
            arrow_length = max_range * 0.25 # Adjusted scale for a tighter bounding box
            ax.quiver(root_pos[0], root_pos[1], root_pos[2], 
                      facing_dir[0], facing_dir[1], facing_dir[2], 
                      length=arrow_length, color='red', normalize=True, arrow_length_ratio=0.3)

        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(handles, labels, loc='upper right')

    ani = animation.FuncAnimation(fig, update, frames=len(frames_data), 
                                  interval=50, repeat=True)
    
    plt.show()

if __name__ == "__main__":
    # Point this to your local jsonl file 
    animate_3d_poses(r"pipetrack_v8-selected__CCPL080626M1_1_16_4\06_roles\predictions\bt_01__CCPL080626M1_1_16_4__cam_01.jsonl")