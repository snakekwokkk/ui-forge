# Material-style detection and matching

Detect what kind of visual material the references use, then generate original assets in the closest appropriate material language. Match the system, not the copyrighted content.

## Detect the system

Classify each relevant reference and determine a dominant modality plus any credible secondary modalities:

- `photography`
- `photoreal-composite`
- `3d-render`
- `clay-3d`
- `flat-vector`
- `flat-cartoon`
- `editorial-illustration`
- `hand-drawn`
- `collage`
- `pixel-art`
- `mixed-media`
- `minimal-native-ui`

Record evidence and confidence. Analyze rendering realism, dimensionality, contour and line behavior, proportions, palette, lighting, shadows, texture, camera or illustration perspective, cropping, background treatment, character language, prop language, composition density, text-media pairing, media position, and visual share.

When references conflict, weight repeated target-brand product UI above isolated campaign images or competitor references. Ask one compact clarification only when the conflict would materially change every generated asset; otherwise follow the strongest repeated evidence and document the decision.

## Generate a corresponding original system

- Photography reference -> generate original photography or photographic cutouts with comparable lighting, framing, palette, and commercial tone.
- 3D reference -> generate original 3D objects with comparable material finish, lighting, depth, and camera angle.
- Cartoon or vector reference -> generate original characters and objects with comparable proportions, line behavior, palette, shading, and expressiveness.
- Hand-drawn reference -> preserve the drawing medium, stroke character, texture, and looseness.
- Clay reference -> preserve soft volume, tactile material, rounded forms, and studio lighting.
- Collage reference -> preserve layering, paper or photographic cutout logic, and intentional edge treatment.
- Mixed-media reference -> assign a documented modality to each semantic role instead of mixing media randomly.

Generate subjects from wireframe content and product meaning. Select domain-relevant people, objects, environments, and scenes without importing a concrete example from the conversation into the reusable rules. Do not reuse the reference's specific person, character, vehicle design, building, device, logo, mascot, prop arrangement, pose, scene, or distinctive composition.

Do not interpret a wireframe's missing pictures as evidence that media is unwanted. Use repeated reference component anatomy to decide whether an existing module needs a semantic icon, isolated object, original composite scene, or surface texture. Preserve text-only treatments when the reference evidence or a documented option decision supports them.

## Consistency

For recurring people or characters, establish a compact identity sheet before variants: age range or character proportions, silhouette, wardrobe or shape language, palette, facial or expression language, and rendering rules. Reuse that identity specification across poses and pages without copying a reference individual.

For a selected direction, ensure every accepted complex candidate declares its modality and the profile it matches. Allow a secondary modality only when it is listed in the profile and has a clear semantic role.

## QA

Evaluate medium, finish, lighting, palette, contour, dimensionality, composition, and subject suitability. Reject an asset when it is attractive but belongs to the wrong medium, looks like a generic stock style unrelated to the references, or resembles a reference asset too closely.

Run `scripts/validate_material_style.py` before option preview generation and again with `--asset-manifest --selected` before screen extension and Figma upload.
