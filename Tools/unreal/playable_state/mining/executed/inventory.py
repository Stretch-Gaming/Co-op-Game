"""Root executes in its stopped editor. Inspection only; no world switch/save."""
import json, hashlib, traceback
from pathlib import Path
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets.object import ObjectTools as OBJ

OUT = Path('/tmp/coop-mining')
ROOT = Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')
SOURCE = '/Game/Hazards/L_Site01_HZ'
PERSISTENT = '/Game/Puzzles/Test/SixRound/L_SixRound_Test'
HZ = '/Game/Hazards/Test/SixRound/L_WorldRoute_Test'
HC = '/Game/Puzzles/Test/SixRound/L_SixRound_HC_Test'
CAVE = '/Game/Puzzles/Test/SixRound/L_CaveEnvironment_Test'
MINE = ['/Game/Hazards/FirstRoom/BP_' + n for n in
        ('MinePuzzle','MineCart','MineDeposit','MinePickaxe','MineRock')]
GRAPH_TARGETS = {
 '/Game/Core/BP_CoopGameMode': ['SixRoundMonitor','MonitorSixResources','RefreshSixObjective'],
 '/Game/Puzzles/UI/HCA3/WBP_HCA3RoundHUD': ['UpdateSixHUD'],
 '/Game/Puzzles/Test/SixRound/BP_PuzzleConnectionDoor': ['GetInteractInfo','MoveDoor'],
 '/Game/Puzzles/BP_PuzzleSetup': [],
 **{p: [] for p in MINE},
}

def dirty():
    return sorted({p.get_name() for p in
       list(ue.EditorLoadingAndSavingUtils.get_dirty_content_packages()) +
       list(ue.EditorLoadingAndSavingUtils.get_dirty_map_packages())})

def transform(a):
    t=a.get_actor_transform()
    return {'location': [t.translation.x,t.translation.y,t.translation.z],
            'rotation': str(a.get_actor_rotation()), 'scale': str(t.scale3d),
            'export': t.export_text()}

def props(a, names):
    values={}
    for n in names:
        try: values[n]=json.loads(OBJ.get_properties(a,[str(n)]))
        except Exception as e: values[n]={'read_error':str(e)}
    return values

def inherited_vars(bp):
    # Installed BlueprintTools.get_parent uses the exposed Blueprint method
    # get_blueprint_parent_class(), not protected reflected parent properties.
    names=[]
    while bp:
        names.extend(str(n) for n in BP.list_variables(bp))
        bp=ue.BlueprintEditorLibrary.get_blueprint_asset(BP.get_parent(bp))
    return sorted(set(names))

def actor_info(a):
    bp=ue.BlueprintEditorLibrary.get_blueprint_asset(a.get_class())
    names=inherited_vars(bp) if bp else []
    return {'path':a.get_path_name(),'label':a.get_actor_label(),
            'class':a.get_class().get_path_name(),
            'level':a.get_level().get_outermost().get_name(),
            'transform':transform(a),'tags':[str(x) for x in a.tags],
            'schema':OBJ.list_properties(a), 'variables':props(a,names)}

