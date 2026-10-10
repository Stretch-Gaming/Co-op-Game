import json,time,math,traceback,unreal as ue
from editor_toolset.toolsets.object import ObjectTools
report={'passed':False,'fixture_only':True,'actual_travel_tested':False,'input_path':'owning Enhanced Input action injection; no Python RPC calls','checks':[],'started_at':str(__import__('datetime').datetime.now())}
count=ARGS.get('clients',2);hostmode=ARGS.get('host',False)
state={'stage':0,'at':time.monotonic()+3,'deadline':time.monotonic()+160,'held':[]};second=None;late=None;oldwidgets={}
coordcls=ue.load_asset('/Game/Puzzles/Run/BP_RunCoordinator').generated_class();exitcls=ue.load_asset('/Game/Puzzles/BP_MapExit').generated_class();pccls=ue.load_asset('/Game/Puzzles/Test/HC_RunEnding/BP_RunEndingFixturePC').generated_class();resultscls=ue.load_asset('/Game/Puzzles/UI/Results/AC_RunResults').generated_class()
probe=ue.get_default_object(ue.load_asset('/Game/Puzzles/Test/HC2/BP_HC2InputProbe').generated_class());action=ue.load_asset('/Game/Puzzles/Test/HC_RunEnding/IA_FixtureRestart')

def worlds():return list(ue.EditorLevelLibrary.get_pie_worlds(True))
def server():return next(w for w in worlds() if ue.GameplayStatics.get_game_mode(w))
def coordinator(w=None):return ue.GameplayStatics.get_all_actors_of_class(w or server(),coordcls)[0]
def owners():return [pc for w in worlds() for pc in ue.GameplayStatics.get_all_actors_of_class(w,pccls) if pc.is_local_controller()]
def states():return list(ue.GameplayStatics.get_game_state(server()).player_array)
def calls():return ue.GameplayStatics.get_game_mode(server()).get_editor_property('FixtureCompleteCalls')
def prop(a,n):return a.get_editor_property(n)
def move(ps,inside):
 sid=ps.get_editor_property('PlayerId')
 for w in worlds():
  for pawn in ue.GameplayStatics.get_all_actors_of_class(w,ue.Pawn):
   if pawn.player_state and pawn.player_state.get_editor_property('PlayerId')==sid:
    if isinstance(pawn,ue.Character):pawn.get_component_by_class(ue.CharacterMovementComponent).disable_movement()
    pawn.set_actor_enable_collision(False);pawn.set_actor_location(ue.Vector(1200,0,100) if inside else ue.Vector(0,600,100),False,True)

def no_results():
 assert all(not prop(pc.get_component_by_class(resultscls),'ResultsWidget') for pc in owners())
def snapshot():
 return {'worlds':[{'world':w.get_path_name(),'roster':len(ue.GameplayStatics.get_game_state(w).player_array),'coordinators':[{'path':a.get_path_name(),'committed':prop(a,'SnapshotCommitted'),'results_active':prop(a,'ResultsActive'),'restart':prop(a,'RestartInProgress'),'collected':prop(a,'CapturedCollected'),'available':prop(a,'CapturedAvailable')} for a in ue.GameplayStatics.get_all_actors_of_class(w,coordcls)]} for w in worlds()],'complete_calls':calls()}
def step(n,delay=1):state['stage']=n;state['at']=time.monotonic()+delay
def inject(pc,val):
 sub=ue.EnhancedInputLocalPlayerSubsystem.cast(probe.call_method('ResolveInput',args=(pc,)));assert sub;sub.inject_input_vector_for_action(action,ue.Vector(val,0,0),[],[])
def press(pc):state['held']=[pc];state['at']=time.monotonic()+.35
def release():
 for pc in state['held']:inject(pc,0)
 state['held']=[]
