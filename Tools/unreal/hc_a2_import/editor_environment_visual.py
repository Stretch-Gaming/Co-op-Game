"""Render approved HZ integration without saving cameras or temporary gate poses."""
import json,gc,time,traceback,struct
from pathlib import Path
import unreal
root=Path(__file__).resolve().parents[3]
assert Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve()==root/'CoopGame.uproject'
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assert levels.load_level('/Game/Maps/L_Site01');assert levels.set_current_level_by_name('L_Site01_HC')
gates={a.get_actor_label():a for a in actors.get_all_level_actors() if a.actor_has_tag('HC_A2_Prop') and '_Gate_' in a.get_actor_label()}
shots=[{'name':'cave_plate_hall','camera':(4100,-1200,310),'target':(4000,1100,100)}, {'name':'cave_altar','camera':(11300,-150,170),'target':(10800,0,65)}]
for label,x in [('G1',2500),('G2',5500),('G3',11500)]:
 for pose,z in [('closed',0),('half',200),('open',400)]:
  shots.append({'name':'cave_gate_'+label+'_'+pose,'camera':(x-500,-60,210),'target':(x,0,260),'gate':'HC_A2_Gate_'+label,'z':z})
for name,x,y in [('diamond',3200,-800),('circle',3200,800),('triangle',4800,-800),('cross',4800,800)]:
 shots.append({'name':'cave_half_'+name,'camera':(x+300,y,170),'target':(x,y,25),'size':(800,450)})
out=root/'Tools/unreal/hc_a2_import/evidence'
run_id=json.loads((root/'Saved/HCA2/request.json').read_text(encoding='utf-8-sig'))['id']
(out/'environment_capture.json').write_text(json.dumps({'status':'running','run_id':run_id}),encoding='utf-8')
state={'i':0,'camera':None,'task':None,'started':time.monotonic(),'wait':time.monotonic()+4,'results':[]}
def restore():
 for a in gates.values():a.call_method('SetOpenVisual',args=(False,))
def finish(error=None):
 unreal.unregister_slate_post_tick_callback(handle)
 if state['camera']:actors.destroy_actor(state['camera']);state['camera']=None
 try:restore()
 except Exception:error=error or traceback.format_exc()
 r={'status':'failed' if error else 'captured; visual review required','run_id':run_id,'shots':state['results'],'temporary_poses_restored':not bool(error),'camera_packages_saved':False}
 if error:r['error']=error
 (out/'environment_capture.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
def tick(delta):
 try:
  if time.monotonic()-state['started']>300:raise RuntimeError('Capture timeout')
  if state['i']>=len(shots):finish();return
  if time.monotonic()<state['wait']:return
  shot=shots[state['i']]
  if state['task'] is None:
   restore()
   if 'gate' in shot:
    a=gates[shot['gate']];c=next(c for c in a.get_components_by_class(unreal.StaticMeshComponent) if c.get_name().startswith('GateLeaf'));c.set_relative_location(unreal.Vector(0,0,shot['z']),False,False)
   loc=unreal.Vector(*shot['camera']);rot=unreal.MathLibrary.find_look_at_rotation(loc,unreal.Vector(*shot['target']))
   cam=actors.spawn_actor_from_class(unreal.CameraActor,loc,rot,False);state['camera']=cam;cam.set_actor_label('HCA2_ReviewCamera');cam.get_component_by_class(unreal.CameraComponent).set_field_of_view(90)
   state['task']=unreal.AutomationLibrary.take_high_res_screenshot(*shot.get('size',(1600,900)),str(out/(shot['name']+'.png')),camera=cam,delay=1.0,force_game_view=True)
   assert state['task'] is not None;state['wait']=time.monotonic()+3;return
  if not state['task'].is_task_done():return
  path=out/(shot['name']+'.png');assert path.exists() and path.stat().st_size>10000
  state['results'].append({'name':shot['name'],'camera_cm':shot['camera'],'target_cm':shot['target'],'leaf_z_cm':shot.get('z'),'actual_pixels':list(struct.unpack('>II',path.read_bytes()[16:24])),'bytes':path.stat().st_size})
  actors.destroy_actor(state['camera']);state['camera']=None;state['task']=None;restore();gc.collect();state['i']+=1;state['wait']=time.monotonic()+2
 except Exception:finish(traceback.format_exc())
handle=unreal.register_slate_post_tick_callback(tick)
print('HCA2_ENVIRONMENT_VISUAL scheduled')
