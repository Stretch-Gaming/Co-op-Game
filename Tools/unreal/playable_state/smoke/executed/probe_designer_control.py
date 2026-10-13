"""Parent-only PIE control for rendered-HUD diagnosis; no asset edits/saves.

ARGS action=create (default), read, or cleanup; report_name defaults
'designer-control-runtime'; optional owner_id selects an actual local joining
controller's PlayerState ID. Otherwise choose a joining owner by world path/ID.
Create one verified existing UI_Vehicle instance using its explicit owning PC,
AddToPlayerScreen(0), observe <=8 actual Slate callbacks/5s callback deadline,
then KEEP it attached for the parent's native-window screenshot. Only explicit
cleanup removes this exact instance. No gameplay/input/viewport preference edits.
Native geometry readback is not rendered-pixel acceptance and zero stays zero.
"""
import hashlib,json,os,re,time,traceback
from pathlib import Path
import unreal as ue

EXPECTED=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary')
SOURCE=Path('/tmp/coop-audit/probe_designer_control.py')
ASSET='/Game/VehicleTemplate/UI/UI_Vehicle'
DISK=EXPECTED/'Content/VehicleTemplate/UI/UI_Vehicle.uasset'
ASSET_SHA='8c43a8756d2f29837d9eec323226f3a9e3061debb9a3b577ab502d985d3f59cb'
DESIGNER=Path('/tmp/coop-audit/runtime-evidence/designer-control-inventory.json')
DESIGNER_SHA='5717fb1a64b6058f9405142ff58b4b880a0ca55d2a2361e9d5613c1ed6e015f4'
GRAPHS=Path('/tmp/coop-runtime/vehicle-graphs.json')
GRAPHS_SHA='60d5c9d13cb7d80590cae587ebc518566fd89cf2ec0756926bdd983e4045cccf'
args=globals().get('ARGS',{});action=args.get('action','create')
name=args.get('report_name','designer-control-runtime')
assert re.fullmatch(r'[A-Za-z0-9_-]+',name)
OUT=Path('/tmp/coop-audit/runtime-evidence')/(name+'.json')
assert action in ('create','read','cleanup')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(o):return o.get_path_name() if o else None
def vec(v):return [float(v.x),float(v.y)]
def bounds(g):return vec(ue.SlateLibrary.get_local_size(g))
def positive(v):return len(v)==2 and all(x>1.0 for x in v)
def write(r):
 OUT.parent.mkdir(parents=True,exist_ok=True)
 tmp=OUT.with_suffix('.json.tmp');tmp.write_text(json.dumps(r,indent=2));tmp.replace(OUT)
def geometry(w):
 return {'path':ref(w),'class':ref(w.get_class()),'world':ref(w.get_world()),
  'visibility':str(w.get_visibility()),'opacity':float(w.get_render_opacity()),
  'desired':vec(w.get_desired_size()),'cache':bounds(w.get_cached_geometry()),
  'paint':bounds(w.get_paint_space_geometry()),'tick':bounds(w.get_tick_space_geometry())}
def runtime_tree(control):
 # WidgetTree duplicates each designer widget with outer=runtime WidgetTree;
 # WidgetTree's outer is this exact runtime UserWidget. No unexposed root setter.
 rows=[]
 for w in ue.ObjectIterator(ue.Widget):
  outer=w.get_outer()
  if outer and outer.get_outer()==control:
   row=geometry(w);row.update({'name':w.get_name(),'outer':ref(outer),'parent':ref(w.get_parent())})
   if isinstance(w,ue.TextBlock):row['text']=str(w.get_text())
   rows.append(row)
 assert len(rows)==9 and len({r['name'] for r in rows})==9,'Expected exact duplicated nine-widget designer tree'
 assert sum(r['class']=='/Script/UMG.Overlay' and r['parent'] is None for r in rows)==1
 return sorted(rows,key=lambda r:r['name'])
def find_exact_control(r):
 assert r['editor_pid']==os.getpid(),'Receipt belongs to a different editor process'
 found=[w for w in ue.ObjectIterator(ue.UserWidget) if ref(w)==r['control_path']]
 assert len(found)==1,'Exact previously created runtime control no longer exists'
 w=found[0];pc=w.get_owning_player()
 assert ref(w.get_class())==ASSET+'.UI_Vehicle_C' and pc
 assert ref(pc)==r['owner_controller'] and ref(w.get_world())==r['owner_world']
 assert pc.is_local_controller() and pc.player_state and pc.player_state.player_id==r['owner_id']
 return w,pc

