"""Opt-in Windows socket playtests. Python 3.9+, standard library only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone
from contextlib import contextmanager

BRANCH = "codex/hc-windows-session-qa"
ROOT = Path(__file__).resolve().parents[3]
ERROR = re.compile(
    r"\b(?:Error|Fatal|Fatal error):|Accessed None|Assertion failed|"
    r"Ensure condition failed|Unhandled Exception|NetworkFailure|TravelFailure|"
    r"Failed to load|Failed to find object|Connection TIMED OUT|"
    r"Connection refused|NetVersionMismatch", re.I)
CHECKS = (
    "commit_engine_agreement", "windows_socket_join", "player_count_scaling",
    "client_move_jump", "local_input_hud", "physical_gamepad_routing",
    "relic_totals", "late_join", "duplicate_pickup", "carrying",
    "first_puzzle", "f4_site02", "f4_return_site01", "travel_input_hud",
    "startup_runtime_logs", "both_macs_join")


class Refusal(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise Refusal(message)


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest() if hasattr(
            hashlib, "file_digest") else _digest_stream(stream)


def _digest_stream(stream):
    result = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        result.update(block)
    return result.hexdigest()


def git(root, *args):
    return subprocess.run(["git", "-C", str(root), *args], check=True,
                          capture_output=True, text=True, timeout=30).stdout.strip()


def utc():
    return datetime.now(timezone.utc).isoformat()


def powershell(script):
    require(os.name == "nt", "Windows is required for process inspection/launch.")
    # Fixed read-only scripts only. No user values or shell command interpolation.
    result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive",
                             "-Command", script], check=True, capture_output=True,
                            text=True, timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
    return json.loads(result.stdout.strip() or "[]")


def processes():
    return powershell("$ErrorActionPreference='Stop'; ConvertTo-Json -Compress -InputObject @("
        "Get-CimInstance Win32_Process -Filter \"Name LIKE 'UnrealEditor%'\" | "
        "Select-Object ProcessId,CommandLine,CreationDate,ExecutablePath)")


def owned_project_processes(rows, project):
    project = str(project).replace("/", "\\").casefold()
    matches = []
    for row in rows:
        require(row.get("CommandLine") is not None,
                "An Unreal process has an unreadable command line; cannot prove isolation.")
        args = row["CommandLine"].replace("/", "\\").casefold()
        if project in args:
            matches.append(row)
    return matches


def output_dir(root, run):
    require(re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}", run), "Invalid run ID.")
    path = root.resolve() / "Saved" / "WindowsSessionQA" / run
    require(path.resolve() == path, "Report path contains a symlink/junction or escapes worktree.")
    return path


@contextmanager
def lease(root):
    base = output_dir(root, "tooling").parent
    base.mkdir(parents=True, exist_ok=True)
    lock = base / "launch.lock"
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    except FileExistsError:
        raise Refusal("Another harness operation holds launch.lock. Inspect before removing it.")
    try:
        os.close(fd)
        yield
    finally:
        lock.unlink()


def preflight(root, candidate, engine):
    root, engine = root.resolve(), engine.resolve()
    require((root / ".git").is_file(), "Use the dedicated Git worktree, not the original checkout.")
    require(git(root, "rev-parse", "--show-toplevel").replace("\\", "/").casefold()
            == root.as_posix().casefold(), "Root is not the Git worktree root.")
    require(git(root, "branch", "--show-current") == BRANCH, "Wrong QA branch.")
    require(re.fullmatch(r"[0-9a-f]{40}", candidate), "Supply a full lowercase 40-character candidate SHA.")
    require(git(root, "rev-parse", "HEAD") == candidate, "HEAD differs from agreed candidate.")
    require(not git(root, "status", "--porcelain", "--untracked-files=all"),
            "Worktree has tracked/untracked changes; commit or resolve them before launch.")
    project = root / "CoopGame.uproject"
    require(project.is_file(), "Missing CoopGame.uproject.")
    require(json.loads(project.read_text(encoding="utf-8-sig"))["EngineAssociation"] == "5.8",
            "Project engine association differs from 5.8.")
    version_file = engine / "Engine/Build/Build.version"
    version = json.loads(version_file.read_text(encoding="utf-8-sig"))
    require(tuple(version.get(k) for k in ("MajorVersion", "MinorVersion", "PatchVersion"))
            == (5, 8, 3), "Exact Unreal 5.8.3 is required.")
    exe = engine / "Engine/Binaries/Win64/UnrealEditor.exe"
    require(exe.is_file(), "Missing Win64 UnrealEditor.exe.")
    # Startup safety only; not a repeat of the source-asset validator's green gates.
    assets = git(root, "ls-files", "-z", "Content/*.uasset", "Content/*.umap").split("\0")
    for name in filter(None, assets):
        with (root / name).open("rb") as stream:
            require(not stream.read(80).startswith(b"version https://git-lfs.github.com/spec/v1"),
                    "Unhydrated runtime asset: " + name)
    return {"root": str(root), "candidate": candidate,
            "tree": git(root, "rev-parse", "HEAD^{tree}"),
            "project": str(project), "project_sha256": digest(project),
            "engine": str(engine), "engine_version": version,
            "engine_build_sha256": digest(version_file),
            "editor_sha256": digest(exe), "harness_sha256": digest(Path(__file__)),
            "exe": str(exe)}


def command(identity, role, port, directory):
    address = "/Game/Maps/L_Site01?listen" if role == "host" else "127.0.0.1:" + str(port)
    args = [identity["exe"], identity["project"], address, "-game", "-DisablePython",
            "-windowed", "-ResX=1280", "-ResY=720", "-nosplash", "-nop4",
            "-abslog=" + str(directory / (role + ".log"))]
    if role == "host":
        args.append("-port=" + str(port))
    return args


def init_run(root, candidate, engine, run, players, locals_count, port):
    require(players in (2, 3, 4) and locals_count in (1, 2), "Counts must be 2/3/4 total, 1/2 local.")
    require(players > locals_count, "This Windows socket slice requires a separate client.")
    require(1024 <= port <= 65535, "Port must be 1024..65535.")
    identity = preflight(root, candidate, engine)
    require(not owned_project_processes(processes(), identity["project"]),
            "A worktree Unreal instance is running. Close only your own instance before preparing a run.")
    directory = output_dir(root, run)
    directory.mkdir(parents=True, exist_ok=False)
    roles = ["host"] + ["client" + str(i) for i in range(1, players - locals_count + 1)]
    manifest = {**identity, "created_utc": utc(), "run": run, "players": players,
                "host_local_players": locals_count, "port": port,
                "roles": roles, "launches": {}}
    write_json(directory / "manifest.json", manifest)
    write_json(directory / "observations.json", {key: {"status": "pending", "evidence": ""}
                                               for key in CHECKS})
    return manifest


def write_json(path, value):
    # Callers decide whether this is a new artifact or an updated launch ledger.
    Path(path).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def load_run(root, run):
    directory = output_dir(root, run)
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    require(manifest["root"] == str(root.resolve()) and manifest["run"] == run,
            "Manifest belongs to another worktree/run.")
    expected_roles = ["host"] + ["client" + str(i) for i in range(
        1, manifest["players"] - manifest["host_local_players"] + 1)]
    require(manifest["players"] in (2, 3, 4) and manifest["host_local_players"] in (1, 2)
            and manifest["players"] > manifest["host_local_players"], "Invalid manifest counts.")
    require(manifest["roles"] == expected_roles and 1024 <= manifest["port"] <= 65535,
            "Invalid manifest topology.")
    return directory, manifest


def check_identity(root, manifest):
    current = preflight(root, manifest["candidate"], Path(manifest["engine"]))
    for key, value in current.items():
        require(manifest[key] == value, "Run identity changed: " + key)


def launch(root, run, role, opt_in=False, host_ready=False):
    require(opt_in, "Launching requires --launch. Plan is the default.")
    directory, manifest = load_run(root, run)
    check_identity(root, manifest)
    require(role in manifest["roles"], "Role not in planned topology.")
    require(role not in manifest["launches"], "Role already launched; use a fresh run for retries.")
    require(not (directory / (role + ".log")).exists(), "Role log already exists; refusing overwrite.")
    own = owned_project_processes(processes(), manifest["project"])
    launched = manifest["launches"]
    for row in own:
        require(any(row["ProcessId"] == item["pid"] and row["CreationDate"] == item["creation"]
                    for item in launched.values()), "Unregistered worktree instance is running.")
    if role == "host":
        # Read OS bindings: do not bind/probe a socket or disturb another session.
        bindings = powershell("$ErrorActionPreference='Stop'; ConvertTo-Json -Compress "
                              "-InputObject @(Get-NetUDPEndpoint | Select-Object LocalPort)")
        require(not any(row["LocalPort"] == manifest["port"] for row in bindings),
                "Host UDP port is in use; choose a new run/port.")
    else:
        require(host_ready and "host" in launched, "Confirm native host readiness with --host-ready.")
        require(any(row["ProcessId"] == launched["host"]["pid"] and
                    row["CreationDate"] == launched["host"]["creation"] for row in own),
                "This run's host is no longer running.")
    args = command(manifest, role, manifest["port"], directory)
    child = spawn(args, root)
    # Never kill on error; preserve PID/arguments even if startup fails before inspection.
    launched[role] = {"pid": child.pid, "creation": None, "utc": utc(), "argv": args}
    write_json(directory / "manifest.json", manifest)
    rows = owned_project_processes(processes(), manifest["project"])
    row = next((row for row in rows if row["ProcessId"] == child.pid), None)
    require(row is not None, "Process exited or cannot be inspected; inspect ledger/log, then use a new run.")
    launched[role]["creation"] = row["CreationDate"]
    write_json(directory / "manifest.json", manifest)
    return launched[role]


def spawn(args, root):
    return subprocess.Popen(args, cwd=str(root), creationflags=subprocess.CREATE_NO_WINDOW)


def scan_log(path):
    if not path.is_file():
        return {"status": "missing", "errors": [], "warnings": [], "sha256": None}
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    findings = [{"line": i, "text": line} for i, line in enumerate(lines, 1) if ERROR.search(line)]
    warnings = [{"line": i, "text": line} for i, line in enumerate(lines, 1)
                if re.search(r"\bWarning:", line, re.I) and not ERROR.search(line)]
    return {"status": "errors" if findings else "review" if lines else "empty",
            "errors": findings, "warnings": warnings, "sha256": digest(path),
            "lines": len(lines)}


def report(root, run):
    directory, manifest = load_run(root, run)
    check_identity(root, manifest)
    own = owned_project_processes(processes(), manifest["project"])
    live = [r["ProcessId"] for r in own]
    logs = {role: scan_log(directory / (role + ".log")) for role in manifest["roles"]}
    observations = json.loads((directory / "observations.json").read_text(encoding="utf-8"))
    require(set(observations) == set(CHECKS), "Observation checklist is incomplete/unknown.")
    for key, item in observations.items():
        require(item["status"] in ("pending", "pass", "fail", "blocked"), "Invalid status for " + key)
        require(item["status"] == "pending" or str(item["evidence"]).strip(), "Missing evidence for " + key)
    errors = any(log["errors"] for log in logs.values())
    missing = any(log["status"] in ("missing", "empty") for log in logs.values())
    pending = any(item["status"] in ("pending", "blocked") for item in observations.values())
    failed = any(item["status"] == "fail" for item in observations.values())
    unlaunched = set(manifest["roles"]) - set(manifest["launches"])
    status = "fail" if errors or failed else "pending" if live or missing or pending or unlaunched else "recorded"
    result = {"status": status, "candidate": manifest["candidate"], "created_utc": utc(),
              "manifest_sha256": digest(directory / "manifest.json"),
              "observations_sha256": digest(directory / "observations.json"),
              "live_worktree_pids": live, "unlaunched_roles": sorted(unlaunched),
              "logs": logs, "observations": observations,
              "scope": "Human observations; log scan never proves gameplay or Mac compatibility. HC-7 separate."}
    filename = "report-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + ".json"
    with (directory / filename).open("x", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    init = sub.add_parser("prepare", help="Preflight and create pending evidence; does not launch.")
    init.add_argument("--candidate", required=True)
    init.add_argument("--engine", type=Path, default=Path(os.environ.get(
        "UE_ROOT", r"C:\Program Files\Epic Games\UE_5.8")))
    init.add_argument("--players", type=int, choices=(2, 3, 4), required=True)
    init.add_argument("--host-local", type=int, choices=(1, 2), default=1)
    init.add_argument("--port", type=int, default=17777)
    for name in ("plan", "start", "check"):
        p = sub.add_parser(name)
        if name == "start":
            p.add_argument("--role", required=True)
            p.add_argument("--launch", action="store_true")
            p.add_argument("--host-ready", action="store_true")
    for p in sub.choices.values():
        p.add_argument("--run", required=True)
    args = parser.parse_args()
    try:
        if args.action == "prepare":
            with lease(ROOT):
                result = init_run(ROOT, args.candidate, args.engine, args.run,
                                  args.players, args.host_local, args.port)
        elif args.action == "start":
            with lease(ROOT):
                result = launch(ROOT, args.run, args.role, args.launch, args.host_ready)
        elif args.action == "plan":
            directory, manifest = load_run(ROOT, args.run)
            check_identity(ROOT, manifest)
            result = {role: command(manifest, role, manifest["port"], directory)
                      for role in manifest["roles"]}
        else:
            with lease(ROOT):
                result = report(ROOT, args.run)
        print(json.dumps(result, indent=2))
        return 1 if result.get("status") == "fail" else 2 if result.get("status") == "pending" else 0
    except (Refusal, OSError, KeyError, TypeError, ValueError, subprocess.SubprocessError) as error:
        print("REFUSED: " + str(error), file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
