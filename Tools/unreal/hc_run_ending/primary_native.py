"""Primary independent native fixture verification; no package edits or travel."""
import json,time,traceback,datetime,unreal as ue
from pathlib import Path
assert Path(ue.Paths.project_dir()).resolve()==ROOT
assert ue.SystemLibrary.get_engine_version().startswith('5.8.3-58210709')
report={'passed':False,'independent_primary':True,'fixture_only':True,'actual_travel_tested':False,'checks':[]}
state={'stage':0,'at':time.monotonic()+3,'deadline':time.monotonic()+90,'held':False}
co_cls=ue.load_asset('/Game/Puzzles/Run/BP_RunCoordinator').generated_class()
ex_cls=ue.load_asset('/Game/Puzzles/BP_MapExit').generated_class()
pc_cls=ue.load_asset('/Game/Puzzles/Test/HC_RunEnding/BP_RunEndingFixturePC').generated_class()
ac_cls=ue.load_asset('/Game/Puzzles/UI/Results/AC_RunResults').generated_class()
w_cls=ue.load_asset('/Game/Puzzles/UI/Results/WBP_RunResults').generated_class()
hud_cls=ue.load_asset('/Game/Puzzles/UI/HCA3/AC_HCA3HUD').generated_class()
probe=ue.get_default_object(ue.load_asset('/Game/Puzzles/Test/HC2/BP_HC2InputProbe').generated_class())
action=ue.load_asset('/Game/Puzzles/Test/HC_RunEnding/IA_FixtureRestart')
def ws():return list(ue.EditorLevelLibrary.get_pie_worlds(True))
def server():return next(w for w in ws() if ue.GameplayStatics.get_game_mode(w))
def gm():return ue.GameplayStatics.get_game_mode(server())
def co(w=None):
 items=ue.GameplayStatics.get_all_actors_of_class(w or server(),co_cls);assert len(items)==1,len(items);return items[0]
def pcs():return [pc for w in ws() for pc in ue.GameplayStatics.get_all_actors_of_class(w,pc_cls) if pc.is_local_controller()]
def roster():return list(ue.GameplayStatics.get_game_state(server()).player_array)
def prop(a,n):return a.get_editor_property(n)
def calls():return prop(gm(),'FixtureCompleteCalls')
def totals(obj):return [prop(obj,'RelicsCollected'),prop(obj,'RelicsAvailable')]
def step(n,delay=1):state['stage']=n;state['at']=time.monotonic()+delay
def move(ps,inside):
 sid=prop(ps,'PlayerId')
 for w in ws():
  for p in ue.GameplayStatics.get_all_actors_of_class(w,ue.Pawn):
   if p.player_state and prop(p.player_state,'PlayerId')==sid:
    if isinstance(p,ue.Character):p.get_component_by_class(ue.CharacterMovementComponent).disable_movement()
    p.set_actor_enable_collision(False);p.set_actor_location(ue.Vector(1200,0,100) if inside else ue.Vector(0,600,100),False,True)
def inject(v):
 sub=ue.EnhancedInputLocalPlayerSubsystem.cast(probe.call_method('ResolveInput',args=(state['host'],)));assert sub
 sub.inject_input_vector_for_action(action,ue.Vector(v,0,0),[],[])
def check_widgets():
 out={}
 active=[w for w in ue.ObjectIterator(ue.UserWidget) if w.get_class()==w_cls and w.is_in_viewport()]
 for pc in pcs():
  ac=pc.get_component_by_class(ac_cls);assert ac and len(pc.get_components_by_class(ac_cls))==1
  widget=prop(ac,'ResultsWidget');assert widget and widget.is_in_viewport() and widget.get_owning_player()==pc
  assert prop(ac,'Coordinator')==co(pc.get_world()) and prop(widget,'Coordinator')==co(pc.get_world())
  assert len([w for w in active if w.get_owning_player()==pc])==1
  pawn=pc.get_controlled_pawn();assert pawn and prop(pawn,'InputReady')
  hud=prop(pawn.get_component_by_class(hud_cls),'HUDWidget');assert hud and hud.get_owning_player()==pc
  assert prop(pawn,'PromptWidget').get_owning_player()==pc
  out[pc.get_path_name()]=widget.get_path_name()
 assert len(out)==len(set(out.values()))
 return out
def finish(ok,error=None):
 if state['held']:inject(0);state['held']=False
 report['passed']=ok;report['ended_at']=str(datetime.datetime.now())
 if error:report['error']=error
 (HERE/(ARGS.get('report','primary-native')+'.json')).write_text(json.dumps(report,indent=2));ue.unregister_slate_post_tick_callback(handle)
 ue.log('HC_RUN_ENDING_PRIMARY_VERIFICATION: '+str(ok))
