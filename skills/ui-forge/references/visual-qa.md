# Visual QA

Compare the built Figma frame against the selected design spec and preview.

## Required checks

- Correct number and order of screens
- Required text present, editable, and legible
- Correct primary action and hierarchy
- Semantic color and typography consistency
- Spacing rhythm, alignment, radii, and elevation
- Raster assets separated and named
- Repeated UI represented as components where practical
- Auto Layout and constraints usable
- No unauthorized proprietary assets
- Every raster has an allowed provenance usage and explicit permission basis
- Target dimensions and language correct
- Selected layer spec and preview lock still valid
- Raster hashes match the locked files
- Layer IDs, bounds, crop, rotation, opacity, and z-order match the approved preview
- Pixel-difference report from `scripts/compare_previews.py` is `pass`, or the build report documents a user-approved intentional deviation

Mark each category `pass`, `revise`, or `intentional_deviation`. Perform no more than two focused correction passes unless the user asks for deeper iteration. Preserve approved decisions during corrections.
