# Reference evidence versus reusable assets

Treat visual inspiration and asset permission as separate questions.

## Default rule

URLs, screenshots, moodboards, competitor examples, campaign images, and polished product views are `reference_only` by default. Use them to infer colors, typography behavior, spacing, radii, composition, imagery category, material qualities, and visual tone. Do not crop, trace, extract, place, or upload their people, devices, illustrations, photography, icons, logos, or decorative objects into generated UI.

Uploading or linking an image does not grant reuse permission. A clean PNG, transparent background, or isolated subject is still reference-only unless the user explicitly says it is a reusable target-brand asset.

## Reusable status

Mark an input reusable only when at least one permission basis is explicit:

- The user says the file is their own asset or authorizes reuse.
- The file is an official target-brand asset supplied for placement, not merely a style reference.
- The asset was generated originally during the current workflow.
- The asset was created natively in Figma or code during the current workflow.

Record `permission_basis` and `usage` for each raster. Never infer permission from file format, visual polish, transparency, or proximity to the wireframe.

## Original-generation rule

When a direction needs complex imagery, generate a new original asset that matches only the extracted design DNA and requested subject category. Change the person, pose, device, composition, props, silhouette, and scene details enough that the result is not a copy or near-copy of a reference asset. Do not reproduce reference logos, UI screenshots, identifiable people, mascots, or distinctive compositions unless explicitly authorized.

Use the installed image-generation workflow for original bitmap assets. Generate each complex object or scene independently before composing the UI preview. The preview and Figma build must use the same generated file.

## Guardrail

Create `asset-provenance.json` from the bundled template. Before rendering any layer spec containing raster layers, run `scripts/validate_asset_provenance.py`. Allowed `usage` values are:

- `generated_original`
- `user_authorized_asset`
- `target_brand_owned_asset`

Reject `reference_only`, `competitor_reference`, `website_scrape`, and `unconfirmed`. If authorization is unclear, generate an original replacement instead of asking by default; ask only when exact asset reuse is essential to the request.
