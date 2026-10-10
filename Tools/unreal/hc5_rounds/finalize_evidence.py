import json,hashlib,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
assert ROOT==Path('C:/Users/Stretch/.codex/worktrees/round-progression/Co op Game')
checks=[]
for n in (2,3,4):
 for kind in ('clients','roster'):
  r=json.loads((HERE/f'{kind}-{n}.json').read_text());l=json.loads((HERE/f'{kind}-{n}-log.json').read_text());assert r['passed'] and l['passed']
  checks.append({'gate':f'{kind}-{n}','passed':True,'checks':len(r['checks'])})
for name in ('entrance-overlap','audit','settings-restored'):
 r=json.loads((HERE/f'{name}.json').read_text());assert r['passed'];checks.append({'gate':name,'passed':True})
assert json.loads((HERE/'entrance-overlap-log.json').read_text())['passed']
tracked=subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).splitlines();assert not tracked,tracked
files=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
allowed=lambda p:p in ['Content/Puzzles/BP_Checkpoint.uasset','Content/Puzzles/BP_RoundStart.uasset','docs/hc5-rounds-verification.md'] or p.startswith(('Content/Puzzles/Rounds/','Content/Puzzles/Test/HC5/','Tools/unreal/hc5_rounds/'))
assert all(allowed(p) for p in files),files
summary={'passed':True,'baseline':'4be3f85cff446901bbf88bdf918cfb2050d6fa18','branch':'codex/round-progression-next','project':str(ROOT),'port':8041,'editor_pid':26672,'checks':checks,'tracked_files_changed':tracked,'health_death_revive_tested':False,'rendering_tested':False,'full_issue11_acceptance':False}
(HERE/'acceptance-summary.json').write_text(json.dumps(summary,indent=2))
files=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
manifest={'baseline':summary['baseline'],'files':[{'path':p,'bytes':(ROOT/p).stat().st_size,'sha256':hashlib.sha256((ROOT/p).read_bytes()).hexdigest()} for p in files if not p.endswith('artifact-sha256.json')]}
(HERE/'artifact-sha256.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'passed':True,'gates':len(checks),'files':len(manifest['files'])}))
