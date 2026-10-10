"""Editor-only authoring helpers; every shipped behavior is Blueprint gameplay."""
import json
from pathlib import Path
import unreal as ue
import toolset_registry
from editor_toolset.toolsets.blueprint import BlueprintTools as BP, ContainerType
from editor_toolset.toolsets.actor import ActorTools as AT
from editor_toolset.toolsets import blueprint_dsl

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
QUEUE = ROOT / 'Saved/SixRound'
EXPECTED = Path('C:/Users/Stretch/.codex/worktrees/six-round-adventure/Co op Game').resolve()
I = 'Index_11_91104438409472A6DD374BADC8DC29B1'
P = 'Phase_15_0B3D934F45B47D0BD2F25CA01264D4DF'
A = 'Attempt_12_246832B34F4E147660E8729696BDD44A'
R = 'ScalingRow_14_43C74C304230A92B6620E1A520A230C0'
_contracts_loaded = False
CONTRACT_CLASSES = [
    '/Game/Player/AC_Traversal', '/Game/Player/Tools/AC_Tools',
    '/Game/Player/Tools/BP_Flare', '/Game/Player/Tools/BPI_Lightable',
    '/Game/Player/Taking/BP_TakingDirector', '/Game/Player/Ghosts/BP_ChaseDirector',
    '/Game/Player/RelicChamber/BP_RelicCage', '/Game/Player/RelicChamber/BP_Lever',
    '/Game/Puzzles/BP_RegroupVolume', '/Game/Puzzles/BP_CrystalLock', '/Game/Puzzles/BP_MazeDoor',
    '/Game/Hazards/Maze/BP_MouthSeal', '/Game/Hazards/Maze/BP_ClimbVolume',
]

def guard():
    global _contracts_loaded
    assert ROOT.resolve() == EXPECTED
    assert Path(ue.Paths.project_dir()).resolve() == EXPECTED
    assert not ue.EditorLevelLibrary.get_pie_worlds(True), 'Stop PIE before authoring'
    if not _contracts_loaded:
        for path in CONTRACT_CLASSES:
            if ue.EditorAssetLibrary.does_asset_exist(path):
                assert ue.load_asset(path), path
        _contracts_loaded = True

def owned(obj):
    guard()
    path = obj.get_path_name().split('.')[0]
    assert path.startswith(('/Game/Core/', '/Game/Puzzles/', '/Game/Player/', '/Game/Hazards/')), path

def compile_bp(bp):
    owned(bp)
    with toolset_registry.tool_raising_exceptions():
        BP.compile_blueprint(bp, warnings_as_errors=True)
    assert bp.get_editor_property('status') == ue.BlueprintStatus.BS_UP_TO_DATE, bp.get_path_name()

def create(path, parent):
    guard()
    bp = ue.load_asset(path)
    if bp:
        return bp
    folder, name = path.rsplit('/', 1)
    with toolset_registry.tool_raising_exceptions():
        bp = BP.create(folder, name, parent)
    compile_bp(bp)
    return bp

def var(bp, name, kind, value=None, replicated=False, notify=False, editable=False, array=False):
    owned(bp)
    with toolset_registry.tool_raising_exceptions():
        if name not in BP.list_variables(bp):
            container = ContainerType.ARRAY if array else None
            if isinstance(kind, str):
                BP.add_variable(bp, name, kind, container_type=container)
            else:
                BP.add_object_variable(bp, name, kind, container_type=container)
        if replicated or notify:
            BP.set_variable_replication(bp, name, ue.BlueprintVariableReplication.REP_NOTIFY if notify else ue.BlueprintVariableReplication.REPLICATED)
        if editable:
            BP.set_variable_instance_editable(bp, name, True)
    compile_bp(bp)
    if value is not None:
        BP.get_default_object(bp).set_editor_property(name, value)

def fn(bp, name, inputs=(), outputs=()):
    owned(bp)
    with toolset_registry.tool_raising_exceptions():
        graph = BP.add_function_graph(bp, name)
        for is_input, params in [(True, inputs), (False, outputs)]:
            for param, kind in params:
                if BP._param_name_exists(graph, param, is_input):
                    continue
                if isinstance(kind, str):
                    BP.add_function_param(graph, param, kind, is_input)
                else:
                    BP.add_object_function_param(graph, param, kind, is_input)
    return graph

