"""Parent-only bounded HC import/presentation with durable stage and error receipt.
Inspect first in stopped PIE on the exact primary checkout. Native execution is parent-owned.
"""
import json
import traceback
from datetime import datetime, timezone
from pathlib import Path

RECEIPT_PATH=Path('/tmp/hc-a4-crystal-lock/unreal-root-continuation-receipt.json')
RECEIPT_STATE={'run_started_utc':datetime.now(timezone.utc).isoformat(),'status':'running',
    'stage':'preflight','mutation_started':False,'first_mutation_stage':None,
    'stage_history':[],'created_assets':[],'saved_packages':[],'manifest':None}

def persist_receipt():
    RECEIPT_PATH.parent.mkdir(parents=True,exist_ok=True)
    temporary=RECEIPT_PATH.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(RECEIPT_STATE,indent=2)+'\n')
    temporary.replace(RECEIPT_PATH)

def stage(name,mutation=False,detail=None):
    RECEIPT_STATE['stage']=name
    RECEIPT_STATE['stage_history'].append({'stage':name,'utc':datetime.now(timezone.utc).isoformat(),'mutation':mutation,'detail':detail})
    if mutation:
        RECEIPT_STATE['mutation_started']=True
        if RECEIPT_STATE['first_mutation_stage'] is None:RECEIPT_STATE['first_mutation_stage']=name
    persist_receipt()

persist_receipt()

