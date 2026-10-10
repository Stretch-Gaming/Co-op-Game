"""Offline syntax-only gate; actual Epic parser, no Unreal asset writes."""
import ast,json
from pathlib import Path
folder=Path(__file__).resolve().parent
source=Path('C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Experimental/Toolsets/EditorToolset/Content/Python/editor_toolset/toolsets/blueprint_dsl.py').read_text(encoding='utf-8')
parsed=ast.parse(source);parser={};exec(compile(ast.Module(body=[n for n in parsed.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('Symbol','_source_line','_format_form','tokenize','parse')],type_ignores=[]),'EpicParser','exec'),parser)
class Fake:
 def __getattr__(self,name):return self
 def __call__(self,*args,**kwargs):return self
 def __iter__(self):return iter([])
 def __bool__(self):return True
 def get_path_name(self):return '/mock'
fake=Fake();file=folder/'build_hud.py';env={'Path':Path,'ue':fake,'BP':fake,'__file__':str(file),'ROOT':folder.parents[3],'HERE':folder,'ARGS':{},'V':lambda n:f'(Variables|Default|Get{n})','S':lambda n,v:f'(Variables|Default|Set{n} {v})'}
for name in ('guard','var','fn','event','save'):env[name]=lambda *a,**kw:fake
checks=[];failures=[];paint_bodies=[]
def write(bp,name,body,parameters=''):
 code=f'(fn {name} ({parameters}) {body})'
 try:
  parsed=parser['parse'](code)
  def audit(form):
   if not isinstance(form,list):return
   for i,item in enumerate(form):
    if not isinstance(item,list):continue
    if item and str(item[0])=='bind' and any(isinstance(c,list) and c and str(c[0]).startswith(':') for c in item[3:]) and i+1<len(form):
     next_=form[i+1]
     if isinstance(next_,list) and next_ and str(next_[0])!='else':raise RuntimeError('Unreachable sibling after '+str(item[:2])+' -> '+str(next_[:2]))
    audit(item)
  audit(parsed)
  if name=='OnPaint':
   paint_bodies.append(code)
   def const_audit(form):
    if not isinstance(form,list):return
    if form and str(form[0]).startswith('Variables|Default|Set'):raise RuntimeError('OnPaint mutates a widget property')
    if form and str(form[0]).startswith('CallFunction|'):raise RuntimeError('OnPaint invokes a mutable self function')
    for item in form:const_audit(item)
   const_audit(parsed)
  checks.append(name)
 except Exception as exc:failures.append({'function':name,'error':str(exc),'code':code})
env['write']=write
tree=ast.parse(file.read_text());tree.body=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom)) and not (isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute) and n.value.func.attr=='insert')]
exec(compile(tree,str(file),'exec'),env)
report={'python_ast':True,'dsl_functions':len(checks),'const_paint_graphs':len(paint_bodies),'onpaint_setters':0 if not failures else 'failed','failures':failures,'runtime_visual_acceptance_pending':True};(folder/'syntax-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));raise SystemExit(bool(failures))