def widgets():
 out={}
 for pc in owners():
  component=pc.get_component_by_class(resultscls);assert component
  widget=prop(component,'ResultsWidget');assert widget and widget.get_owning_player()==pc
  assert prop(widget,'Coordinator')==coordinator(pc.get_world())
  assert pc.get_controlled_pawn().get_editor_property('InputReady')
  hud=pc.get_controlled_pawn().get_component_by_class(ue.load_asset('/Game/Puzzles/UI/HCA3/AC_HCA3HUD').generated_class()).get_editor_property('HUDWidget');assert hud and hud.get_owning_player()==pc
  out[pc.get_path_name()]=widget.get_path_name()
 assert len(set(out.values()))==len(out)
 return out

def spawn_restore():
 global oldwidgets
 for exit in ue.GameplayStatics.get_all_actors_of_class(server(),exitcls):exit.call_method('StopExit')
 coordinator().destroy_actor()
 new=ue.GameplayStatics.get_game_mode(server()).call_method('FixtureSpawnCoordinator')
 assert new.call_method('RestoreResults')
 assert not new.call_method('RestoreResults'),'restore must be idempotent'
 return new

def finish(ok,error=None):
 release();report['passed']=ok;report['ended_at']=str(__import__('datetime').datetime.now());report['final']=snapshot()
 if error:report['error']=error
 (HERE/('host-split.json' if hostmode else f'clients-{count}.json')).write_text(json.dumps(report,indent=2));ue.unregister_slate_post_tick_callback(handle);ue.log('HC_RUN_ENDING_ACCEPTANCE: '+str(ok))

