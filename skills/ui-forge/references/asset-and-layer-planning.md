# Asset and layer planning

Plan editability before reconstruction.

## Native-first priority

1. Text: always rebuild with real text layers.
2. Layout: Frames, Sections, Auto Layout, constraints, and grids.
3. Components: buttons, cards, fields, navigation, badges, and repeated modules.
4. Vector: simple icons, gauges, diagrams, and geometric decoration.
5. Raster: complex 3D, photography, illustration, texture, and painterly effects.
6. Flattened raster: only when extraction or reconstruction would materially degrade the result.

## Raster strategy

Prefer only user-authorized target-brand assets. Otherwise generate new original complex assets independently with transparent backgrounds and sufficient padding. Reference screenshots and campaign images are never extraction sources by default. If a user-authorized flattened composition exists, isolate the smallest complex region possible and reconstruct surrounding surfaces natively.

For a selected direction, maintain a candidate catalog of at least 12 meaningful complex assets or variants, normally 12–18. A useful catalog may include primary hero objects, alternate poses, promotional objects, empty-state illustrations, security objects, financial objects, decorative clusters, and background treatments. Count only independently reusable visual assets; do not count text, buttons, cards, or trivial duplicate exports.

Use the approved material-style profile as the source of truth for every generated candidate. If the reference system is photographic, the catalog may consist entirely of original photography and photographic cutouts. If it is cartoon, 3D, vector, hand-drawn, clay, collage, or mixed media, generate the corresponding original asset family. Do not force a medium that is absent from the references. Keep recurring people or characters consistent by defining identity, proportions, wardrobe or shape language, palette, and rendering rules before generating pose variants.

The three-option comparison stage may plan candidate families without rendering every candidate at full resolution. After the primary selection, generate the selected direction's complete 12–18 item catalog before full-screen extension. Store all candidates in the Figma asset library even if only a subset appears in the current screens.

## Same-source composition

Record a stable asset ID, file path, crop box, visible bounds, position, scale, rotation, opacity, and z-index for every placed raster. Use this layer specification both to render the approved preview and to place the asset in Figma. Do not substitute a newly regenerated object during Figma reconstruction.

Record source, ownership, dimensions, crop, alpha status, Figma destination, and quality status. Never describe a placed bitmap as an editable vector.

Record `style_profile_id`, `material_modality`, and `style_match` for every accepted complex asset. The preview and Figma build must use the same validated file.

Record `source_role`, `usage`, and `permission_basis` in `asset-provenance.json`. Validate provenance before preview rendering and again before Figma upload.

## Review triggers

Mark `needs_review` for uncertain ownership, damaged edges, unresolved shadows, missing occluded content, illegible source text, or assets that cannot be cleanly separated.
