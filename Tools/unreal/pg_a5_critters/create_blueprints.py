"""PG-A5: create BP_CaveBat and BP_CaveMouse in /Game/Player/Critters with their components.
Their tick graphs and variables are added through Unreal MCP afterwards (see README.md).
Run in the editor with `py <this file>`. Refuses to overwrite existing Blueprints."""
import json
import traceback
from pathlib import Path

import unreal

FOLDER = "/Game/Player/Critters"
OUT = Path("/tmp/pga5_tools/out.json")
sub = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
lib = unreal.SubobjectDataBlueprintFunctionLibrary


def create_bp(name):
    path = f"{FOLDER}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        raise RuntimeError(f"{path} already exists")
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", unreal.Actor)
    return unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, FOLDER, unreal.Blueprint, factory)


def add(bp, parent_handle, cls, name):
    handle, fail = sub.add_new_subobject(unreal.AddNewSubobjectParams(
        parent_handle=parent_handle, new_class=cls, blueprint_context=bp))
    if not fail.is_empty():
        raise RuntimeError(f"{name}: {fail}")
    sub.rename_subobject(handle, unreal.Text(name))
    return handle, lib.get_object(lib.get_data(handle))


def mesh_comp(comp, mesh_path, location=(0, 0, 0), scale=(1, 1, 1)):
    comp.set_editor_property("static_mesh", unreal.load_asset(mesh_path))
    comp.set_editor_property("relative_location", unreal.Vector(*location))
    comp.set_editor_property("relative_scale3d", unreal.Vector(*scale))
    # Ambient life only: no collision, no overlap events, and nothing for navigation.
    comp.set_collision_profile_name("NoCollision")
    comp.set_editor_property("generate_overlap_events", False)
    comp.set_editor_property("can_ever_affect_navigation", False)


def bat():
    bp = create_bp("BP_CaveBat")
    root = sub.k2_gather_subobject_data_for_blueprint(bp)[0]
    # Bat: the point that orbits. The body's Blender origin sits on it, 1.5 cm behind and
    # 4.1 cm above the mesh's base-center pivot.
    h_bat, bat_c = add(bp, root, unreal.SceneComponent, "Bat")
    _, body = add(bp, h_bat, unreal.StaticMeshComponent, "Body")
    mesh_comp(body, "/Game/Player/Art/SM_Bat_Body", (1.52, 0.0, -4.08))
    # SM_Bat_Wing spreads toward -Y from its shoulder hinge at (1.94, 11.66, 0.32) cm in mesh
    # space, so it's the left wing as imported; the right one is mirrored with a Y scale of -1.
    for side, y, mirror in (("L", -2.8, 1), ("R", 2.8, -1)):
        h_hinge, hinge = add(bp, h_bat, unreal.SceneComponent, f"Hinge{side}")
        hinge.set_editor_property("relative_location", unreal.Vector(0.0, y, 1.2))
        _, wing = add(bp, h_hinge, unreal.StaticMeshComponent, f"Wing{side}")
        mesh_comp(wing, "/Game/Player/Art/SM_Bat_Wing", (-1.94, -11.66 * mirror, -0.32), (1, mirror, 1))
    return bp


def mouse():
    bp = create_bp("BP_CaveMouse")
    root = sub.k2_gather_subobject_data_for_blueprint(bp)[0]
    _, m = add(bp, root, unreal.StaticMeshComponent, "Mouse")
    mesh_comp(m, "/Game/Player/Art/SM_Mouse")
    return bp


try:
    made = [bat(), mouse()]
    for bp in made:
        cdo = unreal.get_default_object(bp.generated_class())
        cdo.set_editor_property("replicates", False)   # cosmetic: each machine animates its own copy
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
    result = {"created": [bp.get_path_name() for bp in made]}
except Exception:
    result = {"error": traceback.format_exc()}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=1))
