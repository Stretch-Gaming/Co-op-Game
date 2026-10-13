"""Offline read-only analysis; safely evaluate selected pure source fragments only."""
import ast,collections,hashlib,json,re
from pathlib import Path
ROOT=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')
source=ROOT/'Tools/unreal/six_round/hud/build_hud.py'
module=ast.parse(source.read_text())
ns={'UI':'/Game/Puzzles/UI/SixRound/','ART':'/Game/Puzzles/Art/HCA3_UI/',
 'heading':'/Game/Shared/UI/Fonts/F_AveriaSerifLibre_Bold.F_AveriaSerifLibre_Bold',
 'bodyfont':'/Game/Shared/UI/Fonts/F_AveriaSerifLibre_Regular.F_AveriaSerifLibre_Regular',
 'V':lambda n:f'(Variables|Default|Get{n})'}
select=[]
for node in module.body:
 if isinstance(node,ast.FunctionDef) and node.name in ('xy','mul','box','panel','text'):select.append(node)
 if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in ('SCALE','body','pbody','rbody'):select.append(node)
# All selected function bodies and expressions are the source's pure string
# construction; no imports, guard, engine calls, loops over assets or saves execute.
exec(compile(ast.Module(body=select,type_ignores=[]),str(source),'exec'),ns)
def tokens(text):return re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',text)
def parse(text):
 stack=[];root=[]
 for tok in tokens(text):
  if tok=='(':
   x=[];(stack[-1] if stack else root).append(x);stack.append(x)
  elif tok==')':assert stack;stack.pop()
  else:(stack[-1] if stack else root).append(tok)
 assert not stack
 return root
def fmt(x):return '('+' '.join(map(fmt,x))+')' if isinstance(x,list) else x
def scales(forms):
 result=[]
 def walk(x,path):
  if not isinstance(x,list):return
  if len(x)==3 and x[0]=='*' and x[2]=='scale':result.append({'ordinal':len(result)+1,'form':fmt(x),'A_source':fmt(x[1]),'tree_position':path})
  for i,c in enumerate(x):walk(c,path+[i])
 for i,form in enumerate(forms):walk(form,[i])
 return result
inventory=Path('/tmp/coop-runtime/hud-paint-pin-inventory.json');native=json.loads(inventory.read_text())
R={'schema':1,'read_only_offline':True,'editor_calls':False,'source_file':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'native_inventory':str(inventory),'native_inventory_sha256':hashlib.sha256(inventory.read_bytes()).hexdigest(),'widgets':{}}
for asset,var,division in [('/Game/Puzzles/UI/HCA3/WBP_HCA3RoundHUD','body','K2Node_PromotableOperator_193'),('/Game/Puzzles/UI/WBP_InteractPrompt','pbody','K2Node_PromotableOperator_25'),('/Game/Puzzles/UI/Results/WBP_RunResults','rbody','K2Node_PromotableOperator_4')]:
 forms=parse(ns[var]);expected=scales(forms);g=native['widgets'][asset]['graphs']['OnPaint'];byname={n['name']:n for n in g}
 scale=byname[division]['outputs'][0];present=scale['links'];missing=[]
 for n in g:
  if n['class']!='K2Node_PromotableOperator' or n['type'] not in ('Math|Float|float*float','Math|Integer|int*int'):continue
  b=next(x for x in n['inputs'] if x['name']=='B')
  if b['links'] or b['default']!='':continue
  a=next(x for x in n['inputs'] if x['name']=='A');assert len(a['links'])==1
  incoming=byname[a['links'][0]['node']]
  missing.append({'node':n['name'],'pin':'B','type':b['type'],'default':b['default'],
   'A_node':incoming['name'],'A_type':incoming['type'],
   'A_input_defaults':{x['name']:x['default'] for x in incoming['inputs'] if not x['links']},
   'downstream':[{'node':x['node'],'pin_index':x['index']} for p in n['outputs'] for x in p['links']]})
 R['widgets'][asset]={'expected_source_scale_uses':len(expected),'existing_division':division,'division_return_type':scale['type'],
  'present_scale_output_links':len(present),'empty_unlinked_multiply_B_candidates':len(missing),
  'count_matches_source':len(expected)==len(present)+len(missing),'source_scale_uses':expected,'missing_candidates':missing}
 print(asset,'source_uses',len(expected),'present',len(present),'missing',len(missing),'type',scale['type'],'countmatch',len(expected)==len(present)+len(missing))
Path('/tmp/coop-audit/hud-scale-source-analysis.json').write_text(json.dumps(R,indent=2))
