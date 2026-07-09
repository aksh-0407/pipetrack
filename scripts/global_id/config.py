"""Validated configuration for P4a global tracking and P4b stitching."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

import yaml

from pose_estimation.cricket.ground_kalman import ROLE_PARAMS


def _default_role_params() -> dict[str, dict[str, float]]:
    return {
        role: {
            "alpha": params.alpha,
            "sigma_a": params.sigma_a,
            "measurement_noise": params.measurement_noise,
        }
        for role, params in ROLE_PARAMS.items()
    }


def _default_incompatible_roles() -> list[list[str]]:
    return [
        ["bowler", "wicketkeeper"],
        ["striker", "wicketkeeper"],
        ["bowler", "striker"],
        ["bowler", "non_striker"],
        ["umpire", "bowler"],
        ["umpire", "striker"],
        ["umpire", "wicketkeeper"],
    ]


@dataclass(frozen=True)
class P4AConfig:
    confirm_hits: int = 3
    lost_window_frames: int = 30
    bowler_lost_window_frames: int = 60
    chi2_gate_2dof: float = 5.991
    reentry_temporal_gate_frames: int = 120
    reentry_mahalanobis_gate: float = 5.991
    reentry_gap_scale_frames: float = 60.0
    reentry_kinematic_slack: float = 1.5
    role_latch_frames: int = 5
    cap_max_pos_var: float = 25.0
    confidence_high: float = 0.7
    confidence_discard: float = 0.3
    local_identity_mahalanobis_gate: float = 25.0
    # A (camera, P2-tracklet) -> global-track ownership claim expires after this
    # many frames without being re-asserted, so one bad P3 merge can no longer
    # weld two players together permanently. 0 keeps the legacy permanent claims.
    ownership_ttl_frames: int = 50
    # Shadow-id suppression: an unmatched observation within the chi2 gate of a
    # track that was already updated this frame is ABSORBED (identity-only)
    # instead of birthing a duplicate; a tentative sitting on top of a confirmed
    # track is not allowed to confirm until it either separates or persists
    # long enough to be a real player.
    shadow_confirm_gate_m: float = 1.2
    shadow_confirm_override_hits: int = 30
    # Cricket capacity prior: at most 15 people can be on the field (11 fielders
    # + 2 batsmen + 2 umpires). At the cap, a new id may only confirm well clear
    # of every existing confirmed track.
    expected_roster_max: int = 15
    roster_cap_min_separation_m: float = 3.0
    # Pose-shape temporal tie-breaker: added to the Stage-2 cost INSIDE the chi2
    # gate only, so it re-ranks admissible candidates but never opens/blocks a
    # match. 0 disables. Needs empirical tuning (no identity ground truth).
    pose_match_weight: float = 2.0
    pose_descriptor_ema: float = 0.15
    pose_min_updates: int = 5
    pose_min_shared_segments: int = 4
    # ID-3 teleport control. When > 0, a Stage-2 candidate whose mature pose-shape
    # descriptor differs from the track's by more than this bone-ratio distance is
    # VETOED (not merely penalised) inside the chi2 gate — a body of clearly the
    # wrong build can no longer capture a track. 0 keeps the additive tie-breaker only.
    pose_gate_veto_distance: float = 0.0
    # ID-2/ID-3. When > 0, reviving a deleted track from the re-entry pool requires
    # its pose-shape descriptor to agree with the observation within this distance
    # (abstains — allows — when either descriptor is immature/unshared, so behaviour
    # is unchanged where pose is unavailable). Blocks kinematically-plausible but
    # wrong-person re-entries (a teleport/ID-swap source).
    reentry_pose_max_distance: float = 0.0
    # ID-2 fragmentation. Adaptive lost-window: a well-established track (many hits)
    # is kept alive across occlusion for up to lost_window_max_frames instead of the
    # flat lost_window_frames, so a briefly-occluded confirmed player is re-acquired
    # rather than deleted and re-born as a fresh id. False keeps the flat window.
    adaptive_lost_window: bool = False
    lost_window_max_frames: int = 90
    # ID-2 cardinality prior. In a ~12 s cricket delivery every one of the ~13-15
    # people is present the whole clip, so a global id that survives only a handful
    # of frames is a fragment/shadow, not a late-entering player. When > 0, any id
    # whose total emitted frame-span is below this is dropped (its detections become
    # unlabelled) AFTER stitching has had its chance to absorb it. 0 = disabled.
    min_emit_frames: int = 0
    # Emit the chi2-gated Kalman POSTERIOR as the ground position instead of the raw
    # per-frame fused observation (ISSUE-5). The posterior cannot jump faster than the
    # gate allows, so a single bad/mis-associated measurement can no longer teleport the
    # reported track; it also removes the double-averaging in the emit path. False keeps
    # the legacy raw-observation emit byte-for-byte.
    emit_kalman_posterior: bool = False
    role_params: dict[str, dict[str, float]] = field(default_factory=_default_role_params)

    def __post_init__(self) -> None:
        for name in ("confirm_hits", "lost_window_frames", "bowler_lost_window_frames",
                     "reentry_temporal_gate_frames", "role_latch_frames",
                     "pose_min_updates", "pose_min_shared_segments"):
            if type(getattr(self, name)) is not int or getattr(self, name) <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if type(self.ownership_ttl_frames) is not int or self.ownership_ttl_frames < 0:
            raise ValueError("ownership_ttl_frames must be a non-negative integer")
        for name in ("shadow_confirm_override_hits", "expected_roster_max"):
            if type(getattr(self, name)) is not int or getattr(self, name) <= 0:
                raise ValueError(f"{name} must be a positive integer")
        for name in ("shadow_confirm_gate_m", "roster_cap_min_separation_m"):
            _positive(name, getattr(self, name))
        for name in ("chi2_gate_2dof", "reentry_mahalanobis_gate", "reentry_gap_scale_frames",
                     "reentry_kinematic_slack", "cap_max_pos_var",
                     "local_identity_mahalanobis_gate"):
            _positive(name, getattr(self, name))
        _nonnegative("pose_match_weight", self.pose_match_weight)
        _nonnegative("pose_gate_veto_distance", self.pose_gate_veto_distance)
        _nonnegative("reentry_pose_max_distance", self.reentry_pose_max_distance)
        if type(self.adaptive_lost_window) is not bool:
            raise ValueError("adaptive_lost_window must be a boolean")
        if type(self.lost_window_max_frames) is not int or self.lost_window_max_frames <= 0:
            raise ValueError("lost_window_max_frames must be a positive integer")
        if type(self.min_emit_frames) is not int or self.min_emit_frames < 0:
            raise ValueError("min_emit_frames must be a non-negative integer")
        for name in ("confidence_high", "confidence_discard", "pose_descriptor_ema"):
            _range(name, getattr(self, name), 0.0, 1.0)
        if self.confidence_discard > self.confidence_high:
            raise ValueError("confidence_discard must be <= confidence_high")
        if not isinstance(self.role_params, dict) or "unknown" not in self.role_params:
            raise ValueError("role_params must be a mapping containing unknown")
        for role, values in self.role_params.items():
            if not isinstance(role, str) or not isinstance(values, dict):
                raise ValueError("role_params entries must be role -> mapping")
            unknown = set(values) - {"alpha", "sigma_a", "measurement_noise"}
            if unknown or set(values) != {"alpha", "sigma_a", "measurement_noise"}:
                raise ValueError(f"invalid role_params entry for {role}")
            for key, value in values.items():
                _positive(f"role_params.{role}.{key}", value)


@dataclass(frozen=True)
class P4BConfig:
    enabled: bool = True
    cross_camera_min_frames: int = 30
    cross_camera_min_track_ratio: float = 0.5
    temporal_gate_frames: int = 120
    w_temporal: float = 0.1
    w_spatial: float = 1.0
    w_role: float = 100.0
    new_traj_cost_factor: float = 0.5
    velocity_continuity_weight: float = 0.5
    kinematic_slack: float = 1.5
    # Stitching v2 (ID-2 / ghost-verification). When > 0, a stitch between two
    # fragments is FORBIDDEN if both carry mature pose-shape descriptors that differ
    # by more than this bone-ratio distance — so only same-build fragments merge
    # (abstains when either descriptor is immature/unshared). w_pose adds the pose
    # distance to the link cost so a better body-shape match is preferred among
    # admissible stitches. 0 = disabled (byte-identical).
    pose_stitch_max_distance: float = 0.0
    w_pose: float = 0.0
    pose_min_shared_segments: int = 4
    incompatible_role_pairs: list[list[str]] = field(default_factory=_default_incompatible_roles)

    def __post_init__(self) -> None:
        if type(self.enabled) is not bool:
            raise ValueError("enabled must be a boolean")
        if type(self.cross_camera_min_frames) is not int or self.cross_camera_min_frames <= 0:
            raise ValueError("cross_camera_min_frames must be a positive integer")
        _range("cross_camera_min_track_ratio", self.cross_camera_min_track_ratio, 0.0, 1.0)
        if type(self.temporal_gate_frames) is not int or self.temporal_gate_frames <= 0:
            raise ValueError("temporal_gate_frames must be a positive integer")
        for name in ("w_spatial", "new_traj_cost_factor", "kinematic_slack"):
            _positive(name, getattr(self, name))
        for name in ("w_temporal", "w_role", "velocity_continuity_weight",
                     "pose_stitch_max_distance", "w_pose"):
            _nonnegative(name, getattr(self, name))
        if type(self.pose_min_shared_segments) is not int or self.pose_min_shared_segments <= 0:
            raise ValueError("pose_min_shared_segments must be a positive integer")
        if not isinstance(self.incompatible_role_pairs, list):
            raise ValueError("incompatible_role_pairs must be a list")
        for pair in self.incompatible_role_pairs:
            if not isinstance(pair, list) or len(pair) != 2 or not all(isinstance(v, str) for v in pair):
                raise ValueError("incompatible_role_pairs entries must be two role strings")


@dataclass(frozen=True)
class P4Config:
    frame_rate_fps: float = 50.0
    kinematic_v_max_mps: float = 9.0
    p4a: P4AConfig = field(default_factory=P4AConfig)
    p4b: P4BConfig = field(default_factory=P4BConfig)

    def __post_init__(self) -> None:
        _positive("frame_rate_fps", self.frame_rate_fps)
        _positive("kinematic_v_max_mps", self.kinematic_v_max_mps)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _positive(name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a positive number")


def _nonnegative(name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be a non-negative number")


def _range(name: str, value: Any, low: float, high: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be numeric")
    if not low <= float(value) <= high:
        raise ValueError(f"{name} must be in [{low}, {high}]")


def _build_nested(cls, raw: Any, section: str):
    if raw is None:
        return cls()
    if not isinstance(raw, dict):
        raise ValueError(f"{section} must be a mapping")
    names = {item.name for item in fields(cls)}
    unknown = set(raw) - names
    if unknown:
        raise ValueError(f"unknown {section} config keys: {sorted(unknown)}")
    return cls(**raw)


def load_global_id_config(path: str | Path | None) -> P4Config:
    if path is None:
        return P4Config()
    with Path(path).open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    if not isinstance(raw, dict):
        raise ValueError("global-id config must be a mapping")
    unknown = set(raw) - {"frame_rate_fps", "kinematic_v_max_mps", "p4a", "p4b"}
    if unknown:
        raise ValueError(f"unknown global-id config keys: {sorted(unknown)}")
    return P4Config(
        frame_rate_fps=float(raw.get("frame_rate_fps", 50.0)),
        kinematic_v_max_mps=float(raw.get("kinematic_v_max_mps", 9.0)),
        p4a=_build_nested(P4AConfig, raw.get("p4a"), "p4a"),
        p4b=_build_nested(P4BConfig, raw.get("p4b"), "p4b"),
    )
