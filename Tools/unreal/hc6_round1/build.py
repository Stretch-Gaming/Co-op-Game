"""Opt-in HC6 Blueprint authoring; execute only through the dedicated editor."""
import json
from pathlib import Path
import unreal
import toolset_registry
from editor_toolset.toolsets.blueprint import BlueprintTools as BP, ContainerType
from editor_toolset.toolsets import blueprint_dsl
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'Tools/unreal/hc6_round1'
ACTORS=('BP_PressurePlate','BP_PuzzleSetup','BP_ChamberGate','BP_StartPad')
def guard():
    assert Path(unreal.Paths.project_dir()).resolve()==ROOT
    assert unreal.SystemLibrary.get_engine_version().startswith('5.8.3-')
def compile_bp(bp):
    with toolset_registry.tool_raising_exceptions(): BP.compile_blueprint(bp,True)
    assert bp.get_editor_property('status')==unreal.BlueprintStatus.BS_UP_TO_DATE,bp.get_name()
def variable(bp,name,kind,default=None,editable=False,rep=False,array=False):
    if name not in BP.list_variables(bp):
        cont=ContainerType.ARRAY if array else None
        if isinstance(kind,str): BP.add_variable(bp,name,kind,container_type=cont)
        else: BP.add_object_variable(bp,name,kind,container_type=cont)
    if editable: BP.set_variable_instance_editable(bp,name,True)
    if rep: BP.set_variable_replication(bp,name,unreal.BlueprintVariableReplication.REP_NOTIFY)
    compile_bp(bp)
    if default is not None: BP.get_default_object(bp).set_editor_property(name,default)
def function(bp,name,ins=(),outs=()):
    g=BP.add_function_graph(bp,name)
    for n,t in ins:
        if isinstance(t,str): BP.add_function_param(g,n,t,True)
        else: BP.add_object_function_param(g,n,t,True)
    for n,t in outs:
        if isinstance(t,str): BP.add_function_param(g,n,t,False)
        else: BP.add_object_function_param(g,n,t,False)
    return g
def write(bp,name,text):
    g=BP.get_graph(bp,name)
    if name=='EventGraph' and '(event ResetForRound ' in text:
        node=BP.add_event(bp,'ResetForRound')
        event_type=BP._get_node_info(node).type_id.removeprefix('AddEvent|')
        text=text.replace('(event ResetForRound ','(event '+event_type+' ')
    for n in list(BP.find_nodes(g)):
        if not isinstance(n,(unreal.K2Node_FunctionEntry,unreal.K2Node_FunctionResult,unreal.K2Node_Event,unreal.K2Node_CustomEvent)): BP.delete_node(n)
    with toolset_registry.tool_raising_exceptions():
        blueprint_dsl.Transpiler(g,lambda graph,typ,pos:BP.create_node(graph,typ,pos,
          declaring_class=bp.generated_class() if typ.startswith('CallFunction|') else None),BP.connect_pins,BP._get_node_info,BP.set_pin_value,
          lambda graph:BP.find_nodes(graph),delete_node_fn=BP.delete_node,
          find_node_types_fn=lambda f:BP.find_node_types(g,f)).transpile(text)
    compile_bp(bp)
def component(bp,name,cls,parent=None):
    ss=unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    lib=unreal.SubobjectDataBlueprintFunctionLibrary
    handles=ss.k2_gather_subobject_data_for_blueprint(bp)
    for h in handles:
        data=lib.get_data(h)
        obj=lib.get_object_for_blueprint(data,bp)
        if obj and str(lib.get_variable_name(data))==name:return obj,h
    root=parent or next(h for h in handles if lib.is_root_actor(lib.get_data(h)))
    h,reason=ss.add_new_subobject(params=unreal.AddNewSubobjectParams(parent_handle=root,new_class=cls,blueprint_context=bp))
    assert lib.is_handle_valid(h),str(reason)
    ss.rename_subobject(h,unreal.Text(name))
    compile_bp(bp)
    return lib.get_object_for_blueprint(lib.get_data(h),bp),h
