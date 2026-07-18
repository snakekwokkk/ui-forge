#!/usr/bin/env python3
"""Run every fail-closed gate required before presenting UIForge options."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from validate_asset_provenance import validate_provenance
from validate_layer_spec import validate as validate_layer_spec
from validate_raster_alpha import validate_alpha
from validate_wireframe_fidelity import load_json, validate_specs


REQUIRED_OPTIONS = {"A", "B", "C"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_gates(
    content_lock: Path,
    provenance: Path,
    project_root: Path,
    spec_paths: list[Path],
) -> dict:
    options = {str(load_json(path).get("option", "")) for path in spec_paths}
    if options != REQUIRED_OPTIONS:
        raise ValueError(
            f"preview gates require exactly options A, B, and C; found={sorted(options)}"
        )

    validated_specs: list[str] = []
    provenance_specs: list[str] = []
    for spec_path in spec_paths:
        validate_layer_spec(spec_path, project_root)
        validated_specs.append(str(spec_path.resolve()))
        validate_provenance(spec_path, provenance)
        provenance_specs.append(str(spec_path.resolve()))

    fidelity = validate_specs(content_lock, spec_paths)
    transparency = validate_alpha(project_root, provenance, spec_paths)
    raster_hashes = {
        asset["path"]: sha256(Path(asset["path"]))
        for asset in transparency["validated_assets"]
    }
    return {
        "schema_version": 1,
        "status": "pass",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(project_root.resolve()),
        "required_options": sorted(REQUIRED_OPTIONS),
        "wireframe_fidelity": fidelity,
        "raster_transparency": transparency,
        "layer_specs": {
            "status": "pass",
            "validated_specs": validated_specs,
        },
        "asset_provenance": {
            "status": "pass",
            "validated_specs": provenance_specs,
        },
        "hashes": {
            "content_lock": sha256(content_lock),
            "asset_provenance": sha256(provenance),
            "layer_specs": {
                str(path.resolve()): sha256(path)
                for path in spec_paths
            },
            "raster_assets": raster_hashes,
        },
        "errors": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--content-lock", required=True, type=Path)
    parser.add_argument("--asset-provenance", required=True, type=Path)
    parser.add_argument("--layer-spec", required=True, action="append", type=Path)
    parser.add_argument("--project-root", type=Path)
    parser.add_argument("--report-out", required=True, type=Path)
    args = parser.parse_args()

    content_lock = args.content_lock.resolve()
    provenance = args.asset_provenance.resolve()
    spec_paths = [path.resolve() for path in args.layer_spec]
    project_root = (
        args.project_root.resolve()
        if args.project_root
        else content_lock.parent.resolve()
    )
    try:
        report = run_gates(content_lock, provenance, project_root, spec_paths)
    except (ValueError, SystemExit) as exc:
        failure = {
            "schema_version": 1,
            "status": "fail",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "required_options": sorted(REQUIRED_OPTIONS),
            "errors": [str(exc)],
        }
        args.report_out.parent.mkdir(parents=True, exist_ok=True)
        args.report_out.write_text(
            json.dumps(failure, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        raise SystemExit(f"preview gates failed: {exc}") from exc

    args.report_out.parent.mkdir(parents=True, exist_ok=True)
    args.report_out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        "preview gates: pass "
        f"({len(report['layer_specs']['validated_specs'])} option specs)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
