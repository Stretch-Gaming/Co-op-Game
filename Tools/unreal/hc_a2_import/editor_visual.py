"""Capture HC-owned cave-light views using the editor renderer, without saving cameras."""
import gc,json,time,traceback,struct
from pathlib import Path
import unreal
root=Path(__file__).resolve().parents[3]
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve()==root/"CoopGame.uproject"
for a in actors.get_all_level_actors():
 if a.get_actor_label()=="HC_A2_Temporary_Camera": actors.destroy_actor(a)
a=None
gc.collect()
assert levels.load_level("/Game/Puzzles/Test/L_HCA2_Props")
if not any(a.get_actor_label()=="HC_A2_Test_Floor" for a in actors.get_all_level_actors()):
 floor=actors.spawn_actor_from_object(unreal.load_asset("/Engine/BasicShapes/Cube"),unreal.Vector(700,1000,-10),unreal.Rotator(),False)
 floor.set_actor_label("HC_A2_Test_Floor");floor.set_actor_scale3d(unreal.Vector(36,24,0.2))
 floor.static_mesh_component.set_material(0,unreal.load_asset("/Game/Puzzles/Art/HCA2_Props/Materials/MI_HCA2_StoneCarving"))
 for name,loc,color,intensity in [
  ("HC_A2_Test_Torch_1",(100,650,300),(1,0.4508,0.063,1),1800),
  ("HC_A2_Test_Torch_2",(1300,650,350),(1,0.4508,0.063,1),2800),
  ("HC_A2_Test_Crystal_Fill",(200,1400,300),(0.0497,0.6308,0.5972,1),1000)]:
  a=actors.spawn_actor_from_class(unreal.PointLight,unreal.Vector(*loc),unreal.Rotator(),False)
  a.set_actor_label(name)
  c=a.get_component_by_class(unreal.PointLightComponent)
  c.set_light_color(unreal.LinearColor(*color));c.set_intensity(intensity);c.set_attenuation_radius(1600)
 assert levels.save_current_level()
shots=[
 {"name":"symbols_and_statues","level":"test","camera":(650,450,280),"target":(-100,1050,90),"size":(1600,900)},
 {"name":"symbols_half_screen","level":"test","camera":(450,650,210),"target":(-120,900,30),"size":(1600,450)},
 {"name":"gate_closed","level":"test","camera":(1450,600,260),"target":(850,1000,250),"size":(1600,900)},
 {"name":"gate_open","level":"test","camera":(2400,700,600),"target":(1800,1000,430),"size":(1600,900)},
 {"name":"site_gate_g1","level":"site","camera":(3200,-80,250),"target":(2500,0,260),"size":(1600,900)},
 {"name":"site_altar","level":"site","camera":(11300,-100,170),"target":(10800,0,65),"size":(1600,900)},
]
state={"index":0,"camera":None,"task":None,"started":time.monotonic(),"results":[],"level":"test","wait_until":time.monotonic()+3}
out=root/"Tools/unreal/hc_a2_import/evidence"
def finish(error=None):
 if state["camera"]:
  actors.destroy_actor(state["camera"]);state["camera"]=None
 unreal.unregister_slate_post_tick_callback(handle)
 result={"status":"failed" if error else "captured; visual review required","shots":state["results"]}
 if error:result["error"]=error
 (out/"visual_capture.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
def tick(delta):
 try:
  if time.monotonic()-state["started"]>300: raise RuntimeError("Screenshot timeout")
  if state["index"]>=len(shots): finish();return
  if time.monotonic()<state["wait_until"]:return
  shot=shots[state["index"]]
  if not state["task"]:
   if shot["level"]!=state["level"]:
    assert levels.load_level("/Game/Maps/L_Site01")
    assert levels.set_current_level_by_name("L_Site01_HC")
    state["level"]=shot["level"];state["wait_until"]=time.monotonic()+3;return
   loc=unreal.Vector(*shot["camera"]);rot=unreal.MathLibrary.find_look_at_rotation(loc,unreal.Vector(*shot["target"]))
   cam=actors.spawn_actor_from_class(unreal.CameraActor,loc,rot,False)
   cam.set_actor_label("HC_A2_Temporary_Camera")
   state["camera"]=cam
   cam.get_component_by_class(unreal.CameraComponent).set_field_of_view(90)
   path=out/(shot["name"]+".png")
   state["task"]=unreal.AutomationLibrary.take_high_res_screenshot(*shot["size"],str(path),camera=cam,delay=1.0,force_game_view=True)
   assert state["task"] is not None
   state["wait_until"]=time.monotonic()+3;return
  if not state["task"].is_task_done():return
  path=out/(shot["name"]+".png")
  assert path.is_file() and path.stat().st_size>10000,"Missing screenshot: "+str(path)
  state["results"].append({"name":shot["name"],"path":path.name,"pixels":shot["size"],"bytes":path.stat().st_size,"actual_pixels":list(struct.unpack(">II",path.read_bytes()[16:24]))})
  actors.destroy_actor(state["camera"]);state["camera"]=None;state["task"]=None;gc.collect()
  state["index"]+=1;state["wait_until"]=time.monotonic()+2
 except Exception:
  finish(traceback.format_exc())
handle=unreal.register_slate_post_tick_callback(tick)
print("HCA2_VISUAL capture scheduled")
