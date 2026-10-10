"""PG-A7 exact-delivery import, editor only. Default is read-only preflight.
Run through playable_game/run_priorities.py with ARGS mode='preflight' or 'execute'.
No actor placement, Blueprint edits, behavior integration, or shared-parent writes.
"""
import hashlib, json, math, re
from pathlib import Path
import unreal as ue
EXPECTED_ROOT=Path('C:/Users/Stretch/.codex/worktrees/one-playable-game/Co op Game').resolve()
ROOT=Path(globals().get('ROOT',EXPECTED_ROOT)).resolve()
HERE=ROOT/'Tools/unreal/taker_art_import'
DEST='/Game/Player/Art/Taker'
PARENT='/Game/Shared/Style/M_Stylized'
NAMES=('SM_Taker','SM_TakerArm','T_Taker_BaseColor','T_Taker_ORM','T_TakerArm_BaseColor','T_TakerArm_ORM','MI_Taker_Body','MI_TakerArm_Body','M_TakerEyes','MI_Taker_Eyes')
SCALARS={'GradientStrength':0.,'EdgeStrength':0.,'CavityStrength':.4,'RoughnessMultiplier':1.,'MetallicMultiplier':0.,'MetallicOffset':0.,'RimStrength':0.}
VECTORS={'Tint':(1.,1.,1.,1.),'GradientBottomColor':(.012983,.017642,.033105,1.)}
ARGS=globals().get('ARGS',{})
def require(value,message):
    if not value: raise RuntimeError(message)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def report(name,data):
    out=Path(globals().get('OUTPUT',ROOT/'Saved/NextPriorities/taker_art_import'))
    require(out.resolve().is_relative_to((ROOT/'Saved').resolve()),'Evidence output outside Saved')
    out.mkdir(parents=True,exist_ok=True); (out/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
def linear(hexcolor):
    values=[int(hexcolor[i:i+2],16)/255 for i in (0,2,4)]
    return [v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values]+[1.]
def preflight():
    require(ROOT==EXPECTED_ROOT,'Wrong assigned checkout')
    require(Path(ue.Paths.project_dir()).resolve()==ROOT,'Editor has another project open')
    require(Path(ue.Paths.get_project_file_path()).resolve()==ROOT/'CoopGame.uproject','Wrong project file')
    require(re.match(r'^5\.8\.3(?:[-+\s]|$)',ue.SystemLibrary.get_engine_version()),'Requires UE5.8.3')
    require(not ue.EditorLevelLibrary.get_pie_worlds(True),'Stop PIE first')
    manifest=json.loads((HERE/'source-manifest.json').read_text())
    for f in manifest['files']:
        p=(ROOT/f['path']).resolve()
        require(p.is_relative_to((ROOT/'SourceArt/PG/PG-A7').resolve()),'Source path outside PG-A7')
        require(p.stat().st_size==f['bytes'] and sha(p)==f['sha256'],'Source changed: '+f['path'])
    require(manifest['source_commit']=='60ae5e0250e790f943064f54e400574e8285463c','Unexpected source revision')
    parent=ue.load_asset(PARENT); require(isinstance(parent,ue.Material),'Missing shared M_Stylized')
    require(parent.get_editor_property('blend_mode')==ue.BlendMode.BLEND_OPAQUE,'Shared master not opaque')
    mel=ue.MaterialEditingLibrary
    scalars=set(map(str,mel.get_scalar_parameter_names(parent)))
    vectors=set(map(str,mel.get_vector_parameter_names(parent)))
    textures=set(map(str,mel.get_texture_parameter_names(parent)))
    require(set(SCALARS)<=scalars and set(VECTORS)<=vectors,'Shared material parameter schema changed')
    require({'BaseColorTexture','MaskTexture'}<=textures,'Shared master texture parameter schema changed')
    require(not mel.get_material_default_static_switch_parameter_value(parent,'UseWorldAligned'),'Shared parent UV default changed; do not edit shared master')
    registry=ue.AssetRegistryHelpers.get_asset_registry()
    require(not registry.get_assets_by_path(DEST,True),'Taker destination already contains assets; refuses overwrite/reimport')
    disk=ROOT/'Content/Player/Art/Taker'
    require(not disk.exists() or not any(disk.rglob('*')),'Taker destination has unregistered disk content')
    require(not any(ue.EditorAssetLibrary.does_asset_exist(DEST+'/'+n) for n in NAMES),'Planned path occupied')
    options=ue.FbxImportUI()
    for key,val in {'import_mesh':True,'import_as_skeletal':False,'import_materials':False,'import_textures':False,'import_animations':False,'automated_import_should_detect_type':False,'mesh_type_to_import':ue.FBXImportType.FBXIT_STATIC_MESH}.items(): options.set_editor_property(key,val)
    for key,val in {'combine_meshes':True,'auto_generate_collision':False,'build_nanite':True,'convert_scene':True,'convert_scene_unit':True,'force_front_x_axis':False,'import_uniform_scale':1.,'transform_vertex_to_absolute':True,'bake_pivot_in_vertex':False,'import_mesh_lo_ds':False,'generate_lightmap_u_vs':False,'remove_degenerates':False,'normal_import_method':ue.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS,'reorder_material_to_fbx_order':True}.items(): options.static_mesh_import_data.set_editor_property(key,val)
    options.static_mesh_import_data.set_editor_property('import_translation',ue.Vector())
    options.static_mesh_import_data.set_editor_property('import_rotation',ue.Rotator())
    require(ue.get_editor_subsystem(ue.StaticMeshEditorSubsystem) is not None,'Full editor required')
    parent_file=ROOT/'Content/Shared/Style/M_Stylized.uasset'
    return manifest,parent,options,{'engine':ue.SystemLibrary.get_engine_version(),'paths':[DEST+'/'+n for n in NAMES],'parent_sha256':sha(parent_file),'topology_warning':manifest['meshes']['SM_Taker']['edge_anomalies'],'writes_performed':False,'uv_mode':'inherited UseWorldAligned=False'}
def asset_task(name,source,options=None,factory=None):
    task=ue.AssetImportTask()
    for key,val in {'filename':str(source),'destination_path':DEST,'destination_name':name,'automated':True,'replace_existing':False,'save':False}.items(): task.set_editor_property(key,val)
    if options: task.set_editor_property('options',options)
    if factory: task.set_editor_property('factory',factory)
    ue.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    require(list(task.imported_object_paths)==[DEST+'/'+name+'.'+name],'Importer produced unexpected package(s): '+str(task.imported_object_paths))
    return ue.load_asset(DEST+'/'+name)
def make_instance(name,parent):
    mi=ue.AssetToolsHelpers.get_asset_tools().create_asset(name,DEST,ue.MaterialInstanceConstant,ue.MaterialInstanceConstantFactoryNew())
    require(mi is not None,'Create failed '+name); ue.MaterialEditingLibrary.set_material_instance_parent(mi,parent); return mi
def body_instance(name,prefix,parent,assets):
    mi=make_instance(name,parent); mel=ue.MaterialEditingLibrary
    for k,v in SCALARS.items():
        mel.set_material_instance_scalar_parameter_value(mi,k,v)
        require(math.isclose(mel.get_material_instance_scalar_parameter_value(mi,k),v,abs_tol=.00001),'Scalar mismatch '+k)
    for k,v in VECTORS.items(): mel.set_material_instance_vector_parameter_value(mi,k,ue.LinearColor(*v))
    for parameter,suffix in [('BaseColorTexture','_BaseColor'),('MaskTexture','_ORM')]:
        mel.set_material_instance_texture_parameter_value(mi,parameter,assets['T_'+prefix+suffix])
        require(mel.get_material_instance_texture_parameter_value(mi,parameter)==assets['T_'+prefix+suffix],'Texture binding mismatch')
    mel.update_material_instance(mi); return mi
def execute():
    manifest,parent,options,evidence=preflight(); assets={}
    for name in NAMES[2:6]:
        a=asset_task(name,ROOT/'SourceArt/PG/PG-A7/textures'/(name+'.png'))
        require(isinstance(a,ue.Texture2D),'Texture import class mismatch')
        mask=name.endswith('_ORM'); a.set_editor_property('srgb',not mask)
        a.set_editor_property('compression_settings',ue.TextureCompressionSettings.TC_MASKS if mask else ue.TextureCompressionSettings.TC_DEFAULT)
        assets[name]=a
    assets['MI_Taker_Body']=body_instance('MI_Taker_Body','Taker',parent,assets)
    assets['MI_TakerArm_Body']=body_instance('MI_TakerArm_Body','TakerArm',parent,assets)
    eye=ue.AssetToolsHelpers.get_asset_tools().create_asset('M_TakerEyes',DEST,ue.Material,ue.MaterialFactoryNew()); require(eye,'Eye material creation failed')
    eye.set_editor_property('blend_mode',ue.BlendMode.BLEND_OPAQUE); eye.set_editor_property('shading_model',ue.MaterialShadingModel.MSM_UNLIT)
    mel=ue.MaterialEditingLibrary
    color=mel.create_material_expression(eye,ue.MaterialExpressionVectorParameter,-400,0)
    color.set_editor_property('parameter_name','EyeColor'); color.set_editor_property('default_value',ue.LinearColor(*linear('D6F0FF')))
    strength=mel.create_material_expression(eye,ue.MaterialExpressionScalarParameter,-400,160)
    strength.set_editor_property('parameter_name','EyeStrength'); strength.set_editor_property('default_value',8.)
    multiply=mel.create_material_expression(eye,ue.MaterialExpressionMultiply,-160,0)
    require(mel.connect_material_expressions(color,'',multiply,'A'),'Eye color link failed')
    require(mel.connect_material_expressions(strength,'',multiply,'B'),'Eye strength link failed')
    require(mel.connect_material_property(multiply,'',ue.MaterialProperty.MP_EMISSIVE_COLOR),'Emissive link failed')
    mel.recompile_material(eye); assets['M_TakerEyes']=eye
    assets['MI_Taker_Eyes']=make_instance('MI_Taker_Eyes',eye)
    mel.set_material_instance_vector_parameter_value(assets['MI_Taker_Eyes'],'EyeColor',ue.LinearColor(*linear('D6F0FF')))
    mel.set_material_instance_scalar_parameter_value(assets['MI_Taker_Eyes'],'EyeStrength',8.); mel.update_material_instance(assets['MI_Taker_Eyes'])
    for name in NAMES[:2]:
        mesh=asset_task(name,ROOT/'SourceArt/PG/PG-A7'/(name+'.fbx'),options,ue.FbxFactory())
        require(isinstance(mesh,ue.StaticMesh),'Mesh import class mismatch')
        mats=list(mesh.get_editor_property('static_materials')); actual=[str(m.material_slot_name) for m in mats]
        require(actual==manifest['meshes'][name]['material_slots'],'Material slot/order mismatch '+name)
        for i,mat in enumerate(mats): mat.material_interface=assets[str(mat.material_slot_name)]; mats[i]=mat
        mesh.set_editor_property('static_materials',mats)
        ue.EditorStaticMeshLibrary.remove_collisions(mesh)
        nanite=mesh.get_editor_property('nanite_settings'); nanite.set_editor_property('enabled',True); mesh.set_editor_property('nanite_settings',nanite)
        assets[name]=mesh
    require(set(assets)==set(NAMES),'Unexpected asset set')
    # Verify before saving. A failure leaves newly created assets for primary inspection;
    # there is deliberately no delete/rollback of editor assets or source files.
    exec(compile((HERE/'verify_import.py').read_text(encoding='utf-8-sig'),str(HERE/'verify_import.py'),'exec'),globals())
    verification=verify_assets()
    for name in NAMES: require(ue.EditorAssetLibrary.save_loaded_asset(assets[name],False),'Save failed '+name)
    require(sha(ROOT/'Content/Shared/Style/M_Stylized.uasset')==evidence['parent_sha256'],'Shared parent bytes changed')
    evidence.update({'writes_performed':True,'verification':verification,'saved_paths':[assets[n].get_path_name() for n in NAMES]})
    report('import',evidence); return evidence
mode=ARGS.get('mode','preflight')
if mode=='execute': RESULT=execute()
elif mode=='preflight':
    _,_,_,RESULT=preflight(); report('preflight',RESULT)
else: raise RuntimeError('Expected mode preflight or execute')
