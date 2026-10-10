"""Submit one script to this worktree's own editor loop and print its result.

Usage: python3 request.py <script.py> ['{"arg": 1, "_timeout": 120, "_during_pie": false}']
"""
import json
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
QUEUE = ROOT / 'Saved/PR119'
ready = json.loads((QUEUE / 'ready.json').read_text())
assert Path(ready['project']).resolve() == ROOT.resolve() and ready['port'] == 8001
request = {'id': str(uuid.uuid4()), 'script': sys.argv[1], 'args': json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}}
request['during_pie'] = request['args'].pop('_during_pie', False)
timeout = request['args'].pop('_timeout', 120)
(QUEUE / 'command.tmp').write_text(json.dumps(request))
(QUEUE / 'command.tmp').replace(QUEUE / 'command.json')
deadline = time.monotonic() + timeout
while time.monotonic() < deadline:
    path = QUEUE / 'command-result.json'
    if path.exists():
        try:
            result = json.loads(path.read_text())
        except ValueError:
            time.sleep(.2)
            continue
        if result['id'] == request['id']:
            print(json.dumps(result, indent=2)[:20000])
            sys.exit(0 if result['ok'] else 1)
    time.sleep(.2)
sys.exit('Script still pending; check the editor before retrying')
