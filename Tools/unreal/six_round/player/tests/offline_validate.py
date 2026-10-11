"""Offline source/native-DSL checks. Never creates assets or submits editor work."""
import ast,hashlib,importlib,importlib.util,json,sys,types
from pathlib import Path
here=Path(__file__).resolve().parent;root=here.parents[4];player=here.parent
files=sorted(here.glob('*.py'))+[player/'build_secondary_keyboard.py',player/'place_test.py',player/'round_ghosts.py']
allowed_queries={'GetHeadlampOn','GetLocalPlayerSubSystemFromPlayerController','CanAcceptSixInput','IsCarryingHeavy','CanTraverse','IsRaised','IsHeld','GetRoomThreatCount','IsActive'}
for file in files:
 tree=ast.parse(file.read_text(),filename=str(file))
 if file.parent==here and file.name!='offline_validate.py':
  for node in ast.walk(tree):
   if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='call_method':
    assert node.args and isinstance(node.args[0],ast.Constant) and node.args[0].value in allowed_queries,(file.name,'Gameplay must use owning Enhanced Input, not a function/RPC shortcut',ast.unparse(node))
class Dummy:
 def __getattr__(self,name):return self
 def __call__(self,*args,**kwargs):return self
 def __iter__(self):return iter(())
 def __bool__(self):return True
class Sink:
 def __truediv__(self,value):return self
 def write_text(self,*args,**kwargs):return 0
module=types.ModuleType('authoring');module.ue=Dummy();module.BP=Dummy();module.ROOT=root;module.HERE=player.parent;module.QUEUE=Sink()
for name in ('guard','var','fn','save','event','compile_bp','owned'):setattr(module,name,lambda *args,**kwargs:None)
module.V=lambda name:f'(Variables|Default|Get{name})';module.S=lambda name,value:f'(Variables|Default|Set{name} {value})'
module.create=lambda *args,**kwargs:Dummy()
captured=[];module.write=lambda bp,name,body,parameters='':captured.append({'function':name,'dsl':f'(fn {name} ({parameters}) {body})'})
sys.modules['authoring']=module;old_reload=importlib.reload;importlib.reload=lambda item:item
data_stub=types.ModuleType('editor_toolset.toolsets.data_table')
class FakeRows:
 @staticmethod
 def get_rows(*args):return json.dumps({'2':{'ghostCount':1},'3':{'ghostCount':1},'4':{'ghostCount':2}})
data_stub.DataTableTools=FakeRows
sys.modules['editor_toolset']=types.ModuleType('editor_toolset');sys.modules['editor_toolset.toolsets']=types.ModuleType('editor_toolset.toolsets');sys.modules['editor_toolset.toolsets.data_table']=data_stub
try:
 for filename in ('build_secondary_keyboard.py','round_ghosts.py'):
  file=player/filename;exec(compile(file.read_text(),str(file),'exec'),{'__file__':str(file),'ARGS':{}})
finally:importlib.reload=old_reload
unreal_stub=types.ModuleType('unreal');unreal_stub.__getattr__=lambda name:Dummy
sys.modules['unreal']=unreal_stub
node_stub=types.ModuleType('editor_toolset.toolsets.blueprint_node')
for name in ('NodeInfo','PinInfo','PinID'):setattr(node_stub,name,type(name,(),{}))
sys.modules['editor_toolset']=types.ModuleType('editor_toolset');sys.modules['editor_toolset.toolsets']=types.ModuleType('editor_toolset.toolsets');sys.modules['editor_toolset.toolsets.blueprint_node']=node_stub
parser_path=Path('C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Experimental/Toolsets/EditorToolset/Content/Python/editor_toolset/toolsets/blueprint_dsl.py')
spec=importlib.util.spec_from_file_location('offline_pg_input_dsl',parser_path);parser=importlib.util.module_from_spec(spec);sys.modules[spec.name]=parser;spec.loader.exec_module(parser)
def audit_sequence(sequence):
 for index,form in enumerate(sequence):
  if not isinstance(form,list) or not form:continue
  continuations=[c for c in form if isinstance(c,list) and c and str(c[0]).startswith(':')]
  assert not continuations or index==len(sequence)-1,('terminal multi-exec followed by unreachable sibling',form[0])
  for c in continuations:audit_sequence(c[1:])
  if str(form[0]) in ('if','elif'):
   body=form[2:];alternate=body[-1] if body and isinstance(body[-1],list) and body[-1] and str(body[-1][0]) in ('else','elif') else None
   audit_sequence(body[:-1] if alternate else body)
   if alternate:audit_sequence(alternate[1:] if str(alternate[0])=='else' else [alternate])
  elif str(form[0])=='for':audit_sequence(form[3:])
for graph in captured:
 for function in parser.parse(graph['dsl']):audit_sequence(function[3:])
report={'python_syntax':True,'native_epic_dsl_parse':True,'terminal_flow':True,'no_gameplay_function_shortcuts_in_input_tests':True,'secondary_keyboard_and_round_ghost_graphs':len(captured),'official_rows_for_offline_capture_only':'stub1/1/2; editor script reads and validates actual readonly official table','runtime_input_or_transpiler_validated':False,'hashes':{str(p.relative_to(player)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
(here/'offline-report.json').write_text(json.dumps(report,indent=2));(here/'secondary-keyboard-dsl.json').write_text(json.dumps(captured,indent=2));print(json.dumps(report,indent=2))
