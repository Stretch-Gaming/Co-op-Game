"""Narrow primary authoring context; no worker delegation or global saves."""
import importlib, json, sys
from pathlib import Path
import unreal as ue
ROOT=Path(ue.Paths.project_dir()).resolve()
assert ROOT==Path(__file__).resolve().parents[3]
QUEUE=ROOT/'Saved/PR130Integration'
sys.path.insert(0,str(ROOT/'Tools/unreal/six_round'))
import authoring
authoring.ROOT=ROOT;authoring.EXPECTED=ROOT;authoring.QUEUE=QUEUE
from authoring import BP, AT, V, S, fn, var, write, compile_bp, component, save

def require_lease(path):
    relative='Content/'+path.removeprefix('/Game/')+'.uasset'
    if path.endswith('.umap'):
        relative='Content/'+path.removeprefix('/Game/')
    rows=json.loads((QUEUE/'leases.json').read_text(encoding='utf-8-sig'))
    match=[r for r in rows if r['path']==relative and r.get('owner',{}).get('name')=='StretchGaming']
    assert len(match)==1, 'Exact own lease required: '+relative
    assert not ue.EditorLevelLibrary.get_pie_worlds(True)
    return match[0]
