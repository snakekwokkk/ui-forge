# Visual Review

Use this workflow after every successful Figma write. Figma remains the only editable design source. Visual Review is a screenshot-based review layer, not an HTML recreation.

## Required outputs

Create:

```text
visual-review/
├── index.html
├── manifest.json
└── screens/
    ├── home.png
    ├── credit-score.png
    └── ...
```

Start from `assets/visual-review-manifest-template.json` when a manifest does not exist.

## Screen discovery

Scan the selected direction's managed Figma page or Section. Include top-level mobile screen Frames; exclude Brand DNA, asset libraries, detached experiments, hidden backups, and reference screenshots unless the user explicitly requests them.

For every screen record:

- stable `screen_key`, independent of display-name changes;
- display `name` and optional `group`;
- `figma_node_id` and file key;
- natural width and height;
- screenshot path;
- `fingerprint` of relevant node structure and properties;
- status: `new`, `changed`, `unchanged`, or `archived`;
- descendant node index with node ID, semantic name, type, and normalized bounds.

Use normalized bounds `[x / screenWidth, y / screenHeight, width / screenWidth, height / screenHeight]` so annotations remain interpretable at different rendered sizes.

## Incremental refresh

Compare the new scan with the previous manifest.

- Export screenshots for `new` and `changed` screens.
- Reuse the existing PNG for `unchanged` screens.
- Keep deleted screens only as archived history; omit them from the default gallery.
- Always regenerate `index.html` with every current screen.
- Preserve unresolved annotation references and the reviewed revision identifier.

Do not use screen count as a reason to omit pages. Four existing plus ten new screens means fourteen current gallery entries.

## Annotation resolution

Treat the user annotation as a tuple:

```text
screen_key + screen_node_id + marked_bounds + feedback_text
```

Find descendant nodes overlapping the marked bounds. Prefer a node whose bounds closely match the annotation, whose semantic name matches the feedback, and whose type is editable for the requested change. Prefer a button over its whole screen when the user marks the button, but prefer the containing card when the wording refers to the complete card.

Ask one clarification when multiple sibling nodes are equally plausible or when the requested change has broad layout consequences. Otherwise apply a targeted Figma patch, rerun QA for affected screens, refresh their screenshots, and regenerate the complete gallery.

## HTML constraints

- Display screenshots at their natural aspect ratio.
- Provide grouping, page count, and status badges. Do not add page search unless the user explicitly requests it.
- Expose the screen name and Figma node ID for traceability.
- Render every screen as its own stable screenshot element keyed by `screen_key`. Never reuse one image element by swapping `src`; annotation bubbles must remain isolated to the screen where the user created them.
- Hide inactive screenshot elements instead of replacing or destroying them. Switching screens must never reveal annotation bubbles created on another screen.
- Do not create editable DOM replicas, draggable UI, color controls, or text editors.
- Do not embed reference-only images that were prohibited from Figma.
