"""Offline AST/DSL plus exact-save boundary tests. No Unreal calls or assets."""
import ast,json,hashlib,runpy,sys
from pathlib import Path
folder=Path(__file__).resolve().parent;root=folder.parents[3]
contract=runpy.run_path(str(folder/'test_map_contract.py'))
for bad in ('/Game/Maps/L_Site01','/Game/Puzzles/L_Site01_HC','/Game/Hazards/L_Site01_HZ','/Game/Puzzles/Test/SixRound/Unexpected'):
 try:contract['writable_package'](bad)
 except AssertionError:pass
 else:raise AssertionError('Unsafe package accepted: '+bad)
for good in contract['WRITE_MAPS']:assert contract['writable_package'](good)==good
for kwargs in ({'target_map':'/Game/Maps/L_Site01'},{'world_level':'/Game/Puzzles/EnvironmentConnection/L_ConnectedMaze'},{'player_level':'/Game/Player/L_Site01_PG'}):
 try:contract['validate_args'](kwargs)
 except AssertionError:pass
 else:raise AssertionError('Unsafe input accepted: '+str(kwargs))
parser_source=Path('C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Experimental/Toolsets/EditorToolset/Content/Python/editor_toolset/toolsets/blueprint_dsl.py').read_text(encoding='utf-8')
tree=ast.parse(parser_source);parser={};exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('Symbol','_source_line','_format_form','tokenize','parse')],type_ignores=[]),'EpicParser','exec'),parser)
class Fake:
 def __init__(self,path='/mock'):self.path=path
 def __getattr__(self,name):return self
 def __call__(self,*a,**kw):return self
 def __iter__(self):return iter([])
 def __bool__(self):return True
 def get_path_name(self):return self.path
 def get_outer(self):return fake
fake=Fake();checks=[];errors=[]
env={'Path':Path,'ROOT':root,'HERE':folder,'QUEUE':root/'Saved/SixRound','ue':fake,'BP':fake,'V':lambda n:f'(Variables|Default|Get{n})','S':lambda n,v:f'(Variables|Default|Set{n} {v})','GS':'(Utilities|Casting|CastToBP_CoopGameState :Object (Game|GetGameState))','STATE':'(bind (index phase attempt ends row) (Utilities|Struct|BreakSRoundState :S_RoundState (Class|BPCoopGameState|GetRoundState :self gs)))','EQ':lambda a,b:f'(Utilities|Enum|Equal(Enum) {a} {b})','CLEAR':'(Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator2")','COMPLETE':'(Utilities|Enum|LiteralenumE_RoundPhase :Enum "NewEnumerator4")'}
env.update(contract)
for name in ('guard','fn','save','compile_bp','event'):env[name]=lambda *a,**kw:fake
env['create']=lambda path,*a:Fake(path)
def audit(form):
 if not isinstance(form,list):return
 for i,item in enumerate(form):
  if not isinstance(item,list):continue
  if item and str(item[0])=='bind' and any(isinstance(c,list) and c and str(c[0]).startswith(':') for c in item[3:]) and i+1<len(form):
   after=form[i+1]
   if isinstance(after,list) and after and str(after[0])!='else':raise RuntimeError('Unreachable continuation sibling')
  audit(item)
def write(bp,name,body,parameters=''):
 code=f'(fn {name} ({parameters}) {body})'
 try:audit(parser['parse'](code));checks.append(name)
 except Exception as exc:errors.append({'function':name,'error':str(exc),'code':code})
env['write']=write
files=[folder/'50_place.py',folder/'puzzle_door_adapter.py',*folder.glob('test_map*.py')]
hashes={}
for file in files:
 ast.parse(file.read_text(encoding='utf-8'));hashes[file.name]=hashlib.sha256(file.read_bytes()).hexdigest()
 if file.name not in ('puzzle_door_adapter.py','test_map_game_mode.py'):continue
 env['__file__']=str(file);tree=ast.parse(file.read_text());tree.body=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom)) and not (isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='insert')]
 exec(compile(tree,str(file),'exec'),env)
report={'python_ast_files':len(files),'dsl_functions':len(checks),'unsafe_packages_rejected':4,'unsafe_args_rejected':3,'failures':errors,'script_sha256':hashes,'runtime_acceptance_pending':True}
queue=root/'Saved/SixRound';queue.mkdir(parents=True,exist_ok=True);(queue/'test-map-offline.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));raise SystemExit(bool(errors))
