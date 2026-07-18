# Same-source preview and Figma pipeline

Treat the layer specification and locked asset files as the source of truth. Never treat a flattened preview as the source.

## Required order

1. Plan native UI layers and complex asset families.
2. Generate every complex asset as a separate original transparent file, or use only explicitly authorized target-brand assets.
3. Create and validate `asset-provenance.json`.
4. Create schema-v2 `option-<id>-home.layers.json` from `assets/layer-spec-template.json`. Analyze the normal module hierarchy first and encode it as nested structural Frames.
5. Validate it with `scripts/validate_layer_spec.py`.
6. Render the preview with `scripts/render_layer_spec.py --asset-provenance asset-provenance.json`; keep the generated lock file.
7. Present A, B, and C and wait for the primary selection.
8. Verify the selected lock and provenance before any Figma write.
9. Build Figma nodes from the same nested layer tree and asset files.
10. Capture a Figma screenshot and compare it with the rendered preview.

## Asset rules

- Use image generation only for isolated complex assets, never for the complete UI screen.
- Use stable asset IDs and project-relative paths.
- Preserve alpha PNG or WebP outputs in the project.
- Record SHA-256 hashes in the preview lock.
- Regenerate a preview and lock after any asset, crop, position, scale, rotation, opacity, text, or style change.
- Do not silently substitute an asset during Figma reconstruction.
- Do not treat upload, transparency, polish, or website origin as reuse permission.

## Layer mapping

- `frame`: create a semantic nested Figma Frame with `HORIZONTAL` or `VERTICAL` Auto Layout. Sections, stacks, rows, cards, lists, action groups, headers, footers, forms, and navigation must use this type.
- `rectangle`, `ellipse`, and `line`: create native Figma shapes.
- `text`: create native editable text with the specified family, style, size, line height, alignment, and color.
- `raster`: upload the exact locked file and apply the layer's fit, crop, bounds, rotation, and opacity.
- Every child declares `sizing.horizontal`, `sizing.vertical`, and `layout_positioning`.
- Use `layout_positioning: AUTO` for normal content. `ABSOLUTE` is allowed only with a non-empty decorative overlay reason and is rejected for structural Frames.
- Preserve child array order as the default z-order; use `z_index` for validation and explicit ordering.

## Fidelity boundary

Asset identity, geometry, z-order, color values, copy, and layout must match. Minor antialiasing differences between Pillow and Figma font/rendering engines are acceptable. A different illustration, missing decoration, changed crop, or manually approximated placement is not acceptable.
