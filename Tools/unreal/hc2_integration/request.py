"""Submit one script to the isolated editor; refuse a mismatched project."""
import json,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
assert Path(json.loads((HERE/'ready.json').read_text())['project']).resolve()==ROOT
script=(HERE/sys.argv[1]).resolve();assert script.is_relative_to(HERE) and script.is_file()
request_id=time.time_ns()
(HERE/'command.json').write_text(json.dumps({'id':request_id,'script':script.name,'args':json.loads(sys.argv[2]) if len(sys.argv)>2 else {}}))
end=time.monotonic()+90
while time.monotonic()<end:
 try:r=json.loads((HERE/'command-result.json').read_text())
 except (FileNotFoundError,ValueError):r={}
 if r.get('id')==request_id:
  print(json.dumps(r,indent=2));sys.exit(0 if r['ok'] else 1)
 time.sleep(.25)
raise TimeoutError('Editor script did not finish within 90s')
