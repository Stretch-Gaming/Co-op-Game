"""HC-A2 opt-in editor-Python importer. run() defaults to a read-only dry run."""
import argparse
import json
from pathlib import Path
import re
import sys

TOOL_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TOOL_DIR.parents[2]
if str(TOOL_DIR) not in sys.path:
    sys.path.insert(0, str(TOOL_DIR))
from source_audit import DESTINATION, MATERIALS, PARENT, require, verify_sources

MANIFEST_PATH = TOOL_DIR / "manifest.json"


def srgb_to_linear(hex_color):
    values = [int(hex_color[i:i + 2], 16) / 255.0 for i in (1, 3, 5)]
    return [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
            for v in values] + [1.0]


def assign_tint(unreal, instance, hex_color):
    tint = unreal.LinearColor(*srgb_to_linear(hex_color))
    # UE 5.8.3 sets this override but its setter returns false unconditionally.
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(instance, "Tint", tint)
    actual = unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(instance, "Tint")
    require(unreal.MaterialEditingLibrary.is_material_instance_parameter_overridden(instance, "Tint")
            and all(abs(getattr(actual, c) - getattr(tint, c)) < 0.00001
                    for c in ("r", "g", "b", "a")), "Tint override read-back failed")
    unreal.MaterialEditingLibrary.update_material_instance(instance)


def load_plan():
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8-sig"))
    sources = verify_sources(PROJECT_ROOT, manifest)
    # These settings are code-owned so editing JSON cannot enable textures,
    # collision auto-hulls or redirect a write. Keep the manifest synchronized.
    expected = {
        "uniform_scale": 1.0, "translation_cm": [0, 0, 0], "rotation_deg": [0, 0, 0],
        "convert_scene": True, "convert_scene_unit": True, "force_front_x_axis": False,
        "transform_vertex_to_absolute": True, "bake_pivot_in_vertex": False,
        "combine_meshes": True, "import_materials": False, "import_textures": False,
        "normal_import_method": "FBXNIM_IMPORT_NORMALS",
        "generate_lightmap_u_vs": False, "auto_generate_collision": False,
        "import_mesh_lo_ds": False,
    }
    require(all(manifest["import_settings"].get(k) == v for k, v in expected.items()),
            "Import settings differ from importer contract")
    require(manifest["engine_version"] == "5.8.3"
            and manifest["project"] == "CoopGame.uproject", "Wrong target project/version")
    require(manifest["nanite_fallback"]["percent_triangles"] == 1.0
            and manifest["nanite_fallback"]["relative_error"] == 0.0, "Fallback must preserve source geometry")
    return manifest, sources


def package_file(package):
    require(package.startswith(DESTINATION + "/"), "Write escaped HC-A2 destination")
    relative = package.removeprefix("/Game/") + ".uasset"
    path = (PROJECT_ROOT / "Content" / relative).resolve()
    require(path.is_relative_to(PROJECT_ROOT / "Content/Puzzles/Art/HCA2_Props"),
            "Destination resolves outside HC-A2 (symlink/junction)")
    return path


def planned_paths(manifest):
    return [m["destination"] for m in manifest["materials"]] + [
        a["destination"] for a in manifest["assets"]]


def disk_conflicts(manifest):
    conflicts = []
    for package in planned_paths(manifest):
        file = package_file(package)
        if file.exists() or file.with_suffix(".umap").exists():
            conflicts.append(package)
    return conflicts


def editor_preflight(unreal, manifest, project_file):
    expected = (PROJECT_ROOT / "CoopGame.uproject").resolve()
    require(project_file is None or Path(project_file).resolve() == expected,
            "--project-file must match the project containing this tool")
    actual = Path(unreal.Paths.convert_relative_path_to_full(
        unreal.Paths.get_project_file_path())).resolve()
    require(actual == expected, "Open editor project differs from tool project: " + str(actual))
    engine = unreal.SystemLibrary.get_engine_version()
    require(re.match(r"^5\.8\.3(?:[-+ ]|$)", engine), "Require Unreal 5.8.3: " + engine)
    parent = unreal.load_asset(PARENT)
    require(parent is not None and isinstance(parent, unreal.Material), "Missing M_Stylized material")
    require(parent.get_editor_property("blend_mode") == unreal.BlendMode.BLEND_OPAQUE,
            "M_Stylized must be opaque for this Nanite plan")
    vectors = [str(n) for n in unreal.MaterialEditingLibrary.get_vector_parameter_names(parent)]
    require("Tint" in vectors, "M_Stylized has no Tint vector parameter")
    subsystem = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    require(subsystem is not None, "Require StaticMeshEditorSubsystem")
    for name in ("get_nanite_settings", "set_nanite_settings", "add_simple_collisions",
                 "remove_collisions", "get_simple_collision_count", "get_num_uv_channels",
                 "get_lod_build_settings", "set_lod_build_settings"):
        require(callable(getattr(subsystem, name, None)), "Missing editor API: " + name)
    for name in ("AssetImportTask", "FbxImportUI", "FbxFactory", "MaterialInstanceConstantFactoryNew",
                 "ScriptCollisionShapeType"):
        require(hasattr(unreal, name), "Missing editor API: " + name)
    conflicts = disk_conflicts(manifest)
    conflicts += [p for p in planned_paths(manifest)
                  if unreal.EditorAssetLibrary.does_asset_exist(p)]
    return parent, subsystem, sorted(set(conflicts)), engine


