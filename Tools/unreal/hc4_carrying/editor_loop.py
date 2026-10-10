"""Isolated HC-4 editor command pump; never runs in another project."""
import json
import pathlib
import traceback
import unreal

ROOT = pathlib.Path(__file__).resolve().parents[3]
EXPECTED = pathlib.Path('C:/Users/Stretch/.codex/worktrees/hc4-carrying/Co op Game').resolve()
assert ROOT == EXPECTED
QUEUE = ROOT / 'Saved/HC4'
QUEUE.mkdir(parents=True, exist_ok=True)

def guard():
    active = pathlib.Path(unreal.Paths.convert_relative_path_to_full(unreal.Paths.get_project_file_path())).resolve()
    assert active == EXPECTED / 'CoopGame.uproject', str(active)
    return str(active)

def tick(delta):
    request = QUEUE / 'request.json'
    if not request.exists():
        return
    try:
        project = guard()
        data = json.loads(request.read_text(encoding='utf-8-sig'))
        request.unlink()
        script = (ROOT / data['script']).resolve()
        assert script.is_relative_to(ROOT / 'Tools/unreal/hc4_carrying')
        namespace = {'__file__': str(script), 'guard': guard}
        exec(compile(script.read_text(encoding='utf-8-sig'), str(script), 'exec'), namespace)
        result = {'ok': True, 'project': project, 'result': namespace.get('RESULT')}
    except Exception:
        result = {'ok': False, 'error': traceback.format_exc()}
    temporary = QUEUE / 'response.tmp'
    temporary.write_text(json.dumps(result, default=str, indent=2), encoding='utf-8')
    temporary.replace(QUEUE / 'response.json')

guard()
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
(QUEUE / 'identity.json').write_text(json.dumps({'project': guard(), 'port': 8024}), encoding='utf-8')
HANDLE = unreal.register_slate_post_tick_callback(tick)
