import sys,importlib,json,unreal as ue
sys.path.insert(0,str(HERE));import authoring;importlib.reload(authoring)
from authoring import BP,save
source=ue.load_asset('/Game/Puzzles/Art/HCA2_Props/SM_ChamberGate_Leaf');path='/Game/Puzzles/EnvironmentConnection/Art/SM_ConnectionDoor'
mesh=ue.load_asset(path)
if not mesh:
 dynamic=ue.DynamicMesh();dynamic,result=ue.GeometryScript_AssetUtils.copy_mesh_from_static_mesh(source,dynamic,ue.GeometryScriptCopyMeshFromAssetOptions(),ue.GeometryScriptMeshReadLOD())
 assert result==ue.GeometryScriptOutcomePins.SUCCESS,result
 ue.GeometryScript_MeshTransforms.translate_mesh(dynamic,source.get_bounds().origin*-1.)
 options=ue.GeometryScriptCreateNewStaticMeshAssetOptions();options.enable_nanite=False;options.enable_collision=True;options.collision_mode=ue.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
 mesh,result=ue.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dynamic,path,options);assert mesh
 for index,item in enumerate(source.get_editor_property('static_materials')):mesh.set_material(index,item.material_interface)
 assert ue.EditorAssetLibrary.save_loaded_asset(mesh,False)
bp=ue.load_asset('/Game/Puzzles/EnvironmentConnection/BP_EnvironmentDoor');BP.get_default_object(bp).static_mesh_component.set_static_mesh(mesh);save(bp)
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world();sub=ue.GameplayStatics.get_streaming_level(world,'L_ConnectedMaze');ue.EditorLevelUtils.make_level_current(sub)
door=next(a for a in ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors()if a.get_actor_label()=='Connected_Door')
door.static_mesh_component.set_static_mesh(mesh);b=mesh.get_bounds();door.set_actor_scale3d(ue.Vector(300/(b.box_extent.x*2),35/(b.box_extent.y*2),400/(b.box_extent.z*2)));door.set_actor_location(ue.Vector(325,1400,200),False,True)
assert ue.EditorLoadingAndSavingUtils.save_packages([sub.get_loaded_level().get_outermost()],False)
RESULT={'door_mesh_center':str(mesh.get_bounds().origin),'door_location':str(door.get_actor_location()),'door_bounds':str(door.get_actor_bounds(False))}
(OUTPUT/'door-centered.json').write_text(json.dumps(RESULT,indent=2))