def assert_unoccupied(unreal, package):
    require(not package_file(package).exists()
            and not package_file(package).with_suffix(".umap").exists()
            and not unreal.EditorAssetLibrary.does_asset_exist(package),
            "Refusing overwrite: " + package)


def import_options(unreal, asset):
    options = unreal.FbxImportUI()
    for key, value in {
        "automated_import_should_detect_type": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
        "original_import_type": unreal.FBXImportType.FBXIT_STATIC_MESH,
        "import_mesh": True, "import_as_skeletal": False, "import_animations": False,
        "import_materials": False, "import_textures": False,
    }.items():
        options.set_editor_property(key, value)
    data = options.get_editor_property("static_mesh_import_data")
    for key, value in {
        "import_uniform_scale": 1.0, "import_translation": unreal.Vector(0, 0, 0),
        "import_rotation": unreal.Rotator(0, 0, 0),
        "convert_scene": True, "convert_scene_unit": True, "force_front_x_axis": False,
        "transform_vertex_to_absolute": True, "bake_pivot_in_vertex": False,
        "combine_meshes": True, "auto_generate_collision": False,
        "build_nanite": False, "generate_lightmap_u_vs": False,
        "import_mesh_lo_ds": False,
        "normal_import_method": unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS,
    }.items():
        data.set_editor_property(key, value)
    return options


def check_imported_mesh(unreal, subsystem, mesh, asset):
    require(isinstance(mesh, unreal.StaticMesh), "Import did not yield a static mesh")
    slots = mesh.get_editor_property("static_materials")
    imported_names = [str(s.get_editor_property("imported_material_slot_name")) for s in slots]
    require(imported_names == asset["material_slots"],
            "Imported material slot names/order differ: " + asset["name"])
    bounds = mesh.get_bounds()
    dimensions = [2 * getattr(bounds.box_extent, axis) for axis in ("x", "y", "z")]
    expected = asset["validation_metadata"]["dimensions_cm"]
    require(all(abs(a - b) <= 0.5 for a, b in zip(dimensions, expected)),
            "Imported scale/bounds mismatch: " + asset["name"])
    require(abs(bounds.origin.z - bounds.box_extent.z) <= 0.5
            and abs(bounds.origin.x) <= 0.5 and abs(bounds.origin.y) <= 0.5,
            "Imported pivot mismatch: " + asset["name"])
    require(subsystem.get_num_uv_channels(mesh, 0) == 1, "Source UV channel count changed")
    return slots


