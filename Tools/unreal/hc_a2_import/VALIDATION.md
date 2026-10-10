# Offline validation evidence

This delivery stops at the offline tooling gate. No Unreal editor was launched or controlled. No imported Unreal asset, gameplay, map or project-setting changes are included.

The gate uses Unreal 5.8.3's bundled standalone Python 3.11.8. It directly parses all ten hydrated FBX files rather than trusting their names or the rounded PR table. Their triangle counts, effective dimensions and pivots agree with their validation JSON snapshots. Direct FBX inspection also checks raw geometry/node scale, the UV channel, finite normals, slots and material-face assignments. It verifies raw SHA-256/size against committed LFS pointers and checks LFS attributes. Text metadata hashes normalize LF newlines; binary hashes retain raw bytes.

The default dry run validates the source/manifest/project structure and prints exactly ten mesh and three material destinations inside HCA2_Props, with correct assembly offsets, both statue variants and pending collision/visual work. It creates no files or Unreal objects. The gate records protected source/Content file state before/after and checks ownership against Git. Python syntax is compiled in memory without generating pycache.

The safety suite exercises default offline and simulated-editor read-only behavior, missing execution opt-in/project path, wrong project/version, occupied registry and disk destinations, source/metadata hash changes, LFS pointers, missing Tint/translucent parent, path escapes, assembly changes and Nanite threshold errors. The editor used for these tests is a small fake read-only API surface: **these are safety-unit tests, not live Unreal validation**.

See [offline_validation.json](evidence/offline_validation.json), [dry_run.json](evidence/dry_run.json) and [safety_tests.txt](evidence/safety_tests.txt) for the captured results and hashes. The manifest carries the complete per-source records.

Installed 5.8.3 headers were read offline to check AssetImportTask, FbxImportUI/static-mesh import properties, material parameter APIs, StaticMeshEditorSubsystem collision/UV/Nanite methods and StaticMesh bounds. Installed AssetTools.cpp confirms a specified FbxFactory bypasses the Interchange import route. These checks support the implementation but do not prove the generated editor-Python bindings or actual imports work.

Supporting public API references: [Epic FBX static-mesh import settings](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/FbxStaticMeshImportData?application_version=4.27) and [Epic ScriptCollisionShapeType](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/ScriptCollisionShapeType?application_version=5.6). Public 5.8 Python API pages were unavailable during this pass; the installed 5.8.3 headers were the version-specific reference.

Actual imports, runtime API execution, material compilation, collision authoring/physics, assembly, cave lighting, other-platform appearance, PIE, split-screen and placement **have not run and remain pending**. The compound props deliberately have no automatic collision. Issue #19 remains open with its original import/test/placement steps pending.
