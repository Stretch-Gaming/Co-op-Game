import json
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
for path in ARGS.get('load',[]):ue.load_asset(path)
bp=ue.load_asset(ARGS.get('asset','/Game/Hazards/AC_Health'))
if ARGS.get('refresh'):
    from editor_toolset.toolsets.blueprint import _BlueprintCache
    _BlueprintCache.invalidate(bp)
graph=BP.get_graph(bp,ARGS.get('graph','Revive'))
matches={query:list(BP.find_node_types(graph,query)) for query in ARGS['queries']}
RESULT=matches
(QUEUE/'node-query.json').write_text(json.dumps(matches,indent=2))


