import json,subprocess,sys,time,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'Tools/unreal/hc_run_ending'
name=sys.argv[1] if len(sys.argv)>1 else 'primary-native'
assert name in ('primary-native','primary-native-fresh')
sys.path.insert(0,str(HERE))
import rpc
if rpc.call('EditorToolset.EditorAppToolset','IsPIERunning',{}).get('returnValue',False):rpc.call('EditorToolset.EditorAppToolset','StopPIE',{})
subprocess.run([sys.executable,'-B',str(HERE/'request.py'),'configure.py',json.dumps({'clients':3,'mode':'PIE_ListenServer'})],check=True)
log=ROOT/'Saved/Logs/CoopGame.log';offset=log.stat().st_size
rpc.call('EditorToolset.EditorAppToolset','StartPIE',{'options':{'bSimulate':False,'playMode':'PlayMode_InViewPort','warmupSeconds':2}})
p=HERE/(name+'.json');assert not p.exists(),'Preserve existing primary evidence before rerun'
subprocess.run([sys.executable,'-B',str(HERE/'request.py'),'primary_native.py',json.dumps({'report':name})],check=True)
end=time.monotonic()+110
while time.monotonic()<end and not p.exists():time.sleep(.3)
assert p.exists(),'Primary evidence missing'
r=json.loads(p.read_text());print(json.dumps({'passed':r['passed'],'checks':len(r['checks']),'error':r.get('error')},indent=2))
rpc.call('EditorToolset.EditorAppToolset','StopPIE',{})
with log.open('rb') as f:f.seek(offset);interval=f.read().decode('utf-8',errors='replace')
errors=[line for line in interval.splitlines() if re.search(r'Accessed None|Blueprint Runtime Error|Log\w+: Error:',line)]
(HERE/(name+'-log.json')).write_text(json.dumps({'passed':not errors,'log':'Saved/Logs/CoopGame.log','start_byte':offset,'end_byte':log.stat().st_size,'errors':errors},indent=2))
assert r['passed'],r.get('error');assert not errors,errors
