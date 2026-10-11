"""Primary native compile/graph gate for only the collected changed assets.
Run after collect_changed_assets.py, with all fixes saved and PIE stopped.
No SaveAll: only successfully compiled, graph-clean changed Blueprints with
an exact own-lease entry may be saved. Templates outside this list are read-only
and are not exceptions for any changed asset. This is not gameplay acceptance.
"""
import sys,json,hashlib,re,traceback
from pathlib import Path
_here=Path(__file__).resolve().parent if '__file__' in globals() else Path(ROOT)/'Tools/unreal/six_round'
sys.path.insert(0,str(_here))
import authoring as author
ue=author.ue;BP=author.BP;ROOT=author.ROOT;QUEUE=author.QUEUE
assert ROOT.resolve()==author.EXPECTED and Path(ue.Paths.project_dir()).resolve()==author.EXPECTED
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
args=globals().get('ARGS',{});assert args.get('inventory','changed-assets.json')=='changed-assets.json'
inventory=json.loads((QUEUE/'changed-assets.json').read_text(encoding='utf-8-sig'))
assert Path(inventory['project']).resolve()==ROOT.resolve()
allowed=('Content/Core/','Content/Hazards/','Content/Player/','Content/Puzzles/','Content/Shared/')
def sha(relative):
 p=ROOT/relative
 return hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
leases={row['path']:row for row in inventory['leases']}
report={'inventory_head':inventory['head'],'inventory_captured_utc':inventory['captured_utc'],'assets':[],'errors':[],'protected_before':{p:sha(p) for p in inventory['protected_hashes']},'template_exceptions':[],'warnings_as_errors':True,'gameplay_acceptance':False}
assert report['protected_before']==inventory['protected_hashes'],'Protected sources differ from collector baseline'
# authoring.guard otherwise preloads unrelated contracts. Only explicit load_asset
# calls for inventory assets are authorized here; engine dependency loading is automatic.
old_preloaded=author._contracts_loaded;author._contracts_loaded=True
try:
 for entry in inventory['assets']:
  relative=entry['relative_path'];path=entry['asset_path']
  assert relative.startswith(allowed) and relative.endswith(('.uasset','.umap')) and '..' not in Path(relative).parts
  assert path=='/Game/'+relative[len('Content/'):].rsplit('.',1)[0]
  row={'relative_path':relative,'path':path,'sha256_before':sha(relative),'class':None,'parent':None,'compile':'not_blueprint','saved':False,'flags':[],'error':None}
  report['assets'].append(row)
  try:
   assert row['sha256_before']==entry['sha256'],'Changed since collector; recollect exact inputs'
   row['registered']=bool(ue.EditorAssetLibrary.does_asset_exist(path))
   assert row['registered'],'Missing registered asset (includes deleted inventory entries); review explicitly'
   assert row['sha256_before'] is not None,'Registered asset missing on disk'
   obj=ue.load_asset(path);assert obj,'Registered asset failed to load'
   row['class']=obj.get_class().get_name()
   if isinstance(obj,ue.Blueprint):
    row['compile']='pending'
    parent=BP.get_parent(obj);row['parent']=parent.get_path_name() if parent else None
    # A graph-inspection error must not skip compilation of this Blueprint.
    try:author.compile_bp(obj);row['compile']='passed'
    except Exception:
     row['compile']='failed';row['compile_error']=traceback.format_exc()
    for graph in BP.list_graphs(obj):
     dsl=BP.read_graph_dsl(graph)
     for node in BP.find_nodes(graph):
      type_id=BP._get_node_info(node).type_id;leaf=re.sub('[^a-z0-9]','',type_id.rsplit('|',1)[-1].lower())
      if leaf=='addtoviewport':row['flags'].append({'graph':graph.get_name(),'node':type_id,'rule':'AddToViewport; owning AddToPlayerScreen required'})
      if leaf in ('getplayercharacter','getplayercontroller','getplayerpawn'):
       pin=node.find_input_pin('PlayerIndex')
       if pin and list(pin.list_connected_pins()):continue
       # Exported literal calls have no nested expressions. Omitted PlayerIndex
       # is the native default zero. Ambiguous export fails instead of passing.
       calls=re.findall(r'\([^()\s]*'+leaf+r'\b([^()]*)\)',dsl,re.IGNORECASE)
       values=[re.search(r':PlayerIndex\s+([^\s)]+)',body,re.IGNORECASE) for body in calls]
       literals=[v.group(1) if v else '0' for v in values]
       if not literals or any(v in ('0','0.0') for v in literals):
        row['flags'].append({'graph':graph.get_name(),'node':type_id,'rule':'literal player index zero or unverifiable unlinked index','exported_literals':literals})
    assert row['compile']=='passed',row.get('compile_error','Blueprint compile failed')
    lease=leases.get(relative);row['lease_id']=lease.get('id') if lease else None
    hc_owned=relative.startswith('Content/Puzzles/')
    row['save_authority']='HC-owned Puzzles folder under AGENTS.md' if hc_owned else 'exact LFS lease'
    if not hc_owned:assert lease and lease.get('owner',{}).get('name')==inventory['required_lease_owner'],'Exact own lease missing; compile result retained, refuse save'
    elif lease:assert lease.get('owner',{}).get('name')==inventory['required_lease_owner'],'Refuse another person\'s Puzzles lease'
    assert not row['flags'],'Gameplay graph policy gate failed; refuse save'
    assert obj.get_path_name().split('.')[0]==path
    assert ue.EditorAssetLibrary.save_loaded_asset(obj,False),'Exact Blueprint save failed'
    row['saved']=True
  except Exception:
   row['error']=traceback.format_exc();report['errors'].append({'path':path,'error':row['error']})
  finally:row['sha256_after']=sha(relative)
finally:author._contracts_loaded=old_preloaded
report['protected_after']={p:sha(p) for p in inventory['protected_hashes']}
if report['protected_after']!=report['protected_before']:report['errors'].append({'error':'Protected source hash changed during audit'})
report['passed']=not report['errors'] and not any(row['flags'] for row in report['assets'])
report['asset_count']=len(report['assets']);report['blueprints_compiled']=sum(r['compile']=='passed' for r in report['assets']);report['blueprints_saved']=sum(r['saved'] for r in report['assets'])
(QUEUE/'saved-assets-audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
RESULT=report
assert report['passed'],'Changed-asset audit failed; inspect Saved/SixRound/saved-assets-audit.json'
