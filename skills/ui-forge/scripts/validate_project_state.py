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
        "preview_gates",
        "preview_gate_report",
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
    if args.kind == "project-state":
        preview_gates = data["preview_gates"]
        required_preview_gates = {
            "wireframe_fidelity",
            "reference_media_relationships",
            "raster_transparency",
            "layer_specs",
            "asset_provenance",
        }
        if not isinstance(preview_gates, dict):
            raise SystemExit("preview_gates must be an object")
        missing_preview_gates = required_preview_gates - set(preview_gates)
        if missing_preview_gates:
            raise SystemExit(
                "preview_gates missing: " + ", ".join(sorted(missing_preview_gates))
            )
        awaiting_selection = data["status"] in {
            "AWAITING_PRIMARY_OPTION_SELECTION",
            "awaiting_primary_option_selection",
        }
        if awaiting_selection:
            if any(
                preview_gates[key] != "pass" for key in required_preview_gates
            ):
                raise SystemExit(
                    "cannot enter AWAITING_PRIMARY_OPTION_SELECTION "
                    "until every preview gate is pass"
                )
            report_value = data["preview_gate_report"]
            if not isinstance(report_value, str) or not report_value.strip():
                raise SystemExit(
                    "AWAITING_PRIMARY_OPTION_SELECTION requires preview_gate_report"
                )
            report_path = (args.path.resolve().parent / report_value).resolve()
            try:
                report = json.loads(report_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise SystemExit(f"invalid preview gate report: {exc}")
            if report.get("schema_version") != 1:
                raise SystemExit("preview gate report schema_version must be 1")
            if report.get("status") != "pass":
                raise SystemExit("preview gate report status must be pass")
            if set(report.get("required_options", [])) != {"A", "B", "C"}:
                raise SystemExit("preview gate report must cover options A, B, and C")
            report_sections = {
                "wireframe_fidelity",
                "reference_media_relationships",
                "raster_transparency",
                "layer_specs",
                "asset_provenance",
            }
            for section in report_sections:
                if report.get(section, {}).get("status") != "pass":
                    raise SystemExit(
                        f"preview gate report section must pass: {section}"
                    )
            try:
                project_root = Path(report["project_root"]).resolve()
                content_lock = Path(
                    report["wireframe_fidelity"]["content_lock"]
                ).resolve()
                media_plan = Path(
                    report["reference_media_relationships"]["media_plan"]
                ).resolve()
                provenance = Path(
                    report["raster_transparency"]["asset_provenance"]
                ).resolve()
                spec_paths = [
                    Path(value).resolve()
                    for value in report["layer_specs"]["validated_specs"]
                ]
                from validate_preview_gates import run_gates

                recomputed = run_gates(
                    content_lock,
                    media_plan,
                    provenance,
                    project_root,
                    spec_paths,
                )
            except (KeyError, TypeError, ValueError, SystemExit) as exc:
                raise SystemExit(
                    f"preview gate report cannot be revalidated: {exc}"
                ) from exc
            if report.get("hashes") != recomputed.get("hashes"):
                raise SystemExit(
                    "preview gate report is stale or fabricated; "
                    "rerun validate_preview_gates.py"
                )

    print(f"valid {args.kind}: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
