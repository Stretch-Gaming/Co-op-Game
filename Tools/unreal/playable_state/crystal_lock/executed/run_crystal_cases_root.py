import json,importlib.util,traceback,time
from pathlib import Path
spec=importlib.util.spec_from_file_location('ue_client','/tmp/coop-ue.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);c.start()
D=Path('/tmp/coop-runtime');E=Path('/tmp/hc-a4-crystal-lock');LOG=Path('/Volumes/CoopBuild/Logs/CoopGameEditor/CoopGame.log');results=[]
for n,profile in [(2,'joining'),(4,'host_split')]:
 r={'players':n,'profile':profile};start=LOG.stat().st_size;started=False
 try:
  (D/'control-args.json').write_text(json.dumps({'action':'prepare','players':n if profile=='joining' else n-1,'mode':'PIE_Client' if profile=='joining' else 'PIE_ListenServer'}));v=json.loads(c.runpy(str(D/'control.py'),str(D/'control-result.json'),30));assert v['ok'],v
  c.tool('EditorToolset.EditorAppToolset','StartPIE',{'options':{'bSimulate':False,'playMode':'PlayMode_InViewPort','warmupSeconds':2}});started=True
  if profile=='host_split':
   (D/'control-args.json').write_text(json.dumps({'action':'split','players':n}));v=json.loads(c.runpy(str(D/'control.py'),str(D/'control-result.json'),30));assert v['ok'],v
  (D/'ready-args.json').write_text(json.dumps({'players':n,'profile':profile}));v=json.loads(c.runpy(str(D/'ready.py'),str(D/'ready-result.json'),40));assert v['ok'],v
  wrapper=E/'execute_lit.py';wrapper.write_text('from pathlib import Path\nARGS='+repr({'players':n,'profile':profile,'timeout':180})+'\np=Path("/tmp/hc-a4-crystal-lock/test_crystal_lock_lit.py")\nexec(compile(p.read_text(),str(p),"exec"),globals())\n')
  report=E/f'runtime-evidence/crystal-lock-lit-{profile}-{n}.json'
  report.unlink(missing_ok=True);c.runpy(str(wrapper),None)
  deadline=time.monotonic()+210
  while True:
   v=json.loads(report.read_text()) if report.exists() else {}
   if v and not v.get('runtime_acceptance_pending',False) and v.get('status') not in ('starting','running','runtime_pending'):break
   assert time.monotonic()<deadline, 'Waiting for terminal Lit report'
   time.sleep(.5)
  r['runtime']=v;r['passed']=v['passed'];print(json.dumps({'players':n,'profile':profile,'passed':v['passed'],'stage':v.get('stage'),'error':v.get('error'),'checks':len(v.get('checks',[]))}),flush=True)
 except Exception:r.update(passed=False,exception=traceback.format_exc());print(json.dumps(r),flush=True)
 finally:
  if started:c.tool('EditorToolset.EditorAppToolset','StopPIE',{})
  with LOG.open('rb') as f:f.seek(start);t=f.read().decode(errors='replace')
  (E/f'runtime-evidence/lit-{profile}-{n}-log.txt').write_text(t)
  r['native_log_errors']=[line for line in t.splitlines() if any(x in line for x in ['Accessed None','Blueprint Runtime Error','LogPython: Error:','LogScript: Error:'])]
  results.append(r);(D/'crystal-matrix-summary.json').write_text(json.dumps(results,indent=2));print(json.dumps({'profile':profile,'native_log_errors':len(r['native_log_errors'])}),flush=True)
 if not r['passed']:break
