"""Sequential opt-in network matrix against the dedicated port and checkout."""
import json,subprocess,sys,time,os
from pathlib import Path
from mcp_client import start,call
HERE=Path(__file__).parent.resolve()
ROOT=HERE.parents[2]
def editor(script):
    runner='run_command.py' if os.environ.get('HC6_COMMAND_BRIDGE')=='1' else 'run_editor.py'
    argument=script if runner=='run_command.py' else str(HERE/script)
    subprocess.run([sys.executable,str(HERE/runner),argument],cwd=ROOT,check=True)
def app(name,args=None):
    return call('call_tool',{'toolset_name':'EditorToolset.EditorAppToolset','tool_name':name,'arguments':args or {}})
start()
cases=[(2,False),(3,False),(4,False),(2,True),(3,True),(4,True)]
if len(sys.argv)>1:
    cases=[(2,True),(3,True),(4,True)] if sys.argv[1]=='split' else [(int(sys.argv[1]),len(sys.argv)>2 and sys.argv[2]=='split')]
summary=[]
for players,split in cases:
    name=('split-' if split else 'clients-')+str(players)
    running=json.loads(app('IsPIERunning')['content'][0]['text'])['returnValue']
    if running:app('StopPIE')
    config={'players':players,'split':split,'run':name}
    (HERE/'run-config.json').write_text(json.dumps(config)+'\n')
    editor('prepare_pie.py')
    settings=json.loads((HERE/'pie-settings.json').read_text())
    assert settings['PlayNetMode']==('PIE_ListenServer' if split else 'PIE_Client'),settings
    assert settings['PlayNumberOfClients']==(players-1 if split else players),settings
    app('StartPIE',{'options':{'bSimulate':False,'playMode':'PlayMode_InViewPort','warmupSeconds':2}})
    began=time.time()
    editor('test_round1.py')
    path=HERE/(name+'.json')
    while time.time()-began<140:
        if path.exists() and path.stat().st_mtime>began:
            try:result=json.loads(path.read_text())
            except json.JSONDecodeError:time.sleep(.2);continue
            if 'passed' in result:break
        time.sleep(1)
    else:raise TimeoutError(name)
    summary.append({'run':name,'passed':result['passed'],'checks':len(result['checks']),'duration_seconds':result['duration_seconds']})
    (HERE/'matrix-summary.json').write_text(json.dumps(summary,indent=2))
    print(json.dumps(summary[-1]),flush=True)
    assert result['passed'],result.get('error')
