"""Use legacy FBX import to retain delivered UCX; no gameplay/root changes."""
import json,sys
sys.path.insert(0,str(HERE))
from context import *
path='/Game/Player/Art/Flares/SM_HandFlare';require_lease(path)
mesh=ue.load_asset(path);materials=[mesh.get_material(i) for i in range(4)]
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
flag='Interchange.FeatureFlags.Import.FBX'
old=ue.SystemLibrary.get_console_variable_int_value(flag)
try:
    ue.SystemLibrary.execute_console_command(world,flag+' 0')
    opts=ue.FbxImportUI()
    opts.set_editor_properties({'automated_import_should_detect_type':False,'mesh_type_to_import':ue.FBXImportType.FBXIT_STATIC_MESH,
        'original_import_type':ue.FBXImportType.FBXIT_STATIC_MESH,'import_mesh':True,'import_as_skeletal':False,
        'import_animations':False,'import_materials':False,'import_textures':False})
    opts.static_mesh_import_data.set_editor_properties({'import_uniform_scale':1.,'convert_scene':True,'convert_scene_unit':True,
        'combine_meshes':True,'auto_generate_collision':False,'one_convex_hull_per_ucx':True,'build_nanite':False,
        'normal_import_method':ue.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS})
    task=ue.AssetImportTask();task.set_editor_properties({'filename':str(ROOT/'SourceArt/PG/PG-A8/SM_HandFlare.fbx'),
        'destination_path':'/Game/Player/Art/Flares','destination_name':'SM_HandFlare','automated':True,'save':False,
        'replace_existing':True,'replace_existing_settings':True,'options':opts,'factory':ue.FbxFactory()})
    ue.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh=ue.load_asset(path)
    assert ue.get_editor_subsystem(ue.StaticMeshEditorSubsystem).get_convex_collision_count(mesh)==1
    b=mesh.get_bounds();dims=[2*b.box_extent.x,2*b.box_extent.y,2*b.box_extent.z]
    assert all(abs(a-b)<.5 for a,b in zip(dims,[6,6,22]))
    slots=[str(s.get_editor_property('imported_material_slot_name')) for s in mesh.static_materials]
    assert slots==['M_FlareMetal','M_FlareGrip','M_FlareBody','M_FlareAmber'],slots
    for i,m in enumerate(materials):mesh.set_material(i,m)
    assert ue.EditorAssetLibrary.save_loaded_asset(mesh,False)
    report=json.loads((QUEUE/'flare-import.json').read_text())
    report.update({'imported_convex_hulls':1,'fbx_importer':'Legacy FBX factory; transient Interchange flag restored. UE5.8 converter maps GenerateCollision off to all collision off, dropping UCX in automated Interchange imports.'})
    (QUEUE/'flare-import.json').write_text(json.dumps(report,indent=2));RESULT=report
finally:ue.SystemLibrary.execute_console_command(world,flag+' '+str(old))
