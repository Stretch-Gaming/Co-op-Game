import json
import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
bp=ue.load_asset('/Game/Core/BP_CoopCharacter')
names=['Server_BraceStart','Server_BraceStop','Server_ToggleView','Server_ToggleHeadlamp','Server_RequestBoost']
for i,name in enumerate(names):
    node=BP.add_event(bp,name)
    BP.set_node_position(node,ue.IntPoint(3000,3000+i*300))
RESULT={'arranged':names,'add_custom_event_api':ue.BlueprintGraphEditor.add_custom_event_node.__doc__}