def run_import():
    """Parent-only bounded HC import/presentation. Inspect first; no global saves or map loads.

    Native execution remains untested until the parent runs this in stopped PIE on primary.
    Keeps the old sphere root/collider and server state, adds only a local visual child/MID.
    """
    import hashlib
    import importlib.util
    import json
    from pathlib import Path
    import unreal as ue

    PRIMARY=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary').resolve()
    BASE='/Game/Puzzles/Art/CrystalLock'
    BP_PATH='/Game/Puzzles/BP_CrystalLock'
    HC_LEVEL='/Game/Puzzles/Test/SixRound/L_SixRound_HC_Test'
    ASSETS=[BASE+'/'+n for n in ('SM_CrystalLock','MI_CrystalLockStone','M_CrystalLockCrystal')]
    MANIFEST={'new_assets':ASSETS,'existing_blueprints':[BP_PATH],'maps':[HC_LEVEL],
        'shared_material_reads':['/Game/Shared/Style/M_Stylized'],'shared_material_writes':[],
        'project_setting_writes':[],'new_helpers':['RefreshCrystalLockPresentation'],
        'new_variables':['CrystalLockMID'],'new_components':['HC_CrystalLockVisual']}
    RECEIPT_STATE['manifest']=MANIFEST;persist_receipt()
    args=globals().get('ARGS',{})
    assert Path(ue.Paths.project_dir()).resolve()==PRIMARY, 'Exact primary checkout required'
    assert not ue.EditorLevelLibrary.get_pie_worlds(True), 'Stop PIE before authoring'
    inspection=Path(args.get('inspection','/tmp/hc-a4-crystal-lock/unreal-inspection.json'))
    assert inspection.resolve().is_relative_to(Path('/tmp').resolve())
    before=json.loads(inspection.read_text())
    assert before['project']==str(PRIMARY)
    world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
    assert world.get_outermost().get_name()==before['editor_world'], 'Inspect this loaded world first'
    assert all(ue.EditorAssetLibrary.does_asset_exist(p) for p in ASSETS), 'Exact unsaved created assets must exist'
    failed=json.loads(Path('/tmp/hc-a4-crystal-lock/unreal-import-receipt.json').read_text())
    assert failed['status']=='failed' and failed['stage']=='add_local_mid_and_presentation_helper' and not failed['saved_packages']

    # Load a private helper module; do not repoint the parent's shared authoring module globals.
    spec=importlib.util.spec_from_file_location('hc_a4_parent_authoring',PRIMARY/'Tools/unreal/six_round/authoring.py')
    auth=importlib.util.module_from_spec(spec);spec.loader.exec_module(auth)
    auth.ROOT=PRIMARY;auth.EXPECTED=PRIMARY;auth.QUEUE=Path('/tmp/hc-a4-crystal-lock')
    def own_only(obj):
        assert Path(ue.Paths.project_dir()).resolve()==PRIMARY
        assert not ue.EditorLevelLibrary.get_pie_worlds(True)
        assert obj.get_path_name().split('.')[0]==BP_PATH, 'Exact Blueprint mutation manifest required'
    auth.owned=own_only
    BP=auth.BP;V=auth.V;S=auth.S
    bp=ue.load_asset(BP_PATH);assert bp
    graphs={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}
    assert {n:d for n,d in graphs.items() if n!='RefreshCrystalLockPresentation'}==before['graphs'], 'Original Blueprint graphs changed'
    assert 'RefreshCrystalLockPresentation' in graphs
    assert hashlib.sha256(graphs['ApplyLock'].encode()).hexdigest()==before['apply_graph_sha256']
    apply_graph=BP.get_graph(bp,'ApplyLock')
    entries=[n for n in BP.find_nodes(apply_graph) if n.get_class().get_name()=='K2Node_FunctionEntry'];assert len(entries)==1
    entry_pin=entries[0].find_then_pin();targets=list(entry_pin.list_connected_pins());assert len(targets)==1
    original_node_paths={n.get_path_name() for n in BP.find_nodes(apply_graph)}
    headlamp_rows=[r for r in before['actors'] if not r['Brazier']]
    assert len(headlamp_rows)==2, 'Expected two native headlamp locks'
    for r in headlamp_rows:
        assert r['level']==HC_LEVEL and 'HeadlampLock' in r['tags'], r
        assert r['root_mesh'].split('.')[0]=='/Engine/BasicShapes/Sphere'
        assert all(abs(a-b)<.1 for a,b in zip(r['world_dimensions'],[80,80,100])), r['world_dimensions']
        assert all(abs(a-b)<.001 for a,b in zip(r['actor_scale'],[.8,.8,1])), r['actor_scale']
        # An unattached StaticMeshActor root stores actor world coordinates as its relative location.
        assert all(abs(a-b)<.001 for a,b in zip(r['root_relative_location'],r['actor_location'])), 'Unattached root must align with actor world origin'
        assert all(abs(a-b)<.001 for a,b in zip(r['root_relative_scale'],r['actor_scale']))
        assert all(abs(v)<.001 for v in r['mesh_local_bounds']['origin'])
        assert all(abs(a-b)<.1 for a,b in zip(r['world_origin'],r['actor_location']))
        # Absolute visual scale preserves root XY scale; local -50 requires unchanged root Z scale.
        assert abs(r['root_relative_scale'][2]-1)<.001
    actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
    initial={a.get_path_name():a for a in actors.get_all_level_actors() if a.get_class()==bp.generated_class()}
    assert {r['path'] for r in before['actors']}==set(initial), 'Actor inventory changed; inspect again'
    for r in before['actors']:
        a=initial[r['path']]
        assert a.get_level().get_outermost().get_name()==r['level']
        assert str(a.static_mesh_component.get_editor_property('static_mesh').get_path_name())==r['root_mesh']
        assert bool(a.get_editor_property('Brazier'))==r['Brazier']
        root=a.static_mesh_component
        location=a.get_actor_location();root_world=root.get_world_location()
        assert all(abs(a-b)<.001 for a,b in zip([location.x,location.y,location.z],r['actor_location']))
        assert (root_world-location).length()<.001, 'Current root world origin must equal actor origin'
        relative=root.get_editor_property('relative_location')
        assert (relative-location).length()<.001, 'Current unattached root relative coordinates must equal actor world coordinates'
        scale=a.get_actor_scale3d()
        assert all(abs(a-b)<.001 for a,b in zip([scale.x,scale.y,scale.z],r['actor_scale']))
        rotation=a.get_actor_rotation()
        assert all(abs(v)<.001 for v in (rotation.pitch,rotation.yaw,rotation.roll)), 'Inspected locks are axis aligned'

    source=PRIMARY/'SourceArt/HC/HC-A4'
    manifest=json.loads((source/'source-manifest.json').read_text())
    assert hashlib.sha256((source/'SM_CrystalLock.fbx').read_bytes()).hexdigest()==manifest['files']['SM_CrystalLock.fbx']['sha256']
    assert 'CC0 1.0 Universal' in (source/'README.md').read_text()
    tools=ue.AssetToolsHelpers.get_asset_tools()
    parent=ue.load_asset('/Game/Shared/Style/M_Stylized');assert parent
    def linear(h):
        c=[int(h[i:i+2],16)/255 for i in (1,3,5)]
        return ue.LinearColor(*[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c],1)
    stage('validate_unsaved_import')
    stone=ue.load_asset(BASE+'/MI_CrystalLockStone');crystal=ue.load_asset(BASE+'/M_CrystalLockCrystal');mesh=ue.load_asset(BASE+'/SM_CrystalLock')
    assert isinstance(stone,ue.MaterialInstanceConstant) and isinstance(crystal,ue.Material) and isinstance(mesh,ue.StaticMesh)
    assert stone.get_editor_property('parent')==parent
    slots=[str(t.get_editor_property('imported_material_slot_name')) for t in mesh.static_materials]
    assert slots==['M_CrystalLockStone','M_CrystalLockCrystal']
    assert mesh.get_material(0)==stone and mesh.get_material(1)==crystal
    assert ue.get_editor_subsystem(ue.StaticMeshEditorSubsystem).get_convex_collision_count(mesh)==1
    b=mesh.get_bounds();dims=[2*b.box_extent.x,2*b.box_extent.y,2*b.box_extent.z]
    assert all(abs(a-b)<.1 for a,b in zip(dims,[80,80,100])) and abs(b.origin.z-b.box_extent.z)<.1
    assert 'CrystalLockMID' in BP.list_variables(bp)
    sds=ue.get_engine_subsystem(ue.SubobjectDataSubsystem);lib=ue.SubobjectDataBlueprintFunctionLibrary
    views=[lib.get_object_for_blueprint(lib.get_data(h),bp) for h in sds.k2_gather_subobject_data_for_blueprint(bp) if str(lib.get_variable_name(lib.get_data(h)))=='HC_CrystalLockVisual']
    assert len(views)==1
    visual=views[0]
    assert visual.get_editor_property('static_mesh')==mesh and visual.get_editor_property('absolute_scale')
    assert (visual.get_editor_property('relative_scale3d')-ue.Vector(1,1,1)).length()<.001
    assert (visual.get_editor_property('relative_location')-ue.Vector(0,0,-50)).length()<.001
    assert visual.get_collision_enabled()==ue.CollisionEnabled.NO_COLLISION
    getter_types=[str(t) for t in BP.find_node_types(BP.get_graph(bp,'RefreshCrystalLockPresentation'),'HCCrystalLockVisual') if str(t).rsplit('|',1)[-1]=='GetHCCrystalLockVisual']
    assert getter_types==['Variables|Default|GetHCCrystalLockVisual'],getter_types
    visual_getter='('+getter_types[0]+')'
    stage('add_local_mid_and_presentation_helper',mutation=True,detail=BP_PATH)
    root='(Variables|StaticMeshActor|GetStaticMeshComponent)'
    set_lit=f'(Rendering|Material|SetScalarParameterValue :self {V("CrystalLockMID")} :ParameterName "Lit" :Value (select {V("Lit")} 1.0 0.0))'
    auth.write(bp,'RefreshCrystalLockPresentation',f'''
     (if (not {V('Brazier')})
      (Rendering|SetVisibility :self {root} :bNewVisibility false)
      (Rendering|SetVisibility :self {visual_getter} :bNewVisibility true)
      (Utilities|IsValid :InputObject {V('CrystalLockMID')}
       (:"Is Valid" {set_lit})
       (:"Is Not Valid"
        {S('CrystalLockMID',f'(Rendering|Material|CreateDynamicMaterialInstance :self {visual_getter} :ElementIndex 1)')}
        (Utilities|IsValid :InputObject {V('CrystalLockMID')} (:"Is Valid" {set_lit}) (:"Is Not Valid"))))
      (else (Rendering|SetVisibility :self {visual_getter} :bNewVisibility false)))''')
    stage('splice_presentation_helper',mutation=True,detail=BP_PATH)
    # Preserve every original ApplyLock node and edge except its entry-to-first-node link.
    apply_graph=BP.get_graph(bp,'ApplyLock')
    entry=next(n for n in BP.find_nodes(apply_graph) if n.get_class().get_name()=='K2Node_FunctionEntry')
    pin=entry.find_then_pin();targets=list(pin.list_connected_pins());assert len(targets)==1
    call=BP.create_node(apply_graph,'CallFunction|RefreshCrystalLockPresentation',ue.IntPoint(250,-300),declaring_class=bp.generated_class())
    pin.break_single_pin_link(targets[0])
    assert pin.try_create_connection(call.find_execute_pin())
    assert call.find_then_pin().try_create_connection(targets[0])
    auth.compile_bp(bp)
    after={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}
    assert all(after[n]==dsl for n,dsl in graphs.items() if n not in ('ApplyLock','RefreshCrystalLockPresentation'))
    assert original_node_paths <= {n.get_path_name() for n in BP.find_nodes(BP.get_graph(bp,'ApplyLock'))}

    stage('set_owned_editor_visibility',mutation=True,detail=HC_LEVEL)
    # Set editor-only visibility on the two owned placed instances. No root transform/collision changes.
    current={a.get_path_name():a for a in actors.get_all_level_actors() if a.get_class()==bp.generated_class()}
    for r in before['actors']:
        a=current[r['path']];root=a.static_mesh_component
        assert str(root.get_editor_property('static_mesh').get_path_name())==r['root_mesh']
        assert str(root.get_collision_profile_name())==r['root_collision_profile']
        assert str(root.get_collision_enabled())==r['root_collision_enabled']
        assert bool(a.get_editor_property('Lit'))==r['Lit'] and bool(a.get_editor_property('Brazier'))==r['Brazier']
        if r['Brazier']:
            assert root.get_editor_property('visible')==r['root_visible'];continue
        assert a.get_level().get_outermost().get_name()==HC_LEVEL
        root.set_visibility(False,False)
        views=[c for c in a.get_components_by_class(ue.StaticMeshComponent) if c.get_name().startswith('HC_CrystalLockVisual')]
        assert len(views)==1;views[0].set_visibility(True,False)
        # Avoid saving transient MIDs into the map; ApplyLock creates them locally at runtime.
        center,extent=a.get_actor_bounds(False)
        assert all(abs(a-b)<.1 for a,b in zip([center.x,center.y,center.z],r['world_origin']))
        assert all(abs(a-b)<.1 for a,b in zip([2*extent.x,2*extent.y,2*extent.z],r['world_dimensions']))
    stage('save_owned_assets',mutation=True)
    for asset in (stone,crystal,mesh,bp):
        assert ue.EditorAssetLibrary.save_loaded_asset(asset,False)
        RECEIPT_STATE['saved_packages'].append(asset.get_path_name().split('.')[0]);persist_receipt()
    hc=ue.GameplayStatics.get_streaming_level(world,HC_LEVEL.rsplit('/',1)[-1]);assert hc and hc.get_loaded_level()
    package=hc.get_loaded_level().get_outermost();assert package.get_name()==HC_LEVEL
    stage('save_owned_hc_sublevel',mutation=True,detail=HC_LEVEL)
    assert ue.EditorLoadingAndSavingUtils.save_packages([package],False)
    RECEIPT_STATE['saved_packages'].append(HC_LEVEL);persist_receipt()
    report={'manifest':MANIFEST,'source_fbx_sha256':manifest['files']['SM_CrystalLock.fbx']['sha256'],
        'mesh_dimensions_cm':dims,'imported_slots':slots,'simple_collision_hulls':1,
        'original_root_and_collision_preserved':True,'original_graphs_preserved_except_entry_splice':['ApplyLock'],
        'local_visual_only':True,'visual_absolute_scale':[1,1,1],'visual_relative_offset_cm':[0,0,-50],
        'unreal_client_split_screen_platform_and_readability_acceptance':'pending'}
    Path('/tmp/hc-a4-crystal-lock/unreal-import-continuation.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

try:
    stage('preflight')
    RESULT=run_import()
except BaseException as error:
    RECEIPT_STATE.update({'status':'failed','exception_type':type(error).__name__,
        'error':str(error),'traceback':traceback.format_exc(),'run_finished_utc':datetime.now(timezone.utc).isoformat()})
    persist_receipt()
    print('HC-A4 import failed at '+RECEIPT_STATE['stage']+'; receipt: '+str(RECEIPT_PATH))
    raise
else:
    RECEIPT_STATE.update({'status':'succeeded','stage':'complete','result':RESULT,
        'run_finished_utc':datetime.now(timezone.utc).isoformat()})
    persist_receipt()
    print('HC-A4 import complete; receipt: '+str(RECEIPT_PATH))
