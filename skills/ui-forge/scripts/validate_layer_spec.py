#!/usr/bin/env python3
"""Validate UIForge same-source layer specifications and preview locks."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


LAYER_TYPES = {"rectangle", "ellipse", "line", "text", "raster", "icon"}


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


def validate(spec_path: Path, project_root: Path) -> list[Path]:
    data = load_json(spec_path)
    for key in ("schema_version", "option", "screen_id", "canvas", "layers"):
        if key not in data:
            raise SystemExit(f"missing required key: {key}")

    canvas = data["canvas"]
    if not isinstance(canvas, dict) or any(key not in canvas for key in ("width", "height", "background")):
        raise SystemExit("canvas must include width, height, and background")
    if canvas["width"] <= 0 or canvas["height"] <= 0:
        raise SystemExit("canvas dimensions must be positive")

    layers = data["layers"]
    if not isinstance(layers, list) or not layers:
        raise SystemExit("layers must be a non-empty array")

    ids: set[str] = set()
    last_z = float("-inf")
    asset_paths: list[Path] = []
    for index, layer in enumerate(layers):
        if not isinstance(layer, dict):
            raise SystemExit(f"layer {index} must be an object")
        for key in ("id", "name", "type", "z_index", "bounds"):
            if key not in layer:
                raise SystemExit(f"layer {index} missing {key}")
        if layer["id"] in ids:
            raise SystemExit(f"duplicate layer id: {layer['id']}")
        ids.add(layer["id"])
        if layer["type"] not in LAYER_TYPES:
            raise SystemExit(f"unsupported layer type: {layer['type']}")
        if layer["z_index"] < last_z:
            raise SystemExit("layers must be ordered by nondecreasing z_index")
        last_z = layer["z_index"]

        bounds = layer["bounds"]
        if not isinstance(bounds, dict) or any(key not in bounds for key in ("x", "y", "width", "height")):
            raise SystemExit(f"layer {layer['id']} has invalid bounds")
        if bounds["width"] <= 0 or bounds["height"] <= 0:
            raise SystemExit(f"layer {layer['id']} must have positive dimensions")

        if layer["type"] == "text" and "text" not in layer:
            raise SystemExit(f"text layer {layer['id']} is missing text data")
        if layer["type"] == "raster":
            raster = layer.get("raster")
            if not isinstance(raster, dict) or any(key not in raster for key in ("asset_id", "path", "fit")):
                raise SystemExit(f"raster layer {layer['id']} has invalid raster data")
            asset_path = (project_root / raster["path"]).resolve()
            if not asset_path.is_file():
                raise SystemExit(f"missing raster asset: {asset_path}")
            asset_paths.append(asset_path)
        if layer["type"] == "icon":
            icon = layer.get("icon")
            required = ("icon_id", "svg_path", "preview_path", "fit")
            if not isinstance(icon, dict) or any(key not in icon for key in required):
                raise SystemExit(f"icon layer {layer['id']} has invalid icon data")
            for key in ("svg_path", "preview_path"):
                asset_path = (project_root / icon[key]).resolve()
                if not asset_path.is_file():
                    raise SystemExit(f"missing icon asset: {asset_path}")
                asset_paths.append(asset_path)
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