def tick(dt):
 global second,late,oldwidgets
 try:
  now=time.monotonic();assert now<state['deadline'],'timeout'
  for pc in state['held']:inject(pc,1)
  if now<state['at']:return
  s=state['stage'];co=coordinator() if s<21 else None;roster=states()
  if s==0:
   assert len(roster)==count,(len(roster),count);no_results();assert calls()==0
   ue.GameplayStatics.get_game_mode(server()).call_method('AddRelics',args=(7,))
   for ps in roster[:-1]:move(ps,True)
   step(1,2)
  elif s==1:
   assert calls()==0 and not prop(co,'SnapshotCommitted');exits=ue.GameplayStatics.get_all_actors_of_class(server(),exitcls)
   assert all(prop(ex,'RequiredPlayers')==count and prop(ex,'ReadyPlayers')==count-1 for ex in exits)
   report['checks'].append({'one_missing_blocks':True,'required':count,'ready':count-1})
   move(roster[0],False);move(roster[-1],True);step(2,2)
  elif s==2:
   assert calls()==0;report['checks'].append({'departure_cancels_readiness':True})
   if hostmode:
    second=ue.GameplayStatics.create_player(server(),-1,True);assert second;step(3,3)
   else:step(5)
  elif s==3:
   assert len(roster)==count+1 and calls()==0;report['checks'].append({'late_host_local_must_enter':True,'distinct_split_state':str(second.player_state.get_path_name())})
   ue.GameplayStatics.remove_player(second,True);second=None;step(4,3)
  elif s==4:
   assert len(roster)==count and calls()==0;report['checks'].append({'disconnect_removes_required_state':True});step(5)
  elif s==5:
   ps=roster[0];pc=ps.get_pawn().get_controller();state['pawnless_pc']=pc;state['pawnless_pawn']=ps.get_pawn();pc.un_possess();step(6,2)
  elif s==6:
   assert calls()==0;report['checks'].append({'pawnless_connected_player_blocks':True})
   state['pawnless_pc'].possess(state['pawnless_pawn']);move(states()[0],True);step(7,2)
  elif s==7:
   assert calls()==1 and prop(co,'SnapshotCommitted') and not prop(co,'ResultsActive');no_results()
   gi=ue.GameplayStatics.get_game_instance(server());assert gi.get_editor_property('RelicsCollected')==7 and gi.get_editor_property('RelicsAvailable')==19
   # Eligible owned fixture relic supplies the authoritative available denominator19.
   assert prop(co,'CapturedCollected')==7 and prop(co,'CapturedAvailable')==19
   assert not co.call_method('TryCommitExtraction') and calls()==1
   report['checks'].append({'all_distinct_possessed_pawns_commit_once':True,'two_exit_volumes':True,'captured':{'collected':prop(co,'CapturedCollected'),'available':prop(co,'CapturedAvailable')},'duplicate_commit_rejected':True,'outbound_results_hidden':True})
   for pc in owners():
    assert not co.call_method('RequestRestart',args=(pc,))
   report['checks'].append({'restart_rejected_until_restored_results':True});spawn_restore();step(8,3)
  elif s==8:
   oldwidgets=widgets();
   for w in worlds():
    gs=ue.GameplayStatics.get_game_state(w);assert gs.get_editor_property('RelicsCollected')==7 and gs.get_editor_property('RelicsAvailable')==19
    cc=coordinator(w);assert prop(cc,'CapturedCollected')==7 and prop(cc,'CapturedAvailable')==19
   report['checks'].append({'restored_results_owning_widgets':oldwidgets,'late_snapshot_replicates':True,'restore_idempotent':True})
   remote=next(pc for pc in owners() if pc.get_world()!=server());press(remote);state['testedpc']=remote;state['stage']=9
  elif s==9:release();step(10,1)
  elif s==10:
   assert prop(state['testedpc'],'RestartInputEvents')==1 and calls()==1 and not prop(co,'RestartInProgress');report['checks'].append({'remote_actual_input_event_rejected':True})
   if hostmode:
    second=ue.GameplayStatics.create_player(server(),-1,True);step(11,3)
   else:step(20)
  elif s==11:
   view=widgets();
   if not state.get('view_recorded'):
    host=next(pc for pc in owners() if pc.get_world()==server() and pc.is_primary_player())
    try:ue.SystemLibrary.execute_console_command(server(),'Shot SHOWUI FILENAME="'+str(HERE/'host-split-results.png').replace(chr(92),'/')+'"',host)
    except Exception:(HERE/'capture-error.json').write_text(json.dumps({'error':traceback.format_exc(),'gameplay_gate_continues':True},indent=2))
    state['view_recorded']=True;(HERE/'results-view-ready.json').write_text(json.dumps({'owning_widgets':view,'stage':'before restart','time':str(__import__('datetime').datetime.now())},indent=2));state['at']=now+8;return
   press(second);state['stage']=12
  elif s==12:release();step(13,1)
  elif s==13:
   assert prop(second,'RestartInputEvents')==1 and calls()==1 and not prop(co,'RestartInProgress');report['checks'].append({'second_local_actual_input_event_rejected':True})
   host=next(pc for pc in owners() if pc.get_world()==server() and pc.is_primary_player());press(host);state['testedpc']=host;state['stage']=14
  elif s==14:release();step(15,2)
  elif s==15:
   assert prop(state['testedpc'],'RestartInputEvents')==1 and calls()==2 and prop(co,'RestartInProgress');gi=ue.GameplayStatics.get_game_instance(server());assert gi.get_editor_property('RelicsCollected')==0 and gi.get_editor_property('RelicsAvailable')==0
   report['checks'].append({'primary_host_actual_input_accepted_once':True,'fresh_run_gi_totals_zero':True,'restart_visible_replicated':True})
   press(state['testedpc']);state['stage']=16
  elif s==16:release();step(17)
  elif s==17:
   assert calls()==2;report['checks'].append({'duplicate_restart_input_rejected':True});step(20)
  elif s==20:
   current=widgets();assert all(current.get(pc)==widget for pc,widget in oldwidgets.items())
   assert len(set(current.values()))==len(current)
   coordinator().destroy_actor();step(21,2)
  elif s==21:
   no_results();assert all(not prop(pc.get_component_by_class(resultscls),'Coordinator') for pc in owners());report['checks'].append({'destroyed_coordinator_clears_only_results':True});finish(True)
 except Exception:finish(False,traceback.format_exc())
handle=ue.register_slate_post_tick_callback(tick)
