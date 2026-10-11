#!/usr/bin/env python3
"""Build/cook/package CoopGame, then run its native Development executable."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import signal
import subprocess
import sys
import uuid


ROOT = Path(__file__).resolve().parents[1]
VERSION = "5.8.3"
MIN_FREE_GIB = 30  # Same working-space budget as Tools/check-mac.command.
MAP_PATTERN = re.compile(r"/Game/(?:[A-Za-z0-9_]+/)*[A-Za-z0-9_]+\Z")
ADDRESS_PATTERN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?(?::[0-9]{1,5})?\Z")


def native_platform():
    if sys.platform == "darwin":
        return "Mac"
    if sys.platform == "win32":
        return "Win64"
    raise ValueError("Packaging is supported on Mac or Windows, on the target machine.")


def default_map(root):
    section, selected = None, None
    for raw in (root / "Config/DefaultEngine.ini").read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            section = line
        elif section == "[/Script/EngineSettings.GameMapsSettings]" and line.startswith("GameDefaultMap="):
            selected = line.split("=", 1)[1].strip().strip('"').split(".", 1)[0]
    if not selected or not MAP_PATTERN.fullmatch(selected):
        raise ValueError("Config/DefaultEngine.ini needs a valid GameDefaultMap, or pass --map /Game/....")
    return selected


def engine_root(target, supplied=None):
    if supplied or os.environ.get("UE_ROOT"):
        candidates = [Path(supplied or os.environ["UE_ROOT"]).expanduser()]
    elif target == "Mac":
        candidates = [Path("/Users/Shared/Epic Games/UE_5.8"),
                      Path.home() / "Documents/UE_5.8"]
    else:
        candidates = [Path(os.environ.get("ProgramFiles", "C:/Program Files"))
                      / "Epic Games/UE_5.8"]
    for candidate in candidates:
        version_file = candidate / "Engine/Build/Build.version"
        if not version_file.is_file():
            continue
        version = json.loads(version_file.read_text(encoding="utf-8"))
        installed = ".".join(str(version[key]) for key in
                             ("MajorVersion", "MinorVersion", "PatchVersion"))
        if installed != VERSION:
            raise ValueError(f"Unreal {installed} found at {candidate}; expected {VERSION}.")
        uat = candidate / "Engine/Build/BatchFiles" / (
            "RunUAT.sh" if target == "Mac" else "RunUAT.bat")
        if not uat.is_file():
            raise ValueError(f"AutomationTool launcher missing: {uat}")
        return candidate.resolve(), uat.resolve()
    raise ValueError("Unreal 5.8.3 not found. Set UE_ROOT to the folder containing Engine/.")


def validate_content(root, selected_map):
    if not MAP_PATTERN.fullmatch(selected_map):
        raise ValueError("Map must be a /Game/... package path without .umap or travel options.")
    project = root / "CoopGame.uproject"
    if not project.is_file():
        raise ValueError(f"Project missing: {project}")
    if not (root / "Content" / (selected_map[6:] + ".umap")).is_file():
        raise ValueError(f"Map missing: {selected_map}. Pull the correct branch first.")
    pointers = []
    for directory in (root / "Content", root / "Plugins"):
        if not directory.exists():
            continue
        for current, dirs, files in os.walk(directory):
            dirs[:] = [name for name in dirs if name not in
                       ("Binaries", "Intermediate", "Saved", ".git")]
            for name in files:
                path = Path(current) / name
                with path.open("rb") as stream:
                    if stream.read(128).startswith(b"version https://git-lfs.github.com/spec/v1"):
                        pointers.append(str(path.relative_to(root)))
    if pointers:
        sample = ", ".join(pointers[:5])
        raise ValueError(f"{len(pointers)} unfetched Git LFS files ({sample}). Run git lfs pull.")
    return project


def git_identity(root):
    def read(*args):
        result = subprocess.run(["git", "-C", str(root), *args], capture_output=True,
                                text=True, check=True)
        return result.stdout.strip()
    return {"commit": read("rev-parse", "HEAD"),
            "branch": read("rev-parse", "--abbrev-ref", "HEAD"),
            "working_tree": read("status", "--porcelain").splitlines()}


def build_command(uat, target, project, selected_map, archive, staging):
    launcher = ["/bin/bash", str(uat)] if target == "Mac" else [str(uat)]
    return launcher + ["BuildCookRun", f"-project={project}", f"-platform={target}",
                       "-clientconfig=Development", "-unattended", "-nop4", "-utf8output",
                       "-nocompileeditor", "-build", "-cook", "-cookall",
                       f"-map={selected_map}", "-stage", "-pak", "-iostore", "-package",
                       "-archive", f"-archivedirectory={archive}",
                       f"-stagingdirectory={staging}"]


def packaged_executable(archive, target):
    if target == "Mac":
        matches = list(archive.rglob("CoopGame.app"))
        if len(matches) != 1:
            raise ValueError(f"Expected one CoopGame.app in {archive}, found {len(matches)}.")
        app = matches[0]
        with (app / "Contents/Info.plist").open("rb") as stream:
            name = plistlib.load(stream)["CFBundleExecutable"]
        executable = app / "Contents/MacOS" / name
        if executable.parent != app / "Contents/MacOS":
            raise ValueError("Unexpected executable name in packaged Info.plist.")
    else:
        # The packaged bootstrap supplies project arguments for content-only builds.
        matches = [path for path in archive.rglob("CoopGame.exe")
                   if "Binaries" not in path.relative_to(archive).parts]
        if len(matches) != 1:
            raise ValueError(f"Expected one packaged CoopGame.exe bootstrap in {archive}, found {len(matches)}.")
        executable = matches[0]
    if not executable.is_file():
        raise ValueError(f"Packaged executable missing: {executable}")
    return executable.resolve()


def game_command(executable, selected_map, mode, address, log):
    if mode == "join":
        if not address or not ADDRESS_PATTERN.fullmatch(address):
            raise ValueError("Join needs --address HOST[:PORT] (IPv4, DNS or Tailscale name).")
        port = address.rsplit(":", 1)[-1] if ":" in address else None
        if port and not 1 <= int(port) <= 65535:
            raise ValueError("Join port must be between 1 and 65535.")
        destination = address
    else:
        if address:
            raise ValueError("--address is only used with --mode join.")
        destination = selected_map + ("?listen" if mode == "host" else "")
    return [str(executable), destination, "-windowed", "-ResX=1280", "-ResY=720",
            "-log", f"-abslog={log}"]


def stop_build(process):
    """Stop only this build's descendants, including its cooker and dotnet host."""
    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       timeout=10, check=False)
    else:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
    finally:
        if os.name != "nt":
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        process.wait(timeout=5)