def scaffold():
    guard()
    assert all(not unreal.EditorAssetLibrary.does_asset_exist('/Game/Puzzles/'+name) for name in ACTORS), 'HC6 assets already exist; scaffold refuses overwrites'
    assets={}
    for name in ACTORS:
        bp=unreal.load_asset('/Game/Puzzles/'+name) or BP.create('/Game/Puzzles',name,unreal.Actor.static_class())
        assets[name]=bp
        cdo=BP.get_default_object(bp)
        cdo.set_editor_property('replicates',True)
        cdo.set_editor_property('always_relevant',True)
        cdo.set_editor_property('net_update_frequency',20)
        root,h=component(bp,'RoundRoot',unreal.SceneComponent)
        variable(bp,'RoundIndex','int',1,True)
        variable(bp,'PuzzleTag','name','HC_Round1',True)
        for f in ('Initialize','Refresh','ApplyVisual','ResetActor'):function(bp,f)
        BP.add_event(bp,'ReceiveBeginPlay');BP.add_event(bp,'ReceiveTick')
    plate=assets['BP_PressurePlate']
    trigger,h=component(plate,'OccupancyVolume',unreal.BoxComponent)
    trigger.set_box_extent(unreal.Vector(70,70,60))
    trigger.set_editor_property('relative_location',unreal.Vector(0,0,60))
    trigger.set_collision_profile_name('OverlapAllDynamic')
    trigger.set_editor_property('generate_overlap_events',True)
    top,h=component(plate,'PlateTop',unreal.StaticMeshComponent)
    top.set_collision_profile_name('NoCollision')
    for n,t,d in [('Enabled','bool',False),('Pressed','bool',False)]:variable(plate,n,t,d,rep=True)
    variable(plate,'PlateSlot','int',0,True)
    variable(plate,'OccupantCount','int',0)
    variable(plate,'PlateMesh',unreal.StaticMesh.static_class(),editable=True)
    variable(plate,'ReleasedMaterial',unreal.MaterialInterface.static_class(),editable=True)
    variable(plate,'PressedMaterial',unreal.MaterialInterface.static_class(),editable=True)
    function(plate,'SetEnabled',[('Value','bool')])
    setup=assets['BP_PuzzleSetup']
    variable(setup,'ConfiguredAttempt','int',-1)
    variable(setup,'PlateCount','int',0,rep=True)
    variable(setup,'StatueCount','int',0,rep=True)
    variable(setup,'Ready','bool',False,rep=True)
    variable(setup,'PressedCount','int',0)
    variable(setup,'Statues',unreal.Actor.static_class(),array=True)
    variable(setup,'StatueTransforms','Transform',editable=True,array=True)
    typ=unreal.BlueprintEditorLibrary.get_basic_type_by_name('class')
    assert typ.import_text('(PinCategory="class",PinSubCategoryObject="/Script/Engine.Actor")')
    if 'StatueClass' not in BP.list_variables(setup):unreal.BlueprintEditorLibrary.add_member_variable(setup,'StatueClass',typ)
    BP.set_variable_instance_editable(setup,'StatueClass',True)
    function(setup,'Configure',[('Attempt','int')]);function(setup,'RemoveStatues')
    gate=assets['BP_ChamberGate']
    leaf,h=component(gate,'GateLeaf',unreal.StaticMeshComponent)
    leaf.set_collision_profile_name('BlockAll')
    variable(gate,'Open','bool',False,rep=True)
    variable(gate,'GateMesh',unreal.StaticMesh.static_class(),editable=True)
    variable(gate,'OpenHeight','float',400.0,True)
    pad=assets['BP_StartPad']
    trigger,h=component(pad,'StartVolume',unreal.BoxComponent)
    trigger.set_box_extent(unreal.Vector(250,250,100));trigger.set_editor_property('relative_location',unreal.Vector(0,0,100))
    trigger.set_collision_profile_name('OverlapAllDynamic');trigger.set_editor_property('generate_overlap_events',True)
    variable(pad,'HoldSeconds','float',3.0,True)
    variable(pad,'HoldStarted','float',-1.0)
    variable(pad,'Started','bool',False,rep=True)
    variable(pad,'InsideCount','int',0)
    variable(pad,'ExpectedCount','int',0)
    variable(pad,'PresentStates',unreal.PlayerState.static_class(),array=True)
    for bp in assets.values():compile_bp(bp);unreal.EditorAssetLibrary.save_loaded_asset(bp)
    probes={}
    for name,bp in assets.items():
        g=BP.get_graph(bp,'Refresh')
        probes[name]={term:list(BP.find_node_types(g,term)) for term in ('GetOverlappingActors','GetPlayerArray','GetRoundState','GetScalingRow','GetStatueClass','BreakSRoundScaling','GetDataTableRow','SpawnActorfromClass','AddUnique','Clear','GetActorTransform','ResetForRound')}
    (OUT/'scaffold.json').write_text(json.dumps(probes,indent=2))
if __name__=='__main__':scaffold()
