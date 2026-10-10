"""Asset presence/pose regression checks in 2/3/4 client worlds and two local views."""
import gc,json,time,traceback
from pathlib import Path
import unreal
root=Path(__file__).resolve().parents[3]
assert Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve()==root/"CoopGame.uproject"
capture=root/'Tools/unreal/hc_a2_import/evidence/environment_capture.json'
if capture.exists():
 assert json.loads(capture.read_text()).get('status')!='running','Finish renderer capture before starting PIE'
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
settings=unreal.load_object(None,"/Script/UnrealEd.Default__LevelEditorPlaySettings")
keys=["PlayNetMode","PlayNumberOfClients","RunUnderOneProcess","ServerPort"]
before=unreal.ToolsetLibrary.get_object_properties(settings,keys)
gc.collect()
assert levels.load_level("/Game/Maps/L_Site01")
cases=[("client",2),("client",3),("client",4),("split",1)]
resume = root/"Saved/HCA2/resume_split.json"
prior = [row for row in json.loads((root/"Tools/unreal/hc_a2_import/evidence/client_checks.json").read_text())["cases"] if row["mode"]=="Play As Client"] if resume.exists() else []
if prior:
 assert [row["players"] for row in prior]==[2,3,4]
 cases=[("split",1)]
state={"i":0,"phase":"start","deadline":time.monotonic()+90,"results":prior,"split_shot":False}
def finish(error=None):
 if levels.is_in_play_in_editor(): levels.editor_request_end_play()
 unreal.ToolsetLibrary.set_object_properties(settings,before)
 unreal.unregister_slate_post_tick_callback(handle)
 r={"status":"failed" if error else "passed","cases":state["results"],"settings_restored":True,
    "split_screenshot_saved":state["split_shot"],
    "scope":"Asset loading, static poses and local views only; gameplay RPC/carry/round logic is not implemented or claimed."}
 if error:r["error"]=error
 (root/"Tools/unreal/hc_a2_import/evidence/client_checks.json").write_text(json.dumps(r,indent=2),encoding="utf-8")
def probe(world):
 all_actors=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.Actor)
 owned=[a for a in all_actors if a.actor_has_tag("HC_A2_Prop")]
 assert len(owned)==11,(world.get_path_name(),len(owned))
 for a in owned:
  components=a.get_components_by_class(unreal.StaticMeshComponent)
  assert components and all(c.static_mesh for c in components)
  for c in components:
   if c.get_name().startswith("PlateTop"): assert abs(c.get_editor_property("relative_location").z-9)<0.001
   if c.get_name().startswith("GateLeaf"): assert abs(c.get_editor_property("relative_location").z)<0.001
 pcs=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.PlayerController)
 locals_=[pc for pc in pcs if pc.is_local_controller()]
 return {"world":world.get_path_name(),"art_actors":len(owned),"controllers":len(pcs),"local_controllers":len(locals_)},locals_
def tick(delta):
 try:
  if time.monotonic()>state["deadline"]:raise RuntimeError("PIE phase timeout")
  if state["i"]>=len(cases):finish();return
  kind,count=cases[state["i"]]
  if state["phase"]=="start":
   assert not levels.is_in_play_in_editor()
   data={"PlayNetMode":"PIE_Client" if kind=="client" else "PIE_ListenServer",
         "PlayNumberOfClients":count,"RunUnderOneProcess":True,"ServerPort":27777}
   assert unreal.ToolsetLibrary.set_object_properties(settings,json.dumps(data))
   levels.editor_request_begin_play();state["phase"]="wait";state["ready_after"]=time.monotonic()+5;state["deadline"]=time.monotonic()+90;return
  if state["phase"]=="wait":
   if not levels.is_in_play_in_editor() or time.monotonic()<state["ready_after"]:return
   worlds=unreal.EditorLevelLibrary.get_pie_worlds(True)
   if kind=="client" and len(worlds)<count+1:return
   if kind=="split" and not worlds:return
   data=[];local_worlds=[]
   for w in worlds:
    row,pcs=probe(w);data.append(row)
    if pcs:local_worlds.append((w,pcs))
   if kind=="client":
    assert len(local_worlds)==count,(count,data)
    state["results"].append({"mode":"Play As Client","players":count,"worlds":data})
    levels.editor_request_end_play();state["phase"]="stop";state["deadline"]=time.monotonic()+45;return
   w,pcs=local_worlds[0]
   second=unreal.GameplayStatics.create_player(w,-1,True)
   assert second is not None
   state["phase"]="split_wait";state["ready_after"]=time.monotonic()+5;state["deadline"]=time.monotonic()+60;return
  if state["phase"]=="split_wait":
   if time.monotonic()<state["ready_after"]:return
   worlds=unreal.EditorLevelLibrary.get_pie_worlds(True)
   found=False
   for w in worlds:
    row,pcs=probe(w)
    if len(pcs)>=2:
     for pc,pos,yaw in zip(pcs,[(3550,-800,100),(5150,800,100)],[180,180]):
      pawn=pc.get_controlled_pawn();assert pawn is not None
      pawn.set_actor_location(unreal.Vector(*pos),False,True)
      pawn.set_actor_rotation(unreal.Rotator(pitch=0,yaw=yaw,roll=0),False)
      pc.set_control_rotation(unreal.Rotator(pitch=-25,yaw=yaw,roll=0))
     state["results"].append({"mode":"Listen server split-screen","local_players":len(pcs),"world":row})
     state["shot_world"]=w;state["shot_pc"]=pcs[0];found=True
   assert found,"Second local controller not present"
   state["phase"]="split_capture";state["ready_after"]=time.monotonic()+3;return
  if state["phase"]=="split_capture":
   if time.monotonic()<state["ready_after"]:return
   path=root/"Tools/unreal/hc_a2_import/evidence/cave_split_screen.png"
   pcs=unreal.GameplayStatics.get_all_actors_of_class(state['shot_world'],unreal.PlayerController)
   positions=[]
   for pc in [pc for pc in pcs if pc.is_local_controller()]:
    p=pc.get_controlled_pawn().get_actor_location();assert 70<p.z<130,('Unsupported split-screen pawn',p)
    positions.append([p.x,p.y,p.z])
   assert len(positions)==2
   state['results'][-1]['supported_pawn_locations_cm']=positions
   unreal.SystemLibrary.execute_console_command(state["shot_world"],'Shot filename="'+str(path)+'"',state["shot_pc"])
   state["shot_world"]=None;state["shot_pc"]=None;state["phase"]="split_done";state["ready_after"]=time.monotonic()+3;return
  if state["phase"]=="split_done":
   if time.monotonic()<state["ready_after"]:return
   path=root/"Tools/unreal/hc_a2_import/evidence/cave_split_screen.png"
   state["split_shot"]=bool(list(path.parent.glob("cave_split_screen*.png")))
   levels.editor_request_end_play();state["phase"]="stop";state["deadline"]=time.monotonic()+45;return
  if state["phase"]=="stop":
   if levels.is_in_play_in_editor() or unreal.EditorLevelLibrary.get_pie_worlds(True):return
   gc.collect();state["i"]+=1;state["phase"]="start";state["deadline"]=time.monotonic()+90
 except Exception:finish(traceback.format_exc())
handle=unreal.register_slate_post_tick_callback(tick)
print("HCA2_CLIENT checks scheduled")