def stream_build(command, root, log):
    with log.open("w", encoding="utf-8") as output:
        with subprocess.Popen(command, cwd=root, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True,
                              encoding="utf-8", errors="replace",
                              start_new_session=os.name != "nt",
                              creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0) as process:
            try:
                for line in process.stdout:
                    print(line, end="", flush=True)
                    output.write(line)
                    output.flush()
                return process.wait()
            except BaseException:
                stop_build(process)
                raise


def write_receipt(path, receipt):
    path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", help="Map package path; defaults to GameDefaultMap or launch-only receipt")
    parser.add_argument("--mode", choices=("play", "host", "join"), default="play")
    parser.add_argument("--address", help="Host IP/name, optionally :port, for join")
    parser.add_argument("--engine-root", help="Unreal install folder; defaults to UE_ROOT")
    parser.add_argument("--build-only", action="store_true", help="Package without starting the game")
    parser.add_argument("--launch-only", type=Path, help="Launch an existing build-receipt.json")
    parser.add_argument("--dry-run", action="store_true", help="Check inputs and print plan; write nothing")
    args = parser.parse_args(argv)
    target = native_platform()
    if args.launch_only and args.build_only:
        raise ValueError("Choose either --launch-only or --build-only.")
    receipt = None
    if args.launch_only:
        receipt = json.loads(args.launch_only.read_text(encoding="utf-8"))
        args.map = args.map or receipt["map"]
    else:
        args.map = args.map or default_map(ROOT)
    # Validate runtime args before spending time packaging.
    if not MAP_PATTERN.fullmatch(args.map):
        raise ValueError("Map must be a /Game/... package path.")
    game_command(Path("CoopGame"), args.map, args.mode, args.address, Path("game.log"))
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    run_dir = ROOT / "Saved/PackagedPlay" / run_id
    archive = ROOT / "Builds/PackagedPlay" / target / run_id
    receipt_file = run_dir / "build-receipt.json"

    if args.launch_only:
        receipt_file = args.launch_only.resolve()
        if receipt.get("status") != "packaged" or receipt.get("platform") != target:
            raise ValueError("Receipt must describe a successful package for this machine's platform.")
        archive = Path(receipt["archive"]).resolve()
        if not archive.is_relative_to((ROOT / "Builds/PackagedPlay").resolve()):
            raise ValueError("Receipt must refer to a package in this checkout's Builds/PackagedPlay/.")
        executable = packaged_executable(archive, target)
        print(f"Using packaged commit {receipt['git']['commit']} ({target}); no rebuild.")
        # launch-only may intentionally run a prior build; show its recorded identity.
        command = game_command(executable, args.map, args.mode, args.address, run_dir / "game.log")
        print(json.dumps({"launch_argv": command, "receipt": str(receipt_file)}, indent=2))
        if args.dry_run:
            return 0
    else:
        project = validate_content(ROOT, args.map)
        engine, uat = engine_root(target, args.engine_root)
        identity = git_identity(ROOT)
        free_gib = shutil.disk_usage(ROOT).free / (1024 ** 3)
        command = build_command(uat, target, project, args.map, archive, run_dir / "stage")
        receipt = {"platform": target, "engine_version": VERSION, "engine_root": str(engine),
                   "configuration": "Development", "map": args.map, "git": identity,
                   "archive": str(archive), "build_argv": command, "status": "planned"}
        print(f"Packaging commit {identity['commit']} ({target}), free disk {free_gib:.1f} GiB.")
        if identity["working_tree"]:
            print("Working tree has local changes; the receipt records them. Save editor changes first.")
        print(json.dumps(receipt, indent=2))
        if free_gib < MIN_FREE_GIB:
            message = f"Need at least {MIN_FREE_GIB} GiB free for packaging; have {free_gib:.1f} GiB."
            if not args.dry_run:
                raise ValueError(message)
            print(f"BLOCKED: {message}")
        if args.dry_run:
            return 0
        run_dir.mkdir(parents=True)
        receipt["status"] = "building"
        write_receipt(receipt_file, receipt)
        try:
            exit_code = stream_build(command, ROOT, run_dir / "build.log")
        except (KeyboardInterrupt, OSError) as error:
            receipt["status"] = "interrupted" if isinstance(error, KeyboardInterrupt) else "failed"
            receipt["error"] = str(error) or "Build cancelled"
            write_receipt(receipt_file, receipt)
            raise
        receipt["uat_exit_code"] = exit_code
        receipt["status"] = "failed" if exit_code else "packaged"
        if not exit_code:
            try:
                executable = packaged_executable(archive, target)
                receipt["executable"] = str(executable)
            except (ValueError, OSError, KeyError) as error:
                receipt["status"] = "failed"
                receipt["error"] = str(error)
                write_receipt(receipt_file, receipt)
                raise
        write_receipt(receipt_file, receipt)
        print(f"Build receipt: {receipt_file}")
        if exit_code:
            print(f"Packaging failed ({exit_code}); build log: {run_dir / 'build.log'}", file=sys.stderr)
            return exit_code
        if args.build_only:
            print(f"Packaged app: {executable}")
            return 0
        command = game_command(executable, args.map, args.mode, args.address, run_dir / "game.log")
    run_dir.mkdir(parents=True, exist_ok=True)
    launch_receipt = {"build_receipt": str(receipt_file), "git": receipt["git"],
                      "launch_argv": command, "game_log": str(run_dir / "game.log")}
    print(f"Launching packaged app; close its window to exit. Log: {run_dir / 'game.log'}")
    launch_receipt["exit_code"] = subprocess.call(command, cwd=executable.parent)
    write_receipt(run_dir / "launch-receipt.json", launch_receipt)
    return launch_receipt["exit_code"]


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError, subprocess.CalledProcessError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("Stopped. Existing build logs/receipts are retained.", file=sys.stderr)
        sys.exit(130)
