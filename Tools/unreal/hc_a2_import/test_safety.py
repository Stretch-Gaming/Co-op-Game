"""Offline safety tests; Unreal is simulated only at read-only preflight boundaries."""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import import_hc_a2 as importer
from source_audit import DESTINATION, PARENT, fbx_summary, verify_sources


class SafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(importer.MANIFEST_PATH.read_text(encoding="utf-8-sig"))

    def fake_unreal(self, *, project=None, engine="5.8.3-58210709", occupied=False,
                    tint=True, opaque=True):
        class Material:
            def get_editor_property(self, key):
                return "opaque" if opaque else "translucent"
        subsystem = SimpleNamespace(**{
            name: Mock(side_effect=AssertionError("Mutation or unexpected mesh call in dry run"))
            for name in ("get_nanite_settings", "set_nanite_settings", "add_simple_collisions",
                         "remove_collisions", "get_simple_collision_count", "get_num_uv_channels",
                         "get_lod_build_settings", "set_lod_build_settings")})
        fake = SimpleNamespace(
            Paths=SimpleNamespace(
                get_project_file_path=lambda: str(project or importer.PROJECT_ROOT / "CoopGame.uproject"),
                convert_relative_path_to_full=lambda p: p),
            SystemLibrary=SimpleNamespace(get_engine_version=lambda: engine),
            Material=Material,
            BlendMode=SimpleNamespace(BLEND_OPAQUE="opaque"),
            load_asset=lambda path: Material() if path == PARENT else None,
            MaterialEditingLibrary=SimpleNamespace(
                get_vector_parameter_names=lambda parent: ["Tint"] if tint else []),
            StaticMeshEditorSubsystem=object,
            get_editor_subsystem=lambda _: subsystem,
            EditorAssetLibrary=SimpleNamespace(does_asset_exist=lambda _: occupied),
            ScriptCollisionShapeType=SimpleNamespace(BOX=0),
        )
        for name in ("AssetImportTask", "FbxImportUI", "FbxFactory", "MaterialInstanceConstantFactoryNew"):
            setattr(fake, name, Mock(side_effect=AssertionError("Creation in dry run")))
        return fake

    def test_all_real_sources_match_manifest(self):
        report = verify_sources(importer.PROJECT_ROOT, self.manifest)
        self.assertEqual(len(report), 10)
        self.assertEqual(sum(a["nanite"] for a in report), 5)

    def test_default_offline_is_read_only(self):
        with patch.dict(sys.modules, {"unreal": None}), patch.object(importer, "execute") as write:
            with contextlib.redirect_stdout(io.StringIO()):
                report = importer.run([])
            write.assert_not_called()
        self.assertEqual(report["mode"], "dry-run")
        self.assertEqual(report["editor_checks"], "not run (offline)")
        self.assertNotIn("created_assets", report)

    def test_default_editor_dry_run_is_read_only(self):
        fake = self.fake_unreal()
        with patch.dict(sys.modules, {"unreal": fake}), patch.object(importer, "execute") as write:
            with contextlib.redirect_stdout(io.StringIO()):
                report = importer.run([])
            write.assert_not_called()
        self.assertEqual(report["editor_checks"], "read-only preflight passed")
        fake.AssetImportTask.assert_not_called()
        fake.FbxImportUI.assert_not_called()

    def test_execute_requires_absolute_project(self):
        for args in (["--execute"], ["--execute", "--project-file", "CoopGame.uproject"]):
            with self.assertRaisesRegex(ValueError, "absolute path"):
                importer.run(args)

    def test_execute_requires_editor(self):
        with patch.dict(sys.modules, {"unreal": None}), self.assertRaisesRegex(ValueError, "running Unreal"):
            importer.run(["--execute", "--project-file",
                          str(importer.PROJECT_ROOT / "CoopGame.uproject")])

    def test_wrong_open_project_refused_before_creation(self):
        with self.assertRaisesRegex(ValueError, "Open editor project"):
            importer.editor_preflight(self.fake_unreal(project=Path("C:/Other/CoopGame.uproject")),
                                      self.manifest, None)

    def test_wrong_explicit_project_refused(self):
        with self.assertRaisesRegex(ValueError, "--project-file must match"):
            importer.editor_preflight(self.fake_unreal(), self.manifest, "C:/Other/CoopGame.uproject")

    def test_offline_wrong_project_argument_refused(self):
        with patch.dict(sys.modules, {"unreal": None}), self.assertRaisesRegex(ValueError, "--project-file must match"):
            importer.run(["--project-file", "C:/Other/CoopGame.uproject"])

    def test_wrong_engine_refused(self):
        with self.assertRaisesRegex(ValueError, "Require Unreal 5.8.3"):
            importer.editor_preflight(self.fake_unreal(engine="5.8.2-123"), self.manifest, None)

    def test_existing_assets_refuse_whole_execution_batch(self):
        fake = self.fake_unreal(occupied=True)
        with patch.dict(sys.modules, {"unreal": fake}), patch.object(importer, "execute") as write:
            with self.assertRaisesRegex(ValueError, "occupied destinations"):
                importer.run(["--execute", "--project-file",
                              str(importer.PROJECT_ROOT / "CoopGame.uproject")])
            write.assert_not_called()

    def test_unregistered_disk_asset_is_refused(self):
        with patch.object(Path, "exists", return_value=True):
            self.assertEqual(len(importer.disk_conflicts(self.manifest)), 13)
            with self.assertRaisesRegex(ValueError, "Refusing overwrite"):
                importer.assert_unoccupied(self.fake_unreal(), self.manifest["assets"][0]["destination"])

    def test_missing_tint_or_translucent_parent_refused(self):
        for fake in (self.fake_unreal(tint=False), self.fake_unreal(opaque=False)):
            with self.assertRaises(ValueError):
                importer.editor_preflight(fake, self.manifest, None)

    def test_manifest_destination_escape_refused(self):
        altered = copy.deepcopy(self.manifest)
        altered["assets"][0]["destination"] = "/Game/Shared/SM_Forbidden"
        with self.assertRaisesRegex(ValueError, "Destination escaped"):
            verify_sources(importer.PROJECT_ROOT, altered)
        with self.assertRaisesRegex(ValueError, "Write escaped"):
            importer.package_file("/Game/Shared/SM_Forbidden")
        with self.assertRaisesRegex(ValueError, "outside HC-A2"):
            importer.package_file(DESTINATION + "/../SM_Forbidden")

    def test_manifest_source_or_hash_change_refused(self):
        altered = copy.deepcopy(self.manifest)
        altered["assets"][0]["source"] = "SourceArt/PG/Other.fbx"
        with self.assertRaisesRegex(ValueError, "Unexpected source"):
            verify_sources(importer.PROJECT_ROOT, altered)
        altered = copy.deepcopy(self.manifest)
        altered["assets"][0]["source_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Source hash changed"):
            verify_sources(importer.PROJECT_ROOT, altered)

    def test_metadata_hash_change_refused(self):
        altered = copy.deepcopy(self.manifest)
        altered["assets"][0]["validation_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Metadata hash changed"):
            verify_sources(importer.PROJECT_ROOT, altered)

    def test_lfs_pointer_refused(self):
        pointer = b"version https://git-lfs.github.com/spec/v1\noid sha256:123\nsize 456\n"
        with patch.object(Path, "read_bytes", return_value=pointer):
            with self.assertRaisesRegex(ValueError, "Unhydrated LFS pointer"):
                fbx_summary(Path("test.fbx"))

    def test_assembly_and_nanite_changes_refused(self):
        altered = copy.deepcopy(self.manifest)
        altered["assemblies"]["pressure_plate"]["top_pressed_cm"] = [0, 0, 0]
        with self.assertRaisesRegex(ValueError, "Assembly contract"):
            verify_sources(importer.PROJECT_ROOT, altered)
        altered = copy.deepcopy(self.manifest)
        altered["assets"][0]["nanite"] = True
        with self.assertRaisesRegex(ValueError, "Nanite threshold"):
            verify_sources(importer.PROJECT_ROOT, altered)

    def test_no_statue_selection_or_gate_bbox_confusion(self):
        self.assertEqual(self.manifest["assemblies"]["statues"]["selection"], "pending owner decision")
        gate = next(a for a in self.manifest["assets"] if a["name"] == "SM_ChamberGate_Frame")
        self.assertGreater(gate["validation_metadata"]["dimensions_cm"][1], 700)
        self.assertEqual(self.manifest["assemblies"]["chamber_gate"]["opening_yz_cm"], [400, 400])

    def tint_api(self, *, overridden=True, wrong=False):
        tint = importer.srgb_to_linear("#7A6E68")
        factory = lambda *v: SimpleNamespace(**dict(zip(("r","g","b","a"),v)))
        value = factory(*(tint if not wrong else [1,1,1,1]))
        return SimpleNamespace(LinearColor=factory, MaterialEditingLibrary=SimpleNamespace(
            set_material_instance_vector_parameter_value=lambda *args: False,
            get_material_instance_vector_parameter_value=lambda *args: value,
            is_material_instance_parameter_overridden=lambda *args: overridden,
            update_material_instance=lambda *args: None))

    def test_false_setter_return_with_correct_override_is_accepted(self):
        importer.assign_tint(self.tint_api(), object(), "#7A6E68")

    def test_missing_actual_override_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "read-back failed"):
            importer.assign_tint(self.tint_api(overridden=False), object(), "#7A6E68")

    def test_wrong_tint_readback_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "read-back failed"):
            importer.assign_tint(self.tint_api(wrong=True), object(), "#7A6E68")

    def test_palette_conversion_uses_linear_color(self):
        self.assertEqual(importer.srgb_to_linear("#000000"), [0, 0, 0, 1])
        self.assertEqual(importer.srgb_to_linear("#FFFFFF"), [1, 1, 1, 1])
        self.assertLess(importer.srgb_to_linear("#7A6E68")[0], 122 / 255)


if __name__ == "__main__":
    unittest.main(verbosity=2)
