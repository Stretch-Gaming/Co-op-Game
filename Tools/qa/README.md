# HC repository and source QA

HC-QA1, [issue #69](https://github.com/Stretch-Gaming/Co-op-Game/issues/69), under HC epic #1. Owned scope: `Tools/qa/`.

`validate_hc.py` is a read-only Python 3.9+ CLI using only the standard library. Git must be on PATH; Git LFS, Blender, Unreal and third-party Python packages are not needed to run it. Validation does not repair assets, write reports to disk, alter Git configuration, install anything, fetch network resources or start editors. It prints text or JSON to stdout and returns a defined exit code.

## Run

Run from any working directory, supplying the exact Git repository root (a normal checkout or attached worktree). Quote paths containing spaces.

Windows:

```powershell
python -B "C:\Users\Stretch\.codex\worktrees\hc-qa-validation\Co op Game\Tools\qa\validate_hc.py" "C:\Users\Stretch\.codex\worktrees\hc-qa-validation\Co op Game" --task HC-A1
```

macOS/Linux:

```sh
python3 -B "/path/Co op Game/Tools/qa/validate_hc.py" "/path/Co op Game" --task HC-A2 --format json
```

With no `--task`, scan all assets under `SourceArt/HC/` and `Content/Puzzles/Art/`. A task filter accepts `HC-A<number>` and scans only that source task, plus imported files explicitly associated with it in supplied manifests. Imported files have no task identity in their filenames, so a filtered run cannot automatically associate them with an asset task. A missing task is an input error.

`--manifest` is repeatable. Relative manifest arguments are resolved from the supplied repository root; an absolute path can identify an explicitly supplied offline JSON file. Paths *inside* every manifest must be repository-relative. References cannot escape the repository through `..`, absolute paths, URLs, drive paths or symlinks. Cleanup records keep their historical generator `input` path as evidence; an old `/tmp/...glb` is not a required repository file.

## Checks and exit policy

| Result | Exit | Meaning |
| --- | --- | --- |
| No errors | 0 | Defined automated checks pass; warnings may remain |
| Validation errors | 1 | Naming, asset bytes, LFS storage, metadata or a supplied assertion fails |
| Input/tool failure | 2 | Bad repository/task scope, missing Git, failed Git query or invalid CLI arguments |

Each finding has `severity`, stable `code`, `path`, `basis` and `message`. JSON also contains facts, counters, scope, limitations and `exit_code`. Errors take precedence over warning-only results. An interrupted/missing Git query yields exit 2, even if other findings exist.

Checks cover:

- Lowercase asset extensions and Unreal prefixes. Mesh formats use `SM_`/`SK_`, textures use `T_`, sounds use `SFX_`/`MS_`, levels use `L_`, and imported assets use an AGENTS.md prefix. Scripts and prose documents are not assets. Existing `SM_*_preview.png`, `SM_*_preview_closeup.png`, `SM_*_compare.png` and `preview.png` are reserved evidence-image exceptions.
- Effective Git attributes, including nested overrides: `filter=lfs diff=lfs merge=lfs -text`. Tracked index blobs must contain LFS pointers. The validator parses pointers itself, then compares hydrated bytes against the indexed SHA-256 and size. Unhydrated, malformed or mismatched pointers, raw binary index blobs, untracked assets and unmerged index entries fail. Git LFS hydration is never attempted.
- Nonempty existing asset files. Missing files and path escapes fail. PNG checks verify the signature, IHDR shape, CRC, legal header encoding and positive dimensions. Header dimensions are compared with supplied pixel dimensions; otherwise they are reported as facts. No 512px assumption is applied to previews.
- Supplied SHA-256 hashes and byte sizes. Pointer text is never hashed as though it were an image or mesh. A pointer failure blocks those byte comparisons. Hashes are case-insensitive hexadecimal; metadata must contain 64 characters.
- Existing source-validation records, with strict required types, finite numbers, duplicate-key rejection and a 2 MiB JSON size limit. Malformed or unsupported supplied manifest schemas fail.

Error codes include `name.extension`, `name.prefix`, `file.invalid`, `file.size`, `png.header`, `png.dimensions`, `hash.mismatch`, `hash.source_pair`, `metadata.invalid`, `metadata.missing`, `record.missing`, `record.triangle_budget`, `record.pivot`, `lfs.attributes`, `lfs.unhydrated`, `lfs.index`, `lfs.pointer_mismatch`, `lfs.size`, `git.untracked`, `git.conflict` and `provenance.redistribution`. `tool.input` yields exit 2.

Warnings include `provenance.missing`, `provenance.review`, `record.unbound`, `record.relic_size`, `record.uv_warning` and `metadata.unsupported`. Missing provenance is a finding, never an inferred license. A record explicitly prohibiting public redistribution fails.

## Existing metadata formats

**Blender cleanup export:** `SM_Name.validation.json`, emitted by `Tools/blender/cleanup_export.py`. Its `output` is repository-relative, and the sidecar must share the output FBX's directory/stem. Required fields are `input`, `output`, `source_unit`, `explicit_unit_correction_factor`, `triangles_before`, `triangles_after`, `dimensions_cm`, `bounds_min_cm`, `pivot`, `fbx_unit`, `up_axis`, `forward_axis` and `UV_warning`. Optional `sha256` binds the record to the output. Without it, `record.unbound` warns that metrics cannot be tied to current bytes. An index LFS hash proves byte identity with the index, not identity with the historical export record.

The tool checks positive counts/dimensions, nonincreasing cleanup triangle count, centimeter/+Z/-Y metadata, and internal consistency for a recorded base-center pivot within 0.001 cm rounding tolerance. It flags recorded HC-A1 triangle counts above the explicit 10k budget. Small relic bounds outside the 20–30 cm brief produce a review warning, since the size intent needs confirmation. No tolerance or axis is invented for the key relic's approximate 60 cm brief.

**HUD source delivery:** `generation.json` and `validation.json`, as present in HC-A3 PR #68. The first supplies tool, source/output pairings, source hashes and an optional repository-root reference image/hash. The second has `schema_version: 1`, `source_delivery_only: true`, `automated_checks` and `preview`. File references are relative to the metadata directory; supplied file hashes, bytes and dimensions are checked, and source hashes are paired with generation records. Known alpha statistics are checked for structurally plausible values and reported as recorded claims, not recomputed pixel measurements.

Repository-root paths beginning `SourceArt/` or `Content/` are accepted in file records; other HUD references are relative to the record's directory. Unrecognized automatic JSON files produce a warning rather than being assumed to pass a known schema. A local `provenance.json` may contain the provenance object described below.

README/delivery documents are listed as local provenance evidence needing manual review. The tool does not interpret prose as legal permission. Complete provenance objects in a manifest can supply offline task evidence. Neither a tool name nor a README's existence proves a license.

## Offline import manifest

There is no committed HC import-manifest format on the audited main commit. This tooling defines a small version-1 input contract; it does not change any import tools. Unknown top-level or asset fields fail so misspelled hash fields cannot silently disappear.

```json
{
  "schema_version": 1,
  "assets": [
    {
      "task": "HC-A2",
      "source": "SourceArt/HC/HC-A2/SM_ChamberGate_Frame.fbx",
      "imported": "Content/Puzzles/Art/SM_ChamberGate_Frame.uasset",
      "source_validation": "SourceArt/HC/HC-A2/SM_ChamberGate_Frame.validation.json",
      "opening_cm": [400, 400]
    }
  ]
}
```

This example contains a suggested imported path, not evidence that the asset has been imported. It fails if that file is absent. Required asset fields: `task` and `source`. Optional fields: `source_sha256`, `imported`, `imported_sha256`, `source_validation`, `dimensions` (PNG pixels), `dimensions_cm` (three reported full-bounds values), `opening_cm` (two or three reported opening values), and `provenance`. Source paths must belong to their named HC task; imported paths must be `.uasset` under `Content/Puzzles/Art/`. Duplicate source entries fail. Unselected tasks are excluded from file checks, but their task/path structure is still validated.

A provenance object records `source`, `url`, `plan`, `license` (including version/terms date), `public_redistribution` (boolean), and `attribution`. Supply the actual documented values; an unknown tier or rights status remains missing evidence. Missing fields warn; malformed field types fail; explicit `public_redistribution: false` fails. The tool records claims without fetching their URLs or endorsing their rights.

## Limits and human gates

Dimensions, bounds, triangle counts, pivots, units, axes and opening sizes are checked *as recorded metadata*. The validator does not parse FBX geometry. A 4 m gate opening is not a 4 m whole mesh: the frame can include wider posts and a lintel, and the sliding leaf can exceed the opening. Opening values are never compared for equality with mesh bounds.

IHDR checks do not decode pixels or establish actual transparency, empty openings, texture quality, seamless tiling or small-size readability. Recorded alpha statistics cannot replace pixel/visual review. Blender must verify geometry, opening clearance, current dimensions, topology, UVs and pivots. Unreal must verify import settings, materials, collision, Nanite, placement, client behavior and split-screen appearance. Source metadata never certifies those gates.

The tool does not audit live GitHub issue comments, fetch licensing terms, write credits or decide whether a legal claim is correct. Missing local provenance does not mean the asset has no provenance anywhere. Partial validation is explicit: pointer checkouts fail rather than pretending that blocked image/hash checks passed.

## Tests and recorded audit

```sh
python3 -B -m unittest discover -s Tools/qa/tests -v
```

Use `python` on Windows. Tests need Git and write synthetic temporary repositories only under ignored `Tools/qa/tests/.tmp/`; the validator itself remains read-only. These fixture repositories stage manufactured pointer blobs directly with Git, so tests do not need Git LFS or run clean/smudge filters. Synthetic FBX/uasset contents are not real geometry.

Fixtures cover valid/invalid metadata, spaces, missing files, stale hashes, LFS pointers, nested attribute overrides, naming, task filters, import manifests, PNG headers, existing HUD metadata, gate-opening semantics and snapshots proving no file/index/config mutation. Symlink escape testing runs where the OS account supports symlink creation.

See [AUDIT.md](AUDIT.md) and [results/audit.json](results/audit.json) for the dated audit, input hashes and practical limitations. Existing asset findings were reported without fixes.
