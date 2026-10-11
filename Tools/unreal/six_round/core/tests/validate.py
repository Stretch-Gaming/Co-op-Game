"""Local read-only syntax/coverage inventory; does not run or accept game tests."""
import ast,json,hashlib
from pathlib import Path
folder=Path(__file__).resolve().parent;core=folder.parent
files=[core/'test_map_native_flow.py',core/'test_map_native_gate.py',core/'test_wipe.py',*folder.glob('*.py')]
for file in files:ast.parse(file.read_text(encoding='utf-8'))
# Expand resource monitor with the actual Epic S-expression parser. Syntax is not node/compile proof.
resource=core/'resource_recovery.py';ast.parse(resource.read_text(encoding='utf-8'))
parser_src=Path('C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Experimental/Toolsets/EditorToolset/Content/Python/editor_toolset/toolsets/blueprint_dsl.py').read_text(encoding='utf-8')
tree=ast.parse(parser_src);parser={};exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('Symbol','_source_line','_format_form','tokenize','parse')],type_ignores=[]),'EpicParser','exec'),parser)
class Fake:
 def __getattr__(self,name):return self
 def __call__(self,*a,**kw):return self
fake=Fake();env={'Path':Path,'__file__':str(resource),'ue':fake,'V':lambda n:f'(Variables|Default|Get{n})','S':lambda n,v:f'(Variables|Default|Set{n} {v})','GS':'(Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))','STATE':'(bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))','EQ':lambda a,b:f'(Utilities|Enum|Equal(Enum) {a} {b})','PLAY':'(Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator1")'}
for name in ('guard','var','fn','save','event'):env[name]=lambda *a,**kw:None
expanded=[]
def write(bp,name,body,parameters=''):
 code=f'(fn {name} ({parameters}) {body})';parsed=parser['parse'](code)
 def flow_audit(form):
  if not isinstance(form,list):return
  for i,item in enumerate(form):
   if not isinstance(item,list):continue
   if item and str(item[0])=='bind' and any(isinstance(c,list) and c and str(c[0]).startswith(':') for c in item[3:]) and i+1<len(form):
    after=form[i+1]
    if isinstance(after,list) and after and str(after[0])!='else':raise AssertionError('Unreachable cast continuation sibling')
   flow_audit(item)
 flow_audit(parsed);expanded.append(name)
env['write']=write;tree=ast.parse(resource.read_text());tree.body=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom)) and not (isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='insert')];exec(compile(tree,str(resource),'exec'),env)
report={'python_ast':True,'files':len(files)+1,'resource_dsl_functions':len(expanded),'sha256':{str(p.relative_to(core)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files+[resource]},'runtime_tests_executed':False}
root=core.parents[3];out=root/'Saved/SixRound/core-test-authoring.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
