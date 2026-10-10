"""PG-A5: import the bat and rat meshes from SourceArt/PG/PG-A5 into /Game/Player/Art and give
each material slot an instance of the shared M_Stylized. Run in the editor with `py <this file>`.
Safe to rerun: it reimports over the same assets and resets the instances."""
import json
import traceback
from pathlib import Path

import unreal

REPO = Path(__file__).resolve().parents[3]
SRC = REPO / "SourceArt" / "PG" / "PG-A5"
DEST = "/Game/Player/Art"
OUT = Path("/tmp/pga5_tools/out.json")
MESHES = ["SM_Bat_Body", "SM_Bat_Wing", "SM_Bat_Hanging", "SM_Rat"]


def linear(hex_color):
    h = hex_color.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return unreal.LinearColor(c[0], c[1], c[2], 1.0)


# Slot name in the FBX (the Blender material) -> instance name, tint and scalar overrides.
# The tints match build_critters.py. Fur stays matte; eyes are glossy so they catch a headlamp.
# The rat's eyes also glow faintly: M_Stylized has no emissive input, so a rim exponent of 0 makes
# its rim term constant, and RimColor and RimStrength set the glow (as HC-A1's idol does).
MATERIALS = {
    "Bat_Fur": ("MI_Bat_Fur", "#5C4B58", {"RoughnessMultiplier": 0.95}),
    "Bat_Membrane": ("MI_Bat_Membrane", "#3B3142", {"RoughnessMultiplier": 0.8}),
    "Rat_Fur": ("MI_Rat_Fur", "#1C1920", {"RoughnessMultiplier": 1.0, "EdgeStrength": 0.5}),
    "Rat_Belly": ("MI_Rat_Belly", "#302B33", {"RoughnessMultiplier": 1.0}),
    "Rat_Skin": ("MI_Rat_Skin", "#5A4346", {"RoughnessMultiplier": 0.6}),
    "Rat_Eye": ("MI_Rat_Eye", "#7A1214", {"RoughnessMultiplier": 0.1, "GradientStrength": 0.0, "EdgeStrength": 0.0,
                                         "RimExponent": 0.0, "RimStrength": 0.35}, {"RimColor": "#7A1214"}),
    "Rat_Teeth": ("MI_Rat_Teeth", "#CDBB8C", {"RoughnessMultiplier": 0.4, "GradientStrength": 0.0}),
    "Critter_Skin": ("MI_Critter_Skin", "#C98F8C", {"RoughnessMultiplier": 0.65}),
    "Critter_Eye": ("MI_Critter_Eye", "#17121A", {"RoughnessMultiplier": 0.15, "GradientStrength": 0.0, "EdgeStrength": 0.0}),
    "Critter_Fang": ("MI_Critter_Fang", "#E8DCC6", {"RoughnessMultiplier": 0.5, "GradientStrength": 0.0}),
}
# Shared by every instance: a softer gradient than the default, no metal, and a faint rim so
# a dark bat still separates from dark rock.
COMMON = {"GradientStrength": 0.35, "MetallicMultiplier": 0.0, "RimStrength": 0.06}


def make_instances():
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    parent = unreal.load_asset("/Game/Shared/Style/M_Stylized")
    mel = unreal.MaterialEditingLibrary
    made = {}
    for slot, (name, tint, scalars, *vectors) in MATERIALS.items():
        path = f"{DEST}/{name}"
        mi = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else \
            tools.create_asset(name, DEST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mi.set_editor_property("parent", parent)
        mel.clear_all_material_instance_parameters(mi)
        mel.set_material_instance_vector_parameter_value(mi, "Tint", linear(tint))
        for k, v in {**COMMON, **scalars}.items():
            mel.set_material_instance_scalar_parameter_value(mi, k, v)
        for k, v in (vectors[0] if vectors else {}).items():
            mel.set_material_instance_vector_parameter_value(mi, k, linear(v))
        mel.update_material_instance(mi)
        made[slot] = mi
    return made


def import_mesh(name):
    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", True)
    ui.set_editor_property("import_as_skeletal", False)
    ui.set_editor_property("import_materials", False)
    ui.set_editor_property("import_textures", False)
    ui.set_editor_property("import_animations", False)
    ui.set_editor_property("automated_import_should_detect_type", False)
    ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    sm = ui.static_mesh_import_data
    sm.set_editor_property("combine_meshes", True)
    sm.set_editor_property("auto_generate_collision", False)
    sm.set_editor_property("generate_lightmap_u_vs", True)
    sm.set_editor_property("build_nanite", False)
    sm.set_editor_property("normal_import_method", unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
    sm.set_editor_property("convert_scene", True)
    sm.set_editor_property("transform_vertex_to_absolute", True)
    sm.set_editor_property("import_uniform_scale", 1.0)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(SRC / f"{name}.fbx"))
    task.set_editor_property("destination_path", DEST)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", False)
    task.set_editor_property("options", ui)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return unreal.load_asset(f"{DEST}/{name}")


def main():
    out = {}
    mis = make_instances()
    for name in MESHES:
        mesh = import_mesh(name)
        if not mesh:
            out[name] = "import failed"
            continue
        mats = list(mesh.get_editor_property("static_materials"))
        slots = []
        for i, m in enumerate(mats):
            slot = str(m.material_slot_name)
            mi = mis.get(slot)
            if mi:
                m.material_interface = mi
                mats[i] = m
            slots.append([slot, mi.get_name() if mi else "UNMATCHED"])
        mesh.set_editor_property("static_materials", mats)
        # Ambient creatures: nothing collides with them, and they're too small for Nanite.
        body = mesh.get_editor_property("body_setup")
        if body:
            body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_SIMPLE_AS_COMPLEX)
            unreal.EditorStaticMeshLibrary.remove_collisions(mesh)
        nanite = mesh.get_editor_property("nanite_settings")
        nanite.set_editor_property("enabled", False)
        mesh.set_editor_property("nanite_settings", nanite)
        b = mesh.get_bounding_box()
        out[name] = {"slots": slots, "tris": unreal.EditorStaticMeshLibrary.get_number_verts(mesh, 0),
                     "min": [round(v, 2) for v in b.min.to_tuple()], "max": [round(v, 2) for v in b.max.to_tuple()]}
    unreal.EditorAssetLibrary.save_directory(DEST, only_if_is_dirty=True, recursive=False)
    return out


try:
    result = main()
except Exception:
    result = {"error": traceback.format_exc()}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, indent=1))
