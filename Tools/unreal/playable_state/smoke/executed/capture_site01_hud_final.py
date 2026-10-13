import json,importlib.util,subprocess,traceback
from pathlib import Path
spec=importlib.util.spec_from_file_location('ue_client','/tmp/coop-ue.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c);c.start();D=Path('/tmp/coop-runtime');LOG=Path('/Volumes/CoopBuild/Logs/CoopGameEditor/CoopGame.log');start=LOG.stat().st_size;R={'passed':False};started=False
try:
 (D/'control-args.json').write_text(json.dumps({'action':'prepare','players':2,'mode':'PIE_Client'}));assert json.loads(c.runpy(str(D/'control.py'),str(D/'control-result.json'),30))['ok']
 (D/'load-map-args.json').write_text(json.dumps({'path':'/Game/Maps/L_Site01'}));assert json.loads(c.runpy(str(D/'load_map.py'),str(D/'load-map-result.json'),90))['ok']
 c.tool('EditorToolset.EditorAppToolset','StartPIE',{'options':{'bSimulate':False,'playMode':'PlayMode_InEditorFloating','warmupSeconds':2}});started=True
 (D/'ready-args.json').write_text(json.dumps({'players':2,'profile':'joining'}));assert json.loads(c.runpy(str(D/'ready.py'),str(D/'ready-result.json'),40))['ok']
 (D/'fixed-hud-args.json').write_text(json.dumps({'players':2,'profile':'joining','report_name':'fixed-hud-site01-final'}));R=json.loads(c.runpy(str(D/'read_fixed_hud_v2.py'),str(D/'fixed-hud-site01-final.json'),30));assert R['passed'],R
 capture=subprocess.run(['python3',str(D/'capture_fixed_hud_windows.py'),'fixed-hud-site01-final'],check=True,capture_output=True,text=True);print(capture.stdout,flush=True)
except Exception:R.update(passed=False,driver_error=traceback.format_exc())
finally:
 if started:c.tool('EditorToolset.EditorAppToolset','StopPIE',{})
 b=LOG.read_bytes()[start:];(D/'fixed-hud-site01-final-log.txt').write_bytes(b);R['native_log_errors']=[l for l in b.decode(errors='replace').splitlines() if any(x in l for x in ['Accessed None','Blueprint Runtime Error','LogPython: Error:','LogScript: Error:'])]
 (D/'fixed-hud-site01-final-owner-summary.json').write_text(json.dumps(R,indent=2));print(json.dumps({'passed':R['passed'],'owners':len(R.get('owners',[])),'native_log_errors':len(R['native_log_errors']),'driver_error':R.get('driver_error')}),flush=True)
 (D/'load-map-args.json').write_text(json.dumps({'path':'/Game/Puzzles/Test/SixRound/L_SixRound_Test'}));assert json.loads(c.runpy(str(D/'load_map.py'),str(D/'load-map-result.json'),90))['ok']
