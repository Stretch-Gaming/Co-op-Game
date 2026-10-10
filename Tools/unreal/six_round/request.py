"""Submit one bounded script to this worktree's dedicated Unreal editor."""
import json
import sys
import time
import uuid
import hashlib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
QUEUE = ROOT / 'Saved/SixRound'
ready = json.loads((QUEUE / 'ready.json').read_text())
assert Path(ready['project']).resolve() == ROOT.resolve() and ready['port'] == 8061
request = {'id': str(uuid.uuid4()), 'script': sys.argv[1], 'args': json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}}
request['during_pie'] = request['args'].pop('_during_pie', False)
temporary = QUEUE / 'command.tmp'
temporary.write_text(json.dumps(request))
temporary.replace(QUEUE / 'command.json')
deadline = time.monotonic() + request['args'].get('_timeout', 50)
while time.monotonic() < deadline:
    path = QUEUE / 'command-result.json'
    if path.exists():
        result = json.loads(path.read_text())
        if result['id'] == request['id']:
            receipts = QUEUE / 'receipts'
            receipts.mkdir(exist_ok=True)
            receipt = {'script': request['script'], 'args': request['args'],
                       'source_sha256': hashlib.sha256((Path(__file__).parent/request['script']).read_bytes()).hexdigest(),
                       'finished_utc': datetime.now(timezone.utc).isoformat(), 'native': result}
            (receipts/(request['id']+'.json')).write_text(json.dumps(receipt, indent=2))
            print(json.dumps(result, indent=2))
            assert result['ok'], result
            break
    time.sleep(.2)
else:
    raise TimeoutError('Native script is still pending; inspect its status before retrying')
