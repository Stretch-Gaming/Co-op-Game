"""Offline syntax/DSL delimiter audit. This cannot validate Unreal node IDs/pins."""
import ast,hashlib,json,re,sys,types,importlib
from pathlib import Path
here=Path(__file__).resolve().parent;root=here.parents[3]
class Dummy:
 def __getattr__(self,name):return self
 def __call__(self,*args,**kwargs):return self
 def __iter__(self):return iter(())
 def __bool__(self):return True
 def __str__(self):return 'DummyBlueprint'
module=types.ModuleType('authoring');module.ue=Dummy();module.BP=Dummy()
module.ROOT=root;module.HERE=here.parent;module.QUEUE=root/'Saved/SixRound'
module.V=lambda name:f'(Variables|Default|Get{name})'
module.S=lambda name,value:f'(Variables|Default|Set{name} {value})'
module.OWNER='(Components|GetOwner)';module.AUTH_COMPONENT='(Networking|HasAuthority :self (Components|GetOwner))'
for name in ('guard','var','fn','save','event','compile_bp','owned'):setattr(module,name,lambda *args,**kwargs:None)
module.component=lambda *args,**kwargs:(Dummy(),Dummy());module.create=lambda *args,**kwargs:Dummy()
captured=[]
module.write=lambda bp,name,body,parameters='':captured.append({'script':current,'function':name,'dsl':f'(fn {name} ({parameters}) {body})'})
sys.modules['authoring']=module
old_reload=importlib.reload;importlib.reload=lambda item:item
try:
 for script in sorted(here.glob('*.py')):
  ast.parse(script.read_text(),filename=str(script))
  if script.name in ('validate_staged.py','stage0.py','repair_lever_declarations.py','test_client_inputs.py','audit_runtime.py','probe_traversal_flight.py'):continue
  current=script.name
  exec(compile(script.read_text(),str(script),'exec'),{'HERE':here.parent})
finally:importlib.reload=old_reload
errors=[]
# Use Epic's actual parser without Unreal runtime graph/node calls. Only its
# annotated node data types are stubbed; parsing implementation is unchanged.
parser_path=Path('C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Experimental/Toolsets/EditorToolset/Content/Python/editor_toolset/toolsets/blueprint_dsl.py')
assert parser_path.is_file(),parser_path
unreal_stub=types.ModuleType('unreal');unreal_stub.__getattr__=lambda name:Dummy
sys.modules['unreal']=unreal_stub
node_stub=types.ModuleType('editor_toolset.toolsets.blueprint_node')
for name in ('NodeInfo','PinInfo','PinID'):setattr(node_stub,name,type(name,(),{}))
sys.modules['editor_toolset']=types.ModuleType('editor_toolset')
sys.modules['editor_toolset.toolsets']=types.ModuleType('editor_toolset.toolsets')
sys.modules['editor_toolset.toolsets.blueprint_node']=node_stub
import importlib.util
spec=importlib.util.spec_from_file_location('offline_epic_blueprint_dsl',parser_path)
parser=importlib.util.module_from_spec(spec);sys.modules[spec.name]=parser
spec.loader.exec_module(parser)
def audit_sequence(sequence,graph):
 for index,form in enumerate(sequence):
  if not isinstance(form,list) or not form:continue
  continuations=[child for child in form if isinstance(child,list) and child and str(child[0]).startswith(':')]
  if continuations and index<len(sequence)-1:
   errors.append({'script':graph['script'],'function':graph['function'],'terminal_multi_exec':str(form[0]),'following_statement':str(sequence[index+1][0])})
  for continuation in continuations:audit_sequence(continuation[1:],graph)
  if str(form[0]) in ('if','elif'):
   then_forms=form[2:]
   alternate=then_forms[-1] if then_forms and isinstance(then_forms[-1],list) and then_forms[-1] and str(then_forms[-1][0]) in ('else','elif') else None
   audit_sequence(then_forms[:-1] if alternate else then_forms,graph)
   if alternate:audit_sequence(alternate[1:] if str(alternate[0])=='else' else [alternate],graph)
  elif str(form[0])=='for':audit_sequence(form[3:],graph)
  elif str(form[0])=='while':audit_sequence(form[2:],graph)
for graph in captured:
 parsed=parser.parse(graph['dsl'])
 for function in parsed:audit_sequence(function[3:],graph)
 depth=0
 for token in re.findall(r'"(?:[^"\\]|\\.)*"|[()]',graph['dsl']):
  if token=='(':depth+=1
  elif token==')':depth-=1
  if depth<0:break
 if depth!=0:errors.append({'script':graph['script'],'function':graph['function'],'delimiter_depth':depth})
 forbidden=[fragment for fragment in ('GetPlayerCharacter','GetPlayerController','GetPlayerPawn','AddtoViewport','ClearAllMappings','(set ') if fragment.lower() in graph['dsl'].lower()]
 if forbidden:errors.append({'script':graph['script'],'function':graph['function'],'forbidden':forbidden})
report={'python_syntax':True,'epic_native_dsl_parse':True,'dsl_delimiters_terminal_exec_and_policy':not errors,'graph_count':len(captured),'errors':errors,'node_ids_and_pins_validated':False,'editor_compile_and_pie_validated':False,'hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(here.glob('*.py'))}}
(here/'staged-validation.json').write_text(json.dumps(report,indent=2))
(here/'generated-dsl.json').write_text(json.dumps(captured,indent=2))
print(json.dumps(report,indent=2))
assert not errors,errors
