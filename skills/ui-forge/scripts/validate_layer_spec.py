#!/usr/bin/env python3
"""Validate UIForge same-source layer specifications and preview locks."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Iterator
from pathlib import Path


SCHEMA_VERSION = 2
LAYER_TYPES = {"frame", "rectangle", "ellipse", "line", "text", "raster", "icon"}
LAYOUT_MODES = {"HORIZONTAL", "VERTICAL"}
SIZING_MODES = {"FIXED", "FILL", "HUG"}
STRUCTURAL_ROLES = {
    "screen", "section", "stack", "row", "card", "list", "list-item",
    "action-group", "navigation", "header", "footer", "content", "form",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid JSON: {exc}")
    if not isinstance(data, dict):
        raise SystemExit("spec root must be an object")
    return data


def iter_layers(layers: list[dict]) -> Iterator[dict]:
    """Yield every layer in document order, including nested children."""
    for layer in layers:
        yield layer
        children = layer.get("children", [])
        if isinstance(children, list):
            yield from iter_layers(children)


def _validate_layout(layout: object, owner: str) -> None:
    if not isinstance(layout, dict):
        raise SystemExit(f"{owner} must define an Auto Layout object")
    required = {
        "mode", "primary_axis_sizing", "counter_axis_sizing",
        "primary_axis_align", "counter_axis_align", "item_spacing", "padding",
    }
    missing = required - set(layout)
    if missing:
        raise SystemExit(f"{owner} Auto Layout missing: {', '.join(sorted(missing))}")
    if layout["mode"] not in LAYOUT_MODES:
        raise SystemExit(f"{owner} layout mode must be HORIZONTAL or VERTICAL")
    if layout["primary_axis_sizing"] not in {"FIXED", "AUTO"}:
        raise SystemExit(f"{owner} has invalid primary_axis_sizing")
    if layout["counter_axis_sizing"] not in {"FIXED", "AUTO"}:
        raise SystemExit(f"{owner} has invalid counter_axis_sizing")
    if layout["primary_axis_align"] not in {"MIN", "CENTER", "MAX", "SPACE_BETWEEN"}:
        raise SystemExit(f"{owner} has invalid primary_axis_align")
    if layout["counter_axis_align"] not in {"MIN", "CENTER", "MAX", "BASELINE"}:
        raise SystemExit(f"{owner} has invalid counter_axis_align")
    if float(layout["item_spacing"]) < 0:
        raise SystemExit(f"{owner} item_spacing must be non-negative")
    padding = layout["padding"]
    if not isinstance(padding, dict) or any(key not in padding for key in ("top", "right", "bottom", "left")):
        raise SystemExit(f"{owner} padding must include top, right, bottom, and left")
    if any(float(padding[key]) < 0 for key in ("top", "right", "bottom", "left")):
        raise SystemExit(f"{owner} padding must be non-negative")
    if layout.get("wrap", "NO_WRAP") not in {"NO_WRAP", "WRAP"}:
        raise SystemExit(f"{owner} has invalid wrap mode")


def _validate_sizing(layer: dict, parent_id: str) -> None:
    sizing = layer.get("sizing")
    if not isinstance(sizing, dict) or any(key not in sizing for key in ("horizontal", "vertical")):
        raise SystemExit(f"layer {layer['id']} must define horizontal and vertical sizing inside {parent_id}")
    for axis in ("horizontal", "vertical"):
        if sizing[axis] not in SIZING_MODES:
            raise SystemExit(f"layer {layer['id']} has invalid {axis} sizing")


def _validate_layers(
    layers: object,
    project_root: Path,
    ids: set[str],
    asset_paths: list[Path],
    parent_id: str,
) -> None:
    if not isinstance(layers, list) or not layers:
        raise SystemExit(f"{parent_id} children must be a non-empty array")
    last_z = float("-inf")
    for index, layer in enumerate(layers):
        if not isinstance(layer, dict):
            raise SystemExit(f"layer {index} inside {parent_id} must be an object")
        for key in ("id", "name", "type", "z_index", "bounds", "sizing"):
            if key not in layer:
                raise SystemExit(f"layer {index} inside {parent_id} missing {key}")
        layer_id = str(layer["id"])
        if layer_id in ids:
            raise SystemExit(f"duplicate layer id: {layer_id}")
        ids.add(layer_id)
        if layer["type"] not in LAYER_TYPES:
            raise SystemExit(f"unsupported layer type: {layer['type']}")
        if layer["z_index"] < last_z:
            raise SystemExit(f"children inside {parent_id} must be ordered by nondecreasing z_index")
        last_z = layer["z_index"]

        bounds = layer["bounds"]
        if not isinstance(bounds, dict) or any(key not in bounds for key in ("x", "y", "width", "height")):
            raise SystemExit(f"layer {layer_id} has invalid bounds")
        if bounds["width"] <= 0 or bounds["height"] <= 0:
            raise SystemExit(f"layer {layer_id} must have positive dimensions")
        _validate_sizing(layer, parent_id)

        positioning = layer.get("layout_positioning", "AUTO")
        if positioning not in {"AUTO", "ABSOLUTE"}:
            raise SystemExit(f"layer {layer_id} has invalid layout_positioning")
        if positioning == "ABSOLUTE":
            overlay = layer.get("overlay")
            if (
                not isinstance(overlay, dict)
                or overlay.get("decorative") is not True
                or not str(overlay.get("reason", "")).strip()
            ):
                raise SystemExit(
                    f"absolute layer {layer_id} must be a documented decorative overlay"
                )
            if layer["type"] == "frame" and layer.get("children"):
                raise SystemExit(f"structural frame {layer_id} cannot use ABSOLUTE positioning")
        elif "overlay" in layer:
            raise SystemExit(f"AUTO layer {layer_id} must not declare an overlay exception")

        children = layer.get("children")
        if layer["type"] == "frame":
            role = layer.get("structural_role")
            if role not in STRUCTURAL_ROLES - {"screen"}:
                raise SystemExit(f"frame {layer_id} must declare a valid structural_role")
            _validate_layout(layer.get("layout"), f"frame {layer_id}")
            _validate_layers(children, project_root, ids, asset_paths, layer_id)
        elif children is not None:
            raise SystemExit(f"non-frame layer {layer_id} cannot contain children")

        if layer["type"] == "text" and not isinstance(layer.get("text"), dict):
            raise SystemExit(f"text layer {layer_id} is missing text data")
        if layer["type"] == "raster":
            raster = layer.get("raster")
            if not isinstance(raster, dict) or any(key not in raster for key in ("asset_id", "path", "fit")):
                raise SystemExit(f"raster layer {layer_id} has invalid raster data")
            asset_path = (project_root / raster["path"]).resolve()
            if not asset_path.is_file():
                raise SystemExit(f"missing raster asset: {asset_path}")
            asset_paths.append(asset_path)
        if layer["type"] == "icon":
            icon = layer.get("icon")
            required = ("icon_id", "svg_path", "preview_path", "fit")
            if not isinstance(icon, dict) or any(key not in icon for key in required):
                raise SystemExit(f"icon layer {layer_id} has invalid icon data")
            for key in ("svg_path", "preview_path"):
                asset_path = (project_root / icon[key]).resolve()
                if not asset_path.is_file():
                    raise SystemExit(f"missing icon asset: {asset_path}")
                asset_paths.append(asset_path)


def validate(spec_path: Path, project_root: Path) -> list[Path]:
    data = load_json(spec_path)
    for key in ("schema_version", "option", "screen_id", "canvas", "layers"):
        if key not in data:
            raise SystemExit(f"missing required key: {key}")
    if data["schema_version"] != SCHEMA_VERSION:
        raise SystemExit(
            f"layer spec schema_version must be {SCHEMA_VERSION}; "
            "schema v1 is rejected because it cannot prove nested Auto Layout"
        )

    canvas = data["canvas"]
    if not isinstance(canvas, dict) or any(key not in canvas for key in ("width", "height", "background", "layout")):
        raise SystemExit("canvas must include width, height, background, and layout")
    if canvas["width"] <= 0 or canvas["height"] <= 0:
        raise SystemExit("canvas dimensions must be positive")
    _validate_layout(canvas["layout"], "canvas")

    ids: set[str] = set()
    asset_paths: list[Path] = []
    _validate_layers(data["layers"], project_root, ids, asset_paths, "screen root")
    return asset_paths


def verify_lock(spec_path: Path, asset_paths: list[Path], lock_path: Path) -> None:
    lock = load_json(lock_path)
    if lock.get("spec_sha256") != sha256(spec_path):
        raise SystemExit("preview lock does not match the current layer spec")
    locked_assets = lock.get("assets", {})
    for path in asset_paths:
        key = str(path)
        if locked_assets.get(key) != sha256(path):
            raise SystemExit(f"preview lock does not match asset: {path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--verify-lock", type=Path)
    args = parser.parse_args()
    spec_path = args.spec.resolve()
    project_root = (args.project_root or spec_path.parent).resolve()
    assets = validate(spec_path, project_root)
    if args.verify_lock:
        verify_lock(spec_path, assets, args.verify_lock.resolve())
    print(f"valid layer spec: {spec_path} ({len(assets)} locked asset files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
