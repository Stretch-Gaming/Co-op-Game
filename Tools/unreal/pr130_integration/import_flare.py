"""Import PG-A8 and add presentation only; preserve the deployed swept root."""
import hashlib, json, sys
sys.path.insert(0,str(HERE))
from context import *

base='/Game/Player/Art/Flares'
paths=[base+'/'+n for n in ('SM_HandFlare','SFX_Flare_Hiss_Loop','MI_FlareMetal','MI_FlareGrip','MI_FlareBody','M_FlareEmber')]
for p in paths:require_lease(p)
require_lease('/Game/Player/Tools/BP_Flare')
assert ARGS.get('resume',False) or not any(ue.EditorAssetLibrary.does_asset_exist(p) for p in paths), 'Import destinations must be unoccupied'
tools=ue.AssetToolsHelpers.get_asset_tools()
parent=ue.load_asset('/Game/Shared/Style/M_Stylized');assert parent
materials=[]
for name,tint,roughness,metal in [('MI_FlareMetal',(0.013,0.018,0.033,1),.48,.45),
                                 ('MI_FlareGrip',(.15,.075,.03,1),.85,0.),
                                 ('MI_FlareBody',(.55,.35,.12,1),.8,0.)]:
    m=ue.load_asset(base+'/'+name) or tools.create_asset(name,base,ue.MaterialInstanceConstant,ue.MaterialInstanceConstantFactoryNew());assert m
    ue.MaterialEditingLibrary.set_material_instance_parent(m,parent)
    ue.MaterialEditingLibrary.set_material_instance_vector_parameter_value(m,'Tint',ue.LinearColor(*tint))
    ue.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(m,'RoughnessMultiplier',roughness)
    ue.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(m,'MetallicMultiplier',metal)
    ue.MaterialEditingLibrary.update_material_instance(m)
    assert ue.EditorAssetLibrary.save_loaded_asset(m,False)
    materials.append(m)
ember=ue.load_asset(base+'/M_FlareEmber') or tools.create_asset('M_FlareEmber',base,ue.Material,ue.MaterialFactoryNew());assert ember
ue.MaterialEditingLibrary.delete_all_material_expressions(ember)
ember.set_editor_property('shading_model',ue.MaterialShadingModel.MSM_UNLIT)
color=ue.MaterialEditingLibrary.create_material_expression(ember,ue.MaterialExpressionConstant3Vector,-500,0)
color.set_editor_property('constant',ue.LinearColor(1,.4508,.063,1))
burn=ue.MaterialEditingLibrary.create_material_expression(ember,ue.MaterialExpressionScalarParameter,-500,180)
burn.set_editor_property('parameter_name','Burn');burn.set_editor_property('default_value',1.)
multiply=ue.MaterialEditingLibrary.create_material_expression(ember,ue.MaterialExpressionMultiply,-200,0)
assert ue.MaterialEditingLibrary.connect_material_expressions(color,'',multiply,'A')
assert ue.MaterialEditingLibrary.connect_material_expressions(burn,'',multiply,'B')
assert ue.MaterialEditingLibrary.connect_material_property(multiply,'',ue.MaterialProperty.MP_EMISSIVE_COLOR)
ue.MaterialEditingLibrary.recompile_material(ember)
assert ue.EditorAssetLibrary.save_loaded_asset(ember,False)
materials.append(ember)

opts=ue.FbxImportUI()
opts.set_editor_properties({'automated_import_should_detect_type':False,'mesh_type_to_import':ue.FBXImportType.FBXIT_STATIC_MESH,
    'original_import_type':ue.FBXImportType.FBXIT_STATIC_MESH,'import_mesh':True,'import_as_skeletal':False,
    'import_animations':False,'import_materials':False,'import_textures':False})
opts.static_mesh_import_data.set_editor_properties({'import_uniform_scale':1.,'convert_scene':True,'convert_scene_unit':True,
    'combine_meshes':True,'auto_generate_collision':False,'one_convex_hull_per_ucx':True,'build_nanite':False,
    'normal_import_method':ue.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS})
