"""Final native compile, ownership and saved source checks; no level changes."""
import json,hashlib,sys
sys.path.insert(0,str(HERE))
from context import *
assets=[MODE,'/Game/Puzzles/Test/SixRound/BP_MazeCheckpoint','/Game/Puzzles/Test/SixRound/BP_HallBArrival','/Game/Puzzles/Test/SixRound/BP_TeamHallDoor','/Game/Puzzles/UI/HCA3/WBP_HCA3RoundHUD']
unused='/Game/Puzzles/Test/SixRound/BP_MazeReturnBridge'
assert not ue.EditorLevelLibrary.get_pie_worlds(True)
if ue.EditorAssetLibrary.does_asset_exist(unused):
    assert not ue.EditorAssetLibrary.find_package_referencers_for_asset(unused,True)
    assert ue.EditorAssetLibrary.delete_asset(unused)
compiled=[]
for path in assets:
    bp=ue.load_asset(path);compile_bp(bp)
    assert 'ERROR' not in str(bp.get_editor_property('status')).upper(),(path,str(bp.get_editor_property('status')))
    compiled.append({'path':path,'status':str(bp.get_editor_property('status'))})
protected=json.loads((QUEUE/'protected-graph-assets.json').read_text())
rows=protected.get('assets',protected) if isinstance(protected,dict) else protected
baseline=json.loads((QUEUE/'baseline.json').read_text())
hashes={**baseline['protected_sha256'],**protected}
assert all(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest for path,digest in hashes.items())
report={'passed':True,'compiled':compiled,'protected_assets_unchanged':hashes,'unused_bridge_removed':True}
(QUEUE/'final-audit.json').write_text(json.dumps(report,indent=2));RESULT=report
