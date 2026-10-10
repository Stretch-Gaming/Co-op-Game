import json
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
bp=ue.load_asset('/Game/Puzzles/Test/HC_Gauntlet/BP_FixtureLatchBridge')
(HERE/'primary-spawn-nodes.json').write_text(json.dumps(list(BP.find_node_types(BP.get_graph(bp,'RequestLatch'),'SpawnActor')),indent=2))
