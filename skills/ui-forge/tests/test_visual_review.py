#!/usr/bin/env python3
"""Regression tests for fail-closed UIForge Visual Review delivery."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from generate_visual_review import render  # noqa: E402
from validate_visual_review import validate_visual_review  # noqa: E402


class VisualReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "screens").mkdir()
        Image.new("RGB", (390, 844), "white").save(self.root / "screens" / "home.png")
        self.manifest = {
            "schema_version": 1,
            "figma_file_key": "test-file",
            "figma_file_url": "https://www.figma.com/design/test-file/Test",
            "generated_at": "2026-07-19T00:00:00Z",
            "review_revision": "test-revision",
            "screens": [
                {
                    "screen_key": "home",
                    "name": "Home",
                    "group": "Direction B",
                    "figma_node_id": "1:2",
                    "width": 390,
                    "height": 844,
                    "screenshot": "screens/home.png",
                    "fingerprint": "test",
                    "status": "new",
                    "nodes": [],
                }
            ],
        }
        self.manifest_path = self.root / "manifest.json"
        self.html_path = self.root / "index.html"
        self.write_outputs()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_outputs(self) -> None:
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        self.html_path.write_text(render(self.manifest), encoding="utf-8")

    def test_official_output_passes(self) -> None:
        self.assertEqual(validate_visual_review(self.manifest_path), [])

    def test_hand_edited_template_fails(self) -> None:
        self.html_path.write_text(
            self.html_path.read_text(encoding="utf-8").replace(
                "<title>UIForge Visual Review</title>",
                "<title>Custom Visual Review</title>",
            ),
            encoding="utf-8",
        )
        errors = validate_visual_review(self.manifest_path)
        self.assertTrue(any("does not exactly match" in error for error in errors))

    def test_non_natural_screenshot_size_fails(self) -> None:
        Image.new("RGB", (780, 1688), "white").save(self.root / "screens" / "home.png")
        errors = validate_visual_review(self.manifest_path)
        self.assertTrue(any("does not match natural size 390x844" in error for error in errors))

    def test_manifest_change_requires_regeneration(self) -> None:
        self.manifest["screens"][0]["name"] = "Inicio"
        self.manifest_path.write_text(json.dumps(self.manifest), encoding="utf-8")
        errors = validate_visual_review(self.manifest_path)
        self.assertTrue(any("does not exactly match" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
