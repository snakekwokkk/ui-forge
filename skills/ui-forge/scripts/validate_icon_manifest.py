#!/usr/bin/env python3
"""Validate sourced icon metadata and optional icon layers."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from validate_layer_spec import iter_layers


ALLOWED_LIBRARIES = {"Iconoir", "Phosphor Icons", "Lucide", "Tabler Icons", "Remix Icon"}
REQUIRED = {
    "icon_id", "semantic_role", "screen", "state", "library", "icon_name",
    "variant", "source_url", "license", "license_url", "permission_basis",
    "svg_path", "preview_path", "size", "color", "target_layers",
}


def load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid icon manifest JSON: {exc}")
    if not isinstance(data, dict):
        raise SystemExit("icon manifest root must be an object")
    return data


def validate(manifest_path: Path, project_root: Path, layer_spec: Path | None = None) -> int:
    data = load(manifest_path)
    icons = data.get("icons")
    if not isinstance(icons, list) or not icons:
        raise SystemExit("icon manifest must contain a non-empty icons array")

    by_id: dict[str, dict] = {}
    libraries: set[str] = set()
    for index, icon in enumerate(icons):
        if not isinstance(icon, dict):
            raise SystemExit(f"icon {index} must be an object")
        missing = REQUIRED - set(icon)
        if missing:
            raise SystemExit(f"icon {index} missing: {', '.join(sorted(missing))}")
        icon_id = str(icon["icon_id"])
        if icon_id in by_id:
            raise SystemExit(f"duplicate icon_id: {icon_id}")
        by_id[icon_id] = icon
        if icon["library"] not in ALLOWED_LIBRARIES:
            raise SystemExit(f"unsupported icon library: {icon['library']}")
        libraries.add(str(icon["library"]))
        if not str(icon["source_url"]).startswith("https://") or not str(icon["license_url"]).startswith("https://"):
            raise SystemExit(f"icon URLs must use https: {icon_id}")
        if not str(icon["permission_basis"]).strip():
            raise SystemExit(f"missing permission_basis: {icon_id}")
        if not isinstance(icon["target_layers"], list) or not icon["target_layers"]:
            raise SystemExit(f"target_layers must be non-empty: {icon_id}")
        if float(icon["size"]) <= 0:
            raise SystemExit(f"icon size must be positive: {icon_id}")
        for key in ("svg_path", "preview_path"):
            asset = (project_root / icon[key]).resolve()
            if not asset.is_file():
                raise SystemExit(f"missing {key} for {icon_id}: {asset}")

    if data.get("family_policy") == "single-library-per-screen-set" and len(libraries) != 1:
        raise SystemExit(
            "family_policy requires one approved icon library per screen set; "
            f"found: {', '.join(sorted(libraries))}"
        )

    if layer_spec:
        spec = load(layer_spec)
        for layer in iter_layers(spec.get("layers", [])):
            if layer.get("type") != "icon":
                continue
            icon_data = layer.get("icon", {})
            icon_id = icon_data.get("icon_id")
            record = by_id.get(icon_id)
            if record is None:
                raise SystemExit(f"missing icon manifest record: {icon_id}")
            for key in ("svg_path", "preview_path"):
                if icon_data.get(key) != record.get(key):
                    raise SystemExit(f"icon path mismatch for {icon_id}: {key}")
    return len(icons)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--layer-spec", type=Path)
    args = parser.parse_args()
    manifest = args.manifest.resolve()
    root = (args.project_root or manifest.parent).resolve()
    count = validate(manifest, root, args.layer_spec.resolve() if args.layer_spec else None)
    print(f"valid icon manifest: {manifest} ({count} icons)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
