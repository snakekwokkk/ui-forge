#!/usr/bin/env python3
"""Require real alpha transparency for isolated raster assets used in previews."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

try:
    from PIL import Image, ImageStat
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Pillow is required for raster alpha validation. "
        "Install it in the active Python environment before running this gate."
    ) from exc

from validate_layer_spec import iter_layers


POLICIES = {
    "transparent_required",
    "opaque_composite_expected",
    "embedded_background_authorized",
}
ASSET_ROLES = {
    "isolated_object",
    "composite_scene",
    "surface_texture",
    "full_bleed_background",
}
OPAQUE_ROLES = {"composite_scene", "surface_texture", "full_bleed_background"}


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return data


def alpha_statistics(path: Path, transparent_threshold: int = 16) -> dict:
    try:
        with Image.open(path) as source:
            image_format = source.format
            bands = source.getbands()
            if "A" not in bands:
                raise ValueError(f"asset has no alpha channel: {path}")
            rgba = source.convert("RGBA")
            alpha = rgba.getchannel("A")
            width, height = alpha.size
    except OSError as exc:
        raise ValueError(f"cannot inspect raster asset {path}: {exc}") from exc

    total = width * height
    transparent = sum(alpha.histogram()[: transparent_threshold + 1])
    transparent_ratio = transparent / max(1, total)
    border_width = max(1, round(min(width, height) * 0.03))
    border_crops = [
        alpha.crop((0, 0, width, border_width)),
        alpha.crop((0, height - border_width, width, height)),
        alpha.crop((0, border_width, border_width, height - border_width)),
        alpha.crop((width - border_width, border_width, width, height - border_width)),
    ]
    border_transparent = sum(
        sum(crop.histogram()[: transparent_threshold + 1])
        for crop in border_crops
    )
    border_total = sum(crop.width * crop.height for crop in border_crops)
    border_transparent_ratio = border_transparent / max(1, border_total)
    alpha_min, alpha_max = alpha.getextrema()
    opaque_bbox = alpha.point(lambda value: 255 if value >= 240 else 0).getbbox()
    if opaque_bbox is None:
        raise ValueError(f"asset contains no opaque subject: {path}")
    left, top, right, bottom = opaque_bbox
    clear_margins = {
        "left": left / max(1, width),
        "top": top / max(1, height),
        "right": (width - right) / max(1, width),
        "bottom": (height - bottom) / max(1, height),
    }
    bbox_width = max(1, right - left)
    bbox_height = max(1, bottom - top)
    patch_width = max(1, round(bbox_width * 0.04))
    patch_height = max(1, round(bbox_height * 0.04))
    corner_boxes = [
        (left, top, left + patch_width, top + patch_height),
        (right - patch_width, top, right, top + patch_height),
        (left, bottom - patch_height, left + patch_width, bottom),
        (right - patch_width, bottom - patch_height, right, bottom),
    ]
    corner_stats = [ImageStat.Stat(rgba.crop(box)) for box in corner_boxes]
    corners_opaque = all(stat.mean[3] >= 250 for stat in corner_stats)
    corners_locally_uniform = all(
        max(stat.stddev[:3]) <= 4 for stat in corner_stats
    )
    channel_means = [
        [stat.mean[channel] for stat in corner_stats]
        for channel in range(3)
    ]
    corners_match = all(
        max(values) - min(values) <= 10 for values in channel_means
    )
    return {
        "format": image_format,
        "mode": "RGBA",
        "width": width,
        "height": height,
        "alpha_min": alpha_min,
        "alpha_max": alpha_max,
        "transparent_ratio": round(transparent_ratio, 6),
        "border_transparent_ratio": round(border_transparent_ratio, 6),
        "opaque_bbox": {
            "x": left,
            "y": top,
            "width": bbox_width,
            "height": bbox_height,
        },
        "clear_margin_ratios": {
            key: round(value, 6) for key, value in clear_margins.items()
        },
        "uniform_opaque_bbox_corners": (
            corners_opaque and corners_locally_uniform and corners_match
        ),
    }


def validate_alpha(
    project_root: Path,
    provenance_path: Path,
    spec_paths: list[Path],
    min_transparent_ratio: float = 0.01,
    min_border_transparent_ratio: float = 0.85,
    min_clear_margin_ratio: float = 0.04,
) -> dict:
    provenance = load_json(provenance_path)
    records = provenance.get("assets")
    if not isinstance(records, list):
        raise ValueError("asset provenance must contain an assets array")
    by_id: dict[str, dict] = {}
    for record in records:
        if not isinstance(record, dict) or not str(record.get("asset_id", "")).strip():
            raise ValueError("every provenance record requires asset_id")
        asset_id = str(record["asset_id"])
        if asset_id in by_id:
            raise ValueError(f"duplicate provenance asset_id: {asset_id}")
        policy = record.get("background_policy", "transparent_required")
        if policy not in POLICIES:
            raise ValueError(f"asset {asset_id} has invalid background_policy: {policy}")
        if policy == "embedded_background_authorized" and not str(
            record.get("background_authorization", "")
        ).strip():
            raise ValueError(
                f"asset {asset_id} requires background_authorization "
                "for embedded_background_authorized"
            )
        role = record.get("asset_role")
        if role not in ASSET_ROLES:
            raise ValueError(f"asset {asset_id} has invalid asset_role: {role}")
        if role == "isolated_object" and policy != "transparent_required":
            raise ValueError(
                f"asset {asset_id} isolated_object must use transparent_required"
            )
        if policy == "transparent_required" and role != "isolated_object":
            raise ValueError(
                f"asset {asset_id} transparent_required is reserved for isolated_object"
            )
        if policy == "opaque_composite_expected" and role not in OPAQUE_ROLES:
            raise ValueError(
                f"asset {asset_id} opaque_composite_expected requires a composite role"
            )
        by_id[asset_id] = record

    seen: set[str] = set()
    validated_assets: list[dict] = []
    transparent_required_count = 0
    authorized_count = 0
    generated_opaque_composite_count = 0
    for spec_path in spec_paths:
        spec = load_json(spec_path)
        for layer in iter_layers(spec.get("layers", [])):
            if layer.get("type") != "raster":
                continue
            raster = layer.get("raster", {})
            asset_id = str(raster.get("asset_id", ""))
            if asset_id in seen:
                continue
            seen.add(asset_id)
            record = by_id.get(asset_id)
            if record is None:
                raise ValueError(f"missing provenance for raster asset: {asset_id}")
            if record.get("path") != raster.get("path"):
                raise ValueError(f"provenance path mismatch for asset: {asset_id}")
            asset_path = (project_root / str(raster.get("path", ""))).resolve()
            if not asset_path.is_file():
                raise ValueError(f"missing raster asset: {asset_path}")
            policy = record.get("background_policy", "transparent_required")
            if policy == "embedded_background_authorized":
                authorized_count += 1
                validated_assets.append(
                    {
                        "asset_id": asset_id,
                        "path": str(asset_path),
                        "background_policy": policy,
                        "status": "authorized",
                    }
                )
                continue
            if policy == "opaque_composite_expected":
                generated_opaque_composite_count += 1
                try:
                    with Image.open(asset_path) as source:
                        source.verify()
                    with Image.open(asset_path) as source:
                        width, height = source.size
                        image_format = source.format
                except OSError as exc:
                    raise ValueError(
                        f"cannot inspect composite raster asset {asset_path}: {exc}"
                    ) from exc
                if width < 2 or height < 2:
                    raise ValueError(
                        f"composite raster asset has invalid dimensions: {asset_id}"
                    )
                validated_assets.append(
                    {
                        "asset_id": asset_id,
                        "path": str(asset_path),
                        "asset_role": record["asset_role"],
                        "background_policy": policy,
                        "status": "pass",
                        "image": {
                            "format": image_format,
                            "width": width,
                            "height": height,
                        },
                    }
                )
                continue

            transparent_required_count += 1
            stats = alpha_statistics(asset_path)
            if stats["alpha_min"] > 16:
                raise ValueError(
                    f"asset {asset_id} contains no genuinely transparent pixels"
                )
            if stats["alpha_max"] < 200:
                raise ValueError(
                    f"asset {asset_id} contains no sufficiently opaque subject pixels"
                )
            if stats["transparent_ratio"] < min_transparent_ratio:
                raise ValueError(
                    f"asset {asset_id} transparent coverage is too low: "
                    f"{stats['transparent_ratio']:.4f}"
                )
            if stats["border_transparent_ratio"] < min_border_transparent_ratio:
                raise ValueError(
                    f"asset {asset_id} retains an opaque or baked background at its border: "
                    f"{stats['border_transparent_ratio']:.4f}"
                )
            if min(stats["clear_margin_ratios"].values()) < min_clear_margin_ratio:
                raise ValueError(
                    f"asset {asset_id} lacks sufficient transparent padding: "
                    f"{stats['clear_margin_ratios']}"
                )
            if stats["uniform_opaque_bbox_corners"]:
                raise ValueError(
                    f"asset {asset_id} appears to contain a padded opaque rectangular "
                    "background inside the alpha border"
                )
            validated_assets.append(
                {
                    "asset_id": asset_id,
                    "path": str(asset_path),
                    "background_policy": policy,
                    "status": "pass",
                    "alpha": stats,
                }
            )

    return {
        "status": "pass",
        "asset_provenance": str(provenance_path.resolve()),
        "validated_assets": validated_assets,
        "transparent_required_count": transparent_required_count,
        "generated_opaque_composite_count": generated_opaque_composite_count,
        "authorized_embedded_background_count": authorized_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("asset_provenance", type=Path)
    parser.add_argument("layer_specs", nargs="+", type=Path)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--report-out", type=Path)
    args = parser.parse_args()
    project_root = (
        args.project_root.resolve()
        if args.project_root
        else args.asset_provenance.resolve().parent
    )
    try:
        report = validate_alpha(
            project_root,
            args.asset_provenance.resolve(),
            [path.resolve() for path in args.layer_specs],
        )
    except ValueError as exc:
        raise SystemExit(f"raster alpha validation failed: {exc}") from exc
    if args.report_out:
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    print(
        "raster alpha: pass "
        f"({report['transparent_required_count']} transparent, "
        f"{report['generated_opaque_composite_count']} generated composite, "
        f"{report['authorized_embedded_background_count']} authorized embedded)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
