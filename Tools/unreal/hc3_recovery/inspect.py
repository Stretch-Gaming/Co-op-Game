import json,unreal
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
bp=unreal.load_asset('/Game/Puzzles/Recovery/BPI_HCHealthBridge')
result={x:BP.find_node_types(BP.get_graph(bp,'IsDowned'),x) for x in ['IsDowned','GetReviveSeconds','Revive','DoesObjectImplement']}
result['asset_subsystem']=[n for n in dir(unreal.AssetEditorSubsystem) if 'open' in n or 'close' in n]
(HERE/'bridge-api.json').write_text(json.dumps(result,default=str,indent=2))
