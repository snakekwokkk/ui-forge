#!/usr/bin/env python3
"""Validate a UIForge Visual Review as an exact official-generator output."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image

from generate_visual_review import GENERATOR_ID, GENERATOR_VERSION, load_manifest, render


def validate_visual_review(manifest_path: Path, html_path: Path | None = None) -> list[str]:
    manifest_path = manifest_path.resolve()
    html_path = (html_path or manifest_path.parent / "index.html").resolve()
    errors: list[str] = []

    try:
        manifest = load_manifest(manifest_path)
    except (OSError, ValueError) as exc:
        return [f"invalid manifest: {exc}"]

    if not html_path.exists():
        errors.append(f"Visual Review HTML missing: {html_path}")
    else:
        actual = html_path.read_text(encoding="utf-8")
        expected = render(manifest)
        if actual != expected:
            errors.append(
                "Visual Review HTML does not exactly match the bundled UIForge generator; "
                "regenerate it instead of editing or replacing the template"
            )

    active = [screen for screen in manifest["screens"] if screen.get("status") != "archived"]
    for screen in active:
        key = str(screen.get("screen_key", "<unknown>"))
        status = screen.get("status", "unchanged")
        if status not in {"new", "changed", "unchanged"}:
            errors.append(f"screen {key} has invalid active status: {status}")

        width = screen.get("width")
        height = screen.get("height")
        if not isinstance(width, int) or width <= 0 or not isinstance(height, int) or height <= 0:
            errors.append(f"screen {key} requires positive integer natural dimensions")
            continue

        screenshot_rel = screen.get("screenshot")
        screenshot_path = (manifest_path.parent / str(screenshot_rel)).resolve()
        try:
            screenshot_path.relative_to(manifest_path.parent)
        except ValueError:
            errors.append(f"screen {key} screenshot must stay inside the Visual Review directory")
            continue
        if not screenshot_path.exists():
            errors.append(f"screen {key} screenshot missing: {screenshot_path}")
            continue
        try:
            with Image.open(screenshot_path) as image:
                actual_size = image.size
        except OSError as exc:
            errors.append(f"screen {key} screenshot is unreadable: {exc}")
            continue
        if actual_size != (width, height):
            errors.append(
                f"screen {key} screenshot size {actual_size[0]}x{actual_size[1]} "
                f"does not match natural size {width}x{height}"
            )

    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--html", type=Path)
    args = parser.parse_args()
    errors = validate_visual_review(args.manifest, args.html)
    if errors:
        raise SystemExit("Visual Review validation failed:\n- " + "\n- ".join(errors))

    manifest = load_manifest(args.manifest.resolve())
    active = [screen for screen in manifest["screens"] if screen.get("status") != "archived"]
    print(
        "Visual Review pass: "
        f"{len(active)} screens; official generator {GENERATOR_ID}@{GENERATOR_VERSION}; "
        "HTML exact; screenshot dimensions exact"
    )


if __name__ == "__main__":
    main()
