import json
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
before=json.loads((QUEUE/'baseline.json').read_text())['flare_graphs']
bp=ue.load_asset('/Game/Player/Tools/BP_Flare');after={g.get_name():BP.read_graph_dsl(g) for g in BP.list_graphs(bp)}
changed={n:{'before':d,'after':after.get(n)} for n,d in before.items() if after.get(n)!=d}
(QUEUE/'flare-graph-diff.json').write_text(json.dumps(changed,indent=2))
RESULT={'changed_original_graphs':list(changed),'new_graphs':sorted(set(after)-set(before))}
