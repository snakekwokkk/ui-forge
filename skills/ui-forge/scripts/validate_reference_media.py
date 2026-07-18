#!/usr/bin/env python3
"""Validate reference-derived media relationships across option layer specs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from validate_asset_provenance import load as load_provenance
from validate_wireframe_fidelity import load_json, validate_lock


OPTIONS = {"A", "B", "C"}
EXPECTATIONS = {"required", "optional", "none"}
DECISIONS = {"apply", "omit"}
ASSET_ROLES = {
    "vector_icon",
    "isolated_raster",
    "composite_raster",
    "surface_texture",
    "full_bleed_background",
    "native_visual",
    "none",
}
ROLE_LAYER_TYPES = {
    "vector_icon": {"icon"},
    "isolated_raster": {"raster"},
    "composite_raster": {"raster"},
    "surface_texture": {"raster"},
    "full_bleed_background": {"raster"},
    "native_visual": {"frame", "rectangle", "ellipse", "line"},
}
ROLE_PROVENANCE = {
    "isolated_raster": ("isolated_object", {"transparent_required"}),
    "composite_raster": (
        "composite_scene",
        {"opaque_composite_expected", "embedded_background_authorized"},
    ),
    "surface_texture": (
        "surface_texture",
        {"opaque_composite_expected", "embedded_background_authorized"},
    ),
    "full_bleed_background": (
        "full_bleed_background",
        {"opaque_composite_expected", "embedded_background_authorized"},
    ),
}
BANDS = {
    "accent": (0.0, 0.12),
    "supporting": (0.12, 0.35),
    "balanced": (0.35, 0.65),
    "dominant": (0.65, 1.0),
}
RECURRENCE = {"repeated", "prominent_single", "isolated"}


def layer_area(layer: dict) -> float:
    bounds = layer.get("bounds", {})
    try:
        return max(0.0, float(bounds["width"])) * max(
            0.0, float(bounds["height"])
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"layer {layer.get('id')} has invalid bounds") from exc


def inventory_spec(spec: dict) -> tuple[dict[str, dict], dict[str, dict]]:
    structures: dict[str, dict] = {}
    layers: dict[str, dict] = {}

    def walk(items: object, nearest_structure: str | None) -> None:
        if not isinstance(items, list):
            return
        for layer in items:
            if not isinstance(layer, dict):
                continue
            layer_id = str(layer.get("id", "")).strip()
            if not layer_id:
                raise ValueError("every layer requires id for media validation")
            if layer_id in layers:
                raise ValueError(f"duplicate layer id in media validation: {layer_id}")
            next_structure = nearest_structure
            structure_id = layer.get("structure_id")
            if structure_id is not None:
                structure_id = str(structure_id).strip()
                if structure_id in structures:
                    raise ValueError(f"duplicate structure_id: {structure_id}")
                structures[structure_id] = layer
                next_structure = structure_id
            layers[layer_id] = {
                "layer": layer,
                "nearest_structure_id": next_structure,
            }
            walk(layer.get("children"), next_structure)

    walk(spec.get("layers"), None)
    return structures, layers


def validate_reference_media(
    plan_path: Path,
    content_lock_path: Path,
    provenance_path: Path,
    spec_paths: list[Path],
) -> dict:
    plan = load_json(plan_path)
    if plan.get("schema_version") != 1:
        raise ValueError("reference media plan schema_version must be 1")
    if plan.get("analysis_complete") is not True:
        raise ValueError("reference media analysis_complete must be true")
    source_ids = plan.get("source_reference_ids")
    if not isinstance(source_ids, list) or not all(
        str(value).strip() for value in source_ids
    ):
        raise ValueError("reference media plan requires source_reference_ids")

    lock = load_json(content_lock_path)
    locked_screens = validate_lock(lock)
    locked_structures = {
        (screen_id, str(record["structure_id"]))
        for screen_id, screen in locked_screens.items()
        for record in screen["structure"]
    }

    patterns = plan.get("reference_patterns")
    if not isinstance(patterns, list) or not patterns:
        raise ValueError("reference media plan requires reference_patterns")
    patterns_by_id: dict[str, dict] = {}
    for pattern in patterns:
        if not isinstance(pattern, dict):
            raise ValueError("reference media patterns must be objects")
        pattern_id = str(pattern.get("pattern_id", "")).strip()
        if not pattern_id or pattern_id in patterns_by_id:
            raise ValueError(f"invalid or duplicate media pattern_id: {pattern_id}")
        if pattern.get("asset_type") not in ASSET_ROLES - {"none"}:
            raise ValueError(f"invalid asset_type for media pattern {pattern_id}")
        for key in ("component_role", "pairing", "position"):
            if not str(pattern.get(key, "")).strip():
                raise ValueError(f"media pattern {pattern_id} requires {key}")
        if pattern.get("visual_share_band") not in BANDS:
            raise ValueError(f"invalid visual_share_band for media pattern {pattern_id}")
        if pattern.get("recurrence") not in RECURRENCE:
            raise ValueError(f"invalid recurrence for media pattern {pattern_id}")
        confidence = pattern.get("confidence")
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            raise ValueError(f"invalid confidence for media pattern {pattern_id}")
        evidence = pattern.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            raise ValueError(f"media pattern {pattern_id} requires evidence")
        for item in evidence:
            if (
                not isinstance(item, dict)
                or not str(item.get("input_id", "")).strip()
                or not str(item.get("observation", "")).strip()
            ):
                raise ValueError(f"media pattern {pattern_id} has invalid evidence")
            if str(item["input_id"]) not in {str(value) for value in source_ids}:
                raise ValueError(
                    f"media pattern {pattern_id} evidence uses an unknown reference input"
                )
        patterns_by_id[pattern_id] = pattern

    provenance = load_provenance(provenance_path)
    provenance_by_id = {
        str(record.get("asset_id")): record
        for record in provenance.get("assets", [])
        if isinstance(record, dict)
    }

    specs_by_option: dict[str, dict] = {}
    inventories: dict[str, tuple[dict[str, dict], dict[str, dict]]] = {}
    for spec_path in spec_paths:
        spec = load_json(spec_path)
        option = str(spec.get("option", "")).strip()
        if option not in OPTIONS or option in specs_by_option:
            raise ValueError(f"media validation requires unique options A, B, C: {option}")
        specs_by_option[option] = spec
        inventories[option] = inventory_spec(spec)
    if set(specs_by_option) != OPTIONS:
        raise ValueError("media validation requires exactly options A, B, and C")

    mappings = plan.get("module_mappings")
    if not isinstance(mappings, list) or not mappings:
        raise ValueError("reference media plan requires module_mappings")
    mapped_patterns: set[str] = set()
    required_patterns: set[str] = set()
    applied_count = 0
    omitted_count = 0
    for mapping in mappings:
        if not isinstance(mapping, dict):
            raise ValueError("module media mappings must be objects")
        screen_id = str(mapping.get("screen_id", "")).strip()
        structure_id = str(mapping.get("structure_id", "")).strip()
        if (screen_id, structure_id) not in locked_structures:
            raise ValueError(
                f"media mapping references unlocked structure: {screen_id}/{structure_id}"
            )
        pattern_ids = mapping.get("reference_pattern_ids")
        if not isinstance(pattern_ids, list) or not pattern_ids:
            raise ValueError(f"media mapping {structure_id} requires reference_pattern_ids")
        unknown = {str(value) for value in pattern_ids} - set(patterns_by_id)
        if unknown:
            raise ValueError(
                f"media mapping {structure_id} references unknown patterns: {sorted(unknown)}"
            )
        mapped_patterns.update(str(value) for value in pattern_ids)
        expectation = mapping.get("media_expectation")
        if expectation not in EXPECTATIONS:
            raise ValueError(f"invalid media_expectation for {structure_id}")
        if expectation == "required":
            required_patterns.update(str(value) for value in pattern_ids)
        decisions = mapping.get("option_decisions")
        if not isinstance(decisions, list):
            raise ValueError(f"media mapping {structure_id} requires option_decisions")
        by_option = {
            str(item.get("option")): item
            for item in decisions
            if isinstance(item, dict)
        }
        if set(by_option) != OPTIONS or len(decisions) != 3:
            raise ValueError(
                f"media mapping {structure_id} requires one decision for A, B, and C"
            )
        mapping_applied = 0
        allowed_pattern_roles = {
            str(patterns_by_id[pattern_id]["asset_type"])
            for pattern_id in pattern_ids
        }
        for option, decision in by_option.items():
            action = decision.get("decision")
            role = decision.get("asset_role")
            layer_ids = decision.get("layer_ids")
            rationale = str(decision.get("rationale", "")).strip()
            if action not in DECISIONS or role not in ASSET_ROLES:
                raise ValueError(
                    f"invalid media decision for {structure_id} option {option}"
                )
            if not rationale:
                raise ValueError(
                    f"media decision requires rationale for {structure_id} option {option}"
                )
            if action == "omit":
                omitted_count += 1
                if role != "none" or layer_ids not in ([], None):
                    raise ValueError(
                        f"omitted media decision must use role none and no layers: "
                        f"{structure_id} option {option}"
                    )
                continue
            if expectation == "none":
                raise ValueError(
                    f"media_expectation none cannot apply media: {structure_id} option {option}"
                )
            if role not in allowed_pattern_roles:
                raise ValueError(
                    f"media role {role} is not supported by mapped reference patterns "
                    f"for {structure_id} option {option}"
                )
            if not isinstance(layer_ids, list) or not layer_ids:
                raise ValueError(
                    f"applied media decision requires layer_ids: {structure_id} option {option}"
                )
            band = decision.get("visual_share_band")
            if band not in BANDS:
                raise ValueError(
                    f"applied media decision requires visual_share_band: "
                    f"{structure_id} option {option}"
                )
            structures, layers = inventories[option]
            module = structures.get(structure_id)
            if module is None:
                raise ValueError(
                    f"option {option} lacks mapped structure_id: {structure_id}"
                )
            module_area = layer_area(module)
            if module_area <= 0:
                raise ValueError(f"mapped structure has zero area: {structure_id}")
            media_area = 0.0
            for layer_id in layer_ids:
                found = layers.get(str(layer_id))
                if found is None:
                    raise ValueError(
                        f"media layer not found in option {option}: {layer_id}"
                    )
                if found["nearest_structure_id"] != structure_id:
                    raise ValueError(
                        f"media layer {layer_id} is outside mapped structure {structure_id}"
                    )
                layer = found["layer"]
                if layer.get("type") not in ROLE_LAYER_TYPES[role]:
                    raise ValueError(
                        f"media layer {layer_id} type does not match role {role}"
                    )
                if role in ROLE_PROVENANCE:
                    asset_id = str(layer.get("raster", {}).get("asset_id", ""))
                    record = provenance_by_id.get(asset_id)
                    expected_role, policies = ROLE_PROVENANCE[role]
                    if record is None:
                        raise ValueError(f"missing provenance for media asset: {asset_id}")
                    if record.get("asset_role") != expected_role:
                        raise ValueError(
                            f"asset {asset_id} role mismatch: "
                            f"expected={expected_role} actual={record.get('asset_role')}"
                        )
                    if record.get("background_policy") not in policies:
                        raise ValueError(
                            f"asset {asset_id} background policy does not match {role}"
                        )
                    if record.get("target_structure_id") != structure_id:
                        raise ValueError(
                            f"asset {asset_id} target_structure_id must be {structure_id}"
                        )
                media_area += layer_area(layer)
            ratio = min(1.0, media_area / module_area)
            lower, upper = BANDS[band]
            if not lower <= ratio <= upper:
                raise ValueError(
                    f"media visual share mismatch for {structure_id} option {option}: "
                    f"band={band} ratio={ratio:.4f}"
                )
            mapping_applied += 1
            applied_count += 1
        if expectation == "required" and mapping_applied == 0:
            raise ValueError(
                f"required reference media pattern is omitted from every option: {structure_id}"
            )

    unmapped = set(patterns_by_id) - mapped_patterns
    if unmapped:
        raise ValueError(f"reference media patterns are not mapped: {sorted(unmapped)}")
    repeated_high_confidence = {
        pattern_id
        for pattern_id, pattern in patterns_by_id.items()
        if pattern.get("recurrence") == "repeated"
        and float(pattern.get("confidence", 0)) >= 0.75
    }
    if not repeated_high_confidence.issubset(required_patterns):
        missing_required = repeated_high_confidence - required_patterns
        raise ValueError(
            "repeated high-confidence media patterns require at least one required "
            f"module mapping: {sorted(missing_required)}"
        )
    return {
        "status": "pass",
        "media_plan": str(plan_path.resolve()),
        "pattern_count": len(patterns_by_id),
        "module_mapping_count": len(mappings),
        "applied_decision_count": applied_count,
        "omitted_with_rationale_count": omitted_count,
        "validated_specs": [str(path.resolve()) for path in spec_paths],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("media_plan", type=Path)
    parser.add_argument("content_lock", type=Path)
    parser.add_argument("asset_provenance", type=Path)
    parser.add_argument("layer_specs", nargs="+", type=Path)
    args = parser.parse_args()
    try:
        report = validate_reference_media(
            args.media_plan.resolve(),
            args.content_lock.resolve(),
            args.asset_provenance.resolve(),
            [path.resolve() for path in args.layer_specs],
        )
    except ValueError as exc:
        raise SystemExit(f"reference media validation failed: {exc}") from exc
    print(
        "reference media: pass "
        f"({report['pattern_count']} patterns, "
        f"{report['module_mapping_count']} module mappings)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
