#!/usr/bin/env python3
"""Compare an approved deterministic preview with a Figma frame screenshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageEnhance, ImageStat


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("approved_preview", type=Path)
    parser.add_argument("figma_screenshot", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--diff", type=Path, required=True)
    parser.add_argument("--mae-threshold", type=float, default=8.0)
    parser.add_argument("--changed-threshold", type=float, default=12.0)
    parser.add_argument("--pixel-threshold", type=int, default=24)
    args = parser.parse_args()

    approved = Image.open(args.approved_preview).convert("RGB")
    figma = Image.open(args.figma_screenshot).convert("RGB")
    if approved.size != figma.size:
        approved_ratio = approved.width / approved.height
        figma_ratio = figma.width / figma.height
        if abs(approved_ratio - figma_ratio) > 0.002:
            raise SystemExit(f"aspect ratio mismatch: preview={approved.size}, figma={figma.size}")
        figma = figma.resize(approved.size, Image.Resampling.LANCZOS)

    diff = ImageChops.difference(approved, figma)
    stat = ImageStat.Stat(diff)
    channel_mae = stat.mean
    mae = sum(channel_mae) / 3
    max_error = max(channel[1] for channel in diff.getextrema())
    grayscale = diff.convert("L")
    changed = sum(1 for value in grayscale.getdata() if value > args.pixel_threshold)
    changed_percent = changed * 100 / (approved.width * approved.height)
    status = "pass" if mae <= args.mae_threshold and changed_percent <= args.changed_threshold else "revise"

    args.diff.parent.mkdir(parents=True, exist_ok=True)
    ImageEnhance.Contrast(diff).enhance(3).save(args.diff, "PNG")
    report = {
        "schema_version": 1,
        "status": status,
        "approved_preview": str(args.approved_preview.resolve()),
        "figma_screenshot": str(args.figma_screenshot.resolve()),
        "compared_size": {"width": approved.width, "height": approved.height},
        "metrics": {
            "mean_absolute_error": round(mae, 4),
            "channel_mae": [round(value, 4) for value in channel_mae],
            "max_channel_error": max_error,
            "changed_pixel_percent": round(changed_percent, 4),
            "pixel_change_threshold": args.pixel_threshold
        },
        "acceptance": {
            "max_mean_absolute_error": args.mae_threshold,
            "max_changed_pixel_percent": args.changed_threshold
        },
        "diff_image": str(args.diff.resolve())
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"preview comparison: {status} (MAE={mae:.4f}, changed={changed_percent:.4f}%)")
    print(f"wrote report: {args.report}")
    return 0 if status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
