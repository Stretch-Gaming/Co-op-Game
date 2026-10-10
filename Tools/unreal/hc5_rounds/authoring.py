"""Editor-only helpers. All gameplay is emitted as Blueprint nodes."""
import pathlib
import unreal
import toolset_registry
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
from editor_toolset.toolsets.actor import ActorTools as AT
from editor_toolset.toolsets import blueprint_dsl

ROOT = pathlib.Path(__file__).resolve().parents[3]
def guard():
    active = pathlib.Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve()
    assert ROOT == pathlib.Path('C:/Users/Stretch/.codex/worktrees/round-progression/Co op Game')
    assert active == ROOT / 'CoopGame.uproject', str(active)

def owned(bp):
    guard()
    p = bp.get_path_name().split('.')[0]
    assert p in ['/Game/Puzzles/BP_Checkpoint','/Game/Puzzles/BP_RoundStart'] or p.startswith(('/Game/Puzzles/Rounds/','/Game/Puzzles/Test/HC5/')), p

def compile_bp(bp):
    owned(bp)
    with toolset_registry.tool_raising_exceptions(): BP.compile_blueprint(bp, warnings_as_errors=True)
    assert bp.get_editor_property('status') == unreal.BlueprintStatus.BS_UP_TO_DATE

def create(path, parent):
    guard()
    assert path in ['/Game/Puzzles/BP_Checkpoint','/Game/Puzzles/BP_RoundStart'] or path.startswith(('/Game/Puzzles/Rounds/','/Game/Puzzles/Test/HC5/')), path
    bp = unreal.load_asset(path)
    if bp: return bp
    folder, name = path.rsplit('/',1)
    with toolset_registry.tool_raising_exceptions(): bp = BP.create(folder, name, parent)
    owned(bp)
    return bp

def var(bp, name, kind, notify=False):
    owned(bp)
    with toolset_registry.tool_raising_exceptions():
        if name not in BP.list_variables(bp):
            if isinstance(kind,str): BP.add_variable(bp,name,kind)
            else: BP.add_object_variable(bp,name,kind)
        if notify: BP.set_variable_replication(bp,name,unreal.BlueprintVariableReplication.REP_NOTIFY)

def fn(bp, name, inputs=(), outputs=()):
    owned(bp)
    with toolset_registry.tool_raising_exceptions():
        g = BP.add_function_graph(bp,name)
        for is_input, params in [(True, inputs),(False,outputs)]:
            for param, kind in params:
                if BP._param_name_exists(g,param,is_input): continue
                if isinstance(kind,str): BP.add_function_param(g,param,kind,is_input)
                else: BP.add_object_function_param(g,param,kind,is_input)
    return g

def write(bp, name, body, parameters=''):
    owned(bp)
    g=BP.get_graph(bp,name)
    with toolset_registry.tool_raising_exceptions():
        for n in BP.find_nodes(g):
            if n.get_class().get_name() not in ('K2Node_FunctionEntry','K2Node_FunctionResult'): BP.delete_node(n)
        blueprint_dsl.Transpiler(g,BP.create_node,BP.connect_pins,BP._get_node_info,BP.set_pin_value,
            lambda gr: BP.find_nodes(gr),delete_node_fn=BP.delete_node,
            find_node_types_fn=lambda f: BP.find_node_types(g,f)).transpile(f'(fn {name} ({parameters}) {body})')
    compile_bp(bp)

def component(bp, name, cls):
    owned(bp)
    with toolset_registry.tool_raising_exceptions():
        sds=AT._sds()
        parts=[unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h)) for h in AT._get_subobject_handles(sds,BP.get_default_object(bp),bp)]
        found=next((p for p in parts if p and p.get_name().removesuffix('_GEN_VARIABLE')==name),None)
        return found or AT.add_component(bp,cls,name)

def defaults(bp, **props):
    owned(bp)
    BP.get_default_object(bp).set_editor_properties(props)

def event(bp, name, handler):
    owned(bp)
    g=BP.get_graph(bp,'EventGraph')
    with toolset_registry.tool_raising_exceptions():
        node=BP.add_event(bp,name)
        links=list(node.find_then_pin().list_connected_pins())
        if links:
            assert len(links)==1 and handler.lower() in BP._get_node_info(links[0].get_owning_node()).type_id.lower()
            return
        call=BP.create_node(g,'CallFunction|'+handler,unreal.IntPoint(450,300))
        assert node.find_output_pin('then').try_create_connection(call.find_execute_pin())
    compile_bp(bp)

def save(bp):
    compile_bp(bp)
    owned(bp)
    assert unreal.EditorAssetLibrary.save_loaded_asset(bp,False)

