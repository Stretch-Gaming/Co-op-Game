"""PG command loop for the PR #119 follow-ups, bound to this worktree's own editor (MCP port 8001)."""
import json
import sys
import traceback
from pathlib import Path
import unreal as ue

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
QUEUE = ROOT / 'Saved/PR119'
QUEUE.mkdir(parents=True, exist_ok=True)
PORT = 8001
assert Path(ue.Paths.convert_relative_path_to_full(ue.Paths.project_dir())).resolve() == ROOT.resolve()
assert ue.SystemLibrary.get_engine_version().startswith('5.8.3-')
ue.EditorPythonScripting.set_keep_python_script_alive(True)
completed = QUEUE / 'command-result.json'
last = json.loads(completed.read_text()).get('id') if completed.exists() else None
busy = False

def tick(delta):
    global last, busy
    request = QUEUE / 'command.json'
    if busy or not request.exists():
        return
    data = json.loads(request.read_text())
    if data['id'] == last:
        return
    busy = True
    last = data['id']
    try:
        script = (HERE / data['script']).resolve()
        assert script.is_relative_to(HERE.resolve()) or script.is_relative_to((HERE.parent / 'playable_game').resolve()), script
        if not data.get('during_pie', False):
            assert not ue.EditorLevelLibrary.get_pie_worlds(True), 'Stop PIE before authoring/inspection'
        namespace = {'__file__': str(script), '__name__': '__main__', 'ROOT': ROOT, 'HERE': script.parent, 'QUEUE': QUEUE, 'ARGS': data.get('args', {})}
        exec(compile(script.read_text(), str(script), 'exec'), namespace)
        result = {'id': last, 'ok': True, 'result': namespace.get('RESULT')}
    except Exception:
        result = {'id': last, 'ok': False, 'error': traceback.format_exc()}
        ue.log_error('PR119_COMMAND: ' + result['error'])
    (QUEUE / 'command-result.json').write_text(json.dumps(result, default=str, indent=2))
    busy = False

handle = ue.register_slate_post_tick_callback(tick)
(QUEUE / 'ready.json').write_text(json.dumps({'project': str(ROOT), 'engine': ue.SystemLibrary.get_engine_version(), 'port': PORT}))
ue.log('PR119_ISOLATED_PROJECT: ' + ROOT.as_posix())
