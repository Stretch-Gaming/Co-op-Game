"""Focused native restoration proof. No travel or RPC called from Python."""
import json,time,traceback,datetime,unreal as ue
report={'passed':False,'fixture_only':True,'actual_travel_tested':False,'checks':[],'started_at':str(datetime.datetime.now())}
state={'stage':0,'at':time.monotonic()+3,'deadline':time.monotonic()+30}
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));server=next(w for w in worlds if ue.GameplayStatics.get_game_mode(w));gm=ue.GameplayStatics.get_game_mode(server);gs=ue.GameplayStatics.get_game_state(server);gi=ue.GameplayStatics.get_game_instance(server)
coCls=ue.load_asset('/Game/Puzzles/Run/BP_RunCoordinator').generated_class();exitCls=ue.load_asset('/Game/Puzzles/BP_MapExit').generated_class();acCls=ue.load_asset('/Game/Puzzles/UI/Results/AC_RunResults').generated_class()
def totals(obj):return {'collected':obj.get_editor_property('RelicsCollected'),'available':obj.get_editor_property('RelicsAvailable')}
def finish(ok,error=None):
 report['passed']=ok;report['ended_at']=str(datetime.datetime.now())
 if error:report['error']=error
 (HERE/'restore-cleared-state.json').write_text(json.dumps(report,indent=2));ue.unregister_slate_post_tick_callback(handle)
def tick(dt):
 try:
  now=time.monotonic();assert now<state['deadline']
  if now<state['at']:return
  if state['stage']==0:
   for ex in ue.GameplayStatics.get_all_actors_of_class(server,exitCls):ex.call_method('StopExit')
   gm.call_method('AddRelics',args=(7,));co=ue.GameplayStatics.get_all_actors_of_class(server,coCls)[0];assert co.call_method('CaptureSnapshot')
   assert totals(gi)=={'collected':7,'available':19}
   gm.call_method('FixtureClearTotals');assert totals(gs)=={'collected':0,'available':0}
   report['checks'].append({'gi_before_restore':totals(gi),'gs_deliberately_cleared_before_restore':totals(gs)})
   co.destroy_actor();new=gm.call_method('FixtureSpawnCoordinator');assert new.call_method('RestoreResults');assert totals(gs)=={'collected':7,'available':19}
   report['checks'].append({'server_restored_immediately':totals(gs)});state['stage']=1;state['at']=now+3
  else:
   snapshots=[]
   for w in worlds:
    stateobj=ue.GameplayStatics.get_game_state(w);co=ue.GameplayStatics.get_all_actors_of_class(w,coCls)[0];assert totals(stateobj)=={'collected':7,'available':19};assert co.get_editor_property('CapturedCollected')==7 and co.get_editor_property('CapturedAvailable')==19 and co.get_editor_property('ResultsActive')
    pcs=[pc for pc in ue.GameplayStatics.get_all_actors_of_class(w,ue.PlayerController) if pc.is_local_controller()]
    for pc in pcs:
     widget=pc.get_component_by_class(acCls).get_editor_property('ResultsWidget');assert widget and widget.get_owning_player()==pc
    snapshots.append({'world':w.get_path_name(),'gs_after_delay':totals(stateobj),'owned_widgets':len(pcs)})
   report['checks'].append({'all_worlds_after_delay':snapshots});finish(True)
 except Exception:finish(False,traceback.format_exc())
handle=ue.register_slate_post_tick_callback(tick)
