"""Inspect actual node identifiers before changing a graph."""
import json
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
bp = ue.load_asset(ARGS.get('asset', '/Game/Player/AC_Traversal'))
g = BP.get_graph(bp, ARGS.get('graph', 'ApplyTraversal'))
RESULT = {term: [str(x) for x in BP.find_node_types(g, term)] for term in ARGS['terms']}
(QUEUE/'node-catalog.json').write_text(json.dumps(RESULT, indent=2))
