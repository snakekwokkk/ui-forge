# Input classification

Classify mixed first-turn inputs before analysis. One file may have multiple roles.

## Signals

### brand_reference

Polished color, typography, imagery, real components, product photography, completed UI, campaign art, or repeated brand motifs.

### wireframe

Grayscale or low-fidelity frames, placeholder rectangles, skeletal navigation, structural labels, annotations, repeated device canvases, or incomplete visual styling.

### official_asset

Logos, icons, photos, illustrations, fonts, or exported files that the user explicitly identifies as reusable target-brand assets or explicitly authorizes for placement. A clean export or transparent PNG is not sufficient evidence by itself.

### existing_product_ui

Production screenshots that provide both brand and component behavior. Assign both `existing_product_ui` and `brand_reference` when appropriate.

### competitor_reference

Material from a different product used for inspiration. Never treat it as owned brand material or copy proprietary assets.

### figma_target

A `figma.com/design/` URL, preferably with `node-id`. Record file and node identifiers only after parsing a valid URL; never guess a node.

## Confidence

- `high`: unmistakable structural or polished-product signals.
- `medium`: mixed-purpose image or incomplete contextual evidence.
- `low`: ambiguous image, unknown ownership, or conflicting cues.

Ask only when an ambiguity changes layout authority, brand authority, asset reuse permission, or write destination.

Default screenshots, URLs, moodboards, polished product views, and campaign images to `reference_only` with `reuse_permission: false`. Do not infer reuse permission from upload alone. When exact reuse is unnecessary, generate an original replacement instead of interrupting the workflow.
