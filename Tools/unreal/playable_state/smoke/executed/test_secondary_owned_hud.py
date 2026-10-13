"""Fresh four-player host split: real owning Q/F/E, disclosed lethal fixture only."""
import hashlib,json,sys,time,traceback
from pathlib import Path
import unreal as ue
ROOT=Path('/Volumes/CoopBuild/Repositories/Co-op-Game-primary');D=Path('/tmp/coop-runtime');sys.path.insert(0,str(ROOT))
from Tools.unreal.playable_state.ghosts.ghost_runtime_support import Harness
h=Harness({'players':4,'profile':'host_split','timeout':30},'owned-hud-secondary');h.report=D/'owned-hud-secondary.json'
assert h.round()['index']==0 and h.round()['phase']==0
host=[i for i,p in h.locals.items() if p.get_world()==h.server];sec=next(i for i in host if not h.locals[i].get_controller().is_primary_player());primary=next(i for i in host if i!=sec)
HUDCLASS=ue.load_asset('/Game/Puzzles/UI/HCA3/AC_HCA3HUD').generated_class()
def hud(i):return h.locals[i].get_component_by_class(HUDCLASS).get_editor_property('HUDWidget')
def stock(i):return int(h.prop(h.pawn(h.server,i),'tools','FlaresLeft'))
def view(i):return h.locals[i].get_controller().get_view_target()
def row(i):
 w=hud(i);return {'owner_id':i,'owner_controller':w.get_owning_player().get_path_name(),'hud':w.get_path_name(),'flares':w.get_editor_property('DisplayedFlares'),'dead':w.get_editor_property('DisplayedDead'),'tools':w.get_editor_property('DisplayTools'),'spectator':w.get_editor_property('DisplaySpectator'),'view_target':view(i).get_path_name() if view(i) else None}
state={'stage':'throw','pressed_at':None,'baseline_stocks':{i:stock(i) for i in h.ids},'baseline_primary_view':view(primary).get_path_name(),'baseline_huds':{i:hud(i).get_path_name() for i in h.ids},'samples':[]};assert state['baseline_stocks'][sec]>=1
h.locals[sec].get_controller().set_control_rotation(ue.Rotator(pitch=-90,yaw=0));h.fixtures.append({'kind':'secondary host aim down','owner_id':sec})
h.hold(sec,'flare')
old_finish=h.finish
def finish(passed,error=None):
 result=old_finish(passed,error)
 if result:
  result.update({'secondary_id':sec,'primary_id':primary,'secondary_is_primary':False,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'state':state,'hud_rendered_pixel_acceptance':False,'limits':'Synthetic owning Enhanced Input, lethal damage and aim fixtures; no devices/fullroute/travel/physical E acceptance.'});h.report.write_text(json.dumps(result,indent=2))
h.finish=finish

def tick(_delta):
 now=time.monotonic();stage=state['stage']
 if stage in ('throw','lamp','cycle','dead_inputs'):
  if state['pressed_at'] is None:state['pressed_at']=now
  if now-state['pressed_at']>.2:
   roles={'throw':['flare'],'lamp':['lamp'],'cycle':['interact'],'dead_inputs':['flare','move']}[stage]
   for role in roles:h.release(sec,role)
   state['released_at']=now;state['stage']=stage+'_settle'
  return
 if now-state['released_at']<.7:return
 if stage=='throw_settle':
  assert stock(sec)==state['baseline_stocks'][sec]-1 and all(stock(i)==state['baseline_stocks'][i] for i in h.ids if i!=sec)
  for world in h.worlds:
   assert h.prop(h.pawn(world,sec),'tools','FlaresLeft')==stock(sec)
  assert all(hud(i).get_editor_property('DisplayedFlares')==stock(i) for i in h.ids)
  state['samples'].append({'phase':'owning_Q','owners':[row(i) for i in host]});h.check('Secondary Q spends only its stock; both host HUDs display their own counters')
  state['stage']='lamp';state['pressed_at']=None;h.hold(sec,'lamp')
 elif stage=='lamp_settle':
  assert h.prop(h.pawn(h.server,sec),'view','bHeadlampOn') and all(not h.prop(h.pawn(h.server,i),'view','bHeadlampOn') for i in h.ids if i!=sec)
  assert hud(sec).get_editor_property('DisplayTools').startswith('LAMP ON') and hud(primary).get_editor_property('DisplayTools').startswith('LAMP OFF')
  assert view(primary).get_path_name()==state['baseline_primary_view'];h.check('Secondary F affects only its lamp and HUD; primary camera remains owned')
  dead=h.pawn(h.server,sec);ue.GameplayStatics.apply_damage(dead,1000,None,None,None);h.fixtures.append({'kind':'server lethal ApplyDamage only on secondary host','owner_id':sec})
  assert h.prop(dead,'health','bDead');state['stage']='death_settle';state['released_at']=now
 elif stage=='death_settle':
  target=view(sec);assert target and target!=h.locals[sec] and target.player_state.player_id!=sec
  assert not h.prop(h.pawn(h.server,target.player_state.player_id),'health','bDead')
  assert hud(sec).get_editor_property('DisplayedDead') and hud(sec).get_editor_property('DisplayedFlares')==stock(sec)
  assert stock(sec)!=stock(target.player_state.player_id),'Own-vs-spectated stock must differ for proof'
  assert view(primary).get_path_name()==state['baseline_primary_view'];state['before_cycle']=target.player_state.player_id;h.check('Dead secondary spectates living player while HUD retains its own lower stock')
  state['stage']='cycle';state['pressed_at']=None;h.hold(sec,'interact')
 elif stage=='cycle_settle':
  target=view(sec);assert target and target.player_state.player_id not in (sec,state['before_cycle'])
  assert not h.prop(h.pawn(h.server,target.player_state.player_id),'health','bDead')
  assert 'watching P' in hud(sec).get_editor_property('DisplaySpectator') and hud(sec).get_editor_property('DisplayedFlares')==stock(sec)
  assert view(primary).get_path_name()==state['baseline_primary_view'];state['after_cycle']=target.player_state.player_id;state['dead_location']=list(h.locals[sec].get_actor_location().to_tuple());h.check('Actual secondary E cycles a living target; HUD owner and primary view remain unchanged')
  state['stage']='dead_inputs';state['pressed_at']=None;h.hold(sec,'flare');h.hold(sec,'move',ue.Vector(1,0,0))
 elif stage=='dead_inputs_settle':
  assert stock(sec)==state['baseline_stocks'][sec]-1
  delta=h.locals[sec].get_actor_location()-ue.Vector(*state['dead_location']);assert delta.length()<5,('Dead pawn moved',delta)
  assert all(hud(i).get_path_name()==state['baseline_huds'][i] and hud(i).get_owning_player()==h.locals[i].get_controller() for i in h.ids)
  assert hud(sec).get_editor_property('DisplayedDead') and hud(sec).get_editor_property('DisplayedFlares')==stock(sec)
  state['samples'].append({'phase':'dead_secondary_after_E_and_blocked_inputs','owners':[row(i) for i in host]});h.check('Dead secondary movement/Q are blocked; four original HUD identities and own data persist');h.finish(True)
 else:raise AssertionError(stage)
h.register(tick)
