"""Native F5-action setup for host split; no gameplay AddLocalPlayer call."""
import json,time,traceback
import unreal as ue
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w))
assert not ue.SystemLibrary.is_dedicated_server(server)
C=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class()
pawns=list(ue.GameplayStatics.get_all_actors_of_class(server,C));assert len(pawns)==3
local=[p for p in pawns if p.is_locally_controlled()];assert len(local)==1
owner=next(iter(local));controller=owner.get_controller();assert controller.is_local_controller()
library=ue.load_object(None,'/Script/Engine.Default__SubsystemBlueprintLibrary')
sub=library.call_method('GetLocalPlayerSubSystemFromPlayerController',args=(controller,ue.EnhancedInputLocalPlayerSubsystem.static_class()));assert sub
action=ue.load_asset('/Game/Core/Input/IA_AddLocalPlayer');assert action
state={'start':time.monotonic()};report=QUEUE/'qa-add-host-split.json'
def finish(passed,error=None):
 sub.inject_input_vector_for_action(action,ue.Vector(),[],[])
 ue.unregister_slate_post_tick_callback(state['handle'])
 report.write_text(json.dumps({'passed':passed,'error':error,'method':'Primary owning subsystem IA_AddLocalPlayer(F5) input; no gameplay function shortcut','world':server.get_path_name()},indent=2))
def tick(delta):
 try:
  elapsed=time.monotonic()-state['start'];assert elapsed<8,'F5 did not finish host split setup'
  sub.inject_input_vector_for_action(action,ue.Vector(1 if elapsed<.15 else 0,0,0),[],[])
  if elapsed>1.5:
   current=list(ue.GameplayStatics.get_all_actors_of_class(server,C))
   assert len(current)==4 and sum(p.is_locally_controlled() for p in current)==2
   finish(True)
 except Exception:finish(False,traceback.format_exc())
state['handle']=ue.register_slate_post_tick_callback(tick);RESULT={'queued':str(report),'runtime_acceptance_pending':True}
