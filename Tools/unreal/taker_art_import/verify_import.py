"""Read-only native verification of the ten canonical PG-A7 art assets."""
import json, math
from pathlib import Path
import unreal as ue
ROOT=Path(globals().get('ROOT','C:/Users/Stretch/.codex/worktrees/one-playable-game/Co op Game')).resolve()
HERE=ROOT/'Tools/unreal/taker_art_import'; DEST='/Game/Player/Art/Taker'
def require(ok,message):
    if not ok: raise RuntimeError(message)
def vec(v): return [v.x,v.y,v.z]
def verify_assets():
    require(Path(ue.Paths.project_dir()).resolve()==ROOT,'Wrong editor project')
    require(not ue.EditorLevelLibrary.get_pie_worlds(True),'Stop PIE first')
    manifest=json.loads((HERE/'source-manifest.json').read_text()); metrics=manifest['author_report']
    subsystem=ue.get_editor_subsystem(ue.StaticMeshEditorSubsystem); mel=ue.MaterialEditingLibrary; rows={}
    for name in ('SM_Taker','SM_TakerArm'):
        mesh=ue.load_asset(DEST+'/'+name); require(isinstance(mesh,ue.StaticMesh),'Missing static mesh '+name)
        bounds=mesh.get_bounding_box(); mins=vec(bounds.min); maxs=vec(bounds.max)
        expected=metrics[name]['bounds_cm']; expected=[expected[0],[-expected[1][1],-expected[1][0]],expected[2]]
        require(all(abs(a-b)<.25 for a,b in zip(mins,[x[0] for x in expected])) and all(abs(a-b)<.25 for a,b in zip(maxs,[x[1] for x in expected])),'Bounds/pivot/facing mismatch '+name+': '+str([mins,maxs]))
        source_count=manifest['meshes'][name]['triangles']
        nanite_count=mesh.get_num_nanite_triangles(); require(nanite_count==source_count,'Nanite source triangle count mismatch '+name)
        require(mesh.get_editor_property('nanite_settings').enabled,'Nanite unexpectedly disabled')
        require(subsystem.get_simple_collision_count(mesh)==0 and subsystem.get_convex_collision_count(mesh)==0,'Visual mesh acquired collision')
        require(subsystem.get_num_uv_channels(mesh,0)>=1,'UV0 missing')
        mats=mesh.get_editor_property('static_materials'); slots=[str(x.material_slot_name) for x in mats]
        require(slots==manifest['meshes'][name]['material_slots'],'Slots changed '+name)
        for mat in mats: require(mat.material_interface.get_path_name()==DEST+'/'+str(mat.material_slot_name)+'.'+str(mat.material_slot_name),'Slot binding wrong')
        sockets={}
        for socket,info in metrics[name]['sockets_unreal_cm'].items():
            s=mesh.find_socket(socket); require(s is not None,'Imported socket missing '+name+'/'+socket+'; no silent socket substitution')
            loc=vec(s.get_editor_property('relative_location')); require(all(abs(a-b)<.2 for a,b in zip(loc,info['location'])),'Socket location wrong '+name+'/'+socket+': '+str(loc))
            sockets[socket]=loc
        rows[name]={'path':mesh.get_path_name(),'bounds_min_cm':mins,'bounds_max_cm':maxs,'source_triangles':source_count,'nanite_triangles':nanite_count,'fallback_triangles':mesh.get_num_triangles(0),'sockets':sockets,'material_slots':slots,'collision':0,'nanite':True}
    for prefix in ('Taker','TakerArm'):
        for suffix in ('BaseColor','ORM'):
            name='T_'+prefix+'_'+suffix; a=ue.load_asset(DEST+'/'+name); require(isinstance(a,ue.Texture2D),'Missing texture '+name)
            mask=suffix=='ORM'; require(a.get_editor_property('srgb')== (not mask),'sRGB wrong '+name)
            require(a.get_editor_property('compression_settings')==(ue.TextureCompressionSettings.TC_MASKS if mask else ue.TextureCompressionSettings.TC_DEFAULT),'Compression wrong '+name)
            require([a.blueprint_get_size_x(),a.blueprint_get_size_y()]==[1024,1024],'Texture dimensions wrong')
            rows[name]={'srgb':not mask,'compression':str(a.get_editor_property('compression_settings')),'size':[1024,1024]}
        mi=ue.load_asset(DEST+'/MI_'+prefix+'_Body'); require(mi.get_editor_property('parent').get_path_name()=='/Game/Shared/Style/M_Stylized.M_Stylized','Wrong shared parent')
        expected={'GradientStrength':0.,'EdgeStrength':0.,'CavityStrength':.4,'RoughnessMultiplier':1.,'MetallicMultiplier':0.,'MetallicOffset':0.,'RimStrength':0.}
        for k,v in expected.items(): require(math.isclose(mel.get_material_instance_scalar_parameter_value(mi,k),v,abs_tol=.00001),'Body scalar wrong '+k)
        tint=mel.get_material_instance_vector_parameter_value(mi,'Tint'); require(all(abs(x-1)<.00001 for x in (tint.r,tint.g,tint.b,tint.a)),'Body tint wrong')
        for param,suffix in (('BaseColorTexture','BaseColor'),('MaskTexture','ORM')): require(mel.get_material_instance_texture_parameter_value(mi,param)==ue.load_asset(DEST+'/T_'+prefix+'_'+suffix),'Body texture binding wrong')
    eyes=ue.load_asset(DEST+'/M_TakerEyes'); require(eyes.get_editor_property('blend_mode')==ue.BlendMode.BLEND_OPAQUE and eyes.get_editor_property('shading_model')==ue.MaterialShadingModel.MSM_UNLIT,'Eye master must be opaque unlit')
    eye_mi=ue.load_asset(DEST+'/MI_Taker_Eyes'); require(eye_mi.get_editor_property('parent')==eyes,'Wrong eye master')
    require(math.isclose(mel.get_material_instance_scalar_parameter_value(eye_mi,'EyeStrength'),8.,abs_tol=.00001),'Wrong eye emission')
    require(not mel.get_material_default_static_switch_parameter_value(ue.load_asset('/Game/Shared/Style/M_Stylized'),'UseWorldAligned'),'Body UV switch default changed')
    return {'passed':True,'assets':rows,'known_warning':'Delivered body has2 boundary edges/one3-face edge near top of head. No collision; source left unchanged.','pending':['Cave/split-screen render and Mac fallback visual check','Placement/behavior integration separately authorized']}
if globals().get('ARGS',{}).get('mode')=='verify':
    RESULT=verify_assets()
    out=Path(globals().get('OUTPUT',ROOT/'Saved/NextPriorities/taker_art_import')); out.mkdir(parents=True,exist_ok=True)
    (out/'verification.json').write_text(json.dumps(RESULT,indent=2)+'\n')
