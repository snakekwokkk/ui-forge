#!/usr/bin/env python3
"""Validate material-style detection and selected asset conformity."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


MODALITIES = {
    "photography", "photoreal-composite", "3d-render", "clay-3d",
    "flat-vector", "flat-cartoon", "editorial-illustration", "hand-drawn",
    "collage", "pixel-art", "mixed-media", "minimal-native-ui",
}
COMPLEX_TYPES = {"clean_raster", "flattened_raster"}


def load(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid JSON: {path}: {exc}")
    if not isinstance(value, dict):
        raise SystemExit(f"JSON root must be an object: {path}")
    return value


def validate_profile(profile: dict) -> list[str]:
    errors: list[str] = []
    if profile.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if not str(profile.get("profile_id", "")).strip():
        errors.append("profile_id is required")
    dominant = profile.get("dominant_modality")
    if dominant not in MODALITIES:
        errors.append(f"unsupported dominant_modality: {dominant}")
    secondary = profile.get("secondary_modalities", [])
    if not isinstance(secondary, list) or any(item not in MODALITIES for item in secondary):
        errors.append("secondary_modalities contains unsupported values")
    confidence = profile.get("confidence")
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        errors.append("confidence must be between 0 and 1")
    if not isinstance(profile.get("evidence"), list) or not profile.get("evidence"):
        errors.append("at least one evidence record is required")
    dimensions = profile.get("style_dimensions")
    if not isinstance(dimensions, dict) or not dimensions:
        errors.append("style_dimensions is required")
    policy = profile.get("generation_policy", {})
    for key in ("must_match_reference_material", "original_subjects_required", "reference_asset_reuse"):
        if not isinstance(policy.get(key), bool):
            errors.append(f"generation_policy.{key} must be boolean")
    if policy.get("must_match_reference_material") is not True:
        errors.append("must_match_reference_material must be true")
    if policy.get("original_subjects_required") is not True:
        errors.append("original_subjects_required must be true")
    if policy.get("reference_asset_reuse") is not False:
        errors.append("reference_asset_reuse must be false")
    return errors


def validate_assets(profile: dict, manifest: dict, selected: bool) -> list[str]:
    errors: list[str] = []
    profile_id = profile.get("profile_id")
    dominant = profile.get("dominant_modality")
    allowed = {dominant, *profile.get("secondary_modalities", [])}
    accepted = [
        item for item in manifest.get("assets", [])
        if item.get("candidate_role") == "used_or_optional"
        and item.get("status") not in {"rejected", "excluded"}
    ]
    if selected and len(accepted) < 12:
        errors.append("selected catalog requires at least 12 accepted assets")
    for item in accepted:
        if item.get("type") not in COMPLEX_TYPES:
            continue
        asset_id = item.get("id", "<unknown>")
        if item.get("style_profile_id") != profile_id:
            errors.append(f"asset {asset_id} uses the wrong style_profile_id")
        if item.get("material_modality") not in allowed:
            errors.append(f"asset {asset_id} uses an unapproved material modality")
        match = item.get("style_match", {})
        expected = "pass" if selected else {"planned", "pass"}
        if selected and match.get("status") != expected:
            errors.append(f"asset {asset_id} lacks a passing style match")
        if not selected and match.get("status") not in expected:
            errors.append(f"asset {asset_id} has an invalid style match status")
        if selected and not str(match.get("evidence", "")).strip():
            errors.append(f"asset {asset_id} lacks style match evidence")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("profile", type=Path)
    parser.add_argument("--asset-manifest", type=Path)
    parser.add_argument("--selected", action="store_true")
    args = parser.parse_args()
    profile = load(args.profile)
    errors = validate_profile(profile)
    if args.selected and not args.asset_manifest:
        errors.append("--selected requires --asset-manifest")
    if args.asset_manifest:
        errors.extend(validate_assets(profile, load(args.asset_manifest), args.selected))
    if errors:
        raise SystemExit("material-style validation failed:\n- " + "\n- ".join(errors))
    print(f"valid material-style profile: {profile.get('dominant_modality')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
