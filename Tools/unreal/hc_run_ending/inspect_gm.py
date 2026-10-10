import json,unreal as ue
from editor_toolset.toolsets.blueprint import BlueprintTools as BP
bp=ue.load_asset('/Game/Puzzles/Test/HC_RunEnding/BP_RunEndingFixtureGM')
(HERE/'gm-inspection.json').write_text(json.dumps({'graphs':[g.get_name() for g in BP.list_graphs(bp)],'functions':[str(f) for f in BP.list_functions(bp)],'events':[str(f) for f in BP.list_events(bp)]},indent=2))
