#!/usr/bin/env python3
"""Fail closed when option layer specs change locked wireframe copy or structure."""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def normalize_text(value: object) -> str:
    text = unicodedata.normalize("NFC", str(value))
    return re.sub(r"\s+", " ", text).strip()


def validate_lock(lock: dict) -> dict[str, dict]:
    if lock.get("schema_version") != 1:
        raise ValueError("content lock schema_version must be 1")
    policy = lock.get("copy_policy")
    if not isinstance(policy, dict) or policy.get("mode") != "exact":
        raise ValueError("copy_policy.mode must be exact")
    if policy.get("normalization") != "unicode-nfc-collapse-whitespace":
        raise ValueError("unsupported copy normalization policy")
    if not isinstance(policy.get("allow_unlocked_text"), bool):
        raise ValueError("copy_policy.allow_unlocked_text must be boolean")
    screens = lock.get("screens")
    if not isinstance(screens, list) or not screens:
        raise ValueError("content lock requires a non-empty screens array")

    by_screen: dict[str, dict] = {}
    for screen in screens:
        if not isinstance(screen, dict) or not str(screen.get("screen_id", "")).strip():
            raise ValueError("every locked screen requires screen_id")
        screen_id = str(screen["screen_id"])
        if screen_id in by_screen:
            raise ValueError(f"duplicate locked screen_id: {screen_id}")
        structure = screen.get("structure")
        copy = screen.get("copy")
        if not isinstance(structure, list) or not structure:
            raise ValueError(f"locked screen {screen_id} requires structure records")
        if not isinstance(copy, list) or not copy:
            raise ValueError(f"locked screen {screen_id} requires copy records")

        structure_ids: set[str] = set()
        sibling_orders: set[tuple[object, int]] = set()
        for record in structure:
            structure_id = str(record.get("structure_id", "")).strip()
            if not structure_id:
                raise ValueError(f"locked screen {screen_id} has structure without structure_id")
            if structure_id in structure_ids:
                raise ValueError(f"duplicate structure_id in {screen_id}: {structure_id}")
            structure_ids.add(structure_id)
            order = record.get("order")
            if not isinstance(order, int) or order < 0:
                raise ValueError(f"structure {structure_id} requires a non-negative integer order")
            sibling_key = (record.get("parent_structure_id"), order)
            if sibling_key in sibling_orders:
                raise ValueError(
                    f"duplicate sibling order in {screen_id}: "
                    f"parent={record.get('parent_structure_id')} order={order}"
                )
            sibling_orders.add(sibling_key)

        for record in structure:
            parent = record.get("parent_structure_id")
            if parent is not None and parent not in structure_ids:
                raise ValueError(
                    f"structure {record['structure_id']} references unknown parent {parent}"
                )

        content_ids: set[str] = set()
        copy_sibling_orders: set[tuple[object, int]] = set()
        for record in copy:
            content_id = str(record.get("content_id", "")).strip()
            if not content_id:
                raise ValueError(f"locked screen {screen_id} has copy without content_id")
            if content_id in content_ids:
                raise ValueError(f"duplicate content_id in {screen_id}: {content_id}")
            content_ids.add(content_id)
            if not isinstance(record.get("expected_text"), str):
                raise ValueError(f"copy {content_id} requires expected_text")
            parent = record.get("parent_structure_id")
            if parent is not None and parent not in structure_ids:
                raise ValueError(
                    f"copy {content_id} references unknown parent structure {parent}"
                )
            order = record.get("order")
            if not isinstance(order, int) or order < 0:
                raise ValueError(f"copy {content_id} requires a non-negative integer order")
            sibling_key = (parent, order)
            if sibling_key in copy_sibling_orders:
                raise ValueError(
                    f"duplicate copy sibling order in {screen_id}: "
                    f"parent={parent} order={order}"
                )
            copy_sibling_orders.add(sibling_key)
        by_screen[screen_id] = screen
    return by_screen


def inventory_layers(
    spec: dict,
) -> tuple[
    dict[str, dict],
    dict[str, dict],
    dict[object, list[str]],
    dict[object, list[str]],
]:
    structures: dict[str, dict] = {}
    copy: dict[str, dict] = {}
    sibling_sequence: dict[object, list[str]] = defaultdict(list)
    copy_sequence: dict[object, list[str]] = defaultdict(list)

    def walk(layers: object, nearest_structure: str | None) -> None:
        if not isinstance(layers, list):
            return
        for layer in layers:
            if not isinstance(layer, dict):
                continue
            next_parent = nearest_structure
            if layer.get("type") == "frame":
                structure_id = layer.get("structure_id")
                if structure_id is not None:
                    structure_id = str(structure_id).strip()
                    if not structure_id:
                        raise ValueError(f"layer {layer.get('id')} has empty structure_id")
                    if structure_id in structures:
                        raise ValueError(f"duplicate structure_id in layer spec: {structure_id}")
                    structures[structure_id] = {
                        "layer": layer,
                        "parent_structure_id": nearest_structure,
                    }
                    sibling_sequence[nearest_structure].append(structure_id)
                    next_parent = structure_id
                walk(layer.get("children"), next_parent)
            elif layer.get("type") == "text":
                content_id = layer.get("content_id")
                if content_id is None:
                    copy[f"__unlocked__:{layer.get('id')}"] = {
                        "layer": layer,
                        "parent_structure_id": nearest_structure,
                    }
                    continue
                content_id = str(content_id).strip()
                if not content_id:
                    raise ValueError(f"text layer {layer.get('id')} has empty content_id")
                if content_id in copy:
                    raise ValueError(f"duplicate content_id in layer spec: {content_id}")
                copy[content_id] = {
                    "layer": layer,
                    "parent_structure_id": nearest_structure,
                }
                copy_sequence[nearest_structure].append(content_id)

    walk(spec.get("layers"), None)
    return structures, copy, sibling_sequence, copy_sequence


