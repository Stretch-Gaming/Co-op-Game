"""Primary-only native verification runner; serialized dedicated endpoint."""
import json,subprocess,sys,time,re
from pathlib import Path
import rpc
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
mode=sys.argv[1];players=int(sys.argv[2])
assert mode in ('clients','host') and players in (2,3,4)
def request(script,args=None):subprocess.run([sys.executable,'-B',str(HERE/'request.py'),script,json.dumps(args or {})],check=True)
log=ROOT/'Saved/Logs/HC-Gauntlet-session2.log'
out=HERE/'primary-boundaries.json'
try:
 assert not rpc.call('EditorToolset.EditorAppToolset','IsPIERunning',{}).get('returnValue')
 request('configure.py',{'clients':players,'mode':'PIE_ListenServer' if mode=='host' else 'PIE_Client'})
 offset=log.stat().st_size
 if out.exists():out.unlink()
 rpc.call('EditorToolset.EditorAppToolset','StartPIE',{'options':{}})
 time.sleep(1.5)
 request('primary_edges.py',{'mode':mode})
 deadline=time.monotonic()+75
 while not out.exists() and time.monotonic()<deadline:time.sleep(.25)
 assert out.exists(),'Primary native result missing'
 report=json.loads(out.read_text())
 assert report['passed'],report
finally:
 if rpc.call('EditorToolset.EditorAppToolset','IsPIERunning',{}).get('returnValue'):rpc.call('EditorToolset.EditorAppToolset','StopPIE',{})
 request('restore.py')
time.sleep(.5)
with log.open('rb') as f:f.seek(offset);interval=f.read().decode('utf-8',errors='replace')
errors=[line for line in interval.splitlines() if re.search(r'Accessed None|Blueprint Runtime Error|Log\w+: Error:',line)]
report.update({'mode':mode,'configured_players':players,'post_stop_log_errors':errors,'log_interval':[offset,log.stat().st_size]})
result=HERE/f'primary-boundaries-{mode}-{players}.json'
result.write_text(json.dumps(report,indent=2))
assert not errors,errors
print(json.dumps({'passed':True,'report':result.name,'checks':len(report['checks'])},indent=2))
