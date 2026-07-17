# Platform guidance

Treat mobile app design as the default and preserve future web portability.

## Mobile default

Identify iOS, Android, or cross-platform intent from the wireframe, annotations, device proportions, navigation, and user instructions. When unspecified, use a neutral modern mobile canvas and avoid inventing platform-exclusive controls.

Account for safe areas, status and home indicators, touch targets, keyboard behavior, scrolling boundaries, bottom navigation, sheets, and native accessibility expectations. Keep primary touch targets at least approximately 44 points on iOS or 48 density-independent pixels on Android when scale permits.

Use semantic component and token names rather than device-specific names. Build repeated navigation, cards, buttons, fields, lists, and sheets as reusable components with variants.

## Future web expansion

Do not generate desktop layouts unless requested. Still keep tokens, content hierarchy, components, and asset manifests platform-neutral enough to extend later.

When the user requests web expansion, preserve approved Brand DNA and component semantics, then define responsive containers, breakpoint behavior, desktop navigation, pointer states, focus states, and wider information density as a separate design direction. Do not merely stretch mobile screens.
