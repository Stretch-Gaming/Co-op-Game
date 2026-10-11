"""Real owning Enhanced Input injection; no server-side gameplay shortcut."""
import time,json,traceback
import unreal as ue
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True))
assert worlds,'Start Play As Client PIE with the intended 2/3/4 player count first'
C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
T=ue.load_asset('/Game/Player/AC_Traversal').generated_class()
U=ue.load_asset('/Game/Player/Tools/AC_Tools').generated_class()
locals_=sorted([p for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,C) if p.is_locally_controlled()],key=lambda p:p.player_state.player_id)
assert len(locals_)>=2,'This gate must observe at least two independently owned local views'
server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w))
ids=[p.player_state.player_id for p in ue.GameplayStatics.get_all_actors_of_class(server,C)]
assert len(ids) in (2,3,4)
library=ue.load_object(None,'/Script/Engine.Default__SubsystemBlueprintLibrary')
state={'start':time.monotonic(),'phase':0,'local_index':0,'checks':[]}
report=QUEUE/('pg-client-inputs-'+str(len(ids))+'.json')
def owned(world,pid):
 matches=[p for p in ue.GameplayStatics.get_all_actors_of_class(world,C) if p.player_state and p.player_state.player_id==pid]
 assert len(matches)==1,(world.get_name(),pid,len(matches))
 return matches[0]
def inject(pawn,name,value):
 subsystem=library.call_method('GetLocalPlayerSubSystemFromPlayerController',args=(pawn.get_controller(),ue.EnhancedInputLocalPlayerSubsystem.static_class()))
 assert subsystem
 subsystem.inject_input_vector_for_action(ue.load_asset('/Game/Core/Input/'+name),ue.Vector(value,0,0),[],[])
def finish(passed,error=None):
 ue.unregister_slate_post_tick_callback(state['handle'])
 report.write_text(json.dumps({'passed':passed,'error':error,'player_count':len(ids),'local_views':len(locals_),'checks':state['checks'],'scope':'input ownership and replication only; route/taking/death/chase gates separate'},indent=2))
def tick(delta):
 try:
  pawn=locals_[state['local_index']];pid=pawn.player_state.player_id
  elapsed=time.monotonic()-state['start'];phase=state['phase']
  if phase==0:
   state['flares']={other:owned(server,other).get_component_by_class(U).get_editor_property('FlaresLeft') for other in ids}
   assert state['flares'][pid]>0,'Restock before test; player must be alive and empty handed'
   state['phase']=1;state['start']=time.monotonic()
  elif phase==1:
   inject(pawn,'IA_Sprint',1)
   if elapsed>1:
    for world in worlds:
     traversal=owned(world,pid).get_component_by_class(T)
     assert traversal.get_editor_property('bSprinting')
     assert owned(world,pid).character_movement.max_walk_speed>=790
     for other in ids:
      if other!=pid:assert not owned(world,other).get_component_by_class(T).get_editor_property('bSprinting')
    state['checks'].append({'owner':pid,'check':'held sprint reaches server/peers; all other players stay walking'})
    state['phase']=2;state['start']=time.monotonic()
  elif phase==2:
   inject(pawn,'IA_Sprint',0)
   if elapsed>1:
    for world in worlds:assert not owned(world,pid).get_component_by_class(T).get_editor_property('bSprinting')
    state['checks'].append({'owner':pid,'check':'release stops sprint on server/peers'})
    state['phase']=3;state['start']=time.monotonic()
  elif phase==3:
   inject(pawn,'IA_ThrowFlare',1 if elapsed<.15 else 0)
   if elapsed>1:
    for world in worlds:
     assert owned(world,pid).get_component_by_class(U).get_editor_property('FlaresLeft')==state['flares'][pid]-1
     for other in ids:
      if other!=pid:assert owned(world,other).get_component_by_class(U).get_editor_property('FlaresLeft')==state['flares'][other]
    state['checks'].append({'owner':pid,'check':'own flare decrements exactly once on server/peers; others retain stock'})
    state['local_index']+=1
    if state['local_index']==len(locals_):finish(True)
    else:state['phase']=0;state['start']=time.monotonic()
 except Exception:finish(False,traceback.format_exc())
state['handle']=ue.register_slate_post_tick_callback(tick)
RESULT={'queued':str(report),'acceptance_pending':True}
