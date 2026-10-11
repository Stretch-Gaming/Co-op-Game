import unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
bp=ue.load_asset('/Game/Hazards/Traps/SixRound/BP_SixRoundTrap')
RESULT={'begin_dsl':BP.read_graph_dsl(BP.get_graph(bp,'SRTrapBeginTrap')),'reset_dsl':BP.read_graph_dsl(BP.get_graph(bp,'SRTrapResetSchedule'))}
(QUEUE/'trap-timer-diagnostic.json').write_text(__import__('json').dumps(RESULT,indent=2))
