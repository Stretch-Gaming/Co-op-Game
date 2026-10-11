"""Exercise packaged-launch boundaries using temporary files and fake UAT/apps."""

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import plistlib
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "package_game.py"
SPEC = importlib.util.spec_from_file_location("package_game", SCRIPT)
package = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(package)


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="packaged game ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "Project with spaces"
        self.root.mkdir()
        (self.root / "CoopGame.uproject").write_text("{}")
        maps = self.root / "Content/Maps"
        maps.mkdir(parents=True)
        (maps / "L_Site01.umap").write_bytes(b"fixture, not an Unreal asset")
        six_round = self.root / "Content/Puzzles/Test/SixRound/L_SixRound_Test.umap"
        six_round.parent.mkdir(parents=True)
        six_round.write_bytes(b"fixture, not an Unreal asset")
        config = self.root / "Config/DefaultEngine.ini"
        config.parent.mkdir()
        config.write_text("[/Script/EngineSettings.GameMapsSettings]\n"
                          "GameDefaultMap=/Game/Maps/L_Site01.L_Site01\n"
                          "GameDefaultMap=/Game/Puzzles/Test/SixRound/L_SixRound_Test.L_SixRound_Test\n")
        self.engine = Path(self.temp.name) / "Engine with spaces"
        version = self.engine / "Engine/Build/Build.version"
        version.parent.mkdir(parents=True)
        version.write_text(json.dumps({"MajorVersion": 5, "MinorVersion": 8, "PatchVersion": 3}))
        self.uat = self.engine / "Engine/Build/BatchFiles/RunUAT.sh"
        self.uat.parent.mkdir(parents=True)
        self.uat.write_text("#!/bin/bash\nexit 0\n")
        self.identity = {"commit": "a" * 40, "branch": "test", "working_tree": []}

    def contexts(self, free_gib=40):
        from contextlib import ExitStack
        stack = ExitStack()
        stack.enter_context(patch.object(package, "ROOT", self.root))
        stack.enter_context(patch.object(package, "native_platform", return_value="Mac"))
        stack.enter_context(patch.object(package, "git_identity", return_value=self.identity))
        stack.enter_context(patch.object(package.shutil, "disk_usage",
                                        return_value=type("Usage", (), {"free": free_gib * 1024 ** 3})()))
        stack.enter_context(patch.dict(os.environ, {"UE_ROOT": str(self.engine)}))
        stack.enter_context(redirect_stdout(io.StringIO()))
        stack.enter_context(redirect_stderr(io.StringIO()))
        return stack

    def app(self, archive):
        app = archive / "Mac/CoopGame.app/Contents"
        binary = app / "MacOS/CoopGame"
        binary.parent.mkdir(parents=True)
        with (app / "Info.plist").open("wb") as output:
            plistlib.dump({"CFBundleExecutable": "CoopGame"}, output)
        binary.write_text("#!/bin/bash\nexit 0\n")
        binary.chmod(0o755)
        return binary.resolve()

    def test_lfs_pointer_in_referenced_content_blocks_before_build(self):
        (self.root / "Content/unfetched.uasset").write_text(
            "version https://git-lfs.github.com/spec/v1\noid sha256:fake\nsize 1\n")
        with self.assertRaisesRegex(ValueError, "unfetched Git LFS"):
            package.validate_content(self.root, "/Game/Maps/L_Site01")

    def test_missing_or_traversal_map_is_rejected(self):
        for name in ("/Game/../Other", "/Game/Maps/Missing", "/Game/Maps/L_Site01?listen"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                package.validate_content(self.root, name)

    def test_default_map_uses_last_assignment_in_game_maps_section(self):
        self.assertEqual(package.default_map(self.root), "/Game/Puzzles/Test/SixRound/L_SixRound_Test")
        config = self.root / "Config/DefaultEngine.ini"
        with config.open("a") as output:
            output.write("[UnrelatedSection]\nGameDefaultMap=/Game/Maps/NotTheDefault\n")
        self.assertEqual(package.default_map(self.root), "/Game/Puzzles/Test/SixRound/L_SixRound_Test")

    def test_wrong_engine_version_is_rejected(self):
        version = self.engine / "Engine/Build/Build.version"
        version.write_text('{"MajorVersion": 5, "MinorVersion": 8, "PatchVersion": 2}')
        with self.assertRaisesRegex(ValueError, "expected 5.8.3"):
            package.engine_root("Mac", str(self.engine))

    def test_dry_run_is_read_only_and_reports_low_disk(self):
        with self.contexts(free_gib=10), patch.object(package, "stream_build") as build:
            self.assertEqual(package.main(["--dry-run"]), 0)
            build.assert_not_called()
        self.assertFalse((self.root / "Saved").exists())
        self.assertFalse((self.root / "Builds").exists())

    def test_real_build_blocks_low_disk_without_writing(self):
        with self.contexts(free_gib=10), patch.object(package, "stream_build") as build:
            with self.assertRaisesRegex(ValueError, "30 GiB"):
                package.main([])
            build.assert_not_called()
        self.assertFalse((self.root / "Saved").exists())

    def test_windows_plan_keeps_spaced_paths_and_selects_bootstrap(self):
        project = Path("C:/Team Work/CoopGame.uproject")
        command = package.build_command(Path("C:/Epic Games/Engine/Build/BatchFiles/RunUAT.bat"), "Win64",
                                        project, "/Game/Maps/L_Site01", Path("archive"), Path("stage"))
        self.assertIn("-project=C:/Team Work/CoopGame.uproject", command)
        self.assertIn("-cookall", command)
        self.assertIn("-unrealexe=C:/Epic Games/Engine/Binaries/Win64/UnrealEditor-Cmd.exe", command)
        self.assertFalse(any("-target=" in part or "Editor.exe" in part for part in command))
        archive = self.root / "Builds/PackagedPlay/Win64/test"
        native = archive / "CoopGame/Binaries/Win64/CoopGame.exe"
        native.parent.mkdir(parents=True)
        native.write_bytes(b"fixture")
        bootstrap = archive / "CoopGame.exe"
        bootstrap.write_bytes(b"fixture")
        self.assertEqual(package.packaged_executable(archive, "Win64"), bootstrap.resolve())

    def test_host_join_and_invalid_address_boundaries(self):
        binary, log = Path("packaged binary"), Path("game log")
        command = package.game_command(binary, "/Game/Maps/L_Site01", "host", None, log)
        self.assertEqual(command[1], "/Game/Maps/L_Site01?listen")
        command = package.game_command(binary, "/Game/Maps/L_Site01", "join", "127.0.0.1:7777", log)
        self.assertEqual(command[1], "127.0.0.1:7777")
        self.assertNotIn("-game", command)
        for address in (None, "127.0.0.1; bad", "host:0", "host:65536", "-flag", "ip?option"):
            with self.subTest(address=address), self.assertRaises(ValueError):
                package.game_command(binary, "/Game/Maps/L_Site01", "join", address, log)

    def test_failed_uat_never_launches_old_package(self):
        archive = self.root / "Builds/PackagedPlay/Mac/old"
        self.app(archive)
        with self.contexts(), patch.object(package, "stream_build", return_value=17), \
                patch.object(package.subprocess, "call") as launch:
            self.assertEqual(package.main([]), 17)
            launch.assert_not_called()
        receipt = json.loads(next((self.root / "Saved").rglob("build-receipt.json")).read_text())
        self.assertEqual(receipt["status"], "failed")
        self.assertEqual(receipt["uat_exit_code"], 17)

    def test_successful_build_launches_only_new_archive_and_records_exit(self):
        def fake_build(command, root, log):
            archive = Path(next(arg.split("=", 1)[1] for arg in command
                                if arg.startswith("-archivedirectory=")))
            self.app(archive)
            log.write_text("Fake UAT finished\n")
            return 0
        with self.contexts(), patch.object(package, "stream_build", side_effect=fake_build), \
                patch.object(package.subprocess, "call", return_value=7) as launch:
            self.assertEqual(package.main(["--mode", "host"]), 7)
        binary = launch.call_args.args[0][0]
        self.assertIn("Builds/PackagedPlay/Mac/", binary)
        self.assertNotIn("UnrealEditor", binary)
        self.assertEqual(launch.call_args.args[0][1], "/Game/Puzzles/Test/SixRound/L_SixRound_Test?listen")
        receipt = json.loads(next((self.root / "Saved").rglob("launch-receipt.json")).read_text())
        self.assertEqual(receipt["git"], self.identity)
        self.assertEqual(receipt["exit_code"], 7)

    def test_interrupted_build_retains_receipt_and_never_launches(self):
        with self.contexts(), patch.object(package, "stream_build", side_effect=KeyboardInterrupt), \
                patch.object(package.subprocess, "call") as launch:
            with self.assertRaises(KeyboardInterrupt):
                package.main([])
            launch.assert_not_called()
        receipt = json.loads(next((self.root / "Saved").rglob("build-receipt.json")).read_text())
        self.assertEqual(receipt["status"], "interrupted")

    def test_missing_packaged_plist_is_recorded_as_failed(self):
        def incomplete_build(command, root, log):
            archive = Path(next(arg.split("=", 1)[1] for arg in command
                                if arg.startswith("-archivedirectory=")))
            (archive / "CoopGame.app/Contents").mkdir(parents=True)
            return 0
        with self.contexts(), patch.object(package, "stream_build", side_effect=incomplete_build), \
                self.assertRaises(OSError):
            package.main([])
        receipt = json.loads(next((self.root / "Saved").rglob("build-receipt.json")).read_text())
        self.assertEqual(receipt["status"], "failed")

    def test_launch_only_needs_successful_matching_receipt_but_no_engine(self):
        archive = self.root / "Builds/PackagedPlay/Mac/existing"
        self.app(archive)
        receipt_file = self.root / "receipt.json"
        receipt = {"platform": "Mac", "status": "packaged", "archive": str(archive),
                   "map": "/Game/Maps/L_Site01",
                   "git": self.identity}
        receipt_file.write_text(json.dumps(receipt))
        with self.contexts(free_gib=0), patch.object(package, "engine_root") as engine, \
                patch.object(package.subprocess, "call", return_value=0):
            self.assertEqual(package.main(["--launch-only", str(receipt_file),
                                           "--mode", "join", "--address", "host.local"]), 0)
            engine.assert_not_called()
        with self.contexts(), patch.object(package.subprocess, "call", return_value=0) as launch:
            self.assertEqual(package.main(["--launch-only", str(receipt_file)]), 0)
            self.assertEqual(launch.call_args.args[0][1], "/Game/Maps/L_Site01")
        receipt["status"] = "failed"
        receipt_file.write_text(json.dumps(receipt))
        with self.contexts(), self.assertRaisesRegex(ValueError, "successful package"):
            package.main(["--launch-only", str(receipt_file)])

    @unittest.skipIf(os.name == "nt", "Synthetic RunUAT.sh execution requires bash")
    def test_stream_build_preserves_argv_and_failure_code(self):
        self.uat.write_text('#!/bin/bash\nprintf "%s\\n" "$1"\nexit 23\n')
        log = self.root / "fake build.log"
        with redirect_stdout(io.StringIO()):
            result = package.stream_build(["/bin/bash", str(self.uat), "argument with spaces"], self.root, log)
        self.assertEqual(result, 23)
        self.assertEqual(log.read_text(), "argument with spaces\n")


if __name__ == "__main__":
    unittest.main()
