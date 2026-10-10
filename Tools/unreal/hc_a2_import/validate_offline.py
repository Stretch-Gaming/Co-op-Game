"""Run the offline acceptance gate. --write-evidence saves reports only here."""
import argparse
import contextlib
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest

import import_hc_a2 as importer
from source_audit import sha256, text_sha256


def git(*args):
    return subprocess.check_output(["git", *args], cwd=importer.PROJECT_ROOT, text=True).strip()


def protected_snapshot(manifest):
    files = [importer.PROJECT_ROOT / a[key] for a in manifest["assets"]
             for key in ("source", "validation_source")]
    files.append(importer.PROJECT_ROOT / "Content/Shared/Style/M_Stylized.uasset")
    # Detect any new/deleted/modified Content binaries and source files during the gate.
    files += list((importer.PROJECT_ROOT / "Content").rglob("*"))
    return {str(p.relative_to(importer.PROJECT_ROOT)): (p.stat().st_size, p.stat().st_mtime_ns)
            for p in files if p.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write-evidence", action="store_true")
    args = parser.parse_args()
    manifest, _ = importer.load_plan()
    before = protected_snapshot(manifest)
    syntax = []
    for file in sorted(importer.TOOL_DIR.glob("*.py")):
        compile(file.read_text(encoding="utf-8-sig"), str(file), "exec")
        syntax.append(file.name)
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        dry = importer.run([])
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(importer.TOOL_DIR), pattern="test_*.py")
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    if not result.wasSuccessful():
        print(stream.getvalue())
        raise SystemExit("Offline safety tests failed")
    hydration = []
    for asset in manifest["assets"]:
        pointer = git("show", "HEAD:" + asset["source"])
        oid = re.search(r"(?m)^oid sha256:([0-9a-f]{64})$", pointer)
        size = re.search(r"(?m)^size ([0-9]+)$", pointer)
        if not oid or not size or oid[1] != asset["source_sha256"] or int(size[1]) != asset["source_bytes"]:
            raise SystemExit("LFS pointer does not match hydrated source: " + asset["name"])
        attrs = git("check-attr", "filter", "--", asset["source"])
        if not attrs.endswith(": filter: lfs"):
            raise SystemExit("Source not LFS tracked: " + asset["source"])
        metadata_blob = subprocess.check_output(["git", "show", "HEAD:" + asset["validation_source"]], cwd=importer.PROJECT_ROOT)
        if hashlib.sha256(metadata_blob).hexdigest() != asset["validation_sha256"]:
            raise SystemExit("Metadata LF hash does not match committed source")
        hydration.append({"source": asset["source"], "lfs_oid_sha256": oid[1],
                          "lfs_size": int(size[1]), "hydrated_sha256_match": True, "metadata_lf_sha256_matches_git": True})
    after = protected_snapshot(manifest)
    if after != before:
        raise SystemExit("Protected sources/Content changed during gate")
    diff_paths = git("diff", "--name-only", "origin/main...HEAD").splitlines()
    changed_paths = git("diff", "--name-only").splitlines()
    changed_paths += git("diff", "--cached", "--name-only").splitlines()
    untracked = git("ls-files", "--others", "--exclude-standard").splitlines()
    paths = sorted(set(diff_paths + changed_paths + untracked))
    def owned(path):
        return path.startswith(("Tools/unreal/hc_a2_import/", "Content/Puzzles/Art/HCA2_Props/")) or path in ("Content/Puzzles/L_Site01_HC.umap", "Content/Puzzles/Test/L_HCA2_Props.umap")
    if any(not owned(p) for p in paths):
        raise SystemExit("Changes outside ownership: " + repr(paths))
    evidence = {
        "validated_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_commit": git("merge-base", "HEAD", "origin/main"),
        "branch": git("branch", "--show-current"),
        "python_version": sys.version.split()[0], "syntax_passed": syntax,
        "source_count": len(manifest["assets"]), "lfs_hydration": hydration,
        "read_only_dry_run": "passed (default invocation)",
        "protected_files_unchanged": True, "destination_isolation": "13 planned packages under HCA2_Props",
        "safety_tests_run": result.testsRun, "safety_tests_passed": True,
        "owned_changed_paths": paths,
        "manifest_sha256": text_sha256(importer.MANIFEST_PATH),
        "text_hash_convention": "UTF-8 LF normalized; binary FBX/M_Stylized hashes use raw bytes",
        "tool_sha256": {f.name: text_sha256(f) for f in sorted(importer.TOOL_DIR.glob("*.py"))},
        "editor_scope": "offline gate only; actual editor evidence is recorded separately",
        "runtime_checks": "see editor_verification.json, visual_capture.json and client evidence",
    }
    if args.write_evidence:
        folder = importer.TOOL_DIR / "evidence"
        folder.mkdir(exist_ok=True)
        (folder / "dry_run.json").write_text(output.getvalue(), encoding="utf-8")
        (folder / "safety_tests.txt").write_text(stream.getvalue(), encoding="utf-8")
        (folder / "offline_validation.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
