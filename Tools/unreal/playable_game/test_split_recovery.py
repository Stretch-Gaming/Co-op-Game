import time,json,traceback
import unreal as ue
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w));C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();V=ue.load_asset('/Game/Player/AC_PlayerView').generated_class();H=ue.load_asset('/Game/Hazards/AC_Health').generated_class();library=ue.load_object(None,'/Script/Engine.Default__SubsystemBlueprintLibrary')
primary=next(pc for pc in ue.ObjectIterator(ue.PlayerController) if pc.get_world()==server and pc.is_local_controller() and pc.is_primary_player());sub=library.call_method('GetLocalPlayerSubSystemFromPlayerController',args=(primary,ue.EnhancedInputLocalPlayerSubsystem.static_class()))
state={'phase':0,'start':time.monotonic(),'checks':[],'deadline':time.monotonic()+30};report=QUEUE/'split-keyboard-recovery.json'
def players():return list(ue.GameplayStatics.get_all_actors_of_class(server,C))
if ARGS.get('resume_revive'):
 state['phase']=4;state['p1']=primary.get_controlled_pawn();state['p2']=next(p for p in players() if p!=state['p1']);state['checks']=json.loads(report.read_text())['checks']

def inject(name,value):sub.inject_input_vector_for_action(ue.load_asset('/Game/Core/Input/'+name),ue.Vector(value,0,0),[],[])
def transition(phase):state['phase']=phase;state['start']=time.monotonic()
def finish(passed,error=None):
 ue.unregister_slate_post_tick_callback(state['handle']);report.write_text(json.dumps({'passed':passed,'error':error,'checks':state['checks'],'phase':state['phase']},indent=2))
def tick(delta):
 try:
  elapsed=time.monotonic()-state['start'];phase=state['phase']
  assert time.monotonic()<state['deadline'],'test exceeded its deadline'
  if phase==0:
   inject('IA_AddLocalPlayer',1 if elapsed<.2 else 0)
   if elapsed>1:
    ps=players();assert len(ps)==2;state['p1']=primary.get_controlled_pawn();state['p2']=next(p for p in ps if p!=state['p1']);state['secondary_start']=state['p2'].get_actor_location();state['primary_start']=state['p1'].get_actor_location()
    for p in ps:
     assert p.is_locally_controlled() and p.get_editor_property('InputReady');widget=p.get_editor_property('PromptWidget');assert widget and widget.get_owning_player()==p.get_controller()
    state['checks'].append('F5 input adds a second local player with independent prompt and input');transition(1)
  elif phase==1:
   inject('IA_P2Forward',1 if elapsed<.6 else 0)
   if elapsed>1:
    assert (state['p2'].get_actor_location()-state['secondary_start']).length()>50,'second keyboard movement did not move player two'
    assert (state['p1'].get_actor_location()-state['primary_start']).length()<5,'player one moved with player two controls'
    state['checks'].append('arrow input moves only player two');transition(2)
  elif phase==2:
   inject('IA_P2View',1 if elapsed<.2 else 0);inject('IA_P2Lamp',1 if elapsed<.2 else 0);inject('IA_P2Brace',1)
   if elapsed>1:
    p1,p2=state['p1'],state['p2'];assert p2.get_component_by_class(V).get_editor_property('ViewMode')==1;assert p2.get_component_by_class(V).get_editor_property('bHeadlampOn');assert p2.get_editor_property('bBraced');assert not p1.get_editor_property('bBraced');assert p1.get_component_by_class(V).get_editor_property('ViewMode')==0
    state['checks'].append('second-player view, light and brace stay independent');transition(3)
  elif phase==3:
   inject('IA_P2Brace',0)
   if elapsed>1:
    p1,p2=state['p1'],state['p2'];assert not p2.get_editor_property('bBraced');ue.GameplayStatics.apply_damage(p1,200,None,p2,None);transition(4)
  elif phase==4 and elapsed>1:
   p1,p2=state['p1'],state['p2'];health=p1.get_component_by_class(H);assert health.get_editor_property('bDowned');assert p1.get_editor_property('InteractionBlocked')
   proxy=p1.get_editor_property('ReviveTarget');assert proxy and not proxy.get_editor_property('hidden');state['proxy']=proxy
   pos=proxy.get_actor_location();p2.set_actor_location(ue.Vector(pos.x+210,pos.y,92.15),False,True)
   # Return player two to first person before the interaction trace.
   inject('IA_P2View',1);transition(5)
  elif phase==5:
   inject('IA_P2View',0);p2=state['p2'];p2.get_controller().set_control_rotation(ue.MathLibrary.find_look_at_rotation(p2.get_component_by_class(ue.CameraComponent).get_world_location(),state['proxy'].get_actor_location()))
   if elapsed>1:
    assert p2.get_editor_property('FocusedTarget')==state['proxy'],'revive target was not acquired by the normal camera trace';transition(6)
  elif phase==6:
   inject('IA_P2Use',1 if elapsed<3.5 else 0)
   if elapsed>4:
    health=state['p1'].get_component_by_class(H);assert not health.get_editor_property('bDowned');assert health.get_editor_property('Health')==50;assert not state['p1'].get_editor_property('InteractionBlocked')
    state['checks'].append('normal hold interaction revives the teammate at half health');finish(True)
 except Exception:finish(False,traceback.format_exc())
state['handle']=ue.register_slate_post_tick_callback(tick);RESULT={'queued':'split-keyboard-recovery.json'}
