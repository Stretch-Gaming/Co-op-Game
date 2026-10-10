"""Run only the remaining PG regression cases in this dedicated editor."""
import json
from pathlib import Path
import subprocess
import sys
import time
ROOT = Path(__file__).resolve().parents[3]
QUEUE = ROOT / 'Saved/PGSignatureFix'
assert json.loads((QUEUE / 'input-2.json').read_text())['passed']
def rpc(name, args=None):
    result = subprocess.run([sys.executable, '-B', str(Path(__file__).with_name('rpc.py')), name,
                             json.dumps(args or {})], capture_output=True, text=True, timeout=55)
    assert result.returncode == 0, result.stdout + result.stderr
def queue(script, number):
    request = QUEUE / 'request.json'
    assert not request.exists()
    temp = QUEUE / 'request.tmp'
    temp.write_text(json.dumps({'script': script, 'id': number}))
    temp.replace(request)
    deadline = time.monotonic() + 50
    while time.monotonic() < deadline:
        response = QUEUE / 'response.json'
        if response.exists():
            payload = json.loads(response.read_text())
            if payload.get('id') == number:
                assert payload['ok'], payload
                return
        time.sleep(0.2)
    raise AssertionError('Editor queue timeout')
results = []
try:
    for index, opts in enumerate([{'players': 3}, {'players': 4}, {'players': 3, 'split': True}]):
        rpc('StopPIE')
        (QUEUE / 'options.json').write_text(json.dumps(opts))
        queue('prepare.py', 20 + index * 2)
        rpc('StartPIE', {'options': {'bSimulate': False, 'playMode': 'PlayMode_InEditorFloating', 'warmupSeconds': 2}})
        report = QUEUE / ('input-' + ('split' if opts.get('split') else str(opts['players'])) + '.json')
        assert not report.exists(), 'Do not overwrite an existing acceptance report'
        queue('test_input.py', 21 + index * 2)
        deadline = time.monotonic() + 50
        while not report.exists() and time.monotonic() < deadline:
            time.sleep(0.2)
        payload = json.loads(report.read_text())
        assert payload['passed'], payload
        results.append({'case': opts, 'checks': payload['checks'], 'passed': True})
        print(json.dumps(results[-1]), flush=True)
finally:
    rpc('StopPIE')
    queue('restore.py', 40)
(QUEUE / 'matrix.json').write_text(json.dumps({'passed': True, 'cases': results}, indent=2))
