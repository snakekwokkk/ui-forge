#!/usr/bin/env python3
"""Reject reference-only raster assets before preview or Figma composition."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from validate_layer_spec import iter_layers


ALLOWED_USAGE = {"generated_original", "user_authorized_asset", "target_brand_owned_asset"}
REJECTED_USAGE = {"reference_only", "competitor_reference", "website_scrape", "unconfirmed"}
BACKGROUND_POLICIES = {"transparent_required", "embedded_background_authorized"}


def load(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid provenance JSON: {exc}")
    if not isinstance(data, dict):
        raise SystemExit("provenance root must be an object")
    return data


def validate_provenance(spec_path: Path, provenance_path: Path) -> int:
    try:
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid layer spec: {exc}")
    provenance = load(provenance_path)
    records = provenance.get("assets")
    if not isinstance(records, list):
        raise SystemExit("asset provenance must contain an assets array")

    by_id: dict[str, dict] = {}
    for record in records:
        if not isinstance(record, dict) or not record.get("asset_id"):
            raise SystemExit("every provenance record requires asset_id")
        if record["asset_id"] in by_id:
            raise SystemExit(f"duplicate provenance asset_id: {record['asset_id']}")
        background_policy = record.get("background_policy", "transparent_required")
        if background_policy not in BACKGROUND_POLICIES:
            raise SystemExit(
                f"invalid background_policy for {record['asset_id']}: {background_policy}"
            )
        if background_policy == "embedded_background_authorized" and not str(
            record.get("background_authorization", "")
        ).strip():
            raise SystemExit(
                "embedded_background_authorized requires background_authorization: "
                f"{record['asset_id']}"
            )
        by_id[record["asset_id"]] = record

    used = 0
    for layer in iter_layers(spec.get("layers", [])):
        if layer.get("type") != "raster":
            continue
        used += 1
        raster = layer.get("raster", {})
        asset_id = raster.get("asset_id")
        record = by_id.get(asset_id)
        if record is None:
            raise SystemExit(f"missing provenance for raster asset: {asset_id}")
        usage = record.get("usage", "unconfirmed")
        if usage in REJECTED_USAGE or usage not in ALLOWED_USAGE:
            raise SystemExit(f"raster asset is not reusable: {asset_id} (usage={usage})")
        if record.get("path") != raster.get("path"):
            raise SystemExit(f"provenance path mismatch for asset: {asset_id}")
        if not str(record.get("permission_basis", "")).strip():
            raise SystemExit(f"missing permission_basis for asset: {asset_id}")
        if usage == "generated_original" and record.get("source_role") != "generated_in_workflow":
            raise SystemExit(f"generated_original must use source_role=generated_in_workflow: {asset_id}")
    return used


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    parser.add_argument("provenance", type=Path)
    args = parser.parse_args()
    used = validate_provenance(args.spec.resolve(), args.provenance.resolve())
    print(f"valid asset provenance: {args.provenance.resolve()} ({used} raster placements)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
