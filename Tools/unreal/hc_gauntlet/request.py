"""Submit exactly one owned script to the primary-verified editor inbox."""
import json,sys,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ready=json.loads((HERE/'ready.json').read_text())
assert Path(ready['project']).resolve()==ROOT
assert ready['engine'].startswith('5.8.3-58210709') and ready['mcp_port']==8045
script=(HERE/sys.argv[1]).resolve()
assert script.is_relative_to(HERE) and script.is_file() and script.suffix=='.py'
request_id=time.time_ns()
pending=HERE/'command.part'
pending.write_text(json.dumps({'id':request_id,'session':ready['session'],'script':script.name,'args':json.loads(sys.argv[2]) if len(sys.argv)>2 else {}}))
pending.replace(HERE/'command.json')
end=time.monotonic()+90
while time.monotonic()<end:
 try:r=json.loads((HERE/'command-result.json').read_text())
 except (FileNotFoundError,ValueError):r={}
 if r.get('id')==request_id:
  assert r['session']==ready['session']
  print(json.dumps(r,indent=2));sys.exit(0 if r['ok'] else 1)
 time.sleep(.25)
raise TimeoutError('Editor inbox did not finish within 90s')
