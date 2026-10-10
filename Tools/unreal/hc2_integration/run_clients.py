"""Run one isolated Play As Client acceptance and archive its log interval."""
import json,subprocess,sys,time,re
from pathlib import Path
import rpc
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
n=int(sys.argv[1]);assert n in (2,3,4)
running=rpc.call('EditorToolset.EditorAppToolset','IsPIERunning',{})
if running.get('returnValue',False):rpc.call('EditorToolset.EditorAppToolset','StopPIE',{})
subprocess.run([sys.executable,'-B',str(HERE/'request.py'),'configure.py',json.dumps({'clients':n})],check=True)
log=ROOT/'Saved/Logs/HC2-ui.log';offset=log.stat().st_size
rpc.call('EditorToolset.EditorAppToolset','StartPIE',{'options':{}})
p=HERE/f'clients-{n}.json'
if p.exists():p.unlink()
subprocess.run([sys.executable,'-B',str(HERE/'request.py'),'test_clients.py',json.dumps({'clients':n})],check=True)
end=time.monotonic()+135
while time.monotonic()<end and not p.exists():time.sleep(.25)
assert p.exists(),'Acceptance report missing'
r=json.loads(p.read_text());print(json.dumps(r,indent=2));assert r['passed'],r
with log.open('rb') as f:f.seek(offset);interval=f.read().decode('utf-8',errors='replace')
errors=[line for line in interval.splitlines() if re.search(r'Accessed None|Blueprint Runtime Error|Log\w+: Error:',line)]
(HERE/f'clients-{n}-log.json').write_text(json.dumps({'passed':not errors,'log':'Saved/Logs/HC2-ui.log','start_byte':offset,'end_byte':log.stat().st_size,'errors':errors},indent=2))
assert not errors,errors
