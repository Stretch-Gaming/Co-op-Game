"""Wait for native network ownership/PlayerStates before executing the matrix."""
import pathlib,time,traceback,json,unreal as ue
HERE=pathlib.Path(__file__).parent;ROOT=HERE.parents[2];N=json.loads((ROOT/'Saved/HC6Altar/options.json').read_text(encoding='utf-8-sig'))['clients'];state={'deadline':time.monotonic()+30}
def tick(dt):
 try:
  assert time.monotonic()<state['deadline'],'Native PIE readiness timeout'
  ws=list(ue.EditorLevelLibrary.get_pie_worlds(True));ps=[p for w in ws for p in ue.GameplayStatics.get_all_actors_of_class(w,ue.Character) if p.is_locally_controlled()]
  if len(ws)!=N+1 or len(ps)!=N or any(not p.player_state for p in ps):return
  if any(len(ue.GameplayStatics.get_all_actors_of_class(w,ue.Character))!=N for w in ws):return
  ue.unregister_slate_post_tick_callback(handle)
  script=HERE/'test_clients.py';exec(compile(script.read_text(encoding='utf-8-sig'),str(script),'exec'),{'__file__':str(script),'guard':guard})
 except Exception:
  HERE.joinpath('readiness-error.txt').write_text(traceback.format_exc());ue.unregister_slate_post_tick_callback(handle)
handle=ue.register_slate_post_tick_callback(tick)
RESULT={'waiting_for_native_4_client_ownership':True}

