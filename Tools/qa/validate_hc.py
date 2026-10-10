#!/usr/bin/env python3
"""Offline HC repository/source checks. Python 3.9+, standard library only."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PureWindowsPath
import re
import struct
import subprocess
import sys
import zlib

ASSET_EXTENSIONS = set("""
.uasset .umap .fbx .glb .obj .blend .psd .gltf .bin .usd .usdc .usdz
.tif .tiff .webp .png .jpg .jpeg .tga .exr .hdr .wav .mp3 .ogg .mp4 .ttf .otf
""".split())
MESH_EXTENSIONS = {".fbx", ".glb", ".obj", ".blend", ".gltf", ".usd", ".usdc", ".usdz"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp", ".tga", ".exr", ".hdr", ".psd"}
PREFIXES = "BP BPI AC AIC WBP E S DT DA IA IMC L SM SK M MI T SFX MS".split()
LFS_HEADER = b"version https://git-lfs.github.com/spec/v1"
HASH = re.compile(r"[0-9a-fA-F]{64}")
TASK = re.compile(r"HC-A[1-9][0-9]*")
LIMITATIONS = [
    "Blender export dimensions, bounds, triangles, pivots, units and axes are recorded claims; FBX geometry is not measured.",
    "Gate opening dimensions are not full mesh bounds; no 400 cm full-bounds assertion is made.",
    "PNG checks inspect IHDR only, not pixels, actual alpha, image decoding or visual readability.",
    "Unreal import settings, materials, collision, Nanite, client/split-screen behavior and appearance require editor review.",
    "No network access: issue provenance and licensing terms are not fetched or legally verified.",
]

class MetadataError(ValueError):
    pass

def number(value):
    try:
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    except OverflowError:
        return False

def integer(value):
    return isinstance(value, int) and not isinstance(value, bool)

def vector(value, length, positive=False):
    return (isinstance(value, list) and len(value) == length and
            all(number(x) and (not positive or x > 0) for x in value))

def require(condition, message):
    if not condition:
        raise MetadataError(message)

def object_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result

def finite_float(value):
    result = float(value)
    require(math.isfinite(result), "non-finite JSON number: " + value)
    return result

def read_json(path):
    require(path.stat().st_size <= 2 * 1024 * 1024, "metadata exceeds 2 MiB")
    return json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=object_pairs, parse_float=finite_float,
                      parse_constant=lambda x: (_ for _ in ()).throw(MetadataError("non-finite JSON number: " + x)))

def pointer(data):
    """Return (oid, size) or None; pointer-looking corrupt data must not be an asset."""
    if not data.startswith(b"version https://git-lfs.github.com/"):
        return None
    match = re.fullmatch(
        rb"version https://git-lfs.github.com/spec/v1\r?\n"
        rb"oid sha256:([0-9a-f]{64})\r?\nsize ([0-9]+)\r?\n?", data)
    require(match is not None, "malformed or unsupported LFS pointer")
    return match[1].decode("ascii"), int(match[2])

class Validator:
    def __init__(self, repository, task=None):
        self.repo = Path(repository).resolve()
        self.task = task
        self.findings = []
        self.facts = []
        self.assets = set()
        self.file_cache = {}
        self.records = set()
        self.digest_cache = {}
        self.provenance_tasks = set()

    def label(self, path):
        try:
            return Path(path).relative_to(self.repo).as_posix()
        except ValueError:
            return str(path)

    def finding(self, code, path, message, severity="error", basis="repository"):
        self.findings.append(dict(severity=severity, code=code, path=self.label(path),
                                  basis=basis, message=message))

    def fact(self, path, kind, value, basis="recorded"):
        self.facts.append(dict(path=self.label(path), kind=kind, basis=basis, value=value))

    def git(self, *args, data=None):
        env = os.environ.copy()
        env["GIT_OPTIONAL_LOCKS"] = "0"
        result = subprocess.run(["git", "-C", str(self.repo), *args], input=data,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env=env, timeout=30, check=False)
        if result.returncode:
            raise MetadataError("read-only Git query failed: " + result.stderr.decode("utf-8", "replace").strip())
        return result.stdout

    def safe_path(self, value, base=None):
        require(isinstance(value, str) and value.strip(), "file path must be a nonempty string")
        value = value.replace("\\", "/")
        require(":" not in value, "referenced file cannot be a URL or drive path")
        win = PureWindowsPath(value)
        require(not Path(value).is_absolute() and not win.drive and not win.root,
                "referenced file must be repository-relative: " + value)
        path = ((base or self.repo) / value).resolve()
        require(path.is_relative_to(self.repo), "referenced file escapes repository: " + value)
        return path

    def recorded_path(self, value, record):
        # cleanup_export writes repository-root-relative outputs; HUD records are sibling-relative.
        if isinstance(value, str) and value.replace("\\", "/").startswith(("SourceArt/", "Content/")):
            return self.safe_path(value)
        return self.safe_path(value, record.parent)

    def selected(self, path):
        parts = path.relative_to(self.repo).parts
        tasks = [p for p in parts if TASK.fullmatch(p)]
        return self.task is None or self.task in tasks

    def inspect_file(self, path):
        if path in self.file_cache:
            return self.file_cache[path]
        try:
            require(path.resolve().is_relative_to(self.repo), "file escapes repository through symlink")
            require(path.is_file(), "file is missing or not a regular file")
            with path.open("rb") as stream:
                head = stream.read(4096)
            info = dict(size=path.stat().st_size, pointer=pointer(head), head=head)
            require(info["size"] > 0, "empty asset")
            self.file_cache[path] = info
            if info["pointer"]:
                oid, size = info["pointer"]
                self.finding("lfs.unhydrated", path, f"LFS pointer, not asset bytes (sha256 {oid}, expected {size} bytes).")
            return info
        except (OSError, MetadataError) as error:
            self.finding("file.invalid", path, str(error))
            self.file_cache[path] = None
            return None

    def digest(self, path):
        if path not in self.digest_cache:
            h = hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    h.update(chunk)
            self.digest_cache[path] = h.hexdigest()
        return self.digest_cache[path]

    def check_hash(self, path, expected, context):
        require(isinstance(expected, str) and HASH.fullmatch(expected), "SHA-256 must be 64 hex characters")
        info = self.inspect_file(path)
        if info and not info["pointer"]:
            actual = self.digest(path)
            if actual != expected.lower():
                self.finding("hash.mismatch", path, f"{context}: expected {expected.lower()}, got {actual}.", basis="bytes")

    def png_header(self, path):
        info = self.inspect_file(path)
        if not info or info["pointer"]:
            return None
        head = info["head"]
        try:
            require(len(head) >= 33 and head[:8] == b"\x89PNG\r\n\x1a\n", "invalid or truncated PNG signature/header")
            require(head[8:16] == b"\x00\x00\x00\x0dIHDR", "PNG must begin with a 13-byte IHDR")
            require(zlib.crc32(head[12:29]) & 0xffffffff == struct.unpack(">I", head[29:33])[0],
                    "IHDR CRC mismatch")
            width, height, depth, colour, compression, filtering, interlace = struct.unpack(">IIBBBBB", head[16:29])
            require(0 < width <= 0x7fffffff and 0 < height <= 0x7fffffff, "invalid PNG dimensions")
            depths = {0: {1, 2, 4, 8, 16}, 2: {8, 16}, 3: {1, 2, 4, 8}, 4: {8, 16}, 6: {8, 16}}
            require(colour in depths and depth in depths[colour] and compression == 0 and
                    filtering == 0 and interlace in (0, 1), "invalid IHDR encoding")
            return [width, height]
        except MetadataError as error:
            self.finding("png.header", path, str(error), basis="bytes")
            return None

    def check_name(self, path):
        ext = path.suffix.lower()
        if path.suffix != ext:
            self.finding("name.extension", path, "Asset extension must be lowercase.")
        name = path.stem
        # Repository evidence sheets retain mesh prefixes or use preview.png.
        evidence = ext == ".png" and (name == "preview" or
                   re.fullmatch(r"SM_[A-Za-z][A-Za-z0-9_]*_(preview(?:_closeup)?|compare)", name))
        if evidence:
            return
        if ext in MESH_EXTENSIONS:
            prefixes = ["SM", "SK"]
        elif ext in IMAGE_EXTENSIONS:
            prefixes = ["T"]
        elif ext in {".wav", ".mp3", ".ogg"}:
            prefixes = ["SFX", "MS"]
        elif ext == ".umap":
            prefixes = ["L"]
        else:
            prefixes = PREFIXES
        if not re.fullmatch(r"(?:" + "|".join(prefixes) + r")_[A-Za-z][A-Za-z0-9_]*", name):
            self.finding("name.prefix", path, "Expected an asset prefix and alphanumeric/underscore name: " + ", ".join(prefixes))

    def source_record(self, path, data):
        require(isinstance(data, dict), "source validation record must be an object")
        output = self.recorded_path(data.get("output"), path)
        require(output.suffix == ".fbx", "cleanup-export output must be a lowercase .fbx")
        require(path.name == output.stem + ".validation.json" and path.parent == output.parent,
                "record filename/location must match output")
        require(output.is_relative_to(self.repo / "SourceArt/HC"), "cleanup output must be in SourceArt/HC")
        self.assets.add(output)
        self.records.add(output)
        require(isinstance(data.get("input"), str) and data["input"].strip(), "input must record its historical source path")
        require(data.get("source_unit") in ("auto", "meters", "centimeters"), "invalid source_unit")
        require(number(data.get("explicit_unit_correction_factor")) and data["explicit_unit_correction_factor"] > 0,
                "unit correction factor must be finite and positive")
        for field in ("triangles_before", "triangles_after"):
            require(integer(data.get(field)) and data[field] > 0, field + " must be a positive integer")
        require(data["triangles_after"] <= data["triangles_before"], "triangles_after exceeds triangles_before")
        require(vector(data.get("dimensions_cm"), 3, True), "dimensions_cm must have three finite positive numbers")
        require(vector(data.get("bounds_min_cm"), 3), "bounds_min_cm must have three finite numbers")
        require(isinstance(data.get("pivot"), str) and data["pivot"].strip(), "pivot must be recorded")
        for field, expected in (("fbx_unit", "centimeters"), ("up_axis", "+Z"), ("forward_axis", "-Y")):
            require(data.get(field) == expected, field + " must be " + expected)
        require("UV_warning" in data and (data["UV_warning"] is None or isinstance(data["UV_warning"], str)),
                "UV_warning must be a string or null")
        if data["UV_warning"]:
            self.finding("record.uv_warning", path, data["UV_warning"], "warning", "recorded")
        self.inspect_file(output)
        if "sha256" in data:
            self.check_hash(output, data["sha256"], self.label(path))
        else:
            self.finding("record.unbound", path, "No output SHA-256 in export record; measurements cannot be tied to current bytes.", "warning", "recorded")
        if data["pivot"] == "base center":
            expected = [-data["dimensions_cm"][0] / 2, -data["dimensions_cm"][1] / 2, 0]
            if any(not math.isclose(a, b, abs_tol=0.001, rel_tol=0) for a, b in zip(data["bounds_min_cm"], expected)):
                self.finding("record.pivot", path, "Recorded bounds are inconsistent with the recorded base-center pivot (0.001 cm rounding tolerance).", basis="recorded")
        self.fact(path, "export_metrics", {k: data[k] for k in (
            "dimensions_cm", "bounds_min_cm", "triangles_after", "pivot", "fbx_unit", "up_axis", "forward_axis")})
        if self.selected(output) and "HC-A1" in output.parts:
            if data["triangles_after"] > 10000:
                self.finding("record.triangle_budget", path, "Recorded HC-A1 triangle count exceeds 10,000.", basis="recorded")
            # Small relic brief describes overall size, not a required height on every axis.
            longest = max(data["dimensions_cm"])
            if output.stem.startswith("SM_Relic_") and not 20 <= longest <= 30:
                self.finding("record.relic_size", path, f"Recorded longest dimension {longest:g} cm differs from small relic brief (20-30 cm); review size intent in Blender/Unreal.", "warning", "recorded")

    def file_record(self, entry, path):
        require(isinstance(entry, dict), "file record must be an object")
        output = self.recorded_path(entry.get("file", entry.get("path")), path)
        self.assets.add(output)
        info = self.inspect_file(output)
        if "sha256" in entry:
            self.check_hash(output, entry["sha256"], self.label(path))
        if "bytes" in entry:
            require(integer(entry["bytes"]) and entry["bytes"] > 0, "bytes must be a positive integer")
            if info and not info["pointer"] and info["size"] != entry["bytes"]:
                self.finding("file.size", output, f"Recorded size {entry['bytes']} differs from {info['size']}.", basis="bytes")
        if "dimensions" in entry:
            dims = entry["dimensions"]
            require(isinstance(dims, list) and len(dims) == 2 and all(integer(x) and x > 0 for x in dims),
                    "dimensions must be two positive integers")
            require(output.suffix.lower() == ".png", "pixel dimensions are supported only for PNG")
            actual = self.png_header(output)
            if actual and actual != dims:
                self.finding("png.dimensions", output, f"Recorded dimensions {dims} differ from IHDR {actual}.", basis="bytes")
        if "provenance" in entry:
            self.provenance(entry["provenance"], path)

    def hud_validation(self, path, data):
        require(isinstance(data, dict) and integer(data.get("schema_version")) and data["schema_version"] == 1,
                "unsupported HUD validation schema_version")
        require(data.get("source_delivery_only") is True, "source_delivery_only must be true")
        entries = data.get("automated_checks")
        require(isinstance(entries, list) and entries, "automated_checks must be a nonempty list")
        for entry in entries:
            require(isinstance(entry, dict) and all(k in entry for k in ("file", "sha256", "bytes", "dimensions")),
                    "HUD automated check needs file, sha256, bytes, dimensions")
            self.file_record(entry, path)
            dims = entry["dimensions"]
            if "mode" in entry:
                require(entry["mode"] in ("RGBA", "RGB", "P", "L", "LA", "1", "I", "I;16"), "unknown recorded pixel mode")
            for field in ("alpha_extrema", "central_opening_alpha_extrema"):
                if field in entry:
                    values = entry[field]
                    require(isinstance(values, list) and len(values) == 2 and
                            all(integer(x) and 0 <= x <= 255 for x in values) and values[0] <= values[1],
                            field + " must be an ordered pair of byte values")
            if "fully_transparent_pixels" in entry:
                require(integer(entry["fully_transparent_pixels"]) and
                        0 <= entry["fully_transparent_pixels"] <= dims[0] * dims[1], "invalid transparent pixel count")
            if "max_boundary_alpha" in entry:
                require(integer(entry["max_boundary_alpha"]) and 0 <= entry["max_boundary_alpha"] <= 255,
                        "invalid recorded max_boundary_alpha")
            if "visible_bounds_alpha_gt_8" in entry:
                bounds = entry["visible_bounds_alpha_gt_8"]
                require(isinstance(bounds, list) and len(bounds) == 4 and all(integer(x) for x in bounds) and
                        0 <= bounds[0] < bounds[2] <= dims[0] and 0 <= bounds[1] < bounds[3] <= dims[1],
                        "invalid recorded visible bounds")
            require(isinstance(entry.get("source_sha256"), str) and HASH.fullmatch(entry["source_sha256"]),
                    "HUD source_sha256 must be 64 hex characters")
            self.fact(path, "pixel_claims", {k: v for k, v in entry.items() if k not in ("file", "sha256", "bytes", "dimensions")})
        require(isinstance(data.get("preview"), dict), "HUD preview must be an object")
        self.file_record(data["preview"], path)
        # Match each recorded source hash with generation.json's source/output pairing.
        generation_path = path.parent / "generation.json"
        if not generation_path.is_file():
            self.finding("metadata.missing", generation_path, "HUD validation needs generation.json for source hash pairing.")
        else:
            generation = read_json(generation_path)
            require(isinstance(generation, dict) and isinstance(generation.get("records"), list), "generation records must be a list")
            pairs = {self.recorded_path(e.get("output"), generation_path): e.get("source_sha256")
                     for e in generation["records"] if isinstance(e, dict)}
            for entry in entries:
                output = self.recorded_path(entry["file"], path)
                paired_hash = pairs.get(output)
                if not isinstance(paired_hash, str) or paired_hash.lower() != entry["source_sha256"].lower():
                    self.finding("hash.source_pair", path, "HUD source_sha256 does not match generation record for " + self.label(output), basis="recorded")

    def generation(self, path, data):
        require(isinstance(data, dict) and isinstance(data.get("tool"), str) and data["tool"].strip(),
                "generation must record tool")
        entries = data.get("records")
        require(isinstance(entries, list) and entries, "generation records must be a nonempty list")
        names = set()
        for entry in entries:
            require(isinstance(entry, dict) and isinstance(entry.get("name"), str), "generation record needs name")
            require(entry["name"] not in names, "duplicate generation name")
            names.add(entry["name"])
            source = self.recorded_path(entry.get("source"), path)
            output = self.recorded_path(entry.get("output"), path)
            require(output.stem == entry["name"], "generation name must match output")
            self.assets.update((source, output))
            self.inspect_file(output)
            self.check_hash(source, entry.get("source_sha256"), self.label(path))
        if "reference_path" in data or "reference_sha256" in data:
            ref = self.safe_path(data.get("reference_path"))
            self.assets.add(ref)
            self.check_hash(ref, data.get("reference_sha256"), self.label(path))

    def provenance(self, data, path):
        require(isinstance(data, dict), "provenance must be an object")
        fields = ("source", "url", "plan", "license", "attribution")
        for field in fields:
            require(field not in data or isinstance(data[field], str), "provenance " + field + " must be a string")
        require("public_redistribution" not in data or isinstance(data["public_redistribution"], bool),
                "provenance public_redistribution must be boolean")
        missing = [k for k in fields if not isinstance(data.get(k), str) or not data[k].strip()]
        if missing or not isinstance(data.get("public_redistribution"), bool):
            self.finding("provenance.missing", path, "Missing provenance fields: " + ", ".join(missing + (
                [] if isinstance(data.get("public_redistribution"), bool) else ["public_redistribution"])), "warning", "recorded")
        if data.get("public_redistribution") is False:
            self.finding("provenance.redistribution", path, "Record says public redistribution is not permitted.", basis="recorded")
        self.fact(path, "provenance", data)
        return not missing and isinstance(data.get("public_redistribution"), bool)

    def manifest(self, path, data):
        require(isinstance(data, dict) and integer(data.get("schema_version")) and data["schema_version"] == 1,
                "import manifest needs schema_version 1")
        require(set(data) <= {"schema_version", "assets"}, "unknown import manifest fields")
        entries = data.get("assets")
        require(isinstance(entries, list) and entries, "manifest assets must be a nonempty list")
        seen = set()
        for entry in entries:
            require(isinstance(entry, dict), "manifest asset must be an object")
            require(set(entry) <= {"task", "source", "source_sha256", "imported", "imported_sha256",
                                   "provenance", "source_validation", "dimensions", "dimensions_cm", "opening_cm"},
                    "unknown import manifest asset fields")
            require("imported_sha256" not in entry or "imported" in entry, "imported_sha256 requires an imported file")
            task = entry.get("task")
            require(isinstance(task, str) and TASK.fullmatch(task), "manifest task must be HC-A<number>")
            # Validate structure and path boundaries even for excluded entries.
            source = self.safe_path(entry.get("source"))
            require(source.is_relative_to(self.repo / "SourceArt/HC" / task), "manifest source must be inside its HC task")
            imported = self.safe_path(entry["imported"]) if "imported" in entry else None
            if imported:
                require(imported.is_relative_to(self.repo / "Content/Puzzles/Art") and imported.suffix == ".uasset",
                        "manifest imported path must be .uasset in Content/Puzzles/Art")
            require(source not in seen, "duplicate manifest source")
            seen.add(source)
            if self.task and task != self.task:
                continue
            require(source.suffix.lower() in ASSET_EXTENSIONS, "manifest source must be a supported asset file")
            self.assets.add(source)
            self.check_hash(source, entry["source_sha256"], self.label(path)) if "source_sha256" in entry else self.inspect_file(source)
            if imported:
                self.assets.add(imported)
                self.check_hash(imported, entry["imported_sha256"], self.label(path)) if "imported_sha256" in entry else self.inspect_file(imported)
            if "provenance" in entry:
                if self.provenance(entry["provenance"], path):
                    self.provenance_tasks.add(task)
            else:
                self.finding("provenance.missing", source, "Manifest has no provenance record.", "warning", "recorded")
            if "source_validation" in entry:
                record = self.safe_path(entry["source_validation"])
                require(record.parent == source.parent and record.name == source.stem + ".validation.json",
                        "source_validation must match the source FBX")
                self.read_metadata(record, "export")
            if "dimensions" in entry:
                self.file_record(dict(file=entry["source"], dimensions=entry["dimensions"]), path)
            for field in ("opening_cm", "dimensions_cm"):
                if field in entry:
                    require(any(vector(entry[field], n, True) for n in ((2, 3) if field == "opening_cm" else (3,))),
                            field + " must contain positive finite numbers (opening: 2 or 3; full dimensions: 3)")
                    self.fact(source, field, entry[field])  # no opening-to-bounds equality inference

    def read_metadata(self, path, kind):
        try:
            require(path.resolve().is_relative_to(self.repo) or kind == "manifest",
                    "metadata escapes repository through symlink")
            data = read_json(path)
            {"export": self.source_record, "hud": self.hud_validation,
             "generation": self.generation, "manifest": self.manifest, "provenance": self.provenance}[kind](path, data)
        except (OSError, ValueError, TypeError, RecursionError) as error:
            self.finding("metadata.invalid", path, str(error), basis="recorded")

    def lfs_checks(self):
        files = sorted(self.assets)
        if not files:
            return
        encoded = b"".join(self.label(p).encode("utf-8") + b"\0" for p in files)
        attributes = self.git("check-attr", "-z", "--stdin", "filter", "diff", "merge", "text", data=encoded).split(b"\0")
        attrs = {}
        for i in range(0, len(attributes) - 1, 3):
            file, key, value = (x.decode("utf-8", "replace") for x in attributes[i:i + 3])
            attrs.setdefault(file, {})[key] = value
        index = {}
        for entry in self.git("ls-files", "--stage", "-z").split(b"\0"):
            if entry:
                meta, name = entry.split(b"\t", 1)
                mode, oid, stage = meta.split()
                index.setdefault(name.decode("utf-8", "replace"), []).append((oid.decode(), stage))
        for path in files:
            name = self.label(path)
            attr = attrs.get(name, {})
            if not all(attr.get(k) == v for k, v in (("filter", "lfs"), ("diff", "lfs"), ("merge", "lfs"), ("text", "unset"))):
                self.finding("lfs.attributes", path, "Expected filter/diff/merge=lfs and -text; effective attributes: " + str(attr))
            entries = index.get(name, [])
            if not entries:
                self.finding("git.untracked", path, "Asset is not in Git's index; stored LFS coverage cannot be verified.")
                continue
            if len(entries) != 1 or entries[0][1] != b"0":
                self.finding("git.conflict", path, "Asset has an unmerged index entry.")
                continue
            oid = entries[0][0]
            size = int(self.git("cat-file", "-s", oid))
            if size > 4096:
                self.finding("lfs.index", path, "Tracked asset's index blob is asset bytes rather than an LFS pointer.")
                continue
            try:
                lfs = pointer(self.git("cat-file", "blob", oid))
                require(lfs is not None, "tracked asset's index blob is not an LFS pointer")
            except MetadataError as error:
                self.finding("lfs.index", path, str(error))
                continue
            info = self.inspect_file(path)
            if info and info["pointer"]:
                if info["pointer"] != lfs:
                    self.finding("lfs.pointer_mismatch", path, "Working pointer differs from indexed pointer.")
            elif info:
                self.check_hash(path, lfs[0], "Git index LFS oid")
                if info["size"] != lfs[1]:
                    self.finding("lfs.size", path, f"LFS index size {lfs[1]} differs from {info['size']}.", basis="bytes")

    def run(self, manifests=()):
        try:
            require(self.repo.is_dir(), "repository path is missing or not a directory")
            if self.task:
                require(TASK.fullmatch(self.task), "task must be HC-A<number>")
            require(Path(self.git("rev-parse", "--show-toplevel").decode().strip()).resolve() ==
                    self.repo, "path must be the Git repository root")
            source_root = self.repo / "SourceArt/HC"
            scope = source_root / self.task if self.task else source_root
            require(scope.is_dir(), "HC source scope is missing: " + self.label(scope))
            candidates = sorted(scope.rglob("*"))
            for path in candidates:
                if not path.is_file():
                    continue
                require(path.resolve().is_relative_to(self.repo), "source file escapes repository: " + self.label(path))
                if path.suffix.lower() in ASSET_EXTENSIONS:
                    self.assets.add(path)
                elif path.suffix.lower() == ".json" and path.suffix != ".json":
                    self.finding("name.extension", path, "Metadata extension must be lowercase.")
                elif path.name.lower().endswith(".validation.json"):
                    self.read_metadata(path, "export")
                elif path.name == "validation.json":
                    self.read_metadata(path, "hud")
                elif path.name == "generation.json":
                    self.read_metadata(path, "generation")
                elif path.name == "provenance.json":
                    self.read_metadata(path, "provenance")
                elif path.suffix == ".json":
                    self.finding("metadata.unsupported", path, "JSON format is not an automatic source-validation format; supply an explicit supported manifest if appropriate.", "warning", "recorded")
            imported_root = self.repo / "Content/Puzzles/Art"
            if not self.task and imported_root.is_dir():
                for path in sorted(imported_root.rglob("*")):
                    if path.is_file() and path.suffix.lower() in ASSET_EXTENSIONS:
                        require(path.resolve().is_relative_to(self.repo), "imported file escapes repository")
                        self.assets.add(path)
            for manifest_path in manifests:
                path = Path(manifest_path)
                if not path.is_absolute():
                    path = self.repo / path
                self.read_metadata(path.resolve(), "manifest")
            for task_dir in sorted(scope.iterdir()) if not self.task else [scope]:
                if not task_dir.is_dir() or not TASK.fullmatch(task_dir.name):
                    continue
                evidence = [p for p in (task_dir / "README.md", task_dir / "delivery.md", task_dir / "provenance.json") if p.is_file()]
                if evidence:
                    for doc in evidence:
                        require(doc.resolve().is_relative_to(self.repo), "provenance evidence escapes repository")
                    self.fact(task_dir, "provenance_evidence", [self.label(p) for p in evidence], "repository")
                    self.finding("provenance.review", task_dir, "Local provenance documents exist; verify their rights, tier, URL and attribution manually.", "warning")
                elif task_dir.name not in self.provenance_tasks:
                    self.finding("provenance.missing", task_dir, "No local provenance document; check asset issue offline evidence or supply a manifest. No license inferred.", "warning")
            require(self.assets, "no HC assets found in selected scope/manifests")
            for path in sorted(self.assets):
                self.check_name(path)
                info = self.inspect_file(path)
                if path.suffix.lower() == ".png" and info and not info["pointer"]:
                    dims = self.png_header(path)
                    if dims:
                        self.fact(path, "png_dimensions", dims, "bytes")
                if path.suffix.lower() == ".fbx" and path.is_relative_to(source_root) and path not in self.records:
                    self.finding("record.missing", path, "FBX has no matching source-validation record.")
            self.lfs_checks()
        except (OSError, MetadataError, subprocess.SubprocessError, ValueError) as error:
            self.finding("tool.input", self.repo, str(error))
        # Each error remains stable and deterministic, without duplicate header/hash findings.
        self.findings = sorted({json.dumps(f, sort_keys=True): f for f in self.findings}.values(),
                               key=lambda f: (f["path"], f["code"], f["message"]))
        errors = sum(f["severity"] == "error" for f in self.findings)
        warnings = sum(f["severity"] == "warning" for f in self.findings)
        return dict(repository=str(self.repo), task=self.task, assets_checked=len(self.assets),
                    errors=errors, warnings=warnings, findings=self.findings,
                    facts=self.facts, limitations=LIMITATIONS,
                    exit_code=2 if any(f["code"] == "tool.input" for f in self.findings) else (1 if errors else 0))

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", type=Path, help="explicit Git repository root")
    parser.add_argument("--task", help="HC asset task, e.g. HC-A1")
    parser.add_argument("--manifest", type=Path, action="append", default=[], help="offline import manifest; repeatable")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)
    report = Validator(args.repository, args.task).run(args.manifest)
    if args.format == "json":
        print(json.dumps(report, indent=2, allow_nan=False))
    else:
        print(f"HC QA: {report['assets_checked']} assets; {report['errors']} errors, {report['warnings']} warnings")
        for finding in report["findings"]:
            print(f"{finding['severity'].upper()} {finding['code']} [{finding['basis']}] {finding['path']}: {finding['message']}")
        for limit in report["limitations"]:
            print("LIMIT: " + limit)
    return report["exit_code"]

if __name__ == "__main__":
    sys.exit(main())
