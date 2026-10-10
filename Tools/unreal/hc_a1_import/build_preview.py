"""Create a dedicated HC asset inspection map and render it in read-only L_StyleTest.
Requires -HCA1BuildPreview; never saves the shared map.
"""
import json
import math
from pathlib import Path
import sys
import time
import unreal as ue
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
assert '-HCA1BuildPreview' in ue.SystemLibrary.get_command_line().split()
assert Path(ue.Paths.project_dir()).resolve()==ROOT
TARGET='/Game/Puzzles/Test/L_HCA1_AssetTest'
exists=ue.EditorAssetLibrary.does_asset_exist(TARGET)
assert not exists or '-HCA1RepairPreview' in ue.SystemLibrary.get_command_line().split(),'Preview already exists; refusing overwrite'
manifest=json.loads((HERE/'manifest.json').read_text())
actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
levels=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
world=ue.EditorLoadingAndSavingUtils.load_map(TARGET) if exists else ue.EditorLoadingAndSavingUtils.new_blank_map(False)
if exists:
 for previous in list(actors.get_all_level_actors()):
  if 'HCA1_AssetInspection' in [str(t) for t in previous.tags]:
   assert previous.get_level().get_outermost().get_name()==TARGET
   assert actors.destroy_actor(previous)
assert ue.EditorLoadingAndSavingUtils.save_map(world,TARGET)
assert levels.set_current_level_by_name('L_HCA1_AssetTest')
OFFSET=1500.0
CUBE=ue.load_asset('/Engine/BasicShapes/Cube')
ROCK=ue.load_asset('/Game/Shared/Style/MI_Stylized_Rock')
created=[]

def spawn(cls,label,location,rotation=ue.Rotator(0,0,0)):
 actor=actors.spawn_actor_from_class(cls,ue.Vector(*location),rotation)
 assert actor.get_level().get_outermost().get_name()==TARGET
 actor.set_actor_label(label)
 actor.set_editor_property('tags',[ue.Name('HCA1_AssetInspection')])
 created.append(actor)
 return actor

def cube(label,location,size):
 actor=spawn(ue.StaticMeshActor,label,location)
 actor.static_mesh_component.set_static_mesh(CUBE)
 actor.static_mesh_component.set_material(0,ROCK)
 actor.set_actor_scale3d(ue.Vector(*(v/100 for v in size)))
 return actor

floor=cube('HCA1_TestFloor',(OFFSET,180,-5),(700,1000,10))
for index,asset in enumerate(manifest['assets']):
 y=index*120.0
 cube('HCA1_Plinth_'+asset['name'],(OFFSET,y,22.5),(65,90,45))
 actor=spawn(ue.StaticMeshActor,'HCA1_'+asset['name'],(OFFSET,y,45))
 actor.static_mesh_component.set_static_mesh(ue.load_asset(asset['destination']))
 # The headlamp-like white key and cool cave fill expose shiny material response.
 for suffix,x,z,intensity,color in [('Headlamp',100,90,50,ue.Color(255,244,223,255)),('CaveFill',-50,130,20,ue.Color(63,208,201,255))]:
  light=spawn(ue.PointLight,'HCA1_'+suffix+'_'+str(index),(OFFSET+x,y+45,z))
  light.point_light_component.set_editor_property('intensity_units',ue.LightUnits.LUMENS)
  light.point_light_component.set_editor_property('intensity',intensity)
  light.point_light_component.set_editor_property('attenuation_radius',260.0)
  light.point_light_component.set_editor_property('light_color',color)
  light.point_light_component.set_editor_property('source_radius',8.0)
 height=asset['source_validation']['dimensions_cm'][2]
 width=max(asset['source_validation']['dimensions_cm'])
 center=(OFFSET,y,45+height*0.5)
 cam_pos=(OFFSET+max(85,width*2.6),y+max(25,width*0.65),center[2]+max(15,height*0.4))
 delta=[b-a for a,b in zip(cam_pos,center)]
 rotation=ue.Rotator(pitch=math.degrees(math.atan2(delta[2],math.hypot(delta[0],delta[1]))),yaw=math.degrees(math.atan2(delta[1],delta[0])),roll=0)
 camera=spawn(ue.CameraActor,'HCA1_Camera_'+asset['name'],cam_pos,rotation)
 camera.get_component_by_class(ue.CameraComponent).set_editor_property('field_of_view',40.0)

