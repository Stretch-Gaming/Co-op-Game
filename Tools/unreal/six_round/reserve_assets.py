"""Reserve exact task asset paths, recording only leases acquired by this call."""
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
assert ROOT==Path(r'C:\Users\Stretch\.codex\worktrees\six-round-adventure\Co op Game')
paths=json.loads(Path(sys.argv[1]).read_text())
assert isinstance(paths,list)
inventory=json.loads(subprocess.check_output(['git','lfs','locks','--json'],cwd=ROOT,text=True))
if isinstance(inventory,dict):inventory=inventory['locks']
by_path={row['path']:row for row in inventory}
ledger=ROOT/'Saved/SixRound/acquired-leases.json'
acquired=json.loads(ledger.read_text()) if ledger.exists() else []
for path in paths:
    assert path.startswith(('Content/Core/','Content/Hazards/','Content/Player/','Content/Shared/','Content/Puzzles/Test/SixRound/')) and path.endswith(('.uasset','.umap')),path
    if path in by_path:
        assert by_path[path]['owner']['name']=='StretchGaming',path
        continue
    result=json.loads(subprocess.check_output(['git','lfs','lock','--json',path],cwd=ROOT,text=True))
    row=result[0] if isinstance(result,list) else result.get('lock',result)
    assert row['path']==path
    acquired.append(row)
    ledger.write_text(json.dumps(acquired,indent=2))
    print(path,flush=True)
fresh=json.loads(subprocess.check_output(['git','lfs','locks','--json'],cwd=ROOT,text=True))
if isinstance(fresh,dict):fresh=fresh['locks']
fresh={row['path']:row for row in fresh}
assert all(fresh[path]['owner']['name']=='StretchGaming' for path in paths)
(ROOT/'Saved/SixRound'/('reserved-'+Path(sys.argv[1]).stem+'.json')).write_text(json.dumps([fresh[path] for path in paths],indent=2))
