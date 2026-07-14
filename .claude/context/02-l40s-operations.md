# L40S box operations

> **RESTRUCTURE 2026-07-14:** repo reorganised into `src/{core,identity}` + `tools/`, stages renumbered (`01…06`), single `pose-lab` env, benchmarking off `main`. New layout/commands: see `01-current-state.md` + `04-conventions.md`. The L40S box is UNCHANGED until it pulls the branch and rebuilds/renames its env — its `/home/ubuntu/...` paths and old `pN` stage-dir names below remain valid as-is.


- **SSH**: `ssh quidich-gpu-intern` (ubuntu@3.238.21.21, key `~/.ssh/quidich-gpu-intern.pem`).
  L40S 46 GB VRAM, 8 vCPU EPYC, 61 GB RAM. ALL GPU work runs here (user directive); CPU-bound
  pipeline can run either side (laptop i9 is ~1.5× faster CPU but crashes; box is stable).
- **Repo**: `~/pose-estimation-benchmark` (github aksh-0407/pose-estimation-benchmark).
  Sync: user pushes → `git pull` on box; for fast iteration rsync files then reconcile via
  stash→ff-pull→verify→drop (worked cleanly).
- **Data**: `~/pose_data/{bt1,bt2,bt3}/<delivery>/camera<NN>/frame_*.jpg` (40 deliveries ×
  7 cams × 600 @ 2560×1440; cam_07 panoramic 3775×960; byte-identical to the laptop's
  `drive/dataset/bt_0X`). **Drive-layout bridge** `~/render_drive/dataset/` = symlinks
  bt_0X→pose_data/btX + copied `calibration-data/` + `events-data/` — REQUIRED by P2+ and
  renders (`--drive-root ~/render_drive`).
- **Envs**: `cricket-rtmpose-l` (torch 2.1 cu121 + mmdet/mmpose + numpy/scipy/cv2/yaml —
  runs BOTH P1 and the CPU pipeline). Static ffmpeg at `~/bin/ffmpeg` (johnvansickle build —
  check nvenc support before GPU-render work; renderer probes `_ffmpeg_has_nvenc()`).
- **P1 production command** (18–25 fps, 168k frames ≈ 2.2 h):
  `python scripts/inference/run_phase1_l40s.py --tiled-det --nms-thr 0.55 --det-batch-size 4
   --io-workers 12 --prefetch-batches 3 --pose-batch-size 256 --output-dir <out>`
  (fp16 + worker-side crop prep default ON; `--resume` safe; ALWAYS include cam_07 in probes
  — the pad-to-/32 incident).
- **Chain**: `bash scripts/pipetrack/run_v8_l40s.sh` (uses `--deliveries all`, v8 configs,
  `--jobs 7`; ~5–6 h for 40 on 8 vCPU). Panel: driver `--panel-only`.
- **Renders**: `render_phase1_videos.py --drive-root ~/render_drive --run-dir <D>/p4
  --mode mosaic --show p4 --letterbox-tiles` (~10 min/delivery, 2 parallel; CPU-bound —
  see VRAM lead in 05).
- **Monitors**: ALWAYS arm one per long run (user directive): ssh-poll the log for
  progress + `Done in|Error|Traceback|CUDA|Killed`, 5–10 min cadence, retry-tolerant
  (4 consecutive ssh misses before declaring). pgrep patterns must not self-match the ssh
  command string.
