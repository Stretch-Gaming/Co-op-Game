"""Offline pure-source float arithmetic contract; no Unreal/editor/Git calls.

Evaluate only five pure string helpers +literal colors/SCALE/body/pbody/rbody AST assignments.
Do not import/execute the original builder or write into the repository.
Keep baseline inventory/source analysis immutable and compare all scale uses.
"""
import ast,hashlib,json,re
from pathlib import Path
ROOT=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')
baseline_path=Path('/tmp/coop-audit/hud-scale-source-analysis.json')
baseline=json.loads(baseline_path.read_text())
# Reuse only the already inspected offline extraction/parser definitions. That
# prefix evaluates selected pure AST fragments and defines parsing; no writes.
prelude=Path('/tmp/coop-audit/analyze_hud_scale_source.py').read_text().split('inventory=Path(')[0]
prelude=prelude.replace("('SCALE','body','pbody','rbody')","('colors','SCALE','body','pbody','rbody')")
ns_env={};exec(compile(prelude,'<offline-pure-source-extraction>','exec'),ns_env)
source=ns_env['source'];ns=ns_env['ns'];scales=ns_env['scales']
# Load the installed DSL's pure parser AST only: handles parentheses inside
# catalog IDs exactly as Unreal does; no unreal imports or transpiler execution.
engine_parser=Path('/Volumes/CoopBuild/UnrealEngine/UE_5.8/Engine/Plugins/Experimental/Toolsets/EditorToolset/Content/Python/editor_toolset/toolsets/blueprint_dsl.py')
parser_ast=ast.parse(engine_parser.read_text());pure=[]
for n in parser_ast.body:
 if isinstance(n,ast.ClassDef) and n.name=='Symbol':pure.append(n)
 if isinstance(n,ast.FunctionDef) and n.name in ('_source_line','tokenize','parse'):pure.append(n)
parser_ns={};exec(compile(ast.Module(body=pure,type_ignores=[]),str(engine_parser),'exec'),parser_ns)
parse=parser_ns['parse']
def fmt(x):return '('+' '.join(map(fmt,x))+')' if isinstance(x,list) else str(x)
ns_env['fmt']=fmt
inventory=json.loads(Path('/tmp/coop-runtime/hud-paint-pin-inventory.json').read_text())
R={'schema':1,'read_only_offline':True,'editor_calls':False,'original_builder_executed':False,
 'current_source':str(source),'current_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'baseline_analysis_sha256':hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
 'native_inventory_sha256':hashlib.sha256(Path('/tmp/coop-runtime/hud-paint-pin-inventory.json').read_bytes()).hexdigest(),
 'widgets':{},'font_parameter':'Float(single-precision), DrawTextFormatted; not Integer',
 'float_precision_boundary':'Preserve fractions via native implicit double->float; explicit deprecated Conv_DoubleToFloat/Truncate not included'}