task=ue.AssetImportTask();task.set_editor_properties({'filename':str(ROOT/'SourceArt/PG/PG-A8/SM_HandFlare.fbx'),
    'destination_path':base,'destination_name':'SM_HandFlare','automated':True,'save':True,'options':opts})
if not ue.EditorAssetLibrary.does_asset_exist(base+'/SM_HandFlare'):
    # UE5.8's Interchange converter maps auto_generate_collision=False to
    # bCollision=False, which also drops delivered UCX. Legacy honors UCX.
    world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
    flag='Interchange.FeatureFlags.Import.FBX';old=ue.SystemLibrary.get_console_variable_int_value(flag)
    try:
        ue.SystemLibrary.execute_console_command(world,flag+' 0')
        task.set_editor_property('factory',ue.FbxFactory())
        tools.import_asset_tasks([task])
    finally:ue.SystemLibrary.execute_console_command(world,flag+' '+str(old))
mesh=ue.load_asset(base+'/SM_HandFlare');assert isinstance(mesh,ue.StaticMesh)
assert ue.get_editor_subsystem(ue.StaticMeshEditorSubsystem).get_convex_collision_count(mesh)==1
slots=[str(s.get_editor_property('imported_material_slot_name')) for s in mesh.static_materials]
assert slots==['M_FlareMetal','M_FlareGrip','M_FlareBody','M_FlareAmber'], slots
b=mesh.get_bounds();dims=[2*b.box_extent.x,2*b.box_extent.y,2*b.box_extent.z]
assert all(abs(a-b)<.5 for a,b in zip(dims,[6,6,22])), dims
assert abs(b.origin.z-b.box_extent.z)<.5
for i,m in enumerate(materials):mesh.set_material(i,m)
assert ue.EditorAssetLibrary.save_loaded_asset(mesh,False)
audio_task=ue.AssetImportTask();audio_task.set_editor_properties({'filename':str(ROOT/'SourceArt/PG/PG-A8/SFX_Flare_Hiss_Loop.wav'),
    'destination_path':base,'destination_name':'SFX_Flare_Hiss_Loop','automated':True,'save':True})
if not ue.EditorAssetLibrary.does_asset_exist(base+'/SFX_Flare_Hiss_Loop'):tools.import_asset_tasks([audio_task])
sound=ue.load_asset(base+'/SFX_Flare_Hiss_Loop');assert isinstance(sound,ue.SoundWave)
sound.set_editor_property('looping',True)
assert ue.EditorAssetLibrary.save_loaded_asset(sound,False)

bp=ue.load_asset('/Game/Player/Tools/BP_Flare')
before=json.loads((QUEUE/'baseline.json').read_text())['flare_graphs']
root,root_handle=component(bp,'FlareRoot',ue.StaticMeshComponent)
root_before={p:str(root.get_editor_property(p)) for p in ('static_mesh','relative_scale3d')}
collision_before=str(root.get_collision_profile_name())
visual,visual_handle=component(bp,'FlareVisual',ue.StaticMeshComponent)
sds=ue.get_engine_subsystem(ue.SubobjectDataSubsystem)
assert sds.attach_subobject(root_handle,visual_handle)
visual.set_static_mesh(mesh)
visual.set_editor_properties({'absolute_scale':True,'relative_scale3d':ue.Vector(1,1,1),'relative_location':ue.Vector(0,0,-50)})
visual.set_collision_enabled(ue.CollisionEnabled.NO_COLLISION)
root.set_editor_property('visible',False) # Does not propagate to the independently visible child.
light,_=component(bp,'FlareLight',ue.PointLightComponent)
light.set_editor_properties({'absolute_scale':True,'relative_location':ue.Vector(0,0,8/.22)})
light.set_light_color(ue.LinearColor(1,.4508,.063,1))
audio,audio_handle=component(bp,'FlareHiss',ue.AudioComponent)
assert sds.attach_subobject(root_handle,audio_handle)
attenuation=ue.SoundAttenuationSettings()
attenuation.set_editor_properties({'attenuate':True,'spatialize':True,'attenuation_shape_extents':ue.Vector(30,0,0),'falloff_distance':370.})
audio.set_editor_properties({'sound':sound,'auto_activate':False,'allow_spatialization':True,
    'override_attenuation':True,'attenuation_overrides':attenuation,'volume_multiplier':.25})
