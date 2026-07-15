#!/usr/bin/env python3
"""Convert selected pipetrack_v8 deliveries to the latest g1_player_frame/v1 (Halpe-26) format.

Reformats an existing v8 run (READ-ONLY on the source) into the current schema + run layout:

    <out-run>/<DELIVERY>/{00_inference,01_stabilization,02_tracking,03_association,
                          04_lift,05_global_id,06_roles}/

Per-record promotion: pose_2d <- pose_2d_native (26 Halpe); pose_3d <- pose_3d_native (26) plus a
self-describing pose_3d_named (root = mid-hip, joints root-relative); the *_native blocks are
dropped; schema_version -> g1_player_frame/v1. Roles are stamped onto the 06_roles terminal records
from p5/roles.json. Diagnostics/metrics are copied verbatim. Identity/3D are NOT recomputed.

v8 stage -> new stage:
    p1_rtmpose-x-tiled(flat) -> 00_inference   p1b -> 01_stabilization   p2 -> 02_tracking
    p3 -> 03_association       p3_5 -> 04_lift  p4 -> 05_global_id        p6_3d(+p5) -> 06_roles
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from core.contract import validate_group1_frame  # noqa: E402
from core.keypoints import HALPE26_KEYPOINTS, named_root_relative  # noqa: E402

# (v8 per-delivery stage dir, new stage dir). 00_inference is handled separately (flat P1).
STAGE_MAP = [
    ("p1b", "01_stabilization"),
    ("p2", "02_tracking"),
    ("p3", "03_association"),
    ("p3_5", "04_lift"),
    ("p4", "05_global_id"),
    ("p6_3d", "06_roles"),
]


def _promote_player(player: dict, roles_map: dict[str, str] | None) -> dict:
    p = dict(player)
    native2 = p.pop("pose_2d_native", None)
    if native2 is not None:
        p["pose_2d"] = {
            "skeleton": "halpe26",
            "keypoints_px": native2["keypoints_px"],
            "keypoints_norm": native2["keypoints_norm"],
            "confidence": native2["confidence"],
        }
    native3 = p.pop("pose_3d_native", None)
    if native3 is not None and native3.get("keypoints_world_m"):
        p["pose_3d"] = {
            "keypoints_world_m": native3["keypoints_world_m"],
            "confidence": native3["confidence"],
            "mean_reprojection_error_px": native3["mean_reprojection_error_px"],
        }
        pts = np.array(
            [[float("nan")] * 3 if v is None else v for v in native3["keypoints_world_m"]],
            dtype=float,
        )
        p["pose_3d_named"] = named_root_relative(pts, HALPE26_KEYPOINTS)
    else:
        # Only the native 26-joint skeleton is canonical; drop any stale COCO-17 pose_3d.
        existing = p.get("pose_3d")
        if not (isinstance(existing, dict) and len(existing.get("keypoints_world_m", [])) == 26):
            p["pose_3d"] = None
    if roles_map is not None:
        gid = p.get("global_player_id")
        if gid and str(gid) in roles_map:
            p["role"] = roles_map[str(gid)]
    return p


def _convert_record(record: dict, roles_map: dict[str, str] | None) -> dict:
    rec = dict(record)
    rec["schema_version"] = "g1_player_frame/v1"
    rec["players"] = [_promote_player(pl, roles_map) for pl in rec.get("players", [])]
    validate_group1_frame(rec, final_handoff=False)
    return rec


def _convert_jsonl(src: Path, dst: Path, roles_map: dict[str, str] | None) -> int:
    dst.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with src.open("r", encoding="utf-8") as fin, dst.open("w", encoding="utf-8") as fout:
        for line in fin:
            if not line.strip():
                continue
            fout.write(json.dumps(_convert_record(json.loads(line), roles_map),
                                  sort_keys=True, allow_nan=False) + "\n")
            n += 1
    return n


def _copy_aux(src_stage: Path, dst_stage: Path) -> None:
    """Copy every non-predictions artifact (diagnostics/, *_metrics.json, run_manifest.json) verbatim."""
    if not src_stage.is_dir():
        return
    for item in src_stage.iterdir():
        if item.name == "predictions":
            continue
        dest = dst_stage / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            dst_stage.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, dest)


def _load_roles(roles_json: Path) -> dict[str, str]:
    if not roles_json.is_file():
        return {}
    payload = json.loads(roles_json.read_text())
    return {str(gid): (entry or {}).get("role", "unknown")
            for gid, entry in (payload.get("roles") or {}).items()}


def convert_delivery(delivery: str, v8_root: Path, p1_dir: Path, out_run: Path,
                     mosaic_src: Path | None, viz_out: Path | None) -> dict:
    v8d = v8_root / "deliveries" / delivery
    outd = out_run / delivery
    counts: dict[str, int] = {}

    # 00_inference: the flat P1 predictions for this delivery.
    p1_pred = p1_dir / "predictions"
    n0 = 0
    for src in sorted(p1_pred.glob(f"*__{delivery}__*.jsonl")):
        n0 += _convert_jsonl(src, outd / "00_inference" / "predictions" / src.name, None)
    counts["00_inference"] = n0

    roles_map = _load_roles(v8d / "p5" / "roles.json")
    for v8_stage, new_stage in STAGE_MAP:
        src_stage = v8d / v8_stage
        dst_stage = outd / new_stage
        rm = roles_map if new_stage == "06_roles" else None
        n = 0
        for src in sorted((src_stage / "predictions").glob("*.jsonl")):
            n += _convert_jsonl(src, dst_stage / "predictions" / src.name, rm)
        counts[new_stage] = n
        _copy_aux(src_stage, dst_stage)

    # 06_roles also carries the role solver artifacts from v8 p5.
    for name in ("roles.json", "suppression.json"):
        srcf = v8d / "p5" / name
        if srcf.is_file():
            (outd / "06_roles").mkdir(parents=True, exist_ok=True)
            shutil.copy2(srcf, outd / "06_roles" / name)

    # Reference mosaic (v8-rendered; the README notes it is the 17-joint render).
    if mosaic_src and viz_out:
        for mp4 in sorted(mosaic_src.glob(f"*{delivery}*.mp4")):
            (viz_out / delivery).mkdir(parents=True, exist_ok=True)
            shutil.copy2(mp4, viz_out / delivery / mp4.name)

    return counts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--v8-root", default="/home/ubuntu/pipetrack_v8")
    ap.add_argument("--p1-dir", default="/home/ubuntu/pipetrack_v8/p1_rtmpose-x-tiled")
    ap.add_argument("--out-run", required=True, help="e.g. ~/bits-pose-data/derived/40_full/pipetrack_v8-selected")
    ap.add_argument("--viz-out", default=None, help="e.g. ~/bits-pose-data/viz/40_full/pipetrack_v8-selected")
    ap.add_argument("--mosaic-src", default="/home/ubuntu/pose-estimation-benchmark/artifacts/mosaics_all40")
    ap.add_argument("--deliveries", required=True, help="comma-separated delivery ids")
    args = ap.parse_args()

    v8_root, p1_dir, out_run = Path(args.v8_root), Path(args.p1_dir), Path(args.out_run)
    viz_out = Path(args.viz_out) if args.viz_out else None
    mosaic_src = Path(args.mosaic_src) if args.mosaic_src else None
    deliveries = [d.strip() for d in args.deliveries.split(",") if d.strip()]

    manifest = {"schema_version": "conversion/v1", "source_run": str(v8_root),
                "target_schema": "g1_player_frame/v1", "deliveries": {}}
    for delivery in deliveries:
        counts = convert_delivery(delivery, v8_root, p1_dir, out_run, mosaic_src, viz_out)
        manifest["deliveries"][delivery] = counts
        print(f"{delivery}: " + ", ".join(f"{k}={v}" for k, v in counts.items()))

    out_run.mkdir(parents=True, exist_ok=True)
    (out_run / "conversion_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"\nWrote {len(deliveries)} deliveries -> {out_run}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
