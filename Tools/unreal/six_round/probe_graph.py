"""Inspect only the requested graph's pin types after a failed edit."""
import json
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
bp = ue.load_asset(ARGS['asset'])
g = BP.get_graph(bp, ARGS['graph'])
RESULT = []
for node in BP.find_nodes(g):
    n = BP._get_node_info(node)
    if any(term.lower() in n.type_id.lower() for term in ARGS.get('terms', [])):
        RESULT.append({'type': n.type_id,
                       'inputs': [{'name': p.name, 'type': p.type_id, 'value': p.value} for p in n.input_pins],
                       'outputs': [{'name': p.name, 'type': p.type_id} for p in n.output_pins]})
(QUEUE/'graph-pin-probe.json').write_text(json.dumps(RESULT, indent=2))
