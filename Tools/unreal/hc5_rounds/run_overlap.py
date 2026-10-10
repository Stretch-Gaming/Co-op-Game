import json,subprocess,sys,time,re
from pathlib import Path
import rpc
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
if rpc.call('EditorToolset.EditorAppToolset','IsPIERunning',{}).get('returnValue',False):rpc.call('EditorToolset.EditorAppToolset','StopPIE',{})
subprocess.run([sys.executable,'-B',str(HERE/'request.py'),'configure.py',json.dumps({'clients':2})],check=True)
log=ROOT/'Saved/Logs/HC5.log';offset=log.stat().st_size;rpc.call('EditorToolset.EditorAppToolset','StartPIE',{'options':{}})
p=HERE/'entrance-overlap.json'
if p.exists():p.unlink()
subprocess.run([sys.executable,'-B',str(HERE/'request.py'),'test_overlap.py'],check=True)
end=time.monotonic()+40
while time.monotonic()<end and not p.exists():time.sleep(.25)
assert p.exists();r=json.loads(p.read_text());print(json.dumps(r))
with log.open('rb') as f:f.seek(offset);txt=f.read().decode('utf-8',errors='replace')
errors=[l for l in txt.splitlines() if re.search(r'Accessed None|Blueprint Runtime Error|Log\w+: Error:',l)];(HERE/'entrance-overlap-log.json').write_text(json.dumps({'passed':not errors,'start_byte':offset,'end_byte':log.stat().st_size,'errors':errors},indent=2))
assert r['passed'],r
assert not errors,errors
rpc.call('EditorToolset.EditorAppToolset','StopPIE',{})