def tick(dt):
 try:
  now=time.monotonic();assert now<state['deadline'],'primary scenario timed out'
  if state['held']:inject(1)
  if now<state['at']:return
  stage=state['stage']
  if stage==0:
   assert len(roster())==3 and len(pcs())==3
   gm().call_method('AddRelics',args=(7,));state['second']=ue.GameplayStatics.create_player(server(),-1,True);assert state['second'];step(1,3)
  elif stage==1:
   assert len(roster())==4
   for ps in roster():move(ps,ps!=state['second'].player_state)
   step(2,2)
  elif stage==2:
   assert calls()==0 and all(prop(ex,'RequiredPlayers')==4 and prop(ex,'ReadyPlayers')==3 for ex in ue.GameplayStatics.get_all_actors_of_class(server(),ex_cls))
   report['checks'].append({'four_player_roster_includes_second_host_local':True,'missing_local_blocks':True})
   ue.GameplayStatics.remove_player(state['second'],True);step(3,3)
  elif stage==3:
   assert len(roster())==3 and calls()==1 and prop(co(),'SnapshotCommitted')
   assert totals(ue.GameplayStatics.get_game_instance(server()))==[7,19]
   report['checks'].append({'disconnect_of_only_missing_player_commits_once':True,'gi_captured':[7,19]})
   for ex in ue.GameplayStatics.get_all_actors_of_class(server(),ex_cls):ex.call_method('StopExit')
   co().destroy_actor();step(4,1)
  elif stage==4:
   gm().call_method('FixtureClearTotals');assert totals(ue.GameplayStatics.get_game_state(server()))==[0,0]
   new=gm().call_method('FixtureSpawnCoordinator');assert new.call_method('RestoreResults') and not new.call_method('RestoreResults')
   assert totals(ue.GameplayStatics.get_game_state(server()))==[7,19]
   report['checks'].append({'restore_changes_gs_from_zero_to_snapshot':True});step(5,3)
  elif stage==5:
   check_widgets();state['second']=ue.GameplayStatics.create_player(server(),-1,True);step(6,3)
  elif stage==6:
   assert len(roster())==4 and len(pcs())==4;report['checks'].append({'late_host_local_results':check_widgets()})
   state['host']=next(pc for pc in pcs() if pc.get_world()==server() and pc.is_primary_player())
   remote_server=next(pc for pc in ue.GameplayStatics.get_all_actors_of_class(server(),pc_cls) if not pc.is_local_controller())
   other_world=next(pc for pc in pcs() if pc.get_world()!=server() and pc.is_primary_player())
   for pc in [None,remote_server,other_world,state['second']]:assert not co().call_method('RequestRestart',args=(pc,))
   assert calls()==1 and totals(ue.GameplayStatics.get_game_instance(server()))==[7,19]
   report['checks'].append({'direct_server_guards_reject_null_remote_foreign_world_and_secondary':True,'guard_calls_are_not_rpc_proof':True})
   state['extra']=gm().call_method('FixtureSpawnCoordinator');step(7,2)
  elif stage==7:
   assert not state['extra'].call_method('CaptureSnapshot') and not state['extra'].call_method('RestoreResults')
   first=next(a for a in ue.GameplayStatics.get_all_actors_of_class(server(),co_cls) if a!=state['extra'])
   assert not first.call_method('RequestRestart',args=(state['host'],))
   for pc in pcs():
    ac=pc.get_component_by_class(ac_cls);assert not prop(ac,'ResultsWidget') and not prop(ac,'Coordinator')
   assert calls()==1;report['checks'].append({'ambiguous_coordinators_hide_results_and_reject_capture_restore_restart':True})
   state['extra'].destroy_actor();step(8,2)
  elif stage==8:
   report['checks'].append({'singleton_recovery_one_live_widget_per_owner':check_widgets()})
   state['held']=True;step(9,.35)
  elif stage==9:
   inject(0);state['held']=False;step(10,2)
  elif stage==10:
   assert calls()==2 and prop(state['host'],'RestartInputEvents')==1 and prop(co(),'RestartInProgress')
   assert totals(ue.GameplayStatics.get_game_instance(server()))==[0,0]
   for w in ws():assert prop(co(w),'RestartInProgress')
   report['checks'].append({'actual_owning_input_after_lifecycle_recovery_restarts_once':True,'gi_reset':[0,0]})
   state['held']=True;step(11,.35)
  elif stage==11:
   inject(0);state['held']=False;step(12,1)
  else:
   assert calls()==2 and prop(state['host'],'RestartInputEvents')==2
   report['checks'].append({'repeat_input_cannot_restart_twice':True,'final_active_widgets':check_widgets()});finish(True)
 except Exception:finish(False,traceback.format_exc())
handle=ue.register_slate_post_tick_callback(tick)
