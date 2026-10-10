"""Main-thread script bridge for unattended saved-file checks."""
import json,sys,traceback
from pathlib import Path
import unreal
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
assert Path(unreal.Paths.project_dir()).resolve()==ROOT
assert unreal.SystemLibrary.get_engine_version().startswith('5.8.3-')
sys.path.insert(0,str(HERE))
ALLOWED={'saved_audit.py','prepare_integrated_smoke.py','integrated_smoke.py','verify_editor.py','integrate_references.py','prepare_pie.py','test_round1.py','verify_configuration.py','audit.py'}
loop_state={'last_id':None}
def pump(dt):
    command=HERE/'editor-command.json'
    if not command.exists():return
    request=json.loads(command.read_text())
    if request['id']==loop_state['last_id']:return
    loop_state['last_id']=request['id']
    result={'id':request['id'],'project':str(ROOT),'script':request['script']}
    try:
        assert request['script'] in ALLOWED
        script=HERE/request['script']
        exec(compile(script.read_text(),str(script),'exec'),{'__file__':str(script),'__name__':'__main__'})
        result['passed']=True
    except Exception:result['passed']=False;result['error']=traceback.format_exc()
    (HERE/'editor-command-result.json').write_text(json.dumps(result,indent=2))
unreal.register_slate_post_tick_callback(pump)
(HERE/'editor-loop-status.json').write_text(json.dumps({'project':str(ROOT),'ready':True,'engine':unreal.SystemLibrary.get_engine_version()},indent=2))
