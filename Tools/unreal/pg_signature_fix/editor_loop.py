"""Dedicated, guarded editor queue for the PG test compatibility repair."""
import json
from pathlib import Path
import traceback
import unreal

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).parent.resolve()
EXPECTED = Path('C:/Users/Stretch/Development/Co op Game/Saved/MergeBuild/Source')
assert ROOT == EXPECTED
assert Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve() == ROOT / 'CoopGame.uproject'
QUEUE = ROOT / 'Saved/PGSignatureFix'
QUEUE.mkdir(parents=True, exist_ok=True)
def tick(_delta):
    request = QUEUE / 'request.json'
    if not request.exists():
        return
    try:
        payload = json.loads(request.read_text(encoding='utf-8-sig'))
    except json.JSONDecodeError:
        return
    request.unlink()
    try:
        path = (HERE / payload['script']).resolve()
        assert path.parent == HERE
        namespace = {'__file__': str(path), 'ROOT': ROOT}
        exec(compile(path.read_text(encoding='utf-8-sig'), str(path), 'exec'), namespace)
        result = {'ok': True, 'id': payload['id'], 'result': namespace.get('RESULT')}
    except Exception:
        result = {'ok': False, 'id': payload['id'], 'error': traceback.format_exc()}
    temp = QUEUE / 'response.tmp'
    temp.write_text(json.dumps(result, default=str, indent=2))
    temp.replace(QUEUE / 'response.json')
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
HANDLE = unreal.register_slate_post_tick_callback(tick)
(QUEUE / 'identity.json').write_text(json.dumps({'project': str(ROOT / 'CoopGame.uproject')}))
