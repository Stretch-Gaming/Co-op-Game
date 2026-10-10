import json,sys,time,uuid
from pathlib import Path
h=Path(__file__).resolve().parent
id=str(uuid.uuid4());(h/'command.json').write_text(json.dumps({'id':id,'script':sys.argv[1],'args':json.loads(sys.argv[2]) if len(sys.argv)>2 else {}}))
end=time.monotonic()+90
while time.monotonic()<end:
 p=h/'command-result.json'
 if p.exists():
  d=json.loads(p.read_text())
  if d['id']==id:
   print(json.dumps(d));assert d['ok'],d;break
 time.sleep(.25)
else:raise TimeoutError('Editor request timed out')
