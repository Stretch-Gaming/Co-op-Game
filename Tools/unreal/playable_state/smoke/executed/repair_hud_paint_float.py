"""Regenerate only three HC OnPaint graphs from reviewed source; exact saves only."""
import hashlib,importlib.util,json,sys,traceback
from pathlib import Path
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
ROOT=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary');D=Path('/tmp/coop-runtime')
OUT=D/'hud-paint-float-repair.json';PACKET=D/'hud-paint-float-packet.json';BASE=D/'hud-paint-pin-inventory.json'
R={'passed':False,'packages_saved':[],'stage':'preflight','manifest':[],'scope':'HC three existing OnPaint graphs only; no variables, owner/input/gameplay/other graphs/designer/assets/settings edits'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write():
 tmp=OUT.with_suffix('.json.tmp');tmp.write_text(json.dumps(R,indent=2));tmp.replace(OUT)
def key(p):
 q=BP._pin_to_id(p) if hasattr(p,'get_owning_node') else p
 return {'node':q.node.get_name(),'index':q.index_id,'direction':str(q.direction)}
def snapshot(g):
 rows=[]
 for i in BP.get_node_infos(BP.find_nodes(g)):
  row={'name':i.node.get_name(),'class':i.node.get_class().get_name(),'type':str(i.type_id),'inputs':[],'outputs':[]}
  for direction,pins in [('inputs',i.input_pins),('outputs',i.output_pins)]:
   for p in pins:
    row[direction].append({'name':str(p.name),'type':str(p.type_id),'id':key(p.pin_id),'default':BP.get_pin_value(p.pin_id) if direction=='inputs' else None,'links':[key(q) for q in p.connected_pins]})
  rows.append(row)
 return sorted(rows,key=lambda x:x['name'])
def normalize(rows):
 result=json.loads(json.dumps(rows))
 for n in result:
  for p in n['inputs']+n['outputs']:p['links'].sort(key=lambda q:(q['node'],q['index'],q['direction']))
 return sorted(result,key=lambda x:x['name'])
def pure_scale_contract(path,bp,expected):
 rows=snapshot(BP.get_graph(bp,'OnPaint'));by={n['name']:n for n in rows};scales=[]
 for n in rows:
  if n['type']!='Math|Float|float/float':continue
  pins={p['name']:p for p in n['inputs']}
  a=pins['A']['links'];b=pins['B']['links']
  if len(a)!=1 or len(b)!=1:continue
  anum=by[a[0]['node']];den=by[b[0]['node']]
  if den['type']!='Math|Float|Max(Float)':continue
  if path.endswith('WBP_InteractPrompt'):
   if anum['type']!='Math|Float|MakeLiteralFloat' or not any(p['name']=='Value' and float(p['default'])==1.0 for p in anum['inputs']):continue
  elif anum['type']!='Math|Float|Clamp(Float)':continue
  scales.append(n)
 assert len(scales)==1,('Unique scale chain required',path,[n['name'] for n in scales])
 scale=scales[0];out=scale['outputs'][0]
 assert out['type']=='Float (double-precision)',('Scale must stay double',path,out)
 assert len(out['links'])==expected,('Scale fanout mismatch',path,len(out['links']),expected)
 for link in out['links']:
  target=by[link['node']];pin=target['inputs'][link['index']]
  assert target['type']=='Math|Float|float*float' and pin['name']=='B' and pin['type']=='Float (double-precision)',('Nonfloating scale consumer',path,target,pin)
 missing=[]
 for n in rows:
  if n['type'] in ('Math|Float|float*float','Math|Integer|int*int'):
   for p in n['inputs']:
    if p['name'] in ('A','B') and not p['links'] and p['default'] in ('','0','0.0','0.000000'):missing.append((n['name'],p['name']))
 assert not missing,('Paint multiply has zero operand',path,missing)
 fonts=[n for n in rows if n['type']=='Painting|DrawText']
 assert fonts and all(next(p for p in n['inputs'] if p['name']=='FontSize')['type']=='Float (single-precision)' for n in fonts)
 return {'scale_node':scale['name'],'scale_return_type':out['type'],'scale_fanouts':len(out['links']),'expected_scale_fanouts':expected,'zero_multiply_inputs':missing,'font_nodes':len(fonts),'node_count':len(rows)}
try:
 assert not OUT.exists(),'Do not overwrite a mutation receipt'
 assert Path(ue.Paths.project_dir()).resolve()==ROOT and not ue.EditorLevelLibrary.get_pie_worlds(True)
 packet=json.loads(PACKET.read_text());base=json.loads(BASE.read_text());allowed=set(packet['bodies'])
 assert allowed==set(base['widgets']) and len(allowed)==3
 assert sha(ROOT/packet['source_path'])==packet['source_sha256'],'Source packet changed'
 R.update({'manifest':sorted(allowed),'source_sha256':packet['source_sha256'],'packet_sha256':sha(PACKET),'baseline_sha256':sha(BASE),'before_disk_hashes':{},'results':{}})
 assets={};before_others={};before_entry={}
 for path in sorted(allowed):
  disk=ROOT/'Content'/(path[len('/Game/'):]+'.uasset');assert sha(disk)==base['widgets'][path]['saved_sha256'],('Saved baseline changed',path)
  bp=ue.load_asset(path);assets[path]=bp;R['before_disk_hashes'][path]=sha(disk)
  graphs={g.get_name():snapshot(g) for g in BP.list_graphs(bp)}
  assert set(graphs)==set(base['widgets'][path]['graphs'])
  for name,rows in graphs.items():assert normalize(rows)==normalize(base['widgets'][path]['graphs'][name]),('Loaded baseline changed',path,name)
  before_others[path]={name:normalize(rows) for name,rows in graphs.items() if name!='OnPaint'}
  before_entry[path]=[(n['name'],n['class']) for n in graphs['OnPaint'] if n['class'] in ('K2Node_FunctionEntry','K2Node_FunctionResult')]
  assert len(before_entry[path])==2
 assert ue.load_asset(packet['heading']) and ue.load_asset(packet['bodyfont'])
 # Isolated module adapts its exact root/ownership to these three assets only;
 # the existing Windows authoring source/guard is not edited or weakened.
 spec=importlib.util.spec_from_file_location('coop_hud_paint_private_authoring',ROOT/'Tools/unreal/six_round/authoring.py');authoring=importlib.util.module_from_spec(spec);sys.modules[spec.name]=authoring;spec.loader.exec_module(authoring)
 def guard():assert Path(ue.Paths.project_dir()).resolve()==ROOT and not ue.EditorLevelLibrary.get_pie_worlds(True)
 def owned(obj):guard();assert obj.get_path_name().split('.')[0] in allowed
 authoring.guard=guard;authoring.owned=owned
 write()
 for path,bp in assets.items():
  R['stage']='regenerate:'+path;write()
  authoring.write(bp,'OnPaint',packet['bodies'][path],'Context')
  contract=pure_scale_contract(path,bp,packet['expected_scale_fanouts'][path])
  after={g.get_name():snapshot(g) for g in BP.list_graphs(bp)}
  assert {name:normalize(rows) for name,rows in after.items() if name!='OnPaint'}==before_others[path],('Other graph changed',path)
  assert [(n['name'],n['class']) for n in after['OnPaint'] if n['class'] in ('K2Node_FunctionEntry','K2Node_FunctionResult')]==before_entry[path]
  R['results'][path]={'compile_warnings_as_errors_passed':True,'other_graphs_preserved':len(before_others[path]),'terminators_preserved':True,'paint_contract':contract};write()
 for path,bp in assets.items():
  R['stage']='save:'+path;write();assert ue.EditorAssetLibrary.save_loaded_asset(bp,False);R['packages_saved'].append(path);write()
 R.update({'passed':True,'stage':'complete','after_disk_hashes':{path:sha(ROOT/'Content'/(path[len('/Game/'):]+'.uasset')) for path in allowed}});write()
except Exception:
 R['error']=traceback.format_exc();write();raise
