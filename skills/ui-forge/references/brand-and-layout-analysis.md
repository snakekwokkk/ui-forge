# Brand and layout analysis

Analyze brand behavior and wireframe structure concurrently.

## Brand evidence priority

1. User-supplied official guidelines and tokens
2. Official source CSS, fonts, and assets
3. Repeated patterns across official product views
4. A single official screenshot
5. Third-party reference or descriptive text

Label conclusions as `observed`, `inferred`, `proposed`, or `user_directive`, with `high`, `medium`, or `low` confidence.

Capture semantic colors, type style and fallback, spacing scale, grids, component density, radii, borders, shadows, surfaces, photography, illustration, 3D, icons, motion evidence, traits, usage rules, and exclusions. Also capture component anatomy: whether titles and body copy pair with icons, people, product imagery, 3D objects, textures, or composite scenes; where that media sits; and how much visual weight it carries. Do not claim an exact font from appearance alone.

## Wireframe authority

Preserve screen count, order, hierarchy, primary actions, required content, and repeated components. Ignore accidental sketch imprecision and placeholder styling. Identify missing copy, media roles, responsive assumptions, and product decisions that cannot be inferred safely.

Do not let a reference screenshot silently replace the user's wireframe structure.

Create `wireframe-content-lock.json` from the bundled template before option planning. Transcribe every user-visible string, number, label, and action in the original language. Default to exact copy with Unicode normalization and whitespace-only layout normalization. Do not translate, rewrite, shorten, expand, omit, or add product copy unless the user explicitly authorizes the change and the lock records that authorization.

Assign stable `content_id` values to locked text and stable `structure_id` values to required modules. Lock each required module's nearest required parent and sibling order. The three options may add reference-supported visual layers and decorative, non-content structure inside locked modules, but they must preserve the locked modules and their relative hierarchy. Adding an icon, original complex visual region, person, 3D object, or illustration to complete an observed component anatomy is visual enrichment, not a wireframe violation, provided it adds no product copy, action, or module.
