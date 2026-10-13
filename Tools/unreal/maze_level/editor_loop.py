"""Serialized primary-owned native editor queue for the maze-level correction."""
import json,os,traceback,hashlib
from pathlib import Path
import unreal as ue
ROOT=Path(ue.Paths.project_dir()).resolve();HERE=Path(__file__).resolve().parent
assert ROOT==HERE.parents[2] and ue.SystemLibrary.get_engine_version().startswith('5.8.3-')
QUEUE=ROOT/'Saved/MazeLevel';QUEUE.mkdir(parents=True,exist_ok=True)
world=ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
for command in ('t.IdleWhenNotForeground 0','Slate.AllowSlateToSleep 0','Slate.bAllowThrottling 0'):
    ue.SystemLibrary.execute_console_command(world,command)
ue.EditorPythonScripting.set_keep_python_script_alive(True)
last=None
def tick(delta):
    global last
    request=QUEUE/'request.json'
    if not request.exists():return
    try:data=json.loads(request.read_text(encoding='utf-8-sig'))
    except json.JSONDecodeError:return
    if data['id']==last:return
    last=data['id']
    try:
        script=(HERE/data['script']).resolve();assert script.is_relative_to(HERE)
        if not data.get('during_pie'):assert not ue.EditorLevelLibrary.get_pie_worlds(True)
        scope={'__file__':str(script),'__name__':'__main__','ROOT':ROOT,'HERE':HERE,'QUEUE':QUEUE,'ARGS':data.get('args',{})}
        exec(compile(script.read_text(encoding='utf-8-sig'),str(script),'exec'),scope)
        result={'id':last,'ok':True,'script_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),'result':scope.get('RESULT')}
    except Exception:result={'id':last,'ok':False,'error':traceback.format_exc()};ue.log_error(str(result))
    (QUEUE/'result.json').write_text(json.dumps(result,default=str,indent=2))
handle=ue.register_slate_post_tick_callback(tick)
(QUEUE/'ready.json').write_text(json.dumps({'pid':os.getpid(),'project':str(ROOT)}))
