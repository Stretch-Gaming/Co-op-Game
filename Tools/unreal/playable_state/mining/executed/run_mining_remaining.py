import json,importlib.util,traceback
from pathlib import Path
spec=importlib.util.spec_from_file_location('ue_client','/tmp/coop-ue.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);c.start()
D=Path('/tmp/coop-runtime');E=Path('/tmp/coop-mining');LOG=Path('/Volumes/CoopBuild/Logs/CoopGameEditor/CoopGame.log')
cases=json.loads((D/'mining-matrix-args.json').read_text())['cases'];results=[]
try:
 for n,profile,owner,case in cases:
  result={'players':n,'profile':profile,'owner':owner,'case':case};start=LOG.stat().st_size;started=False
  try:
   (D/'control-args.json').write_text(json.dumps({'action':'prepare','players':n if profile=='joining' else n-1,'mode':'PIE_Client' if profile=='joining' else 'PIE_ListenServer'}));v=json.loads(c.runpy(str(D/'control.py'),str(D/'control-result.json'),15));assert v['ok'],v
   c.tool('EditorToolset.EditorAppToolset','StartPIE',{'options':{'bSimulate':False,'playMode':'PlayMode_InViewPort','warmupSeconds':2}});started=True
   if profile=='host_split':
    (D/'control-args.json').write_text(json.dumps({'action':'split','players':n}));v=json.loads(c.runpy(str(D/'control.py'),str(D/'control-result.json'),15));assert v['ok'],v
   (D/'ready-args.json').write_text(json.dumps({'players':n,'profile':profile}));v=json.loads(c.runpy(str(D/'ready.py'),str(D/'ready-result.json'),35));assert v['ok'],v
   args={'players':n,'profile':profile,'owner':owner,'rock_owner':1 if owner!=1 else 0,'timeout':240,'case':case,'mode':'trigger_and_injected_pickup'}
   (E/'acceptance-args.json').write_text(json.dumps(args))
   for role,filename,report in [('trigger','acceptance_trigger_pickaxe-v2.py',f'trigger-pickaxe-{profile}-{n}-owner{owner}-trigger_and_injected_pickup.json')]+([] if case=='trigger' else [('completion','acceptance_transaction-v5.py',f'completion-{case}-{profile}-{n}-owner{owner}.json')]):
    wrapper=E/('execute_'+role+'.py');wrapper.write_text("import json\nfrom pathlib import Path\nARGS=json.loads(Path('/tmp/coop-mining/acceptance-args.json').read_text())\np=Path('/tmp/coop-mining/"+filename+"')\nexec(compile(p.read_text(),str(p),'exec'),globals())\n")
    v=json.loads(c.runpy(str(wrapper),str(E/report),280));result[role]=v;print(json.dumps({'players':n,'profile':profile,'owner':owner,'case':case,'role':role,'passed':v['passed'],'stage':v.get('phase'),'error':v.get('error'),'checks':len(v['checks'])}),flush=True)
    if not v['passed']:break
   result['passed']=all(v.get('passed',False) for k,v in result.items() if k in ('trigger','completion')) and 'trigger' in result
  except Exception:result.update(passed=False,exception=traceback.format_exc());print(json.dumps({'case':case,'exception':result['exception']}),flush=True)
  finally:
   if started:c.tool('EditorToolset.EditorAppToolset','StopPIE',{})
   with LOG.open('rb') as f:f.seek(start);text=f.read().decode(errors='replace')
   lp=E/f'acceptance-{case}-{profile}-{n}-owner{owner}-log.txt';lp.write_text(text)
   result['native_log_errors']=[line for line in text.splitlines() if any(x in line for x in ['Accessed None','Blueprint Runtime Error','LogPython: Error:','LogScript: Error:'])]
   results.append(result);(D/'mining-matrix-summary.json').write_text(json.dumps(results,indent=2));print(json.dumps({'case':case,'native_log_errors':len(result['native_log_errors'])}),flush=True)
  if not result['passed']:break
finally:
 (D/'mining-matrix-summary.json').write_text(json.dumps(results,indent=2))
