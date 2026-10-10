"""Offline acceptance checks; no Unreal module or editor is used."""
import argparse
import contextlib
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import types
import unittest
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import import_relics as importer

ROOT = importer.ROOT
MANIFEST = json.loads((HERE / "manifest.json").read_text())


def fake_editor(project=ROOT, version="5.8.3-58210709+++UE5+Release-5.8", existing=()):
    class Material:
        def get_editor_property(self, name):
            return "opaque"
    ue = types.SimpleNamespace(
        Paths=types.SimpleNamespace(project_dir=lambda: str(project), get_project_file_path=lambda: str(project / "CoopGame.uproject")),
        SystemLibrary=types.SimpleNamespace(get_engine_version=lambda: version),
        UnrealEditorSubsystem=object, get_editor_subsystem=lambda _: types.SimpleNamespace(get_game_world=lambda: None),
        Material=Material, load_asset=lambda _: Material(), BlendMode=types.SimpleNamespace(BLEND_OPAQUE="opaque"),
        MaterialEditingLibrary=types.SimpleNamespace(get_scalar_parameter_names=lambda _: [], get_vector_parameter_names=lambda _: []),
        AssetRegistryHelpers=types.SimpleNamespace(get_asset_registry=lambda: types.SimpleNamespace(get_assets_by_path=lambda *a, **k: list(existing))),
        EditorAssetLibrary=types.SimpleNamespace(does_asset_exist=lambda _: False), FbxImportUI=Mock())
    return ue


