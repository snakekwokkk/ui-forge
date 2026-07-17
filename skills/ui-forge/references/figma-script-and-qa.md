# Deterministic Figma script and visual QA

Use this procedure after a preview has been approved and locked.

## 1. Upload the locked assets

Upload every raster referenced by the selected `*.layers.json`. Use the exact files recorded in the preview lock. Save each returned Figma image hash in a copy of `assets/figma-image-map-template.json`. The `asset_id` and `source_path` must match the layer spec.

## 2. Generate the write script

Run:

```bash
python scripts/generate_figma_script.py option-b-home.layers.json option-b-home.figma.js \
  --project-root PROJECT_ROOT \
  --verify-lock option-b-home.png.lock.json \
  --asset-provenance asset-provenance.json \
  --image-map figma-image-map.json \
  --page-id FIGMA_PAGE_ID
```

The generator refuses stale locks, reference-only assets, missing image hashes, mismatched source paths, unsupported fills, and raster crops without an exact Figma transform. Fix the source specification instead of bypassing the refusal.

## 3. Write to Figma

Load the installed Figma-use prerequisite, then submit the generated JavaScript as the write body. Do not manually retype coordinates or substitute assets. The script creates one frame, editable native layers, text nodes, and image-filled asset nodes whose names retain stable layer IDs.

## 4. Compare screenshots

Capture the exact Figma frame without editor chrome. Compare it with the approved preview:

```bash
python scripts/compare_previews.py option-b-home.png figma-option-b-home.png \
  --report option-b-home.qa.json \
  --diff option-b-home.diff.png
```

`pass` is required for normal completion. Font rasterization can create small differences, so the default tolerances permit limited antialiasing drift. Asset identity, geometry, crop, z-order, and major color differences should exceed the tolerance and return `revise`.

When the result is `revise`, change the layer spec, rerender and relock the preview, regenerate the Figma script, and rewrite the affected frame. Never fix only the Figma copy because that breaks same-source reproducibility.