def inspect_existing(w,pc,sub):
 return {'control':geometry(w),'tree':runtime_tree(w),'in_viewport':bool(w.is_in_viewport()),
  'subsystem_widget_added':bool(sub.is_widget_added(w)),'owning_controller':ref(w.get_owning_player()),
  'pixels':vec(ue.WidgetLayoutLibrary.get_viewport_size(pc)),
  'viewport':bounds(ue.WidgetLayoutLibrary.get_viewport_widget_geometry(pc)),
  'player':bounds(ue.WidgetLayoutLibrary.get_player_screen_widget_geometry(pc))}

class ControlProbe:
 def __init__(self):
  self.control=None;self.handle=None;self.finished=False;self.callbacks=0;self.start=time.monotonic();self.owners=[]
  self.r={'schema':1,'status':'preflight','collection_complete':False,'pie_only':True,'packages_saved':[],
   'script_file':str(SOURCE),'script_sha256':sha(SOURCE),'editor_pid':os.getpid(),
   'rendered_pixel_acceptance':False,'native_log_scan_pending':True,'fixture_actions':[],
   'callback_limit':8,'wall_poll_limit_seconds':5,'samples':[],
   'callback_type':'actual Slate post-tick callback, not an inferred paint frame',
   'limitations':['Control remains attached for parent screenshot until explicit cleanup or StopPIE.',
    'Positive native geometry is layout/paint readback; pixel visibility needs native-window observation.',
    'Wall deadline is checked on callbacks; a stalled editor requires parent cancellation.']}
  assert Path(ue.Paths.project_dir()).resolve()==EXPECTED,'Wrong editor project'
  assert not OUT.exists(),'Use a new report_name; create never overwrites an earlier receipt'
  assert sha(DISK)==ASSET_SHA and sha(DESIGNER)==DESIGNER_SHA and sha(GRAPHS)==GRAPHS_SHA,'Pinned native candidate proof changed'
  d=json.loads(DESIGNER.read_text());g=json.loads(GRAPHS.read_text())
  assert d['collection_complete'] and 'error' not in d and g['read_only']
  vehicle=[a for a in d['assets'] if a['asset']==ASSET];assert len(vehicle)==1
  assert vehicle[0]['root_widget_class']=='/Script/UMG.Overlay' and vehicle[0]['widget_count']==9
  assert vehicle[0]['saved_bytes_unchanged'] and vehicle[0]['saved_asset_sha256']==ASSET_SHA
  assert set(g['graphs'])=={'EventGraph'} and g['asset']==ASSET+'.UI_Vehicle'
  # Pinned parent-native graph contains only PreConstruct unit-label SetText and
  # custom speed/gear text setters, no pawn/vehicle/controller access on creation.
  self.r['candidate_proofs']={'asset_sha256':ASSET_SHA,'designer_receipt_sha256':DESIGNER_SHA,'graphs_receipt_sha256':GRAPHS_SHA,
   'creation_event_review':'PreConstruct sets existing UnitLabel only; custom UpdateSpeed/UpdateGear not invoked'}
  self.sub=ue.get_engine_subsystem(ue.GameViewportSubsystem);assert self.sub
  worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));assert 2<=len(worlds)<=3,'Fresh two-player PIE required'
  server=[w for w in worlds if ue.GameplayStatics.get_game_mode(w)];assert len(server)==1
  self.server=server[0]
  C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
  HC=ue.load_asset('/Game/Puzzles/UI/HCA3/AC_HCA3HUD').generated_class()
  server_pawns=list(ue.GameplayStatics.get_all_actors_of_class(self.server,C));assert len(server_pawns)==2
  ids={p.player_state.player_id for p in server_pawns};assert len(ids)==2
  self.r['world_inventory']=[]
  for world in worlds:
   pawns=list(ue.GameplayStatics.get_all_actors_of_class(world,C))
   assert {p.player_state.player_id for p in pawns}==ids,'Two-player roster must have replicated to all peers'
   local=[p for p in pawns if p.is_locally_controlled()]
   self.r['world_inventory'].append({'world':ref(world),'server':world==self.server,'dedicated':ue.SystemLibrary.is_dedicated_server(world),'local_ids':[p.player_state.player_id for p in local]})
   for p in local:
    pc=p.get_controller();assert pc and pc.is_local_controller() and pc.get_world()==world
    components=p.get_components_by_class(HC);assert len(components)==1
    hud=components[0].get_editor_property('HUDWidget');prompt=p.get_editor_property('PromptWidget')
    assert hud and prompt and all(w.get_owning_player()==pc and w.is_in_viewport() and self.sub.is_widget_added(w) for w in (hud,prompt))
    self.owners.append({'id':p.player_state.player_id,'pawn':p,'pc':pc,'hud':hud,'prompt':prompt})
  assert len(self.owners)==2 and {e['id'] for e in self.owners}==ids
  candidates=[e for e in self.owners if e['pawn'].get_world()!=self.server]
  assert candidates,'A joining client owner is mandatory'
  if 'owner_id' in args:candidates=[e for e in candidates if e['id']==int(args['owner_id'])]
  assert candidates,'Requested actual joining owner ID not present'
  self.owner=sorted(candidates,key=lambda e:(ref(e['pawn'].get_world()),e['id']))[0]
  pc=self.owner['pc'];self.r.update({'owner_id':self.owner['id'],'owner_controller':ref(pc),'owner_world':ref(pc.get_world()),
   'selection':'requested PlayerState ID' if 'owner_id' in args else 'actual joining local pawn, sorted world path/PlayerState ID'})
  self.r['before']=self.snapshot(False);write(self.r)
 def snapshot(self,with_control=True):
  active=[w for w in ue.ObjectIterator(ue.UserWidget) if w.is_in_viewport()]
  owners=[]
  for e in self.owners:
   pc=e['pc'];rows={}
   for key in ('hud','prompt'):
    w=e[key];row=geometry(w);row.update({'controller':ref(w.get_owning_player()),'in_viewport':w.is_in_viewport(),
     'subsystem_widget_added':self.sub.is_widget_added(w),'active_owner_class_count':sum(a.get_class()==w.get_class() and a.get_owning_player()==pc for a in active)})
    rows[key]=row
   owners.append({'id':e['id'],'controller':ref(pc),'world':ref(pc.get_world()),
    'pixels':vec(ue.WidgetLayoutLibrary.get_viewport_size(pc)),
    'viewport':bounds(ue.WidgetLayoutLibrary.get_viewport_widget_geometry(pc)),
    'player':bounds(ue.WidgetLayoutLibrary.get_player_screen_widget_geometry(pc)),**rows})
  result={'owners':owners}
  if with_control:result['candidate']=inspect_existing(self.control,self.owner['pc'],self.sub)
  return result
 def create(self):
  bp=ue.load_asset(ASSET);assert bp and bp.get_class().get_name()=='WidgetBlueprint'
  klass=bp.generated_class();assert ref(klass)==ASSET+'.UI_Vehicle_C'
  assert not any(w.get_class()==klass and w.is_in_viewport() for w in ue.ObjectIterator(ue.UserWidget)),'A control of this template class is already attached'
  pc=self.owner['pc'];assert pc
  library=ue.load_object(None,'/Script/UMG.Default__WidgetBlueprintLibrary');assert library
  self.control=library.call_method('Create',args=(pc,klass,pc));assert self.control
  assert self.control.get_class()==klass and self.control.get_owning_player()==pc and self.control.get_world()==pc.get_world()
  self.r['control_path']=ref(self.control);write(self.r)
  assert self.control.add_to_player_screen(0),'Explicit owning AddToPlayerScreen failed'
  assert self.sub.is_widget_added(self.control) and self.control.is_in_viewport()
  self.r['fixture_actions'].append({'action':'Create explicit WorldContext=owning PC, OwningPlayer=same PC; AddToPlayerScreen(0)',
   'widget':ref(self.control),'runtime_texts_unchanged':True,'saved_asset_edited':False})
  self.r['immediate_after']=self.snapshot();self.r['status']='waiting_for_callbacks';write(self.r)
  self.deadline=time.monotonic()+5;self.handle=ue.register_slate_post_tick_callback(self.tick)
 def tick(self,delta):
  if self.finished:return
  try:
   self.callbacks+=1;sample=self.snapshot();self.r['samples'].append({'callback':self.callbacks,'snapshot':sample})
   self.r['last_after']=sample
   if self.callbacks>=8 or time.monotonic()>=self.deadline:self.finish('callback_limit' if self.callbacks>=8 else 'wall_deadline')
  except Exception:self.finish('collection_error',traceback.format_exc())
 def finish(self,reason,error=None):
  if self.finished:return
  self.finished=True
  if self.handle is not None:ue.unregister_slate_post_tick_callback(self.handle);self.handle=None
  self.r['actual_callbacks']=self.callbacks;self.r['stop_reason']=reason;self.r['elapsed_seconds']=round(time.monotonic()-self.start,6)
  self.r['control_left_attached']=bool(self.control and self.control.is_in_viewport())
  if error:self.r['error']=error
  last=self.r.get('last_after',self.r.get('immediate_after',{}));candidate=last.get('candidate',{});control=candidate.get('control',{})
  self.r['checks']={'saved_candidate_bytes_unchanged':sha(DISK)==ASSET_SHA,
   'control_owning_attachment':bool(candidate.get('in_viewport') and candidate.get('subsystem_widget_added') and candidate.get('owning_controller')==self.r['owner_controller']),
   'nonzero_control_paint':positive(control.get('paint',[])),
   'nonzero_control_cache_and_tick':positive(control.get('cache',[])) and positive(control.get('tick',[])),
   'nonzero_candidate_player_and_viewport':positive(candidate.get('player',[])) and positive(candidate.get('viewport',[])),
   'all_native_text_blocks_have_nonzero_paint':bool(candidate.get('tree')) and all(positive(w['paint']) for w in candidate.get('tree',[]) if w['class']=='/Script/UMG.TextBlock')}
  before={e['id']:e for e in self.r['before']['owners']};preserved=True
  for e in last.get('owners',[]):
   for key in ('hud','prompt'):
    old=before[e['id']][key];new=e[key]
    preserved=preserved and new['path']==old['path'] and new['controller']==old['controller'] and new['in_viewport'] and new['subsystem_widget_added'] and new['active_owner_class_count']==1
  self.r['checks']['existing_hud_prompt_identity_ownership_and_counts_preserved']=bool(last.get('owners')) and preserved
  self.r['collection_complete']=not bool(error)
  self.r['geometry_qualified']=not bool(error) and all(self.r['checks'].values())
  self.r['status']='control_geometry_qualified_awaiting_native_screenshot' if self.r['geometry_qualified'] else 'control_geometry_unqualified_awaiting_native_screenshot'
  write(self.r)

