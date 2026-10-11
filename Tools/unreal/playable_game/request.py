"""Submit one bounded script to this worktree's dedicated Unreal editor."""
import json
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
QUEUE = ROOT / 'Saved/PlayableGame'
ready = json.loads((QUEUE / 'ready.json').read_text())
assert Path(ready['project']).resolve() == ROOT.resolve() and ready['port'] == 8060
request = {'id': str(uuid.uuid4()), 'script': sys.argv[1], 'args': json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}}
request['during_pie'] = request['args'].pop('_during_pie', False)
temporary = QUEUE / 'command.tmp'
temporary.write_text(json.dumps(request))
for publish_attempt in range(10):
    try:
        temporary.replace(QUEUE / 'command.json')
        break
    except PermissionError:
        if publish_attempt == 9:
            raise
        time.sleep(.025)
deadline = time.monotonic() + request['args'].get('_timeout', 50)
while time.monotonic() < deadline:
    path = QUEUE / 'command-result.json'
    if path.exists():
        result = json.loads(path.read_text())
        if result['id'] == request['id']:
            print(json.dumps(result, indent=2))
            assert result['ok'], result
            break
    time.sleep(.2)
else:
    raise TimeoutError('Native script is still pending; inspect its status before retrying')
