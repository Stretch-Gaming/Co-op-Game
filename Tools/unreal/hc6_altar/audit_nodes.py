import pathlib,json,unreal
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
bp=unreal.load_asset('/Game/Puzzles/BP_Altar')
out={}
for name in ['CanAccept','AcceptKey','ResetAltar','IsRoundActive']:
 out[name]=[{'info':str(BP._get_node_info(n)),'node_methods':[x for x in dir(n) if 'function' in x or 'reference' in x]} for n in BP.find_nodes(BP.get_graph(bp,name)) if isinstance(n,unreal.K2Node_CallFunction)]
pathlib.Path(__file__).parent.joinpath('node-audit.json').write_text(json.dumps(out,indent=2))
RESULT=out