probe=None
try:
 assert Path(ue.Paths.project_dir()).resolve()==EXPECTED,'Wrong editor project'
 if action=='create':
  probe=ControlProbe();probe.create()
 else:
  r=json.loads(OUT.read_text());w,pc=find_exact_control(r);sub=ue.get_engine_subsystem(ue.GameViewportSubsystem);assert sub
  assert r.get('collection_complete') or r.get('error'),'Wait for terminal collection before read/cleanup'
  current=inspect_existing(w,pc,sub)
  if action=='read':
   r.setdefault('parent_readbacks',[]).append(current);write(r)
  else:
   w.remove_from_parent()
   r['cleanup']={'exact_recorded_widget':ref(w),'owning_controller':ref(pc),'before':current,
    'in_viewport_after':bool(w.is_in_viewport()),'subsystem_widget_added_after':bool(sub.is_widget_added(w)),
    'saved_candidate_bytes_unchanged':sha(DISK)==ASSET_SHA}
   assert not w.is_in_viewport() and not sub.is_widget_added(w),'Exact control cleanup failed'
   r['control_left_attached']=False;r['cleanup']['passed']=True;write(r)
except Exception:
 error=traceback.format_exc()
 if probe is not None:
  if probe.control and probe.control.is_in_viewport():probe.control.remove_from_parent()
  probe.finish('fixture_or_collection_error',error)
 else:
  r=json.loads(OUT.read_text()) if OUT.exists() else {'schema':1,'pie_only':True,'packages_saved':[],'rendered_pixel_acceptance':False}
  r.setdefault('operation_errors',[]).append({'action':action,'error':error});write(r)
