import json,importlib.util,traceback,time
from pathlib import Path
spec=importlib.util.spec_from_file_location('ue_client','/tmp/coop-ue.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);c.start()
D=Path('/tmp/coop-runtime');E=Path('/tmp/coop-audit/runtime-evidence');LOG=Path('/Volumes/CoopBuild/Logs/CoopGameEditor/CoopGame.log');r={};started=False;start=LOG.stat().st_size
try:
 # Set the test prefs while default assembly is current; the map helper never saves packages.
 (D/'control-args.json').write_text(json.dumps({'action':'prepare','players':2,'mode':'PIE_Client'}));v=json.loads(c.runpy(str(D/'control.py'),str(D/'control-result.json'),30));assert v['ok'],v
 (D/'load-map-args.json').write_text(json.dumps({'path':'/Game/Maps/L_Site01'}));v=json.loads(c.runpy(str(D/'load_map.py'),str(D/'load-map-result.json'),120));assert v['ok'],v
 c.tool('EditorToolset.EditorAppToolset','StartPIE',{'options':{'bSimulate':False,'playMode':'PlayMode_InEditorFloating','warmupSeconds':2}});started=True
 (D/'ready-args.json').write_text(json.dumps({'players':2,'profile':'joining'}));v=json.loads(c.runpy(str(D/'ready.py'),str(D/'ready-result.json'),40));assert v['ok'],v
 wrapper=D/'execute_site_smoke_hud_final.py';wrapper.write_text('from pathlib import Path\nARGS={"timeout":90}\np=Path("/tmp/coop-audit/test_site01_smoke_hud_final.py")\nexec(compile(p.read_text(),str(p),"exec"),globals())\n')
 r=json.loads(c.runpy(str(wrapper),str(E/'site01-client2-smoke-hud-final.json'),110));print(json.dumps({'passed':r['passed'],'stage':r.get('stage'),'error':r.get('error'),'checks':len(r.get('checks',[]))}),flush=True)
 assert r['passed'],r
 (D/'fixed-hud-args.json').write_text(json.dumps({'players':2,'profile':'joining'}))
 ui=json.loads(c.runpy(str(D/'read_fixed_hud.py'),str(D/'fixed-hud-site01-final.json'),30));assert ui['passed'],ui
 import subprocess
 capture=subprocess.run(['python3',str(D/'capture_fixed_hud_windows.py'),'fixed-hud-site01-final'],check=True,capture_output=True,text=True);print(capture.stdout,flush=True)

except Exception:r.update(passed=False,exception=traceback.format_exc());print(json.dumps(r),flush=True)
finally:
 if started:c.tool('EditorToolset.EditorAppToolset','StopPIE',{})
 with LOG.open('rb') as f:f.seek(start);t=f.read().decode(errors='replace')
 (E/'site01-client2-smoke-hud-final-log.txt').write_text(t)
 r['native_log_errors']=[line for line in t.splitlines() if any(x in line for x in ['Accessed None','Blueprint Runtime Error','LogPython: Error:','LogScript: Error:'])]
 (D/'site-smoke-hud-final-summary.json').write_text(json.dumps(r,indent=2));print(json.dumps({'native_log_errors':len(r['native_log_errors'])}),flush=True)
 (D/'load-map-args.json').write_text(json.dumps({'path':'/Game/Puzzles/Test/SixRound/L_SixRound_Test'}));v=json.loads(c.runpy(str(D/'load_map.py'),str(D/'load-map-result.json'),120));assert v['ok'],v
