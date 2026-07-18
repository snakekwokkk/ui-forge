# Reference media relationships

Analyze how reference screens pair product content with visual media. Do not treat imagery as a loose moodboard attribute, and do not assume that a text-only wireframe means the finished module should remain text-only.

## Separate authorities

- The wireframe controls required copy, product meaning, modules, order, and actions.
- The references provide evidence for component anatomy, media type, media position, and visual share.
- Reference-derived enrichment may add icons, original imagery, texture, or decoration inside an existing locked module. It may not add product claims, actions, modules, or replacement copy.

## Extract the relationship

For every repeated or prominent pattern, record:

- pairing: icon-title-body, image-title, person-copy, 3D-object-number, composite-image-with-native-overlay, or no-media;
- asset type: vector icon, isolated raster, composite raster, surface texture, full-bleed background, or native visual;
- position: leading, trailing, top, background-fill, foreground overlap, or full-bleed;
- visual share: accent, supporting, balanced, or dominant;
- recurrence, evidence, and confidence.

Map each pattern to an existing wireframe `structure_id`. Mark media as `required`, `optional`, or `none`. Each A/B/C decision may apply or omit the pattern. An omission requires a design rationale, and a required high-value relationship must appear in at least one option.

The gate checks whether the analysis and decisions exist; it does not ban text-and-color-block directions. A restrained option is valid when its omission is deliberate and documented.

## Choose native or generated media

Use native editable layers for text, layout, simple surfaces, basic gradients, controls, and uncomplicated geometry. Use editable vector icons for semantic navigation and actions.

Generate an original raster when the reference relies on visual content that would be materially degraded or become generic if approximated with primitives:

- photography or people;
- 3D objects;
- painterly or collaged surfaces;
- complex card artwork;
- textured illustration;
- multi-element scenes;
- atmospheric light, particles, or integrated effects.

Do not generate a full UI screenshot. Generate only the complex visual region, then compose native copy, controls, and layout around or above it.

## Raster roles

- `isolated_object` + `transparent_required`: reusable people, objects, cutouts, 3D props, and foreground illustrations. Require real alpha and clear outer borders.
- `composite_scene` + `opaque_composite_expected`: an original integrated scene whose background and subjects are inseparable.
- `surface_texture` + `opaque_composite_expected`: complex card face, painterly panel, or material surface clipped inside an editable component.
- `full_bleed_background` + `opaque_composite_expected`: an original image intended to fill a hero or screen region.
- `embedded_background_authorized`: an exact user-authorized target-brand asset whose embedded background is intentionally retained.

Generated composite images do not require alpha. They require a target `structure_id`, a composition purpose, a defined placement/crop, and native editable overlay text.

## Banking-card example

When a reference shows a bank card with complex painted artwork, rebuild the card Frame, radius, shadow, carousel, labels, numbers, and controls as native layers. Generate an original card-surface image and clip it inside the card Frame. Do not recreate a distinctive third-party card design or bake dynamic product copy into the image.
