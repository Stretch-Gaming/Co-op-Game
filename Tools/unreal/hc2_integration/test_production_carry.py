"""Production character integration, using actual owning input and RPCs."""
import unreal as ue,json,time,math,traceback
N=ARGS['clients'];SPLIT=ARGS.get('split',False);report={'passed':False,'clients':N,'checks':[],'production_character':True,'input_path':'IA_Interact / IA_Drop -> production character -> reliable server RPC -> delivered AC_Carrying'}
state={'stage':0,'at':time.monotonic()+2,'held':None,'deadline':time.monotonic()+90}
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w))
cls=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();accls=ue.load_asset('/Game/Puzzles/Carrying/AC_Carrying').generated_class()
locals=[p for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,cls) if p.is_locally_controlled()]
pawn=next(p for p in locals if p.get_world()==server and not p.get_controller().is_primary_player()) if SPLIT else locals[0];pid=pawn.player_state.get_editor_property('PlayerId')
base=None

def target(w,name):return ue.GameplayStatics.get_all_actors_with_tag(w,'HC2_'+name)[0]
def comp(p):return p.get_component_by_class(accls)
def owner(w):return next(p for p in ue.GameplayStatics.get_all_actors_of_class(w,cls) if p.player_state.get_editor_property('PlayerId')==pid)
def inject(name,value):
 probe=ue.get_default_object(ue.load_asset('/Game/Puzzles/Test/HC2/BP_HC2InputProbe').generated_class())
 sub=ue.EnhancedInputLocalPlayerSubsystem.cast(probe.call_method('ResolveInput',args=(pawn.get_controller(),)))
 sub.inject_input_vector_for_action(ue.load_asset('/Game/Core/Input/'+name),ue.Vector(float(value),0,0),[],[])
def focus(name):
 a=target(pawn.get_world(),name)
 for w in worlds:
  for p in ue.GameplayStatics.get_all_actors_of_class(w,cls):
   p.set_actor_enable_collision(False)
   if p.player_state.get_editor_property('PlayerId')==pid:p.set_actor_location(ue.Vector(a.get_actor_location().x-210,a.get_actor_location().y,92.15),False,True)
 look=a.get_actor_location()-pawn.get_editor_property('CameraBoom').get_world_location()
 pawn.get_controller().set_control_rotation(ue.Rotator(pitch=math.degrees(math.atan2(look.z,math.hypot(look.x,look.y))),yaw=math.degrees(math.atan2(look.y,look.x))))
def step(n,delay=1):state['stage']=n;state['at']=time.monotonic()+delay

def held(name,next_stage):state['held']=name;step(next_stage,.4)
def release(next_stage):
 inject(state['held'],0);state['held']=None;step(next_stage,1)
def carrying(name):
 for w in worlds:
  a=target(w,name);p=owner(w)
  assert a.get_editor_property('CarryState')==1 and a.get_editor_property('Carrier')==p,(w,a.get_editor_property('CarryState'))
  assert comp(p).get_editor_property('CarriedItem')==a
  assert a.static_mesh_component.get_collision_enabled()==ue.CollisionEnabled.NO_COLLISION
 assert owner(server).call_method('GetCarried')==target(server,name)
def dropped(name):
 for w in worlds:
  a=target(w,name);p=owner(w)
  assert a.get_editor_property('CarryState')==0 and not a.get_editor_property('Carrier')
  assert comp(p).get_editor_property('CarriedItem') is None
  assert a.static_mesh_component.is_simulating_physics()
 assert owner(server).call_method('GetCarried') is None

def finish(ok,error=None):
 report['passed']=ok
 if error:report['error']=error
 (HERE/('production-carry-split.json' if SPLIT else f'production-carry-{N}.json')).write_text(json.dumps(report,indent=2))
 ue.unregister_slate_post_tick_callback(handle);ue.log('HC2_PRODUCTION_CARRY_'+str(N)+': '+str(ok))
def tick(dt):
 global base
 try:
  now=time.monotonic();assert now<state['deadline'],'Production carrying timeout'
  if state['held']:inject(state['held'],1)
  if now<state['at']:return
  s=state['stage']
  if s==0:
   assert len(worlds)==(2 if SPLIT else N+1) and len(locals)==N
   for w in worlds:
    for p in ue.GameplayStatics.get_all_actors_of_class(w,cls):assert len(p.get_components_by_class(accls))==1,p.get_path_name()
   base={w.get_path_name():owner(w).get_component_by_class(ue.CharacterMovementComponent).get_editor_property('max_walk_speed') for w in worlds}
   report['checks'].append({'single_replicated_runtime_component_every_pawn':True})
   focus('Crate');step(1,2)
  elif s==1:
   if pawn.get_editor_property('FocusedTarget')!=target(pawn.get_world(),'Crate'):
    focus('Crate');state['at']=now+1;return
   held('IA_Interact',2)
  elif s==2:release(3)
  elif s==3:
   carrying('Crate');report['checks'].append({'client_pickup_production_hook':True,'server_GetCarried_forwarding':True});held('IA_Drop',4)
  elif s==4:release(5)
  elif s==5:
   dropped('Crate');report['checks'].append({'client_G_reliable_server_drop':True});focus('Crate');step(6,2)
  elif s==6:held('IA_Interact',7)
  elif s==7:release(8)
  elif s==8:
   carrying('Crate');report['checks'].append({'production_repickup':True});held('IA_Drop',9)
  elif s==9:release(10)
  elif s==10:focus('Heavy');step(11,2)
  elif s==11:held('IA_Interact',12)
  elif s==12:release(13)
  elif s==13:
   carrying('Heavy')
   for w in worlds:assert abs(owner(w).get_component_by_class(ue.CharacterMovementComponent).get_editor_property('max_walk_speed')-base[w.get_path_name()]*.5)<.01
   report['checks'].append({'heavy_speed_uses_production_baseline_on_server_and_clients':True});held('IA_Drop',14)
  elif s==14:release(15)
  elif s==15:
   dropped('Heavy')
   for w in worlds:assert abs(owner(w).get_component_by_class(ue.CharacterMovementComponent).get_editor_property('max_walk_speed')-base[w.get_path_name()])<.01
   report['checks'].append({'drop_restores_baseline_speed':True});finish(True)
 except Exception:finish(False,traceback.format_exc())
handle=ue.register_slate_post_tick_callback(tick)
