# Three-option generation

Create meaningful directions, not recolors.

## A — Product Clear

Prioritize scanning, accessibility, information density, and platform conventions. Use brand color selectively and keep complex imagery limited.

## B — Brand Balanced

Balance usability and recognizable brand expression. Use branded hero areas and strategic imagery while keeping functional regions clean. Recommend this option by default unless evidence favors another.

## C — Campaign Bold

Maximize promotional energy through composition, depth, imagery, contrast, and branded surfaces. Preserve usability and required copy; do not turn functional screens into posters.

## Comparison rules

Keep identical content and information architecture unless the user authorizes structural exploration. Vary art direction, hierarchy emphasis, surface treatment, media scale, density, and motion implications. Label every preview clearly.

Treat `wireframe-content-lock.json` as immutable input to all three options. Every required text layer must carry its locked `content_id`; every required structural Frame must carry its locked `structure_id`. Visual emphasis may change, but language, wording, numbers, labels, actions, parent relationships, and required-module order may not.

Treat `reference-media-plan.json` as the bridge between sparse wireframes and visually complete product UI. Analyze reference text-media pairing, component anatomy, asset type, position, and visual share before deciding whether an option is text-led or media-led. Each option may apply or deliberately omit a mapped pattern, but omissions require rationale and a required relationship must appear in at least one option.

For quick comparison, use the screen with the richest combination of brand, hierarchy, CTA, and media. Default to three home-screen previews only. Extend every screen for one direction only after the user selects it as primary. Generate three complete sets only when the user explicitly overrides the staged workflow.

Reference images contribute abstract design DNA only. Do not insert, crop, trace, or closely reproduce their visual assets. Generate original imagery with different subjects and compositions whenever a direction needs photography, 3D, illustration, or device imagery, unless the user explicitly authorized exact target-brand asset reuse.

## Preview source-of-truth rule

Do not ask an image model to invent a complete final UI screenshot and later reverse-engineer it. First define the native UI layers, complex asset list, exact bounds, and z-order. Generate complex assets separately, then compose the preview from those same assets and the same layer specification intended for Figma. The approved preview and Figma build must share asset identities and geometry.

Before presenting the options, run `scripts/validate_preview_gates.py` for A, B, and C. A copy mismatch, missing or reordered required module, unlocked text, unanalyzed reference-media relationship, unexplained media omission, role-mismatched raster, opaque isolated object, missing provenance, or invalid layer spec blocks the option-selection gate.