class SafetyChecks(unittest.TestCase):
    def test_source_gate(self):
        manifest, report = importer.validate()
        self.assertEqual(len(report["assets"]), 4)
        self.assertFalse(report["writes_performed"])
        self.assertEqual(manifest, MANIFEST)

    def test_default_dry_run_does_not_import_unreal_or_execute(self):
        with patch.object(importer, "editor_preflight", side_effect=AssertionError("editor accessed")), patch.object(importer, "execute", side_effect=AssertionError("mutation")), contextlib.redirect_stdout(io.StringIO()) as stream:
            self.assertEqual(importer.main([]), 0)
        self.assertEqual(json.loads(stream.getvalue())["mode"], "read_only_dry_run")

    def test_execute_missing_bindings_refused_before_editor(self):
        with patch.object(importer, "editor_preflight", side_effect=AssertionError("editor accessed")), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(importer.main(["--execute"]), 2)

    def test_unverified_material_example_refused(self):
        with self.assertRaisesRegex(ValueError, "verified_in_ue"):
            importer.read_bindings(HERE / "material_bindings.example.json", MANIFEST)

    def test_wrong_checkout_refused(self):
        with self.assertRaisesRegex(ValueError, "tooling checkout"):
            importer.validate(ROOT.parent)

    def test_source_path_traversal_refused(self):
        with self.assertRaisesRegex(ValueError, "escapes"):
            importer.source_path(ROOT, "AGENTS.md")

    def test_missing_source_refused(self):
        with self.assertRaisesRegex(ValueError, "Missing source"):
            importer.source_path(ROOT, "SourceArt/HC/HC-A1/missing.fbx")

    def test_pointer_source_refused(self):
        with patch.object(Path, "read_bytes", return_value=b"version https://git-lfs.github.com/spec/v1\n"), self.assertRaisesRegex(ValueError, "Unhydrated"):
            importer.source_path(ROOT, MANIFEST["assets"][0]["fbx_path"])

    def test_hash_mismatch_refused(self):
        with patch.object(importer, "digest", return_value="0" * 64), self.assertRaisesRegex(ValueError, "Hash mismatch"):
            importer.validate()

    def test_binary_inspection_mismatch_refused(self):
        altered = copy.deepcopy(MANIFEST["assets"][0]["fbx_inspection"])
        altered["triangles"] -= 1
        with patch.object(importer, "inspect_fbx", return_value=altered), self.assertRaisesRegex(ValueError, "inspection mismatch"):
            importer.validate()

    def test_destination_isolation(self):
        for path in ("/Game/Shared/Style/MI_X", "/Game/Puzzles/Art/HCA1_RelicsOther/SM_X", "/Game/Puzzles/Art/HCA1_Relics/../SM_X", "/Game/Puzzles/Art/HCA1_Relics/Sub/SM_X"):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "outside"):
                importer.isolated(path)

    def test_wrong_active_editor_project_refused(self):
        with patch.dict(sys.modules, {"unreal": fake_editor(project=ROOT.parent)}), self.assertRaisesRegex(ValueError, "different project"):
            importer.editor_preflight(ROOT, MANIFEST, None)

    def test_wrong_engine_patch_refused(self):
        with patch.dict(sys.modules, {"unreal": fake_editor(version="5.8.2-123")}), self.assertRaisesRegex(ValueError, "5.8.3"):
            importer.editor_preflight(ROOT, MANIFEST, None)

    def test_repeat_run_existing_package_refused_before_factory(self):
        fake = fake_editor(existing=["SM_Relic_GoldIdol"])
        with patch.dict(sys.modules, {"unreal": fake}), self.assertRaisesRegex(ValueError, "no overwrite"):
            importer.editor_preflight(ROOT, MANIFEST, None)
        fake.FbxImportUI.assert_not_called()

    def test_unregistered_disk_content_refused(self):
        fake = fake_editor()
        with patch.dict(sys.modules, {"unreal": fake}), patch.object(Path, "exists", return_value=True), patch.object(Path, "rglob", return_value=iter([Path("unregistered_package")])), self.assertRaisesRegex(ValueError, "disk content"):
            importer.editor_preflight(ROOT, MANIFEST, None)
        fake.FbxImportUI.assert_not_called()

    def test_unknown_material_parameter_refused(self):
        bindings = {"profiles": {"gold": {"scalars": {"Unknown": 1}, "vectors": {}}}}
        with patch.dict(sys.modules, {"unreal": fake_editor()}), self.assertRaisesRegex(ValueError, "Unknown M_Stylized binding"):
            importer.editor_preflight(ROOT, MANIFEST, bindings)


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).rstrip("\r\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-evidence", action="store_true", help="Write evidence.json and dry_run.txt inside this tooling folder")
    args = parser.parse_args()
    syntax = []
    for path in sorted(HERE.glob("*.py")):
        compile(path.read_text(encoding="utf-8-sig"), str(path), "exec")
        syntax.append(path.name)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SafetyChecks))
    print(stream.getvalue())
    if not result.wasSuccessful():
        return 1
    for asset in MANIFEST["assets"]:
        source = ROOT / asset["fbx_path"]
        pointer = git("show", "HEAD:" + asset["fbx_path"])
        oid = next(line.split(":", 1)[1] for line in pointer.splitlines() if line.startswith("oid sha256:"))
        size = int(next(line.split()[1] for line in pointer.splitlines() if line.startswith("size ")))
        importer.require(oid == importer.digest(source) == asset["lfs_object"]["oid_sha256"], "LFS object hash mismatch")
        importer.require(size == source.stat().st_size == asset["lfs_object"]["size_bytes"], "LFS size mismatch")
    lfs = git("lfs", "ls-files", "-l", "--include=SourceArt/HC/HC-A1/*.fbx")
    importer.require(len(lfs.splitlines()) == 4 and all(" * " in line for line in lfs.splitlines()), "Expected four hydrated LFS FBXs")
    dirty = git("status", "--porcelain", "--untracked-files=all")
    importer.require(all(line[3:].strip('"').replace('\\', '/').startswith("Tools/unreal/hc_a1_import/") for line in dirty.splitlines()), "Writes outside tooling scope")
    before = {p: importer.digest(p) for p in HERE.rglob("*") if p.is_file()}
    dry = subprocess.run([sys.executable, str(HERE / "import_relics.py")], cwd=ROOT, capture_output=True, text=True, check=True)
    importer.require(json.loads(dry.stdout)["writes_performed"] is False, "Dry-run write flag")
    importer.require(before == {p: importer.digest(p) for p in HERE.rglob("*") if p.is_file()}, "Dry run changed tooling files")
    evidence = {"validation_date": "2026-10-10", "base_origin_main": MANIFEST["base_origin_main"],
                "branch": git("branch", "--show-current"), "python": sys.version,
                "offline_tests_passed": result.testsRun, "test_output": stream.getvalue(), "python_syntax_passed": syntax,
                "source_validation": json.loads(dry.stdout), "lfs_hydration": lfs,
                "working_tree_scope_check": "Only Tools/unreal/hc_a1_import/ is changed", "default_dry_run_no_tooling_file_changes": True,
                "tooling_hashes": {p.name: value for p, value in before.items() if p.name not in ("evidence.json", "dry_run.txt")},
                "editor_launched_or_controlled": False, "engine_import_tested": False, "gameplay_tested": False,
                "mock_tests_note": "Editor refusal cases use a fake API only; these are not Unreal validation.",
                "installed_api_reference": {"engine": "5.8.3", "changelist": 58210709,
                    "headers_read": ["Engine/Build/Build.version", "AssetImportTask.h", "FbxStaticMeshImportData.h", "FbxMeshImportData.h", "StaticMesh.h", "MaterialEditingLibrary.h", "StaticMeshEditorSubsystem.h", "UnrealEditorSubsystem.h"]}}
    if args.write_evidence:
        (HERE / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        (HERE / "dry_run.txt").write_text(dry.stdout, encoding="utf-8")
    print(f"PASS: {result.testsRun} offline checks; four hydrated sources; syntax; default dry run; destination and write scope.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