reference=spawn(ue.SkeletalMeshActor,'HCA1_Reference_TemplateCharacter_180cm',(OFFSET,530,0),ue.Rotator(0,0,0))
reference.skeletal_mesh_component.set_skeletal_mesh_asset(ue.load_asset('/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple'))
ref_bounds=reference.get_actor_bounds(False)
ref_height=ref_bounds[1].z*2
reference.set_actor_scale3d(ue.Vector(*(180.0/ref_height for _ in range(3))))
volume=spawn(ue.PostProcessVolume,'HCA1_FixedCaveExposure',(OFFSET,180,0))
volume.set_editor_property('unbound',True)
settings=volume.get_editor_property('settings')
for field,value in {'override_auto_exposure_min_brightness':True,'override_auto_exposure_max_brightness':True,'auto_exposure_min_brightness':1.3,'auto_exposure_max_brightness':1.3,'override_motion_blur_amount':True,'motion_blur_amount':0.0}.items():
 settings.set_editor_property(field,value)
volume.set_editor_property('settings',settings)
volume.set_editor_property('priority',100.0)
overview=spawn(ue.CameraActor,'HCA1_Camera_Overview',(OFFSET+800,260,160),ue.Rotator(pitch=-4,yaw=180,roll=0))
overview.get_component_by_class(ue.CameraComponent).set_editor_property('field_of_view',48.0)
assert ue.EditorLoadingAndSavingUtils.save_map(world,TARGET)

# Read-only shared style review: mount only our owned HC test level in memory.
style=ue.EditorLoadingAndSavingUtils.load_map('/Game/Shared/Style/L_StyleTest')
assert style
stream=ue.EditorLevelUtils.add_level_to_world(style,TARGET,ue.LevelStreamingAlwaysLoaded)
assert stream
assert levels.set_current_level_by_name('L_HCA1_AssetTest')
levels.editor_set_game_view(True)
by_label={a.get_actor_label():a for a in actors.get_all_level_actors()}
render_dir=HERE/'renders'
render_dir.mkdir(exist_ok=True)
shots=[('overview','HCA1_Camera_Overview')]+[(a['name'],'HCA1_Camera_'+a['name']) for a in manifest['assets']]
report={'project':str(ROOT),'engine':ue.SystemLibrary.get_engine_version(),'saved_test_level':TARGET,'style_map_loaded_read_only':'/Game/Shared/Style/L_StyleTest','shared_map_saved':False,'reference_character_height_cm':180.0,'actors_created_in_owned_test_level':[a.get_actor_label() for a in actors.get_all_level_actors() if a.get_level().get_outermost().get_name()==TARGET],'renders':[],'gameplay_acceptance':False}
ue.EditorPythonScripting.set_keep_python_script_alive(True)
state={'index':0,'task':None,'started':time.monotonic(),'next':time.monotonic()+5}

def tick(delta):
 try:
  now=time.monotonic()
  if now-state['started']>240:
   raise RuntimeError('Screenshot timeout')
  if state['task'] is not None:
   if not state['task'].is_task_done():
    return
   name,_=shots[state['index']]
   path=render_dir/(name+'.png')
   assert path.is_file() and path.stat().st_size>1000,'Screenshot missing'
   report['renders'].append(str(path))
   state['index']+=1
   state['task']=None
   state['next']=now+2
  if state['index']==len(shots):
   (HERE/'engine_render_validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
   ue.log('HC-A1_RENDER_VALIDATION_COMPLETE')
   ue.unregister_slate_post_tick_callback(handle)
   ue.EditorPythonScripting.set_keep_python_script_alive(False)
   return
  if now>=state['next']:
   name,label=shots[state['index']]
   state['task']=ue.AutomationLibrary.take_high_res_screenshot(1280,720,str(render_dir/(name+'.png')),camera=by_label[label],delay=2.0)
 except Exception as error:
  ue.log_error('HC-A1_RENDER_FAILED: '+repr(error))
  ue.unregister_slate_post_tick_callback(handle)
  ue.EditorPythonScripting.set_keep_python_script_alive(False)
handle=ue.register_slate_post_tick_callback(tick)
