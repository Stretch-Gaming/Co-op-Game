import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
bp=ue.load_asset('/Game/Core/BP_CoopCharacter');RESULT={n:BP.read_graph_dsl(BP.get_graph(bp,n)) for n in ['UseAllowed','BeginUse','RefreshFocus','PressInteract','ConfirmLocalUse']}
