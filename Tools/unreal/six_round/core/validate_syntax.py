"""Offline Python + actual Epic S-expression parser gate; no Unreal mutations."""
import ast,json,re
from pathlib import Path
folder=Path(__file__).resolve().parent
source=Path('C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Experimental/Toolsets/EditorToolset/Content/Python/editor_toolset/toolsets/blueprint_dsl.py').read_text(encoding='utf-8')
module=ast.parse(source);parser=ast.Module(body=[n for n in module.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('Symbol','_source_line','_format_form','tokenize','parse')],type_ignores=[])
parser_env={};exec(compile(parser,'EpicDSLParser','exec'),parser_env)
class Fake:
 def __init__(self,path='fake'):self.path=path
 def __getattr__(self,name):return Fake(self.path+'/'+name)
 def __call__(self,*a,**kw):return self
 def __iter__(self):return iter([])
 def get_path_name(self):return self.path
 def __bool__(self):return True
checks=[];failures=[]
env={'Path':Path,'ROOT':folder.parents[3],'HERE':folder,'QUEUE':folder,'json':json,'ue':Fake(),'BP':Fake(),'I':'Index','P':'Phase','A':'Attempt','R':'ScalingRow','V':lambda n:f'(Variables|Default|Get{n})','S':lambda n,v:f'(Variables|Default|Set{n} {v})','OWNER':'(Components|GetOwner)','AUTH_COMPONENT':'(Networking|HasAuthority :self (Components|GetOwner))'}
for name in ('guard','fn','var','save','compile_bp','component','event','exclusive_event','interface'):env[name]=lambda *a,**kw:Fake()
env['create']=lambda path,*a:Fake(path)
# Use real shared expression constants, without importing Unreal.
common=ast.parse((folder/'common.py').read_text(encoding='utf-8'));start=next(i for i,n in enumerate(common.body) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='T' for t in n.targets))
exec(compile(ast.Module(body=common.body[start:],type_ignores=[]),'common','exec'),env)
env['exclusive_event']=lambda *a,**kw:None
for file in sorted(folder.glob('[0-9]*.py')):
 if file.name=='50_place.py': ast.parse(file.read_text(encoding='utf-8')); continue
 ast.parse(file.read_text(encoding='utf-8'))
 def write(bp,name,body,parameters=''):
  code=f'(fn {name} ({parameters}) {body})'
  try:
   parsed=parser_env['parse'](code)
   def check_flow(form):
    if not isinstance(form,list):return
    for idx,item in enumerate(form):
     if not isinstance(item,list):continue
     continuations=[c for c in item[3:] if isinstance(c,list) and c and str(c[0]).startswith(':')]
     if item and str(item[0])=='bind' and continuations and idx+1<len(form):
      following=form[idx+1]
      if isinstance(following,list) and following and str(following[0])!='else':raise RuntimeError('Cast continuation has unreachable following sibling: '+str(following))
     check_flow(item)
   check_flow(parsed)
   checks.append({'file':file.name,'function':name})
  except Exception as exc:failures.append({'file':file.name,'function':name,'error':str(exc),'code':code})
 env['write']=write;env['__file__']=str(file)
 tree=ast.parse(file.read_text(encoding='utf-8'));tree.body=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom)) and not (isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='insert')]
 try:exec(compile(tree,str(file),'exec'),env)
 except Exception as exc:failures.append({'file':file.name,'python_eval':str(exc)})
report={'python_ast':True,'dsl_functions':len(checks),'failures':failures,'note':'Syntax only; node resolution, compilation and runtime remain editor gates.'}
(folder/'syntax-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));raise SystemExit(bool(failures))
