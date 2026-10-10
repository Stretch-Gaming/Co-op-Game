"""Verify the repaired PG subclass against HC2 Core using actual input."""
import json,re,subprocess,sys,time
from pathlib import Path
import rpc
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
log=ROOT/'Saved/Logs/HC2-completion.log'
start=log.stat().st_size
results=[]
def request(script,args=None):
 subprocess.run([sys.executable,'-B',str(HERE/'request.py'),script,json.dumps(args or {})],check=True)
try:
 for opts in [{'players':2},{'players':3},{'players':4},{'players':3,'split':True}]:
  if rpc.call('EditorToolset.EditorAppToolset','IsPIERunning',{}).get('returnValue',False):
   rpc.call('EditorToolset.EditorAppToolset','StopPIE',{})
  request('configure.py',{'clients':opts['players'],'mode':'PIE_ListenServer' if opts.get('split') else 'PIE_Client','map':'/Game/Player/Test/L_PG_Test'})
  case='split' if opts.get('split') else str(opts['players'])
  report=ROOT/'Saved/PGSignatureFix'/f'input-{case}.json'
  if report.exists():report.unlink()
  rpc.call('EditorToolset.EditorAppToolset','StartPIE',{'options':{'warmupSeconds':2}})
  request('review_pg_input.py',opts)
  deadline=time.monotonic()+55
  while not report.exists() and time.monotonic()<deadline:time.sleep(.25)
  data=json.loads(report.read_text());assert data['passed'],data
  (HERE/f'pg-core-input-{case}.json').write_text(json.dumps(data,indent=2))
  results.append({'case':case,'checks':data['checks'],'passed':True})
  print(json.dumps(results[-1]),flush=True)
finally:
 if rpc.call('EditorToolset.EditorAppToolset','IsPIERunning',{}).get('returnValue',False):rpc.call('EditorToolset.EditorAppToolset','StopPIE',{})
 request('restore.py')
with log.open('rb') as f:f.seek(start);interval=f.read().decode('utf-8',errors='replace')
errors=[line for line in interval.splitlines() if re.search(r'Accessed None|Blueprint Runtime Error|Log\w+: Error:',line)]
(HERE/'pg-core-input-log.json').write_text(json.dumps({'passed':not errors,'cases':results,'log':'Saved/Logs/HC2-completion.log','start_byte':start,'end_byte':log.stat().st_size,'errors':errors},indent=2))
assert not errors,errors
