"""Offline authored-graph capture/native parsing only; no Unreal or assets."""
import ast,hashlib,importlib,importlib.util,json,sys,types
from pathlib import Path
here=Path(__file__).resolve().parent;script=here/'presentation_hooks.py';ast.parse(script.read_text(),filename=str(script))
class Meta(type):
 def __getattr__(cls,name):return Dummy()
class Dummy(metaclass=Meta):
 def __init__(self,*args,**kwargs):self.path=str(args[0]) if args else ''
 def __getattr__(self,name):return lambda *args,**kwargs:Dummy()
 def __call__(self,*args,**kwargs):return Dummy()
 def __iter__(self):return iter(())
 def __bool__(self):return True
 def get_editor_property(self,name):
  if name=='static_materials':return [Dummy()] if 'Arm' in self.path else [Dummy(),Dummy()]
  return Dummy()
 def get_path_name(self):return '/Game/Player/Art/Taker/Material'
class UeStub:
 def __getattr__(self,name):return Dummy
 def load_asset(self,path):return Dummy(path)
class Sink:
 def __truediv__(self,name):return self
 def write_text(self,*args,**kwargs):return 0
module=types.ModuleType('authoring');module.ue=UeStub();module.BP=Dummy();module.QUEUE=Sink()
for name in ('guard','var','fn','save','event','compile_bp'):setattr(module,name,lambda *args,**kwargs:None)
module.create=lambda *args,**kwargs:Dummy();module.component=lambda *args,**kwargs:(Dummy(),Dummy())
module.V=lambda name:f'(Variables|Default|Get{name})';module.S=lambda name,value:f'(Variables|Default|Set{name} {value})'
module.OWNER='(Components|GetOwner)';module.AUTH_COMPONENT='(Networking|HasAuthority :self (Components|GetOwner))'
graphs=[];module.write=lambda bp,name,body,parameters='':graphs.append({'function':name,'dsl':f'(fn {name} ({parameters}) {body})'})
sys.modules['authoring']=module;old_reload=importlib.reload;importlib.reload=lambda item:item
try:exec(compile(script.read_text(),str(script),'exec'),{'__file__':str(script),'ARGS':{}})
finally:importlib.reload=old_reload
unreal_stub=types.ModuleType('unreal');unreal_stub.__getattr__=lambda name:Dummy;sys.modules['unreal']=unreal_stub
node_stub=types.ModuleType('editor_toolset.toolsets.blueprint_node')
for name in ('NodeInfo','PinInfo','PinID'):setattr(node_stub,name,type(name,(),{}))
sys.modules['editor_toolset']=types.ModuleType('editor_toolset');sys.modules['editor_toolset.toolsets']=types.ModuleType('editor_toolset.toolsets');sys.modules['editor_toolset.toolsets.blueprint_node']=node_stub
parser_path=Path('C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Experimental/Toolsets/EditorToolset/Content/Python/editor_toolset/toolsets/blueprint_dsl.py')
spec=importlib.util.spec_from_file_location('offline_pg_presentation_dsl',parser_path);parser=importlib.util.module_from_spec(spec);sys.modules[spec.name]=parser;spec.loader.exec_module(parser)
def audit(sequence):
 for index,form in enumerate(sequence):
  if not isinstance(form,list) or not form:continue
  clauses=[c for c in form if isinstance(c,list) and c and str(c[0]).startswith(':')]
  assert not clauses or index==len(sequence)-1,('terminal continuation followed by sibling',form[0])
  for c in clauses:audit(c[1:])
  if str(form[0]) in ('if','elif'):
   body=form[2:];alternate=body[-1] if body and isinstance(body[-1],list) and body[-1] and str(body[-1][0]) in ('else','elif') else None
   audit(body[:-1] if alternate else body)
   if alternate:audit(alternate[1:] if str(alternate[0])=='else' else [alternate])
  elif str(form[0])=='for':audit(form[3:])
for graph in graphs:
 for function in parser.parse(graph['dsl']):audit(function[3:])
report={'source_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),'python_syntax':True,'native_dsl_parse':True,'terminal_flow':True,'graphs':len(graphs),'native_node_pin_compile_runtime_visual_gates':False}
(here/'presentation-report.json').write_text(json.dumps(report,indent=2));(here/'presentation-dsl.json').write_text(json.dumps(graphs,indent=2));print(json.dumps(report,indent=2))
