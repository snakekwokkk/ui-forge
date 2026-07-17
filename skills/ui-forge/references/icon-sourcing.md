# Open-source icon sourcing

Use official vector icons for navigation, functional shortcuts, status, and actions. Never draw a substitute, trace a screenshot, generate a lookalike, or replace an icon with emoji, Unicode, initials, or label-only navigation.

## Approved libraries

1. **Iconoir** — https://iconoir.com/
   - Primary choice for refined, lightweight line icons in modern tools, finance, and international products.
   - Official repository: https://github.com/iconoir-icons/iconoir
2. **Phosphor Icons** — https://phosphoricons.com/
   - Primary choice when Thin, Regular, Bold, Fill, or Duotone variants and state transitions are required.
   - Official repository: https://github.com/phosphor-icons/core
3. **Lucide** — https://lucide.dev/
   - Stable general-purpose fallback with consistent geometry and adjustable stroke width.
   - Official repository: https://github.com/lucide-icons/lucide
4. **Tabler Icons** — https://tabler.io/icons
   - Broad business coverage for B2B, finance, operations, and tool products.
   - Official repository: https://github.com/tabler/tabler-icons
5. **Remix Icon** — https://remixicon.com/
   - Preferred for domestic internet products and paired line/fill navigation states.
   - Official repository: https://github.com/Remix-Design/RemixIcon

Use `Iconoir -> Phosphor -> Lucide` for general discovery. Override that order by need: use `Phosphor -> Remix Icon` for matched outline/fill states; use `Tabler -> Lucide` for broad B2B coverage. Do not use Iconly as a default source because its free catalog is not an open-source library. Preserve legacy IconPark or Iconly records only when revising an existing approved project; do not introduce new usage.

## On-demand retrieval

- Search the approved catalog by semantic role.
- Fetch only the exact official SVG files required by the current screen set.
- Do not download a complete icon pack or crawl the whole repository.
- Preserve the source SVG unchanged. Theme color, size, and placement in Figma without modifying the path to imitate another family.
- If the primary family lacks a required semantic icon, document the capability gap before using one secondary library.

## Consistency and navigation

- Use one primary library per coherent screen set.
- Keep grid, optical size, corner style, stroke width, cap, and join consistent.
- Do not mix line, filled, and duotone icons randomly.
- A selected tab should use the matching filled or heavier official variant when the family provides one; the unselected tab should use the corresponding outline variant.
- When a family has no official fill variant, use a container, indicator, weight, or color treatment instead of inventing one.
- Keep the same semantic identity across selected and unselected states.
- Use 24 px icons by default and preserve approximately 44 pt iOS or 48 dp Android tap targets.
- Primary tab bars normally require both icons and short labels.

## Manifest and Figma delivery

For every icon, record stable ID, semantic role, screen, library, official name, variant, exact source URL, license and license URL, SVG path, preview derivative, size, state color, target layers, and permission basis in `icon-manifest.json`.

The layer specification must reference the same `icon_id`, `svg_path`, and `preview_path`. Figma must import the locked SVG as an editable vector with a semantic name such as `Navigation / Home / Selected`. Run `scripts/validate_icon_manifest.py` before preview rendering and before Figma delivery.
