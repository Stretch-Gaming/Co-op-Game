"""Sequential native PIE gate in only the recorded dedicated editor."""
import json,subprocess,sys,time,re,base64
from pathlib import Path
import rpc
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
n=int(sys.argv[1]);host=len(sys.argv)>2 and sys.argv[2]=='host';assert n in (2,3,4)
if rpc.call('EditorToolset.EditorAppToolset','IsPIERunning',{}).get('returnValue',False):rpc.call('EditorToolset.EditorAppToolset','StopPIE',{})
subprocess.run([sys.executable,'-B',str(HERE/'request.py'),'configure.py',json.dumps({'clients':n,'mode':'PIE_ListenServer' if host else 'PIE_Client'})],check=True)
log=ROOT/'Saved/Logs/CoopGame.log';offset=log.stat().st_size
rpc.call('EditorToolset.EditorAppToolset','StartPIE',{'options':{'bSimulate':False,'playMode':'PlayMode_InViewPort','warmupSeconds':2}})
name='host-split' if host else f'clients-{n}';p=HERE/(name+'.json')
assert not p.exists(),'Preserve/rename an existing gate report before rerun'
subprocess.run([sys.executable,'-B',str(HERE/'request.py'),'test_run.py',json.dumps({'clients':n,'host':host})],check=True)
end=time.monotonic()+180
while time.monotonic()<end and not p.exists():time.sleep(.3)
assert p.exists(),'Report missing'
r=json.loads(p.read_text());print(json.dumps({'passed':r['passed'],'checks':len(r['checks']),'error':r.get('error')},indent=2))
with log.open('rb') as f:f.seek(offset);interval=f.read().decode('utf-8',errors='replace')
errors=[line for line in interval.splitlines() if re.search(r'Accessed None|Blueprint Runtime Error|Log\w+: Error:',line)]
(HERE/(name+'-log.json')).write_text(json.dumps({'passed':not errors,'log':'Saved/Logs/CoopGame.log','start_byte':offset,'end_byte':log.stat().st_size,'errors':errors},indent=2))
assert r['passed'],r.get('error');assert not errors,errors
