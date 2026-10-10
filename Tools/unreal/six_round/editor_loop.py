"""Primary-owned, project-specific Unreal command loop for issue #93."""
import json
import sys
import traceback
from pathlib import Path
import unreal as ue

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
EXPECTED = Path('C:/Users/Stretch/.codex/worktrees/six-round-adventure/Co op Game').resolve()
QUEUE = ROOT / 'Saved/SixRound'
QUEUE.mkdir(parents=True, exist_ok=True)
assert ROOT.resolve() == EXPECTED
assert Path(ue.Paths.project_dir()).resolve() == EXPECTED
assert ue.SystemLibrary.get_engine_version().startswith('5.8.3-')
ue.EditorPythonScripting.set_keep_python_script_alive(True)
ue.SystemLibrary.execute_console_command(ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world(), 'ModelContextProtocol.StartServer 8061')
completed = QUEUE / 'command-result.json'
last = json.loads(completed.read_text(encoding='utf-8-sig')).get('id') if completed.exists() else None
busy = False

def tick(delta):
    global last, busy
    request = QUEUE / 'command.json'
    if busy or not request.exists():
        return
    data = json.loads(request.read_text(encoding='utf-8-sig'))
    if data['id'] == last:
        return
    busy = True
    last = data['id']
    try:
        assert Path(ue.Paths.project_dir()).resolve() == EXPECTED
        script = (HERE / data['script']).resolve()
        assert script.is_relative_to(HERE.resolve()), script
        if not data.get('during_pie', False):
            assert not ue.EditorLevelLibrary.get_pie_worlds(True), 'Stop PIE before authoring/inspection'
        namespace = {'__file__': str(script), '__name__': '__main__', 'ROOT': ROOT, 'HERE': HERE, 'QUEUE': QUEUE, 'ARGS': data.get('args', {})}
        exec(compile(script.read_text(encoding='utf-8-sig'), str(script), 'exec'), namespace)
        result = {'id': last, 'ok': True, 'result': namespace.get('RESULT')}
    except Exception:
        result = {'id': last, 'ok': False, 'error': traceback.format_exc()}
        ue.log_error('PLAYABLE_GAME_COMMAND: ' + result['error'])
    (QUEUE / 'command-result.json').write_text(json.dumps(result, default=str, indent=2))
    busy = False

handle = ue.register_slate_post_tick_callback(tick)
(QUEUE / 'ready.json').write_text(json.dumps({'project': str(ROOT), 'engine': ue.SystemLibrary.get_engine_version(), 'port': 8061}))
ue.log('SIX_ROUND_ISOLATED_PROJECT: ' + ROOT.as_posix())
