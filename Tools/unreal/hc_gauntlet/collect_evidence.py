"""Hash final owned source, evidence and engine-authored binary deliverables."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
assert ROOT==Path('C:/Users/Stretch/.codex/worktrees/haunted-gauntlet-integration/Co op Game')
ignored={'artifact-hashes.json','ready.json','authorization.json','command.json','command.part','command-result.json','original-settings.json'}
files=[]
for folder in ['Content/Puzzles/Gauntlet','Content/Puzzles/Test/HC_Gauntlet','Tools/unreal/hc_gauntlet']:
 for path in (ROOT/folder).rglob('*'):
  if path.is_file() and path.name not in ignored and '__pycache__' not in path.parts:files.append(path)
files.append(ROOT/'docs/hc-gauntlet-verification.md')
rows=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]
matrix={}
for name in ['input-clients-2','input-clients-3','input-clients-4','input-host-3']:
 r=json.loads((HERE/(name+'.json')).read_text());l=json.loads((HERE/(name+'-log.json')).read_text())
 assert r['passed'] and l['passed'],name
 matrix[name]={'passed':True,'log_passed':True,'checks':len(r['checks'])}
primary={}
for name in ['primary-boundaries-clients-2','primary-boundaries-clients-3','primary-boundaries-clients-4','primary-boundaries-host-3']:
 r=json.loads((HERE/(name+'.json')).read_text());assert r['passed'] and not r['post_stop_log_errors'],name
 primary[name]={'passed':True,'checks':len(r['checks'])}
assert json.loads((HERE/'primary-review.json').read_text())['passed']
out={'root':str(ROOT),'blueprint_only':True,'binary_authorship':'UnrealEditor only','production_completion':'blocked until PG persistent latch and Core/PG/HZ integration deliveries','native_matrix':matrix,'primary_boundaries':primary,'files':rows,'aggregate_sha256':hashlib.sha256(json.dumps(rows,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
(HERE/'artifact-hashes.json').write_text(json.dumps(out,indent=2))
print(json.dumps({'files':len(rows),'binary_assets':sum(r['path'].startswith('Content/') for r in rows),'aggregate_sha256':out['aggregate_sha256']},indent=2))