def execute(unreal, manifest, parent, subsystem):
    # No force/reimport/skip flag. The whole batch must be unoccupied before ANY creation.
    for package in planned_paths(manifest):
        assert_unoccupied(unreal, package)
    assets = unreal.AssetToolsHelpers.get_asset_tools()
    # Build transient options first, so unsupported option properties fail before import.
    prepared = [(a, import_options(unreal, a)) for a in manifest["assets"]]
    created = []
    materials = {}
    try:
        for material in manifest["materials"]:
            package = material["destination"]
            assert_unoccupied(unreal, package)
            instance = assets.create_asset(
                material["name"], package.rsplit("/", 1)[0],
                unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
            require(instance is not None and instance.get_path_name().split(".")[0] == package,
                    "Material creation returned unexpected path")
            created.append(instance)
            unreal.MaterialEditingLibrary.set_material_instance_parent(instance, parent)
            assign_tint(unreal, instance, material["tint_srgb_hex"])
            materials[material["slot"]] = instance
        for asset, options in prepared:
            package = asset["destination"]
            assert_unoccupied(unreal, package)
            task = unreal.AssetImportTask()
            for key, value in {
                "filename": str(PROJECT_ROOT / asset["source"]),
                "destination_path": DESTINATION, "destination_name": asset["name"],
                "replace_existing": False, "replace_existing_settings": False,
                "automated": True, "save": False, "async_": False,
                "factory": unreal.FbxFactory(), "options": options,
            }.items():
                task.set_editor_property(key, value)
            assets.import_asset_tasks([task])
            imported = [str(p).split(".")[0] for p in
                        task.get_editor_property("imported_object_paths")]
            require(imported == [package], "Unexpected imported assets: " + repr(imported))
            mesh = unreal.load_asset(package)
            created.append(mesh)
            slots = check_imported_mesh(unreal, subsystem, mesh, asset)
            for index, slot_name in enumerate(asset["material_slots"]):
                mesh.set_material(index, materials[slot_name])
            build = subsystem.get_lod_build_settings(mesh, 0)
            build.set_editor_property("recompute_normals", False)
            build.set_editor_property("recompute_tangents", True)
            build.set_editor_property("use_mikk_t_space", True)
            subsystem.set_lod_build_settings(mesh, 0, build)
            # Explicit simple collision only; never complex-as-simple.
            require(subsystem.remove_collisions(mesh), "Could not clear imported collision")
            if asset["collision"]["automatic"] == "one_fitted_box":
                require(subsystem.add_simple_collisions(mesh, unreal.ScriptCollisionShapeType.BOX) >= 0,
                        "Simple box creation failed")
                require(subsystem.get_simple_collision_count(mesh) == 1, "Expected one simple box")
            else:
                require(subsystem.get_simple_collision_count(mesh) == 0,
                        "Compound collision must remain pending manual authoring")
            body = mesh.get_editor_property("body_setup")
            require(body is not None, "Missing mesh BodySetup")
            body.set_editor_property("collision_trace_flag",
                                     unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AND_COMPLEX)
            settings = subsystem.get_nanite_settings(mesh)
            settings.set_editor_property("enabled", asset["nanite"])
            settings.set_editor_property("fallback_percent_triangles", 1.0)
            settings.set_editor_property("fallback_relative_error", 0.0)
            subsystem.set_nanite_settings(mesh, settings, True)
            require(subsystem.get_nanite_settings(mesh).get_editor_property("enabled")
                    == asset["nanite"], "Nanite setting failed")
            check_imported_mesh(unreal, subsystem, mesh, asset)
        # Save ONLY the freshly created lane assets, after the batch's checks.
        for obj in created:
            require(obj is not None and obj.get_path_name().split(".")[0] in planned_paths(manifest),
                    "Refusing save outside planned destinations")
            require(unreal.EditorAssetLibrary.save_loaded_asset(obj, False),
                    "Save failed: " + obj.get_path_name())
    except Exception:
        print("HC-A2 failed; batch is not atomic. Partial unsaved or saved assets may exist. "
              "Do not rerun blindly; inspect only HCA2_Props in the editor. No automatic rollback.")
        raise
    return [obj.get_path_name() for obj in created]


def run(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Explicitly create editor assets")
    parser.add_argument("--project-file", help="Required for execution; exact absolute CoopGame.uproject")
    args = parser.parse_args(argv)
    require(not args.execute or (args.project_file and Path(args.project_file).is_absolute()),
            "Execution requires --project-file with an absolute path")
    require(args.project_file is None or Path(args.project_file).resolve()
            == (PROJECT_ROOT / "CoopGame.uproject").resolve(),
            "--project-file must match the project containing this tool")
    manifest, sources = load_plan()
    conflicts = disk_conflicts(manifest)
    report = {
        "mode": "execute" if args.execute else "dry-run",
        "source_validation": "passed", "assets": sources,
        "materials": manifest["materials"], "assemblies": manifest["assemblies"],
        "disk_conflicts": conflicts, "editor_checks": "not run (offline)",
        "remaining": ["compound collision authoring", "all collision verification",
                      "assembly and orientation checks", "cave light and split-screen checks",
                      "statue selection", "map placement and gameplay verification"],
    }
    try:
        import unreal
    except ImportError:
        require(not args.execute, "Execution requires a running Unreal 5.8.3 editor Python session")
        report["execution_ready"] = not conflicts
    else:
        parent, subsystem, conflicts, engine = editor_preflight(unreal, manifest, args.project_file)
        report.update(editor_checks="read-only preflight passed", engine=engine,
                      editor_conflicts=conflicts)
        report["execution_ready"] = not conflicts
        if args.execute:
            require(not conflicts, "Refusing occupied destinations: " + repr(conflicts))
            report["created_assets"] = execute(unreal, manifest, parent, subsystem)
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    run()
