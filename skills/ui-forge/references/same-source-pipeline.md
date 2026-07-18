# Same-source preview and Figma pipeline

Treat the layer specification and locked asset files as the source of truth. Never treat a flattened preview as the source.

## Required order

1. Plan native UI layers and complex asset families.
2. Create `wireframe-content-lock.json` and lock exact copy plus required structure.
3. Generate every complex asset as a separate original transparent file, or use only explicitly authorized target-brand assets.
4. Create `asset-provenance.json` with a `background_policy` for every raster.
5. Create schema-v2 `option-<id>-home.layers.json` from `assets/layer-spec-template.json`. Analyze the normal module hierarchy first and encode it as nested structural Frames. Apply every locked `content_id` and `structure_id`.
6. Validate the layer specs and provenance.
7. Render the preview with `scripts/render_layer_spec.py --asset-provenance asset-provenance.json`; keep the generated lock file.
8. Run `scripts/validate_preview_gates.py` against A, B, and C and require a passing `preview-gates.json`.
9. Present A, B, and C and wait for the primary selection.
10. Verify the selected lock, provenance, content lock, and preview-gate report before any Figma write.
11. Build Figma nodes from the same nested layer tree and asset files.
12. Capture a Figma screenshot and compare it with the rendered preview.

## Asset rules

- Use image generation only for isolated complex assets, never for the complete UI screen.
- Use stable asset IDs and project-relative paths.
- Preserve alpha PNG or WebP outputs in the project.
- Default every isolated raster to `background_policy: transparent_required`.
- Reject opaque white, pale, studio, gradient, or other baked rectangular backgrounds. A PNG extension alone is not transparency evidence.
- Use `embedded_background_authorized` only when the user explicitly authorizes the raster background as part of the final composition; record the authorization in provenance.
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

Line wrapping may differ only through layout behavior. Do not change semantic text content to force a wrap; the fidelity validator normalizes Unicode and whitespace while preserving wording, numbers, and punctuation.
