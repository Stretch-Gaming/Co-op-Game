"""HC-7/HC-8 isolated editor command loop. Never operates outside this checkout."""
import json, sys, time, traceback, os
from pathlib import Path
import unreal
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'Tools/unreal/hc_run_ending'
assert Path(unreal.Paths.project_dir()).resolve()==ROOT
assert unreal.SystemLibrary.get_engine_version().startswith('5.8.3-58210709')
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
(HERE/'ready.json').write_text(json.dumps({'project':str(ROOT),'engine':unreal.SystemLibrary.get_engine_version(),'pid':os.getpid(),'port':8017}))
last=None
busy=False

def tick(dt):
 global last,busy
 if busy:return
 path=HERE/'command.json'
 if not path.exists():return
 data=json.loads(path.read_text())
 if data['id']==last:return
 last=data['id'];busy=True
 try:
  script=(HERE/data['script']).resolve()
  assert script.is_relative_to(HERE)
  if script.name in {'scaffold.py','build.py','build_results.py','fixtures.py','build_fixture.py','fixture_spawn.py','fixture_clear.py','seed_fixture.py','audit.py'}:
   assert not unreal.EditorLevelLibrary.get_pie_worlds(True),'Stop PIE before authoring or compiling'
  env={'__file__':str(script),'__name__':'__main__','ARGS':data.get('args',{}),'ROOT':ROOT,'HERE':HERE}
  exec(compile(script.read_text(encoding='utf-8'),str(script),'exec'),env)
  result={'id':last,'ok':True}
 except Exception:
  result={'id':last,'ok':False,'error':traceback.format_exc()}
  unreal.log_error(result['error'])
 (HERE/'command-result.json').write_text(json.dumps(result,indent=2))
 busy=False
handle=unreal.register_slate_post_tick_callback(tick)
unreal.log('HC_RUN_ENDING_ISOLATED_PROJECT: '+ROOT.as_posix())
