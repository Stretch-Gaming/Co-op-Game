import json,time,traceback,unreal as ue
N=ARGS['clients'];report={'passed':False,'clients':N,'checks':[],'map':'L_Site01','placements_authored':False}
worlds=list(ue.EditorLevelLibrary.get_pie_worlds(True));cls=ue.load_asset('/Game/Core/BP_CoopCharacter').generated_class();ac=ue.load_asset('/Game/Puzzles/Carrying/AC_Carrying').generated_class();hud=ue.load_asset('/Game/Puzzles/UI/HCA3/AC_HCA3HUD').generated_class()
local=[p for w in worlds for p in ue.GameplayStatics.get_all_actors_of_class(w,cls) if p.is_locally_controlled()]
state={'at':time.monotonic()+2,'stage':0,'deadline':time.monotonic()+45}
positions={};move=ue.load_asset('/Game/Input/Actions/IA_Move')
if not move:move=next(m.action for m in ue.load_asset('/Game/Core/Input/IMC_Coop').get_editor_property('mappings') if m.action.get_name()=='IA_Move')

def inject(value):
 for p in local:
  sub=next(s for s in ue.ObjectIterator(ue.EnhancedInputLocalPlayerSubsystem) if 'Default__' not in s.get_path_name() and s.get_world()==p.get_world())
  sub.inject_input_vector_for_action(move,ue.Vector(value,0,0),[],[])
def finish(ok,error=None):
 report['passed']=ok
 if error:report['error']=error
 (HERE/f'site01-{N}.json').write_text(json.dumps(report,indent=2));ue.unregister_slate_post_tick_callback(handle);ue.log('HC2_SITE01_'+str(N)+': '+str(ok))
def tick(dt):
 try:
  now=time.monotonic();assert now<state['deadline'],'Main smoke timeout'
  if state['stage']==1:inject(1)
  if now<state['at']:return
  if state['stage']==0:
   assert len(worlds)==N+1 and len(local)==N
   for w in worlds:
    gs=ue.GameplayStatics.get_game_state(w);assert gs.call_method('GetPlayerCount')==N
    assert sorted(p.get_editor_property('ColorSlot') for p in gs.player_array)==list(range(N))
    assert len(ue.GameplayStatics.get_all_actors_with_tag(w,'HC_A2_Prop'))==11
    for tag in ['HC1MainInstant','HC1MainTimed','HC1MainContinuous']:assert len(ue.GameplayStatics.get_all_actors_with_tag(w,tag))==1
    for p in ue.GameplayStatics.get_all_actors_of_class(w,cls):assert len(p.get_components_by_class(ac))==1
   for p in local:
    assert p.get_editor_property('InputReady')
    assert p.get_component_by_class(hud).get_editor_property('HUDWidget').get_owning_player()==p.get_controller()
    positions[p.get_path_name()]=p.get_actor_location()
   report['checks'].append({'preserved_hc1_markers':3,'reviewed_art_actors':11,'single_carrying_component':True,'owned_hud_and_colors':N})
   state['stage']=1;state['at']=now+.5
  elif state['stage']==1:inject(0);state['stage']=2;state['at']=now+1
  else:
   distances=[(p.get_actor_location()-positions[p.get_path_name()]).length() for p in local]
   assert all(d>10 for d in distances),distances
   assert all(p.get_actor_location().z>-100 for p in local)
   report['checks'].append({'actual_client_movement_cm':distances,'floor_support':True});finish(True)
 except Exception:finish(False,traceback.format_exc())
handle=ue.register_slate_post_tick_callback(tick)
