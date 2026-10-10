"""Opt-in HC gauntlet editor inbox. The primary owns editor lifecycle.

This script only registers an inbox and publishes identity on startup. Mutation
requires primary-written authorization.json matching this process session.
"""
import json, os, sys, time, traceback, uuid
from pathlib import Path
import unreal

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
EXPECTED = Path('C:/Users/Stretch/.codex/worktrees/haunted-gauntlet-integration/Co op Game').resolve()
assert ROOT == EXPECTED
assert Path(unreal.Paths.project_dir()).resolve() == EXPECTED
ENGINE = unreal.SystemLibrary.get_engine_version()
assert ENGINE.startswith('5.8.3-58210709'), ENGINE
SESSION = str(uuid.uuid4())
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
(HERE/'ready.json').write_text(json.dumps({'project':str(ROOT),'engine':ENGINE,'pid':os.getpid(),'session':SESSION,'mcp_port':8045},indent=2))
last = None
busy = False

def tick(dt):
 global last,busy
 if busy: return
 path = HERE/'command.json'
 if not path.exists(): return
 try: data = json.loads(path.read_text())
 except (ValueError,OSError): return
 if data['id'] == last: return
 last = data['id']; busy = True
 try:
  assert data['session'] == SESSION, 'Stale or mismatched editor session'
  script = (HERE/data['script']).resolve()
  assert script.is_relative_to(HERE) and script.suffix == '.py' and script.is_file()
  read_only = script.name.startswith('inspect_')
  if not read_only:
   authorization = json.loads((HERE/'authorization.json').read_text())
   assert authorization['session'] == SESSION and authorization['project'] == str(ROOT)
   assert authorization['allow_owned_mutation'] is True
  if script.name.startswith(('author_','audit_','fixture_')):
   assert not unreal.EditorLevelLibrary.get_pie_worlds(True), 'Stop PIE before authoring/compiling'
  env={'__file__':str(script),'__name__':'__main__','ARGS':data.get('args',{}),'ROOT':ROOT,'HERE':HERE,'SESSION':SESSION}
  exec(compile(script.read_text(encoding='utf-8'),str(script),'exec'),env)
  result={'id':last,'session':SESSION,'ok':True}
 except Exception:
  result={'id':last,'session':SESSION,'ok':False,'error':traceback.format_exc()}
  unreal.log_error(result['error'])
 (HERE/'command-result.json').write_text(json.dumps(result,indent=2))
 busy=False

handle=unreal.register_slate_post_tick_callback(tick)
unreal.log('HC_GAUNTLET_ISOLATED_PROJECT: '+ROOT.as_posix()+' SESSION: '+SESSION)
