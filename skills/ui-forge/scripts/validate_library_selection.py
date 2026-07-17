#!/usr/bin/env python3
"""Validate on-demand library selection and provenance."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ICON_LIBRARIES = {"Iconoir", "Phosphor Icons", "Lucide", "Tabler Icons", "Remix Icon"}
COMPONENT_LIBRARIES = {
    "Tamagui", "gluestack-ui", "React Native Reusables", "Ant Design Mobile",
    "TDesign Mobile Vue", "Vant", "NutUI", "Ionic",
}
CHART_LIBRARIES = {"none", "Apache ECharts", "AntV G2", "Recharts", "Nivo", "visx"}


def https(value: object) -> bool:
    return isinstance(value, str) and value.startswith("https://")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    errors: list[str] = []

    policy = data.get("retrieval_policy", {})
    if policy.get("mode") != "registry-plus-on-demand":
        errors.append("retrieval mode must be registry-plus-on-demand")
    if policy.get("bulk_download") is not False:
        errors.append("bulk_download must be false")
    if policy.get("full_repository_scan") is not False:
        errors.append("full_repository_scan must be false")

    icon = data.get("icon_library", {})
    if icon.get("primary") not in ICON_LIBRARIES:
        errors.append(f"unsupported primary icon library: {icon.get('primary')}")
    if not https(icon.get("official_url")):
        errors.append("primary icon library requires an official https URL")

    component = data.get("component_library", {})
    if component.get("primary") not in COMPONENT_LIBRARIES:
        errors.append(f"unsupported primary component library: {component.get('primary')}")
    if not https(component.get("official_url")):
        errors.append("primary component library requires an official https URL")
    if not isinstance(component.get("code_installation_required"), bool):
        errors.append("code_installation_required must be boolean")

    for index, item in enumerate(data.get("components", [])):
        if item.get("library") not in COMPONENT_LIBRARIES:
            errors.append(f"component {index} uses an unsupported library")
        if not https(item.get("docs_url")):
            errors.append(f"component {index} requires an official docs_url")
        if not isinstance(item.get("consulted_states"), list) or not item.get("consulted_states"):
            errors.append(f"component {index} requires consulted_states")
        if not isinstance(item.get("brand_token_mapping"), dict) or not item.get("brand_token_mapping"):
            errors.append(f"component {index} requires brand_token_mapping")

    chart = data.get("chart_library", {})
    primary_chart = chart.get("primary")
    if primary_chart not in CHART_LIBRARIES:
        errors.append(f"unsupported chart library: {primary_chart}")
    if primary_chart != "none" and not https(chart.get("official_url")):
        errors.append("selected chart library requires an official https URL")
    for index, item in enumerate(data.get("charts", [])):
        if item.get("library") not in CHART_LIBRARIES - {"none"}:
            errors.append(f"chart {index} uses an unsupported library")
        if not https(item.get("docs_url")):
            errors.append(f"chart {index} requires an official docs_url")

    if errors:
        raise SystemExit("library selection failed:\n- " + "\n- ".join(errors))
    print("valid library selection: registry-plus-on-demand")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
