# Component and chart sourcing

Use a lightweight capability registry plus on-demand official retrieval. Do not vendor complete libraries, download every component, or scan an entire repository merely to discover what exists.

## Retrieval workflow

1. Identify target platform, implementation stack when known, product type, and required semantic controls.
2. Select one primary component foundation for the coherent screen set.
3. Consult the official component index and retrieve only the exact documentation, state examples, token pages, or individual source files required.
4. Record every consulted component and chart pattern in `library-selection-manifest.json`.
5. Map Brand DNA tokens onto the selected structure and behavior.
6. Rebuild local Figma components and variants. Install code dependencies only when executable code is requested.

## Lightweight registry

### React Native and Expo

- **Tamagui** — https://tamagui.dev/ — default when token, theme, responsive, animation, and future web portability matter.
- **gluestack-ui** — https://gluestack.io/ui/docs/home/overview/introduction — use when project-owned, highly editable component source is preferred.
- **React Native Reusables** — https://reactnativereusables.com/ — use for lightweight Expo projects and copy-owned components.

### Mobile web and hybrid apps

- **Ant Design Mobile** — https://mobile.ant.design/ — React business flows and comprehensive mobile controls.
- **TDesign Mobile Vue** — https://tdesign.tencent.com/mobile-vue/ — Vue enterprise and utility products.
- **Vant** — https://vant-ui.github.io/vant/ — mature Vue consumer and transactional products.
- **NutUI** — https://nutui.jd.com/ — commerce, marketing, promotions, and activity flows.
- **Ionic** — https://ionicframework.com/docs/components — cross-platform web and hybrid apps using React, Vue, or Angular.

### Charts

- **Apache ECharts** — https://echarts.apache.org/ — complex finance, analytics, interactions, and dense chart coverage.
- **AntV G2** — https://g2.antv.antgroup.com/ — branded chart grammar and chart design tokens.
- **Recharts** — https://recharts.github.io/ — ordinary React business charts.
- **Nivo** — https://nivo.rocks/ — presentation-led data visualization.
- **visx** — https://airbnb.io/visx/ — highly customized branded React charts.

## Selection rules

- Select by platform compatibility first, semantic capability second, product fit third, and default appearance last.
- Use one primary component foundation. Use a secondary source only for a documented capability gap.
- Never mix visible default skins from multiple libraries.
- Treat a library as the authority for anatomy, interaction, state coverage, accessibility, touch behavior, keyboard behavior, safe areas, and platform conventions.
- Treat Brand DNA as the authority for color, type, radius, spacing, border, shadow, icon treatment, elevation, and permitted motion character.
- Preserve disabled, loading, selected, indeterminate, validation, error, empty, and accessibility states when they apply.
- For checkboxes, tags, pickers, calendars, sheets, tabs, and navigation, inspect all relevant official states rather than copying a single screenshot.

## Figma versus code

During Figma design, do not install the package merely to draw the UI. Recreate the required pattern as a local Figma component with variants, Auto Layout, semantic names, and Brand DNA variable bindings. Record the external library only as structure and behavior provenance.

During code generation, verify stack compatibility and current official documentation, then install only the selected package. Do not claim a component library is implemented when only its design pattern was referenced.

For charts in Figma, rebuild axes, grid, marks, labels, legend, tooltip state, and annotations as editable layers. Do not paste a chart screenshot. For code, choose a library compatible with the target runtime; a web chart library is not automatically a React Native chart implementation.

## Caching policy

Cache only stable metadata useful for selection: component name, semantic roles, supported states, platform, official URL, license basis, and Brand DNA token hooks. Treat exact APIs, versions, and maintenance status as time-sensitive and verify them from official sources when implementation depends on them.
