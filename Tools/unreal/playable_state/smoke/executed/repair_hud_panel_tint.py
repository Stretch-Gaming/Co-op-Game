import ast,hashlib,json,traceback
from pathlib import Path
import unreal as ue
import toolset_registry
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
ROOT=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary');D=Path('/tmp/coop-runtime');OUT=D/'hud-panel-tint-repair.json';R={'passed':False,'stage':'preflight','packages_saved':[],'scope':'24 existing DrawBox Tint literals across HC three OnPaint graphs only'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write():
 t=OUT.with_suffix('.tmp');t.write_text(json.dumps(R,indent=2));t.replace(OUT)
def k(q):return (q.node.get_name(),q.index_id,str(q.direction))
def snapshot(g):
 result=[]
 for i in BP.get_node_infos(BP.find_nodes(g)):
  n={'name':i.node.get_name(),'class':i.node.get_class().get_name(),'type':str(i.type_id),'inputs':[],'outputs':[]}
  for side,pins in [('inputs',i.input_pins),('outputs',i.output_pins)]:
   for p in pins:n[side].append({'name':str(p.name),'type':str(p.type_id),'default':BP.get_pin_value(p.pin_id) if side=='inputs' else None,'links':sorted(k(q) for q in p.connected_pins)})
  result.append(n)
 return sorted(result,key=lambda n:n['name'])
try:
 assert Path(ue.Paths.project_dir()).resolve()==ROOT and not ue.EditorLevelLibrary.get_pie_worlds(True) and not OUT.exists()
 repair=json.loads((D/'hud-paint-float-repair.json').read_text());assert repair['passed']
 src=ROOT/'Tools/unreal/six_round/hud/build_hud.py';tree=ast.parse(src.read_text());color_nodes=[n for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='colors'];assert len(color_nodes)==1;colors=ast.literal_eval(color_nodes[0].value)
 R['source_sha256']=sha(src);R['results']={};assets={};expected={}
 for path,original_sha in repair['after_disk_hashes'].items():
  disk=ROOT/'Content'/(path[6:]+'.uasset');assert sha(disk)==original_sha
  bp=ue.load_asset(path);assets[path]=bp;expected[path]={g.get_name():snapshot(g) for g in BP.list_graphs(bp)}
  edits=[]
  for i in BP.get_node_infos(BP.find_nodes(BP.get_graph(bp,'OnPaint'))):
   if str(i.type_id)!='Painting|DrawBox':continue
   pins={str(p.name):p for p in i.input_pins};value=BP.get_pin_value(pins['Brush'].pin_id)
   name=next((name for name in colors if value=='/Game/Puzzles/UI/SixRound/DA_'+name+'Brush.DA_'+name+'Brush'),None)
   if not name:continue
   p=pins['Tint'];assert not p.connected_pins and str(p.type_id)=='Linear Color Structure';old=BP.get_pin_value(p.pin_id)
   assert old=='(R=1.000000,G=1.000000,B=1.000000,A=1.000000)' or old=='(R=1,G=1,B=1,A=1)',('Unexpected initial tint',path,i.node.get_name(),old)
   r,g,b,a=colors[name];new=f'(R={r},G={g},B={b},A={a})';edits.append((i.node.get_name(),p.pin_id,old,new))
  assert len(edits)==(16 if path.endswith('WBP_HCA3RoundHUD') else 4)
  R['results'][path]={'edits':[{'node':name,'before':old,'after':new} for name,p,old,new in edits]}
  expected_nodes={n['name']:n for n in expected[path]['OnPaint']}
  R['stage']='tint:'+path;write()
  with toolset_registry.tool_raising_exceptions():
   for name,p,old,new in edits:
    BP.set_pin_value(p,new);normalized=BP.get_pin_value(p)
    next(v for v in expected_nodes[name]['inputs'] if v['name']=='Tint')['default']=normalized
   BP.compile_blueprint(bp,warnings_as_errors=True)
  actual={g.get_name():snapshot(g) for g in BP.list_graphs(bp)};assert actual==expected[path],('Unexpected graph change',path)
  R['results'][path]['strict_compile_and_only_tint_default_changes']=True;write()
 for path,bp in assets.items():
  R['stage']='save:'+path;write();assert ue.EditorAssetLibrary.save_loaded_asset(bp,False);R['packages_saved'].append(path);write()
 R.update({'passed':True,'stage':'complete','final_widget_sha256':{path:sha(ROOT/'Content'/(path[6:]+'.uasset')) for path in assets}});write()
except Exception:R['error']=traceback.format_exc();write();raise
