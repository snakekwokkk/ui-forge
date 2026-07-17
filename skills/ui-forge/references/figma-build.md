# Figma build

Use the installed Figma workflows and obey their prerequisites.

## Before writing

- Require a valid file or node URL.
- Inspect the target file, node, existing design system, variables, and components.
- Search the design system before creating equivalents.
- Default to a new Section or Frame; do not overwrite without explicit permission.
- Upload or prepare raster assets before assembling dependent nodes.
- Validate the selected `*.layers.json` file and its preview lock before writing.
- Treat the locked layer specification as the geometry and z-order source of truth.
- Read `figma-script-and-qa.md`, create a verified image-hash map, and generate the Figma write body from the locked specification.
- Validate asset provenance and reject reference-only, competitor, website-scraped, or unconfirmed rasters before upload.

## Build order

1. Create or reuse semantic variables.
2. Create the target Section and screen Frames.
3. Establish grids and Auto Layout.
4. Add native surfaces and reusable components.
5. Add editable text with correct styles.
6. Add simple vector icons and diagrams.
7. Place separate raster assets with semantic names.
8. Bind tokens and verify constraints.
9. Capture a screenshot for QA.
10. Populate `delivery-gates.json` from live Figma node IDs, layout modes, variable bindings, and asset placements.
11. Run `python3 scripts/validate_delivery_gates.py delivery-gates.json`; stop and repair the Figma build unless it returns `pass`.

## Hard-gate evidence

- Asset evidence must contain one unique Figma asset node and one labeled library-tile node for every accepted `asset-manifest.json` ID.
- Auto Layout evidence must enumerate every managed screen root and every structural container. Do not classify a content container as decoration to bypass the gate.
- Variable evidence must map every required Brand DNA token to a Figma variable and count all eligible and bound properties across managed screens. Require 100% coverage and zero unbound eligible properties.
- Do not mark the build report as complete when `delivery-gates.json` is absent, stale, or failing.

## Same-source write contract

For each locked layer, preserve its ID in the semantic Figma layer name or build report. Upload the exact locked raster file; do not regenerate it. Apply the exact bounds, crop, rotation, opacity, and z-order from the layer spec. Map text and native shapes to editable Figma nodes. If a change is needed, update the layer spec and preview first, then rebuild or patch Figma from the new lock.

Do not manually recreate a locked composition when the deterministic generator supports its layers. Generated scripts are disposable build artifacts; the layer spec, asset files, and lock remain authoritative.

## Naming

Use names such as `Option B / Home / Hero`, `Component / Button / Primary`, and `Asset / 3D / Shield`. Keep option Sections independent when building multiple directions.

## Failure boundary

If Figma tools or authorization are unavailable, complete the design specs and asset manifest, then report the exact missing capability. Do not pretend that a Figma write occurred.
