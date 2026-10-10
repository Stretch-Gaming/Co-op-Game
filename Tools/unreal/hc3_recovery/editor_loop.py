"""Isolated HC3 command loop; only this checkout is writable."""
import json,time,traceback,sys
from pathlib import Path
import unreal
ROOT=Path(__file__).resolve().parents[3]; HERE=Path(__file__).resolve().parent
assert ROOT==Path('C:/Users/Stretch/.codex/worktrees/revive-recovery/Co op Game')
assert Path(unreal.Paths.project_dir()).resolve()==ROOT
assert unreal.SystemLibrary.get_engine_version().startswith('5.8.3-')
sys.dont_write_bytecode=True
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
(HERE/'ready.json').write_text(json.dumps({'project':str(ROOT),'engine':unreal.SystemLibrary.get_engine_version(),'port':8043}))
last=None;busy=False

def tick(dt):
 global last,busy
 if busy:return
 path=HERE/'command.json'
 if not path.exists():return
 data=json.loads(path.read_text())
 if data['id']==last:return
 last=data['id'];busy=True
 try:
  script=(HERE/data['script']).resolve();assert script.is_relative_to(HERE)
  if script.name.startswith(('build','fixtures','audit')):assert not unreal.EditorLevelLibrary.get_pie_worlds(True)
  env={'__file__':str(script),'__name__':'__main__','ARGS':data.get('args',{}),'ROOT':ROOT,'HERE':HERE}
  exec(compile(script.read_text(encoding='utf-8-sig'),str(script),'exec'),env)
  result={'id':last,'ok':True}
 except Exception:
  result={'id':last,'ok':False,'error':traceback.format_exc()};unreal.log_error(result['error'])
 (HERE/'command-result.json').write_text(json.dumps(result,indent=2));busy=False
handle=unreal.register_slate_post_tick_callback(tick)
