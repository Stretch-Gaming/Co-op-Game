"""Isolated tooling tests: temporary Git worktrees, fake engine, mocked OS/launch."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import session as qa


class SessionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Temporary fixtures never use the project's assets, engine or network.
        cls.temp = tempfile.TemporaryDirectory(prefix="coop-session-fixture-")
        cls.base = Path(cls.temp.name)
        origin = cls.base / "original"
        origin.mkdir()
        qa.git(origin, "init", "-q")
        qa.git(origin, "config", "user.name", "Fixture")
        qa.git(origin, "config", "user.email", "fixture@example.invalid")
        (origin / "CoopGame.uproject").write_text('{"EngineAssociation":"5.8"}')
        (origin / ".gitignore").write_text("Saved/\n")
        (origin / "Content").mkdir()
        (origin / "Content/test.uasset").write_bytes(b"fake fixture only")
        qa.git(origin, "add", ".")
        qa.git(origin, "commit", "-qm", "Fixture")
        cls.root = cls.base / "QA worktree with spaces"
        qa.git(origin, "worktree", "add", "-b", qa.BRANCH, str(cls.root))
        cls.sha = qa.git(cls.root, "rev-parse", "HEAD")
        cls.engine = cls.base / "Fake engine with spaces"
        cls.version = cls.engine / "Engine/Build/Build.version"
        cls.version.parent.mkdir(parents=True)
        cls.version.write_text(json.dumps({"MajorVersion": 5, "MinorVersion": 8, "PatchVersion": 3}))
        cls.exe = cls.engine / "Engine/Binaries/Win64/UnrealEditor.exe"
        cls.exe.parent.mkdir(parents=True)
        cls.exe.write_bytes(b"not an executable; fixture only")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.proc = patch.object(qa, "processes", return_value=[])
        self.proc.start()
        self.addCleanup(self.proc.stop)
        self.run = self.id().split(".")[-1][:60]

    def prepare(self, players=3, local=1):
        return qa.init_run(self.root, self.sha, self.engine, self.run, players, local, 17777)

    def test_exact_identity_and_plan_does_not_spawn(self):
        with patch.object(qa, "spawn") as spawn:
            manifest = self.prepare()
            argv = qa.command(manifest, "host", 17777, qa.output_dir(self.root, self.run))
        spawn.assert_not_called()
        self.assertEqual(manifest["candidate"], self.sha)
        self.assertEqual(manifest["roles"], ["host", "client1", "client2"])
        self.assertEqual(argv[:4], [str(self.exe), str(self.root / "CoopGame.uproject"),
                                  "/Game/Maps/L_Site01?listen", "-game"])
        self.assertIn("-DisablePython", argv)
        self.assertIn("-port=17777", argv)
        self.assertEqual(len(manifest["editor_sha256"]), 64)

    def test_all_socket_topologies(self):
        for players, local in ((2, 1), (3, 1), (4, 1), (3, 2), (4, 2)):
            m = qa.init_run(self.root, self.sha, self.engine, self.run + str(players) + str(local),
                            players, local, 17777)
            self.assertEqual(len(m["roles"]), players - local + 1)
        with self.assertRaises(qa.Refusal):
            self.prepare(2, 2)

    def test_wrong_sha_and_abbreviation_refused(self):
        for sha in ("a" * 40, self.sha[:7], "HEAD", self.sha.upper()):
            with self.assertRaises(qa.Refusal):
                qa.preflight(self.root, sha, self.engine)

    def test_original_checkout_refused(self):
        with self.assertRaises(qa.Refusal):
            qa.preflight(self.base / "original", self.sha, self.engine)

    def test_wrong_branch_refused(self):
        qa.git(self.root, "switch", "-c", "fixture-wrong")
        try:
            with self.assertRaises(qa.Refusal):
                qa.preflight(self.root, self.sha, self.engine)
        finally:
            qa.git(self.root, "switch", qa.BRANCH)

    def test_dirty_tracked_and_untracked_refused(self):
        for name in ("CoopGame.uproject", "unknown.txt"):
            path = self.root / name
            old = path.read_bytes() if path.exists() else None
            try:
                path.write_bytes(b"dirty")
                with self.assertRaises(qa.Refusal):
                    qa.preflight(self.root, self.sha, self.engine)
            finally:
                if old is None:
                    path.unlink()
                else:
                    path.write_bytes(old)

    def test_wrong_engine_and_changed_engine_refused(self):
        m = self.prepare()
        old = self.version.read_bytes()
        try:
            self.version.write_text('{"MajorVersion":5,"MinorVersion":8,"PatchVersion":2}')
            with self.assertRaises(qa.Refusal):
                qa.preflight(self.root, self.sha, self.engine)
            self.version.write_bytes(old + b"\n")
            with self.assertRaises(qa.Refusal):
                qa.check_identity(self.root, m)
        finally:
            self.version.write_bytes(old)

    def test_missing_executable_refused(self):
        moved = self.exe.with_suffix(".fixture")
        self.exe.rename(moved)
        try:
            with self.assertRaises(qa.Refusal):
                qa.preflight(self.root, self.sha, self.engine)
        finally:
            moved.rename(self.exe)

    def test_unhydrated_runtime_pointer_refused(self):
        asset = self.root / "Content/test.uasset"
        old = asset.read_bytes()
        asset.write_bytes(b"version https://git-lfs.github.com/spec/v1\n")
        # Isolate the hydration gate from the earlier dirty-check gate.
        original_git = qa.git
        def clean_git(root, *args):
            return "" if args[0] == "status" else original_git(root, *args)
        try:
            with patch.object(qa, "git", side_effect=clean_git), self.assertRaisesRegex(
                    qa.Refusal, "Unhydrated"):
                qa.preflight(self.root, self.sha, self.engine)
        finally:
            asset.write_bytes(old)

    def test_path_traversal_and_invalid_runs_refused(self):
        for run in ("../other", "a/b", "", "x;quit", "a" * 65):
            with self.assertRaises(qa.Refusal):
                qa.output_dir(self.root, run)

    def test_no_run_overwrite_and_launch_requires_opt_in(self):
        self.prepare()
        with self.assertRaises(FileExistsError):
            self.prepare()
        with patch.object(qa, "spawn") as spawn, self.assertRaises(qa.Refusal):
            qa.launch(self.root, self.run, "host")
        spawn.assert_not_called()

    def test_process_isolation_and_unreadable_process(self):
        unrelated = {"CommandLine": '"C:\\Other\\CoopGame.uproject"', "ProcessId": 1}
        self.assertEqual(qa.owned_project_processes([unrelated], self.root / "CoopGame.uproject"), [])
        own = {"CommandLine": str(self.root / "CoopGame.uproject"), "ProcessId": 2}
        with patch.object(qa, "processes", return_value=[own]), self.assertRaises(qa.Refusal):
            self.prepare()
        with self.assertRaises(qa.Refusal):
            qa.owned_project_processes([{"CommandLine": None}], self.root / "CoopGame.uproject")

    def test_unknown_worktree_instance_blocks_launch(self):
        self.prepare()
        own = {"CommandLine": str(self.root / "CoopGame.uproject"), "ProcessId": 22,
               "CreationDate": "other-session"}
        with patch.object(qa, "processes", return_value=[own]), patch.object(
                qa, "spawn") as spawn, self.assertRaises(qa.Refusal):
            qa.launch(self.root, self.run, "host", True)
        spawn.assert_not_called()

    def test_busy_port_and_client_readiness_refused(self):
        self.prepare()
        with patch.object(qa, "powershell", return_value=[{"LocalPort": 17777}]), patch.object(
                qa, "spawn") as spawn, self.assertRaises(qa.Refusal):
            qa.launch(self.root, self.run, "host", True)
        spawn.assert_not_called()
        with self.assertRaises(qa.Refusal):
            qa.launch(self.root, self.run, "client1", True)

    def test_mocked_launch_pid_ledger_and_reuse_refused(self):
        self.prepare()
        row = {"CommandLine": str(self.root / "CoopGame.uproject"),
               "ProcessId": 456, "CreationDate": "fixture-time"}
        with patch.object(qa, "processes", side_effect=[[], [row]]), patch.object(
                qa, "powershell", return_value=[]), patch.object(qa, "spawn") as spawn:
            spawn.return_value.pid = 456
            qa.launch(self.root, self.run, "host", True)
            self.assertIsInstance(spawn.call_args.args[0], list)
            self.assertEqual(spawn.call_args.args[1], self.root)
        _, manifest = qa.load_run(self.root, self.run)
        self.assertEqual(manifest["launches"]["host"]["creation"], "fixture-time")
        with self.assertRaises(qa.Refusal):
            qa.launch(self.root, self.run, "host", True)

    def test_pid_reuse_blocks_client(self):
        m = self.prepare()
        m["launches"]["host"] = {"pid": 456, "creation": "original"}
        qa.write_json(qa.output_dir(self.root, self.run) / "manifest.json", m)
        row = {"CommandLine": m["project"], "ProcessId": 456, "CreationDate": "reused"}
        with patch.object(qa, "processes", return_value=[row]), self.assertRaises(qa.Refusal):
            qa.launch(self.root, self.run, "client1", True, True)

    def test_lease_blocks_concurrent_launch(self):
        with qa.lease(self.root), self.assertRaises(qa.Refusal):
            with qa.lease(self.root):
                self.fail("Second writer entered")

    def test_missing_empty_clean_logs_never_prove_session(self):
        m = self.prepare()
        directory = qa.output_dir(self.root, self.run)
        self.assertEqual(qa.report(self.root, self.run)["status"], "pending")
        for role in m["roles"]:
            (directory / (role + ".log")).write_text("")
        self.assertEqual(qa.report(self.root, self.run)["status"], "pending")
        for role in m["roles"]:
            (directory / (role + ".log")).write_text("LogInit: Engine Version: 5.8.3\nLogWorld: loaded\n")
        result = qa.report(self.root, self.run)
        self.assertEqual(result["status"], "pending")
        self.assertEqual(result["observations"]["both_macs_join"]["status"], "pending")
        self.assertEqual(result["observations"]["physical_gamepad_routing"]["status"], "pending")
        self.assertEqual(len(list(directory.glob("report-*.json"))), 3)

    def test_startup_and_runtime_errors_fail_report(self):
        self.prepare()
        path = qa.output_dir(self.root, self.run) / "host.log"
        cases = ["LogInit: Error: startup", "LogBlueprint: Warning: Accessed None",
                 "Fatal error: crash", "Ensure condition failed: bad", "TravelFailure: failed",
                 "LogNet: Connection TIMED OUT", "LogLinker: Failed to load asset"]
        path.write_text("\n".join(cases))
        result = qa.report(self.root, self.run)
        self.assertEqual(result["status"], "fail")
        self.assertEqual(len(result["logs"]["host"]["errors"]), len(cases))
        self.assertEqual(result["logs"]["host"]["errors"][1]["line"], 2)

    def test_warnings_preserved_and_pass_requires_evidence(self):
        self.prepare()
        directory = qa.output_dir(self.root, self.run)
        (directory / "host.log").write_text("LogTest: Warning: inspect manually\n")
        self.assertEqual(len(qa.report(self.root, self.run)["logs"]["host"]["warnings"]), 1)
        path = directory / "observations.json"
        observations = json.loads(path.read_text())
        observations["both_macs_join"]["status"] = "pass"
        qa.write_json(path, observations)
        with self.assertRaisesRegex(qa.Refusal, "Missing evidence"):
            qa.report(self.root, self.run)

    def test_manifest_tampering_refused(self):
        m = self.prepare()
        m["root"] = "some other checkout"
        qa.write_json(qa.output_dir(self.root, self.run) / "manifest.json", m)
        with self.assertRaises(qa.Refusal):
            qa.load_run(self.root, self.run)

    def test_spawn_adapter_uses_argv_without_shell(self):
        argv = [str(self.exe), str(self.root / "CoopGame.uproject"), "127.0.0.1:17777"]
        with patch.object(qa.subprocess, "Popen") as popen:
            qa.spawn(argv, self.root)
        self.assertEqual(popen.call_args.args, (argv,))
        self.assertEqual(popen.call_args.kwargs["cwd"], str(self.root))
        self.assertNotIn("shell", popen.call_args.kwargs)
        self.assertEqual(popen.call_args.kwargs["creationflags"], qa.subprocess.CREATE_NO_WINDOW)

    def test_inside_root_reparse_path_refused(self):
        original = Path.resolve
        def redirect(path, *args, **kwargs):
            if path.name == "redirected-run":
                return self.root / "Content" / "redirected-run"
            return original(path, *args, **kwargs)
        with patch.object(Path, "resolve", redirect), self.assertRaises(qa.Refusal):
            qa.output_dir(self.root, "redirected-run")

    def test_role_log_cannot_be_overwritten(self):
        self.prepare()
        (qa.output_dir(self.root, self.run) / "host.log").write_text("preserve")
        with patch.object(qa, "spawn") as spawn, self.assertRaises(qa.Refusal):
            qa.launch(self.root, self.run, "host", True)
        spawn.assert_not_called()

    def test_live_or_unlaunched_roles_keep_completed_observations_pending(self):
        m = self.prepare()
        directory = qa.output_dir(self.root, self.run)
        observations = {key: {"status": "pass", "evidence": "synthetic fixture, not gameplay"}
                        for key in qa.CHECKS}
        qa.write_json(directory / "observations.json", observations)
        for role in m["roles"]:
            (directory / (role + ".log")).write_text("synthetic fixture\n")
        self.assertEqual(qa.report(self.root, self.run)["status"], "pending")
        m["launches"] = {role: {"pid": i, "creation": "fixture"}
                         for i, role in enumerate(m["roles"], 100)}
        qa.write_json(directory / "manifest.json", m)
        row = {"CommandLine": m["project"], "ProcessId": 100, "CreationDate": "fixture"}
        with patch.object(qa, "processes", return_value=[row]):
            self.assertEqual(qa.report(self.root, self.run)["status"], "pending")
        result = qa.report(self.root, self.run)
        self.assertEqual(result["status"], "recorded")
        self.assertEqual(len(result["manifest_sha256"]), 64)

    def test_failed_process_registration_preserves_ledger(self):
        self.prepare()
        with patch.object(qa, "powershell", return_value=[]), patch.object(qa, "spawn") as spawn:
            spawn.return_value.pid = 789
            with self.assertRaises(qa.Refusal):
                qa.launch(self.root, self.run, "host", True)
        _, m = qa.load_run(self.root, self.run)
        self.assertEqual(m["launches"]["host"]["pid"], 789)
        self.assertIsNone(m["launches"]["host"]["creation"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