def write(bp, name, body, parameters=''):
    owned(bp)
    code=f'(fn {name} ({parameters}) {body})'
    blueprint_dsl.parse(code)
    graph = BP.get_graph(bp, name)
    with toolset_registry.tool_raising_exceptions():
        for node in BP.find_nodes(graph):
            if node.get_class().get_name() not in ('K2Node_FunctionEntry', 'K2Node_FunctionResult'):
                BP.delete_node(node)
        palette_cache={}
        def palette(query):
            if query not in palette_cache:palette_cache[query]=BP.find_node_types(graph,query)
            return palette_cache[query]
        def make_node(g,type_id,position):
            if not type_id.startswith('CallFunction|'):
                exact = [t for t in palette(type_id) if str(t).lower()==type_id.lower()]
                if exact:
                    type_id = str(exact[0])
                else:
                    leaf = type_id.rsplit('|',1)[-1].lower()
                    candidates = [str(t) for t in palette(leaf) if str(t).rsplit('|',1)[-1].lower()==leaf]
                    if len(candidates)==1:
                        type_id = candidates[0]
            declaring=bp.generated_class() if type_id.startswith('CallFunction|') else None
            if type_id == 'CallFunction|ResetItem' and bp.get_name() == 'BP_KeyRelic':
                declaring=ue.load_asset('/Game/Puzzles/BP_Carryable').generated_class()
            if bp.get_name()=='BP_SixRoundTestGameMode' and type_id.rsplit('|',1)[-1] in ('CancelAllUses','RestartAdventure','TravelToResults'):
                declaring=ue.load_asset('/Game/Core/BP_CoopGameMode').generated_class()
            if type_id.startswith('Class|BPLever|') or type_id == 'Utilities|Casting|CastToBP_Lever':
                declaring=ue.load_asset('/Game/Player/RelicChamber/BP_Lever').generated_class()
            if type_id in ('Class|BPILightable|LightBegin(Message)', 'Class|BPILightable|LightEnd(Message)'):
                declaring=ue.load_asset('/Game/Player/Tools/BPI_Lightable').generated_class()
            if type_id=='Collision|GetOverlappingActors' and bp.get_name() in ('BP_AdventureTrap', 'BP_SixRoundTrap', 'BP_SprintSequence'):
                declaring=ue.PrimitiveComponent.static_class()
            if type_id=='Behavior|GetValue':
                declaring=ue.load_asset('/Game/Puzzles/BP_Relic').generated_class()
            if type_id in ('Rendering|Material|SetVectorParameterValue','Rendering|Material|SetScalarParameterValue'):
                declaring=ue.MaterialInstanceDynamic.static_class()
            if type_id=='Rendering|Material|CreateDynamicMaterialInstance':
                declaring=ue.PrimitiveComponent.static_class()
            return BP.create_node(g,type_id,position,declaring_class=declaring)
        blueprint_dsl.Transpiler(graph,make_node,
            BP.connect_pins, BP._get_node_info, BP.set_pin_value, lambda g: BP.find_nodes(g),
            delete_node_fn=BP.delete_node, find_node_types_fn=palette
        ).transpile(code)
    compile_bp(bp)

def event(bp, name, handler, parameter_names=()):
    owned(bp)
    graph = BP.get_graph(bp, 'EventGraph')
    event_node = BP.add_event(bp, name)
    existing = list(event_node.find_then_pin().list_connected_pins())
    if any(handler in BP._get_node_info(pin.get_owning_node()).type_id for pin in existing):
        return event_node
    call = BP.create_node(graph, 'CallFunction|' + handler, ue.IntPoint(500,300), declaring_class=bp.generated_class())
    if existing:
        sequence = BP.create_node(graph, 'Utilities|FlowControl|Sequence', ue.IntPoint(250,300))
        assert sequence,'Sequence node unavailable; preserve existing event wiring'
        for target in existing:
            event_node.find_then_pin().break_single_pin_link(target)
        assert event_node.find_then_pin().try_create_connection(sequence.find_execute_pin())
        assert sequence.find_output_pin('Then_0').try_create_connection(existing[0])
        assert sequence.find_output_pin('Then_1').try_create_connection(call.find_execute_pin())
    else:
        assert event_node.find_then_pin().try_create_connection(call.find_execute_pin())
    for name in parameter_names:
        assert event_node.find_output_pin(name).try_create_connection(call.find_input_pin(name)), name
    compile_bp(bp)
    return event_node

def component(bp, name, cls):
    owned(bp)
    sds = ue.get_engine_subsystem(ue.SubobjectDataSubsystem)
    lib = ue.SubobjectDataBlueprintFunctionLibrary
    handles = sds.k2_gather_subobject_data_for_blueprint(bp)
    for handle in handles:
        data = lib.get_data(handle)
        if str(lib.get_variable_name(data)) == name:
            return lib.get_object_for_blueprint(data,bp), handle
    root = next(h for h in handles if lib.is_root_actor(lib.get_data(h)))
    handle, reason = sds.add_new_subobject(params=ue.AddNewSubobjectParams(parent_handle=root,new_class=cls,blueprint_context=bp))
    assert lib.is_handle_valid(handle), str(reason)
    sds.rename_subobject(handle,ue.Text(name))
    compile_bp(bp)
    return lib.get_object_for_blueprint(lib.get_data(handle),bp), handle

def save(bp):
    compile_bp(bp)
    assert ue.EditorAssetLibrary.save_loaded_asset(bp,False)

V = lambda name: f'(Variables|Default|Get{name})'
S = lambda name,value: f'(Variables|Default|Set{name} {value})'
OWNER = '(Components|GetOwner)'
AUTH_COMPONENT = f'(Networking|HasAuthority :self {OWNER})'
