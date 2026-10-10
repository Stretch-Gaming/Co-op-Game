"""Submit an allowed script to the dedicated unattended editor's main thread."""
import json,sys,time,uuid
from pathlib import Path
HERE=Path(__file__).parent.resolve()
ident=str(uuid.uuid4())
(HERE/'editor-command.json').write_text(json.dumps({'id':ident,'script':sys.argv[1]}))
deadline=time.monotonic()+120
while time.monotonic()<deadline:
    path=HERE/'editor-command-result.json'
    if path.exists():
        try:result=json.loads(path.read_text())
        except json.JSONDecodeError:time.sleep(.1);continue
        if result['id']==ident:
            assert result['passed'],result.get('error')
            print('Completed '+sys.argv[1]);break
    time.sleep(.2)
else:raise TimeoutError(sys.argv[1])
