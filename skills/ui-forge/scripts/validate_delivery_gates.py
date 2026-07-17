#!/usr/bin/env python3
"""Validate UIForge hard Figma delivery gates."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    report_path = args.report.resolve()
    report = load_json(report_path)
    errors: list[str] = []

    if report.get("schema_version") != 1:
        errors.append("schema_version must be 1")

    assets_gate = report.get("asset_library", {})
    manifest_rel = assets_gate.get("asset_manifest_path", "asset-manifest.json")
    manifest_path = (report_path.parent / manifest_rel).resolve()
    if not manifest_path.exists():
        errors.append(f"asset manifest missing: {manifest_path}")
        accepted_manifest_ids: list[str] = []
    else:
        manifest = load_json(manifest_path)
        accepted_manifest_ids = [
            item.get("id", "")
            for item in manifest.get("assets", [])
            if item.get("candidate_role") == "used_or_optional"
            and item.get("status") not in {"rejected", "excluded"}
        ]
        if any(not nonempty(item) for item in accepted_manifest_ids):
            errors.append("accepted asset manifest entries require non-empty IDs")
        if len(set(accepted_manifest_ids)) != len(accepted_manifest_ids):
            errors.append("accepted asset IDs must be unique")

    minimum = assets_gate.get("minimum_assets", 12)
    accepted_gate_ids = assets_gate.get("accepted_asset_ids", [])
    if len(accepted_manifest_ids) < minimum:
        errors.append(f"candidate asset count {len(accepted_manifest_ids)} is below {minimum}")
    if set(accepted_gate_ids) != set(accepted_manifest_ids):
        errors.append("delivery gate accepted_asset_ids must exactly match asset-manifest IDs")
    if not nonempty(assets_gate.get("figma_section_node_id")):
        errors.append("Asset Library Figma section node ID is required")
    placements = assets_gate.get("placements", [])
    placement_ids = [item.get("asset_id", "") for item in placements]
    if set(placement_ids) != set(accepted_manifest_ids) or len(placement_ids) != len(set(placement_ids)):
        errors.append("Figma asset placement IDs must exactly and uniquely match accepted assets")
    for item in placements:
        if not nonempty(item.get("asset_node_id")) or not nonempty(item.get("library_tile_node_id")):
            errors.append(f"asset {item.get('asset_id', '<unknown>')} lacks Figma placement evidence")

    screens = report.get("auto_layout", {}).get("screens", [])
    if not screens:
        errors.append("at least one managed screen is required for Auto Layout validation")
    seen_screens: set[str] = set()
    for screen in screens:
        key = screen.get("screen_key", "")
        if not nonempty(key) or key in seen_screens:
            errors.append("managed screen keys must be non-empty and unique")
        seen_screens.add(key)
        if not nonempty(screen.get("root_node_id")):
            errors.append(f"screen {key} lacks a root node ID")
        if screen.get("root_layout_mode") not in {"VERTICAL", "HORIZONTAL"}:
            errors.append(f"screen {key} root is not Auto Layout")
        structural = screen.get("structural_container_ids", [])
        automatic = screen.get("auto_layout_container_ids", [])
        if len(structural) != len(set(structural)) or len(automatic) != len(set(automatic)):
            errors.append(f"screen {key} contains duplicate container IDs")
        missing = sorted(set(structural) - set(automatic))
        if missing:
            errors.append(f"screen {key} has structural containers without Auto Layout: {missing}")
        for exception in screen.get("exceptions", []):
            if exception.get("node_id") in set(structural):
                errors.append(f"screen {key} illegally exempts structural node {exception.get('node_id')}")
            if not nonempty(exception.get("reason")):
                errors.append(f"screen {key} has an undocumented Auto Layout exception")

    variables = report.get("brand_dna_variables", {})
    required_collections = {"primitives", "semantic", "dimensions", "typography"}
    collections = variables.get("collections", {})
    for name in required_collections:
        if not nonempty(collections.get(name)):
            errors.append(f"Brand DNA variable collection missing: {name}")
    required_tokens = variables.get("required_token_ids", [])
    if not required_tokens or any(not nonempty(item) for item in required_tokens):
        errors.append("required_token_ids must contain non-empty Brand DNA token IDs")
    if len(required_tokens) != len(set(required_tokens)):
        errors.append("required Brand DNA token IDs must be unique")
    mappings = variables.get("token_to_variable", [])
    mapped_tokens = [item.get("token_id", "") for item in mappings]
    if set(mapped_tokens) != set(required_tokens) or len(mapped_tokens) != len(set(mapped_tokens)):
        errors.append("token-to-variable mappings must exactly and uniquely cover required Brand DNA tokens")
    for item in mappings:
        if not nonempty(item.get("variable_id")) or item.get("collection") not in required_collections:
            errors.append(f"invalid variable mapping for token {item.get('token_id', '<unknown>')}")
    eligible = variables.get("eligible_property_count")
    bound = variables.get("bound_property_count")
    if not isinstance(eligible, int) or eligible <= 0:
        errors.append("eligible_property_count must be a positive integer")
    if bound != eligible:
        errors.append(f"Brand DNA binding coverage is incomplete: {bound}/{eligible}")
    if variables.get("unbound_eligible_properties"):
        errors.append("unbound eligible Brand DNA properties must be empty")

    if errors:
        raise SystemExit("delivery gates failed:\n- " + "\n- ".join(errors))
    print(
        "delivery gates pass: "
        f"{len(accepted_manifest_ids)} assets; "
        f"{len(screens)} Auto Layout screens; "
        f"{len(required_tokens)} Brand DNA variables; "
        f"{bound}/{eligible} eligible properties bound"
    )


if __name__ == "__main__":
    main()
