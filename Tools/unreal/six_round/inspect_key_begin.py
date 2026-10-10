import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
RESULT={}
for path in ('/Game/Puzzles/BP_Carryable','/Game/Puzzles/BP_KeyRelic'):
    bp=ue.load_asset(path)
    RESULT[path]=BP.read_graph_dsl(BP.get_graph(bp,'EventGraph'))
