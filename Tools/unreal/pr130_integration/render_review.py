"""Transient native engine renders; no packages saved and no gameplay gate claimed."""
import hashlib,json,time
from pathlib import Path
import unreal as ue
ROOT=Path(ue.Paths.project_dir()).resolve();assert ROOT==Path(__file__).resolve().parents[3]
out=ROOT/'Saved/PR130Integration/renders';out.mkdir(parents=True,exist_ok=True)
editor=ue.get_editor_subsystem(ue.LevelEditorSubsystem)
actors=ue.get_editor_subsystem(ue.EditorActorSubsystem)
assert editor.load_level('/Game/Puzzles/Test/SixRound/L_SixRound_Test')
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
ue.GameplayStatics.flush_level_streaming(world)
assert editor.set_current_level_by_name('L_SixRound_HC_Test')
editor.editor_set_game_view(True)
for command in ('t.IdleWhenNotForeground 0','Slate.AllowSlateToSleep 0','Slate.bAllowThrottling 0'):
    ue.SystemLibrary.execute_console_command(world,command)
shots=[('maze_entry',(325,2550,175),(-175,3500,150),80),
       ('meeting_hall',(-175,8900,-110),(-1275,9250,90),90),
       ('flare_art',(550,-80,163),(550,0,160),45)]
camera=actors.spawn_actor_from_class(ue.CameraActor,ue.Vector())
assert camera.get_level().get_outermost().get_name()=='/Game/Puzzles/Test/SixRound/L_SixRound_HC_Test'
flare=actors.spawn_actor_from_class(ue.load_asset('/Game/Player/Tools/BP_Flare').generated_class(),ue.Vector(550,0,160))
assert flare.get_level()==camera.get_level()
state={'index':0,'at':time.monotonic(),'task':None,'next':time.monotonic()+12}
report={'method':'Native D3D11 engine screenshots using transient inspection cameras and one flare-art fixture; no asset saves. Separate from normal packaged startup and human play.','images':[],'passed':False}
ue.EditorPythonScripting.set_keep_python_script_alive(True)
def finish():
    actors.destroy_actor(flare);actors.destroy_actor(camera)
    (out/'report.json').write_text(json.dumps(report,indent=2))
    ue.unregister_slate_post_tick_callback(handle)
    ue.EditorPythonScripting.set_keep_python_script_alive(False)
    ue.SystemLibrary.quit_editor()
def tick(delta):
    try:
        now=time.monotonic();assert now-state['at']<220,'Render timeout'
        if state['task']:
            if not state['task'].is_task_done():return
            path=out/(shots[state['index']][0]+'.png');assert path.is_file() and path.stat().st_size>1000
            report['images'].append({'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
            state['index']+=1;state['task']=None;state['next']=now+3
        if state['index']==len(shots):report['passed']=True;finish();return
        if now>=state['next']:
            name,pos,target,fov=shots[state['index']]
            camera.set_actor_location(ue.Vector(*pos),False,True)
            camera.set_actor_rotation(ue.MathLibrary.find_look_at_rotation(ue.Vector(*pos),ue.Vector(*target)),True)
            camera.camera_component.set_field_of_view(fov)
            state['task']=ue.AutomationLibrary.take_high_res_screenshot(1280,720,str(out/(name+'.png')),camera=camera,delay=3.)
    except Exception as error:report['error']=repr(error);finish()
handle=ue.register_slate_post_tick_callback(tick)
