#!/usr/bin/env python3
"""Regression tests for fail-closed UIForge preview gates."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from validate_preview_gates import run_gates  # noqa: E402
from validate_raster_alpha import validate_alpha  # noqa: E402
from validate_wireframe_fidelity import validate_specs  # noqa: E402


def auto_layout(mode: str) -> dict:
    return {
        "mode": mode,
        "primary_axis_sizing": "FIXED",
        "counter_axis_sizing": "FIXED",
        "primary_axis_align": "MIN",
        "counter_axis_align": "MIN",
        "item_spacing": 8,
        "padding": {"top": 0, "right": 0, "bottom": 0, "left": 0},
        "wrap": "NO_WRAP",
        "clips_content": False,
    }


def leaf(layer_id: str) -> dict:
    return {
        "id": layer_id,
        "name": layer_id,
        "type": "rectangle",
        "z_index": 10,
        "bounds": {"x": 0, "y": 0, "width": 8, "height": 8},
        "sizing": {"horizontal": "FIXED", "vertical": "FIXED"},
        "layout_positioning": "AUTO",
        "style": {"fill": "#000000"},
    }


def layer_spec(option: str, text_value: str, asset_path: str, reverse: bool = False) -> dict:
    hero = {
        "id": f"{option}-hero",
        "name": "Home / Hero",
        "type": "frame",
        "structural_role": "section",
        "structure_id": "home.hero",
        "z_index": 10 if not reverse else 20,
        "bounds": {"x": 0, "y": 0, "width": 390, "height": 300},
        "sizing": {"horizontal": "FILL", "vertical": "FIXED"},
        "layout_positioning": "AUTO",
        "layout": auto_layout("VERTICAL"),
        "children": [
            {
                "id": f"{option}-title",
                "name": "Home / Hero / Title",
                "type": "text",
                "content_id": "home.hero.title",
                "z_index": 10,
                "bounds": {"x": 16, "y": 16, "width": 320, "height": 40},
                "sizing": {"horizontal": "FILL", "vertical": "FIXED"},
                "layout_positioning": "AUTO",
                "text": {
                    "content": text_value,
                    "font_family": "Arial",
                    "font_style": "Bold",
                    "font_size": 24,
                    "line_height": 30,
                    "align": "left",
                    "color": "#111111",
                },
            },
            {
                "id": f"{option}-asset",
                "name": "Home / Hero / Asset",
                "type": "raster",
                "z_index": 20,
                "bounds": {"x": 100, "y": 80, "width": 120, "height": 120},
                "sizing": {"horizontal": "FIXED", "vertical": "FIXED"},
                "layout_positioning": "AUTO",
                "raster": {
                    "asset_id": "hero-asset",
                    "path": asset_path,
                    "fit": "contain",
                },
            },
        ],
    }
    navigation = {
        "id": f"{option}-navigation",
        "name": "Home / Navigation",
        "type": "frame",
        "structural_role": "navigation",
        "structure_id": "home.bottom-navigation",
        "z_index": 20 if not reverse else 10,
        "bounds": {"x": 0, "y": 760, "width": 390, "height": 84},
        "sizing": {"horizontal": "FILL", "vertical": "FIXED"},
        "layout_positioning": "AUTO",
        "layout": auto_layout("HORIZONTAL"),
        "children": [leaf(f"{option}-nav-leaf")],
    }
    layers = [hero, navigation] if not reverse else [navigation, hero]
    return {
        "schema_version": 2,
        "option": option,
        "screen_id": "home",
        "canvas": {
            "width": 390,
            "height": 844,
            "background": "#FFFFFF",
            "layout": auto_layout("VERTICAL"),
        },
        "layers": layers,
    }


class PreviewGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "assets").mkdir()
        self.alpha_path = self.root / "assets" / "hero.png"
        alpha = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        ImageDraw.Draw(alpha).ellipse((20, 20, 80, 80), fill=(20, 90, 230, 255))
        alpha.save(self.alpha_path)
        self.opaque_path = self.root / "assets" / "opaque.png"
        Image.new("RGB", (100, 100), (255, 255, 255)).save(self.opaque_path)
        self.padded_opaque_path = self.root / "assets" / "padded-opaque.png"
        padded = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        ImageDraw.Draw(padded).rectangle(
            (8, 8, 92, 92),
            fill=(245, 247, 252, 255),
        )
        padded.save(self.padded_opaque_path)

        self.lock_path = self.root / "wireframe-content-lock.json"
        self.lock_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "source_id": "wireframe",
                    "copy_policy": {
                        "mode": "exact",
                        "normalization": "unicode-nfc-collapse-whitespace",
                        "allow_unlocked_text": False,
                        "authorization_basis": "",
                    },
                    "screens": [
                        {
                            "screen_id": "home",
                            "screen_order": 0,
                            "structure": [
                                {
                                    "structure_id": "home.hero",
                                    "parent_structure_id": None,
                                    "order": 0,
                                    "required": True,
                                },
                                {
                                    "structure_id": "home.bottom-navigation",
                                    "parent_structure_id": None,
                                    "order": 1,
                                    "required": True,
                                },
                            ],
                            "copy": [
                                {
                                    "content_id": "home.hero.title",
                                    "expected_text": "预计最高可借",
                                    "parent_structure_id": "home.hero",
                                    "order": 0,
                                    "required": True,
                                    "source": "wireframe",
                                }
                            ],
                        }
                    ],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        self.provenance_path = self.root / "asset-provenance.json"
        self.write_provenance("assets/hero.png", "transparent_required")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_provenance(
        self,
        asset_path: str,
        policy: str,
        authorization: str = "",
    ) -> None:
        self.provenance_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "assets": [
                        {
                            "asset_id": "hero-asset",
                            "path": asset_path,
                            "source_role": "generated_in_workflow",
                            "usage": "generated_original",
                            "permission_basis": "test fixture",
                            "background_policy": policy,
                            "background_authorization": authorization,
                            "reference_inputs": [],
                            "notes": "",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    def write_specs(
        self,
        changed_option: str | None = None,
        changed_text: str = "翻译后的内容",
        reverse_option: str | None = None,
        asset_path: str = "assets/hero.png",
    ) -> list[Path]:
        paths: list[Path] = []
        for option in ("A", "B", "C"):
            path = self.root / f"option-{option.lower()}.layers.json"
            path.write_text(
                json.dumps(
                    layer_spec(
                        option,
                        changed_text if option == changed_option else "预计最高可借",
                        asset_path,
                        reverse=option == reverse_option,
                    ),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            paths.append(path)
        return paths

    def write_awaiting_state(self, gate_status: str) -> Path:
        state_path = self.root / "project-state.json"
        state_path.write_text(
            json.dumps(
                {
                    "status": "AWAITING_PRIMARY_OPTION_SELECTION",
                    "inputs": [],
                    "options": {"a": {}, "b": {}, "c": {}},
                    "primary_selected_option": None,
                    "primary_selection_confirmed": False,
                    "additional_option_queue": [],
                    "asset_manifest": [],
                    "candidate_asset_minimum": 12,
                    "candidate_asset_target_range": [12, 18],
                    "preview_gates": {
                        "wireframe_fidelity": gate_status,
                        "raster_transparency": gate_status,
                        "layer_specs": gate_status,
                        "asset_provenance": gate_status,
                    },
                    "preview_gate_report": "preview-gates.json",
                    "qa": [],
                }
            ),
            encoding="utf-8",
        )
        return state_path

    def test_all_preview_gates_pass(self) -> None:
        report = run_gates(
            self.lock_path,
            self.provenance_path,
            self.root,
            self.write_specs(),
        )
        self.assertEqual(report["status"], "pass")
        self.assertEqual(report["wireframe_fidelity"]["copy_checks"], 3)
        self.assertEqual(
            report["raster_transparency"]["transparent_required_count"],
            1,
        )

    def test_translated_copy_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "copy mismatch"):
            validate_specs(
                self.lock_path,
                self.write_specs(changed_option="B"),
            )

    def test_reordered_required_structure_fails(self) -> None:
        with self.assertRaisesRegex(ValueError, "structure order mismatch"):
            validate_specs(
                self.lock_path,
                self.write_specs(reverse_option="C"),
            )

    def test_copy_moved_to_wrong_module_fails(self) -> None:
        paths = self.write_specs()
        moved_path = paths[1]
        spec = json.loads(moved_path.read_text(encoding="utf-8"))
        title = spec["layers"][0]["children"].pop(0)
        spec["layers"][1]["children"].append(title)
        moved_path.write_text(
            json.dumps(spec, ensure_ascii=False),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "copy parent mismatch"):
            validate_specs(self.lock_path, paths)

    def test_opaque_png_fails_transparency(self) -> None:
        self.write_provenance("assets/opaque.png", "transparent_required")
        with self.assertRaisesRegex(ValueError, "no alpha channel"):
            validate_alpha(
                self.root,
                self.provenance_path,
                self.write_specs(asset_path="assets/opaque.png"),
            )

    def test_transparent_gutter_around_baked_rectangle_fails(self) -> None:
        self.write_provenance(
            "assets/padded-opaque.png",
            "transparent_required",
        )
        with self.assertRaisesRegex(ValueError, "opaque rectangular background"):
            validate_alpha(
                self.root,
                self.provenance_path,
                self.write_specs(asset_path="assets/padded-opaque.png"),
            )

    def test_user_authorized_embedded_background_passes(self) -> None:
        self.write_provenance(
            "assets/opaque.png",
            "embedded_background_authorized",
            "User explicitly approved this full-bleed background.",
        )
        report = validate_alpha(
            self.root,
            self.provenance_path,
            self.write_specs(asset_path="assets/opaque.png"),
        )
        self.assertEqual(report["authorized_embedded_background_count"], 1)

    def test_project_state_cannot_await_selection_with_pending_gates(self) -> None:
        state_path = self.root / "project-state.json"
        state_path.write_text(
            json.dumps(
                {
                    "status": "AWAITING_PRIMARY_OPTION_SELECTION",
                    "inputs": [],
                    "options": {"a": {}, "b": {}, "c": {}},
                    "primary_selected_option": None,
                    "primary_selection_confirmed": False,
                    "additional_option_queue": [],
                    "asset_manifest": [],
                    "candidate_asset_minimum": 12,
                    "candidate_asset_target_range": [12, 18],
                    "preview_gates": {
                        "wireframe_fidelity": "pending",
                        "raster_transparency": "pending",
                        "layer_specs": "pending",
                        "asset_provenance": "pending",
                    },
                    "preview_gate_report": "preview-gates.json",
                    "qa": [],
                }
            ),
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "validate_project_state.py"),
                str(state_path),
                "--kind",
                "project-state",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot enter AWAITING_PRIMARY_OPTION_SELECTION", result.stderr)

    def test_project_state_accepts_generated_passing_report(self) -> None:
        report = run_gates(
            self.lock_path,
            self.provenance_path,
            self.root,
            self.write_specs(),
        )
        (self.root / "preview-gates.json").write_text(
            json.dumps(report),
            encoding="utf-8",
        )
        state_path = self.write_awaiting_state("pass")
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "validate_project_state.py"),
                str(state_path),
                "--kind",
                "project-state",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_project_state_rejects_fabricated_pass_report(self) -> None:
        (self.root / "preview-gates.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "status": "pass",
                    "required_options": ["A", "B", "C"],
                    "wireframe_fidelity": {"status": "pass"},
                    "raster_transparency": {"status": "pass"},
                    "layer_specs": {"status": "pass"},
                    "asset_provenance": {"status": "pass"},
                    "hashes": {},
                }
            ),
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "validate_project_state.py"),
                str(self.write_awaiting_state("pass")),
                "--kind",
                "project-state",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot be revalidated", result.stderr)

    def test_project_state_rejects_stale_report_after_raster_change(self) -> None:
        report = run_gates(
            self.lock_path,
            self.provenance_path,
            self.root,
            self.write_specs(),
        )
        (self.root / "preview-gates.json").write_text(
            json.dumps(report),
            encoding="utf-8",
        )
        Image.new("RGB", (100, 100), (255, 255, 255)).save(self.alpha_path)
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "validate_project_state.py"),
                str(self.write_awaiting_state("pass")),
                "--kind",
                "project-state",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot be revalidated", result.stderr)


if __name__ == "__main__":
    unittest.main()
