# Hard delivery gates

Run these checks after the selected direction has been written to Figma and before final QA completion. Populate `delivery-gates.json` from live Figma inspection, not assumptions or planned node IDs.

## 1. Candidate asset placement

- Treat every non-rejected `used_or_optional` entry in `asset-manifest.json` as an accepted candidate.
- Require at least 12 unique accepted asset IDs; normally keep the catalog within 12–18.
- Create `Asset Library — Candidate Materials` in Figma.
- Place every accepted asset as a separate labeled library item.
- Record the Figma asset node ID and library-tile node ID for every accepted asset.
- Require the accepted manifest ID set and placement ID set to match exactly.
- Do not count duplicates, color-only duplicates, empty placeholders, reference-only imagery, or one composition split into arbitrary fragments as separate candidates.

## 2. Auto Layout coverage

- Require every managed screen root to have `layoutMode` equal to `VERTICAL` or `HORIZONTAL`.
- Inventory every structural Frame: page sections, stacks, rows, cards, lists, action groups, headers, footers, and navigation.
- Require every structural Frame to use Auto Layout.
- Allow exceptions only for vectors, raster/image nodes, leaf shapes, masks, and documented decorative or absolute overlays whose children do not form a content structure.
- Record root IDs, structural-container IDs, Auto Layout container IDs, and exception reasons from a live Figma scan.
- Any missing root, undocumented structural exception, or structural set mismatch fails the gate.

## 3. Brand DNA variable binding

- Convert confirmed Brand DNA colors, spacing, radii, and typography into Figma variables.
- Require collections for `primitives`, `semantic`, `dimensions`, and `typography`.
- Give every required Brand DNA token a stable token ID and map it to one Figma variable ID.
- Bind every eligible fill, stroke, text color, font property, spacing, padding, gap, radius, and other supported managed-screen property.
- Record required token IDs, token-to-variable mappings, eligible property count, bound property count, and any unbound properties.
- Require exact required-token coverage, zero unbound eligible properties, and `bound_property_count == eligible_property_count`.

## Evidence and validation

Start from `assets/delivery-gates-template.json`. Then run:

```bash
python3 scripts/validate_delivery_gates.py delivery-gates.json
```

The validator must print `pass`. Otherwise remain in `BUILDING_FIGMA`, `VISUAL_QA`, or `REVISING`; do not report completion or move to the additional-option gate.
