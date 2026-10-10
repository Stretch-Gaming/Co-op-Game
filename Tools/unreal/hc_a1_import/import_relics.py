"""HC-A1 import plan. Read-only unless --execute is explicitly supplied."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
from fbx_inspect import inspect_fbx

DESTINATION = "/Game/Puzzles/Art/HCA1_Relics"
PARENT = "/Game/Shared/Style/M_Stylized"
NAMES = ("SM_Relic_GoldIdol", "SM_Relic_JadeMask", "SM_Relic_GemScarab", "SM_KeyRelic_StoneHeart")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_path(root, relative):
    path = (root / relative).resolve()
    require(path.is_relative_to((root / "SourceArt/HC/HC-A1").resolve()), "Source escapes HC-A1: " + relative)
    require(path.is_file(), "Missing source: " + relative)
    require(not path.read_bytes().startswith(b"version https://git-lfs.github.com/spec/v1"), "Unhydrated LFS pointer: " + relative)
    return path


def isolated(path):
    require(re.fullmatch(re.escape(DESTINATION) + r"/[A-Za-z][A-Za-z0-9_]*", path) is not None,
            "Destination outside isolated flat folder: " + path)
    return path


def validate(root=ROOT):
    root = Path(root).resolve()
    require(root == ROOT.resolve(), "Project root must contain this tooling checkout")
    project = root / "CoopGame.uproject"
    require(project.is_file() and list(root.glob("*.uproject")) == [project], "Expected only CoopGame.uproject")
    descriptor = json.loads(project.read_text(encoding="utf-8-sig"))
    require(descriptor.get("EngineAssociation") == "5.8", "Project must use UE 5.8")
    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf-8-sig"))
    require(manifest["destination_root"] == DESTINATION and manifest["material_parent"] == PARENT, "Altered destination or parent")
    require(tuple(a["name"] for a in manifest["assets"]) == NAMES, "Expected the four reviewed relics in order")
    destinations = []
    for material in manifest["material_proposals"]:
        require(material["name"].startswith("MI_HCA1_"), "Unscoped instance name")
        destinations.append(isolated(material["destination"]))
        require(material["destination"] == DESTINATION + "/" + material["name"], "Material name/path mismatch")
    profiles = {m["id"] for m in manifest["material_proposals"]}
    evidence = []
    for asset in manifest["assets"]:
        destinations.append(isolated(asset["destination"]))
        require(asset["destination"] == DESTINATION + "/" + asset["name"], "Mesh name/path mismatch")
        for record in asset["source_files"]:
            path = source_path(root, record["path"])
            require(digest(path) == record["sha256"], "Hash mismatch: " + record["path"])
            require(path.stat().st_size == record["size_bytes"], "Size mismatch: " + record["path"])
        fbx = source_path(root, asset["fbx_path"])
        require(asset["fbx_path"] == "SourceArt/HC/HC-A1/" + asset["name"] + ".fbx", "Unexpected FBX path")
        metadata = json.loads(source_path(root, asset["validation_path"]).read_text(encoding="utf-8"))
        require(metadata == asset["source_validation"], "Metadata differs from source report")
        require(metadata["output"] == asset["fbx_path"], "Metadata output path mismatch")
        require(metadata["UV_warning"] is None and metadata["triangles_before"] == metadata["triangles_after"] <= 10000,
                "Source validation UV or triangle gate failed")
        require(metadata["fbx_unit"] == "centimeters" and metadata["pivot"] == "base center" and metadata["up_axis"] == "+Z",
                "Source validation unit/pivot/axis gate failed")
        actual = inspect_fbx(fbx)
        require(digest(fbx) == asset["lfs_object"]["oid_sha256"] and fbx.stat().st_size == asset["lfs_object"]["size_bytes"],
                "Manifest LFS object mismatch")
        require(actual == asset["fbx_inspection"], "Binary FBX inspection mismatch: " + asset["name"])
        require(actual["triangles"] == metadata["triangles_after"] and actual["all_triangles"], "Topology mismatch")
        require(actual["material_slots"] == [s["source_slot"] for s in asset["material_slots"]], "FBX slot order mismatch")
        require(all(s["profile"] in profiles for s in asset["material_slots"]), "Unknown material profile")
        require(actual["has_normals"] and actual["uv_layer_count"] >= 1, "Normals/UV missing")
        require(actual["model_transforms"][0]["Lcl Scaling"] == [100.0] * 3, "Unexpected FBX model scale")
        require(actual["global_settings"]["UnitScaleFactor"] == 1.0, "Unexpected FBX unit scale")
        require(all(math.isclose(raw * 100, cm, abs_tol=0.001) for raw, cm in
                    zip(actual["raw_vertex_dimensions"], metadata["dimensions_cm"])), "Reported size differs from FBX/model scale")
        evidence.append({"name": asset["name"], "source_sha256": digest(fbx), "hydrated": True,
                         "source_reported_dimensions_cm": metadata["dimensions_cm"], "triangles": actual["triangles"],
                         "material_slots": actual["material_slots"], "collision": asset["collision"], "destination": asset["destination"]})
    require(len(destinations) == len(set(destinations)), "Duplicate destination")
    for record in manifest["shared_source_dependencies"]:
        path = source_path(root, record["path"])
        require(digest(path) == record["sha256"], "Dependency hash mismatch: " + record["path"])
    return manifest, {"mode": "read_only_dry_run", "project_root": str(root), "assets": evidence,
                      "proposed_material_destinations": destinations[:len(manifest["material_proposals"])],
                      "writes_performed": False, "unreal_imports_tested": False,
                      "pending": ["UE 5.8.3 editor preflight and execution", "Verified M_Stylized parameter bindings including idol emission",
                                  "Heart stone-only collision fitting", "Style, platform and gameplay acceptance"]}


def read_bindings(path, manifest):
    require(path is not None, "--material-bindings is required for execution; verify the example in the editor first")
    bindings = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    require(bindings.get("verified_in_ue_5_8_3") is True, "Material bindings need verified_in_ue_5_8_3=true after editor review")
    require(set(bindings["profiles"]) == {m["id"] for m in manifest["material_proposals"]}, "Expected every material profile")
    for values in bindings["profiles"].values():
        require(set(values) == {"scalars", "vectors"}, "Only scalar/vector instance overrides are supported")
        require(values["vectors"] and all(len(v) == 4 and all(math.isfinite(n) for n in v) for v in values["vectors"].values()), "Invalid vectors")
        require(all(math.isfinite(v) for v in values["scalars"].values()), "Invalid scalar")
    return bindings


def editor_preflight(root, manifest, bindings):
    import unreal as ue
    require(Path(ue.Paths.project_dir()).resolve() == Path(root).resolve(), "Active editor is a different project checkout")
    require(Path(ue.Paths.get_project_file_path()).resolve() == (Path(root) / "CoopGame.uproject").resolve(), "Wrong active .uproject")
    require(re.match(r"^5\.8\.3(?:[-+\s]|$)", ue.SystemLibrary.get_engine_version()) is not None, "Execution requires Unreal 5.8.3")
    actor_subsystem = ue.get_editor_subsystem(ue.UnrealEditorSubsystem)
    require(not actor_subsystem.get_game_world(), "Stop PIE before importing")
    parent = ue.load_asset(PARENT)
    require(isinstance(parent, ue.Material), "Missing M_Stylized master material")
    require(parent.get_editor_property("blend_mode") == ue.BlendMode.BLEND_OPAQUE, "Expected opaque M_Stylized for Nanite")
    scalar_names = {str(n) for n in ue.MaterialEditingLibrary.get_scalar_parameter_names(parent)}
    vector_names = {str(n) for n in ue.MaterialEditingLibrary.get_vector_parameter_names(parent)}
    if bindings:
        for profile, values in bindings["profiles"].items():
            require(set(values["scalars"]) <= scalar_names and set(values["vectors"]) <= vector_names,
                    "Unknown M_Stylized binding for " + profile + "; available scalars=" + str(sorted(scalar_names)) + ", vectors=" + str(sorted(vector_names)))
    registry = ue.AssetRegistryHelpers.get_asset_registry()
    existing = registry.get_assets_by_path(DESTINATION, recursive=True)
    # Require an entirely empty destination, including assets not named in this manifest.
    require(not existing, "Destination contains assets; no overwrite, reuse, reimport or automatic cleanup allowed")
    disk_folder = Path(root) / "Content/Puzzles/Art/HCA1_Relics"
    require(not disk_folder.exists() or not any(disk_folder.rglob("*")), "Destination folder has disk content (including unregistered packages)")
    planned = [a["destination"] for a in manifest["assets"]] + [m["destination"] for m in manifest["material_proposals"]]
    require(not any(ue.EditorAssetLibrary.does_asset_exist(p) for p in planned), "A planned package already exists")
    # Construct options before mutations so unsupported API properties fail early.
    ui = ue.FbxImportUI()
    for key, value in {"import_mesh": True, "import_as_skeletal": False, "import_materials": False,
                       "import_textures": False, "import_animations": False, "automated_import_should_detect_type": False,
                       "mesh_type_to_import": ue.FBXImportType.FBXIT_STATIC_MESH}.items():
        ui.set_editor_property(key, value)
    mesh_data = ui.get_editor_property("static_mesh_import_data")
    for key, value in {"combine_meshes": True, "auto_generate_collision": False, "build_nanite": True,
                       "convert_scene": True, "convert_scene_unit": True, "force_front_x_axis": False,
                       "import_uniform_scale": 1.0, "transform_vertex_to_absolute": True, "bake_pivot_in_vertex": False,
                       "import_mesh_lo_ds": False, "generate_lightmap_u_vs": False, "remove_degenerates": False,
                       "normal_import_method": ue.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS,
                       "reorder_material_to_fbx_order": True}.items():
        mesh_data.set_editor_property(key, value)
    mesh_data.set_editor_property("import_translation", ue.Vector(0, 0, 0))
    mesh_data.set_editor_property("import_rotation", ue.Rotator(0, 0, 0))
    # Pin the legacy FBX factory, rather than relying on Interchange defaults.
    factory = ue.FbxFactory()
    return ue, parent, ui, factory, {"engine": ue.SystemLibrary.get_engine_version(),
                                    "scalar_parameters": sorted(scalar_names), "vector_parameters": sorted(vector_names),
                                    "destination_empty": True, "execution_ready": bindings is not None}


def execute(root, manifest, bindings, context):
    ue, parent, ui, factory, _ = context
    tools = ue.AssetToolsHelpers.get_asset_tools()
    meshes = ue.get_editor_subsystem(ue.StaticMeshEditorSubsystem)
    material_paths = {}
    created = []
    try:
        for proposal in manifest["material_proposals"]:
            path = isolated(proposal["destination"])
            require(not ue.EditorAssetLibrary.does_asset_exist(path), "Package appeared during run: " + path)
            instance = tools.create_asset(proposal["name"], DESTINATION, ue.MaterialInstanceConstant,
                                          ue.MaterialInstanceConstantFactoryNew())
            require(instance is not None, "Could not create " + path)
            created.append(instance)
            ue.MaterialEditingLibrary.set_material_instance_parent(instance, parent)
            values = bindings["profiles"][proposal["id"]]
            for name, value in values["scalars"].items():
                require(ue.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(instance, name, value), "Scalar binding failed: " + name)
            for name, value in values["vectors"].items():
                require(ue.MaterialEditingLibrary.set_material_instance_vector_parameter_value(instance, name, ue.LinearColor(*value)), "Vector binding failed: " + name)
            ue.MaterialEditingLibrary.update_material_instance(instance)
            material_paths[proposal["id"]] = instance
        for asset in manifest["assets"]:
            path = isolated(asset["destination"])
            require(not ue.EditorAssetLibrary.does_asset_exist(path), "Package appeared during run: " + path)
            task = ue.AssetImportTask()
            for key, value in {"filename": str(root / asset["fbx_path"]), "destination_path": DESTINATION,
                               "destination_name": asset["name"], "automated": True, "replace_existing": False,
                               "replace_existing_settings": False, "save": False, "options": ui, "factory": factory}.items():
                task.set_editor_property(key, value)
            tools.import_asset_tasks([task])
            imported = list(task.get_editor_property("imported_object_paths"))
            require(imported == [path + "." + asset["name"]], "Unexpected importer output: " + str(imported))
            mesh = ue.load_asset(path)
            require(isinstance(mesh, ue.StaticMesh), "Import did not produce a StaticMesh")
            created.append(mesh)
            require(mesh.get_path_name() == path + "." + asset["name"], "Unexpected mesh package")
            actual_size = mesh.get_bounds().box_extent * 2.0
            require(all(math.isclose(v, cm, abs_tol=0.1) for v, cm in zip((actual_size.x, actual_size.y, actual_size.z),
                       asset["source_validation"]["dimensions_cm"])), "Imported bounds mismatch; no automatic rescaling")
            slots = list(mesh.get_editor_property("static_materials"))
            actual_slots = [str(s.get_editor_property("imported_material_slot_name")) for s in slots]
            require(actual_slots == [s["source_slot"] for s in asset["material_slots"]], "Imported slot order/name mismatch")
            for i, slot in enumerate(asset["material_slots"]):
                mesh.set_material(i, material_paths[slot["profile"]])
            if asset["collision"]["automatic"] == "box":
                require(meshes.add_simple_collisions(mesh, ue.ScriptCollisionShapeType.BOX) >= 0, "Simple collision generation failed")
            else:
                ue.log_warning("HC-A1: stone heart has NO collision yet. Fit a stone-only box manually; exclude rope loops before acceptance.")
            settings = meshes.get_nanite_settings(mesh)
            settings.set_editor_property("enabled", True)
            meshes.set_nanite_settings(mesh, settings, apply_changes=True)
        # Save only the exact assets created by this invocation, never Save All.
        for obj in created:
            isolated(obj.get_path_name().split(".")[0])
            require(ue.EditorAssetLibrary.save_loaded_asset(obj, only_if_is_dirty=False), "Failed to save " + obj.get_path_name())
    except Exception:
        ue.log_error("HC-A1 stopped. Partial/unsaved assets may exist in HCA1_Relics. No rollback or overwrite attempted. Inspect in the editor before any retry.")
        raise
    return {"mode": "executed", "created": [o.get_path_name() for o in created],
            "acceptance_pending": True, "heart_collision_pending": True}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--execute", action="store_true", help="Explicitly create and save new assets in the active UE 5.8.3 editor")
    parser.add_argument("--editor-check", action="store_true", help="Read-only active editor/API/destination/material preflight")
    parser.add_argument("--material-bindings", type=Path, help="Editor-reviewed scalar/vector bindings; required for --execute")
    args = parser.parse_args(argv)
    try:
        manifest, report = validate(args.project_root)
        root = args.project_root.resolve()
        bindings = read_bindings(args.material_bindings, manifest) if args.material_bindings else None
        context = None
        if args.editor_check or args.execute:
            if args.execute:
                require(args.material_bindings is not None, "Execution requires --material-bindings")
            context = editor_preflight(root, manifest, bindings)
            report["editor_preflight"] = context[-1]
        if args.execute:
            report = execute(root, manifest, bindings, context)
        print(json.dumps(report, indent=2))
        return 0
    except (ValueError, OSError, KeyError, ImportError) as error:
        print("HC-A1 REFUSED: " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