var(bp,'FlareEmberDynamic',ue.MaterialInstanceDynamic.static_class())
fn(bp,'RefreshFlarePresentation');fn(bp,'StopFlarePresentation')
write(bp,'StopFlarePresentation',f'''
 (Audio|Components|Audio|Stop :self {V('FlareHiss')})
 (Utilities|IsValid :InputObject {V('FlareEmberDynamic')}
  (:"Is Valid" (Rendering|Material|SetScalarParameterValue :self {V('FlareEmberDynamic')} :ParameterName "Burn" :Value 0.0)) (:"Is Not Valid"))''')
active_body=f'''(Rendering|Material|SetScalarParameterValue :self {V('FlareEmberDynamic')} :ParameterName "Burn" :Value 1.0)
 (if (not (Audio|Components|Audio|IsPlaying :self {V('FlareHiss')})) (Audio|Components|Audio|Play :self {V('FlareHiss')}))'''
write(bp,'RefreshFlarePresentation',f'''
 (bind active (CallFunction|IsBurningFlare))
 (if active
  (Utilities|IsValid :InputObject {V('FlareEmberDynamic')}
   (:"Is Valid" {active_body})
   (:"Is Not Valid"
    {S('FlareEmberDynamic',f'(Rendering|Material|CreateDynamicMaterialInstance :self {V("FlareVisual")} :ElementIndex 3)')}
    (Utilities|IsValid :InputObject {V('FlareEmberDynamic')}
     (:"Is Valid" {active_body}) (:"Is Not Valid" (CallFunction|StopFlarePresentation)))))
  (else (CallFunction|StopFlarePresentation)))''')

def prepend(name,helper):
    graph=BP.get_graph(bp,name)
    entries=[n for n in BP.find_nodes(graph) if n.get_class().get_name()=='K2Node_FunctionEntry'];assert len(entries)==1
    pin=entries[0].find_then_pin();targets=list(pin.list_connected_pins());assert len(targets)==1
    if BP._get_node_info(targets[0].get_owning_node()).type_id.endswith('|'+helper):return
    call=BP.create_node(graph,'CallFunction|'+helper,ue.IntPoint(250,-300),declaring_class=bp.generated_class())
    pin.break_single_pin_link(targets[0])
    assert pin.try_create_connection(call.find_execute_pin())
    assert call.find_then_pin().try_create_connection(targets[0])
prepend('RefreshFlare','RefreshFlarePresentation');prepend('EndFlare','StopFlarePresentation')
save(bp)
after={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}
assert all(after[n]==d for n,d in before.items() if n not in ('RefreshFlare','EndFlare'))
assert root_before=={p:str(root.get_editor_property(p)) for p in root_before}
assert str(root.get_collision_profile_name())==collision_before
report={'assets':paths,'mesh_dimensions_cm':dims,'material_slots':slots,'source_license':'CC0 1.0; SourceArt/PG/PG-A8/README.md',
        'collision_root_preserved':True,'visual_parent_offset_cm':-11,'root_scale_preserved':[.06,.06,.22],
        'changed_existing_graphs':['RefreshFlare','EndFlare'],'new_helpers':['RefreshFlarePresentation','StopFlarePresentation'],'light_tip_offset_cm':8,
        'source_hashes':{n:hashlib.sha256((ROOT/'SourceArt/PG/PG-A8'/n).read_bytes()).hexdigest() for n in ('SM_HandFlare.fbx','SFX_Flare_Hiss_Loop.wav')}}
(QUEUE/'flare-import.json').write_text(json.dumps(report,indent=2));RESULT=report
