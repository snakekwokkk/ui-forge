#!/usr/bin/env python3
"""Validate UIForge JSON artifacts for basic structural integrity."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


EXPECTED = {
    "project-state": {
        "status",
        "inputs",
        "options",
        "primary_selected_option",
        "primary_selection_confirmed",
        "additional_option_queue",
        "asset_manifest",
        "candidate_asset_minimum",
        "candidate_asset_target_range",
        "qa",
    },
    "design-spec": {"option", "label", "intent", "canvas", "screens", "tokens", "components", "assets", "constraints"},
    "asset-manifest": {"status", "assets", "minimum_candidate_assets", "target_candidate_range"},
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    parser.add_argument("--kind", choices=EXPECTED, required=True)
    args = parser.parse_args()

    try:
        data = json.loads(args.path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid JSON artifact: {exc}")

    if not isinstance(data, dict):
        raise SystemExit("artifact root must be a JSON object")

    missing = sorted(EXPECTED[args.kind] - data.keys())
    if missing:
        raise SystemExit(f"missing required keys: {', '.join(missing)}")

    if args.kind == "asset-manifest" and not isinstance(data["assets"], list):
        raise SystemExit("assets must be an array")
    if args.kind == "asset-manifest":
        minimum = data["minimum_candidate_assets"]
        target = data["target_candidate_range"]
        if not isinstance(minimum, int) or minimum < 12:
            raise SystemExit("minimum_candidate_assets must be an integer >= 12")
        if not (
            isinstance(target, list)
            and len(target) == 2
            and all(isinstance(value, int) for value in target)
            and target[0] >= minimum
            and target[1] >= target[0]
        ):
            raise SystemExit("target_candidate_range must be [min, max] and start at or above the minimum")
        if data["status"] in {"ready_for_extension", "complete"} and len(data["assets"]) < minimum:
            raise SystemExit(f"asset catalog requires at least {minimum} assets before extension")
    if args.kind == "design-spec" and not isinstance(data["screens"], list):
        raise SystemExit("screens must be an array")

    print(f"valid {args.kind}: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
