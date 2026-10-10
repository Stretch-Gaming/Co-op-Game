import json, sys, traceback
from pathlib import Path
import unreal
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
assert Path(unreal.Paths.project_dir()).resolve()==ROOT
assert unreal.SystemLibrary.get_engine_version().startswith('5.8.3-')
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
(HERE/'ready.json').write_text(json.dumps({'project':str(ROOT),'engine':unreal.SystemLibrary.get_engine_version()}))
last=None
busy=False
def tick(dt):
 global last,busy
 if busy:return
 p=HERE/'command.json'
 if not p.exists():return
 d=json.loads(p.read_text())
 if d['id']==last:return
 last=d['id'];busy=True
 try:
  script=(HERE/d['script']).resolve();assert script.is_relative_to(HERE)
  env={'__file__':str(script),'__name__':'__main__','ARGS':d.get('args',{}),'ROOT':ROOT,'HERE':HERE}
  exec(compile(script.read_text(encoding='utf-8'),str(script),'exec'),env)
  r={'id':last,'ok':True}
 except Exception:
  r={'id':last,'ok':False,'error':traceback.format_exc()};unreal.log_error(r['error'])
 (HERE/'command-result.json').write_text(json.dumps(r,indent=2));busy=False
handle=unreal.register_slate_post_tick_callback(tick)
unreal.log('HC5_ISOLATED_PROJECT: '+ROOT.as_posix())