def run_inventory():
    assert Path(ue.Paths.project_dir()).resolve()==ROOT
    assert not ue.EditorLevelLibrary.get_pie_worlds(True), 'Stop PIE for this inventory'
    before=dirty()
    protected=['Content/Hazards/L_Site01_HZ.umap']+[p.replace('/Game/','Content/')+'.uasset' for p in MINE]
    protected += ['Content/Hazards/FirstRoom/Input/'+n+'.uasset' for n in
                  ('IA_HZ_Pickup','IA_HZ_Swing','IMC_HZ_Pickaxe','IMC_HZ_PickupNear')]
    protected_before={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in protected}
    world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
    editor_actors=list(ue.get_editor_subsystem(ue.EditorActorSubsystem).get_all_level_actors())
    assert world.get_outermost().get_name()==PERSISTENT, 'Inventory expects latest default adventure open'
    source=ue.load_asset(SOURCE)
    assert source and source.get_outermost().get_name()==SOURCE
    # Loading a source World asset does not change the editor's current world. All
    # subsequent reads select by package; this script never compiles or saves it.
    source_actors=[a for a in ue.ObjectIterator(ue.Actor)
                   if a.get_level() and a.get_level().get_outermost().get_name()==SOURCE
                   and not a.get_name().startswith('Default__')]
    assert source_actors, 'Source package contains no serialized actors; stop and inspect loading API'
    blueprints={}
    partial={'inspection_only':True,'stage':'before_blueprint_reads','blueprints':blueprints,
             'protected_sha256':protected_before,'dirty_before':before,'source_actors':[],
             'current_actors':[]}
    def persist():
        (OUT/'inventory-partial.json').write_text(json.dumps(partial,indent=2))
    persist()
    for path,requested in GRAPH_TARGETS.items():
        bp=ue.load_asset(path); assert bp,path
        graph_names=[str(g.get_name()) for g in BP.list_graphs(bp)]
        blueprints[path]={'variables':inherited_vars(bp),
                         'schema':OBJ.list_properties(BP.get_default_object(bp)),
                         'defaults':props(BP.get_default_object(bp),inherited_vars(bp)),
                         'graphs':{n:BP.read_graph_dsl(BP.get_graph(bp,n))
                                   for n in (requested or graph_names)}}
        partial['stage']='blueprint:'+path;persist()
        (OUT/(bp.get_name()+'.json')).write_text(json.dumps(blueprints[path],indent=2))
    source_selected=[a for a in source_actors if a.get_class().get_name().startswith('BP_Mine')
                     or a.get_class().get_name()=='BP_PressurePlate_C']
    editor_selected=[a for a in editor_actors if a.get_level().get_outermost().get_name() in (HC,HZ,CAVE)
                     and (a.get_class().get_name().startswith(('BP_Mine','BP_PressurePlate','BP_PuzzleSetup','BP_Statue','BP_StartPad','BP_Checkpoint'))
                          or a.actor_has_tag('ConnectionDoor')
                          or 'cart' in a.get_actor_label().lower())]
    cart_scenery=[]
    for a in editor_actors:
        if a.get_level().get_outermost().get_name()!=CAVE or not isinstance(a,ue.StaticMeshActor):continue
        origin,extent=a.get_actor_bounds(False)
        if origin.x+extent.x>=-700 and origin.x-extent.x<=1000 and origin.y+extent.y>=-1200 and origin.y-extent.y<=-650:
            cart_scenery.append({'path':a.get_path_name(),'label':a.get_actor_label(),
                                 'transform':transform(a),
                                 'mesh':str(a.static_mesh_component.static_mesh),
                                 'bounds':{'origin':str(origin),'extent':str(extent)}})
    for a in source_selected:
        partial['source_actors'].append(actor_info(a));partial['stage']='source_actor:'+a.get_path_name();persist()
    for a in editor_selected:
        partial['current_actors'].append(actor_info(a));partial['stage']='current_actor:'+a.get_path_name();persist()
    RESULT={'inspection_only':True,'editor_world':world.get_outermost().get_name(),
            'source_actors':partial['source_actors'],
            'current_actors':partial['current_actors'],
            'cart_scenery':cart_scenery,
            'blueprints':blueprints,'dirty_before':before,'dirty_after':dirty(),
            'protected_sha256':protected_before,
            'duplicate_api':str(ue.EditorActorSubsystem.duplicate_actors.__doc__)}
    assert ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()==world
    RESULT['load_dirty_side_effects']=sorted(set(dirty())-set(before))
    RESULT['protected_packages_saved']=False
    assert protected_before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in protected}
    return RESULT

OUT.mkdir(parents=True,exist_ok=True)
try:
    RESULT=run_inventory()
    (OUT/'inventory.json').write_text(json.dumps(RESULT,indent=2))
    print('COOP_MINING inventory only: '+str(OUT/'inventory.json'))
except Exception:
    RESULT={'inspection_only':True,'passed':False,'error':traceback.format_exc()}
    try: RESULT['dirty_after_failure']=dirty()
    except Exception: pass
    (OUT/'inventory-error.json').write_text(json.dumps(RESULT,indent=2))
    print('COOP_MINING inventory failure: '+str(OUT/'inventory-error.json'))
    raise
