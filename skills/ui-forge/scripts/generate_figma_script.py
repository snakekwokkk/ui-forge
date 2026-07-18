#!/usr/bin/env python3
"""Generate deterministic nested Auto Layout Figma JavaScript from a locked layer spec."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from validate_asset_provenance import validate_provenance
from validate_icon_manifest import validate as validate_icons
from validate_layer_spec import iter_layers, load_json, sha256, validate, verify_lock


def hex_color(value: str) -> dict[str, float]:
    raw = value.lstrip("#")
    if len(raw) == 3:
        raw = "".join(character * 2 for character in raw)
    if len(raw) not in (6, 8):
        raise SystemExit(f"unsupported color: {value}")
    return {name: int(raw[index:index + 2], 16) / 255 for name, index in (("r", 0), ("g", 2), ("b", 4))}


def alpha(value: str) -> float:
    raw = value.lstrip("#")
    return int(raw[6:8], 16) / 255 if len(raw) == 8 else 1


def paint(fill: str | dict) -> dict:
    if isinstance(fill, str):
        return {"type": "SOLID", "color": hex_color(fill), "opacity": alpha(fill)}
    if fill.get("type") != "linear_gradient":
        raise SystemExit(f"unsupported fill type: {fill.get('type')}")
    direction = fill.get("direction", "vertical")
    transform = [[1, 0, 0], [0, 1, 0]] if direction == "horizontal" else [[0, 1, 0], [-1, 0, 1]]
    return {
        "type": "GRADIENT_LINEAR",
        "gradientTransform": transform,
        "gradientStops": [
            {"position": 0, "color": {**hex_color(fill.get("start", "#000000")), "a": alpha(fill.get("start", "#000000"))}},
            {"position": 1, "color": {**hex_color(fill.get("end", "#FFFFFF")), "a": alpha(fill.get("end", "#FFFFFF"))}},
        ],
    }


def js(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def emit_layout(lines: list[str], variable: str, layout: dict) -> None:
    padding = layout["padding"]
    lines.extend([
        f"{variable}.layoutMode = {js(layout['mode'])};",
        f"{variable}.primaryAxisSizingMode = {js(layout['primary_axis_sizing'])};",
        f"{variable}.counterAxisSizingMode = {js(layout['counter_axis_sizing'])};",
        f"{variable}.primaryAxisAlignItems = {js(layout['primary_axis_align'])};",
        f"{variable}.counterAxisAlignItems = {js(layout['counter_axis_align'])};",
        f"{variable}.itemSpacing = {float(layout['item_spacing'])};",
        f"{variable}.paddingTop = {float(padding['top'])};",
        f"{variable}.paddingRight = {float(padding['right'])};",
        f"{variable}.paddingBottom = {float(padding['bottom'])};",
        f"{variable}.paddingLeft = {float(padding['left'])};",
        f"{variable}.layoutWrap = {js(layout.get('wrap', 'NO_WRAP'))};",
    ])


def emit_common(lines: list[str], variable: str, parent: str, layer: dict) -> None:
    bounds = layer["bounds"]
    positioning = layer.get("layout_positioning", "AUTO")
    sizing = layer["sizing"]
    lines.extend([
        f"{variable}.name = {js(layer['name'] + ' [' + layer['id'] + ']')};",
        f"{variable}.resize({float(bounds['width'])}, {float(bounds['height'])});",
        f"{variable}.rotation = {float(layer.get('rotation', 0))};",
        f"{variable}.opacity = {float(layer.get('opacity', 1))};",
        f"{parent}.appendChild({variable});",
        f"{variable}.layoutPositioning = {js(positioning)};",
    ])
    if positioning == "ABSOLUTE":
        lines.append(f"{variable}.x = {float(bounds['x'])}; {variable}.y = {float(bounds['y'])};")
    lines.extend([
        f"{variable}.layoutSizingHorizontal = {js(sizing['horizontal'])};",
        f"{variable}.layoutSizingVertical = {js(sizing['vertical'])};",
        f"createdNodeIds.push({variable}.id);",
    ])


def emit_layer(
    lines: list[str],
    layer: dict,
    parent: str,
    index: list[int],
    project_root: Path,
    image_map: dict,
) -> None:
    current = index[0]
    index[0] += 1
    variable = f"node{current}"
    kind = layer["type"]
    if kind == "frame":
        style = layer.get("style", {})
        lines.extend([
            f"const {variable} = figma.createFrame();",
            f"{variable}.fills = [{js(paint(style.get('fill', '#00000000')))}];",
            f"{variable}.cornerRadius = {float(style.get('corner_radius', 0))};",
            f"{variable}.clipsContent = {str(bool(layer.get('layout', {}).get('clips_content', False))).lower()};",
        ])
        if style.get("stroke"):
            lines.extend([
                f"{variable}.strokes = [{js(paint(style['stroke']))}];",
                f"{variable}.strokeWeight = {float(style.get('stroke_width', 1))};",
            ])
    elif kind == "text":
        text = layer["text"]
        font = {"family": text.get("font_family", "Arial"), "style": text.get("font_style", "Regular")}
        lines.extend([
            f"const {variable} = figma.createText();",
            f"{variable}.fontName = {js(font)};",
            f"{variable}.characters = {js(str(text.get('content', '')))};",
            f"{variable}.fontSize = {float(text.get('font_size', 16))};",
            f"{variable}.lineHeight = {{unit:'PIXELS', value:{float(text.get('line_height', text.get('font_size', 16) * 1.2))}}};",
            f"{variable}.textAlignHorizontal = {js({'left':'LEFT','center':'CENTER','right':'RIGHT'}.get(text.get('align','left'), 'LEFT'))};",
            f"{variable}.fills = [{js(paint(text.get('color', '#000000')))}];",
            f"{variable}.textAutoResize = 'NONE';",
        ])
    elif kind == "raster":
        raster = layer["raster"]
        mapped = image_map[raster["asset_id"]]
        scale_mode = {"contain": "FIT", "cover": "FILL", "stretch": "FILL"}.get(raster.get("fit", "contain"), "FIT")
        lines.extend([
            f"const {variable} = figma.createRectangle();",
            f"{variable}.fills = [{{type:'IMAGE', imageHash:{js(mapped['image_hash'])}, scaleMode:{js(scale_mode)}}}];",
        ])
    elif kind == "icon":
        svg_text = (project_root / layer["icon"]["svg_path"]).read_text(encoding="utf-8")
        lines.append(f"const {variable} = figma.createNodeFromSvg({js(svg_text)});")
    elif kind == "ellipse":
        lines.append(f"const {variable} = figma.createEllipse();")
    else:
        lines.append(f"const {variable} = figma.createRectangle();")

    if kind not in ("text", "raster", "icon", "frame"):
        style = layer.get("style", {})
        lines.append(f"{variable}.fills = [{js(paint(style.get('fill', '#00000000')))}];")
        if kind == "line":
            lines.append(f"{variable}.cornerRadius = {float(style.get('stroke_width', 1)) / 2};")
        elif kind == "rectangle":
            lines.append(f"{variable}.cornerRadius = {float(style.get('corner_radius', 0))};")
        if style.get("stroke"):
            lines.extend([
                f"{variable}.strokes = [{js(paint(style['stroke']))}];",
                f"{variable}.strokeWeight = {float(style.get('stroke_width', 1))};",
            ])

    emit_common(lines, variable, parent, layer)
    if kind == "frame":
        emit_layout(lines, variable, layer["layout"])
        for child in layer["children"]:
            emit_layer(lines, child, variable, index, project_root, image_map)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--verify-lock", type=Path, required=True)
    parser.add_argument("--image-map", type=Path, required=True)
    parser.add_argument("--icon-manifest", type=Path)
    parser.add_argument("--asset-provenance", type=Path)
    parser.add_argument("--page-id", required=True)
    parser.add_argument("--frame-name")
    parser.add_argument("--x", type=float, default=0)
    parser.add_argument("--y", type=float, default=0)
    args = parser.parse_args()

    spec_path = args.spec.resolve()
    project_root = (args.project_root or spec_path.parent).resolve()
    asset_paths = validate(spec_path, project_root)
    verify_lock(spec_path, asset_paths, args.verify_lock.resolve())
    provenance_path = args.asset_provenance.resolve() if args.asset_provenance else None
    spec = load_json(spec_path)
    all_layers = list(iter_layers(spec["layers"]))
    has_raster = any(layer.get("type") == "raster" for layer in all_layers)
    has_icons = any(layer.get("type") == "icon" for layer in all_layers)
    if has_raster and provenance_path is None:
        raise SystemExit("--asset-provenance is required when the layer spec contains raster assets")
    if has_icons and args.icon_manifest is None:
        raise SystemExit("--icon-manifest is required when the layer spec contains icons")
    if args.icon_manifest:
        validate_icons(args.icon_manifest.resolve(), project_root, spec_path)
    if provenance_path:
        validate_provenance(spec_path, provenance_path)
        lock = load_json(args.verify_lock.resolve())
        if lock.get("provenance_sha256") != sha256(provenance_path):
            raise SystemExit("preview lock does not match the current asset provenance")
    image_map = load_json(args.image_map.resolve()).get("assets", {})

    fonts: list[dict[str, str]] = []
    for layer in all_layers:
        if layer["type"] == "text":
            font = {"family": layer["text"].get("font_family", "Arial"), "style": layer["text"].get("font_style", "Regular")}
            if font not in fonts:
                fonts.append(font)
        if layer["type"] == "raster":
            raster = layer["raster"]
            if raster.get("crop") is not None:
                raise SystemExit(f"raster crop requires an explicit Figma imageTransform implementation: {layer['id']}")
            mapped = image_map.get(raster["asset_id"], {})
            if not mapped.get("image_hash") or str(mapped["image_hash"]).startswith("REPLACE_"):
                raise SystemExit(f"missing Figma image hash for asset: {raster['asset_id']}")
            if mapped.get("source_path") and mapped["source_path"] != str(raster["path"]):
                raise SystemExit(f"image map source mismatch for {raster['asset_id']}: expected {raster['path']}")

    canvas = spec["canvas"]
    frame_name = args.frame_name or f"Option {spec['option']} / {spec['screen_id']}"
    lines = [
        "// Generated by UIForge. Do not hand-edit; regenerate from the locked layer spec.",
        f"const page = await figma.getNodeByIdAsync({js(args.page_id)});",
        "if (!page || page.type !== 'PAGE') throw new Error('Target page was not found');",
        "await figma.setCurrentPageAsync(page);",
        f"await Promise.all({js(fonts)}.map(font => figma.loadFontAsync(font)));",
        "const createdNodeIds = [];",
        "const screen = figma.createFrame();",
        f"screen.name = {js(frame_name)}; screen.x = {args.x}; screen.y = {args.y};",
        f"screen.resize({float(canvas['width'])}, {float(canvas['height'])});",
        f"screen.clipsContent = {str(bool(canvas['layout'].get('clips_content', True))).lower()};",
        f"screen.fills = [{js(paint(canvas['background']))}];",
        "page.appendChild(screen);",
    ]
    emit_layout(lines, "screen", canvas["layout"])
    node_index = [0]
    for layer in spec["layers"]:
        emit_layer(lines, layer, "screen", node_index, project_root, image_map)

    lines.extend([
        "figma.currentPage.selection = [screen];",
        "figma.viewport.scrollAndZoomIntoView([screen]);",
        "return {frameId: screen.id, createdNodeIds, layerCount: createdNodeIds.length};",
    ])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"generated Figma script: {args.output} ({len(all_layers)} layers)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
