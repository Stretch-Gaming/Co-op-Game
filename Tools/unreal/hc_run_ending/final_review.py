import ast,hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
BASE='4be3f85cff446901bbf88bdf918cfb2050d6fa18'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True).splitlines()
def scope():return sorted(set(git('diff','--name-only',BASE)+git('ls-files','--others','--exclude-standard')))
def owned(p):return p in ('Content/Puzzles/BP_MapExit.uasset','docs/hc-run-ending-verification.md') or p.startswith(('Content/Puzzles/Run/','Content/Puzzles/UI/Results/','Content/Puzzles/Test/HC_RunEnding/','Tools/unreal/hc_run_ending/'))
files=scope();assert all(owned(p) for p in files),[p for p in files if not owned(p)]
protected=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig'))
bad=[entry['path'] for entry in protected if sha(ROOT/entry['path'])!=entry['sha256'].lower()];assert not bad,bad
saved=json.loads((HERE/'primary-save-review.json').read_text());assert saved['protected_core_controller_graphs_unchanged'] and all(saved['owned_graphs_match_worker_audit'].values())
worker=json.loads((HERE/'worker-artifact-hashes.json').read_text());native=[]
for entry in worker['files']:
 if entry['path'].endswith(('.uasset','.umap')):
  native.append({'path':entry['path'],'worker_sha256':entry['sha256'].lower(),'final_sha256':sha(ROOT/entry['path'])})
assert len(native)==9
syntax=[]
for p in files:
 if p.endswith('.py'):ast.parse((ROOT/p).read_text(encoding='utf-8-sig'),filename=p);syntax.append(p)
log=ROOT/'Saved/Logs/CoopGame.log';logchecks=[];pieces=[]
for name in ['clients-2','clients-3','clients-4','host-split','restore-cleared-state','primary-native','primary-native-fresh']:
 data=json.loads((HERE/(name+'.json')).read_text());assert data['passed'],name
 interval=json.loads((HERE/(name+'-log.json')).read_text());assert interval['passed'] and not interval['errors'],name
 log=ROOT/interval['log'];assert interval['end_byte']<=log.stat().st_size
 with log.open('rb') as f:f.seek(interval['start_byte']);raw=f.read(interval['end_byte']-interval['start_byte'])
 text=raw.decode('utf-8',errors='replace')
 errors=[line for line in text.splitlines() if re.search(r'Accessed None|Blueprint Runtime Error|Log\w+: Error:',line)];assert not errors,(name,errors)
 logchecks.append({'gate':name,'checks':len(data['checks']),'start_byte':interval['start_byte'],'end_byte':interval['end_byte'],'rescanned_clean':True,'interval_sha256':hashlib.sha256(raw).hexdigest()})
 pieces.append('GATE '+name+'\n'+text)
(HERE/'native-passing-log-intervals.txt').write_text('\n\n'.join(pieces),encoding='utf-8')
report={'passed':True,'baseline':BASE,'ownership_passed':True,'protected_files_checked':len(protected),'protected_hashes_unchanged':True,'protected_baseline':protected,'native_assets':native,'native_graphs_match_worker_audit':True,'python_syntax_checked':syntax,'passing_log_intervals':logchecks,'actual_travel_tested':False,'production_core_gamepad_mac_acceptance_pending':True}
(HERE/'primary-final-review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
files=scope();manifest={'baseline':BASE,'primary_review_passed':True,'files':[{'path':p,'sha256':sha(ROOT/p),'bytes':(ROOT/p).stat().st_size} for p in files if p!='Tools/unreal/hc_run_ending/artifact-hashes.json']}
(HERE/'artifact-hashes.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'passed':True,'protected_files':len(protected),'native_assets':len(native),'native_hashes_changed_after_compile_save':[e['path'] for e in native if e['worker_sha256']!=e['final_sha256']],'syntax_files':len(syntax),'log_gates':len(logchecks),'owned_changed_files':len(files),'manifest_sha256':sha(HERE/'artifact-hashes.json')},indent=2))
