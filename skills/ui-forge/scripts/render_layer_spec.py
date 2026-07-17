#!/usr/bin/env python3
"""Render a deterministic UIForge preview from a same-source layer spec."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont

from validate_layer_spec import validate
from validate_asset_provenance import validate_provenance


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rgba(value: str, opacity: float = 1) -> tuple[int, int, int, int]:
    color = ImageColor.getcolor(value, "RGBA")
    return color[:3] + (round(color[3] * max(0, min(1, opacity))),)


def resize_for_fit(image: Image.Image, width: int, height: int, fit: str) -> Image.Image:
    if fit == "stretch":
        return image.resize((width, height), Image.Resampling.LANCZOS)
    scale = min(width / image.width, height / image.height) if fit == "contain" else max(width / image.width, height / image.height)
    resized = image.resize((max(1, round(image.width * scale)), max(1, round(image.height * scale))), Image.Resampling.LANCZOS)
    if fit == "cover":
        left = max(0, (resized.width - width) // 2)
        top = max(0, (resized.height - height) // 2)
        resized = resized.crop((left, top, left + width, top + height))
    return resized


def apply_opacity(image: Image.Image, opacity: float) -> Image.Image:
    if opacity >= 1:
        return image
    alpha = image.getchannel("A").point(lambda value: round(value * max(0, opacity)))
    image = image.copy()
    image.putalpha(alpha)
    return image


def load_font(text: dict, project_root: Path) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    size = max(1, round(text.get("font_size", 16)))
    path = text.get("font_path")
    candidates = []
    if path:
        candidates.append(project_root / path)
    family = text.get("font_family", "Arial")
    style = text.get("font_style", "Regular")
    candidates.extend([
        Path(f"/System/Library/Fonts/Supplemental/{family} {style}.ttf"),
        Path(f"/System/Library/Fonts/Supplemental/{family}.ttf"),
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf" if "Bold" in style else "/System/Library/Fonts/Supplemental/Arial.ttf"),
    ])
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def rounded_mask(width: int, height: int, radius: int) -> Image.Image:
    mask = Image.new("L", (width, height), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, width - 1, height - 1), radius=max(0, radius), fill=255)
    return mask


def fill_image(fill: str | dict, width: int, height: int, opacity: float) -> Image.Image:
    if isinstance(fill, str):
        return Image.new("RGBA", (width, height), rgba(fill, opacity))
    if fill.get("type") != "linear_gradient":
        raise SystemExit(f"unsupported fill type: {fill.get('type')}")
    start = rgba(fill.get("start", "#000000"), opacity)
    end = rgba(fill.get("end", "#FFFFFF"), opacity)
    direction = fill.get("direction", "vertical")
    image = Image.new("RGBA", (width, height), start)
    draw = ImageDraw.Draw(image)
    steps = width if direction == "horizontal" else height
    for index in range(max(1, steps)):
        ratio = index / max(1, steps - 1)
        color = tuple(round(start[channel] + (end[channel] - start[channel]) * ratio) for channel in range(4))
        if direction == "horizontal":
            draw.line((index, 0, index, height), fill=color)
        else:
            draw.line((0, index, width, index), fill=color)
    return image


def render_shape(layer: dict, width: int, height: int) -> Image.Image:
    style = layer.get("style", {})
    opacity = layer.get("opacity", 1)
    fill = style.get("fill", "#00000000")
    source = fill_image(fill, width, height, opacity)
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    radius = round(style.get("corner_radius", 0))
    if layer["type"] == "ellipse":
        mask = Image.new("L", (width, height), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, width - 1, height - 1), fill=255)
        image.paste(source, (0, 0), mask)
    elif layer["type"] == "line":
        draw = ImageDraw.Draw(image)
        color = rgba(fill if isinstance(fill, str) else fill.get("start", "#000000"), opacity)
        draw.line((0, height // 2, width - 1, height // 2), fill=color, width=max(1, round(style.get("stroke_width", 1))))
    else:
        image.paste(source, (0, 0), rounded_mask(width, height, radius))
    stroke = style.get("stroke")
    if stroke and layer["type"] != "line":
        draw = ImageDraw.Draw(image)
        stroke_width = max(1, round(style.get("stroke_width", 1)))
        if layer["type"] == "ellipse":
            draw.ellipse((0, 0, width - 1, height - 1), outline=rgba(stroke, opacity), width=stroke_width)
        else:
            draw.rounded_rectangle((0, 0, width - 1, height - 1), radius=max(0, radius), outline=rgba(stroke, opacity), width=stroke_width)
    return image


def render_text(layer: dict, width: int, height: int, project_root: Path) -> Image.Image:
    text = layer["text"]
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    font = load_font(text, project_root)
    content = str(text.get("content", ""))
    color = rgba(text.get("color", "#000000"), layer.get("opacity", 1))
    align = text.get("align", "left")
    line_height = max(1, round(text.get("line_height", text.get("font_size", 16) * 1.2)))
    lines = content.splitlines() or [""]
    y = 0
    for line in lines:
        box = draw.textbbox((0, 0), line, font=font)
        line_width = box[2] - box[0]
        x = 0 if align == "left" else (width - line_width) / 2 if align == "center" else width - line_width
        draw.text((round(x), y), line, font=font, fill=color)
        y += line_height
    return image


def render_raster(layer: dict, width: int, height: int, project_root: Path) -> Image.Image:
    raster = layer["raster"]
    source = Image.open(project_root / raster["path"]).convert("RGBA")
    crop = raster.get("crop")
    if crop:
        x, y, w, h = (crop[key] for key in ("x", "y", "width", "height"))
        source = source.crop((x, y, x + w, y + h))
    resized = resize_for_fit(source, width, height, raster.get("fit", "contain"))
    layer_image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    layer_image.alpha_composite(resized, ((width - resized.width) // 2, (height - resized.height) // 2))
    return apply_opacity(layer_image, layer.get("opacity", 1))


def render_icon(layer: dict, width: int, height: int, project_root: Path) -> Image.Image:
    icon = layer["icon"]
    source = Image.open(project_root / icon["preview_path"]).convert("RGBA")
    resized = resize_for_fit(source, width, height, icon.get("fit", "contain"))
    layer_image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    layer_image.alpha_composite(resized, ((width - resized.width) // 2, (height - resized.height) // 2))
    return apply_opacity(layer_image, layer.get("opacity", 1))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--lock-out", type=Path)
    parser.add_argument("--asset-provenance", type=Path)
    args = parser.parse_args()

    spec_path = args.spec.resolve()
    project_root = (args.project_root or spec_path.parent).resolve()
    asset_paths = validate(spec_path, project_root)
    provenance_path = args.asset_provenance.resolve() if args.asset_provenance else None
    spec = json.loads(spec_path.read_text(encoding="utf-8"))
    has_raster = any(layer.get("type") == "raster" for layer in spec.get("layers", []))
    if has_raster and provenance_path is None:
        raise SystemExit("--asset-provenance is required when the layer spec contains raster assets")
    if provenance_path:
        validate_provenance(spec_path, provenance_path)
    canvas_spec = spec["canvas"]
    canvas = fill_image(canvas_spec["background"], round(canvas_spec["width"]), round(canvas_spec["height"]), 1)

    for layer in spec["layers"]:
        bounds = layer["bounds"]
        width, height = round(bounds["width"]), round(bounds["height"])
        if layer["type"] == "text":
            layer_image = render_text(layer, width, height, project_root)
        elif layer["type"] == "raster":
            layer_image = render_raster(layer, width, height, project_root)
        elif layer["type"] == "icon":
            layer_image = render_icon(layer, width, height, project_root)
        else:
            layer_image = render_shape(layer, width, height)
        rotation = layer.get("rotation", 0)
        if rotation:
            layer_image = layer_image.rotate(-rotation, expand=True, resample=Image.Resampling.BICUBIC)
        center_x = bounds["x"] + bounds["width"] / 2
        center_y = bounds["y"] + bounds["height"] / 2
        canvas.alpha_composite(layer_image, (round(center_x - layer_image.width / 2), round(center_y - layer_image.height / 2)))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(args.output, "PNG")
    lock_path = args.lock_out or args.output.with_suffix(args.output.suffix + ".lock.json")
    lock = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "spec_path": str(spec_path),
        "spec_sha256": sha256(spec_path),
        "preview_path": str(args.output.resolve()),
        "preview_sha256": sha256(args.output.resolve()),
        "assets": {str(path): sha256(path) for path in asset_paths},
    }
    if provenance_path:
        lock["provenance_path"] = str(provenance_path)
        lock["provenance_sha256"] = sha256(provenance_path)
    lock_path.write_text(json.dumps(lock, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"rendered preview: {args.output}")
    print(f"wrote preview lock: {lock_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
