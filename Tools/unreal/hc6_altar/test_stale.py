import pathlib,json,time,traceback,unreal as ue
ROOT=pathlib.Path(__file__).resolve().parents[3];HERE=pathlib.Path(__file__).parent
ws=list(ue.EditorLevelLibrary.get_pie_worlds(True));server=next(w for w in ws if ue.GameplayStatics.get_game_mode(w));C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();AC=ue.load_asset('/Game/Puzzles/Carrying/AC_Carrying').generated_class()
client=next(w for w in ws if w!=server and any(p.is_locally_controlled() and p.get_component_by_class(AC).get_editor_property('CarriedItem') for p in ue.GameplayStatics.get_all_actors_of_class(w,C)))
pawn=next(p for p in ue.GameplayStatics.get_all_actors_of_class(client,C) if p.is_locally_controlled());pid=pawn.player_state.player_id;sp=next(p for p in ue.GameplayStatics.get_all_actors_of_class(server,C) if p.player_state.player_id==pid)
a=ue.GameplayStatics.get_all_actors_with_tag(server,'Altar')[0];key=sp.call_method('GetCarried');assert key
report={'passed':False,'before_clear_count':a.get_editor_property('ClearCallCount'),'destroyed_carried_key':key.get_path_name()};state={'stage':0,'at':time.monotonic()+1,'frames':0,'deadline':time.monotonic()+25}
probe=ue.get_default_object(ue.load_asset('/Game/Puzzles/Test/HC6_Altar/BP_HC6InputProbe').generated_class());sub=ue.EnhancedInputLocalPlayerSubsystem.cast(probe.call_method('ResolveInput',args=(pawn.get_controller(),)))
def inject(name,v):sub.inject_input_vector_for_action(ue.load_asset('/Game/Core/Input/'+name),ue.Vector(v,0,0),[],[])
def aim():
 ca=ue.GameplayStatics.get_all_actors_with_tag(client,'Altar')[0];dest=ca.get_actor_location();dest.z+=50
 pawn.get_component_by_class(ue.SpringArmComponent).target_arm_length=0;pawn.get_controller().set_control_rotation(ue.MathLibrary.find_look_at_rotation(pawn.get_component_by_class(ue.CameraComponent).get_world_location(),dest))
def finish(ok,error=None):
 report['passed']=ok
 if error:report['error']=error
 HERE.joinpath('stale-key-rejection.json').write_text(json.dumps(report,indent=2));ue.unregister_slate_post_tick_callback(handle)
def tick(dt):
 try:
  now=time.monotonic();assert now<state['deadline'],'Stale reference test timeout'
  if now<state['at']:return
  if state['stage']==0:
   key.destroy_actor()
   loc=a.get_actor_location()
   for w in ws:
    for p in ue.GameplayStatics.get_all_actors_of_class(w,C):
     if p.player_state and p.player_state.player_id==pid:p.set_actor_location(ue.Vector(loc.x-210,loc.y,92),False,True)
   aim();state.update(stage=1,at=now+1)
  elif state['stage']==1:
   aim()
   if state['frames']==0 and pawn.get_editor_property('FocusedTarget')!=ue.GameplayStatics.get_all_actors_with_tag(client,'Altar')[0]:return
   inject('IA_Interact',1);state['frames']+=1
   if state['frames']>=4:inject('IA_Interact',0);state.update(stage=2,at=now+1)
  elif state['stage']==2:
   assert not a.call_method('CanAccept',args=(sp,)) and not a.call_method('CanAccept',args=(None,))
   assert not a.get_editor_property('Completed') and a.get_editor_property('ClearCallCount')==report['before_clear_count']
   report['native_stale_key_and_invalid_instigator_rejected']=True;finish(True)
 except Exception:finish(False,traceback.format_exc())
handle=ue.register_slate_post_tick_callback(tick)
RESULT={'started':'stale carried key'}

