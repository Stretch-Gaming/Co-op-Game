"""Sequential native acceptance runner; always stop own PIE and restore unsaved preferences."""
import json,subprocess,sys,time,re
from pathlib import Path
import rpc
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
mode=sys.argv[1];n=int(sys.argv[2]);assert mode in ('clients','host') and n in (2,3,4)
output=f'input-{mode}-{n}.json'
def request(script,args=None):subprocess.run([sys.executable,'-B',str(HERE/'request.py'),script,json.dumps(args or {})],check=True)
try:
 if rpc.call('EditorToolset.EditorAppToolset','IsPIERunning',{}).get('returnValue'):rpc.call('EditorToolset.EditorAppToolset','StopPIE',{})
 request('configure.py',{'clients':n,'mode':'PIE_ListenServer' if mode=='host' else 'PIE_Client'})
 log=ROOT/'Saved/Logs/HC-Gauntlet-session2.log';offset=log.stat().st_size
 rpc.call('EditorToolset.EditorAppToolset','StartPIE',{'options':{}})
 result=HERE/output
 if result.exists():result.unlink()
 request('test_input.py',{'mode':mode,'output':output,'reconnect':mode=='clients' and n==3})
 end=time.monotonic()+190
 while time.monotonic()<end and not result.exists():time.sleep(.25)
 assert result.exists(),'Missing native acceptance result'
 value=json.loads(result.read_text());print(json.dumps(value,indent=2))
 with log.open('rb') as f:f.seek(offset);interval=f.read().decode('utf-8',errors='replace')
 errors=[l for l in interval.splitlines() if re.search(r'Accessed None|Blueprint Runtime Error|Log\w+: Error:',l)]
 (HERE/f'input-{mode}-{n}-log.json').write_text(json.dumps({'passed':not errors,'source':str(log.relative_to(ROOT)),'start_byte':offset,'end_byte':log.stat().st_size,'errors':errors},indent=2))
 assert value['passed'] and not errors,(value,errors)
finally:
 if rpc.call('EditorToolset.EditorAppToolset','IsPIERunning',{}).get('returnValue'):rpc.call('EditorToolset.EditorAppToolset','StopPIE',{})
 request('restore.py')
