"""Focused validator tests. Fixtures are synthetic, not Blender/Unreal acceptance."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

QA = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validate_hc", QA / "validate_hc.py")
qa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qa)
FIXTURES = Path(__file__).parent / "fixtures"

def digest(data):
    return hashlib.sha256(data).hexdigest()

def png(width=512, height=512):
    def chunk(kind, value):
        payload = kind + value
        return struct.pack(">I", len(value)) + payload + struct.pack(">I", zlib.crc32(payload) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" +
            chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)) +
            chunk(b"IDAT", zlib.compress((b"\0" + b"\0" * width * 4) * height)) + chunk(b"IEND", b""))

def lfs(data):
    return f"version https://git-lfs.github.com/spec/v1\noid sha256:{digest(data)}\nsize {len(data)}\n".encode()

class ValidatorTests(unittest.TestCase):
    def setUp(self):
        parent = Path(__file__).parent / ".tmp"
        parent.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="repository with spaces ", dir=parent)
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name).resolve()
        assert self.repo.is_relative_to(parent.resolve())
        self.git("init", "--quiet")
        self.write(".gitattributes", "*.fbx filter=lfs diff=lfs merge=lfs -text\n*.png filter=lfs diff=lfs merge=lfs -text\n*.uasset filter=lfs diff=lfs merge=lfs -text\n")
        self.mesh = self.asset("SourceArt/HC/HC-A1/SM_Relic_Test.fbx", b"synthetic fixture, not geometry")
        self.record = self.mesh.with_suffix(".validation.json")
        self.metadata = json.loads((FIXTURES / "export.json").read_text())
        self.metadata["output"] = self.mesh.relative_to(self.repo).as_posix()
        self.metadata["sha256"] = digest(self.mesh.read_bytes())
        self.record.write_text(json.dumps(self.metadata), encoding="utf-8")

    def git(self, *args, data=None):
        result = subprocess.run(["git", "-C", str(self.repo), *args], input=data,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return result.stdout

    def write(self, relative, value):
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(value, bytes):
            path.write_bytes(value)
        else:
            path.write_text(value, encoding="utf-8")
        return path

    def stage(self, path, blob):
        oid = self.git("hash-object", "-w", "--stdin", data=blob).decode().strip()
        self.git("update-index", "--add", "--cacheinfo", "100644," + oid + "," + path.relative_to(self.repo).as_posix())

    def asset(self, relative, data):
        path = self.write(relative, data)
        self.stage(path, lfs(data))
        return path

    def change_record(self, **values):
        self.metadata.update(values)
        self.record.write_text(json.dumps(self.metadata), encoding="utf-8")

    def run_qa(self, task="HC-A1", manifests=()):
        return qa.Validator(self.repo, task).run(manifests)

    def codes(self, report):
        return {x["code"] for x in report["findings"]}

    def manifest(self, entries):
        path = self.repo / "manifest.json"
        path.write_text(json.dumps(dict(schema_version=1, assets=entries)), encoding="utf-8")
        return path

    def test_valid_export_png_and_warning_only_exit(self):
        self.asset("SourceArt/HC/HC-A1/SM_Relic_Test_preview.png", png())
        report = self.run_qa()
        self.assertEqual(report["exit_code"], 0, report)
        self.assertEqual(report["errors"], 0)
        self.assertIn("provenance.missing", self.codes(report))
        self.assertEqual([f["value"] for f in report["facts"] if f["kind"] == "png_dimensions"], [[512, 512]])

    def test_cli_spaces_json_and_exit(self):
        result = subprocess.run([sys.executable, "-B", str(QA / "validate_hc.py"), str(self.repo),
                                 "--task", "HC-A1", "--format", "json"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["assets_checked"], 1)
        self.change_record(sha256="0" * 64)
        result = subprocess.run([sys.executable, "-B", str(QA / "validate_hc.py"), str(self.repo),
                                 "--task", "HC-A1"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("hash.mismatch", result.stdout)

    def test_bad_names_and_uppercase_extensions(self):
        self.asset("SourceArt/HC/HC-A1/wrong.PNG", png())
        self.asset("SourceArt/HC/HC-A1/T_Wrong.fbx", b"fixture")
        report = self.run_qa()
        self.assertTrue({"name.prefix", "name.extension", "record.missing"} <= self.codes(report))
        self.assertEqual(report["exit_code"], 1)

    def test_working_lfs_pointer_is_failure_and_not_png(self):
        image = png()
        path = self.asset("SourceArt/HC/HC-A1/T_Test.png", image)
        path.write_bytes(lfs(image))
        report = self.run_qa()
        self.assertIn("lfs.unhydrated", self.codes(report))
        self.assertNotIn("png.header", self.codes(report))
        self.assertNotIn("hash.mismatch", self.codes(report))
        self.assertEqual(report["exit_code"], 1)

    def test_corrupt_pointer(self):
        self.mesh.write_bytes(b"version https://git-lfs.github.com/spec/v1\noid nope\n")
        report = self.run_qa()
        self.assertIn("file.invalid", self.codes(report))
        self.assertEqual(report["exit_code"], 1)

    def test_pointer_differs_from_index(self):
        self.mesh.write_bytes(lfs(b"different data"))
        self.assertIn("lfs.pointer_mismatch", self.codes(self.run_qa()))

    def test_stale_hydrated_content_against_lfs_oid(self):
        self.mesh.write_bytes(b"stale mesh")
        self.assertTrue({"hash.mismatch", "lfs.size"} <= self.codes(self.run_qa()))

    def test_attributes_and_index_pointer_independent(self):
        self.write(".gitattributes", "*.fbx -filter -diff -merge text\n")
        self.stage(self.mesh, self.mesh.read_bytes())
        self.assertTrue({"lfs.attributes", "lfs.index"} <= self.codes(self.run_qa()))

    def test_nested_attributes_override(self):
        self.write("SourceArt/HC/HC-A1/.gitattributes", "*.fbx -filter\n")
        self.assertIn("lfs.attributes", self.codes(self.run_qa()))

    def test_missing_output(self):
        self.mesh.unlink()
        report = self.run_qa()
        self.assertIn("file.invalid", self.codes(report))
        self.assertEqual(report["exit_code"], 1)

    def test_missing_source_record(self):
        self.record.unlink()
        self.assertIn("record.missing", self.codes(self.run_qa()))

    def test_empty_asset(self):
        self.mesh.write_bytes(b"")
        self.assertIn("file.invalid", self.codes(self.run_qa()))

    def test_unbound_export_is_warning(self):
        self.metadata.pop("sha256")
        self.change_record()
        report = self.run_qa()
        self.assertIn("record.unbound", self.codes(report))
        self.assertEqual(report["exit_code"], 0)

    def test_reported_relic_spec_and_triangle_budget(self):
        self.change_record(triangles_before=11000, triangles_after=11000, dimensions_cm=[18, 16, 7])
        report = self.run_qa()
        self.assertTrue({"record.triangle_budget", "record.relic_size"} <= self.codes(report))
        self.assertTrue(all(f["basis"] == "recorded" for f in report["findings"] if f["code"].startswith("record.")))
        self.assertEqual(next(f["severity"] for f in report["findings"] if f["code"] == "record.relic_size"), "warning")

    def test_recorded_pivot_consistency(self):
        self.change_record(bounds_min_cm=[0, 0, 9])
        self.assertIn("record.pivot", self.codes(self.run_qa()))

    def test_malformed_provenance_fields(self):
        for provenance in (dict(license=123), dict(public_redistribution="yes"), []):
            manifest = self.manifest([dict(task="HC-A1", source=self.mesh.relative_to(self.repo).as_posix(),
                                           provenance=provenance)])
            self.assertIn("metadata.invalid", self.codes(self.run_qa(manifests=[manifest])))

    def test_bad_export_field_types(self):
        cases = [dict(triangles_after=True), dict(dimensions_cm=[1, 2]), dict(bounds_min_cm=[0, float("inf"), 0]),
                 dict(explicit_unit_correction_factor=0), dict(up_axis="+Y"), dict(pivot=None), dict(UV_warning=3), dict(dimensions_cm=[10**400, 1, 2]),
                 dict(output="../../escape.fbx"), dict(output="C:/outside.fbx")]
        for changes in cases:
            with self.subTest(changes=changes):
                original = copy.deepcopy(self.metadata)
                self.change_record(**changes)
                self.assertIn("metadata.invalid", self.codes(self.run_qa()))
                self.metadata = original
                self.change_record()

    def test_malformed_json_duplicate_keys_and_roots(self):
        samples = [(FIXTURES / "malformed.json").read_text(), '{"output":"x","output":"y"}',
                   "[]", "null", '{"dimensions_cm":[NaN,1,2]}', '{"dimensions_cm":[1e999,1,2]}']
        for sample in samples:
            with self.subTest(sample=sample):
                self.record.write_text(sample, encoding="utf-8")
                report = self.run_qa()
                self.assertIn("metadata.invalid", self.codes(report))
                self.assertEqual(report["exit_code"], 1)

    def test_png_header_dimensions_crc_and_truncation(self):
        path = self.asset("SourceArt/HC/HC-A1/T_Test.png", png(1024, 512))
        report = self.run_qa()
        self.assertIn([1024, 512], [f["value"] for f in report["facts"] if f["kind"] == "png_dimensions"])
        data = bytearray(path.read_bytes())
        data[29] ^= 1
        for blob in (bytes(data), b"\x89PNG", b"not a png", png(0, 1)):
            with self.subTest(size=len(blob)):
                path.write_bytes(blob)
                self.stage(path, lfs(blob))
                self.assertIn("png.header", self.codes(self.run_qa()))

    def test_manifest_hashes_dimensions_imports_provenance(self):
        texture = self.asset("SourceArt/HC/HC-A1/T_Test.png", png())
        imported = self.asset("Content/Puzzles/Art/T_Test.uasset", b"synthetic import")
        manifest = self.manifest([dict(task="HC-A1", source=texture.relative_to(self.repo).as_posix(),
            source_sha256=digest(texture.read_bytes()), dimensions=[512, 512],
            imported=imported.relative_to(self.repo).as_posix(), imported_sha256=digest(imported.read_bytes()),
            provenance=dict(source="fixture", url="https://example.invalid/fixture", plan="synthetic",
                            license="synthetic test only", public_redistribution=True, attribution="none"))])
        report = self.run_qa(manifests=[manifest])
        self.assertEqual(report["exit_code"], 0, report)
        self.assertEqual(report["assets_checked"], 3)
        manifest_data = json.loads(manifest.read_text())
        manifest_data["assets"][0]["dimensions"] = [256, 256]
        manifest_data["assets"][0]["source_sha256"] = "0" * 64
        manifest_data["assets"][0]["provenance"]["public_redistribution"] = False
        manifest.write_text(json.dumps(manifest_data))
        report = self.run_qa(manifests=[manifest])
        self.assertTrue({"png.dimensions", "hash.mismatch", "provenance.redistribution"} <= self.codes(report))

    def test_manifest_missing_and_malformed(self):
        missing = self.repo / "missing.json"
        self.assertIn("metadata.invalid", self.codes(self.run_qa(manifests=[missing])))
        for data in ([], {}, dict(schema_version=True, assets=[]), dict(schema_version=2, assets=[]),
                     dict(schema_version=1, assets=[dict(task="PG-A1", source="x")]),
                     dict(schema_version=1, assets=[dict(task="HC-A1", source="SourceArt/HC/HC-A1/T_X.png", sha256="0" * 64)]),
                     dict(schema_version=1, assets=[dict(task="HC-A1", source="SourceArt/HC/HC-A1/T_X.png", imported_sha256="0" * 64)]),
                     dict(schema_version=1, assets=[dict(task="HC-A1", source="../escape.png")]),
                     dict(schema_version=1, assets=[dict(task="HC-A1", source="SourceArt/HC/HC-A1/T_X.png",
                                                       imported="Content/Player/Art/T_X.uasset")])):
            with self.subTest(data=data):
                path = self.write("manifest.json", json.dumps(data))
                self.assertIn("metadata.invalid", self.codes(self.run_qa(manifests=[path])))

    def test_manifest_missing_asset(self):
        path = self.manifest([dict(task="HC-A1", source="SourceArt/HC/HC-A1/T_Missing.png")])
        self.assertIn("file.invalid", self.codes(self.run_qa(manifests=[path])))

    def test_task_filter_excludes_other_assets_and_imports(self):
        self.asset("SourceArt/HC/HC-A2/bad.PNG", b"bad")
        self.asset("Content/Puzzles/Art/bad.uasset", b"bad")
        self.assertEqual(self.run_qa()["exit_code"], 0)
        self.assertIn("name.prefix", self.codes(self.run_qa(task=None)))
        manifest = self.manifest([dict(task="HC-A2", source="SourceArt/HC/HC-A2/SM_Missing.fbx")])
        self.assertEqual(self.run_qa(manifests=[manifest])["exit_code"], 0)

    def test_gate_opening_is_not_mesh_bounds(self):
        path = self.asset("SourceArt/HC/HC-A2/SM_ChamberGate_Frame.fbx", b"gate")
        record = copy.deepcopy(self.metadata)
        record.update(output=path.relative_to(self.repo).as_posix(), dimensions_cm=[156, 708.8224, 511.2001],
                      bounds_min_cm=[-78, -354.4112, 0],
                      sha256=digest(path.read_bytes()))
        path.with_suffix(".validation.json").write_text(json.dumps(record))
        manifest = self.manifest([dict(task="HC-A2", source=path.relative_to(self.repo).as_posix(),
                                      opening_cm=[400, 400])])
        report = self.run_qa(task="HC-A2", manifests=[manifest])
        self.assertEqual(report["exit_code"], 0, report)
        self.assertIn("opening_cm", [f["kind"] for f in report["facts"]])

    def hud(self):
        raw = self.asset("SourceArt/HC/HC-A3/sources/T_Test_source.png", png(16, 16))
        image = self.asset("SourceArt/HC/HC-A3/T_Test.png", png())
        preview = self.asset("SourceArt/HC/HC-A3/preview.png", png(1200, 4))
        generation = dict(tool="fixture", records=[dict(name="T_Test", source="sources/T_Test_source.png",
                          source_sha256=digest(raw.read_bytes()), output="T_Test.png")])
        self.write("SourceArt/HC/HC-A3/generation.json", json.dumps(generation))
        validation = dict(schema_version=1, source_delivery_only=True,
            automated_checks=[dict(file="T_Test.png", sha256=digest(image.read_bytes()),
                                  bytes=image.stat().st_size, dimensions=[512, 512], mode="RGBA",
                                  alpha_extrema=[0, 255], source_sha256=digest(raw.read_bytes()))],
            preview=dict(file="preview.png", dimensions=[1200, 4], sha256=digest(preview.read_bytes())))
        path = self.write("SourceArt/HC/HC-A3/validation.json", json.dumps(validation))
        return raw, image, path, validation

    def test_existing_hud_schemas(self):
        self.hud()
        report = self.run_qa(task="HC-A3")
        self.assertEqual(report["exit_code"], 0, report)
        self.assertIn("pixel_claims", [f["kind"] for f in report["facts"]])

    def test_hud_source_hash_hex_case(self):
        _, _, path, validation = self.hud()
        validation["automated_checks"][0]["source_sha256"] = validation["automated_checks"][0]["source_sha256"].upper()
        path.write_text(json.dumps(validation))
        report = self.run_qa(task="HC-A3")
        self.assertEqual(report["exit_code"], 0, report)

    def test_hud_stale_source_pair_and_missing_generation(self):
        _, _, path, validation = self.hud()
        validation["automated_checks"][0]["source_sha256"] = "0" * 64
        path.write_text(json.dumps(validation))
        self.assertIn("hash.source_pair", self.codes(self.run_qa(task="HC-A3")))
        (path.parent / "generation.json").unlink()
        self.assertIn("metadata.missing", self.codes(self.run_qa(task="HC-A3")))

    def test_generation_missing_sources_and_bad_reference_path(self):
        raw, _, path, _ = self.hud()
        raw.unlink()
        self.assertIn("file.invalid", self.codes(self.run_qa(task="HC-A3")))
        generation = path.parent / "generation.json"
        data = json.loads(generation.read_text())
        data.update(reference_path="https://example.invalid/resource.png", reference_sha256="0" * 64)
        generation.write_text(json.dumps(data))
        self.assertIn("metadata.invalid", self.codes(self.run_qa(task="HC-A3")))

    def test_hud_malformed_pixel_claims_and_nonfinite_extra(self):
        _, _, path, data = self.hud()
        for changes in (dict(alpha_extrema=[255, 0]), dict(fully_transparent_pixels=-1),
                        dict(max_boundary_alpha=256), dict(visible_bounds_alpha_gt_8=[0, 0, 999, 999]),
                        dict(mode=None), dict(extra=1e999)):
            with self.subTest(changes=changes):
                item = copy.deepcopy(data)
                item["automated_checks"][0].update(changes)
                path.write_text(json.dumps(item))
                self.assertIn("metadata.invalid", self.codes(self.run_qa(task="HC-A3")))

    def test_no_license_inferred_from_generation_tool(self):
        self.hud()
        report = self.run_qa(task="HC-A3")
        self.assertIn("provenance.missing", self.codes(report))
        self.assertFalse(any(f["kind"] == "provenance" for f in report["facts"]))

    def test_missing_repository_task_and_subdirectory(self):
        missing = qa.Validator(self.repo / "absent").run()
        self.assertEqual(missing["exit_code"], 2)
        self.assertEqual(self.run_qa(task="HC-A9")["exit_code"], 2)
        self.assertEqual(self.run_qa(task="../HC-A1")["exit_code"], 2)
        self.assertEqual(qa.Validator(self.mesh.parent).run()["exit_code"], 2)

    def test_symlink_escape_if_supported(self):
        outside = QA / "README.md"
        path = self.repo / "SourceArt/HC/HC-A1/T_Link.png"
        try:
            path.symlink_to(outside)
        except OSError:
            self.skipTest("symlinks unavailable to current OS user")
        report = self.run_qa()
        self.assertEqual(report["exit_code"], 2)
        self.assertIn("tool.input", self.codes(report))

    def test_read_only_files_git_index_config_and_allowed_commands(self):
        def snapshot():
            return {p.relative_to(self.repo).as_posix(): (digest(p.read_bytes()), p.stat().st_mtime_ns)
                    for p in self.repo.rglob("*") if p.is_file()}
        before = snapshot()
        original = subprocess.run
        calls = []
        def guard(args, **kwargs):
            self.assertEqual(args[0], "git")
            self.assertIn(args[3], {"rev-parse", "check-attr", "ls-files", "cat-file"})
            calls.append(args)
            return original(args, **kwargs)
        with patch.object(qa.subprocess, "run", side_effect=guard):
            report = self.run_qa()
        self.assertEqual(report["exit_code"], 0)
        self.assertTrue(calls)
        self.assertEqual(before, snapshot())
        # Same inputs yield stable output, without using mtime as validity evidence.
        self.assertEqual(report, self.run_qa())

    def test_untracked_asset_fails_lfs_coverage(self):
        self.write("SourceArt/HC/HC-A1/T_Untracked.png", png())
        report = self.run_qa()
        self.assertIn("git.untracked", self.codes(report))
        self.assertEqual(report["exit_code"], 1)

if __name__ == "__main__":
    unittest.main()