def validate_specs(lock_path: Path, spec_paths: list[Path]) -> dict:
    lock = load_json(lock_path)
    locked_screens = validate_lock(lock)
    allow_unlocked_text = lock["copy_policy"]["allow_unlocked_text"]
    option_ids: list[str] = []
    copy_checks = 0
    structure_checks = 0
    validated_specs: list[str] = []

    for spec_path in spec_paths:
        spec = load_json(spec_path)
        screen_id = str(spec.get("screen_id", ""))
        locked = locked_screens.get(screen_id)
        if locked is None:
            raise ValueError(f"layer spec screen_id is not present in content lock: {screen_id}")
        option = str(spec.get("option", "")).strip()
        if not option:
            raise ValueError(f"layer spec requires option: {spec_path}")
        if option in option_ids:
            raise ValueError(f"duplicate option in fidelity validation: {option}")
        option_ids.append(option)

        structures, copy, sibling_sequence, copy_sequence = inventory_layers(spec)
        locked_structure = {
            record["structure_id"]: record
            for record in locked["structure"]
            if record.get("required", True)
        }
        for structure_id, record in locked_structure.items():
            actual = structures.get(structure_id)
            if actual is None:
                raise ValueError(
                    f"option {option} missing required structure_id: {structure_id}"
                )
            if actual["parent_structure_id"] != record.get("parent_structure_id"):
                raise ValueError(
                    f"option {option} structure parent mismatch for {structure_id}: "
                    f"expected={record.get('parent_structure_id')} "
                    f"actual={actual['parent_structure_id']}"
                )
            structure_checks += 1

        expected_by_parent: dict[object, list[dict]] = defaultdict(list)
        for record in locked_structure.values():
            expected_by_parent[record.get("parent_structure_id")].append(record)
        for parent, records in expected_by_parent.items():
            expected = [
                record["structure_id"]
                for record in sorted(records, key=lambda item: item["order"])
            ]
            actual_sequence = sibling_sequence.get(parent, [])
            filtered = [item for item in actual_sequence if item in expected]
            if filtered != expected:
                raise ValueError(
                    f"option {option} structure order mismatch under {parent}: "
                    f"expected={expected} actual={filtered}"
                )

        locked_copy = {
            record["content_id"]: record
            for record in locked["copy"]
            if record.get("required", True)
        }
        for content_id, record in locked_copy.items():
            actual = copy.get(content_id)
            if actual is None:
                raise ValueError(f"option {option} missing required content_id: {content_id}")
            actual_text = actual["layer"].get("text", {}).get("content", "")
            if normalize_text(actual_text) != normalize_text(record["expected_text"]):
                raise ValueError(
                    f"option {option} copy mismatch for {content_id}: "
                    f"expected={record['expected_text']!r} actual={actual_text!r}"
                )
            if actual["parent_structure_id"] != record.get("parent_structure_id"):
                raise ValueError(
                    f"option {option} copy parent mismatch for {content_id}: "
                    f"expected={record.get('parent_structure_id')} "
                    f"actual={actual['parent_structure_id']}"
                )
            copy_checks += 1

        expected_copy_by_parent: dict[object, list[dict]] = defaultdict(list)
        for record in locked_copy.values():
            expected_copy_by_parent[record.get("parent_structure_id")].append(record)
        for parent, records in expected_copy_by_parent.items():
            expected = [
                record["content_id"]
                for record in sorted(records, key=lambda item: item["order"])
            ]
            actual_sequence = copy_sequence.get(parent, [])
            filtered = [item for item in actual_sequence if item in expected]
            if filtered != expected:
                raise ValueError(
                    f"option {option} copy order mismatch under {parent}: "
                    f"expected={expected} actual={filtered}"
                )

        if not allow_unlocked_text:
            unlocked = [
                item["layer"].get("id")
                for key, item in copy.items()
                if key.startswith("__unlocked__:")
            ]
            extra = [
                content_id
                for content_id in copy
                if not content_id.startswith("__unlocked__:")
                and content_id not in {record["content_id"] for record in locked["copy"]}
            ]
            if unlocked or extra:
                raise ValueError(
                    f"option {option} contains unlocked text: "
                    f"layers={unlocked} content_ids={extra}"
                )
        validated_specs.append(str(spec_path.resolve()))

    return {
        "status": "pass",
        "content_lock": str(lock_path.resolve()),
        "validated_specs": validated_specs,
        "options": option_ids,
        "copy_checks": copy_checks,
        "structure_checks": structure_checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("content_lock", type=Path)
    parser.add_argument("layer_specs", nargs="+", type=Path)
    parser.add_argument("--report-out", type=Path)
    args = parser.parse_args()
    try:
        report = validate_specs(
            args.content_lock.resolve(),
            [path.resolve() for path in args.layer_specs],
        )
    except ValueError as exc:
        raise SystemExit(f"wireframe fidelity failed: {exc}") from exc
    if args.report_out:
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(
        "wireframe fidelity: pass "
        f"({report['copy_checks']} copy checks, "
        f"{report['structure_checks']} structure checks)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
