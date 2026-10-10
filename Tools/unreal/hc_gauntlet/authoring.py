"""Editor-only Blueprint authoring helpers restricted to this milestone."""
import json
from pathlib import Path
import unreal as ue
import toolset_registry
from editor_toolset.toolsets.blueprint import BlueprintTools as BP, ContainerType
from editor_toolset.toolsets import blueprint_dsl

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
OWNED=('/Game/Puzzles/Gauntlet/','/Game/Puzzles/Test/HC_Gauntlet/')
def guard():
 assert Path(ue.Paths.project_dir()).resolve()==ROOT
 assert ROOT==Path('C:/Users/Stretch/.codex/worktrees/haunted-gauntlet-integration/Co op Game')
 assert ue.SystemLibrary.get_engine_version().startswith('5.8.3-58210709')
 assert not ue.EditorLevelLibrary.get_pie_worlds(True)
def owned(bp):
 guard();assert bp.get_path_name().startswith(OWNED),bp.get_path_name()
def compile_bp(bp):
 owned(bp)
 with toolset_registry.tool_raising_exceptions():BP.compile_blueprint(bp,warnings_as_errors=True)
 assert bp.get_editor_property('status')==ue.BlueprintStatus.BS_UP_TO_DATE,bp.get_path_name()
def create(path,parent=ue.Actor.static_class(),probe=False):
 guard();assert path.startswith(OWNED)
 bp=ue.load_asset(path)
 if bp:return bp
 if probe:
  bp=ue.EditorAssetLibrary.duplicate_asset('/Game/Puzzles/BP_Carryable',path)
  owned(bp)
  for g in BP.list_graphs(bp):
   if g.get_name() not in ['UserConstructionScript','EventGraph','CanInteract','GetInteractInfo']:
    BP.remove_function_graph(bp,g.get_name())
  for n in BP.find_nodes(BP.get_graph(bp,'EventGraph')):BP.delete_node(n)
  for n in BP.find_nodes(BP.get_graph(bp,'UserConstructionScript')):
   if not isinstance(n,ue.K2Node_FunctionEntry):BP.delete_node(n)
  for graph_name in ['CanInteract','GetInteractInfo']:
   for n in BP.find_nodes(BP.get_graph(bp,graph_name)):
    if not isinstance(n,(ue.K2Node_FunctionEntry,ue.K2Node_FunctionResult)):BP.delete_node(n)
  for name in list(BP.list_variables(bp)):BP.remove_variable(bp,name)
 else:
  folder,name=path.rsplit('/',1)
  with toolset_registry.tool_raising_exceptions():bp=BP.create(folder,name,parent)
 owned(bp);return bp
def var(bp,name,kind,rep=False,array=False,editable=False):
 owned(bp)
 with toolset_registry.tool_raising_exceptions():
  if name not in BP.list_variables(bp):
   container=ContainerType.ARRAY if array else None
   if isinstance(kind,str):BP.add_variable(bp,name,kind,container_type=container)
   else:BP.add_object_variable(bp,name,kind,container_type=container)
  if rep:BP.set_variable_replication(bp,name,ue.BlueprintVariableReplication.REPLICATED)
  if editable:BP.set_variable_instance_editable(bp,name,True)
def fn(bp,name,inputs=(),outputs=()):
 owned(bp)
 with toolset_registry.tool_raising_exceptions():
  g=BP.add_function_graph(bp,name)
  for is_input,params in [(True,inputs),(False,outputs)]:
   for param,kind in params:
    if BP._param_name_exists(g,param,is_input):continue
    if isinstance(kind,str):BP.add_function_param(g,param,kind,is_input)
    else:BP.add_object_function_param(g,param,kind,is_input)
 return g
def write(bp,name,body,parameters=''):
 owned(bp);g=BP.get_graph(bp,name)
 code=f'(fn {name} ({parameters}) {body})'
 source=HERE/'dsl';source.mkdir(exist_ok=True)
 (source/(bp.get_name()+'_'+name+'.dsl')).write_text(code,encoding='utf-8')
 blueprint_dsl.parse(code)
 with toolset_registry.tool_raising_exceptions():
  for n in BP.find_nodes(g):
   if not isinstance(n,(ue.K2Node_FunctionEntry,ue.K2Node_FunctionResult)):BP.delete_node(n)
  blueprint_dsl.Transpiler(g,BP.create_node,BP.connect_pins,BP._get_node_info,BP.set_pin_value,lambda gr:BP.find_nodes(gr),delete_node_fn=BP.delete_node,find_node_types_fn=lambda f:BP.find_node_types(g,f)).transpile(code)
def event(bp,name,handler,params=()):
 owned(bp);g=BP.get_graph(bp,'EventGraph')
 with toolset_registry.tool_raising_exceptions():
  node=BP.add_event(bp,name)
  call=BP.create_node(g,'CallFunction|'+handler,ue.IntPoint(450,300))
  assert node.find_then_pin().try_create_connection(call.find_execute_pin())
  for source,destination in params:assert node.find_output_pin(source).try_create_connection(call.find_input_pin(destination))
def save(bp):
 compile_bp(bp);assert ue.EditorAssetLibrary.save_loaded_asset(bp,False)
def snapshot(bps,filename):
 report={'project':str(ROOT),'engine':ue.SystemLibrary.get_engine_version(),'blueprints':{bp.get_path_name():{'status':str(bp.get_editor_property('status')),'graphs':{g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}} for bp in bps}}
 (HERE/filename).write_text(json.dumps(report,indent=2))
V=lambda n:f'(Variables|Default|Get{n})'
S=lambda n,value:f'(Variables|Default|Set{n} {value})'
