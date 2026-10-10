import pathlib,json,unreal,toolset_registry
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
bp=unreal.load_asset('/Game/Puzzles/BP_Altar')
if not bp: bp=unreal.EditorAssetLibrary.duplicate_asset('/Game/Puzzles/BP_Carryable','/Game/Puzzles/BP_Altar')
out={'variables':BP.list_variables(bp),'methods':[m for m in dir(BP) if 'variable' in m or 'graph' in m]}
g=BP.get_graph(bp,'EventGraph')
for term in ['RoundState','BreakS_RoundState','ResetForRound','AttachActorToComponent','SetActorRelativeTransform','GetCarried','ReleaseCarried','ClearRound']:
 out[term]=BP.find_node_types(g,term)
pathlib.Path(__file__).parent.joinpath('node-inspection.json').write_text(json.dumps(out,default=str,indent=2))
RESULT=out
