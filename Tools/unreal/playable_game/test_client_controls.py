import time,json,traceback
import unreal as ue
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w))
C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();V=ue.load_asset('/Game/Player/AC_PlayerView').generated_class();library=ue.load_object(None,'/Script/Engine.Default__SubsystemBlueprintLibrary')
locals_=sorted([p for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,C) if p.is_locally_controlled()],key=lambda p:p.player_state.player_id)
assert len(locals_)==2
pid=locals_[0].player_state.player_id
state={'start':time.monotonic(),'phase':0,'checks':[]}
report=QUEUE/'client-controls.json'
def owned(world):return next(p for p in ue.GameplayStatics.get_all_actors_of_class(world,C) if p.player_state.player_id==pid)
def inject(name,value):
 subsystem=library.call_method('GetLocalPlayerSubSystemFromPlayerController',args=(locals_[0].get_controller(),ue.EnhancedInputLocalPlayerSubsystem.static_class()))
 subsystem.inject_input_vector_for_action(ue.load_asset('/Game/Core/Input/'+name),ue.Vector(value,0,0),[],[])
def finish(passed,error=None):
 ue.unregister_slate_post_tick_callback(state['handle']);report.write_text(json.dumps({'passed':passed,'error':error,'checks':state['checks']},indent=2))
def tick(delta):
 try:
  elapsed=time.monotonic()-state['start'];phase=state['phase']
  if phase==0:
   inject('IA_ToggleView',1 if elapsed<.2 else 0);inject('IA_Headlamp',1 if elapsed<.2 else 0)
   if elapsed>1:
    for w in worlds:
     view=owned(w).get_component_by_class(V);assert view.get_editor_property('ViewMode')==1;assert view.get_editor_property('bHeadlampOn')
    state['checks'].append('client view and headlamp input reached server and every peer');state['phase']=1;state['start']=time.monotonic()
  elif phase==1:
   inject('IA_Brace',1)
   if elapsed>1:
    for w in worlds:assert owned(w).get_editor_property('bBraced');assert owned(w).character_movement.max_walk_speed==0
    state['checks'].append('client brace reached server and peers');state['phase']=2;state['start']=time.monotonic()
  elif phase==2:
   inject('IA_Brace',0)
   if elapsed>1:
    for w in worlds:assert not owned(w).get_editor_property('bBraced');assert owned(w).character_movement.max_walk_speed>0
    state['checks'].append('client release restores walking');finish(True)
 except Exception:finish(False,traceback.format_exc())
state['handle']=ue.register_slate_post_tick_callback(tick)
RESULT={'queued':'client-controls.json'}
