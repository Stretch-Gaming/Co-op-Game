"""Primary-owned serialized Unreal queue for the bounded PR130 integration."""
import hashlib
import json
import os
import traceback
from pathlib import Path
import unreal as ue

ROOT = Path(ue.Paths.project_dir()).resolve()
assert ROOT == Path(__file__).resolve().parents[3]
assert ue.SystemLibrary.get_engine_version().startswith('5.8.3-')
HERE = Path(__file__).resolve().parent
QUEUE = ROOT / 'Saved/PR130Integration'
QUEUE.mkdir(parents=True, exist_ok=True)
ue.EditorPythonScripting.set_keep_python_script_alive(True)
last = None

def tick(delta):
    global last
    request = QUEUE / 'request.json'
    if not request.exists():
        return
    try:
        data = json.loads(request.read_text(encoding='utf-8-sig'))
    except json.JSONDecodeError:
        return # A producer may still be replacing the request file.
    if data['id'] == last:
        return
    last = data['id']
    try:
        script = (HERE / data['script']).resolve()
        assert script.is_relative_to(HERE) and script.suffix == '.py'
        if not data.get('during_pie', False):
            assert not ue.EditorLevelLibrary.get_pie_worlds(True), 'Stop PIE first'
        namespace = {'__file__': str(script), '__name__': '__main__', 'ROOT': ROOT,
                     'HERE': HERE, 'QUEUE': QUEUE, 'ARGS': data.get('args', {})}
        exec(compile(script.read_text(encoding='utf-8-sig'), str(script), 'exec'), namespace)
        result = {'id': last, 'ok': True, 'script_sha256': hashlib.sha256(script.read_bytes()).hexdigest(),
                  'result': namespace.get('RESULT')}
    except Exception:
        result = {'id': last, 'ok': False, 'error': traceback.format_exc()}
        ue.log_error('PR130_PRIMARY_QUEUE: ' + result['error'])
    (QUEUE/'result.json').write_text(json.dumps(result, default=str, indent=2))

handle = ue.register_slate_post_tick_callback(tick)
(QUEUE/'ready.json').write_text(json.dumps({'pid': os.getpid(), 'project': str(ROOT), 'engine': ue.SystemLibrary.get_engine_version()}))
