import json,subprocess,sys,time,re
from pathlib import Path
import rpc
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
if rpc.call('EditorToolset.EditorAppToolset','IsPIERunning',{}).get('returnValue',False):rpc.call('EditorToolset.EditorAppToolset','StopPIE',{})
subprocess.run([sys.executable,'-B',str(HERE/'request.py'),'configure.py',json.dumps({'clients':2,'mode':'PIE_Client'})],check=True)
log=ROOT/'Saved/Logs/CoopGame.log';offset=log.stat().st_size
rpc.call('EditorToolset.EditorAppToolset','StartPIE',{'options':{'bSimulate':False,'playMode':'PlayMode_InViewPort','warmupSeconds':2}})
p=HERE/'restore-cleared-state.json';assert not p.exists()
subprocess.run([sys.executable,'-B',str(HERE/'request.py'),'test_restore.py'],check=True)
end=time.monotonic()+40
while time.monotonic()<end and not p.exists():time.sleep(.3)
assert p.exists();r=json.loads(p.read_text())
with log.open('rb') as f:f.seek(offset);interval=f.read().decode('utf-8',errors='replace')
errors=[l for l in interval.splitlines() if re.search(r'Accessed None|Blueprint Runtime Error|Log\w+: Error:',l)]
(HERE/'restore-cleared-state-log.json').write_text(json.dumps({'passed':not errors,'log':'Saved/Logs/CoopGame.log','start_byte':offset,'end_byte':log.stat().st_size,'errors':errors},indent=2))
print(json.dumps({'passed':r['passed'],'error':r.get('error'),'log_clean':not errors}));assert r['passed'],r.get('error');assert not errors