for asset,var in [('/Game/Puzzles/UI/HCA3/WBP_HCA3RoundHUD','body'),('/Game/Puzzles/UI/WBP_InteractPrompt','pbody'),('/Game/Puzzles/UI/Results/WBP_RunResults','rbody')]:
 forms=parse(ns[var]);expected=scales(forms);bad=[];fonts=[];cast_count=[0];solid_tints=[]
 def walk(x,path):
  if not isinstance(x,list):return
  if x and x[0] in ('*','/','+','-'):
   for arg in x[1:]:
    if (isinstance(arg,int) and not isinstance(arg,bool)) or (isinstance(arg,str) and arg in ('rowCount','row')):bad.append({'tree_position':path,'arithmetic':fmt(x),'integer_arg':arg})
  if x and x[0]=='Math|Conversions|ToFloat(Integer)':cast_count[0]+=1
  if x and x[0]=='Painting|DrawBox' and ':Brush' in x:
   brush=x[x.index(':Brush')+1]
   solids=[name for name in ns['colors'] if str(brush).endswith('DA_'+name+'Brush.DA_'+name+'Brush')]
   if solids:
    assert len(solids)==1 and ':Tint' in x,'Explicit solid panel Tint required'
    name=solids[0];tint=str(x[x.index(':Tint')+1])
    expected_tint='(R={},G={},B={},A={})'.format(*ns['colors'][name])
    assert tint==expected_tint,(name,tint,expected_tint)
    solid_tints.append({'brush':name,'tint':tint})
  if x and x[0]=='Painting|DrawText':
   assert ':FontSize' in x
   font=x[x.index(':FontSize')+1];fonts.append(fmt(font))
   assert isinstance(font,list) and len(font)==3 and font[0]=='*' and font[2]=='scale','Float font product shape changed'
  for i,c in enumerate(x):walk(c,path+[i])
 for i,f in enumerate(forms):walk(f,[i])
 b=baseline['widgets'][asset];assert len(expected)==b['expected_source_scale_uses']
 assert not bad,('Integer contamination remains in paint geometry',asset,bad)
 assert all(not re.fullmatch(r'-?\d+',u['A_source']) for u in expected),'Integer scale literal remains'
 old=inventory['widgets'][asset]['graphs']['OnPaint'];byname={n['name']:n for n in old}
 division=byname[b['existing_division']]['outputs'][0]
 user_names={x['node'] for x in division['links']}|{x['node'] for x in b['missing_candidates']}
 users=sorted((byname[n] for n in user_names),key=lambda n:int(n['name'].rsplit('_',1)[-1]))
 assert len(users)==len(expected)
 mapping=[]
 for e,n in zip(b['source_scale_uses'],users):
  a=next(p for p in n['inputs'] if p['name']=='A');assert len(a['links'])==1
  incoming=byname[a['links'][0]['node']];literal=None
  if re.fullmatch(r'-?\d+(\.\d+)?',e['A_source']):
   defaults={p['name']:p['default'] for p in incoming['inputs'] if not p['links']}
   assert incoming['type'] in ('Math|Float|MakeLiteralFloat','Math|Integer|MakeLiteralInt')
   assert float(defaults['Value'])==float(e['A_source']) and float(e['A_source'])!=0
   literal=float(e['A_source'])
  bp=next(p for p in n['inputs'] if p['name']=='B')
  mapping.append({'source_ordinal':e['ordinal'],'baseline_source_A':e['A_source'],'current_source_tree_position':expected[e['ordinal']-1]['tree_position'],'current_source_A':expected[e['ordinal']-1]['A_source'],
   'native_node':n['name'],'native_A_node':incoming['name'],'native_A_type':incoming['type'],
   'literal_A_exactly_matches_nonzero_source':literal is not None,
   'native_B_links':len(bp['links']),'native_B_empty_numeric_zero':not bp['links'] and bp['default']=='',
   'native_B_type':bp['type']})
 intended_missing=[m for m in mapping if m['native_B_empty_numeric_zero']]
 assert len(intended_missing)==b['empty_unlinked_multiply_B_candidates']
 R['widgets'][asset]={'expected_scale_output_links':len(expected),'baseline_missing_scale_B_links':len(intended_missing),
  'source_positions_and_native_consumers':mapping,'font_product_count':len(fonts),'font_products':fonts,
  'geometry_integer_to_float_cast_count':cast_count[0],'arithmetic_integer_violations':bad,
  'float_source_contract_passed':True,'explicit_solid_panel_tints':solid_tints,'native_post_regeneration_required':{'scale_return_type':'Float(double-precision)',
   'scale_fanout':len(expected),'all_expected_multiply_B_linked':True,'empty_unlinked_scale_B_count':0,
   'FontSize':'Float(single-precision), existing implicit real conversion allowed',
   'no_other_graph_or_designer_or_owner_data_changes':True,'strict_compile':True,'native_visible_HUD_client_and_hostsplit':'required separately'}}
 Path('/tmp/coop-audit/'+var+'-float-contract-final.dsl').write_text(ns[var])
print('CURRENT SOURCE',R['current_source_sha256'])
for a,w in R['widgets'].items():print(a,'scale',w['expected_scale_output_links'],'baseline missing',w['baseline_missing_scale_B_links'],'drawtext',w['font_product_count'],'geometry casts',w['geometry_integer_to_float_cast_count'],'FLOAT SOURCE PASS')
R['all_float_source_contracts_passed']=True
R['explicit_solid_panel_tint_count']=sum(len(w['explicit_solid_panel_tints']) for w in R['widgets'].values())
assert R['explicit_solid_panel_tint_count']==24
print('EXPLICIT EXISTING COLOR TINTS',R['explicit_solid_panel_tint_count'])
Path('/tmp/coop-audit/hud-float-scale-contract-final.json').write_text(json.dumps(R,indent=2))
